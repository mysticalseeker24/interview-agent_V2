"""
Monitoring and metrics service for Media Service.
"""
import logging
import time
from datetime import datetime
from typing import Dict, Any

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.media import MediaChunk, MediaSession, MediaProcessingTask

logger = logging.getLogger(__name__)
settings = get_settings()

# Prometheus metrics
chunk_uploads_total = Counter(
    'media_chunk_uploads_total',
    'Total number of chunk uploads',
    ['status', 'session_id']
)

chunk_upload_duration = Histogram(
    'media_chunk_upload_duration_seconds',
    'Time spent uploading chunks',
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
)

chunk_processing_duration = Histogram(
    'media_chunk_processing_duration_seconds',
    'Time spent processing chunks',
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)

active_sessions_gauge = Gauge(
    'media_active_sessions',
    'Number of active media sessions'
)

total_chunks_gauge = Gauge(
    'media_total_chunks',
    'Total number of media chunks'
)

storage_usage_bytes = Gauge(
    'media_storage_usage_bytes',
    'Storage usage in bytes'
)

failed_uploads_total = Counter(
    'media_failed_uploads_total',
    'Total number of failed uploads',
    ['error_type']
)

processing_queue_size = Gauge(
    'media_processing_queue_size',
    'Number of items in processing queue'
)

session_completion_time = Histogram(
    'media_session_completion_time_seconds',
    'Time to complete a session',
    buckets=[60.0, 300.0, 600.0, 1800.0, 3600.0, 7200.0]
)


class MetricsService:
    """Service for collecting and exposing metrics."""
    
    def __init__(self):
        self.start_time = time.time()
    
    async def collect_database_metrics(self, db: AsyncSession) -> Dict[str, Any]:
        """Collect metrics from database."""
        try:
            # Session metrics
            result = await db.execute(select(func.count(MediaSession.id)))
            total_sessions = result.scalar() or 0
            
            result = await db.execute(
                select(func.count(MediaSession.id))
                .where(MediaSession.session_status == 'active')
            )
            active_sessions = result.scalar() or 0
            
            result = await db.execute(
                select(func.count(MediaSession.id))
                .where(MediaSession.session_status == 'completed')
            )
            completed_sessions = result.scalar() or 0
            
            # Chunk metrics
            result = await db.execute(select(func.count(MediaChunk.id)))
            total_chunks = result.scalar() or 0
            
            result = await db.execute(
                select(func.count(MediaChunk.id))
                .where(MediaChunk.upload_status == 'uploaded')
            )
            uploaded_chunks = result.scalar() or 0
            
            result = await db.execute(
                select(func.count(MediaChunk.id))
                .where(MediaChunk.upload_status == 'failed')
            )
            failed_chunks = result.scalar() or 0
            
            result = await db.execute(
                select(func.count(MediaChunk.id))
                .where(MediaChunk.transcription_status == 'processing')
            )
            processing_chunks = result.scalar() or 0
            
            # Storage metrics
            result = await db.execute(select(func.sum(MediaChunk.file_size_bytes)))
            total_storage = result.scalar() or 0
            
            result = await db.execute(select(func.avg(MediaChunk.file_size_bytes)))
            avg_chunk_size = result.scalar() or 0
            
            # Processing task metrics
            result = await db.execute(
                select(func.count(MediaProcessingTask.id))
                .where(MediaProcessingTask.task_status == 'pending')
            )
            pending_tasks = result.scalar() or 0
            
            # Update Prometheus gauges
            active_sessions_gauge.set(active_sessions)
            total_chunks_gauge.set(total_chunks)
            storage_usage_bytes.set(total_storage)
            processing_queue_size.set(pending_tasks)
            
            return {
                'sessions': {
                    'total': total_sessions,
                    'active': active_sessions,
                    'completed': completed_sessions
                },
                'chunks': {
                    'total': total_chunks,
                    'uploaded': uploaded_chunks,
                    'failed': failed_chunks,
                    'processing': processing_chunks
                },
                'storage': {
                    'total_bytes': total_storage,
                    'average_chunk_size': float(avg_chunk_size)
                },
                'processing': {
                    'pending_tasks': pending_tasks
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
            return {}
    
    def record_chunk_upload(self, session_id: str, status: str, duration: float):
        """Record chunk upload metrics."""
        chunk_uploads_total.labels(status=status, session_id=session_id).inc()
        chunk_upload_duration.observe(duration)
        
        if status == 'failed':
            failed_uploads_total.labels(error_type='upload_error').inc()
    
    def record_chunk_processing(self, duration: float, success: bool):
        """Record chunk processing metrics."""
        chunk_processing_duration.observe(duration)
        
        if not success:
            failed_uploads_total.labels(error_type='processing_error').inc()
    
    def record_session_completion(self, duration: float):
        """Record session completion metrics."""
        session_completion_time.observe(duration)
    
    async def get_health_status(self, db: AsyncSession) -> Dict[str, Any]:
        """Get comprehensive health status."""
        try:
            health_data = {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'version': settings.app_version,
                'uptime_seconds': time.time() - self.start_time,
                'components': {}
            }
            
            # Database health
            try:
                await db.execute(select(1))
                health_data['components']['database'] = 'healthy'
            except Exception as e:
                health_data['components']['database'] = f'unhealthy: {e}'
                health_data['status'] = 'degraded'
            
            # Storage health
            try:
                upload_dir = settings.upload_dir
                if upload_dir.exists() and upload_dir.is_dir():
                    health_data['components']['storage'] = 'healthy'
                else:
                    health_data['components']['storage'] = 'unhealthy: upload directory not accessible'
                    health_data['status'] = 'degraded'
            except Exception as e:
                health_data['components']['storage'] = f'unhealthy: {e}'
                health_data['status'] = 'degraded'
            
            # Redis health (for Celery)
            try:
                import redis
                r = redis.from_url(settings.redis_url)
                r.ping()
                health_data['components']['redis'] = 'healthy'
            except Exception as e:
                health_data['components']['redis'] = f'unhealthy: {e}'
                health_data['status'] = 'degraded'
            
            # Get database metrics for additional context
            db_metrics = await self.collect_database_metrics(db)
            health_data['metrics'] = db_metrics
            
            return health_data
            
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus-formatted metrics."""
        try:
            return generate_latest().decode('utf-8')
        except Exception as e:
            logger.error(f"Error generating Prometheus metrics: {e}")
            return ""


# Global metrics service instance
metrics_service = MetricsService()
