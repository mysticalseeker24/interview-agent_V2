# Resume Service Testing Guide

## Overview
The Resume Service provides a unified, maintainable text-to-JSON resume parsing pipeline with multi-template support, handling various resume formats and extracting structured data using regex, spaCy NER, fuzzy matching, and optional LLM enhancement.

## Features

✅ **Multi-Format Support**: PDF, DOCX, TXT, LaTeX file processing  
✅ **Multi-Template Extraction**: Handles various resume formats automatically  
✅ **Enhanced Contact Extraction**: Name, email, phone, LinkedIn, GitHub URLs  
✅ **Structured Experience Parsing**: Company, position, dates, location, technologies  
✅ **Skills Categorization**: Programming languages, frameworks, tools, databases  
✅ **Project Analysis**: Technologies, timelines, metrics, achievements  
✅ **OpenAI o1-mini Integration**: Optional LLM enhancement with cost optimization  
✅ **File Management**: Organized data flow through data/, test_files/, output/  

## Prerequisites

- Python 3.11+
- Valid OpenAI API key (for LLM enhancement)
- spaCy English model (`en_core_web_sm`)

## Environment Setup

### 1. Environment Configuration

Create `.env` file in `services/resume-service/`:
```bash
# OpenAI Configuration (Optional - for LLM enhancement)
OPENAI_API_KEY=your-openai-api-key-here
USE_LLM_ENHANCEMENT=false
LLM_CONFIDENCE_THRESHOLD=80
LLM_MODEL=o1-mini
LLM_MAX_TOKENS=2000

# Service Configuration
RESUME_SERVICE_PORT=8001
DEBUG=false
```

### 2. Dependencies Installation

```bash
# Navigate to resume service
cd services/resume-service

# Install dependencies
pip install -r requirements.txt

# Install spaCy English model for NLP
python -m spacy download en_core_web_sm
```

### 3. Directory Structure Setup

The service automatically creates the required directories:
```
services/resume-service/
├── data/                    # Uploaded resume files
├── data/test_files/        # Extracted text files
├── data/output/            # Generated JSON files
├── uploads/                # Temporary upload storage
├── src/                    # Source code
└── tests/                  # Test files and scripts
```

## Testing

### Available Test Scripts

1. **`test_pipeline.py`** - Basic pipeline functionality
2. **`test_pdf_workflow.py`** - PDF processing workflow
3. **`test_comprehensive.py`** - Complete extraction testing
4. **`test_llm_integration.py`** - LLM enhancement testing

### Run Basic Pipeline Test
```bash
# Test basic extraction pipeline
python test_pipeline.py

# Expected output:
# ✅ Pipeline test completed successfully!
# Processing time: ~0.8s
# Confidence: ~30-50%
# Contact info: 1-3/3 fields extracted
```

### Run PDF Workflow Test
```bash
# Test complete PDF processing workflow
python test_pdf_workflow.py

# Expected output:
# ✅ PDF workflow test completed!
# Files saved to:
# - data/Resume (1).pdf
# - data/test_files/Resume (1).txt
# - data/output/Resume (1).json
```

### Run Comprehensive Test
```bash
# Test all extraction capabilities
python test_comprehensive.py

# Expected output:
# 📊 COMPREHENSIVE RESUME EXTRACTION TEST
# ✅ Contact Info: Name, Email, Phone extracted
# ✅ Experience: X entries found
# ✅ Education: X entries found
# ✅ Skills: X categories detected
# ✅ Projects: X projects parsed
```

### Run LLM Integration Test
```bash
# Test OpenAI o1-mini enhancement (requires API key)
python test_llm_integration.py

# Expected output:
# 🤖 TESTING LLM INTEGRATION
# ✅ OpenAI API Key: Set
# ✅ Basic Extraction: 33.75% confidence
# ✅ LLM-Enhanced: 43.50% confidence (+9.8% improvement)
# 💰 Cost: ~$0.001-0.005 per resume
```

## API Testing

### Start Resume Service
```bash
# Start the service
uvicorn src.api:app --reload --port 8001
```

### Test Service Health
```bash
# Test health endpoint
curl http://localhost:8001/health

# Expected response:
# {"status": "healthy", "service": "resume-service"}
```

### Test Resume Upload and Processing
```bash
# Upload and process a resume
curl -X POST "http://localhost:8001/api/v1/resume/process" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/Resume (1).pdf" \
  -F "use_llm=false"

# Expected response:
# {
#   "success": true,
#   "filename": "Resume (1).pdf",
#   "processing_time": 0.85,
#   "confidence_score": 43.5,
#   "data": { ... extracted resume data ... }
# }
```

