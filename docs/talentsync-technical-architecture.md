# TalentSync — Technical Architecture & Tech Stack

## 1. System Architecture Overview

TalentSync employs a modern microservices architecture optimized for scalability, maintainability, and real-time performance. The system uses a **hybrid data storage** approach combining managed PostgreSQL (Supabase) for user data, SQLite for service-specific data, Pinecone for vector search, and file-based storage for resumes.

### 1.1 High-Level Architecture

```
[Frontend (React/Vite)] <-> [API Gateway (Nginx)] <-> { FastAPI Microservices }
                                                           |         ↙         ↘
                                                           ↓    [SQLite]   [Pinecone Vector DB]
[Auth Gateway (8001)] ─→ [Supabase Auth + PostgreSQL]  ↗
                                                     ↘
[Transcription Service] ─→ [Groq Whisper-Large-V3]  ↗
                                                     ↘
[Feedback Service] ─→ [Blackbox AI o4-mini]        ↗
```

This architecture ensures clear separation of concerns. The API Gateway (Nginx) routes requests from the browser or mobile clients to the appropriate service. Microservices communicate via JSON over HTTP, enabling independent scaling and deployment.

### 1.2 Service Architecture Summary

| Service | Port | Storage/DB | Responsibilities |
|---------|------|------------|------------------|
| **auth-gateway** | 8001 | Supabase Auth + PostgreSQL | Manages user authentication, profiles, and authorization. Acts as adapter between services and Supabase. |
| **resume-service** | 8004 | File-based (no DB) | Processes uploaded resumes. Uses OpenAI o4-mini to parse candidate data (skills, experience) and generate tailored questions. No persistent DB; uses local file storage. |
| **interview-service** | 8006 | Pinecone (Vector DB only) | Orchestrates interview Q&A sessions. Retrieves and sequences questions via semantic search. Uses Pinecone for embedding-based lookup; no relational DB. |
| **transcription-service** | 8005 | SQLite | Handles audio transcription and TTS. Uses Groq Whisper-Large-V3 for STT and PlayAI-TTS for TTS. High-performance, ultra-fast transcription with caching. |
| **media-service** | 8002 | SQLite | Manages media files (recordings, documents). Stores metadata/URLs for audio/video in object storage (e.g. S3) and tracks references. |
| **feedback-service** | 8010 | SQLite | Collects interview responses and scores. Generates feedback reports using Blackbox AI's `blackboxai/openai/o4-mini` model. Stores scores and feedback in SQLite. |

## 2. Data Storage Strategy

### 2.1 Supabase (Managed PostgreSQL)

**Purpose:** User authentication and profile data are managed through Supabase's managed PostgreSQL database with built-in authentication.

**Implementation:**
- **Supabase Auth**: Handles user registration, login, password management, and JWT token generation
- **User Profiles**: Custom `user_profiles` table linked to Supabase Auth users
- **Row Level Security (RLS)**: Fine-grained access control for user data
- **Real-time Subscriptions**: WebSocket connections for live user data updates

**Database Schema:**
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

**Benefits:**
- **Managed Infrastructure**: Automatic backups, updates, and scaling
- **Built-in Security**: Row Level Security and authentication
- **Real-time Capabilities**: WebSocket subscriptions for live updates
- **Social Login**: Easy integration with OAuth providers
- **Multi-factor Auth**: Built-in MFA support

### 2.2 SQLite (Service-Specific Data)

**Purpose:** Service-specific structured data (sessions, media metadata, feedback reports, transcription data) are stored in SQLite databases via the SQLAlchemy ORM.

**Implementation:**
- Each service (except stateless ones) uses a local SQLite file for its specific data
- Simplifies setup (no DB server needed) and ensures strong consistency
- SQLite only allows one writer at a time, which we accept given moderate write volumes
- Writes occur mainly when creating sessions or saving scores

**Scaling Patterns:**
- One DB per service (current implementation)
- One DB per user in extreme cases
- Typical tables include: `sessions`, `responses`, `feedback_reports`, `media_files`, `transcriptions`
- JSON or text columns in SQLite (using JSON1 extension) can index resume data if needed

