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

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .resume_processor import ResumeProcessor
from .enhanced_resume_processor import EnhancedResumeProcessor
from .schema import ResumeJSON, ProcessingResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Resume Processing Service",
    description="Unified text-to-JSON resume parsing pipeline with advanced OCR and metadata extraction",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors
processor = ResumeProcessor(use_llm=False)  # Set to True to enable LLM features
enhanced_processor = EnhancedResumeProcessor(use_llm=False)  # Enhanced processor with OCR

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


class EnhancedResumeUploadResponse(BaseModel):
    """Response for enhanced resume upload endpoint."""
    success: bool
    resume_id: str
    filename: str
    file_size: int
    processing_result: ProcessingResult
    storage_path: Optional[str] = None
    enhanced_features: dict
    extraction_summary: dict


class ResumeListResponse(BaseModel):
    """Response for listing resumes."""
    resumes: List[dict]
    total: int


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Resume Processing Service",
        "version": "2.0.0",
        "status": "healthy",
        "pipeline_info": processor.get_pipeline_info(),
        "enhanced_features": {
            "ocr_support": True,
            "hidden_link_detection": True,
            "metadata_extraction": True,
            "table_extraction": True,
            "image_ocr": True
        }
    }


@app.get("/api/v1/health")
async def health_check():
    """
    Standardized health check endpoint.
    
    Returns:
        dict: Health status
    """
    return {"status": "healthy"}


