# TalentSync Coding Conventions and Best Practices

Consistent, readable code is critical for maintainability and team collaboration. Style guides help enforce uniform standards, making code easier to understand and reducing bugs. For example, PEP 8 (the official Python style guide) emphasizes that "code is read much more often than it is written" and that "readability counts." Established conventions also improve project scalability and performance: by following standard patterns and avoiding ad hoc solutions, developers can more easily optimize and secure their services. In a multi-service system, consistent principles (clear naming, documented APIs, etc.) and security practices (input validation, secret rotation) help support high throughput (100+ concurrent users, 1,000+ RPS) while reducing vulnerabilities.

---

## 1. Repository & Project Structure
- Organize code logically to simplify navigation and deployment.
- Monorepo layout:
  - `/services/` (each microservice in its own subfolder with its own `requirements.txt`/`pyproject.toml` and tests)
  - `/frontend/`
  - `/infra/` (deployment configs like Docker/Kubernetes manifests)
  - `/docs/`
  - `/scripts/`
- Each service should be self-contained (FastAPI app for Python backends, for example) to facilitate independent development and scaling.
- Version-controlled migration scripts (e.g. Alembic migrations in `/app/migrations/`) ensure that database schema changes are tracked.
- Use consistent build and lint scripts (in `/scripts`) and a top-level `README.md` for setup instructions.

## 2. Python Backend Conventions
- **Formatting & Linting:**
  - Follow PEP 8. Use an autoformatter like Black (standardizes quotes, line breaks, wraps to 88 chars).
  - Enforce style checks via pre-commit hooks (Black, isort for imports, flake8).
- **Naming:**
  - Modules/packages: all lowercase (underscores if needed)
  - Classes: PascalCase
  - Functions/variables: snake_case
  - Constants: UPPER_SNAKE_CASE
- **Type Hints & Docstrings:**
  - Use Python 3 type annotations everywhere practical (PEP 484).
  - Write clear docstrings for public functions/classes (Google or NumPy style).
- **FastAPI Patterns:**
  - Structure app using routers and Pydantic schemas.
  - Group related endpoints in separate router modules (e.g. under `app/routers/`).
  - Use `APIRouter` and `Depends()` for shared dependencies.
  - Validate inputs/outputs with Pydantic models in `app/schemas/`.
  - Use `HTTPException` for expected errors; log unexpected exceptions centrally.
  - Leverage FastAPI's auto-generated docs at `/docs` (Swagger UI) and `/redoc` (ReDoc).
- **Concurrency & Performance:**
  - Prefer `async def` endpoints when using async libraries (e.g. aioredis).
  - Run Uvicorn with multiple workers for high-throughput (1000+ RPS): `uvicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker`
  - Offload CPU-intensive/long-running tasks to background workers (e.g. Celery).
  - Implement rate limiting at the gateway or via middleware (e.g. Redis token bucket).
  - Use connection pooling for database operations.
  - Implement circuit breakers for external API calls (Groq Whisper Large v3, Groq PlayAI TTS, OpenAI o4-mini, Supabase, Blackbox AI).

## 3. Frontend (React + Vite)
- **Formatting & Linting:**
  - Use ESLint (Airbnb style guide) and Prettier for code formatting.
  - Inline CSS: Write styles as inline objects for simple layouts; extract common styles as needed.
- **File & Component Structure:**
  - `src/components/` (reusable UI components)
  - `src/pages/` (page-level components/routes)
  - `src/services/` (API call modules)
  - `src/utils/` (shared utilities/hooks)
  - `src/assets/` (images, fonts, etc.)
  - Use PascalCase for component filenames and hook files.
  - Flat folder structure; co-locate tests with components.
- **JSX & State Management:**
  - Use React Function Components with Hooks exclusively.
  - Destructure props in function signatures.
  - Start with `useState`/`useContext`; consider Redux/Zustand if global state grows complex.
  - Break UI into small, focused components for testability and reuse.
- **Accessibility & ARIA:**
  - All interactive elements must be accessible (labels, aria-labels, semantic HTML).
  - Use `<label>` or `aria-label` for form controls; use semantic elements over generic `<div>`s.

## 4. Data & Configuration
- **Environment Variables:**
  - Store config in the environment (`.env` files, loaded via python-dotenv or Vite env vars).
  - Include `.env.example` with placeholders to document needed vars.
  - Supabase configuration requires: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
- **Databases & Migrations:**
  - Use version-controlled migrations (Alembic for SQLite) under each service.
  - Keep Alembic scripts in `app/migrations/`.
  - Resume service uses file-based storage (no database migrations).
  - Interview service uses Pinecone only (no SQL migrations).
  - Auth Gateway uses Supabase (managed migrations via Supabase dashboard).
  - Transcription service uses SQLite for caching and session data.
- **Configs and Infrastructure:**
  - Keep Docker, Compose, and Nginx configs in `/infra`.
  - Document required setup in each service's `README.md`.

## 5. Testing Strategy
- **Backend (Python):**
  - Use pytest; organize tests in `tests/` with subfolders matching code structure.
  - Write unit and integration tests; aim for ≥80% coverage.
  - Use `@pytest.mark.asyncio` for async FastAPI routes.
  - Test rate limiting and circuit breaker patterns.
