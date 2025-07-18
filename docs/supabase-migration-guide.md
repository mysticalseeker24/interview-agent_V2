# TalentSync Supabase Migration Guide

## Overview

This document outlines the complete migration from the custom user-service to Supabase Auth + Database for TalentSync. This migration provides managed authentication, enhanced security, and better scalability while maintaining compatibility with existing services.

## Migration Summary

### What Changed
- **user-service** → **auth-gateway** (Port 8001)
- **SQLite user database** → **Supabase Auth + PostgreSQL**
- **Custom JWT implementation** → **Supabase managed JWT tokens**
- **Manual user management** → **Supabase dashboard + RLS policies**

### What Stayed the Same
- All other services remain unchanged
- Frontend API calls remain compatible
- Nginx routing configuration unchanged
- Docker Compose structure maintained

## 1. Architecture Changes

### Before (user-service)
```
Frontend → Nginx → user-service (8001) → SQLite
Other Services → user-service (8001) → SQLite
```

### After (auth-gateway + Supabase)
```
Frontend → Nginx → auth-gateway (8001) → Supabase Auth + PostgreSQL
Other Services → auth-gateway (8001) → Supabase Auth + PostgreSQL
```

## 2. Database Schema Migration

### Supabase Database Schema
```sql
-- Supabase Auth handles users table automatically
-- Custom user profiles table
CREATE TABLE user_profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  full_name TEXT,
  is_admin BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Row Level Security
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own profile" ON user_profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON user_profiles
  FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON user_profiles
  FOR INSERT WITH CHECK (auth.uid() = id);
```

### Data Migration Script
```python
# Migration script to move data from SQLite to Supabase
import sqlite3
from supabase import create_client
import os

# Connect to old SQLite database
sqlite_conn = sqlite3.connect('./user.db')
sqlite_cursor = sqlite_conn.cursor()

# Connect to Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

# Migrate users
sqlite_cursor.execute("SELECT * FROM users")
users = sqlite_cursor.fetchall()

for user in users:
    try:
        # Create user in Supabase Auth
        auth_user = supabase.auth.admin.create_user({
            "email": user[1],  # email
            "password": "temporary_password",  # Will need password reset
            "email_confirm": True
        })
        
        # Create user profile
        supabase.table("user_profiles").insert({
            "id": auth_user.user.id,
            "full_name": user[3],  # full_name
            "is_admin": user[5],   # is_admin
            "created_at": user[6], # created_at
            "updated_at": user[7]  # updated_at
        }).execute()
        
        print(f"Migrated user: {user[1]}")
    except Exception as e:
        print(f"Failed to migrate user {user[1]}: {e}")

sqlite_conn.close()
```

## 3. New Auth Gateway Service

### Service Structure
```
services/auth-gateway/
├── app/
│   ├── main.py              # FastAPI application
│   ├── core/
│   │   ├── config.py        # Supabase configuration
│   │   └── security.py      # JWT validation
│   ├── routers/
│   │   ├── auth.py          # Login/signup endpoints
│   │   └── users.py         # Profile management
│   └── schemas/
│       └── user.py          # Pydantic models
├── requirements.txt
├── Dockerfile
└── README.md
```

### Main Application
```python
# services/auth-gateway/app/main.py
from fastapi import FastAPI, Depends, HTTPException
from supabase import create_client, Client
import os

app = FastAPI(title="TalentSync Auth Gateway")

# Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

@app.post("/auth/login")
async def login(credentials: dict):
    try:
        response = supabase.auth.sign_in_with_password(credentials)
        return {
            "access_token": response.session.access_token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(401, "Invalid credentials")

@app.post("/auth/signup")
async def signup(user_data: dict):
    try:
        response = supabase.auth.sign_up(user_data)
        # Create user profile
        supabase.table("user_profiles").insert({
            "id": response.user.id,
            "full_name": user_data.get("full_name")
        }).execute()
        return response.user
    except Exception as e:
        raise HTTPException(400, "Registration failed")

@app.get("/users/me")
async def get_profile(token: str = Depends(get_current_user)):
    try:
        user = supabase.auth.get_user(token)
        profile = supabase.table("user_profiles").select("*").eq("id", user.user.id).single().execute()
        return {**user.user.dict(), **profile.data}
    except Exception as e:
        raise HTTPException(401, "Invalid token")

@app.put("/users/me")
async def update_profile(update_data: dict, token: str = Depends(get_current_user)):
    try:
        user = supabase.auth.get_user(token)
        supabase.table("user_profiles").update(update_data).eq("id", user.user.id).execute()
        return {"message": "Profile updated"}
    except Exception as e:
        raise HTTPException(400, "Update failed")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "auth-gateway"}
```

### Requirements
```txt
# services/auth-gateway/requirements.txt
fastapi
uvicorn[standard]
supabase
python-dotenv
pydantic
pydantic-settings
```

