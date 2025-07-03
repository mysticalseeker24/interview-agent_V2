"""Resume upload and parsing routers."""
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.resume import ResumeUploadResponse, ResumeRead, ResumeList
from app.schemas.user import UserRead
from app.services.resume_service import ResumeService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/parse", response_model=ResumeUploadResponse)
async def upload_and_parse_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """
    Upload and parse a resume file.
    
    Args:
        file: Resume file (PDF, DOCX, DOC, TXT)
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Upload response with parsing results
    """
    try:
        service = ResumeService(db)
        result = await service.upload_and_parse_resume(file, current_user.id)
        
        logger.info(f"Uploaded and parsed resume for user {current_user.id}")
        return result
        
    except ValueError as e:
        logger.warning(f"Invalid file upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload and parse resume"
        )


@router.get("/", response_model=List[ResumeRead])
async def list_resumes(
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """
    List all resumes for the current user.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of user resumes
    """
    try:
        service = ResumeService(db)
        resumes = await service.list_user_resumes(current_user.id)
        
        logger.info(f"Listed {len(resumes)} resumes for user {current_user.id}")
        return resumes
        
    except Exception as e:
        logger.error(f"Error listing resumes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list resumes"
        )


@router.get("/{resume_id}", response_model=ResumeRead)
async def get_resume(
    resume_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """
    Get resume by ID.
    
    Args:
        resume_id: Resume ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Resume data
    """
    try:
        service = ResumeService(db)
        resume = await service.get_resume_by_id(resume_id, current_user.id)
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        logger.info(f"Retrieved resume {resume_id} for user {current_user.id}")
        return resume
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resume {resume_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get resume"
        )


@router.get("/{resume_id}/parsed-data")
async def get_parsed_resume_data(
    resume_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get parsed resume data for integration with other services.
    
    Args:
        resume_id: Resume ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Parsed resume data
    """
    try:
        service = ResumeService(db)
        parsed_data = await service.get_parsed_resume_data(resume_id, current_user.id)
        
        if not parsed_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found or not processed"
            )
        
        logger.info(f"Retrieved parsed data for resume {resume_id}")
        return parsed_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting parsed data for resume {resume_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get parsed resume data"
        )


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """
    Delete resume by ID.
    
    Args:
        resume_id: Resume ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    try:
        service = ResumeService(db)
        deleted = await service.delete_resume(resume_id, current_user.id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        logger.info(f"Deleted resume {resume_id} for user {current_user.id}")
        return {"message": "Resume deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting resume {resume_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete resume"
        )


# Internal endpoints for service-to-service communication
@router.get("/internal/{resume_id}/data")
async def get_resume_data_internal(
    resume_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Internal endpoint for other services to get resume data.
    
    Args:
        resume_id: Resume ID
        user_id: User ID
        db: Database session
        
    Returns:
        Parsed resume data
    """
    try:
        service = ResumeService(db)
        parsed_data = await service.get_parsed_resume_data(resume_id, user_id)
        
        if not parsed_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found or not processed"
            )
        
        return parsed_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resume data internally: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get resume data"
        )
