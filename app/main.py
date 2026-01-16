"""
FastAPI application entry point.
"""
import uuid
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import ORJSONResponse

from app.core.config import get_settings
from app.core.schemas import RunRequest, RunResponse
from app.core.security import require_api_key
from app.core.job_store import job_store, JobStatus
from app.utils.logging import setup_logging, set_trace_id

from app.crews.marketing_crew import MarketingCrew
from app.crews.support_crew import SupportCrew
from app.crews.analysis_crew import AnalysisCrew
from app.crews.social_media_crew import SocialMediaCrew

# Initialize logging
logger = setup_logging()

# Map crew names to their classes
CREW_MAP = {
    "marketing": MarketingCrew,
    "support": SupportCrew,
    "analysis": AnalysisCrew,
    "social_media": SocialMediaCrew,
}


def _run_crew_job(job_id: str, crew_name: str, payload: dict, meta: dict | None, trace_id: str):
    """
    Background task to run a crew job.
    
    Args:
        job_id: The job ID
        crew_name: Name of the crew to run
        payload: Input data
        meta: Optional metadata
        trace_id: Trace ID for the request
    """
    set_trace_id(trace_id)
    
    # Update job to running
    job_store.update_job(job_id, status=JobStatus.RUNNING)
    logger.info(f"Job {job_id} started for crew: {crew_name}")
    
    try:
        crew_class = CREW_MAP[crew_name]
        crew = crew_class()
        result = crew.run(payload, meta, trace_id)
        
        job_store.update_job(job_id, status=JobStatus.DONE, result=result)
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {type(e).__name__}")
        job_store.update_job(
            job_id,
            status=JobStatus.FAILED,
            error={"code": "EXECUTION_ERROR", "message": "An error occurred during crew execution"}
        )


def _cleanup_jobs_periodically():
    """Background thread to cleanup old jobs periodically."""
    import time
    while True:
        time.sleep(300)  # Every 5 minutes
        removed = job_store.cleanup_old_jobs()
        if removed > 0:
            logger.info(f"Cleaned up {removed} old jobs")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=_cleanup_jobs_periodically, daemon=True)
    cleanup_thread.start()
    logger.info("Job cleanup thread started")
    
    yield
    
    logger.info("Shutting down")


# Initialize FastAPI app
app = FastAPI(
    title="My AI Agency",
    description="AI Agency API with CrewAI crews for Marketing, Support, and Analysis",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    lifespan=lifespan
)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"ok": True}


@app.post("/crews/{crew_name}/run")
async def run_crew(
    crew_name: str,
    request: RunRequest,
    background_tasks: BackgroundTasks,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    async_mode: bool = Query(default=False, alias="async")
) -> dict:
    """
    Run a specific crew with the provided input.
    
    Args:
        crew_name: Name of the crew to run (marketing, support, analysis)
        request: Input data and optional metadata
        x_api_key: API key for authentication
        async_mode: If true, run asynchronously and return job_id
        
    Returns:
        RunResponse or async job reference
    """
    # Generate trace ID for this request
    trace_id = str(uuid.uuid4())
    set_trace_id(trace_id)
    
    logger.info(f"Received request for crew: {crew_name} (async={async_mode})")
    
    # Validate API key
    settings = get_settings()
    require_api_key(x_api_key, settings)
    
    # Check if crew exists
    if crew_name not in CREW_MAP:
        logger.warning(f"Crew not found: {crew_name}")
        return {
            "ok": False,
            "crew": crew_name,
            "trace_id": trace_id,
            "error": {"code": "CREW_NOT_FOUND", "message": f"Crew '{crew_name}' not found"}
        }
    
    # Async mode: create job and return immediately
    if async_mode:
        job = job_store.create_job(trace_id=trace_id, crew=crew_name)
        
        # Run in background thread (not asyncio task for CPU-bound work)
        thread = threading.Thread(
            target=_run_crew_job,
            args=(job.job_id, crew_name, request.input, request.meta, trace_id)
        )
        thread.start()
        
        logger.info(f"Created async job: {job.job_id}")
        
        return {
            "ok": True,
            "trace_id": trace_id,
            "crew": crew_name,
            "job_id": job.job_id
        }
    
    # Sync mode: run immediately and return result
    try:
        crew_class = CREW_MAP[crew_name]
        crew = crew_class()
        
        logger.info(f"Running crew: {crew_name}")
        result = crew.run(request.input, request.meta, trace_id)
        
        logger.info(f"Crew {crew_name} completed successfully")
        
        return {
            "ok": True,
            "crew": crew_name,
            "trace_id": trace_id,
            "result": result,
            "error": None
        }
        
    except Exception as e:
        logger.error(f"Crew {crew_name} failed: {type(e).__name__}")
        
        return {
            "ok": False,
            "crew": crew_name,
            "trace_id": trace_id,
            "result": None,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": "An error occurred during crew execution"
            }
        }


@app.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    x_api_key: str | None = Header(default=None, alias="X-API-Key")
) -> dict:
    """
    Get the status of an async job.
    
    Args:
        job_id: The job ID
        x_api_key: API key for authentication
        
    Returns:
        Job status and result if completed
    """
    # Validate API key
    settings = get_settings()
    require_api_key(x_api_key, settings)
    
    job = job_store.get_job(job_id)
    
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found"
        )
    
    return {
        "ok": True,
        "job_id": job.job_id,
        "status": job.status.value,
        "crew": job.crew,
        "trace_id": job.trace_id,
        "result": job.result,
        "error": job.error
    }
