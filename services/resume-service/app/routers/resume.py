"""Resume upload and parsing routers using JSON file storage."""
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Query

from app.services.resume_service import ResumeService
from app.schemas.resume import ResumeUploadResponse, ResumeRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/parse", response_model=ResumeUploadResponse)
async def upload_and_parse_resume(
    file: UploadFile = File(...),
    user_id: int = Query(..., description="User ID for the resume")
):
    """
    Upload and parse a resume file.
    
    Args:
        file: Resume file (PDF, DOCX, DOC, TXT)
        user_id: User ID for the resume
        
    Returns:
        Upload response with parsing results
    """
    try:
        service = ResumeService()
        result = await service.upload_and_parse_resume(file, user_id)
        
        logger.info(f"Uploaded and parsed resume for user {user_id}")
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
    user_id: int = Query(..., description="User ID to list resumes for")
):
    """
    List all resumes for a user.
    
    Args:
        user_id: User ID to list resumes for
        
    Returns:
        List of user resumes
    """
    try:
        service = ResumeService()
        resumes = await service.list_user_resumes(user_id)
        
        logger.info(f"Listed {len(resumes)} resumes for user {user_id}")
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
    user_id: int = Query(..., description="User ID for the resume")
):
    """
    Get resume by ID.
    
    Args:
        resume_id: Resume ID
        user_id: User ID for the resume
        
    Returns:
        Resume data
    """
    try:
        service = ResumeService()
        resume = await service.get_resume_by_id(resume_id, user_id)
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        logger.info(f"Retrieved resume {resume_id} for user {user_id}")
        return resume
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resume {resume_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get resume"
        )


@router.get("/{resume_id}/data")
async def get_parsed_resume_data(
    resume_id: int,
    user_id: int = Query(..., description="User ID for the resume")
) -> Dict[str, Any]:
    """
    Get parsed resume data.
    
    Args:
        resume_id: Resume ID
        user_id: User ID for the resume
        
    Returns:
        Parsed resume data
    """
    try:
        service = ResumeService()
        parsed_data = await service.get_parsed_resume_data(resume_id, user_id)
        
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
    user_id: int = Query(..., description="User ID for the resume")
):
    """
    Delete resume by ID.
    
    Args:
        resume_id: Resume ID
        user_id: User ID for the resume
        
    Returns:
        Success message
    """
    try:
        service = ResumeService()
        deleted = await service.delete_resume(resume_id, user_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        logger.info(f"Deleted resume {resume_id} for user {user_id}")
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
    user_id: int = Query(..., description="User ID for the resume")
) -> Dict[str, Any]:
    """
    Internal endpoint for other services to get resume data.
    
    Args:
        resume_id: Resume ID
        user_id: User ID for the resume
        
    Returns:
        Parsed resume data
    """
    try:
        service = ResumeService()
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


@router.get("/admin/stats")
async def get_service_stats() -> Dict[str, Any]:
    """
    Get service statistics.
    
    Returns:
        Service statistics including total resumes and storage info
    """
    try:
        service = ResumeService()
        stats = await service.get_service_stats()
        
        logger.info("Retrieved service statistics")
        return stats
        
    except Exception as e:
        logger.error(f"Error getting service stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get service statistics"
        )
