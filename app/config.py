"""Application configuration management."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    figma_access_token: str = ""
    gemini_api_key: str = ""
    groq_api_key: str = ""

    # Database
    database_url: str = "sqlite+aiosqlite:///./qa_test_generator.db"

    # Redis (optional)
    redis_url: Optional[str] = None

    # Application
    app_name: str = "QA Test Generator"
    debug: bool = True
    log_level: str = "INFO"

    # LLM Settings
    llm_model: str = "gemini-2.5-flash"
    llm_max_tokens: int = 8192
    llm_temperature: float = 0.3

    # Processing Settings
    max_concurrent_screens: int = 10
    figma_api_base_url: str = "https://api.figma.com/v1"
    
    # Noise Reduction Settings
    enable_component_filtering: bool = True
    component_relevance_threshold: float = 20.0  # Minimum score to keep component
    max_component_depth: int = 10
    
    # Test Generation Settings
    enable_baseline_knowledge: bool = True
    baseline_file_path: str = "app/data/test_baseline.json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
