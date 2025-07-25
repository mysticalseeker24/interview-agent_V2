# TalentSync Auth Gateway Service

High-performance authentication and user management service for TalentSync, optimized for 1000+ RPS with proper security, monitoring, and scalability.

## 🚀 Features

- **High-Performance Authentication**: Optimized for 1000+ requests per second
- **Supabase Integration**: Managed authentication with PostgreSQL backend
- **JWT Token Management**: Secure token validation and refresh
- **User Profile Management**: Complete CRUD operations for user profiles
- **Admin Controls**: Role-based access control for administrative operations
- **Comprehensive Testing**: Full test coverage with pytest and httpx
- **Production Ready**: Docker containerization with health checks
- **Monitoring**: Prometheus metrics and structured logging
- **Security**: CORS, rate limiting, and input validation

## 📋 Requirements

- Python 3.11+
- Supabase account and project
- Redis (optional, for caching and rate limiting)

## 🛠️ Installation

### 1. Clone the repository
```bash
cd talentsync/services/user-service
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
```bash
cp env.example .env
# Edit .env with your actual values
```

### 4. Set up Supabase (Cloud)
1. **Create a Supabase project** (if not already created):
   - Go to [supabase.com](https://supabase.com)
   - Create a new project
   - Note down your project URL and API keys

2. **Configure environment variables**:
   - Update `.env` with your cloud Supabase credentials
   - Ensure `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` are set

3. **Create the `user_profiles` table** (if not already created):

```sql
-- Create user profiles table
CREATE TABLE user_profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  full_name TEXT,
  is_admin BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own profile" ON user_profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON user_profiles
  FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON user_profiles
  FOR INSERT WITH CHECK (auth.uid() = id);
```

## 🚀 Running the Service

### Development
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Production
```bash
# Using Docker
docker build -t talentsync-user-service .
docker run -p 8001:8001 --env-file .env talentsync-user-service

# Using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 4
```

## 📚 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **OpenAPI JSON**: http://localhost:8001/openapi.json

## 🔐 Authentication Endpoints

### User Registration
```http
POST /auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123",
  "full_name": "John Doe"
}
```

### User Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123"
}
```

### User Logout
```http
POST /auth/logout
Authorization: Bearer <access_token>
```

### Get Current User
```http
GET /auth/me
Authorization: Bearer <access_token>
```

## 👤 User Management Endpoints

### Get My Profile
```http
GET /users/me
Authorization: Bearer <access_token>
```

### Update My Profile
```http
PUT /users/me
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "full_name": "Updated Name"
}
```

### Get User by ID (Admin Only)
```http
GET /users/{user_id}
Authorization: Bearer <admin_token>
```

### Update User by ID (Admin Only)
```http
PUT /users/{user_id}
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "full_name": "Updated Name",
  "is_active": true
}
```

## 🧪 Testing

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_auth.py -v
```

## 📊 Monitoring

### Health Check
```http
GET /health
```

### Prometheus Metrics
```http
GET /metrics
```

### Readiness Check
```http
GET /ready
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SUPABASE_URL` | Cloud Supabase URL | `https://your-project.supabase.co` |
| `SUPABASE_ANON_KEY` | Cloud Supabase anonymous key | From Supabase dashboard |
| `SUPABASE_SERVICE_ROLE_KEY` | Cloud Supabase service role key | From Supabase dashboard |
| `SECRET_KEY` | Application secret key | Required |
| `DEBUG` | Enable debug mode | `true` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `PORT` | Service port | `8001` |
| `HOST` | Service host | `0.0.0.0` |

### Performance Tuning

For high-throughput scenarios (1000+ RPS):

1. **Uvicorn Workers**: Use multiple workers based on CPU cores
   ```bash
   uvicorn app.main:app --workers 4
   ```

2. **Redis Configuration**: Enable caching and rate limiting
   ```bash
   REDIS_URL=redis://localhost:6379/0
   ```

3. **Database Connection Pooling**: Configure Supabase connection limits

4. **Load Balancing**: Use multiple service instances behind a load balancer

## 🔧 Local Supabase Management

### Start Local Supabase
```bash
# From talentsync root directory
supabase start
```

### Stop Local Supabase
```bash
supabase stop
```

### Reset Local Database
```bash
supabase db reset
```

### View Local Supabase Status
```bash
supabase status
```

### Access Local Supabase Studio
- **URL**: http://localhost:54323
- **Email**: supabase_admin@admin.com
- **Password**: (shown in `supabase status` output)

## 🐳 Docker Deployment

### Build Image
```bash
docker build -t talentsync-user-service .
```

### Run Container
```bash
docker run -d \
  --name talentsync-user-service \
  -p 8001:8001 \
  --env-file .env \
  talentsync-user-service
```

### Docker Compose
```yaml
version: '3.8'
services:
  user-service:
    build: .
    ports:
      - "8001:8001"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
      - SECRET_KEY=${SECRET_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 🔒 Security

- **JWT Token Validation**: Secure token validation using Supabase JWKs
- **Password Requirements**: Strong password validation
- **CORS Protection**: Configurable CORS policies
- **Rate Limiting**: Request rate limiting per user
- **Input Validation**: Comprehensive input validation with Pydantic
- **Error Handling**: Secure error responses without information leakage

## 📈 Performance

### Benchmarks
- **Latency**: < 100ms for authentication operations
- **Throughput**: 1000+ RPS with proper configuration
- **Memory**: ~50MB per worker process
- **CPU**: Optimized for async operations

### Optimization Tips
1. Use connection pooling for database connections
2. Enable Redis caching for frequently accessed data
3. Implement proper logging levels in production
4. Monitor and tune worker processes based on load
5. Use load balancing for horizontal scaling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the test files for usage examples 