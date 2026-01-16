"""
In-memory job store with thread-safe operations and TTL cleanup.
"""
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class JobStatus(str, Enum):
    """Job execution status."""
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Job:
    """Represents an async job."""
    job_id: str
    trace_id: str
    crew: str
    status: JobStatus = JobStatus.QUEUED
    result: dict[str, Any] | None = None
    error: dict[str, str] | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class JobStore:
    """
    Thread-safe in-memory job store with TTL cleanup.
    """
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize the job store.
        
        Args:
            ttl_seconds: Time-to-live for jobs in seconds (default: 1 hour)
        """
        self._jobs: dict[str, Job] = {}
        self._lock = threading.RLock()
        self._ttl_seconds = ttl_seconds
    
    def create_job(self, trace_id: str, crew: str) -> Job:
        """
        Create a new job in QUEUED status.
        
        Args:
            trace_id: Trace ID for the request
            crew: Name of the crew to execute
            
        Returns:
            Job: The created job
        """
        job_id = str(uuid.uuid4())
        job = Job(job_id=job_id, trace_id=trace_id, crew=crew)
        
        with self._lock:
            self._jobs[job_id] = job
        
        return job
    
    def get_job(self, job_id: str) -> Job | None:
        """
        Get a job by ID.
        
        Args:
            job_id: The job ID
            
        Returns:
            Job or None if not found
        """
        with self._lock:
            return self._jobs.get(job_id)
    
    def update_job(
        self,
        job_id: str,
        status: JobStatus | None = None,
        result: dict[str, Any] | None = None,
        error: dict[str, str] | None = None
    ) -> Job | None:
        """
        Update a job's status and/or result.
        
        Args:
            job_id: The job ID
            status: New status (optional)
            result: Result data (optional)
            error: Error data (optional)
            
        Returns:
            Updated Job or None if not found
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            
            if status is not None:
                job.status = status
            if result is not None:
                job.result = result
            if error is not None:
                job.error = error
            
            job.updated_at = time.time()
            return job
    
    def cleanup_old_jobs(self) -> int:
        """
        Remove jobs older than TTL.
        
        Returns:
            int: Number of jobs removed
        """
        now = time.time()
        cutoff = now - self._ttl_seconds
        
        with self._lock:
            old_job_ids = [
                job_id for job_id, job in self._jobs.items()
                if job.created_at < cutoff
            ]
            
            for job_id in old_job_ids:
                del self._jobs[job_id]
            
            return len(old_job_ids)
    
    def get_stats(self) -> dict[str, int]:
        """Get job store statistics."""
        with self._lock:
            status_counts = {}
            for job in self._jobs.values():
                status_counts[job.status.value] = status_counts.get(job.status.value, 0) + 1
            return {
                "total": len(self._jobs),
                **status_counts
            }


# Global job store instance
job_store = JobStore(ttl_seconds=3600)
