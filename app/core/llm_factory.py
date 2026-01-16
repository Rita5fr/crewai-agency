"""
LLM Factory for creating LLM instances.

Provides a unified interface for interacting with different LLM providers
(Anthropic Claude and Google Gemini).
"""
from abc import ABC, abstractmethod
from typing import Any

import anthropic
from google import genai
from google.genai import types

from app.core.config import Settings


class BaseLLM(ABC):
    """Abstract base class for LLM wrappers."""
    
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The input prompt
            
        Returns:
            str: The generated response text
        """
        pass


class AnthropicLLM(BaseLLM):
    """Wrapper for Anthropic Claude models."""
    
    def __init__(self, api_key: str, model: str, timeout: int):
        """
        Initialize the Anthropic LLM wrapper.
        
        Args:
            api_key: Anthropic API key
            model: Model name (e.g., claude-3-5-sonnet-20240620)
            timeout: Request timeout in seconds
        """
        self.client = anthropic.Anthropic(
            api_key=api_key,
            timeout=float(timeout)
        )
        self.model = model
        self.timeout = timeout
    
    def generate(self, prompt: str) -> str:
        """
        Generate a response using Claude.
        
        Args:
            prompt: The input prompt
            
        Returns:
            str: The generated response text
        """
        message = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract text from the response
        if message.content and len(message.content) > 0:
            return message.content[0].text
        return ""


class GeminiLLM(BaseLLM):
    """Wrapper for Google Gemini models."""
    
    def __init__(self, api_key: str, model: str, timeout: int):
        """
        Initialize the Gemini LLM wrapper.
        
        Args:
            api_key: Google API key
            model: Model name (e.g., gemini-1.5-pro)
            timeout: Request timeout in seconds
        """
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.timeout = timeout
    
    def generate(self, prompt: str) -> str:
        """
        Generate a response using Gemini.
        
        Args:
            prompt: The input prompt
            
        Returns:
            str: The generated response text
        """
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                http_options=types.HttpOptions(timeout=self.timeout * 1000)
            )
        )
        
        # Extract text from the response
        if response.text:
            return response.text
        return ""


def get_llm(meta: dict[str, Any] | None, settings: Settings) -> BaseLLM:
    """
    Get an LLM instance based on meta configuration and settings.
    
    Provider selection priority:
    1. meta["llm_provider"] if present
    2. settings.default_llm_provider
    
    Model selection priority:
    1. meta["model"] if present
    2. Provider-specific model from settings
    
    Args:
        meta: Optional metadata dict with llm_provider and model overrides
        settings: Application settings
        
    Returns:
        BaseLLM: An LLM instance ready to use
        
    Raises:
        ValueError: If required API key is not configured
    """
    meta = meta or {}
    
    # Determine provider
    provider = meta.get("llm_provider", settings.default_llm_provider)
    
    # Get timeout
    timeout = settings.request_timeout_seconds
    
    if provider == "anthropic":
        # Validate API key
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is not configured")
        
        # Determine model
        model = meta.get("model", settings.anthropic_model)
        
        return AnthropicLLM(
            api_key=settings.anthropic_api_key,
            model=model,
            timeout=timeout
        )
    
    elif provider == "google":
        # Validate API key
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY is not configured")
        
        # Determine model
        model = meta.get("model", settings.gemini_model)
        
        return GeminiLLM(
            api_key=settings.google_api_key,
            model=model,
            timeout=timeout
        )
    
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
