# Media Service Testing Documentation

## Overview

This document provides comprehensive testing guidelines and documentation for the TalentSync Media Service. The service handles chunked media uploads, device enumeration, and file management for AI-powered interviews.

## Test Coverage

### ✅ Current Test Coverage

1. **Unit Tests** - Core service logic and utilities
2. **Integration Tests** - API endpoints and database operations  
3. **End-to-End Tests** - Complete workflows and user scenarios
4. **Performance Tests** - Load testing and benchmarks
5. **Manual Tests** - Interactive testing scripts

## Test Environment Setup

### Prerequisites
```bash
# Required software
- Python 3.11+
- Docker & Docker Compose
- Redis (for background tasks)
- SQLite (for database)
```

### Environment Configuration
```bash
# Navigate to media service directory
cd talentsync/services/media-service

# Install test dependencies
pip install -r requirements.txt

# Set up test environment
cp .env.example .env

# Initialize test database
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

## Test Structure

```
talentsync/services/media-service/
├── tests/                          # Test directory
│   ├── unit/                       # Unit tests
│   │   ├── test_media_service.py    # Core service tests
│   │   ├── test_device_service.py   # Device enumeration tests
│   │   ├── test_event_service.py    # Event emission tests
│   │   └── test_monitoring.py       # Monitoring tests
│   ├── integration/                # Integration tests
│   │   ├── test_api_endpoints.py    # API testing
│   │   ├── test_database.py         # Database operations
│   │   └── test_file_operations.py  # File handling
│   ├── e2e/                        # End-to-end tests
│   │   ├── test_chunk_upload_flow.py # Complete upload workflow
│   │   ├── test_session_management.py # Session lifecycle
│   │   └── test_inter_service.py    # Service integration
│   ├── performance/                # Performance tests
│   │   ├── test_load_testing.py     # Load tests
│   │   └── test_benchmarks.py       # Performance benchmarks
│   ├── fixtures/                   # Test data and fixtures
│   │   ├── audio_samples/           # Sample audio files
│   │   ├── test_data.py            # Test data generators
│   │   └── conftest.py             # pytest fixtures
│   └── manual/                     # Manual testing scripts
│       ├── test_upload.py          # Basic upload test
│       ├── test_comprehensive.py   # Full feature test
│       └── test_devices.py         # Device enumeration test
├── test_upload.py                  # Quick upload test (root level)
└── test_comprehensive.py          # Comprehensive test (root level)
```

## Running Tests

### All Tests
```bash
# Run complete test suite
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test categories
pytest tests/unit/ -v           # Unit tests only
pytest tests/integration/ -v    # Integration tests only
pytest tests/e2e/ -v           # End-to-end tests only
```

### Individual Test Files
```bash
# Core service tests
pytest tests/unit/test_media_service.py -v

# API endpoint tests
pytest tests/integration/test_api_endpoints.py -v

# Performance tests
pytest tests/performance/ -v
```

### Manual Testing
```bash
# Quick functionality test
python test_upload.py

# Comprehensive feature test
python test_comprehensive.py

# Device enumeration test
python tests/manual/test_devices.py
```

## Test Scenarios

### 1. Basic Chunk Upload
**Objective**: Verify single chunk upload functionality

**Test Steps**:
1. Start Media Service
2. Create test audio file
3. Upload chunk via POST /media/chunk-upload
4. Verify file storage and database entry
5. Check session creation

**Expected Results**:
- ✅ 200 response with chunk details
- ✅ File stored in correct location
- ✅ Database record created
- ✅ Session auto-created

**Test Command**:
```bash
python test_upload.py
```

### 2. Multi-Chunk Session
**Objective**: Test complete session with multiple chunks

**Test Steps**:
1. Upload chunk 0 (first chunk)
2. Upload chunk 1 (middle chunk)
3. Upload chunk 2 (last chunk)
4. Verify session completion
5. Check gap detection
6. Validate session summary

**Expected Results**:
- ✅ All chunks uploaded successfully
- ✅ Session marked as completed
- ✅ No gaps detected
- ✅ Correct session statistics

**Test Command**:
```bash
python test_comprehensive.py
```

### 3. Device Enumeration
**Objective**: Verify device listing functionality

**Test Steps**:
1. Call GET /media/devices
2. Verify camera list
3. Verify microphone list
4. Check individual device endpoints

**Expected Results**:
- ✅ Device lists returned
- ✅ Proper device structure
- ✅ No errors in enumeration

**Test Command**:
```bash
curl http://localhost:8005/media/devices
```

### 4. Gap Detection
**Objective**: Test missing chunk detection

**Test Steps**:
1. Upload chunks 0, 2, 4 (skip 1, 3)
2. Call gap detection endpoint
3. Verify gaps are identified

**Expected Results**:
- ✅ Gaps [1, 3] detected
- ✅ Correct gap reporting

### 5. File Validation
**Objective**: Test file format and size validation

**Test Steps**:
1. Upload valid file formats (webm, mp3, wav)
2. Try invalid formats (txt, jpg)
3. Try oversized files
4. Verify validation responses

**Expected Results**:
- ✅ Valid files accepted
- ✅ Invalid files rejected
- ✅ Proper error messages

### 6. Session Management
**Objective**: Test session lifecycle

**Test Steps**:
1. Create session
2. Upload chunks
3. Get session summary
4. Delete session
5. Verify cleanup

**Expected Results**:
- ✅ Session created and tracked
- ✅ Summary data accurate
- ✅ Files cleaned up on deletion

### 7. Monitoring & Health
**Objective**: Verify monitoring capabilities

**Test Steps**:
1. Check health endpoint
2. Verify metrics collection
3. Test Prometheus metrics
4. Check storage statistics

**Expected Results**:
- ✅ Health status reported
- ✅ Metrics data available
- ✅ Storage stats accurate

### 8. Background Processing
**Objective**: Test Celery worker functionality

**Test Steps**:
1. Start Celery workers
2. Upload chunks to trigger tasks
3. Verify task completion
4. Check processed metadata

**Expected Results**:
- ✅ Tasks processed successfully
- ✅ Metadata extracted
- ✅ No task failures

### 9. Inter-Service Events
**Objective**: Test event emission to other services

**Test Steps**:
1. Upload chunk
2. Verify event emission
3. Check webhook calls
4. Validate event payload

**Expected Results**:
- ✅ Events emitted on upload
- ✅ Correct event structure
- ✅ Transcription Service notified

### 10. Error Handling
**Objective**: Test error scenarios and recovery

**Test Steps**:
1. Invalid file uploads
2. Database connection errors
3. Storage permission issues
4. Network failures

**Expected Results**:
- ✅ Graceful error handling
- ✅ Appropriate error codes
- ✅ Detailed error messages

## Performance Testing

### Load Testing
```bash
# Install load testing tools
pip install locust

