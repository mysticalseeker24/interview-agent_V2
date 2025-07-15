# Enhanced Resume Processing API

## Overview

The Enhanced Resume Processing API provides advanced resume parsing capabilities with OCR, hidden link detection, metadata extraction, and comprehensive data extraction. This API extends the standard resume processing with cutting-edge techniques to extract every detail from resumes.

## Features

### 🔍 Advanced Text Extraction
- **OCR Support**: Extract text from scanned documents and images
- **Hidden Link Detection**: Find links in PDF annotations and metadata
- **Table Extraction**: Parse structured data from tables
- **Form Field Detection**: Extract form field data
- **Image OCR**: Extract text from embedded images

### 🎯 Enhanced Entity Extraction
- **Contact Information**: Extract with social media profiles
- **Experience**: Parse from tables and text with metadata
- **Projects**: Detect from URLs and descriptions
- **Skills**: Categorize with fuzzy matching
- **Domains**: Detect from multiple sources

### 📊 Comprehensive Output
- **Enhanced JSON Schema**: Structured output with metadata
- **Confidence Scoring**: With metadata support
- **Link Tracking**: Social profile and URL extraction
- **Table Preservation**: Maintain structured data

## API Endpoints

### Health & Status

#### `GET /`
Root endpoint with service information and enhanced features.

**Response:**
```json
{
  "service": "Resume Processing Service",
  "version": "2.0.0",
  "status": "healthy",
  "enhanced_features": {
    "ocr_support": true,
    "hidden_link_detection": true,
    "metadata_extraction": true,
    "table_extraction": true,
    "image_ocr": true
  }
}
```

#### `GET /enhanced/status`
Get enhanced processing system status.

**Response:**
```json
{
  "status": "operational",
  "enhanced_features": {
    "ocr_available": true,
    "hidden_link_detection": true,
    "metadata_extraction": true,
    "table_extraction": true,
    "image_ocr": true
  },
  "processing_options": {
    "enable_ocr": true,
    "enable_hidden_links": true,
    "enable_metadata": true,
    "enable_tables": true,
    "enable_image_ocr": true,
    "enable_llm_enhancement": false
  }
}
```

### Resume Upload

#### `POST /upload`
Standard resume upload with basic processing.

**Parameters:**
- `file`: Resume file (PDF, DOCX, DOC, TXT)
- `user_id`: User identifier (optional, default: "anonymous")

#### `POST /upload/enhanced`
Enhanced resume upload with configurable processing options.

**Parameters:**
- `file`: Resume file (PDF, DOCX, DOC, TXT, JPG, PNG)
- `user_id`: User identifier (optional, default: "anonymous")
- `enable_ocr`: Enable OCR for text extraction (default: true)
- `enable_hidden_links`: Enable hidden link detection (default: true)
- `enable_metadata`: Enable metadata extraction (default: true)
- `enable_tables`: Enable table extraction (default: true)
- `enable_image_ocr`: Enable OCR for embedded images (default: true)

**Response:**
```json
{
  "success": true,
  "resume_id": "user_20240115_143022",
  "filename": "resume.pdf",
  "file_size": 245760,
  "processing_result": {
    "success": true,
    "processing_time": 2.34,
    "stages_completed": ["advanced_text_extraction", "enhanced_entity_extraction", "enhanced_json_formatting"]
  },
  "storage_path": "/path/to/resume.json",
  "enhanced_features": {
    "ocr_enabled": true,
    "hidden_links_enabled": true,
    "metadata_enabled": true,
    "tables_enabled": true,
    "image_ocr_enabled": true
  },
  "extraction_summary": {
    "processing_time": 2.34,
    "text_length": 15420,
    "confidence": 0.87,
    "contact_info": {
      "name": "John Doe",
      "email": "john.doe@email.com",
      "phone": "(555) 123-4567",
      "linkedin": "linkedin.com/in/johndoe",
      "github": "github.com/johndoe",
      "website": "johndoe.com"
    },
    "extracted_data": {
      "experience_count": 3,
      "projects_count": 5,
      "education_count": 2,
      "skills_count": 8,
      "certifications_count": 2,
      "achievements_count": 4
    },
    "hidden_elements": {
      "links_found": 12,
      "tables_found": 2,
      "form_fields_found": 0,
      "images_found": 1,
      "hidden_text_found": 3
    },
    "social_profiles": [
      {
        "platform": "linkedin",
        "username": "johndoe",
        "url": "linkedin.com/in/johndoe"
      },
      {
        "platform": "github",
        "username": "johndoe",
        "url": "github.com/johndoe"
      }
    ],
    "domains": ["Software Engineering", "Web Development", "AI/ML"],
    "llm_enhanced": false,
    "processing_options": {
      "enable_ocr": true,
      "enable_hidden_links": true,
      "enable_metadata": true,
      "enable_tables": true,
      "enable_image_ocr": true,
      "enable_llm_enhancement": false
    }
  }
}
```

### Text Processing

#### `POST /process-text/enhanced`
Process raw text with enhanced features.

**Parameters:**
- `text`: Raw resume text
- `user_id`: User identifier (optional, default: "anonymous")
- `enable_llm_enhancement`: Enable LLM enhancement (default: false)

