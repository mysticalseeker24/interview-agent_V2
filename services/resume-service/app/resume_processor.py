"""
Unified Resume Processing Pipeline
Main orchestrator for the text-to-JSON conversion process.

Directory Structure:
- data/: Uploaded resume files
- data/test_files/: Extracted text files (.txt)
- data/output/: Final JSON outputs
"""
import logging
import time
import json
import shutil
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from app.schema import ProcessingResult, ResumeJSON
from app.pipeline.text_extractor import TextExtractor
from app.pipeline.unified_extractor import UnifiedExtractor
from app.pipeline.json_formatter import JSONFormatter

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ResumeProcessor:
    """
    Main pipeline orchestrator that converts uploaded resumes to structured JSON.
    
    Pipeline Flow:
    [Upload] → [data/] → [Text Extraction] → [data/test_files/*.txt] → 
    [Entity Extraction] → [JSON Formatting] → [data/output/*.json]
    """
    
    def __init__(self, use_llm: Optional[bool] = None, openai_api_key: Optional[str] = None):
        """
        Initialize the processing pipeline.
        
        Args:
            use_llm: Whether to use LLM for enhanced extraction (overrides env var)
            openai_api_key: OpenAI API key for LLM features (overrides env var)
        """
        # Use environment variables if not explicitly provided
        if use_llm is None:
            use_llm = os.getenv('USE_LLM_ENHANCEMENT', 'false').lower() == 'true'
        
        if openai_api_key is None:
            openai_api_key = os.getenv('OPENAI_API_KEY')
        
        self.text_extractor = TextExtractor()
        self.unified_extractor = UnifiedExtractor(use_llm=use_llm, openai_api_key=openai_api_key)
        self.json_formatter = JSONFormatter()
        self.use_llm = use_llm
        self.openai_api_key = openai_api_key
        
        # Setup directory structure
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / os.getenv('DATA_DIR', 'data')
        self.test_files_dir = self.base_dir / os.getenv('TEST_FILES_DIR', 'data/test_files')
        self.output_dir = self.base_dir / os.getenv('OUTPUT_DIR', 'data/output')
        
        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.test_files_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info(f"Resume processor initialized (LLM: {use_llm}, API Key: {'***' if openai_api_key else 'None'})")
    
    def upload_and_process(self, source_file_path: str, resume_name: Optional[str] = None) -> ProcessingResult:
        """
        Upload a resume file to data directory and process it through the complete pipeline.
        
        Args:
            source_file_path: Path to the original resume file
            resume_name: Optional custom name for the resume (will use original filename if not provided)
            
        Returns:
            ProcessingResult with success status and extracted data
        """
        source_path = Path(source_file_path)
        if not source_path.exists():
            return ProcessingResult(
                success=False,
                error_message=f"Source file not found: {source_file_path}",
                processing_time=0.0
            )
        
        # Determine target filename
        if resume_name:
            file_extension = source_path.suffix
            target_filename = f"{resume_name}{file_extension}"
        else:
            target_filename = source_path.name
        
        # Copy file to data directory
        target_path = self.data_dir / target_filename
        try:
            shutil.copy2(source_path, target_path)
            logger.info(f"Uploaded resume to: {target_path}")
        except Exception as e:
            return ProcessingResult(
                success=False,
                error_message=f"Failed to upload file: {str(e)}",
                processing_time=0.0
            )
        
        # Process the uploaded file
        return self.process_resume(str(target_path))
    
    def process_resume(self, file_path: str) -> ProcessingResult:
        """
        Process a resume file through the complete pipeline.
        Saves extracted text to test_files/ and JSON output to output/
        
        Args:
            file_path: Path to the resume file in data directory
            
        Returns:
            ProcessingResult with success status and extracted data
        """
        start_time = time.time()
        stages_completed = []
        
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return ProcessingResult(
                    success=False,
                    error_message=f"File not found: {file_path}",
                    processing_time=time.time() - start_time
                )
            
            logger.info(f"Starting resume processing for: {file_path}")
            
            # Stage 1: Text Extraction
            logger.info("Stage 1: Extracting text from file")
            extraction_result = self.text_extractor.extract_text(file_path)
            
            # Handle both tuple and string returns for backward compatibility
            if isinstance(extraction_result, tuple):
                extracted_text, extraction_method = extraction_result
            else:
                extracted_text = extraction_result
                extraction_method = "unknown"
            
            if not extracted_text or len(extracted_text.strip()) < 50:
                return ProcessingResult(
                    success=False,
                    error_message="Insufficient text extracted from file",
                    processing_time=time.time() - start_time
                )
            
            stages_completed.append("text_extraction")
            
            # Save extracted text to test_files directory
            base_name = file_path_obj.stem
            text_file_path = self.test_files_dir / f"{base_name}.txt"
            
            try:
                with open(text_file_path, 'w', encoding='utf-8') as f:
                    f.write(extracted_text)
                logger.info(f"Saved extracted text to: {text_file_path}")
            except Exception as e:
                logger.warning(f"Failed to save text file: {e}")
            
            # Stage 2: Entity Extraction
            logger.info("Stage 2: Extracting entities and structuring data")
            extracted_entities = self.unified_extractor.extract_all(extracted_text)
            stages_completed.append("entity_extraction")
            
            # Stage 3: JSON Formatting
            logger.info("Stage 3: Formatting to JSON schema")
            resume_json = self.json_formatter.format_to_json(
                extracted_entities, 
                len(extracted_text),  # Pass length, not the text itself
                extraction_method=extraction_method
            )
            stages_completed.append("json_formatting")
            
            # Save JSON output to output directory
            json_file_path = self.output_dir / f"{base_name}.json"
            
            try:
                with open(json_file_path, 'w', encoding='utf-8') as f:
                    # Use Pydantic's model_dump with proper serialization
                    json_data = resume_json.model_dump(mode='json')
                    json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)
                logger.info(f"Saved JSON output to: {json_file_path}")
            except Exception as e:
                logger.warning(f"Failed to save JSON file: {e}")
            
            processing_time = time.time() - start_time
            logger.info(f"Resume processing completed successfully in {processing_time:.2f}s")
            
            return ProcessingResult(
                success=True,
                data=resume_json,
                processing_time=processing_time,
                stages_completed=stages_completed,
                text_file_path=str(text_file_path),
                json_file_path=str(json_file_path)
            )
            
        except Exception as e:
            logger.error(f"Resume processing failed: {str(e)}", exc_info=True)
            return ProcessingResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time,
                stages_completed=stages_completed
            )
    
    def process_text(self, text: str) -> ProcessingResult:
        """
        Process raw text directly (skip text extraction stage).
        
        Args:
            text: Raw resume text
            
        Returns:
            ProcessingResult with extracted data
        """
        start_time = time.time()
        stages_completed = ["text_provided"]
        
        try:
            logger.info(f"Processing raw text: {len(text)} characters")
            
            # Stage 2: Unified Entity Extraction
            logger.info("Stage 2: Unified Entity Extraction")
            extracted_data = self.unified_extractor.extract_all(text)
            stages_completed.append("entity_extraction")
            
            # Stage 3: JSON Formatting
            logger.info("Stage 3: JSON Formatting")
            resume_json = self.json_formatter.format_to_json(
                extracted_data, 
                len(text),
                extraction_method="direct_text"
            )
            stages_completed.append("json_formatting")
            
            processing_time = time.time() - start_time
            
            logger.info(f"Text processing completed in {processing_time:.2f}s")
            
            return ProcessingResult(
                success=True,
                data=resume_json,
                processing_time=processing_time,
                stages_completed=stages_completed
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Text processing failed: {str(e)}"
            
            logger.error(error_msg)
            
            return ProcessingResult(
                success=False,
                error_message=error_msg,
                processing_time=processing_time,
                stages_completed=stages_completed
            )
    
    def get_pipeline_info(self) -> dict:
        """Get information about the current pipeline configuration."""
        return {
            "pipeline_version": "1.0.0",
            "use_llm": self.use_llm,
            "supported_formats": ['.docx', '.doc', '.pdf', '.txt'],
            "stages": [
                "text_extraction",
                "entity_extraction", 
                "json_formatting"
            ],
            "confidence_factors": [
                "contact_info_completeness",
                "section_detection_quality",
                "experience_detail_richness",
                "skills_categorization",
                "overall_data_coherence"
            ],
            "directories": {
                "data": str(self.data_dir),
                "test_files": str(self.test_files_dir),
                "output": str(self.output_dir)
            }
        }
