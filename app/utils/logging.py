"""
Logging configuration with trace ID support.
"""
import logging
import sys
from contextvars import ContextVar

# Context variable to store the current trace ID
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="-")


class TraceIdFilter(logging.Filter):
    """Logging filter that adds trace_id to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = trace_id_var.get()
        return True


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging with trace ID included in the format.
    
    Args:
        level: Logging level (default: INFO)
        
    Returns:
        Logger: Configured logger instance
    """
    # Create formatter with trace_id
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | trace_id=%(trace_id)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(TraceIdFilter())
    
    # Configure root logger
    logger = logging.getLogger("my_ai_agency")
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False
    
    return logger


def set_trace_id(trace_id: str) -> None:
    """Set the current trace ID for logging context."""
    trace_id_var.set(trace_id)


def get_trace_id() -> str:
    """Get the current trace ID from logging context."""
    return trace_id_var.get()
