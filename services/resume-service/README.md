# Resume Processing Service

A comprehensive resume parsing service that extracts structured data from various file formats (PDF, DOCX, TXT) and converts them to standardized JSON format.

## Overview

The resume-service is a production-ready microservice designed for the TalentSync platform. It provides robust resume parsing capabilities with advanced text extraction, entity recognition using spaCy, and optional LLM enhancement for improved accuracy.

## Architecture

### Pipeline Components

1. **Text Extraction** (`TextExtractor`)
   - Multi-format support: PDF, DOCX, DOC, TXT
   - Robust extraction with fallback methods (pypdf → tika)
   - Atomic file operations for data integrity

2. **Entity Extraction** (`UnifiedExtractor`)
   - spaCy-based named entity recognition
   - Contact info, experience, education, skills, projects extraction
   - Domain detection and technology identification
   - Optional OpenAI integration for enhanced accuracy

3. **JSON Formatting** (`JsonFormatter`)
   - Structured output with consistent schema
   - Data validation and cleaning
   - Confidence scoring and metadata tracking

### Compliance with TalentSync Specs

✅ **Fully Compliant Architecture**
- Microservice design with clear separation of concerns
- RESTful API with proper HTTP status codes
- Comprehensive error handling and validation
- Environment-based configuration
- Docker containerization support

✅ **Performance Optimized**
- Async processing with FastAPI
- Efficient text extraction with fallback mechanisms
- Configurable file size limits and rate limiting
- Memory-efficient processing pipeline

✅ **Security & Reliability**
- CORS middleware for cross-origin requests
- File type validation and size limits
- Atomic file operations to prevent corruption
- Comprehensive logging and monitoring

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload` | POST | Upload and process resume files |
| `/resume/{id}` | GET | Retrieve processed resume data |
| `/resumes` | GET | List all processed resumes |
| `/delete/{id}` | DELETE | Delete a resume |
| `/process-text` | POST | Process raw text directly |
| `/pipeline/info` | GET | Get pipeline information |

## Quick Start

### Prerequisites
```bash
python -m spacy download en_core_web_lg
```

### Installation
```bash
pip install -r requirements.txt
cp env.example .env
# Configure .env with your settings
```

### Running
```bash
# Development
python main.py

# Production
uvicorn app.api:app --host 0.0.0.0 --port 8004
```

### Docker
```bash
docker build -t resume-service .
docker run -p 8004:8004 resume-service
```

## Configuration

Key environment variables:
- `USE_LLM_ENHANCEMENT`: Enable OpenAI integration
- `OPENAI_API_KEY`: OpenAI API key for LLM enhancement
- `MAX_FILE_SIZE`: Maximum file size (default: 10MB)
- `ALLOWED_EXTENSIONS`: Supported file types

## Output Schema

```json
{
  "contact": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-0123",
    "linkedin": "linkedin.com/in/johndoe",
    "location": "San Francisco, CA"
  },
  "summary": "Experienced software engineer...",
  "experience": [
    {
      "position": "Senior Software Engineer",
      "company": "Tech Corp",
      "start_date": "2020-01",
      "end_date": "2023-01",
      "technologies": ["Python", "React", "AWS"],
      "bullets": ["Led development of..."],
      "metrics": ["Improved performance by 40%"]
    }
  ],
  "education": [...],
  "skills": [...],
  "projects": [...],
  "certifications": [...],
  "domains": ["DevOps", "AI Engineering"],
  "parsing_confidence": 0.85,
  "extraction_timestamp": "2024-01-15T10:30:00Z"
}
```

## Performance Metrics

- **Text Extraction**: 1-3 seconds per document
- **Entity Extraction**: 2-5 seconds (with spaCy)
- **LLM Enhancement**: 5-15 seconds (if enabled)
- **Total Processing**: 3-20 seconds depending on document size

## Integration Points

- **User Service**: Authentication and user management
- **Media Service**: File storage and retrieval
- **Interview Service**: Resume data for interview preparation
- **Feedback Service**: Resume analysis and scoring

## Error Handling

- File format validation with detailed error messages
- Graceful degradation when spaCy model unavailable
- Comprehensive logging for debugging
- Atomic file operations to prevent data corruption

## Future Enhancements

- **Multi-language Support**: Expand beyond English
- **Advanced ML Models**: Custom NER models for specific domains
- **Real-time Processing**: WebSocket support for live updates
- **Batch Processing**: Handle multiple resumes simultaneously
- **Enhanced Analytics**: Detailed extraction confidence metrics

## License

Part of the TalentSync project.
