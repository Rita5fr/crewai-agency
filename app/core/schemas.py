"""
Pydantic schemas for API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Any


class RunRequest(BaseModel):
    """Request body for running a crew."""
    input: dict[str, Any] = Field(..., description="Input data for the crew")
    meta: dict[str, Any] | None = Field(default=None, description="Optional metadata")


class RunResponse(BaseModel):
    """Response body from a crew run."""
    ok: bool = Field(..., description="Whether the request succeeded")
    crew: str = Field(..., description="Name of the crew that was executed")
    trace_id: str = Field(..., description="Unique trace ID for this request")
    result: dict[str, Any] | None = Field(default=None, description="Result data if successful")
    error: dict[str, str] | None = Field(default=None, description="Error details if failed")