@app.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Form(default="anonymous")
):
    """
    Upload and process a resume file using standard processing.
    
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
        
        # Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        content = await file.read()
        if len(content) > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: 10MB"
            )
        
        # Generate unique resume ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        resume_id = f"{user_id}_{timestamp}"
        
        # Save uploaded file
        upload_path = UPLOADS_DIR / f"{resume_id}_{file.filename}"
        async with aiofiles.open(upload_path, 'wb') as f:
            await f.write(content)
        
        file_size = len(content)
        logger.info(f"Saved uploaded file: {upload_path} ({file_size} bytes)")
        
        # Process the resume
        result = processor.process_resume(str(upload_path))
        
        # Save JSON result if processing succeeded
        json_path = None
        if result.success and result.data:
            json_path = DATA_DIR / f"{resume_id}.json"
            
            # Convert to dict for JSON serialization
            resume_data = result.data.model_dump()
            
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload/enhanced", response_model=EnhancedResumeUploadResponse)
async def upload_resume_enhanced(
    file: UploadFile = File(...),
    user_id: str = Form(default="anonymous"),
    enable_ocr: bool = Form(default=True),
    enable_hidden_links: bool = Form(default=True),
    enable_metadata: bool = Form(default=True),
    enable_tables: bool = Form(default=True),
    enable_image_ocr: bool = Form(default=True)
):
    """
    Upload and process a resume file using enhanced processing with OCR and metadata extraction.
    
    Args:
        file: Resume file (PDF, DOCX, TXT)
        user_id: User identifier for organization
        enable_ocr: Enable OCR for text extraction
        enable_hidden_links: Enable hidden link detection
        enable_metadata: Enable metadata extraction
        enable_tables: Enable table extraction
        enable_image_ocr: Enable OCR for embedded images
        
    Returns:
        Enhanced processing results with extraction summary
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
        
        # Validate file size (20MB limit for enhanced processing)
        max_size = 20 * 1024 * 1024  # 20MB
        content = await file.read()
        if len(content) > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: 20MB for enhanced processing"
            )
        
        # Generate unique resume ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        resume_id = f"{user_id}_enhanced_{timestamp}"
        
        # Save uploaded file
        upload_path = UPLOADS_DIR / f"{resume_id}_{file.filename}"
        async with aiofiles.open(upload_path, 'wb') as f:
            await f.write(content)
        
        file_size = len(content)
        logger.info(f"Saved uploaded file for enhanced processing: {upload_path} ({file_size} bytes)")
        
        # Configure enhanced processing options
        enhanced_processor.set_processing_options(
            enable_ocr=enable_ocr,
            enable_hidden_links=enable_hidden_links,
            enable_metadata=enable_metadata,
            enable_tables=enable_tables,
            enable_image_ocr=enable_image_ocr
        )
        
        # Process the resume with enhanced features
        result = enhanced_processor.process_resume(str(upload_path))
        
        # Save JSON result if processing succeeded
        json_path = None
        if result.success and result.data:
            json_path = DATA_DIR / f"{resume_id}.json"
            
            # Convert to dict for JSON serialization
            resume_data = result.data.model_dump()
            
            async with aiofiles.open(json_path, 'w') as f:
                await f.write(json.dumps(resume_data, indent=2, default=str))
            
            logger.info(f"Saved enhanced processed JSON: {json_path}")
        
        # Prepare enhanced features summary
        enhanced_features = {
            "ocr_enabled": enable_ocr,
            "hidden_links_enabled": enable_hidden_links,
            "metadata_enabled": enable_metadata,
            "tables_enabled": enable_tables,
            "image_ocr_enabled": enable_image_ocr
        }
        
        # Get extraction summary from enhanced processor
        extraction_summary = enhanced_processor.get_extraction_summary()
        
        return EnhancedResumeUploadResponse(
            success=result.success,
            resume_id=resume_id,
            filename=file.filename,
            file_size=file_size,
            processing_result=result,
            storage_path=str(json_path) if json_path else None,
            enhanced_features=enhanced_features,
            extraction_summary=extraction_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced upload processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process-text/enhanced")
async def process_text_enhanced(
    text: str = Form(...),
    user_id: str = Form(default="anonymous"),
    enable_llm_enhancement: bool = Form(default=False)
):
    """
    Process raw resume text with enhanced features.
    
    Args:
        text: Raw resume text
        user_id: User identifier
        enable_llm_enhancement: Enable LLM enhancement for better extraction
        
    Returns:
        Enhanced processing results
    """
    try:
        # Configure enhanced processor
        enhanced_processor.set_processing_options(
            enable_llm_enhancement=enable_llm_enhancement
        )
        
        # Process the text with enhanced features
        result = enhanced_processor.process_text(text)
        
        # Save result if processing succeeded
        if result.success and result.data:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            resume_id = f"{user_id}_enhanced_text_{timestamp}"
            json_path = DATA_DIR / f"{resume_id}.json"
            
            resume_data = result.data.model_dump()
            
            async with aiofiles.open(json_path, 'w') as f:
                await f.write(json.dumps(resume_data, indent=2, default=str))
        
        # Get extraction summary
        extraction_summary = enhanced_processor.get_extraction_summary()
        
        return {
            "success": result.success,
            "data": result.data.model_dump() if result.data else None,
            "extraction_summary": extraction_summary,
            "resume_id": resume_id if result.success else None
        }
        
    except Exception as e:
        logger.error(f"Enhanced text processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/resume/{resume_id}/enhanced")
async def get_resume_enhanced(resume_id: str):
    """
    Retrieve enhanced processed resume data by ID.
    
    Args:
        resume_id: Resume identifier
        
    Returns:
        Enhanced processed resume JSON with metadata
    """
    try:
        json_path = DATA_DIR / f"{resume_id}.json"
        
        if not json_path.exists():
            raise HTTPException(status_code=404, detail="Resume not found")
        
        async with aiofiles.open(json_path, 'r') as f:
            data = await f.read()
            
        resume_data = json.loads(data)
        
        # Add enhanced metadata if available
        enhanced_metadata = {
            "extraction_method": "enhanced",
            "processing_timestamp": datetime.now().isoformat(),
            "file_size": json_path.stat().st_size,
            "enhanced_features": {
                "ocr_processed": True,
                "hidden_links_detected": True,
                "metadata_extracted": True,
                "tables_extracted": True,
                "image_ocr_processed": True
            }
        }
        
        resume_data["enhanced_metadata"] = enhanced_metadata
            
        return JSONResponse(content=resume_data)
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Resume not found")
    except Exception as e:
        logger.error(f"Failed to retrieve enhanced resume {resume_id}: {e}")
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
async def list_resumes(
    user_id: Optional[str] = None, 
    limit: int = 50,
    enhanced_only: bool = Query(default=False, description="Show only enhanced processed resumes")
):
    """
    List processed resumes.
    
    Args:
        user_id: Filter by user ID (optional)
        limit: Maximum number of results
        enhanced_only: Show only enhanced processed resumes
        
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
                
                # Filter by enhanced processing if requested
                if enhanced_only and "enhanced" not in resume_id:
                    continue
                
                # Get file metadata
                stat = json_file.stat()
                
                # Load basic resume info
                async with aiofiles.open(json_file, 'r') as f:
                    data = json.loads(await f.read())
                
                # Determine processing type
                processing_type = "enhanced" if "enhanced" in resume_id else "standard"
                
                resume_info = {
                    "resume_id": resume_id,
                    "user_id": file_user_id,
                    "processing_type": processing_type,
                    "filename": data.get("contact", {}).get("name", "Unknown") + ".json",
                    "processing_confidence": data.get("parsing_confidence", 0.0),
                    "sections_detected": data.get("sections_detected", []),
                    "domains": data.get("domains", []),
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "file_size": stat.st_size
                }
                
                # Add enhanced features info if available
                if processing_type == "enhanced":
                    resume_info["enhanced_features"] = {
                        "ocr_processed": True,
                        "hidden_links_detected": True,
                        "metadata_extracted": True,
                        "tables_extracted": True,
                        "image_ocr_processed": True
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
    return {
        "standard_pipeline": processor.get_pipeline_info(),
        "enhanced_pipeline": {
            "name": "Enhanced Resume Processing Pipeline",
            "version": "2.0.0",
            "features": [
                "Advanced PDF parsing with PyMuPDF",
                "OCR text extraction with pytesseract",
                "Hidden link detection from annotations",
                "Metadata extraction from PDF properties",
                "Table extraction and parsing",
                "Image OCR for embedded graphics",
                "Enhanced contact information extraction",
                "Improved skill and domain detection",
                "Project and certification extraction",
                "Confidence scoring with metadata"
            ],
            "dependencies": [
                "PyMuPDF (fitz)",
                "pytesseract",
                "opencv-python",
                "Pillow",
                "numpy",
                "spacy",
                "fuzzywuzzy"
            ]
        }
    }


@app.get("/enhanced/status")
async def get_enhanced_status():
    """Get enhanced processing system status."""
    return {
        "status": "operational",
        "enhanced_features": {
            "ocr_available": True,
            "hidden_link_detection": True,
            "metadata_extraction": True,
            "table_extraction": True,
            "image_ocr": True
        },
        "processing_options": {
            "enable_ocr": True,
            "enable_hidden_links": True,
            "enable_metadata": True,
            "enable_tables": True,
            "enable_image_ocr": True,
            "enable_llm_enhancement": False
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
