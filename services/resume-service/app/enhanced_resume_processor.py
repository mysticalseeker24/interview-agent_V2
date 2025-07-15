"""
Enhanced Resume Processor
Uses advanced extraction techniques to extract every detail from resumes.
"""
import logging
import os
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from app.schema import ProcessingResult, ResumeJSON
from app.pipeline.advanced_text_extractor import AdvancedTextExtractor
from app.pipeline.enhanced_unified_extractor import EnhancedUnifiedExtractor
from app.pipeline.json_formatter import JSONFormatter

logger = logging.getLogger(__name__)


class EnhancedResumeProcessor:
    """
    Enhanced resume processor that extracts every detail from resumes.
    
    Features:
    - Advanced text extraction with OCR support
    - Hidden link detection from PDF annotations and metadata
    - Table and form field extraction
    - Image analysis for embedded text
    - Enhanced entity extraction with metadata processing
    - Comprehensive link and social media profile extraction
    """
    
    def __init__(self, use_llm: Optional[bool] = None, openai_api_key: Optional[str] = None):
        """
        Initialize the enhanced resume processor.
        
        Args:
            use_llm: Whether to use LLM enhancement (defaults to env var)
            openai_api_key: OpenAI API key for LLM enhancement
        """
        # Load configuration from environment
        self.use_llm = use_llm if use_llm is not None else os.getenv('USE_LLM_ENHANCEMENT', 'false').lower() == 'true'
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        # Processing options
        self.processing_options = {
            'enable_ocr': True,
            'enable_hidden_links': True,
            'enable_metadata': True,
            'enable_tables': True,
            'enable_image_ocr': True,
            'enable_llm_enhancement': self.use_llm
        }
        
        # Extraction summary storage
        self.last_extraction_summary = {}
        
        # Initialize pipeline components
        self.text_extractor = AdvancedTextExtractor()
        self.unified_extractor = EnhancedUnifiedExtractor(
            use_llm=self.use_llm,
            openai_api_key=self.openai_api_key
        )
        self.json_formatter = JSONFormatter()
        
        # Setup directories
        self.data_dir = Path(os.getenv('DATA_DIR', 'data'))
        self.test_files_dir = self.data_dir / os.getenv('TEST_FILES_DIR', 'test_files')
        self.output_dir = self.data_dir / os.getenv('OUTPUT_DIR', 'output')
        
        # Ensure directories exist
        self.test_files_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Enhanced Resume Processor initialized with LLM: {self.use_llm}")
    
    def set_processing_options(self, **options):
        """
        Set processing options for enhanced extraction.
        
        Args:
            **options: Processing options to set
                - enable_ocr: Enable OCR for text extraction
                - enable_hidden_links: Enable hidden link detection
                - enable_metadata: Enable metadata extraction
                - enable_tables: Enable table extraction
                - enable_image_ocr: Enable OCR for embedded images
                - enable_llm_enhancement: Enable LLM enhancement
        """
        for key, value in options.items():
            if key in self.processing_options:
                self.processing_options[key] = value
                logger.info(f"Set processing option {key}: {value}")
        
        # Update LLM setting if changed
        if 'enable_llm_enhancement' in options:
            self.use_llm = options['enable_llm_enhancement']
            self.unified_extractor.use_llm = self.use_llm
    
    def get_extraction_summary(self) -> Dict[str, Any]:
        """
        Get the last extraction summary.
        
        Returns:
            Dictionary containing extraction summary information
        """
        return self.last_extraction_summary.copy()
    
    def upload_and_process(self, source_file_path: str, resume_name: Optional[str] = None) -> ProcessingResult:
        """
        Upload and process a resume file with enhanced extraction.
        
        Args:
            source_file_path: Path to the resume file
            resume_name: Optional name for the resume
            
        Returns:
            ProcessingResult with enhanced extraction results
        """
        start_time = time.time()
        stages_completed = []
        
        try:
            logger.info(f"Starting enhanced processing of: {source_file_path}")
            
            # Configure text extractor with processing options
            self.text_extractor.set_processing_options(**self.processing_options)
            
            # Stage 1: Advanced Text Extraction
            logger.info("Stage 1: Advanced Text Extraction")
            text, extraction_method, metadata = self.text_extractor.extract_text(source_file_path)
            stages_completed.append("advanced_text_extraction")
            
            # Save extracted text
            text_file_path = self._save_text_file(text, resume_name or Path(source_file_path).stem)
            
            # Stage 2: Enhanced Entity Extraction
            logger.info("Stage 2: Enhanced Entity Extraction")
            extracted_data = self.unified_extractor.extract_all_enhanced(text, metadata)
            stages_completed.append("enhanced_entity_extraction")
            
            # Stage 3: JSON Formatting with Enhanced Data
            logger.info("Stage 3: Enhanced JSON Formatting")
            resume_json = self.json_formatter.format_to_json_enhanced(
                extracted_data, 
                len(text), 
                extraction_method,
                metadata
            )
            stages_completed.append("enhanced_json_formatting")
            
            # Save JSON output
            json_file_path = self._save_json_file(resume_json, resume_name or Path(source_file_path).stem)
            
            processing_time = time.time() - start_time
            
            # Create comprehensive result
            result = ProcessingResult(
                success=True,
                data=resume_json,
                processing_time=processing_time,
                stages_completed=stages_completed,
                text_file_path=str(text_file_path),
                json_file_path=str(json_file_path)
            )
            
            # Store extraction summary
            self.last_extraction_summary = self._create_extraction_summary(result, metadata)
            
            # Log extraction summary
            self._log_extraction_summary(result, metadata)
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced processing failed: {str(e)}")
            return ProcessingResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time,
                stages_completed=stages_completed
            )
    
    def process_resume(self, file_path: str) -> ProcessingResult:
        """
        Process a resume file with enhanced extraction.
        
        Args:
            file_path: Path to the resume file
            
        Returns:
            ProcessingResult with enhanced extraction results
        """
        return self.upload_and_process(file_path)
    
    def process_text(self, text: str) -> ProcessingResult:
        """
        Process raw text with enhanced extraction.
        
        Args:
            text: Raw text to process
            
        Returns:
            ProcessingResult with enhanced extraction results
        """
        start_time = time.time()
        stages_completed = []
        
        try:
            logger.info("Processing raw text with enhanced extraction")
            
            # Create mock metadata for text processing
            metadata = {
                'links': [],
                'tables': [],
                'form_fields': [],
                'annotations': [],
                'hidden_text': [],
                'metadata': {}
            }
            
            # Extract links from text
            text_links = self.text_extractor._extract_links_from_text(text)
            metadata['links'] = text_links
            
            # Stage 1: Enhanced Entity Extraction
            logger.info("Stage 1: Enhanced Entity Extraction")
            extracted_data = self.unified_extractor.extract_all_enhanced(text, metadata)
            stages_completed.append("enhanced_entity_extraction")
            
            # Stage 2: Enhanced JSON Formatting
            logger.info("Stage 2: Enhanced JSON Formatting")
            resume_json = self.json_formatter.format_to_json_enhanced(
                extracted_data, 
                len(text), 
                "text_input",
                metadata
            )
            stages_completed.append("enhanced_json_formatting")
            
            # Save JSON output
            json_file_path = self._save_json_file(resume_json, f"text_input_{int(time.time())}")
            
            processing_time = time.time() - start_time
            
            result = ProcessingResult(
                success=True,
                data=resume_json,
                processing_time=processing_time,
                stages_completed=stages_completed,
                json_file_path=str(json_file_path)
            )
            
            # Store extraction summary
            self.last_extraction_summary = self._create_extraction_summary(result, metadata)
            
            # Log extraction summary
            self._log_extraction_summary(result, metadata)
            
            return result
            
        except Exception as e:
            logger.error(f"Text processing failed: {str(e)}")
            return ProcessingResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time,
                stages_completed=stages_completed
            )
    
    def _create_extraction_summary(self, result: ProcessingResult, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a comprehensive extraction summary.
        
        Args:
            result: Processing result
            metadata: Extraction metadata
            
        Returns:
            Dictionary containing extraction summary
        """
        if not result.success or not result.data:
            return {"error": "Processing failed"}
        
        data = result.data
        
        summary = {
            "processing_time": result.processing_time,
            "text_length": data.raw_text_length,
            "confidence": data.parsing_confidence,
            "sections_detected": data.sections_detected,
            "contact_info": {
                "name": data.contact.name,
                "email": data.contact.email,
                "phone": data.contact.phone,
                "linkedin": data.contact.linkedin,
                "github": data.contact.github,
                "website": data.contact.website
            },
            "extracted_data": {
                "experience_count": len(data.experience),
                "projects_count": len(data.projects),
                "education_count": len(data.education),
                "skills_count": len(data.skills),
                "certifications_count": len(data.certifications),
                "achievements_count": len(data.achievements)
            },
            "hidden_elements": {
                "links_found": len(metadata.get('links', [])),
                "tables_found": len(metadata.get('tables', [])),
                "form_fields_found": len(metadata.get('form_fields', [])),
                "images_found": len(metadata.get('images', [])),
                "hidden_text_found": len(metadata.get('hidden_text', []))
            },
            "social_profiles": [
                {
                    "platform": link.get('platform', 'unknown'),
                    "username": link.get('username', ''),
                    "url": link.get('url', '')
                }
                for link in metadata.get('links', [])
                if link.get('type') == 'social_media'
            ],
            "domains": data.domains,
            "llm_enhanced": data.llm_enhanced,
            "processing_options": self.processing_options.copy()
        }
        
        return summary
    
    def _save_text_file(self, text: str, filename: str) -> Path:
        """Save extracted text to file."""
        text_file_path = self.test_files_dir / f"{filename}.txt"
        
        with open(text_file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        logger.info(f"Saved extracted text to: {text_file_path}")
        return text_file_path
    
    def _save_json_file(self, resume_json: ResumeJSON, filename: str) -> Path:
        """Save processed JSON to file."""
        json_file_path = self.output_dir / f"{filename}.json"
        
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(resume_json.dict(), f, indent=2, default=str)
        
        logger.info(f"Saved JSON output to: {json_file_path}")
        return json_file_path
    
    def _log_extraction_summary(self, result: ProcessingResult, metadata: Dict[str, Any]):
        """Log a comprehensive summary of the extraction results."""
        if not result.success or not result.data:
            return
        
        data = result.data
        
        logger.info("=" * 80)
        logger.info("ENHANCED EXTRACTION SUMMARY")
        logger.info("=" * 80)
        
        # Basic stats
        logger.info(f"📊 Processing Time: {result.processing_time:.2f}s")
        logger.info(f"📝 Text Length: {data.raw_text_length:,} characters")
        logger.info(f"🎯 Confidence: {data.parsing_confidence:.2%}")
        logger.info(f"🏷️ Sections Detected: {', '.join(data.sections_detected)}")
        
        # Contact information
        contact = data.contact
        logger.info(f"👤 Contact: {contact.name or 'N/A'}")
        logger.info(f"📧 Email: {contact.email or 'N/A'}")
        logger.info(f"📱 Phone: {contact.phone or 'N/A'}")
        logger.info(f"🔗 LinkedIn: {contact.linkedin or 'N/A'}")
        logger.info(f"💻 GitHub: {contact.github or 'N/A'}")
        logger.info(f"🌐 Website: {contact.website or 'N/A'}")
        
        # Experience and projects
        logger.info(f"💼 Experience: {len(data.experience)} entries")
        logger.info(f"🚀 Projects: {len(data.projects)} entries")
        logger.info(f"🎓 Education: {len(data.education)} entries")
        logger.info(f"🛠️ Skills: {len(data.skills)} categories")
        logger.info(f"🏆 Certifications: {len(data.certifications)} entries")
        logger.info(f"🏅 Achievements: {len(data.achievements)} entries")
        
        # Hidden elements from metadata
        if metadata:
            logger.info(f"🔗 Links Found: {len(metadata.get('links', []))}")
            logger.info(f"📊 Tables Found: {len(metadata.get('tables', []))}")
            logger.info(f"📝 Form Fields: {len(metadata.get('form_fields', []))}")
            logger.info(f"🖼️ Images Found: {len(metadata.get('images', []))}")
            logger.info(f"📄 Hidden Text: {len(metadata.get('hidden_text', []))}")
            
            # Social media profiles
            social_profiles = [
                link for link in metadata.get('links', []) 
                if link.get('type') == 'social_media'
            ]
            if social_profiles:
                logger.info(f"📱 Social Profiles: {len(social_profiles)}")
                for profile in social_profiles:
                    platform = profile.get('platform', 'unknown')
                    username = profile.get('username', '')
                    logger.info(f"   - {platform}: {username}")
        
        # Domains detected
        if data.domains:
            logger.info(f"🎯 Professional Domains: {', '.join(data.domains)}")
        
        # LLM enhancement status
        if data.llm_enhanced:
            logger.info("🤖 LLM Enhancement: Applied")
        
        logger.info("=" * 80)
    
    def get_pipeline_info(self) -> dict:
        """Get information about the enhanced pipeline."""
        return {
            "pipeline_name": "Enhanced Resume Processing Pipeline",
            "version": "2.0.0",
            "description": "Advanced resume parsing with OCR, hidden link detection, and comprehensive metadata extraction",
            "stages": [
                {
                    "name": "Advanced Text Extraction",
                    "description": "Multi-format extraction with OCR support and hidden element detection",
                    "capabilities": [
                        "PDF parsing with PyMuPDF",
                        "OCR for scanned documents",
                        "Hidden link extraction",
                        "Table and form field detection",
                        "Image analysis for embedded text"
                    ]
                },
                {
                    "name": "Enhanced Entity Extraction",
                    "description": "Comprehensive entity extraction using metadata and advanced NLP",
                    "capabilities": [
                        "Contact information with social media profiles",
                        "Experience extraction from tables and text",
                        "Project detection from URLs and descriptions",
                        "Skills categorization with fuzzy matching",
                        "Domain detection from multiple sources"
                    ]
                },
                {
                    "name": "Enhanced JSON Formatting",
                    "description": "Structured output with comprehensive metadata",
                    "capabilities": [
                        "Enhanced schema with hidden elements",
                        "Confidence scoring with metadata",
                        "Link and social profile tracking",
                        "Table and form field preservation"
                    ]
                }
            ],
            "supported_formats": [
                "PDF (with OCR support)",
                "DOCX (with hyperlink extraction)",
                "DOC",
                "TXT",
                "Images (JPG, PNG with OCR)"
            ],
            "advanced_features": [
                "Hidden link detection from PDF annotations",
                "Social media profile extraction",
                "Table data extraction and parsing",
                "Form field extraction",
                "Document metadata extraction",
                "Image OCR for embedded text",
                "LLM enhancement for improved accuracy"
            ],
            "llm_enhancement": {
                "enabled": self.use_llm,
                "model": "o1-mini",
                "cost_optimization": "Only used when confidence < 80%"
            }
        } 