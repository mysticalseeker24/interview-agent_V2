# TalentSync User Service

The User Service handles authentication, user management, and profile operations for the TalentSync platform.

## Features

- User registration and authentication
- JWT token management
- User profile management
- Role-based access control (candidate, interviewer, admin)
- Password reset functionality
- OAuth2 with Password flow

## API Endpoints

### Authentication
- `POST /api/v1/auth/signup` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh JWT token
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/forgot-password` - Request password reset
- `POST /api/v1/auth/reset-password` - Reset password

### User Management
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update current user profile
- `GET /api/v1/users/{user_id}` - Get user by ID (admin only)
- `PUT /api/v1/users/{user_id}` - Update user (admin only)
- `DELETE /api/v1/users/{user_id}` - Delete user (admin only)

### Health Check
- `GET /api/v1/health` - Service health status

## Environment Variables

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/talentsync_users
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_ORIGINS=["http://localhost:3000"]
ALLOWED_HOSTS=["localhost", "127.0.0.1"]
```

## Database Schema

The service uses the following main tables:
- `users` - User accounts and basic information
- `user_profiles` - Extended user profile data
- `user_roles` - Role assignments
- `refresh_tokens` - JWT refresh token storage

## Security Features

- Password hashing using bcrypt
- JWT token authentication
- Role-based access control
- Rate limiting on authentication endpoints
- CORS configuration for frontend integration

## Getting Started

1. Set environment variables
2. Install dependencies: `pip install -e .`
3. Run migrations: `alembic upgrade head`
4. Start service: `uvicorn app.main:app --reload --port 8001`

## Development

The service follows FastAPI best practices with:
- Dependency injection for database sessions
- Pydantic models for request/response validation
- Comprehensive error handling
- Structured logging
- Health check endpoints

## Testing

Run tests with:
```bash
pytest tests/
```

API documentation is available at `/docs` when running the service.
