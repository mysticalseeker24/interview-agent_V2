"""
Monitoring Service for health checks and metrics.
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.media import MediaChunk, MediaSession, MediaProcessingTask

logger = logging.getLogger(__name__)
settings = get_settings()

# Global metrics storage
_metrics = {
    "chunk_uploads": {"success": 0, "failed": 0, "total_duration": 0.0},
    "chunk_processing": {"success": 0, "failed": 0, "total_duration": 0.0},
    "session_completions": {"count": 0, "total_duration": 0.0}
}

_start_time = time.time()


class MetricsService:
    """Service for collecting and providing metrics."""
    
    def __init__(self):
        self.start_time = _start_time
    
    async def collect_database_metrics(self, db: AsyncSession) -> Dict[str, Any]:
        """Collect metrics from database."""
        try:
            # Session metrics
            session_result = await db.execute(select(func.count(MediaSession.id)))
            total_sessions = session_result.scalar()
            
            active_session_result = await db.execute(
                select(func.count(MediaSession.id))
                .where(MediaSession.session_status == "active")
            )
            active_sessions = active_session_result.scalar()
            
            # Chunk metrics
            chunk_result = await db.execute(select(func.count(MediaChunk.id)))
            total_chunks = chunk_result.scalar()
            
            pending_chunk_result = await db.execute(
                select(func.count(MediaChunk.id))
                .where(MediaChunk.upload_status == "pending")
            )
            pending_chunks = pending_chunk_result.scalar()
            
            processed_chunk_result = await db.execute(
                select(func.count(MediaChunk.id))
                .where(MediaChunk.transcription_status == "completed")
            )
            processed_chunks = processed_chunk_result.scalar()
            
            failed_chunk_result = await db.execute(
                select(func.count(MediaChunk.id))
                .where(MediaChunk.upload_status == "failed")
            )
            failed_chunks = failed_chunk_result.scalar()
            
            # Storage metrics
            storage_result = await db.execute(
                select(func.sum(MediaChunk.file_size_bytes))
                .where(MediaChunk.file_size_bytes.isnot(None))
            )
            storage_used_bytes = storage_result.scalar() or 0
            
            # Average chunk size
            avg_size_result = await db.execute(
                select(func.avg(MediaChunk.file_size_bytes))
                .where(MediaChunk.file_size_bytes.isnot(None))
            )
            average_chunk_size_bytes = avg_size_result.scalar() or 0.0
            
            # Processing queue size
            queue_result = await db.execute(
                select(func.count(MediaProcessingTask.id))
                .where(MediaProcessingTask.task_status.in_(["pending", "running"]))
            )
            processing_queue_size = queue_result.scalar()
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "total_chunks": total_chunks,
                "pending_chunks": pending_chunks,
                "processed_chunks": processed_chunks,
                "failed_chunks": failed_chunks,
                "storage_used_bytes": storage_used_bytes,
                "average_chunk_size_bytes": round(average_chunk_size_bytes, 2),
                "processing_queue_size": processing_queue_size
            }
            
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
            return {
                "total_sessions": 0,
                "active_sessions": 0,
                "total_chunks": 0,
                "pending_chunks": 0,
                "processed_chunks": 0,
                "failed_chunks": 0,
                "storage_used_bytes": 0,
                "average_chunk_size_bytes": 0.0,
                "processing_queue_size": 0
            }
    
    def record_chunk_upload(self, session_id: str, status: str, duration: float):
        """Record chunk upload metrics."""
        if status == "success":
            _metrics["chunk_uploads"]["success"] += 1
        else:
            _metrics["chunk_uploads"]["failed"] += 1
        
        _metrics["chunk_uploads"]["total_duration"] += duration
        logger.debug(f"Recorded chunk upload: {status}, duration: {duration:.3f}s")
    
    def record_chunk_processing(self, duration: float, success: bool):
        """Record chunk processing metrics."""
        if success:
            _metrics["chunk_processing"]["success"] += 1
        else:
            _metrics["chunk_processing"]["failed"] += 1
        
        _metrics["chunk_processing"]["total_duration"] += duration
        logger.debug(f"Recorded chunk processing: {'success' if success else 'failed'}, duration: {duration:.3f}s")
    
    def record_session_completion(self, duration: float):
        """Record session completion metrics."""
        _metrics["session_completions"]["count"] += 1
        _metrics["session_completions"]["total_duration"] += duration
        logger.debug(f"Recorded session completion, duration: {duration:.3f}s")
    
    async def get_health_status(self, db: AsyncSession) -> Dict[str, Any]:
        """Get comprehensive health status."""
        try:
            # Database health
            db_health = "healthy"
            try:
                await db.execute(select(1))
            except Exception as e:
                db_health = "unhealthy"
                logger.error(f"Database health check failed: {e}")
            
            # Storage health
            storage_health = "healthy"
            try:
                upload_dir = settings.upload_dir
                if not upload_dir.exists():
                    upload_dir.mkdir(parents=True, exist_ok=True)
                
                # Check if we can write to the directory
                test_file = upload_dir / ".health_check"
                test_file.write_text("health_check")
                test_file.unlink()
                
            except Exception as e:
                storage_health = "unhealthy"
                logger.error(f"Storage health check failed: {e}")
            
            # Service health
            uptime_seconds = time.time() - self.start_time
            
            # Collect database metrics
            db_metrics = await self.collect_database_metrics(db)
            
            return {
                "status": "healthy" if db_health == "healthy" and storage_health == "healthy" else "degraded",
                "timestamp": datetime.utcnow().isoformat(),
                "version": settings.app_version,
                "uptime_seconds": round(uptime_seconds, 2),
                "components": {
                    "database": db_health,
                    "storage": storage_health,
                    "service": "healthy"
                },
                "metrics": {
                    **db_metrics,
                    "memory_usage_mb": self._get_memory_usage(),
                    "uptime_hours": round(uptime_seconds / 3600, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": settings.app_version,
                "uptime_seconds": round(time.time() - self.start_time, 2),
                "components": {
                    "database": "unknown",
                    "storage": "unknown",
                    "service": "unhealthy"
                },
                "error": str(e)
            }
    
    def get_prometheus_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        try:
            uptime_seconds = time.time() - self.start_time
            
            metrics = [
                f"# HELP media_service_uptime_seconds Service uptime in seconds",
                f"# TYPE media_service_uptime_seconds gauge",
                f"media_service_uptime_seconds {uptime_seconds}",
                "",
                f"# HELP media_service_chunk_uploads_total Total chunk uploads",
                f"# TYPE media_service_chunk_uploads_total counter",
                f"media_service_chunk_uploads_total{{status=\"success\"}} {_metrics['chunk_uploads']['success']}",
                f"media_service_chunk_uploads_total{{status=\"failed\"}} {_metrics['chunk_uploads']['failed']}",
                "",
                f"# HELP media_service_chunk_processing_total Total chunk processing operations",
                f"# TYPE media_service_chunk_processing_total counter",
                f"media_service_chunk_processing_total{{status=\"success\"}} {_metrics['chunk_processing']['success']}",
                f"media_service_chunk_processing_total{{status=\"failed\"}} {_metrics['chunk_processing']['failed']}",
                "",
                f"# HELP media_service_session_completions_total Total session completions",
                f"# TYPE media_service_session_completions_total counter",
                f"media_service_session_completions_total {_metrics['session_completions']['count']}",
                "",
                f"# HELP media_service_memory_usage_bytes Memory usage in bytes",
                f"# TYPE media_service_memory_usage_bytes gauge",
                f"media_service_memory_usage_bytes {self._get_memory_usage() * 1024 * 1024}"
            ]
            
            return "\n".join(metrics)
            
        except Exception as e:
            logger.error(f"Error generating Prometheus metrics: {e}")
            return f"# Error generating metrics: {e}"
    
    def _get_memory_usage(self) -> float:
        """Get memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0
        except Exception:
            return 0.0


# Global metrics service instance
metrics_service = MetricsService() 