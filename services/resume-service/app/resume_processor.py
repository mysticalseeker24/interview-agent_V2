"""
Resume Processor - Main Pipeline Orchestrator
Coordinates the entire resume processing pipeline from file to JSON.
"""

import os
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from app.pipeline.text_extractor import TextExtractor
from app.pipeline.llm_extractor import LLMExtractor
from app.schema import ProcessingResult, ResumeJSON

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ResumeProcessor:
    """
    Advanced resume processor with improved extraction and formatting.
    Orchestrates the entire pipeline from file upload to structured JSON output.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the resume processor with LLM-based extraction.
        
        Args:
            openai_api_key: OpenAI API key for LLM extraction
        """
        # Get OpenAI API key
        if openai_api_key is None:
            openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not openai_api_key:
            raise ValueError("OpenAI API key is required for LLM-based extraction")
        
        # Initialize pipeline components
        self.text_extractor = TextExtractor()
        self.llm_extractor = LLMExtractor(openai_api_key=openai_api_key)
        
        # Configuration
        self.data_dir = Path(os.getenv('DATA_DIR', 'data'))
        self.output_dir = Path(os.getenv('OUTPUT_DIR', 'data/output'))
        self.test_files_dir = Path(os.getenv('TEST_FILES_DIR', 'data/test_files'))
        
        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        self.test_files_dir.mkdir(exist_ok=True)
        
        logger.info("ResumeProcessor initialized with LLM-based extraction")
    
    def upload_and_process(self, source_file_path: str, resume_name: Optional[str] = None) -> ProcessingResult:
        """
        Upload and process a resume file with advanced extraction.
        
        Args:
            source_file_path: Path to the source resume file
            resume_name: Optional name for the resume
            
        Returns:
            ProcessingResult with structured data
        """
        try:
            start_time = time.time()
            stages_completed = []
            
            # Stage 1: Text Extraction
            logger.info("Starting text extraction...")
            text, extraction_method = self.text_extractor.extract_text(source_file_path)
            stages_completed.append("text_extraction")
            
            if not text or len(text.strip()) < 50:
                return ProcessingResult(
                    success=False,
                    error_message="Failed to extract meaningful text from resume",
                    processing_time=time.time() - start_time,
                    stages_completed=stages_completed
                )
            
            # Save extracted text
            text_file_path = self._save_text_file(text, resume_name)
            
            # Stage 2: LLM-based Extraction
            logger.info("Starting LLM-based extraction...")
            resume_json = self.llm_extractor.extract_resume(text)
            stages_completed.append("llm_extraction")
            
            # Save JSON output
            json_file_path = self._save_json_file(resume_json, resume_name)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Processing completed in {processing_time:.2f}s with confidence: {resume_json.parsing_confidence:.1%}")
            
            return ProcessingResult(
                success=True,
                data=resume_json,
                processing_time=processing_time,
                stages_completed=stages_completed,
                text_file_path=str(text_file_path),
                json_file_path=str(json_file_path)
            )
            
        except Exception as e:
            logger.error(f"Error in upload_and_process: {e}")
            return ProcessingResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time if 'start_time' in locals() else 0.0,
                stages_completed=stages_completed if 'stages_completed' in locals() else []
            )
    
    def process_resume(self, file_path: str) -> ProcessingResult:
        """
        Process a resume file with advanced extraction techniques.
        
        Args:
            file_path: Path to the resume file
            
        Returns:
            ProcessingResult with structured data
        """
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                return ProcessingResult(
                    success=False,
                    error_message=f"File not found: {file_path}"
                )
            
            # Get file name for output
            file_name = Path(file_path).stem
            
            # Process the resume
            return self.upload_and_process(file_path, file_name)
            
        except Exception as e:
            logger.error(f"Error in process_resume: {e}")
            return ProcessingResult(
                success=False,
                error_message=str(e)
            )
    
    def process_text(self, text: str) -> ProcessingResult:
        """
        Process raw text directly with advanced extraction.
        
        Args:
            text: Raw resume text
            
        Returns:
            ProcessingResult with structured data
        """
        try:
            start_time = time.time()
            stages_completed = []
            
            if not text or len(text.strip()) < 50:
                return ProcessingResult(
                    success=False,
                    error_message="Text too short to process meaningfully"
                )
            
            # Stage 1: LLM-based Extraction
            logger.info("Starting LLM-based extraction from text...")
            resume_json = self.llm_extractor.extract_resume(text)
            stages_completed.append("llm_extraction")
            
            # Save text input and JSON output
            timestamp = int(time.time())
            text_file_path = self._save_text_file(text, f"text_input_{timestamp}")
            json_file_path = self._save_json_file(resume_json, f"text_input_{timestamp}")
            
            processing_time = time.time() - start_time
            
            logger.info(f"Text processing completed in {processing_time:.2f}s with confidence: {resume_json.parsing_confidence:.1%}")
            
            return ProcessingResult(
                success=True,
                data=resume_json,
                processing_time=processing_time,
                stages_completed=stages_completed,
                text_file_path=str(text_file_path),
                json_file_path=str(json_file_path)
            )
            
        except Exception as e:
            logger.error(f"Error in process_text: {e}")
            return ProcessingResult(
                success=False,
                error_message=str(e)
            )
    
    def get_pipeline_info(self) -> dict:
        """Get information about the processing pipeline."""
        return {
            "pipeline_version": "3.0.0",
            "components": {
                "text_extractor": "Advanced TextExtractor with fallback methods",
                "llm_extractor": "LLM-based extractor with industry-grade practices"
            },
            "capabilities": {
                "file_formats": ["PDF", "DOCX", "DOC", "TXT"],
                "extraction_methods": ["pypdf", "tika", "docx", "txt"],
                "llm_extraction": True,
                "confidence_scoring": True,
                "data_validation": True,
                "rate_limiting": True,
                "caching": True,
                "retry_logic": True
            },
            "performance": {
                "typical_processing_time": "30-60 seconds",
                "text_extraction_time": "1-3 seconds",
                "llm_extraction_time": "25-55 seconds",
                "cache_hit_time": "< 1 second"
            },
            "llm_stats": self.llm_extractor.get_extraction_stats()
        }
    
    def _save_text_file(self, text: str, name: Optional[str] = None) -> Path:
        """Save extracted text to file."""
        if not name:
            name = f"extracted_text_{int(time.time())}"
        
        text_file = self.test_files_dir / f"{name}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        logger.info(f"Text saved to: {text_file}")
        return text_file
    
    def _save_json_file(self, resume_json: ResumeJSON, name: Optional[str] = None) -> Path:
        """Save processed JSON to file."""
        if not name:
            name = f"resume_{int(time.time())}"
        
        json_file = self.output_dir / f"{name}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            f.write(resume_json.model_dump_json(indent=2))
        
        logger.info(f"JSON saved to: {json_file}")
        return json_file
