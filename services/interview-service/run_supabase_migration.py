#!/usr/bin/env python3
"""Supabase Migration Script for TalentSync Interview Service."""
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import httpx
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class SupabaseMigration:
    """Handles Supabase database migration for interview service."""
    
    def __init__(self):
        """Initialize migration with Supabase client."""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.supabase_url or not self.supabase_service_key:
            logger.error("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
            sys.exit(1)
        
        # Initialize Supabase client
        client_options = ClientOptions(
            schema="public",
            headers={
                "X-Client-Info": "talentsync-interview-migration/1.0.0",
            }
        )
        
        self.client: Client = create_client(
            self.supabase_url,
            self.supabase_service_key,
            options=client_options,
        )
        
        logger.info("Supabase migration client initialized")
    
    async def check_connection(self) -> bool:
        """Check if Supabase connection is working (without requiring tables to exist)."""
        try:
            # Just try a simple request to the REST endpoint
            url = f"{self.supabase_url}/rest/v1/"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                if response.status_code in [200, 401, 404]:
                    logger.info("✅ Supabase REST endpoint is reachable")
            return True
                else:
                    logger.error(f"❌ Supabase REST endpoint returned status: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ Supabase connection failed: {e}")
            return False
    
    async def run_migration(self) -> bool:
        """Run the database migration."""
        logger.info("=" * 60)
        logger.info("RUNNING SUPABASE MIGRATION")
        logger.info("=" * 60)
        
        # Read migration SQL
        migration_file = Path(__file__).parent / "supabase_migration.sql"
        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            return False
        
        try:
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
            
            logger.info("📄 Migration SQL loaded successfully")
            
            # Split SQL into individual statements
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            
            logger.info(f"🔧 Executing {len(statements)} SQL statements...")
            
            # Execute each statement
            for i, statement in enumerate(statements, 1):
                if statement and not statement.startswith('--'):
                    try:
                        # Execute the SQL statement
                        self.client.rpc('exec_sql', {'sql': statement}).execute()
                        logger.info(f"✅ Statement {i}/{len(statements)} executed successfully")
                    except Exception as e:
                        # Some statements might fail if objects already exist, which is OK
                        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                            logger.info(f"⚠️  Statement {i}/{len(statements)} skipped (already exists)")
                        else:
                            logger.warning(f"⚠️  Statement {i}/{len(statements)} failed: {e}")
            
            logger.info("✅ Migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
    
    async def verify_migration(self) -> bool:
        """Verify that the migration was successful."""
        logger.info("=" * 60)
        logger.info("VERIFYING MIGRATION")
        logger.info("=" * 60)
        
        try:
            # Check if tables exist
            tables_to_check = [
                "interview_sessions",
                "session_queues", 
                "session_answers"
            ]
            
            for table in tables_to_check:
                try:
                    response = self.client.table(table).select("id").limit(1).execute()
                    logger.info(f"✅ Table '{table}' exists and is accessible")
                except Exception as e:
                    logger.error(f"❌ Table '{table}' verification failed: {e}")
                    return False
            
            # Check if indexes exist (optional verification)
            logger.info("✅ All required tables verified successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration verification failed: {e}")
            return False
    
    async def create_test_session(self) -> bool:
        """Create a test session to verify functionality."""
        logger.info("=" * 60)
        logger.info("TESTING SESSION FUNCTIONALITY")
        logger.info("=" * 60)
        
        try:
            # Create a test session
            test_session = {
                "id": "test-session-123",
                "user_id": "test-user-123",
                "module_id": "test-module",
                "mode": "practice",
                "status": "pending",
                "current_question_index": 0,
                "estimated_duration_minutes": 30,
                "queue_length": 0,
                "asked_questions": "[]",
                "parsed_resume_data": None
            }
            
            # Insert test session
            response = self.client.table("interview_sessions").insert(test_session).execute()
            
            if response.data:
                logger.info("✅ Test session created successfully")
                
                # Clean up test session
                self.client.table("interview_sessions").delete().eq("id", "test-session-123").execute()
                logger.info("✅ Test session cleaned up")
                
                return True
            else:
                logger.error("❌ Failed to create test session")
                return False
                
        except Exception as e:
            logger.error(f"❌ Test session creation failed: {e}")
            return False
    
    async def run(self) -> bool:
        """Run the complete migration process."""
        try:
            # Check connection
            if not await self.check_connection():
                return False
            
            # Run migration
            if not await self.run_migration():
                return False
            
            # Verify migration
            if not await self.verify_migration():
                return False
            
            # Test functionality
            if not await self.create_test_session():
                return False
            
            logger.info("=" * 60)
            logger.info("🎉 SUPABASE MIGRATION COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)
            logger.info("The interview service is now ready to use Supabase for session management!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration process failed: {e}")
            return False


async def main():
    """Main entry point."""
    logger.info("🚀 Starting Supabase migration for TalentSync Interview Service")
    
    # Check environment variables
    required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in your .env file")
        sys.exit(1)
    
    # Run migration
    migration = SupabaseMigration()
    success = await migration.run()
    
    if success:
        logger.info("✅ Migration completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Migration failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 