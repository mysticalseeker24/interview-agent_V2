import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Transcription Service"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./transcription_service.db")
    interview_service_url: str = os.getenv("INTERVIEW_SERVICE_URL", "http://localhost:8002")
    enable_integrations: bool = os.getenv("ENABLE_INTEGRATIONS", "true").lower() == "true"
    PORT: int = 8005

settings = Settings()