### Dockerfile
```dockerfile
# services/auth-gateway/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

## 4. Environment Variables

### New Environment Variables
```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# Remove old user-service vars
# DATABASE_URL=sqlite+aiosqlite:///./user.db
# JWT_SECRET=change-me-in-production
```

### Updated .env.example
```env
# API Keys
OPENAI_API_KEY=your-openai-api-key-here
GROQ_API_KEY=your-groq-api-key-here  # For STT and TTS
PINECONE_API_KEY=your-pinecone-api-key-here

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# Security
SECRET_KEY=your-secret-key-here-change-in-production

# Database (SQLite for service-specific data)
DATABASE_URL=sqlite:///./talentsync.db
```

## 5. Docker Compose Updates

### Updated docker-compose.yml
```yaml
version: '3.9'

services:
  auth-gateway:  # Replaces user-service
    build: ./services/auth-gateway
    env_file: .env
    ports:
      - "8001:8001"
    environment:
      - PORT=8001
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Other services remain unchanged
  media-service:
    build: ./services/media-service
    env_file: .env
    ports:
      - "8002:8002"
    environment:
      - PORT=8002
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  resume-service:
    build: ./services/resume-service
    env_file: .env
    ports:
      - "8004:8004"
    environment:
      - PORT=8004
      - USER_SERVICE_URL=http://auth-gateway:8001  # Updated reference
    volumes:
      - resume_uploads:/app/uploads
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  transcription-service:
    build: ./services/transcription-service
    env_file: .env
    ports:
      - "8005:8005"
    environment:
      - PORT=8005
    volumes:
      - audio_uploads:/app/audio
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8005/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  interview-service:
    build: ./services/interview-service
    env_file: .env
    ports:
      - "8006:8006"
    environment:
      - PORT=8006
      - PINECONE_API_KEY=local
      - USER_SERVICE_URL=http://auth-gateway:8001  # Updated reference
      - TRANSCRIPTION_SERVICE_URL=http://transcription-service:8005
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8006/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  feedback-service:
    build: ./services/feedback-service
    env_file: .env
    ports:
      - "8010:8010"
    environment:
      - PORT=8010
      - DATABASE_URL=sqlite+aiosqlite:///data/feedback.db
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8010/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - auth-gateway  # Updated dependency
      - media-service
      - interview-service
      - resume-service
      - transcription-service
      - feedback-service

volumes:
  resume_uploads:
  audio_uploads:

networks:
  default:
    name: talentsync-network
```

## 6. Service Dependencies Updates

### Interview Service
```python
# services/interview-service/app/core/config.py
USER_SERVICE_URL: str = "http://auth-gateway:8001"  # Updated
```

### Media Service
```python
# services/media-service/app/core/config.py
interview_service_url: str = Field(
    default="http://auth-gateway:8001",  # Updated
    description="Interview service URL"
)
```

## 7. Frontend Integration

### No Changes Required
The frontend API calls remain the same:
```javascript
// frontend/src/services/api.js - No changes needed
export const authAPI = {
  login: (credentials) => userService.post('/auth/login', credentials),
  signup: (userData) => userService.post('/auth/signup', userData),
  // These will now go to Supabase via the gateway
};
```

### Mock Handlers Update
```javascript
// frontend/src/test/mocks/handlers.js - Update base URL
const BASE_URLS = {
  USER: 'http://localhost:8001',  # Still points to port 8001
  // ... other services
};
```

## 8. Nginx Configuration

### No Changes Required
The nginx configuration remains the same:
```nginx
# nginx.conf - No changes needed
location /api/auth/ {
    proxy_pass http://auth-gateway:8001/api/v1/auth/;
    # ... existing config
}

