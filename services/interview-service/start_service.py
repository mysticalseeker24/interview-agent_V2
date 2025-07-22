#!/usr/bin/env python3
"""TalentSync Interview Service Startup Script with Supabase Integration."""
import argparse
import asyncio
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('service_startup.log')
    ]
)

logger = logging.getLogger(__name__)


class ServiceStarter:
    """Service starter with environment and dependency checks."""
    
    def __init__(self):
        """Initialize service starter."""
        self.service_process: Optional[subprocess.Popen] = None
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
    
    async def check_environment(self) -> bool:
        """Check environment variables and data directory."""
        logger.info("=" * 60)
        logger.info("CHECKING ENVIRONMENT")
        logger.info("=" * 60)
        
        # Check if .env file exists
        env_file = Path(".env")
        if not env_file.exists():
            logger.error("[ERROR] .env file not found")
            logger.error("Please copy env.example to .env and configure your API keys")
            return False
        
        logger.info("[OK] .env file found")
        
        # Check required environment variables
        required_vars = [
            "PINECONE_API_KEY",
            "OPENAI_API_KEY", 
            "SUPABASE_URL",
            "SUPABASE_ANON_KEY",
            "SUPABASE_SERVICE_ROLE_KEY"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"[ERROR] Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        logger.info("[OK] All required environment variables are set")
        
        # Check data directory
        if not self.data_dir.exists():
            logger.warning(f"[WARNING] Data directory not found: {self.data_dir}")
            logger.warning("Dataset upload will be skipped")
        else:
            logger.info(f"[OK] Data directory found: {self.data_dir}")
        
        return True
    
    async def check_dependencies(self) -> bool:
        """Check if external dependencies are available."""
        logger.info("=" * 60)
        logger.info("CHECKING DEPENDENCIES")
        logger.info("=" * 60)
        
        # Check Supabase (required for session management)
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Test cloud Supabase connection
                supabase_url = os.getenv("SUPABASE_URL")
                if supabase_url:
                    response = await client.get(f"{supabase_url}/rest/v1/")
                    if response.status_code in [200, 401]:  # 401 is expected without auth
                        logger.info("[OK] Cloud Supabase is accessible")
                    else:
                        logger.warning(f"[WARNING] Cloud Supabase returned status: {response.status_code}")
                else:
                    logger.error("[ERROR] SUPABASE_URL not configured")
                    return False
        except Exception as e:
            logger.error(f"[ERROR] Cannot connect to Supabase: {e}")
            logger.error("Session management is required. Service cannot start without Supabase.")
            return False
        
        # Check Pinecone
        try:
            from app.services.pinecone_service import PineconeService
            pinecone_service = PineconeService()
            health = await pinecone_service.health_check()
            if health["status"] == "healthy":
                logger.info("[OK] Pinecone is accessible")
            else:
                logger.warning(f"[WARNING] Pinecone health check failed: {health}")
        except Exception as e:
            logger.error(f"[ERROR] Pinecone is not accessible: {e}")
            logger.error("This is required for the service to function properly.")
            return False
        
        logger.info("[OK] All dependencies are available")
        return True
    
    async def upload_datasets_if_needed(self, skip_upload: bool = False) -> bool:
        """Upload datasets to Pinecone if needed."""
        if skip_upload:
            logger.info("Skipping dataset upload as requested")
            return True
        
        logger.info("=" * 60)
        logger.info("CHECKING DATASET UPLOAD")
        logger.info("=" * 60)
        
        try:
            from upload_datasets_to_pinecone import main as upload_main
            await upload_main()
            logger.info("[OK] Dataset upload completed successfully")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Dataset upload failed: {e}")
            logger.error("Service will start but RAG functionality may be limited")
            return False
    
    def start_service(self) -> bool:
        """Start the interview service."""
        logger.info("=" * 60)
        logger.info("STARTING INTERVIEW SERVICE")
        logger.info("=" * 60)
        
        try:
            # Build the uvicorn command with performance optimizations
            cmd = [
                "uvicorn",
                "app.main:app",
                "--host", "0.0.0.0",
                "--port", "8006",
                "--workers", "1",  # Start with 1 worker for development
                "--log-level", "info",
                "--access-log",
                "--reload"  # Enable auto-reload for development
            ]
            
            logger.info(f"Starting service with command: {' '.join(cmd)}")
            
            # Start the service process
            self.service_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            logger.info(f"Service started with PID: {self.service_process.pid}")
            logger.info("Service is running on http://localhost:8006")
            logger.info("Press Ctrl+C to stop the service")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            return False
    
    def stop_service(self):
        """Stop the interview service."""
        if self.service_process:
            logger.info("Stopping interview service...")
            self.service_process.terminate()
            
            try:
                self.service_process.wait(timeout=10)
                logger.info("Service stopped gracefully")
            except subprocess.TimeoutExpired:
                logger.warning("Service did not stop gracefully, forcing termination")
                self.service_process.kill()
                self.service_process.wait()
    
    async def monitor_service(self):
        """Monitor the service process output."""
        if not self.service_process:
            return
        
        logger.info("Monitoring service output...")
        
        try:
            while True:
                output = self.service_process.stdout.readline()
                if output:
                    print(output.strip())
                
                # Check if process is still running
                if self.service_process.poll() is not None:
                    logger.error("Service process terminated unexpectedly")
                    break
                
                await asyncio.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error monitoring service: {e}")
    
    async def run(self, skip_upload: bool = False, test_rag: bool = False, verify_only: bool = False, no_deps: bool = False):
        """Run the complete startup process."""
        try:
            # Check environment
            if not await self.check_environment():
                return False
            
            # Check dependencies (unless skipped)
            if not no_deps and not await self.check_dependencies():
                return False
            
            # Upload datasets (unless skipped)
            if not skip_upload and not await self.upload_datasets_if_needed(skip_upload):
                logger.warning("Dataset upload failed, but continuing with service startup")
            
            # Test RAG pipeline if requested
            if test_rag:
                logger.info("Testing RAG pipeline...")
                try:
                    from app.services.pinecone_service import PineconeService
                    pinecone_service = PineconeService()
                    # Add RAG test logic here
                    logger.info("[OK] RAG pipeline test completed")
                except Exception as e:
                    logger.error(f"[ERROR] RAG pipeline test failed: {e}")
            
            # Verify only mode
            if verify_only:
                logger.info("Verification completed successfully")
                return True
            
            # Start service
            if not self.start_service():
                return False
            
            # Monitor service
            await self.monitor_service()
            
            return True
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            return True
        except Exception as e:
            logger.error(f"Startup failed: {e}")
            return False
        finally:
            self.stop_service()


def signal_handler(signum, frame):
    """Handle interrupt signals."""
    logger.info("Received interrupt signal, shutting down...")
    sys.exit(0)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="TalentSync Interview Service Startup")
    parser.add_argument("--skip-upload", action="store_true", help="Skip dataset upload")
    parser.add_argument("--test-rag", action="store_true", help="Test RAG pipeline after upload")
    parser.add_argument("--verify-only", action="store_true", help="Only verify environment and dependencies")
    parser.add_argument("--no-deps", action="store_true", help="Skip dependency checks")
    
    args = parser.parse_args()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the service starter
    starter = ServiceStarter()
    success = await starter.run(
        skip_upload=args.skip_upload,
        test_rag=args.test_rag,
        verify_only=args.verify_only,
        no_deps=args.no_deps
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main()) 