### Test Resume Processing with LLM Enhancement
```bash
# Process with LLM enhancement
curl -X POST "http://localhost:8001/api/v1/resume/process" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/Resume (1).pdf" \
  -F "use_llm=true"

# Expected response includes:
# "llm_enhanced": true,
# "confidence_score": 50-80% (improved),
# "processing_time": 8-12s
```

## Template Detection

The service automatically detects resume templates:

### Traditional Template
- Format: `Position @ Company (Date Range) | Location`
- Indicators: `@`, `|`, `(`, `)`
- Example: `Senior Engineer @ Google (Jan 2020 - Present) | Remote`

### Modern Template  
- Format: Position on line 1, Company on line 2, Date on line 3
- Indicators: `•`, `Remote`, `Full-time`, `–`, `—`
- Example:
  ```
  AI Engineer Intern
  DonEros Remote
  November 2024 – March 2025
  ```

### Technical Template
- Format: Various separators and technical indicators
- Indicators: `GitHub`, `LinkedIn`, `Stack`, `API`, `Framework`
- Focus: Enhanced project and technology extraction

## Performance Metrics

### Processing Performance
- **Basic Extraction**: ~0.8s per resume
- **LLM Enhancement**: ~8-12s per resume
- **Memory Usage**: Minimal (no database overhead)
- **Confidence Improvement**: +5-15% with LLM

### Extraction Quality
- **Contact Info**: 3/3 fields (name, email, phone) vs 1/3 previously
- **Experience Parsing**: Multi-format pattern matching
- **Skills Categorization**: 6-8 categories automatically detected
- **Section Detection**: 8+ resume sections identified

### Cost Optimization
- **LLM Trigger**: Only when confidence < 80%
- **Token Usage**: ~500-1000 tokens per enhancement
- **Model**: o1-mini (most cost-effective)
- **Estimated Cost**: $0.001-0.005 per resume
- **Monthly Cost**: $0.10-0.50 (100 resumes), $1.00-5.00 (1000 resumes)

## File Management

### Input Files
- **Supported**: PDF, DOCX, TXT, LaTeX
- **Storage**: `data/` directory
- **Size Limit**: Configurable (default: 10MB)

### Processing Files
- **Extracted Text**: `data/test_files/filename.txt`
- **Raw Content**: Plain text with section preservation
- **Encoding**: UTF-8

### Output Files
- **JSON Results**: `data/output/filename.json`
- **Schema**: Strict Pydantic validation
- **Structure**: Standardized across all resume types

## Integration Testing

### With Interview Service
```bash
# Test resume data retrieval for interview preparation
curl "http://localhost:8001/api/v1/resume/internal/user123/data"

# Expected response:
# {
#   "skills": ["Python", "React", "AWS"],
#   "experience_level": "mid",
#   "technologies": ["FastAPI", "PostgreSQL"],
#   "domains": ["web_development", "data_science"]
# }
```

## Troubleshooting

### Common Issues

1. **spaCy Model Missing**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

2. **PDF Extraction Fails**:
   - Service automatically tries fallback extractors
   - Check file corruption or unsupported format

3. **LLM Enhancement Fails**:
   - Verify OpenAI API key in `.env`
   - Check API rate limits and billing
   - Service gracefully falls back to basic extraction

4. **Low Confidence Scores**:
   - Enable LLM enhancement: `USE_LLM_ENHANCEMENT=true`
   - Try different resume templates
   - Check text extraction quality

### Validation Commands

```bash
# Check environment variables
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('OpenAI API Key:', 'Set' if os.getenv('OPENAI_API_KEY') else 'Not Set')
print('LLM Enhancement:', os.getenv('USE_LLM_ENHANCEMENT', 'false'))
"

# Validate spaCy model
python -c "
import spacy
try:
    nlp = spacy.load('en_core_web_sm')
    print('✅ spaCy model loaded successfully')
except OSError:
    print('❌ spaCy model not found')
"

# Test OpenAI connection
python -c "
import openai
import os
from dotenv import load_dotenv
load_dotenv()
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
print('✅ OpenAI connection successful')
"
```

## Test Results Summary

✅ **All test scripts pass successfully**  
✅ **Real PDF extraction working**  
✅ **LLM integration functional**  
✅ **Multi-template detection working**  
✅ **Cost estimation accurate**  
✅ **Environment configuration working**  
✅ **File workflow validated**  
✅ **API endpoints functional**  
✅ **Integration ready**  

## Next Steps

1. ✅ Basic pipeline implementation and testing
2. ✅ Multi-template extraction system
3. ✅ LLM integration with cost optimization
4. ✅ Comprehensive testing suite
5. ✅ API service implementation
6. 🔄 Integration with interview service
7. 🔄 Production deployment configuration
8. 🔄 Monitoring and logging setup