### Resume Retrieval

#### `GET /resume/{resume_id}`
Retrieve standard processed resume data.

#### `GET /resume/{resume_id}/enhanced`
Retrieve enhanced processed resume data with metadata.

**Response includes:**
```json
{
  "enhanced_metadata": {
    "extraction_method": "enhanced",
    "processing_timestamp": "2024-01-15T14:30:22",
    "file_size": 15420,
    "enhanced_features": {
      "ocr_processed": true,
      "hidden_links_detected": true,
      "metadata_extracted": true,
      "tables_extracted": true,
      "image_ocr_processed": true
    }
  }
}
```

### Resume Listing

#### `GET /resumes`
List processed resumes with optional filters.

**Query Parameters:**
- `user_id`: Filter by user ID (optional)
- `limit`: Maximum number of results (default: 50)
- `enhanced_only`: Show only enhanced processed resumes (default: false)

### Pipeline Information

#### `GET /pipeline/info`
Get detailed pipeline information including enhanced features.

## Processing Options

### OCR Processing
- **enable_ocr**: Enable OCR for text extraction from scanned documents
- **enable_image_ocr**: Enable OCR for embedded images in PDFs

### Hidden Element Detection
- **enable_hidden_links**: Extract links from PDF annotations and metadata
- **enable_metadata**: Extract document metadata (title, author, etc.)
- **enable_tables**: Extract and parse table data

### LLM Enhancement
- **enable_llm_enhancement**: Use OpenAI API for improved extraction accuracy

## Usage Examples

### Python Client

```python
import requests

# Enhanced upload with full processing
with open('resume.pdf', 'rb') as f:
    files = {'file': ('resume.pdf', f, 'application/pdf')}
    data = {
        'user_id': 'user123',
        'enable_ocr': True,
        'enable_hidden_links': True,
        'enable_metadata': True,
        'enable_tables': True,
        'enable_image_ocr': True
    }
    
    response = requests.post('http://localhost:8004/upload/enhanced', 
                           files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Resume ID: {result['resume_id']}")
        print(f"Processing time: {result['processing_result']['processing_time']:.2f}s")
        print(f"Links found: {result['extraction_summary']['hidden_elements']['links_found']}")
        print(f"Social profiles: {len(result['extraction_summary']['social_profiles'])}")
```

### cURL Examples

```bash
# Enhanced upload
curl -X POST "http://localhost:8004/upload/enhanced" \
  -F "file=@resume.pdf" \
  -F "user_id=user123" \
  -F "enable_ocr=true" \
  -F "enable_hidden_links=true" \
  -F "enable_metadata=true" \
  -F "enable_tables=true" \
  -F "enable_image_ocr=true"

# Enhanced text processing
curl -X POST "http://localhost:8004/process-text/enhanced" \
  -F "text=John Doe Software Engineer..." \
  -F "user_id=user123" \
  -F "enable_llm_enhancement=false"

# List enhanced resumes only
curl "http://localhost:8004/resumes?enhanced_only=true&limit=10"
```

## Advanced Features

### Hidden Link Detection
The enhanced API can detect links in:
- PDF annotations and comments
- Document metadata
- Embedded hyperlinks
- Social media profiles

### Table Extraction
Extracts structured data from:
- PDF tables
- Form fields
- Structured layouts

### Image OCR
Processes embedded images for:
- Logos and graphics with text
- Scanned document sections
- Screenshots with text

### Metadata Extraction
Extracts document properties:
- Title and author
- Creation and modification dates
- Creator and producer information
- Subject and keywords

## Error Handling

The API returns appropriate HTTP status codes:
- `200`: Success
- `400`: Bad request (unsupported file type, invalid parameters)
- `413`: File too large (20MB limit for enhanced processing)
- `404`: Resume not found
- `500`: Internal server error

## Performance Considerations

- **File Size Limit**: 20MB for enhanced processing
- **Processing Time**: 2-5 seconds for typical resumes
- **OCR Processing**: May take longer for image-heavy documents
- **LLM Enhancement**: Adds 1-2 seconds when enabled

## Dependencies

The enhanced API requires:
- PyMuPDF (fitz) for advanced PDF parsing
- pytesseract for OCR processing
- opencv-python for image processing
- Pillow for image manipulation
- numpy for numerical operations
- spacy for NLP processing
- fuzzywuzzy for fuzzy string matching

## Testing

Run the comprehensive test script:

```bash
python test_enhanced_api.py
```

This will test all endpoints with various configurations and provide detailed output about the enhanced features.

## Migration from Standard API

The enhanced API is backward compatible. Existing standard endpoints continue to work while new enhanced endpoints provide additional capabilities:

1. **Standard Upload**: `POST /upload` (unchanged)
2. **Enhanced Upload**: `POST /upload/enhanced` (new)
3. **Standard Text Processing**: `POST /process-text` (unchanged)
4. **Enhanced Text Processing**: `POST /process-text/enhanced` (new)

## Future Enhancements

- **Batch Processing**: Process multiple resumes simultaneously
- **Custom Models**: Support for custom OCR and NLP models
- **Real-time Processing**: WebSocket support for streaming results
- **Advanced Analytics**: Detailed processing analytics and insights 