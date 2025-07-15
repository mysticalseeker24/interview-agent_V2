import os
import pytest_asyncio
from pathlib import Path
from dotenv import load_dotenv
from httpx import AsyncClient
from app.main import app
from app.services.supabase_service import supabase_service

# Load environment variables from .env file
service_dir = Path(__file__).parent.parent
env_file = service_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Load env variables for real Supabase
from app.core.settings import settings  # ensure .env is loaded

@pytest_asyncio.fixture
async def client():
    """Async HTTP client for FastAPI app."""
    base_url = f"http://{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '8001')}"
    async with AsyncClient(app=app, base_url=base_url) as ac:
        yield ac

import pytest

@pytest.fixture(scope="module")
def cleanup_container():
    """Holder for cleanup data."""
    data = {"user_id": None}
    yield data
    # Teardown: remove test user if created
    uid = data.get("user_id")
    if uid:
        # Delete profile and auth user
        try:
            supabase_service.admin_client.table("user_profiles").delete().eq("id", uid).execute()
        except Exception:
            pass
        try:
            supabase_service.admin_client.auth.admin.delete_user(uid)
        except Exception:
            pass 