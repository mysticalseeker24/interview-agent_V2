"""JSON-based resume service for file storage operations."""
import asyncio
import json
import logging
import os
import shutil
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
from fastapi import UploadFile
from filelock import FileLock

from app.schemas.resume import ResumeParseResult, ResumeRead, ResumeUploadResponse
from app.services.resume_parsing_service import ResumeParsingService
from app.core.json_config import get_json_settings

logger = logging.getLogger(__name__)

settings = get_json_settings()


class JsonResumeService:
    """Service for resume management using local JSON file storage."""
    
    def __init__(self):
        """Initialize JSON Resume Service."""
        self.parser = ResumeParsingService()
        self.data_dir = Path("data")
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.metadata_dir = self.data_dir / "metadata"
        self.resumes_dir = self.data_dir / "resumes"
        
        self._ensure_directories()
        self._ensure_metadata_files()
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        for directory in [self.data_dir, self.upload_dir, self.metadata_dir, self.resumes_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _ensure_metadata_files(self):
        """Ensure metadata files exist with default values."""
        counters_file = self.metadata_dir / "counters.json"
        if not counters_file.exists():
            default_counters = {
                "next_resume_id": 1,
                "total_resumes": 0,
                "last_updated": datetime.utcnow().isoformat()
            }
            self._write_json_file(counters_file, default_counters)
    
    def _read_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Read JSON file with error handling."""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error reading JSON file {file_path}: {str(e)}")
            return {}
    
    def _write_json_file(self, file_path: Path, data: Dict[str, Any]) -> bool:
        """Write JSON file with error handling and atomic operations."""
        try:
            # Write to temporary file first, then move (atomic operation)
            temp_file = file_path.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            # Atomic move
            temp_file.replace(file_path)
            return True
        except Exception as e:
            logger.error(f"Error writing JSON file {file_path}: {str(e)}")
            return False
    
    def _get_next_resume_id(self) -> int:
        """Get next available resume ID with thread safety."""
        counters_file = self.metadata_dir / "counters.json"
        lock_file = self.metadata_dir / "counters.lock"
        
        with FileLock(str(lock_file)):
            counters = self._read_json_file(counters_file)
            next_id = counters.get("next_resume_id", 1)
            
            # Update counters
            counters["next_resume_id"] = next_id + 1
            counters["total_resumes"] = counters.get("total_resumes", 0) + 1
            counters["last_updated"] = datetime.utcnow().isoformat()
            
            self._write_json_file(counters_file, counters)
            return next_id
    
    def _get_user_dir(self, user_id: int) -> Path:
        """Get user-specific directory path."""
        return self.resumes_dir / f"user_{user_id}"
    
    def _get_resume_file_path(self, user_id: int, resume_id: int) -> Path:
        """Get resume JSON file path."""
        return self._get_user_dir(user_id) / f"resume_{resume_id}.json"
    
    def _get_user_index_path(self, user_id: int) -> Path:
        """Get user index file path."""
        return self._get_user_dir(user_id) / "index.json"
    
    def _update_user_index(self, user_id: int, resume_data: Dict[str, Any], is_delete: bool = False):
        """Update user index file."""
        user_dir = self._get_user_dir(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        
        index_file = self._get_user_index_path(user_id)
        lock_file = user_dir / "index.lock"
        
        with FileLock(str(lock_file)):
            index_data = self._read_json_file(index_file)
            
            if not index_data:
                index_data = {
                    "user_id": user_id,
                    "resume_count": 0,
                    "resumes": [],
                    "last_updated": datetime.utcnow().isoformat()
                }
            
            # Update resume list
            resume_id = resume_data["id"]
            existing_resumes = [r for r in index_data["resumes"] if r["id"] != resume_id]
            
            if not is_delete:
                # Add or update resume entry
                resume_entry = {
                    "id": resume_id,
                    "filename": resume_data["filename"],
                    "created_at": resume_data["created_at"],
                    "processing_status": resume_data["processing_status"]
                }
                existing_resumes.append(resume_entry)
            
            index_data["resumes"] = existing_resumes
            index_data["resume_count"] = len(existing_resumes)
            index_data["last_updated"] = datetime.utcnow().isoformat()
            
            self._write_json_file(index_file, index_data)
    
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
    
    async def save_uploaded_file(self, file: UploadFile, user_id: int, resume_id: int) -> str:
        """
        Save uploaded file to user-specific directory.
        
        Args:
            file: Uploaded file
            user_id: User ID
            resume_id: Resume ID
            
        Returns:
            File path
        """
        # Create user upload directory
        user_upload_dir = self.upload_dir / f"user_{user_id}"
        user_upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with resume ID
        extension = self._get_file_extension(file.filename)
        filename = f"{resume_id}_{file.filename}"
        file_path = user_upload_dir / filename
        
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
        
        # Get new resume ID
        resume_id = self._get_next_resume_id()
        
        # Save file
        file_path = await self.save_uploaded_file(file, user_id, resume_id)
        
        # Create initial resume data
        extension = self._get_file_extension(file.filename)
        file_type = self._get_file_type(extension)
        
        now = datetime.utcnow()
        resume_data = {
            "id": resume_id,
            "user_id": user_id,
            "filename": file.filename,
            "file_path": file_path,
            "file_size": file.size,
            "file_type": file_type,
            "raw_text": None,
            "parsed_data": None,
            "processing_status": "pending",
            "processing_error": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "processed_at": None
        }
        
        # Save initial resume data
        resume_file_path = self._get_resume_file_path(user_id, resume_id)
        self._write_json_file(resume_file_path, resume_data)
        
        # Update user index
        self._update_user_index(user_id, resume_data)
        
        # Parse resume
        try:
            resume_data["processing_status"] = "processing"
            resume_data["updated_at"] = datetime.utcnow().isoformat()
            self._write_json_file(resume_file_path, resume_data)
            
            # Extract text from file
            text = self.parser.extract_text_from_file(file_path, file_type)
            
            if not text:
                raise ValueError("Could not extract text from file")
            
            # Parse resume
            parsed_result = self.parser.parse_resume(text)
            
            # Update resume data
            resume_data["raw_text"] = text
            resume_data["parsed_data"] = parsed_result.dict()
            resume_data["processing_status"] = "completed"
            resume_data["processed_at"] = datetime.utcnow().isoformat()
            resume_data["updated_at"] = datetime.utcnow().isoformat()
            
            self._write_json_file(resume_file_path, resume_data)
            self._update_user_index(user_id, resume_data)
            
            logger.info(f"Successfully parsed resume {resume_id}")
            
            return ResumeUploadResponse(
                id=resume_id,
                filename=resume_data["filename"],
                file_size=resume_data["file_size"],
                file_type=resume_data["file_type"],
                processing_status=resume_data["processing_status"],
                parsed_data=parsed_result,
                created_at=datetime.fromisoformat(resume_data["created_at"]),
                message="Resume uploaded and parsed successfully"
            )
            
        except Exception as e:
            # Update status to failed
            resume_data["processing_status"] = "failed"
            resume_data["processing_error"] = str(e)
            resume_data["updated_at"] = datetime.utcnow().isoformat()
            
            self._write_json_file(resume_file_path, resume_data)
            self._update_user_index(user_id, resume_data)
            
            logger.error(f"Error parsing resume {resume_id}: {str(e)}")
            
            return ResumeUploadResponse(
                id=resume_id,
                filename=resume_data["filename"],
                file_size=resume_data["file_size"],
                file_type=resume_data["file_type"],
                processing_status=resume_data["processing_status"],
                parsed_data=None,
                created_at=datetime.fromisoformat(resume_data["created_at"]),
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
        resume_file = self._get_resume_file_path(user_id, resume_id)
        resume_data = self._read_json_file(resume_file)
        
        if resume_data and resume_data.get("user_id") == user_id:
            # Convert ISO strings back to datetime objects for Pydantic
            for field in ["created_at", "updated_at", "processed_at"]:
                if resume_data.get(field):
                    resume_data[field] = datetime.fromisoformat(resume_data[field])
            
            return ResumeRead(**resume_data)
        
        return None
    
    async def list_user_resumes(self, user_id: int) -> List[ResumeRead]:
        """
        List all resumes for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of user resumes
        """
        index_file = self._get_user_index_path(user_id)
        index_data = self._read_json_file(index_file)
        
        resumes = []
        for resume_entry in index_data.get("resumes", []):
            resume_id = resume_entry["id"]
            resume = await self.get_resume_by_id(resume_id, user_id)
            if resume:
                resumes.append(resume)
        
        return resumes
    
    async def delete_resume(self, resume_id: int, user_id: int) -> bool:
        """
        Delete resume by ID for specific user.
        
        Args:
            resume_id: Resume ID
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        resume_file = self._get_resume_file_path(user_id, resume_id)
        resume_data = self._read_json_file(resume_file)
        
        if not resume_data or resume_data.get("user_id") != user_id:
            return False
        
        # Delete uploaded file
        try:
            file_path = resume_data.get("file_path")
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.warning(f"Could not delete file {file_path}: {str(e)}")
        
        # Delete resume JSON file
        try:
            resume_file.unlink()
            logger.info(f"Deleted resume file: {resume_file}")
        except Exception as e:
            logger.error(f"Could not delete resume file {resume_file}: {str(e)}")
            return False
        
        # Update user index
        self._update_user_index(user_id, resume_data, is_delete=True)
        
        # Update global counters
        counters_file = self.metadata_dir / "counters.json"
        lock_file = self.metadata_dir / "counters.lock"
        
        with FileLock(str(lock_file)):
            counters = self._read_json_file(counters_file)
            counters["total_resumes"] = max(0, counters.get("total_resumes", 1) - 1)
            counters["last_updated"] = datetime.utcnow().isoformat()
            self._write_json_file(counters_file, counters)
        
        logger.info(f"Deleted resume {resume_id}")
        return True
    
    async def get_parsed_resume_data(self, resume_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get parsed resume data for integration with other services.
        
        Args:
            resume_id: Resume ID
            user_id: User ID
            
        Returns:
            Parsed resume data or None
        """
        resume_file = self._get_resume_file_path(user_id, resume_id)
        resume_data = self._read_json_file(resume_file)
        
        if (resume_data and 
            resume_data.get("user_id") == user_id and 
            resume_data.get("processing_status") == "completed" and
            resume_data.get("parsed_data")):
            return resume_data["parsed_data"]
        
        return None
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """
        Get service statistics.
        
        Returns:
            Service statistics
        """
        counters_file = self.metadata_dir / "counters.json"
        counters = self._read_json_file(counters_file)
        
        return {
            "total_resumes": counters.get("total_resumes", 0),
            "next_resume_id": counters.get("next_resume_id", 1),
            "storage_type": "json_files",
            "data_directory": str(self.data_dir),
            "upload_directory": str(self.upload_dir),
            "last_updated": counters.get("last_updated")
        }
