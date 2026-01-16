"""
Application configuration loaded from environment variables.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Authentication
    api_key: str = Field(..., description="API key for authenticating requests")
    
    # LLM Provider Configuration
    default_llm_provider: Literal["anthropic", "google", "deepseek"] = Field(
        default="deepseek",
        description="Default LLM provider to use"
    )
    
    # Anthropic Configuration
    anthropic_api_key: str | None = Field(
        default=None,
        description="Anthropic API key for Claude models"
    )
    anthropic_model: str = Field(
        default="claude-3-5-sonnet-20240620",
        description="Default Anthropic model to use"
    )
    
    # Google Configuration
    google_api_key: str | None = Field(
        default=None,
        description="Google API key for Gemini models"
    )
    gemini_model: str = Field(
        default="gemini-2.0-flash",
        description="Default Gemini model to use"
    )
    
    # DeepSeek Configuration
    deepseek_api_key: str | None = Field(
        default=None,
        description="DeepSeek API key"
    )
    deepseek_model: str = Field(
        default="deepseek-chat",
        description="Default DeepSeek model to use"
    )
    
    # Perplexity Configuration (for research)
    perplexity_api_key: str | None = Field(
        default=None,
        description="Perplexity API key for research agents"
    )
    perplexity_model: str = Field(
        default="sonar-pro",
        description="Default Perplexity model to use"
    )
    
    # Request Configuration
    request_timeout_seconds: int = Field(
        default=90,
        description="Timeout for LLM requests in seconds"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()