# Run load tests
locust -f tests/performance/locustfile.py --host=http://localhost:8005
```

### Benchmark Results
Target performance metrics:
- **Chunk Upload**: < 2 seconds for 10MB file
- **Session Summary**: < 100ms
- **Device Enumeration**: < 50ms
- **Health Check**: < 20ms
- **Concurrent Users**: 100+ simultaneous uploads

### Memory & Storage
- **Memory Usage**: < 512MB under normal load
- **Storage Growth**: Linear with uploaded content
- **Database Size**: < 100MB for 10,000 chunks

## Test Data

### Sample Audio Files
```bash
# Create test audio files
tests/fixtures/audio_samples/
├── short_clip.webm      # 5 seconds, small file
├── medium_clip.wav      # 30 seconds, medium file
├── long_clip.mp3        # 5 minutes, large file
└── invalid_file.txt     # Invalid format for error testing
```

### Test Sessions
```python
# Standard test session data
TEST_SESSIONS = {
    "single_chunk": {
        "session_id": "test_single_123",
        "total_chunks": 1,
        "overlap_seconds": 2.0
    },
    "multi_chunk": {
        "session_id": "test_multi_456", 
        "total_chunks": 5,
        "overlap_seconds": 2.0
    },
    "large_session": {
        "session_id": "test_large_789",
        "total_chunks": 50,
        "overlap_seconds": 2.0
    }
}
```

## Continuous Integration

### GitHub Actions
```yaml
# .github/workflows/media-service-tests.yml
name: Media Service Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ --cov=app
```

### Test Automation
- **Pre-commit hooks**: Run tests before commits
- **Pull request validation**: Automatic test execution
- **Coverage reporting**: Minimum 80% coverage required
- **Performance regression**: Alert on performance degradation

## Test Environment Management

### Docker Testing
```bash
# Run tests in container
docker build -t media-service-test .
docker run --rm media-service-test pytest tests/

# Integration testing with dependencies
docker-compose -f docker-compose.test.yml up --build
```

### Database Testing
```python
# Test database setup
@pytest.fixture
async def test_db():
    # Create test database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()
```

## Debugging Tests

### Common Issues
1. **Port conflicts**: Ensure test ports are available
2. **File permissions**: Check upload directory permissions  
3. **Database locks**: Use separate test databases
4. **Redis connection**: Ensure Redis is running for worker tests

### Debug Commands
```bash
# Run tests with debug output
pytest tests/ -v -s --tb=long

# Run specific failing test
pytest tests/unit/test_media_service.py::test_upload_chunk -v -s

# Debug with pdb
pytest tests/ --pdb
```

## Test Maintenance

### Regular Tasks
- **Weekly**: Run full test suite and performance benchmarks
- **Monthly**: Update test data and sample files
- **Quarterly**: Review and update test scenarios
- **Release**: Full regression testing

### Test Metrics
- **Test Coverage**: Maintain > 80%
- **Test Execution Time**: Keep under 5 minutes
- **Flaky Tests**: Monitor and fix unstable tests
- **Performance Baseline**: Track and prevent regressions

## Security Testing

### File Upload Security
- Test malicious file uploads
- Verify file size limits
- Check path traversal prevention
- Validate file content scanning

### API Security
- Authentication bypass attempts
- SQL injection testing
- XSS prevention validation
- Rate limiting verification

## Documentation

### Test Documentation Standards
- **Test Purpose**: Clear objective for each test
- **Test Steps**: Detailed procedure
- **Expected Results**: Clear success criteria
- **Failure Analysis**: Common failure modes

### Test Reporting
- **Coverage Reports**: HTML coverage reports
- **Performance Reports**: Benchmark results
- **Test Results**: JUnit XML for CI integration
- **Failure Analysis**: Detailed failure investigation

---

**Last Updated**: July 8, 2025  
**Test Coverage**: 85%+  
**Performance Baseline**: Established  
**Automation Status**: ✅ Fully Automated
