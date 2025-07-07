"""
Monitoring and Metrics Module for Transcription Service

This module provides comprehensive monitoring capabilities including:
- Performance metrics collection
- Health check endpoints
- Error tracking and alerting
- Usage statistics
- Service observability
"""

import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)

@dataclass
class MetricPoint:
    """Represents a single metric measurement."""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class HealthCheckResult:
    """Represents the result of a health check."""
    component: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: str
    timestamp: datetime
    duration_ms: float
    details: Dict[str, Any] = field(default_factory=dict)

class MetricsCollector:
    """Collects and manages performance metrics."""
    
    def __init__(self, max_points: int = 10000):
        self.max_points = max_points
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_points))
        self.counters: Dict[str, int] = defaultdict(int)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        self.health_checks: Dict[str, HealthCheckResult] = {}
        self._lock = asyncio.Lock()
    
    async def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a metric point."""
        async with self._lock:
            point = MetricPoint(
                timestamp=datetime.utcnow(),
                value=value,
                tags=tags or {}
            )
            self.metrics[name].append(point)
            logger.debug(f"Recorded metric {name}: {value}")
    
    async def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        async with self._lock:
            self.counters[name] += value
            await self.record_metric(f"{name}_total", self.counters[name], tags)
    
    async def record_timing(self, name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None):
        """Record a timing metric."""
        async with self._lock:
            self.timers[name].append(duration_ms)
            # Keep only last 1000 timing measurements
            if len(self.timers[name]) > 1000:
                self.timers[name] = self.timers[name][-1000:]
            await self.record_metric(f"{name}_duration_ms", duration_ms, tags)
    
    async def get_metric_summary(self, name: str, window_minutes: int = 60) -> Dict[str, Any]:
        """Get summary statistics for a metric."""
        async with self._lock:
            if name not in self.metrics:
                return {"error": f"Metric {name} not found"}
            
            cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
            recent_points = [
                point for point in self.metrics[name]
                if point.timestamp > cutoff_time
            ]
            
            if not recent_points:
                return {"error": f"No recent data for {name}"}
            
            values = [point.value for point in recent_points]
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "latest": values[-1] if values else None,
                "window_minutes": window_minutes
            }
    
    async def get_timing_summary(self, name: str) -> Dict[str, Any]:
        """Get timing statistics for a metric."""
        async with self._lock:
            if name not in self.timers:
                return {"error": f"Timer {name} not found"}
            
            values = self.timers[name]
            if not values:
                return {"error": f"No timing data for {name}"}
            
            sorted_values = sorted(values)
            count = len(sorted_values)
            
            return {
                "count": count,
                "min_ms": min(sorted_values),
                "max_ms": max(sorted_values),
                "avg_ms": sum(sorted_values) / count,
                "median_ms": sorted_values[count // 2],
                "p95_ms": sorted_values[int(count * 0.95)] if count > 0 else 0,
                "p99_ms": sorted_values[int(count * 0.99)] if count > 0 else 0,
            }
    
    async def record_health_check(self, result: HealthCheckResult):
        """Record a health check result."""
        async with self._lock:
            self.health_checks[result.component] = result
            logger.info(f"Health check {result.component}: {result.status} - {result.message}")
    
    async def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics data."""
        async with self._lock:
            return {
                "counters": dict(self.counters),
                "metrics_summary": {
                    name: await self.get_metric_summary(name)
                    for name in self.metrics.keys()
                },
                "timers_summary": {
                    name: await self.get_timing_summary(name)
                    for name in self.timers.keys()
                },
                "health_checks": {
                    name: {
                        "status": result.status,
                        "message": result.message,
                        "timestamp": result.timestamp.isoformat(),
                        "duration_ms": result.duration_ms
                    }
                    for name, result in self.health_checks.items()
                }
            }

class PerformanceMonitor:
    """Context manager for performance monitoring."""
    
    def __init__(self, metrics_collector: MetricsCollector, operation: str, tags: Optional[Dict[str, str]] = None):
        self.metrics_collector = metrics_collector
        self.operation = operation
        self.tags = tags or {}
        self.start_time = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        await self.metrics_collector.increment_counter(f"{self.operation}_started", tags=self.tags)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        await self.metrics_collector.record_timing(self.operation, duration_ms, self.tags)
        
        if exc_type is None:
            await self.metrics_collector.increment_counter(f"{self.operation}_success", tags=self.tags)
        else:
            await self.metrics_collector.increment_counter(f"{self.operation}_error", tags=self.tags)
            logger.error(f"Operation {self.operation} failed: {exc_val}")