**Benefits:**
- **ACID Guarantees**: Full transactional support
- **Zero Configuration**: No separate database server required
- **Portability**: Database files can be easily backed up and moved
- **Performance**: Excellent read performance with unlimited concurrent readers

### 2.3 Pinecone (Vector Database)

**Purpose:** Semantic data (question and answer embeddings) are stored in Pinecone for enabling RAG (Retrieval-Augmented Generation) capabilities.

**Implementation:**
- Maintain separate Pinecone namespaces/indices for different embedding types:
  - `questions-embeddings`
  - `followups-embeddings`
  - `ideal-answers-embeddings`
- Each entry's metadata includes `question_id`, `domain`, and `type`, enabling filtered queries
- Background jobs generate embeddings (via Sentence-BERT or similar) and upsert into Pinecone

**Vector Search Capabilities:**
- Optimized for approximate nearest-neighbor search over high-dimensional vectors
- Pinecone indexes embeddings using algorithms like HNSW
- Can quickly retrieve top-K most similar questions to a given query vector
- Enables real-time matching of candidate answers against relevant follow-up questions

**Use Cases:**
- **Semantic Question Matching**: Find similar questions based on meaning, not just keywords
- **Dynamic Follow-ups**: Generate contextual follow-up questions based on candidate responses
- **Answer Similarity**: Compare candidate answers against ideal responses

### 2.4 File-Based Storage (Resume Service)

**Purpose:** Resume service uses local file storage for processing uploaded resumes without a database.

**Implementation:**
- Uploaded resumes stored in local file system
- Processed JSON output stored in `data/output/` directory
- No database dependencies for resume processing
- File-based workflow: PDF → Text → JSON → Analysis

**Benefits:**
- **Simple Architecture**: No database setup required
- **Fast Processing**: Direct file I/O operations
- **Easy Debugging**: Raw files available for inspection
- **Stateless Design**: Can be easily scaled horizontally

### 2.5 Redis (Cache & Queue)

**Purpose:** Used as a message broker and in-memory data store for high-performance operations.

**Implementation:**
- Queue session question sequences in Redis (ordered list of upcoming questions for each candidate)
- Backs Celery for background tasks (transcription jobs, embedding generation, scoring)
- Caches frequent reads (e.g. session state) and enforces rate limits
- Provides fast pub/sub or lists/sets to manage dynamic interview flow

**Benefits:**
- **In-Memory Performance**: Sub-millisecond response times
- **Pub/Sub Messaging**: Real-time communication between services
- **Queue Management**: Reliable background task processing
- **Session State**: Fast access to interview session data

### 2.6 Object Storage

**Purpose:** Interview media (audio/video recordings, uploaded resumes) are stored in object storage.

**Implementation:**
- AWS S3 or similar cloud storage for large media files
- Media service handles uploads: saves files to S3 and writes file URLs/paths in SQLite database
- Keeps large blobs out of microservice containers
- Resume service sends files to S3 then processes them

**Benefits:**
- **Scalability**: Unlimited storage capacity
- **Cost-Effective**: Pay only for what you use
- **Reliability**: Built-in redundancy and backup
- **Performance**: CDN integration for fast global access

## 3. Authentication & Authorization

### 3.1 Supabase Auth Integration

**Implementation:**
- **Auth Gateway**: FastAPI service that acts as adapter between existing services and Supabase
- **JWT Tokens**: Supabase generates and validates JWT tokens for API access
- **User Management**: Supabase dashboard for user administration and analytics
- **Social Login**: Easy integration with Google, GitHub, and other OAuth providers

**Auth Flow:**
```
Frontend → Auth Gateway (8001) → Supabase Auth → PostgreSQL
Other Services → Auth Gateway (8001) → Supabase Auth → PostgreSQL
```

### 3.2 Auth Gateway Service

**Responsibilities:**
- **Authentication Endpoints**: `/auth/login`, `/auth/signup`, `/auth/logout`
- **Profile Management**: `/users/me` (GET/PUT)
- **Token Validation**: JWT token verification and user context
- **Error Handling**: Graceful handling of Supabase errors

