from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routers import auth_router, users_router
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown (cleanup if needed)


app = FastAPI(
    title="TalentSync User Service",
    lifespan=lifespan
)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)


@app.get("/")
async def root():
    return {
        "service": "TalentSync User Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "user-service"}
