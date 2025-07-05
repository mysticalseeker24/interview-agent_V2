"""
FastAPI Resume Service
REST API for the unified resume processing pipeline.
"""
import logging
import os
import json
import aiofiles
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .resume_processor import ResumeProcessor
from .schema import ResumeJSON, ProcessingResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Resume Processing Service",
    description="Unified text-to-JSON resume parsing pipeline",
    version="1.0.0"
)

# Initialize processor
processor = ResumeProcessor(use_llm=False)  # Set to True to enable LLM features

# Storage directories
UPLOADS_DIR = Path("uploads")
DATA_DIR = Path("data")

# Ensure directories exist
UPLOADS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)


class ResumeUploadResponse(BaseModel):
    """Response for resume upload endpoint."""
    success: bool
    resume_id: str
    filename: str
    file_size: int
    processing_result: ProcessingResult
    storage_path: Optional[str] = None


class ResumeListResponse(BaseModel):
    """Response for listing resumes."""
    resumes: List[dict]
    total: int


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Resume Processing Service",
        "version": "1.0.0",
        "status": "healthy",
        "pipeline_info": processor.get_pipeline_info()
    }


@app.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Form(default="anonymous")
):
    """
    Upload and process a resume file.
    
    Args:
        file: Resume file (PDF, DOCX, TXT)
        user_id: User identifier for organization
        
    Returns:
        Processing results and storage information
    """
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.docx', '.doc', '.txt'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_extensions}"
            )
        
        # Generate unique resume ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        resume_id = f"{user_id}_{timestamp}"
        
        # Save uploaded file
        upload_path = UPLOADS_DIR / f"{resume_id}_{file.filename}"
        async with aiofiles.open(upload_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        file_size = len(content)
        logger.info(f"Saved uploaded file: {upload_path} ({file_size} bytes)")
        
        # Process the resume
        result = processor.process_resume(str(upload_path))
        
        # Save JSON result if processing succeeded
        json_path = None
        if result.success and result.resume_json:
            json_path = DATA_DIR / f"{resume_id}.json"
            
            # Convert to dict for JSON serialization
            resume_data = result.resume_json.model_dump()
            
            async with aiofiles.open(json_path, 'w') as f:
                await f.write(json.dumps(resume_data, indent=2, default=str))
            
            logger.info(f"Saved processed JSON: {json_path}")
        
        return ResumeUploadResponse(
            success=result.success,
            resume_id=resume_id,
            filename=file.filename,
            file_size=file_size,
            processing_result=result,
            storage_path=str(json_path) if json_path else None
        )
        
    except Exception as e:
        logger.error(f"Upload processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process-text")
async def process_text(
    text: str = Form(...),
    user_id: str = Form(default="anonymous")
):
    """
    Process raw resume text directly.
    
    Args:
        text: Raw resume text
        user_id: User identifier
        
    Returns:
        Processing results
    """
    try:
        # Process the text
        result = processor.process_text(text)
        
        # Save result if processing succeeded
        if result.success and result.resume_json:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            resume_id = f"{user_id}_text_{timestamp}"
            json_path = DATA_DIR / f"{resume_id}.json"
            
            resume_data = result.resume_json.model_dump()
            
            async with aiofiles.open(json_path, 'w') as f:
                await f.write(json.dumps(resume_data, indent=2, default=str))
        
        return result
        
    except Exception as e:
        logger.error(f"Text processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/resume/{resume_id}")
async def get_resume(resume_id: str):
    """
    Retrieve processed resume data by ID.
    
    Args:
        resume_id: Resume identifier
        
    Returns:
        Processed resume JSON
    """
    try:
        json_path = DATA_DIR / f"{resume_id}.json"
        
        if not json_path.exists():
            raise HTTPException(status_code=404, detail="Resume not found")
        
        async with aiofiles.open(json_path, 'r') as f:
            data = await f.read()
            
        return JSONResponse(content=json.loads(data))
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Resume not found")
    except Exception as e:
        logger.error(f"Failed to retrieve resume {resume_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/resumes", response_model=ResumeListResponse)
async def list_resumes(user_id: Optional[str] = None, limit: int = 50):
    """
    List processed resumes.
    
    Args:
        user_id: Filter by user ID (optional)
        limit: Maximum number of results
        
    Returns:
        List of resume metadata
    """
    try:
        resumes = []
        
        # Get all JSON files in data directory
        json_files = list(DATA_DIR.glob("*.json"))
        
        for json_file in json_files[:limit]:
            try:
                # Parse resume ID and user from filename
                resume_id = json_file.stem
                file_user_id = resume_id.split('_')[0] if '_' in resume_id else "unknown"
                
                # Filter by user if specified
                if user_id and file_user_id != user_id:
                    continue
                
                # Get file metadata
                stat = json_file.stat()
                
                # Load basic resume info
                async with aiofiles.open(json_file, 'r') as f:
                    data = json.loads(await f.read())
                
                resume_info = {
                    "resume_id": resume_id,
                    "user_id": file_user_id,
                    "filename": data.get("contact", {}).get("name", "Unknown") + ".json",
                    "processing_confidence": data.get("parsing_confidence", 0.0),
                    "sections_detected": data.get("sections_detected", []),
                    "domains": data.get("domains", []),
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "file_size": stat.st_size
                }
                
                resumes.append(resume_info)
                
            except Exception as e:
                logger.warning(f"Failed to process resume file {json_file}: {e}")
                continue
        
        return ResumeListResponse(
            resumes=resumes,
            total=len(resumes)
        )
        
    except Exception as e:
        logger.error(f"Failed to list resumes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/resume/{resume_id}")
async def delete_resume(resume_id: str):
    """
    Delete a processed resume.
    
    Args:
        resume_id: Resume identifier
        
    Returns:
        Deletion confirmation
    """
    try:
        json_path = DATA_DIR / f"{resume_id}.json"
        
        if not json_path.exists():
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Remove JSON file
        json_path.unlink()
        
        # Try to remove associated upload file
        upload_files = list(UPLOADS_DIR.glob(f"{resume_id}_*"))
        for upload_file in upload_files:
            upload_file.unlink()
        
        logger.info(f"Deleted resume: {resume_id}")
        
        return {"success": True, "message": f"Resume {resume_id} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete resume {resume_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pipeline/info")
async def get_pipeline_info():
    """Get detailed pipeline information."""
    return processor.get_pipeline_info()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
