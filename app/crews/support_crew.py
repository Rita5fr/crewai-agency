"""
Support Crew - CrewAI implementation for customer support workflows.
"""
from typing import Any

from crewai import Agent, Task, Crew, LLM
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import get_settings, Settings


def _get_crewai_llm(meta: dict[str, Any] | None, settings: Settings) -> tuple[LLM, str, str]:
    """
    Create a CrewAI-compatible LLM from meta and settings.
    
    Returns:
        tuple: (LLM instance, provider name, model name)
    """
    meta = meta or {}
    
    # Determine provider
    provider = meta.get("llm_provider", settings.default_llm_provider)
    
    if provider == "anthropic":
        model = meta.get("model", settings.anthropic_model)
        llm = LLM(
            model=model,
            temperature=0.7,
            timeout=settings.request_timeout_seconds
        )
        return llm, "anthropic", model
    
    elif provider == "google":
        model = meta.get("model", settings.gemini_model)
        # CrewAI uses "gemini/" prefix for Google models
        llm = LLM(
            model=f"gemini/{model}" if not model.startswith("gemini/") else model,
            temperature=0.7,
            timeout=settings.request_timeout_seconds
        )
        return llm, "google", model
    
    elif provider == "deepseek":
        model = meta.get("model", settings.deepseek_model)
        # CrewAI/LiteLLM uses "deepseek/" prefix for DeepSeek models
        llm = LLM(
            model=f"deepseek/{model}" if not model.startswith("deepseek/") else model,
            temperature=0.7,
            timeout=settings.request_timeout_seconds
        )
        return llm, "deepseek", model
    
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


class SupportCrew:
    """
    Support Crew for customer support automation.
    Uses CrewAI with one agent and one task.
    """
    
    def __init__(self):
        self.settings = get_settings()
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError))
    )
    def _execute_crew(self, crew: Crew) -> str:
        """Execute the crew with retry logic."""
        result = crew.kickoff()
        return result.raw if hasattr(result, 'raw') else str(result)
    
    def run(self, payload: dict, meta: dict | None, trace_id: str) -> dict:
        """
        Run the support crew with the provided input.
        
        Args:
            payload: Input data - requires 'issue' field
            meta: Optional metadata with llm_provider and model overrides
            trace_id: Unique trace ID for the request
            
        Returns:
            dict: Result of the crew execution
        """
        # Validate required fields
        if "issue" not in payload:
            raise ValueError("payload must contain 'issue' field")
        
        issue = payload["issue"]
        customer_context = payload.get("customer_context", "general customer")
        
        # Get LLM
        llm, provider, model = _get_crewai_llm(meta, self.settings)
        
        # Create agent
        support_agent = Agent(
            role="Customer Support Specialist",
            goal=f"Provide helpful and empathetic support for: {issue}",
            backstory="You are a skilled customer support specialist known for resolving issues quickly while maintaining excellent customer relationships.",
            llm=llm,
            verbose=False
        )
        
        # Create task
        task = Task(
            description=f"Draft a helpful response to this customer issue: '{issue}'. Context: {customer_context}. Be empathetic and solution-oriented.",
            expected_output="A helpful customer support response (2-4 sentences)",
            agent=support_agent
        )
        
        # Create and run crew
        crew = Crew(
            agents=[support_agent],
            tasks=[task],
            verbose=False
        )
        
        output = self._execute_crew(crew)
        
        return {
            "workflow": "support",
            "trace_id": trace_id,
            "provider": provider,
            "model": model,
            "output": output,
            "input_summary": {
                "issue": issue,
                "customer_context": customer_context
            }
        }
    
    def kickoff(self) -> str:
        """Legacy method for compatibility."""
        return "Support Crew finished"