- Mock external API calls (Groq Whisper Large v3, Groq PlayAI TTS, OpenAI o4-mini, Supabase, Blackbox AI) in tests.
- **Transcription Service Testing:**
  - Use `test_comprehensive_service.py` for automated testing of all components
  - Use `test_live_mock_interview.py` for interactive interview simulation
  - Use `setup_testing.py` for environment validation and setup
  - Test Groq STT/TTS integration with proper mocking
  - Validate persona system and voice assignments
  - Test interview pipeline end-to-end workflows
- **Frontend (React):**
  - Use Jest and React Testing Library.
  - Mock API calls using MSW or jest mocks.
- **Test Automation:**
  - Integrate tests into CI; fail build if tests fail or coverage drops.
  - Use in-memory/test DBs for backend; mock external dependencies for frontend.

## 6. Documentation & API Contracts
- **Auto-Generated API Docs:**
  - Leverage FastAPI's OpenAPI (Swagger UI at `/docs`, ReDoc at `/redoc`).
  - Ensure endpoints have descriptive docstrings/summaries.
- **README & CHANGELOG:**
  - Include a `README.md` in each service with setup/run/test instructions.
  - Maintain a `CHANGELOG.md` (Keep a Changelog conventions, SemVer).
- **API Versioning:**
  - Tag releases in Git with `vX.Y.Z` (SemVer); breaking changes increment MAJOR version.

## 7. CI/CD & Deployment
- **GitHub Actions Pipelines:**
  - Lint & Format → Test → Build → Push → Deploy.
  - Protect main branch; require PRs.
  - Use GitHub Secrets for sensitive data.
  - Performance testing for 1000+ RPS targets.
  - Load testing with realistic interview scenarios.
- **Health Checks:**
  - Each service exposes a `/health` endpoint (HTTP 200 OK if healthy).
  - Configure load balancers/orchestrators to call this endpoint.
- **Release & Versioning:**
  - Use semantic tags; automate changelog/release notes generation if possible.

## 8. Commit & Branching Guidelines
- **Branching:**
  - Protect `main`; use `develop` for integration; feature branches as `feature/<desc>`.
- **Commit Messages:**
  - Follow Conventional Commits: `<type>(scope?): <short description>`
    - `feat`: new feature (MINOR)
    - `fix`: bug fix (PATCH)
    - `chore`, `docs`, `style`, `refactor`, `perf`, `test`, etc. for other changes
    - Breaking changes: add `!` after type/scope (e.g. `feat(api)!:`)
  - Example: `feat(interview): support PDF resume parsing`

## 9. Production-Grade Requirements

### 9.1 High-Performance Configuration

**Uvicorn Workers:**
- Use multiple workers for high-throughput: `uvicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker`
- Configure worker processes based on CPU cores
- Enable worker preload for faster startup

**Rate Limiting:**
- Implement Redis-based token bucket algorithm
- Configure per-user and per-endpoint limits
- Monitor rate limit violations for abuse detection

**Circuit Breakers:**
- Implement circuit breakers for external API calls (Groq Whisper Large v3, Groq PlayAI TTS, OpenAI o4-mini, Supabase, Blackbox AI)
- Configure timeout and retry policies
- Monitor external service health

### 9.2 Monitoring & Observability

**Application Metrics:**
- Track request rates, latencies, and error rates
- Monitor database connection pool usage
- Measure external API response times (Supabase, Groq Whisper Large v3, Groq PlayAI TTS, OpenAI, Blackbox AI)

**Health Checks:**
- Comprehensive health checks for all dependencies
- Database connectivity verification
- External service availability checks (Supabase, Groq Whisper Large v3, Groq PlayAI TTS, OpenAI, Blackbox AI)

### 9.3 Security Hardening

**Input Validation:**
- Strict Pydantic validation for all inputs
- Sanitize user inputs to prevent injection attacks
- Validate file uploads and media types

**Authentication & Authorization:**
- Supabase Auth handles JWT token generation and validation
- Role-based access control (RBAC) via Supabase RLS policies
- API key management for external services (Groq Whisper Large v3, Groq PlayAI TTS, OpenAI, Pinecone, Blackbox AI)

**Supabase Integration:**
- Use Supabase client for authentication operations
- Implement proper error handling for Supabase API calls
- Leverage Supabase RLS for data access control
- Use Supabase real-time subscriptions for live updates

---

By following these conventions—supported by official guides and best practices—the TalentSync codebase will remain clean, consistent, and maintainable. The use of standardized tools (Black, ESLint, PyTest, Jest, etc.) and workflows (CI/CD pipelines, semantic versioning) ensures the system can scale securely and reliably as it grows.

**Sources:**
- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [The Twelve-Factor App](https://12factor.net/config)
- [Black code style](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Supabase Documentation](https://supabase.com/docs)
- [Prettier](https://prettier.io/)
- [W3C Accessibility Guidelines](https://www.w3.org/WAI/tutorials/forms/labels/)
- [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) 