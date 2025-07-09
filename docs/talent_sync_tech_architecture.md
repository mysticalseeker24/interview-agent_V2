# TalentSync - Technical Architecture & Tech Stack

## 1. Architecture Overview

TalentSync uses a **microservice-based** design with a **hybrid data storage** pattern, combining PostgreSQL for structured data and Pinecone for vector embeddings to power RAG flows.

```
[Frontend React/Vite] ←→ [API Gateway / Nginx] ←→ { FastAPI Microservices }
    ↓                        ↓                    ↙         ↘
[User, Session, Module APIs] ───────────────→ [PostgreSQL]      [Pinecone Vector DB]
                      ↘                                     ↗
                   [Transcription Service] ─→ [Whisper, AssemblyAI]
                      ↗                                     ↘
               [Feedback Service] ─→ [LLM (OpenAI GPT‑4/Gemini)]
```

---

## 2. Microservices & Responsibilities

| Service              | Port   |
|----------------------|--------|
| user-service         | 8001   |
| resume-service       | 8004   |
| interview-service    | 8006   |
| transcription        | 8005   |
| media-service        | 8002   |
| feedback-service     | 8010   |

---

## 3. Data Storage

### 3.1 PostgreSQL (Relational)

- **Tables**:
  - `users`, `roles`, `permissions`
  - `modules`, `questions`, `follow_up_templates`
  - `sessions`, `session_questions`, `responses`
  - `scores`, `percentiles`, `feedback_reports`
- **Indices & Constraints**:
  - FKs linking sessions → users & modules
  - JSONB column for `parsed_resume_data` in `sessions` table
  - GIN indices on JSONB and text columns for full-text search

### 3.2 Pinecone (Vector DB)

- **Namespaces**:
  - `questions-embeddings`
  - `followups-embeddings`
  - `ideal-answers-embeddings`
- **Vector Metadata**: store `question_id`, `domain`, `type` as metadata for retrieval filtering
- **Sync Strategy**: On question creation/update, trigger background job to generate and upsert embedding

---

## 4. RAG Pipeline & Question Flow

1. **Session Seeding**:
   - Fetch core module questions from Postgres
   - Generate resume-driven questions from parsed data
   - Store ordered queue in Redis
2. **Dynamic Q&A**:
   - After each `Response` arrives:
     - Embed answer text → query Pinecone top-K follow-ups
     - Filter out already-asked
     - (Optional) LLM refine: generate bespoke follow-up and store back
3. **Question Delivery**:
   - Interview Service pushes questions via WebSocket or poll

---

## 5. Tech Stack & Tools

| Layer               | Technology / Library                     | Purpose                                               |
| ------------------- | ---------------------------------------- | ----------------------------------------------------- |
| **Language**        | Python 3.11                              | Backend microservices                                 |
| **API Framework**   | FastAPI                                  | High-performance REST APIs                            |
| **Frontend**        | React + Vite + JavaScript + Inline CSS   | SPA, fast build & dev server, utility-first CSS       |
| **DB**              | PostgreSQL 14                            | Relational data storage, strong consistency           |
| **Cache**           | Redis                                    | Session state, rate-limiting                          |
| **Vector DB**       | Pinecone                                 | Semantic retrieval for RAG                            |
| **STT**             | Whisper (local), AssemblyAI (cloud)      | Audio transcription pipeline                          |
| **NLP & Embedding** | spaCy, Transformers, Sentence-BERT       | NER, keyword extraction, semantic similarity          |
| **Task Queue**      | Celery + Redis                           | Asynchronous background jobs (transcription, scoring) |
| **LLM**             | OpenAI LLM Models                        | AI-generated feedback, optional question generation   |
| **Auth**            | OAuth2 + JWT, FastAPI Security Utilities | Secure login, role-based access                       |
| **DevOps**          | Docker, Docker Compose, GitHub Actions   | CI/CD, container orchestration                        |
|                     |                                          |                                                       |

---

## 6. Deployment & Infrastructure

- **Containerization**: Docker images for each microservice
- **Orchestration**: Docker Compose for dev; Kubernetes/EKS for production
- **Ingress**: Nginx or Traefik reverse proxy + TLS via Let’s Encrypt
- **Secrets**: AWS Secrets Manager or Vault for API keys (OpenAI, AssemblyAI)
- **CI/CD**: GitHub Actions pipelines for build, test, deploy
- **Observability**: Centralized logging (ELK), metrics dashboards (Grafana)

---

## 7. Scaling & Future Enhancements

1. **Auto-scaling**: Kubernetes HPA based on CPU/memory & queue depth
2. **Global Vector Index**: Sharded Pinecone indices per domain for faster lookups
3. **Multi-language Support**: Extend resume parsing & RAG to other languages
4. **Employer Portal**: Tiered access for recruiters to view candidate pipelines
5. **Plugin Architecture**: Allow custom question sets via third-party adapters

---

*Document: TalentSync — Technical Architecture & Tech Stack*

