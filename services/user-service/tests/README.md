# TalentSync User Service - Testing Guide

This directory contains comprehensive integration tests for the TalentSync User Service, designed to test the complete authentication and user management flows against the live Supabase backend.

## Test Structure

### Test Files

- **`conftest.py`**: Pytest configuration with fixtures for async testing, HTTP client, and cleanup
- **`test_auth.py`**: Authentication flow tests (signup, login, logout, get current user)
- **`test_users.py`**: User profile management tests (get profile, update profile)
- **`test_integration.py`**: Comprehensive integration tests including error scenarios and edge cases

### Test Coverage

The test suite covers:

#### Authentication Flow
- ✅ User registration (signup)
- ✅ User login with valid credentials
- ✅ Get current user information
- ✅ User logout
- ✅ Duplicate signup prevention
- ✅ Invalid login handling
- ✅ Authentication token validation

#### User Profile Management
- ✅ Get user profile
- ✅ Update user profile
- ✅ Profile update validation
- ✅ Protected endpoint access control

#### Service Health
- ✅ Root endpoint information
- ✅ Health check endpoint
- ✅ Metrics endpoint (Prometheus)
- ✅ Readiness check endpoint

#### Error Handling
- ✅ Invalid authentication tokens
- ✅ Missing authentication headers
- ✅ Invalid request data
- ✅ Duplicate user registration
- ✅ Non-existent user login

## Environment Setup

### Required Environment Variables

Make sure these variables are set in your `.env` file:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Security
SECRET_KEY=your-secret-key

# Test Configuration (optional - defaults provided)
TEST_EMAIL=integration_test@example.com
TEST_PASSWORD=TestPass123
TEST_FULL_NAME=Integration Test
```

### Dependencies

The testing dependencies are already included in `requirements.txt`:

- `pytest==7.4.3`
- `pytest-asyncio==0.21.1`
- `pytest-httpx==0.24.0`
- `httpx==0.24.1`

## Running Tests

### Using the Test Runner Script

The easiest way to run tests is using the provided test runner:

```bash
# Run all tests
python test_runner.py

# Run specific test types
python test_runner.py --type auth
python test_runner.py --type users
python test_runner.py --type integration

# Run with verbose output
python test_runner.py --verbose
```

### Using pytest Directly

```bash
# Run all tests
pytest

# Run specific test files
pytest tests/test_auth.py
pytest tests/test_users.py
pytest tests/test_integration.py

# Run with verbose output
pytest -v

# Run specific test functions
pytest tests/test_auth.py::test_signup_login_logout
```

### Using pytest with Markers

```bash
# Run only authentication tests
pytest -m auth

# Run only user management tests
pytest -m users

# Run only integration tests
pytest -m integration

# Run all tests except integration
pytest -m "not integration"
```

## Test Cleanup

The test suite includes automatic cleanup functionality:

- **User Cleanup**: After each test run, any test users created during testing are automatically deleted from both the Supabase Auth system and the user_profiles table
- **Isolation**: Each test run is isolated, ensuring no interference between test runs
- **Idempotency**: Tests that modify data (like profile updates) revert changes to maintain test consistency

## Test Data

The tests use the following default test data (configurable via environment variables):

- **Email**: `integration_test@example.com`
- **Password**: `TestPass123`
- **Full Name**: `Integration Test`

## Expected Test Flow

1. **Setup**: Test user is created via signup
2. **Authentication**: User logs in and receives JWT token
3. **Profile Operations**: User profile is retrieved and updated
4. **Validation**: Various error scenarios are tested
5. **Cleanup**: Test user is deleted from the system

## Troubleshooting

### Common Issues

1. **Environment Variables Not Set**
   ```
   ❌ Missing required environment variables:
      - SUPABASE_URL
      - SUPABASE_ANON_KEY
   ```
   **Solution**: Ensure your `.env` file is properly configured

2. **Supabase Connection Issues**
   ```
   Failed to initialize Supabase service
   ```
   **Solution**: Check your Supabase credentials and network connectivity

3. **Test User Already Exists**
   ```
   User with this email already exists
   ```
   **Solution**: The cleanup should handle this, but you can manually delete the test user from Supabase

4. **Authentication Token Issues**
   ```
   401 Unauthorized
   ```
   **Solution**: Check that your Supabase JWT configuration is correct

### Debug Mode

To run tests with more detailed output:

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run tests with verbose output
pytest -v -s
```

### Manual Cleanup

If tests fail and leave test data behind, you can manually clean up:

```sql
-- Delete test user profile
DELETE FROM user_profiles WHERE email = 'integration_test@example.com';

-- Delete test user from auth (via Supabase dashboard)
-- Go to Authentication > Users and delete the test user
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines. The test runner script provides proper exit codes and the cleanup ensures no test data remains in the production database.

## Performance Considerations

- Tests use async/await for efficient I/O operations
- HTTP client is reused across tests for better performance
- Cleanup operations are optimized to minimize database load
- Tests are designed to run quickly while maintaining comprehensive coverage 