# TalentSync Resume Service

The Resume Service handles resume parsing, skill extraction, and candidate profile generation for the TalentSync platform.

## Features

- Resume file upload and parsing (PDF, DOCX, TXT)
- Skill extraction using NLP and keyword matching
- Experience timeline analysis
- Education background parsing
- Project and certification extraction
- Resume embedding generation for semantic search
- Resume similarity scoring

## API Endpoints

### Resume Management
- `POST /api/v1/resume/upload` - Upload and parse resume file
- `GET /api/v1/resume/{resume_id}` - Get parsed resume data
- `PUT /api/v1/resume/{resume_id}` - Update resume information
- `DELETE /api/v1/resume/{resume_id}` - Delete resume
- `GET /api/v1/resume/user/{user_id}` - Get resumes for a user

### Skill Analysis
- `GET /api/v1/resume/{resume_id}/skills` - Extract skills from resume
- `POST /api/v1/resume/{resume_id}/skills/match` - Match skills against job requirements
- `GET /api/v1/resume/{resume_id}/experience` - Parse work experience

### Resume Search
- `POST /api/v1/resume/search` - Semantic search across resumes
- `POST /api/v1/resume/similarity` - Find similar resumes
- `GET /api/v1/resume/stats` - Resume database statistics

### Health Check
- `GET /api/v1/health` - Service health status

## Supported File Formats

- **PDF**: Full text extraction with layout preservation
- **DOCX**: Microsoft Word document parsing
- **TXT**: Plain text resume files

## Environment Variables

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/talentsync_resumes
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760  # 10MB
OPENAI_API_KEY=your-openai-api-key
ALLOWED_ORIGINS=["http://localhost:3000"]
ALLOWED_HOSTS=["localhost", "127.0.0.1"]
```

## Resume Parsing Pipeline

1. **File Upload**: Accept and validate resume files
2. **Text Extraction**: Extract text content from various formats
3. **Section Identification**: Identify resume sections (experience, education, skills)
4. **Entity Extraction**: Extract structured data (dates, companies, skills)
5. **Skill Matching**: Match extracted skills against known skill databases
6. **Embedding Generation**: Create vector embeddings for semantic search
7. **Storage**: Store parsed data and embeddings in PostgreSQL

## Database Schema

The service uses the following main tables:
- `resumes` - Resume metadata and file information
- `resume_sections` - Parsed resume sections (experience, education, etc.)
- `extracted_skills` - Skills extracted from resumes
- `resume_embeddings` - Vector embeddings for semantic search

## NLP and AI Features

- **Skill Extraction**: Uses NLP models to identify technical and soft skills
- **Experience Parsing**: Extracts job titles, companies, and date ranges
- **Education Analysis**: Identifies degrees, institutions, and graduation dates
- **Semantic Search**: Vector embeddings for finding similar resumes
- **Job Matching**: Compatibility scoring against job descriptions

## File Processing

- Secure file upload with validation
- Multiple format support (PDF, DOCX, TXT)
- Automatic text cleaning and preprocessing
- Error handling for corrupted or invalid files
- File size limits and security checks

## Getting Started

1. Set environment variables
2. Create upload directory: `mkdir uploads`
3. Install dependencies: `pip install -e .`
4. Run migrations: `alembic upgrade head`
5. Start service: `uvicorn app.main:app --reload --port 8003`

## Development

The service follows these architectural patterns:
- Clean separation of parsing logic and storage
- Async processing for large file uploads
- Structured error handling and logging
- Comprehensive input validation
- Modular design for easy extension

## Integration

The Resume Service integrates with:
- **User Service**: For user authentication and profile linking
- **Interview Service**: For resume-driven question generation
- **Vector databases**: For semantic search capabilities

## Testing

Run tests with:
```bash
pytest tests/
```

Upload test resumes to `/uploads` directory for development testing.