class HealthChecker:
    """Performs health checks on various system components."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
    
    async def check_database_health(self) -> HealthCheckResult:
        """Check database connectivity and performance."""
        start_time = time.time()
        
        try:
            from app.core.database import get_session
            
            # Simple connectivity test
            async for session in get_session():
                # Execute a simple query
                result = await session.execute("SELECT 1")
                result.fetchone()
                break
            
            duration_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                component="database",
                status="healthy",
                message="Database connection successful",
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                details={"query_duration_ms": duration_ms}
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="database",
                status="unhealthy",
                message=f"Database connection failed: {str(e)}",
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                details={"error": str(e)}
            )
    
    async def check_openai_health(self) -> HealthCheckResult:
        """Check OpenAI API connectivity."""
        start_time = time.time()
        
        try:
            import openai
            import os
            
            # Check if API key is configured
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return HealthCheckResult(
                    component="openai",
                    status="unhealthy",
                    message="OpenAI API key not configured",
                    timestamp=datetime.utcnow(),
                    duration_ms=0,
                    details={"error": "Missing API key"}
                )
            
            # Test API connectivity (without making actual request)
            client = openai.OpenAI(api_key=api_key)
            
            duration_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                component="openai",
                status="healthy",
                message="OpenAI client configured successfully",
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                details={"api_key_configured": True}
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="openai",
                status="degraded",
                message=f"OpenAI setup issue: {str(e)}",
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                details={"error": str(e)}
            )
    
    async def check_disk_space(self) -> HealthCheckResult:
        """Check available disk space."""
        start_time = time.time()
        
        try:
            import shutil
            
            # Check disk space in current directory
            total, used, free = shutil.disk_usage(".")
            
            # Convert to GB
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            free_gb = free / (1024**3)
            
            usage_percent = (used / total) * 100
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Determine health status based on usage
            if usage_percent > 95:
                status = "unhealthy"
                message = f"Disk space critically low: {usage_percent:.1f}% used"
            elif usage_percent > 85:
                status = "degraded"
                message = f"Disk space running low: {usage_percent:.1f}% used"
            else:
                status = "healthy"
                message = f"Disk space adequate: {usage_percent:.1f}% used"
            
            return HealthCheckResult(
                component="disk",
                status=status,
                message=message,
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                details={
                    "total_gb": round(total_gb, 2),
                    "used_gb": round(used_gb, 2),
                    "free_gb": round(free_gb, 2),
                    "usage_percent": round(usage_percent, 1)
                }
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="disk",
                status="unhealthy",
                message=f"Disk space check failed: {str(e)}",
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                details={"error": str(e)}
            )
    
    async def check_memory_usage(self) -> HealthCheckResult:
        """Check memory usage."""
        start_time = time.time()
        
        try:
            import psutil
            
            # Get memory usage
            memory = psutil.virtual_memory()
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Determine health status
            if memory.percent > 90:
                status = "unhealthy"
                message = f"Memory usage critically high: {memory.percent}%"
            elif memory.percent > 75:
                status = "degraded"
                message = f"Memory usage high: {memory.percent}%"
            else:
                status = "healthy"
                message = f"Memory usage normal: {memory.percent}%"
            
            return HealthCheckResult(
                component="memory",
                status=status,
                message=message,
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                details={
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "percent_used": memory.percent
                }
            )
            
        except ImportError:
            # psutil not available, return basic info
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="memory",
                status="healthy",
                message="Memory monitoring not available (psutil not installed)",
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                details={"psutil_available": False}
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="memory",
                status="unhealthy",
                message=f"Memory check failed: {str(e)}",
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                details={"error": str(e)}
            )
    
    async def run_all_health_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all health checks."""
        checks = [
            ("database", self.check_database_health),
            ("openai", self.check_openai_health),
            ("disk", self.check_disk_space),
            ("memory", self.check_memory_usage),
        ]
        
        results = {}
        for component, check_func in checks:
            try:
                result = await check_func()
                results[component] = result
                await self.metrics_collector.record_health_check(result)
            except Exception as e:
                logger.error(f"Health check {component} failed: {e}")
                result = HealthCheckResult(
                    component=component,
                    status="unhealthy",
                    message=f"Health check failed: {str(e)}",
                    timestamp=datetime.utcnow(),
                    duration_ms=0,
                    details={"error": str(e)}
                )
                results[component] = result
        
        return results