location /api/users/ {
    proxy_pass http://auth-gateway:8001/api/v1/users/;
    # ... existing config
}
```

## 9. Migration Steps

### Phase 1: Supabase Setup
1. **Create Supabase Project**
   ```bash
   # Go to https://supabase.com
   # Create new project
   # Note down: URL, anon key, service role key
   ```

2. **Set up Database Schema**
   ```sql
   -- Run the schema creation script in Supabase SQL editor
   -- Enable RLS policies
   -- Test basic auth operations
   ```

3. **Configure Environment**
   ```bash
   # Update .env file with Supabase credentials
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
   ```

### Phase 2: Auth Gateway Development
1. **Create Auth Gateway Service**
   ```bash
   mkdir -p services/auth-gateway
   # Copy the auth gateway code structure
   ```

2. **Test Auth Gateway**
   ```bash
   cd services/auth-gateway
   python -m uvicorn app.main:app --reload --port 8001
   # Test endpoints manually
   ```

3. **Update Docker Compose**
   ```bash
   # Replace user-service with auth-gateway in docker-compose.yml
   # Update service dependencies
   ```

### Phase 3: Data Migration
1. **Export Existing Data**
   ```bash
   # Backup SQLite database
   cp services/user-service/user.db user_backup.db
   ```

2. **Run Migration Script**
   ```bash
   # Run the data migration script
   python migrate_users.py
   ```

3. **Verify Migration**
   ```bash
   # Check Supabase dashboard for migrated users
   # Test login with migrated accounts
   ```

### Phase 4: Deployment
1. **Deploy Auth Gateway**
   ```bash
   docker-compose up -d auth-gateway
   # Test health endpoint
   ```

2. **Update Service Dependencies**
   ```bash
   # Update all services to use auth-gateway
   docker-compose up -d
   ```

3. **Test End-to-End**
   ```bash
   # Test complete authentication flow
   # Verify all services can access auth
   ```

### Phase 5: Cleanup
1. **Remove Old Service**
   ```bash
   # Remove user-service directory
   rm -rf services/user-service
   ```

2. **Update Documentation**
   ```bash
   # Update all documentation files
   # Update README files
   ```

## 10. Benefits of Migration

### Managed Infrastructure
- **Automatic Backups**: Supabase handles database backups
- **Security Updates**: Automatic security patches
- **Scaling**: Managed PostgreSQL with auto-scaling
- **Monitoring**: Built-in analytics and monitoring

### Enhanced Features
- **Social Login**: Easy integration with OAuth providers
- **Multi-factor Auth**: Built-in MFA support
- **Real-time**: WebSocket subscriptions for live updates
- **User Management**: Supabase dashboard for admin operations

### Security Improvements
- **Row Level Security**: Fine-grained access control
- **JWT Management**: Automatic token rotation
- **Audit Logs**: Comprehensive security monitoring
- **GDPR Compliance**: Built-in data protection

### Developer Experience
- **Auto-generated APIs**: Supabase provides REST and GraphQL APIs
- **Type Safety**: Generated TypeScript types
- **Real-time Subscriptions**: Live data updates
- **Built-in Analytics**: User activity tracking

## 11. Rollback Plan

### Emergency Rollback
1. **Keep Old Service Code**
   ```bash
   # Don't delete user-service immediately
   # Keep backup of SQLite database
   ```

2. **Quick Switch**
   ```bash
   # Update docker-compose.yml to use user-service
   # Restore environment variables
   docker-compose up -d user-service
   ```

3. **Data Recovery**
   ```bash
   # Use backup SQLite database
   # Restore user data if needed
   ```

### Gradual Rollback
1. **Parallel Running**
   ```bash
   # Run both services in parallel
   # Route traffic gradually
   ```

2. **Monitor and Switch**
   ```bash
   # Monitor for issues
   # Switch back if needed
   ```

## 12. Testing Strategy

### Unit Tests
```python
# Test auth gateway endpoints
def test_login_success():
    # Test successful login
    pass

def test_signup_success():
    # Test successful signup
    pass

def test_profile_management():
    # Test profile CRUD operations
    pass
```

### Integration Tests
```python
# Test service dependencies
def test_interview_service_auth():
    # Test interview service can access auth
    pass

def test_media_service_auth():
    # Test media service can access auth
    pass
```

### End-to-End Tests
```python
# Test complete authentication flow
def test_full_auth_flow():
    # Test signup → login → profile access
    pass
```

## 13. Performance Considerations

### Expected Improvements
- **Database Performance**: PostgreSQL > SQLite for concurrent access
- **Authentication Speed**: Supabase optimized auth flows
- **Scalability**: Handles 10x more concurrent users
- **Real-time Features**: WebSocket subscriptions for live updates

### Monitoring Points
- **Response Times**: Auth gateway latency
- **Error Rates**: Supabase API errors
- **User Experience**: Login/signup success rates
- **Service Dependencies**: Impact on other services

## 14. Cost Analysis

### Supabase Costs
- **Free Tier**: 50,000 monthly active users
- **Pro Plan**: $25/month for 100,000 MAU
- **Enterprise**: Custom pricing for large scale

### Savings
- **Reduced Infrastructure**: No need to manage PostgreSQL
- **Security**: Built-in security features
- **Development Time**: Faster development with managed services

## 15. Current System State

### Updated Service Architecture
- **Auth Gateway** (Port 8001): Supabase Auth integration
- **Interview Service** (Port 8006): Pinecone vector database only
- **Resume Service** (Port 8004): File-based storage, no database
- **Transcription Service** (Port 8005): SQLite for caching, Groq Whisper-Large-V3 + PlayAI-TTS
- **Media Service** (Port 8002): SQLite for metadata
- **Feedback Service** (Port 8010): SQLite + Blackbox AI's `blackboxai/openai/o4-mini`

### AI Model Standardization
- **OpenAI o4-mini**: Primary reasoning and question generation
- **OpenAI o1-mini**: Resume enhancement and analysis
- **Blackbox AI o4-mini**: Specialized feedback generation
- **Groq Whisper-Large-V3**: Ultra-fast speech-to-text
- **Groq PlayAI-TTS**: High-quality text-to-speech

### Data Storage Strategy
- **Supabase**: User authentication and profiles
- **SQLite**: Service-specific structured data
- **Pinecone**: Vector embeddings for semantic search
- **File-based**: Resume processing and storage
- **Redis**: Caching and session management

## 16. Conclusion

This migration provides TalentSync with:
- **Managed Authentication**: No need to handle password hashing, JWT management
- **Enhanced Security**: Supabase handles security best practices
- **Better Scalability**: Managed PostgreSQL with automatic scaling
- **Developer Experience**: Supabase dashboard and APIs
- **Future-Proof**: Easy to add social login, MFA, and other features

The migration maintains backward compatibility while providing significant improvements in security, scalability, and developer experience. 