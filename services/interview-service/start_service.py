#!/usr/bin/env python3
"""
TalentSync Interview Service Startup Script

This script starts the interview service with proper dependency handling.
It can optionally upload datasets to Pinecone and handle missing dependencies gracefully.

Usage:
    python start_service.py [--skip-upload] [--test-rag] [--verify-only] [--no-deps]
"""

import asyncio
import logging
import os
import sys
import subprocess
import time
import signal
from pathlib import Path
from typing import Optional
import argparse
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('service_startup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ServiceStarter:
    """Manages the startup process for TalentSync Interview Service."""
    
    def __init__(self):
        """Initialize the service starter."""
        self.service_process = None
        self.uploader = None
        
    async def check_environment(self) -> bool:
        """Check if the environment is properly configured."""
        logger.info("=" * 60)
        logger.info("CHECKING ENVIRONMENT")
        logger.info("=" * 60)
        
        try:
            # Import settings to validate environment variables
            from app.core.settings import settings
            
            # Check if settings loaded successfully
            logger.info(f"[OK] Service name: {settings.APP_NAME}")
            logger.info(f"[OK] Service version: {settings.APP_VERSION}")
            logger.info(f"[OK] Pinecone environment: {settings.PINECONE_ENV}")
            logger.info(f"[OK] OpenAI model: {settings.OPENAI_CHAT_MODEL}")
            logger.info(f"[OK] Supabase URL: {settings.SUPABASE_URL}")
            
            logger.info("[OK] All required environment variables are set and valid")
            
        except Exception as e:
            logger.error(f"Environment configuration error: {e}")
            logger.error("Please check your .env file and ensure all required variables are set.")
            return False
        
        # Check if data directory exists
        data_dir = Path(__file__).parent.parent.parent / "data"
        if not data_dir.exists():
            logger.error(f"Data directory not found: {data_dir}")
            return False
        
        logger.info(f"[OK] Data directory found: {data_dir}")
        
        # Check if dataset files exist
        json_files = list(data_dir.glob("*.json"))
        if not json_files:
            logger.error(f"No JSON dataset files found in {data_dir}")
            return False
        
        logger.info(f"[OK] Found {len(json_files)} dataset files")
        
        return True
    
    async def check_dependencies(self) -> bool:
        """Check if external dependencies are available."""
        logger.info("=" * 60)
        logger.info("CHECKING DEPENDENCIES")
        logger.info("=" * 60)
        
        # Check Redis
        try:
            import redis.asyncio as redis
            redis_client = redis.from_url("redis://localhost:6379/0")
            await redis_client.ping()
            await redis_client.close()
            logger.info("[OK] Redis is running")
        except Exception as e:
            logger.warning(f"[WARNING] Redis is not available: {e}")
            logger.warning("Session management will be limited. Consider starting Redis.")
        
        # Check Supabase (optional for development)
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://127.0.0.1:54321/health")
                if response.status_code == 200:
                    logger.info("[OK] Local Supabase is running")
                else:
                    logger.warning("[WARNING] Local Supabase is not responding properly")
        except Exception as e:
            logger.warning(f"[WARNING] Local Supabase is not available: {e}")
            logger.warning("Authentication will use mock mode. Consider starting Supabase.")
        
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
        
        return True
    
    async def upload_datasets_if_needed(self, skip_upload: bool = False) -> bool:
        """Upload datasets to Pinecone if not already uploaded."""
        if skip_upload:
            logger.info("Skipping dataset upload as requested")
            return True
        
        try:
            # Import uploader only when needed
            from upload_datasets_to_pinecone import DatasetUploader
            self.uploader = DatasetUploader()
            
            logger.info("=" * 60)
            logger.info("UPLOADING DATASETS TO PINECONE")
            logger.info("=" * 60)
            
            # Check if datasets are already uploaded
            logger.info("Checking if datasets are already uploaded...")
            verification = await self.uploader.verify_upload()
            
            if verification and verification.get('index_stats', {}).get('total_vector_count', 0) > 0:
                logger.info("[OK] Datasets appear to be already uploaded")
                logger.info(f"Found {verification['index_stats']['total_vector_count']} vectors in Pinecone")
                return True
            
            logger.info("No existing datasets found, starting upload...")
            
            # Upload all datasets
            results = await self.uploader.upload_all_datasets()
            
            # Verify upload
            await self.uploader.verify_upload()
            
            total_uploaded = sum(results.values())
            if total_uploaded > 0:
                logger.info(f"[OK] Successfully uploaded {total_uploaded} questions to Pinecone")
                return True
            else:
                logger.error("No questions were uploaded successfully")
                return False
                
        except Exception as e:
            logger.error(f"Error during dataset upload: {e}")
            return False
    
    def start_service(self) -> bool:
        """Start the FastAPI service using uvicorn."""
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
                cwd=os.path.dirname(__file__),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            logger.info(f"[OK] Interview service started with PID: {self.service_process.pid}")
            logger.info("Service is running on http://localhost:8006")
            logger.info("API documentation available at http://localhost:8006/docs")
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting service: {e}")
            return False
    
    def stop_service(self):
        """Stop the running service."""
        if self.service_process:
            logger.info("Stopping interview service...")
            self.service_process.terminate()
            try:
                self.service_process.wait(timeout=10)
                logger.info("[OK] Service stopped gracefully")
            except subprocess.TimeoutExpired:
                logger.warning("Service didn't stop gracefully, forcing termination...")
                self.service_process.kill()
                self.service_process.wait()
                logger.info("[OK] Service force stopped")
    
    async def monitor_service(self):
        """Monitor the service process and handle output."""
        if not self.service_process:
            return
        
        try:
            # Read output from the service process
            for line in iter(self.service_process.stdout.readline, ''):
                if line:
                    # Log the service output
                    logger.info(f"SERVICE: {line.strip()}")
                    
                    # Check if service has started successfully
                    if "Uvicorn running on" in line:
                        logger.info("[OK] Service is now running and accepting requests")
                    
                    # Check for startup errors
                    if "Error" in line and "startup" in line.lower():
                        logger.error(f"Service startup error detected: {line.strip()}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error monitoring service: {e}")
            return False
        
        return True
    
    async def run(self, skip_upload: bool = False, test_rag: bool = False, verify_only: bool = False, no_deps: bool = False):
        """Run the complete startup process."""
        try:
            # Check environment
            if not await self.check_environment():
                logger.error("Environment check failed")
                return False
            
            # Check dependencies (optional)
            if not no_deps:
                if not await self.check_dependencies():
                    logger.error("Dependency check failed")
                    return False
            
            if verify_only:
                # Only verify existing setup
                if self.uploader:
                    await self.uploader.verify_upload()
                return True
            
            # Upload datasets
            if not await self.upload_datasets_if_needed(skip_upload):
                logger.error("Dataset upload failed")
                return False
            
            # Start service
            if not self.start_service():
                logger.error("Failed to start service")
                return False
            
            logger.info("=" * 60)
            logger.info("TALENTSYNC INTERVIEW SERVICE STARTED SUCCESSFULLY")
            logger.info("=" * 60)
            logger.info("Service is ready to handle interview requests!")
            logger.info("Press Ctrl+C to stop the service")
            
            # Monitor the service
            try:
                await self.monitor_service()
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
                if self.service_process:
                    self.stop_service()
            
            return True
            
        except Exception as e:
            logger.error(f"Error during startup: {e}")
            if self.service_process:
                self.stop_service()
            return False


def signal_handler(signum, frame):
    """Handle interrupt signals."""
    logger.info("Received interrupt signal, shutting down...")
    sys.exit(0)


async def main():
    """Main function to run the startup process."""
    parser = argparse.ArgumentParser(description="Start TalentSync Interview Service")
    parser.add_argument("--skip-upload", action="store_true", help="Skip dataset upload")
    parser.add_argument("--test-rag", action="store_true", help="Test RAG pipeline after upload")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing setup")
    parser.add_argument("--no-deps", action="store_true", help="Skip dependency checks")
    
    args = parser.parse_args()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    starter = ServiceStarter()
    
    try:
        success = await starter.run(
            skip_upload=args.skip_upload,
            test_rag=args.test_rag,
            verify_only=args.verify_only,
            no_deps=args.no_deps
        )
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Startup process interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error during startup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 