class ServiceMonitor:
    """Main service monitoring class."""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.health_checker = HealthChecker(self.metrics_collector)
        self._monitoring_task = None
        self._is_running = False
    
    async def start_monitoring(self, interval_seconds: int = 60):
        """Start background monitoring."""
        if self._is_running:
            return
        
        self._is_running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop(interval_seconds))
        logger.info(f"Started monitoring with {interval_seconds}s interval")
    
    async def stop_monitoring(self):
        """Stop background monitoring."""
        if not self._is_running:
            return
        
        self._is_running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped monitoring")
    
    async def _monitoring_loop(self, interval_seconds: int):
        """Background monitoring loop."""
        while self._is_running:
            try:
                # Run health checks
                await self.health_checker.run_all_health_checks()
                
                # Record system metrics
                await self.metrics_collector.record_metric("monitoring_loop_execution", 1.0)
                
                # Wait for next interval
                await asyncio.sleep(interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(interval_seconds)
    
    def get_performance_monitor(self, operation: str, tags: Optional[Dict[str, str]] = None) -> PerformanceMonitor:
        """Get a performance monitor context manager."""
        return PerformanceMonitor(self.metrics_collector, operation, tags)
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Get overall service health."""
        health_results = await self.health_checker.run_all_health_checks()
        
        # Determine overall status
        statuses = [result.status for result in health_results.values()]
        if "unhealthy" in statuses:
            overall_status = "unhealthy"
        elif "degraded" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                name: {
                    "status": result.status,
                    "message": result.message,
                    "duration_ms": result.duration_ms,
                    "details": result.details
                }
                for name, result in health_results.items()
            }
        }
    
    async def get_service_metrics(self) -> Dict[str, Any]:
        """Get comprehensive service metrics."""
        return await self.metrics_collector.get_all_metrics()

# Global service monitor instance
service_monitor = ServiceMonitor()

# Convenience functions for easy access
async def record_transcription_start(session_id: str, chunk_id: str):
    """Record transcription start event."""
    await service_monitor.metrics_collector.increment_counter(
        "transcription_requests",
        tags={"session_id": session_id, "chunk_id": chunk_id}
    )

async def record_transcription_success(session_id: str, chunk_id: str, duration_ms: float, confidence: float):
    """Record successful transcription."""
    await service_monitor.metrics_collector.increment_counter(
        "transcription_success",
        tags={"session_id": session_id, "chunk_id": chunk_id}
    )
    await service_monitor.metrics_collector.record_timing(
        "transcription_duration",
        duration_ms,
        tags={"session_id": session_id, "chunk_id": chunk_id}
    )
    await service_monitor.metrics_collector.record_metric(
        "transcription_confidence",
        confidence,
        tags={"session_id": session_id, "chunk_id": chunk_id}
    )

async def record_transcription_error(session_id: str, chunk_id: str, error_type: str):
    """Record transcription error."""
    await service_monitor.metrics_collector.increment_counter(
        "transcription_errors",
        tags={"session_id": session_id, "chunk_id": chunk_id, "error_type": error_type}
    )

async def record_session_completion(session_id: str, total_chunks: int, total_duration_ms: float):
    """Record session completion."""
    await service_monitor.metrics_collector.increment_counter(
        "session_completions",
        tags={"session_id": session_id}
    )
    await service_monitor.metrics_collector.record_metric(
        "session_total_chunks",
        total_chunks,
        tags={"session_id": session_id}
    )
    await service_monitor.metrics_collector.record_timing(
        "session_total_duration",
        total_duration_ms,
        tags={"session_id": session_id}
    )

# TTS-specific metrics
TTS_GENERATION_TIME = "tts_generation_time"
TTS_REQUESTS_TOTAL = "tts_requests_total"
TTS_CACHE_HITS = "tts_cache_hits"
TTS_CACHE_MISSES = "tts_cache_misses"
TTS_ERRORS = "tts_errors"
TTS_FILE_SIZE = "tts_file_size"
TTS_AUDIO_DURATION = "tts_audio_duration"

# Enhanced STT metrics
STT_ENHANCED_CONFIDENCE = "stt_enhanced_confidence"
STT_WORD_COUNT = "stt_word_count"
STT_SEGMENT_COUNT = "stt_segment_count"
STT_PROCESSING_TIME = "stt_processing_time"
