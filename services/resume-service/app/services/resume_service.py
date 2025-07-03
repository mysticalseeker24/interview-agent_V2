"""Resume service for database operations."""
import logging
import os
import shutil
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import UploadFile

from app.models.resume import Resume
from app.schemas.resume import ResumeParseResult, ResumeRead, ResumeUploadResponse
from app.services.resume_parsing_service import ResumeParsingService
from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class ResumeService:
    """Service for resume management and database operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize Resume Service."""
        self.db = db
        self.parser = ResumeParsingService()
        self._ensure_upload_dir()
    
    def _ensure_upload_dir(self):
        """Ensure upload directory exists."""
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename."""
        return Path(filename).suffix.lower()
    
    def _get_file_type(self, extension: str) -> str:
        """Get file type from extension."""
        type_mapping = {
            '.pdf': 'pdf',
            '.docx': 'docx',
            '.doc': 'doc',
            '.txt': 'txt'
        }
        return type_mapping.get(extension.lower(), 'unknown')
    
    def _is_allowed_file(self, filename: str) -> bool:
        """Check if file type is allowed."""
        extension = self._get_file_extension(filename)
        return extension in settings.ALLOWED_EXTENSIONS
    
    async def save_uploaded_file(self, file: UploadFile, user_id: int) -> str:
        """
        Save uploaded file to disk.
        
        Args:
            file: Uploaded file
            user_id: User ID
            
        Returns:
            File path
        """
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = self._get_file_extension(file.filename)
        filename = f"{user_id}_{timestamp}_{file.filename}"
        file_path = Path(settings.UPLOAD_DIR) / filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Saved file: {file_path}")
        return str(file_path)
    
    async def upload_and_parse_resume(
        self, 
        file: UploadFile, 
        user_id: int
    ) -> ResumeUploadResponse:
        """
        Upload and parse resume file.
        
        Args:
            file: Uploaded resume file
            user_id: User ID
            
        Returns:
            Upload response with parsing results
        """
        # Validate file
        if not self._is_allowed_file(file.filename):
            raise ValueError(f"File type not allowed: {file.filename}")
        
        if file.size > settings.MAX_FILE_SIZE:
            raise ValueError(f"File too large: {file.size} bytes")
        
        # Save file
        file_path = await self.save_uploaded_file(file, user_id)
        
        # Create resume record
        extension = self._get_file_extension(file.filename)
        file_type = self._get_file_type(extension)
        
        resume = Resume(
            user_id=user_id,
            filename=file.filename,
            file_path=file_path,
            file_size=file.size,
            file_type=file_type,
            processing_status="pending"
        )
        
        self.db.add(resume)
        await self.db.flush()  # Get ID
        
        # Parse resume
        try:
            resume.processing_status = "processing"
            await self.db.commit()
            
            # Extract text from file
            text = self.parser.extract_text_from_file(file_path, file_type)
            
            if not text:
                raise ValueError("Could not extract text from file")
            
            # Parse resume
            parsed_result = self.parser.parse_resume(text)
            
            # Update resume record
            resume.raw_text = text
            resume.parsed_data = parsed_result.dict()
            resume.processing_status = "completed"
            resume.processed_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"Successfully parsed resume {resume.id}")
            
            return ResumeUploadResponse(
                id=resume.id,
                filename=resume.filename,
                file_size=resume.file_size,
                file_type=resume.file_type,
                processing_status=resume.processing_status,
                parsed_data=parsed_result,
                created_at=resume.created_at,
                message="Resume uploaded and parsed successfully"
            )
            
        except Exception as e:
            # Update status to failed
            resume.processing_status = "failed"
            resume.processing_error = str(e)
            await self.db.commit()
            
            logger.error(f"Error parsing resume {resume.id}: {str(e)}")
            
            return ResumeUploadResponse(
                id=resume.id,
                filename=resume.filename,
                file_size=resume.file_size,
                file_type=resume.file_type,
                processing_status=resume.processing_status,
                parsed_data=None,
                created_at=resume.created_at,
                message=f"Resume upload failed: {str(e)}"
            )
    
    async def get_resume_by_id(self, resume_id: int, user_id: int) -> Optional[ResumeRead]:
        """
        Get resume by ID for specific user.
        
        Args:
            resume_id: Resume ID
            user_id: User ID
            
        Returns:
            Resume data or None
        """
        result = await self.db.execute(
            select(Resume).where(
                Resume.id == resume_id,
                Resume.user_id == user_id
            )
        )
        resume = result.scalar_one_or_none()
        
        if resume:
            return ResumeRead.from_orm(resume)
        return None
    
    async def list_user_resumes(self, user_id: int) -> List[ResumeRead]:
        """
        List all resumes for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of user resumes
        """
        result = await self.db.execute(
            select(Resume).where(Resume.user_id == user_id)
        )
        resumes = result.scalars().all()
        
        return [ResumeRead.from_orm(resume) for resume in resumes]
    
    async def delete_resume(self, resume_id: int, user_id: int) -> bool:
        """
        Delete resume by ID for specific user.
        
        Args:
            resume_id: Resume ID
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        result = await self.db.execute(
            select(Resume).where(
                Resume.id == resume_id,
                Resume.user_id == user_id
            )
        )
        resume = result.scalar_one_or_none()
        
        if resume:
            # Delete file from disk
            try:
                if os.path.exists(resume.file_path):
                    os.remove(resume.file_path)
                    logger.info(f"Deleted file: {resume.file_path}")
            except Exception as e:
                logger.warning(f"Could not delete file {resume.file_path}: {str(e)}")
            
            # Delete from database
            await self.db.delete(resume)
            await self.db.commit()
            
            logger.info(f"Deleted resume {resume_id}")
            return True
        
        return False
    
    async def get_parsed_resume_data(self, resume_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get parsed resume data for integration with other services.
        
        Args:
            resume_id: Resume ID
            user_id: User ID
            
        Returns:
            Parsed resume data or None
        """
        result = await self.db.execute(
            select(Resume).where(
                Resume.id == resume_id,
                Resume.user_id == user_id,
                Resume.processing_status == "completed"
            )
        )
        resume = result.scalar_one_or_none()
        
        if resume and resume.parsed_data:
            return resume.parsed_data
        
        return None
