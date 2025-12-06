"""
Configuration module for Second-Brain-Agent.
Loads environment variables and provides configuration settings using Pydantic.
"""

from pathlib import Path
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden via environment variables or .env file.
    """
    
    # ============================================================================
    # API Keys
    # ============================================================================
    google_api_key: Optional[str] = Field(
        default=None,
        description="Google API key for Gemini models"
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key for GPT models"
    )
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key for Claude models"
    )
    
    # ============================================================================
    # Model Settings
    # ============================================================================
    default_model: str = Field(
        default="gemini-pro",
        description="Default LLM model to use"
    )
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embedding model for vector search"
    )
    
    # ============================================================================
    # Generation Settings
    # ============================================================================
    max_tokens: int = Field(
        default=4096,
        ge=1,
        le=100000,
        description="Maximum tokens for LLM generation"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM generation (0.0-2.0)"
    )
    top_p: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Top-p sampling parameter"
    )
    
    # ============================================================================
    # Path Settings
    # ============================================================================
    project_root: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent,
        description="Root directory of the project"
    )
    output_dir: Path = Field(
        default_factory=lambda: Path("./output"),
        description="Directory for generated projects"
    )
    chroma_db_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "data" / "chroma_db",
        description="ChromaDB storage directory"
    )
    notes_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "data" / "notes",
        description="Directory for notes/documents"
    )
    cache_dir: Path = Field(
        default_factory=lambda: Path("./cache"),
        description="Cache directory for LLM responses"
    )
    log_dir: Path = Field(
        default_factory=lambda: Path("./logs"),
        description="Directory for log files"
    )
    
    # ============================================================================
    # ChromaDB Settings
    # ============================================================================
    collection_name: str = Field(
        default="second_brain_notes",
        description="ChromaDB collection name"
    )
    chunk_size: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Chunk size for document splitting"
    )
    chunk_overlap: int = Field(
        default=200,
        ge=0,
        le=1000,
        description="Overlap between chunks"
    )
    
    # ============================================================================
    # Cache Settings
    # ============================================================================
    enable_cache: bool = Field(
        default=True,
        description="Enable response caching"
    )
    cache_ttl_hours: int = Field(
        default=24,
        ge=1,
        description="Cache TTL in hours"
    )
    
    # ============================================================================
    # Logging Settings
    # ============================================================================
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_to_file: bool = Field(
        default=True,
        description="Enable file logging"
    )
    
    # ============================================================================
    # Code Generation Settings
    # ============================================================================
    default_framework: str = Field(
        default="fastapi",
        description="Default backend framework"
    )
    default_frontend: str = Field(
        default="react",
        description="Default frontend framework"
    )
    include_tests: bool = Field(
        default=True,
        description="Include test files in generated code"
    )
    include_docker: bool = Field(
        default=True,
        description="Include Docker configuration"
    )
    
    # ============================================================================
    # Development Settings
    # ============================================================================
    debug_mode: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    verbose: bool = Field(
        default=False,
        description="Enable verbose output"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v_upper
    
    @field_validator("default_model")
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        """Validate model name is not empty."""
        if not v or not v.strip():
            raise ValueError("default_model cannot be empty")
        return v.strip()
    
    def __init__(self, **kwargs):
        """Initialize settings and create necessary directories."""
        super().__init__(**kwargs)
        self._create_directories()
    
    def _create_directories(self):
        """Create all necessary directories if they don't exist."""
        directories = [
            self.output_dir,
            self.chroma_db_dir,
            self.notes_dir,
            self.cache_dir,
            self.log_dir,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a specific provider.
        
        Args:
            provider: Provider name (google, openai, anthropic)
            
        Returns:
            API key or None if not configured
        """
        provider_map = {
            "google": self.google_api_key,
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
        }
        return provider_map.get(provider.lower())
    
    def get_model_config(self) -> dict:
        """Get model configuration dictionary."""
        return {
            "model": self.default_model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }


# Global settings instance
settings = Settings()


# ============================================================================
# Backward Compatibility (for existing code)
# ============================================================================
PROJECT_ROOT = settings.project_root
DATA_DIR = PROJECT_ROOT / "data"
NOTES_DIR = settings.notes_dir
CHROMA_DB_DIR = settings.chroma_db_dir
EMBEDDING_MODEL = settings.embedding_model
COLLECTION_NAME = settings.collection_name