**Implementation:**
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
```

### 3.3 Security Features

**Built-in Security:**
- **Row Level Security (RLS)**: Fine-grained access control
- **JWT Token Rotation**: Automatic token refresh and rotation
- **Password Security**: Secure hashing and validation
- **Rate Limiting**: Built-in protection against abuse
- **Audit Logs**: Comprehensive security monitoring

## 4. RAG Pipeline & Interview Flow

TalentSync implements a **Retrieval-Augmented Generation (RAG)** style interview pipeline that enables dynamic, adaptive questioning.

### 4.1 Session Seeding

**Process:**
1. System fetches core questions from SQL database (based on chosen modules)
2. Analyzes candidate's resume to generate personalized questions
3. Resume parsing extracts skills or experiences and creates new question prompts on-the-fly
4. Combined question list (module + resume-driven questions) is enqueued in Redis as the interview's Q&A queue

**Purpose:** This seeding phase is akin to offline "ingestion" in RAG systems, where we prepare the knowledge base ahead of interaction.

### 4.2 Dynamic Q&A

**Process:**
1. After each candidate response, Interview service embeds the answer text into a vector
2. Queries Pinecone for top-K semantically related follow-up questions
3. Filters out questions already asked in this session
4. Optionally invokes OpenAI o4-mini to refine the selected follow-up
5. Generates custom questions if none are a good fit
6. Novel follow-ups generated by OpenAI o4-mini are inserted back into Pinecone for future reuse

**RAG Implementation:** This process (query embeddings → retrieve from vector DB → optional OpenAI o4-mini rewriter) constitutes the live retrieval and generation step of RAG, mirroring typical two-phase RAG architecture.

### 4.3 Question Delivery

**Process:**
1. Next question is pushed to frontend (via WebSockets or API polling)
2. Interview service updates session state (current question index, answers so far) in Redis
3. Service waits for answer, then automatically proceeds with step 2 to fetch next question
4. Loop continues until session's question queue is exhausted

**Benefits:**
- **Reduces Repetitive Questions**: Semantic search prevents duplicate follow-ups
- **Adapts to Responses**: Interview adjusts to each candidate's answers
- **Maintains Context**: Session state ensures continuity throughout interview

## 5. Tech Stack & Tools

### 5.1 Backend Technologies

| Layer | Technology / Library | Purpose |
|-------|---------------------|---------|
| **Language** | Python 3.11+ | Core language for backend microservices (with async support) |
| **API Framework** | FastAPI | High-performance, async web framework for building REST APIs |
| **ORM / DB** | SQLAlchemy + SQLite | ORM for relational data access; SQLite for local persistence |
| **Auth & User DB** | Supabase Auth + PostgreSQL | Managed authentication and user data storage |
| **Cache / Queue** | Redis (broker) + Celery | In-memory store and message queue for sessions and background tasks |
| **Vector DB** | Pinecone | Managed vector database for storing and querying embeddings |

### 5.2 Frontend Technologies

| Layer | Technology / Library | Purpose |
|-------|---------------------|---------|
| **Framework** | React + Vite + Tailwind CSS | Responsive SPA UI; Vite enables fast dev build/reload |
| **State Management** | React Context + Hooks | Local state management for components |
| **HTTP Client** | Axios | API communication with backend services |
| **Real-time** | WebSocket API | Live communication for interview sessions |

### 5.3 AI & Machine Learning

| Layer | Technology / Library | Purpose |
|-------|---------------------|---------|
| **NLP & ML** | spaCy, Hugging Face Transformers, SentenceTransformers | NLP (NER, parsing) and embedding models for question/answer processing |
| **STT** | Groq Whisper-Large-V3 | Ultra-fast, high-accuracy speech-to-text transcription |
| **TTS** | Groq PlayAI-TTS | High-quality text-to-speech with multiple voice options |
| **LLM** | OpenAI o4-mini | Generating feedback reports and optional question refinement |
| **Feedback LLM** | Blackbox AI o4-mini | Specialized feedback generation using `blackboxai/openai/o4-mini` |
| **Embeddings** | OpenAI text-embedding-ada-002 | Vector generation for semantic search |

### 5.4 Security & Authentication

| Layer | Technology / Library | Purpose |
|-------|---------------------|---------|
| **Auth & Security** | Supabase Auth + JWT, FastAPI Security | Managed authentication with JWT tokens and role-based access control |
| **CORS** | FastAPI CORS middleware | Cross-origin resource sharing configuration |
| **Rate Limiting** | Redis-based rate limiting | Prevent API abuse and ensure fair usage |

### 5.5 DevOps & Infrastructure

| Layer | Technology / Library | Purpose |
|-------|---------------------|---------|
| **Containerization** | Docker, Docker Compose | Containerization and local development orchestration |
| **Orchestration** | Kubernetes/EKS | Production container orchestration and scaling |
| **CI/CD** | GitHub Actions | Automated testing and deployment pipelines |
| **Monitoring** | ELK Stack, Prometheus & Grafana | Centralized logging, metrics collection, and dashboards |
| **API Gateway** | Nginx | Request routing, load balancing, and SSL termination |

## 6. Deployment & Infrastructure

### 6.1 Containerization & Orchestration

**Development Environment:**
- Docker Compose for local development
- Each service packaged as Docker container
- Shared volumes for development files
- Hot reloading for fast development cycles

**Production Environment:**
- Kubernetes (AWS EKS or similar) for production deployment
- Deployments and Services per microservice
- LoadBalancer/Ingress for API gateway
- Auto-scaling based on CPU/memory usage

### 6.2 API Gateway & Ingress

**Implementation:**
- Nginx (or Traefik) serves as API gateway
- Terminates TLS (via Let's Encrypt)
- Routes incoming requests to appropriate services
- All HTTP traffic encrypted (Frontend ↔ Gateway ↔ Backend)
- Domain names and certificates managed automatically

### 6.3 Secrets Management

**Security Strategy:**
- Sensitive configuration stored in secure secret store
- AWS Secrets Manager or SSM Parameter Store for AWS
- Kubernetes secrets managed with sealed secrets or Vault
- API keys for OpenAI, Groq, Supabase, database connection strings, OAuth credentials

### 6.4 CI/CD Pipeline

**Automation:**
- GitHub Actions for testing and deployment
- Unit/integration tests run on each push
- Docker images built and pushed to container registry (AWS ECR)
- Kubernetes deployments updated via kubectl or Terraform/Helm
- Automated rollouts with health checks

### 6.5 Logging & Monitoring

**Observability Stack:**
- Structured JSON logging to stdout/stderr
- Centralized ELK (Elasticsearch) or EFK stack
- Prometheus for application metrics (request rates, latencies, queue lengths)
- Grafana dashboards for system health visualization
- Optional Jaeger for end-to-end request tracing

### 6.6 Backup & High Availability

**Data Protection:**
- Supabase provides automatic backups for user data
- SQLite database files periodically backed up to S3
- Pinecone as managed service replicates data across nodes
- Kubernetes ensures high availability via pod replication
- HPA (Horizontal Pod Autoscaler) for auto-scaling under load

## 7. Scaling & Performance

### 7.1 Auto-Scaling Strategy

**Implementation:**
- Kubernetes HPA based on CPU/memory usage or custom metrics
- Redis queue length as scaling metric for background services
- Transcription and feedback services scale out during high traffic
- Uvicorn workers configuration for high-throughput (1000+ RPS)
- Rate limiting with Redis token bucket algorithm
- Ensures responsiveness under varying load

### 7.2 Vector Index Optimization

**Performance Enhancements:**
- Partition Pinecone indexes per domain for faster lookups
- Increase shard count for large question banks
- Pinecone's managed scaling and high throughput (serverless mode)
- Experiment with sparse indexes or filter metadata to limit search scope

### 7.3 Database Scaling

**Supabase Optimization:**
- Managed PostgreSQL with automatic scaling
- Built-in connection pooling and query optimization
- Real-time subscriptions for live updates
- Automatic backups and point-in-time recovery

**SQLite Optimization:**
- Read-heavy operations scale fine with unlimited concurrent readers
- Write operations serialized but acceptable for moderate volumes
- Consider sharding workload (separate DB files per user or domain)
- Serialize writes in application logic when needed

## 8. Security Considerations

### 8.1 Authentication & Authorization

**Implementation:**
- Supabase Auth handles user authentication with JWT tokens
- Role-based access control (RBAC) via Supabase RLS policies
- OAuth2 flows for third-party integrations
- Multi-factor authentication support via Supabase

### 8.2 Data Protection

**Security Measures:**
- All data encrypted in transit (HTTPS/TLS)
- Sensitive data encrypted at rest
- Supabase provides enterprise-grade security
- Regular security audits and penetration testing
- GDPR compliance for user data handling

### 8.3 API Security

**Protection Layers:**
- Rate limiting to prevent abuse
- Input validation to prevent injection attacks
- CORS configuration for cross-origin requests
- API key rotation and management

## 9. Future Enhancements

### 9.1 Advanced Features

**Planned Improvements:**
- **Multi-language Support**: Extend resume parsing and question generation beyond English
- **Employer Portal**: Secured portal for hiring managers and recruiters
- **Plugin Architecture**: Third-party integrations for custom question sets
- **Advanced Analytics**: Predictive performance modeling and trend analysis
- **Mobile Support**: Native mobile applications
- **VR/AR Support**: Immersive interview experiences

### 9.2 Infrastructure Enhancements

**Scalability Improvements:**
- **Global Vector Index**: Sharded Pinecone indices per domain
- **Multi-region Deployment**: Cross-zone or cross-region redundancy
- **Advanced Monitoring**: AI-powered anomaly detection
- **Disaster Recovery**: Cross-region backup and failover

### 9.3 Integration Capabilities

**External Systems:**
- **HRIS Integration**: Connect with existing HR systems
- **ATS Integration**: Applicant tracking system connectivity
- **Calendar Integration**: Automated interview scheduling
- **Analytics Export**: Data warehouse integration for BI tools

## 10. Performance Benchmarks

### 10.1 Response Times

**Target Metrics:**
- API Gateway: < 50ms latency
- Auth Gateway: < 100ms (including Supabase round-trip)
- Question Retrieval: < 200ms (including vector search)
- Audio Transcription: < 2 seconds for 30-second audio (Groq optimized)
- Feedback Generation: < 30 seconds for complete report
- Real-time STT: < 500ms latency for live transcription

### 10.2 Scalability Targets

**Capacity Planning:**
- Concurrent Users: 1000+ simultaneous interviews
- Question Database: 10,000+ questions across all domains
- Audio Processing: 100+ concurrent transcription jobs
- Vector Search: 1000+ queries per second
- API Throughput: 1000+ RPS with Uvicorn workers
- Real-time STT: 500+ concurrent audio streams

## 11. References

**Technical Standards:**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Supabase Documentation](https://supabase.com/docs)
- [SQLite Usage Recommendations](https://www.sqlite.org/whentouse.html)
- [RAG Pipeline Design](https://developer.nvidia.com/blog/rag-101-demystifying-retrieval-augmented-generation-pipelines/)
- [Pinecone Vector Database](https://www.pinecone.io/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [Groq Speech-to-Text](https://console.groq.com/docs/speech-to-text)
- [Groq Text-to-Speech](https://console.groq.com/docs/text-to-speech)
- [Groq Prompting](https://console.groq.com/docs/prompting)
- [Blackbox AI Documentation](https://blackboxai.com/docs)

**Industry Best Practices:**
- Microservices Architecture Patterns
- Vector Database Optimization
- Real-time Audio Processing
- AI-Powered Interview Systems
- Secure API Design Principles

---

*This technical architecture document serves as the comprehensive guide for TalentSync's system design, implementation, and future development. It ensures alignment with industry best practices while maintaining the flexibility needed for rapid iteration and scaling.* 