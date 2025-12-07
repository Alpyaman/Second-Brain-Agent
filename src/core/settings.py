"""
Enhanced configuration management using Pydantic Settings.
Provides type-safe, validated configuration with environment variable support.
"""

from pathlib import Path
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with validation and environment variable support.
    
    Configuration can be provided via:
    1. Environment variables
    2. .env file
    3. Direct instantiation
    
    Example .env file:
        GOOGLE_API_KEY=your_api_key_here
        DEFAULT_MODEL=gemini-pro
        OUTPUT_DIR=./my_output
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields in .env
    )
    
    # ============================================================================
    # API Keys
    # ============================================================================
    
    google_api_key: Optional[str] = Field(
        default=None,
        description="Google Gemini API key",
    )
    
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key",
    )
    
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic Claude API key",
    )
    
    # ============================================================================
    # Model Settings
    # ============================================================================
    
    default_model: str = Field(
        default="gemini-2.5-flash-lite",
        description="Default LLM model to use",
    )
    
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embedding model for vector storage",
    )
    
    max_tokens: int = Field(
        default=4096,
        ge=1,
        le=100000,
        description="Maximum tokens for LLM responses",
    )
    
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM generation",
    )
    
    # ============================================================================
    # Directory Paths
    # ============================================================================
    
    output_dir: Path = Field(
        default=Path("./output"),
        description="Base directory for generated outputs",
    )
    
    data_dir: Path = Field(
        default=Path("./src/data"),
        description="Directory for application data",
    )
    
    chroma_db_dir: Path = Field(
        default=Path("./src/data/chroma_db"),
        description="ChromaDB storage directory",
    )
    
    notes_dir: Path = Field(
        default=Path("./src/data/notes"),
        description="Directory for note storage",
    )
    
    logs_dir: Path = Field(
        default=Path("./logs"),
        description="Directory for log files",
    )
    
    cache_dir: Path = Field(
        default=Path("./.cache"),
        description="Directory for caching responses",
    )
    
    # ============================================================================
    # ChromaDB Settings
    # ============================================================================
    
    collection_name: str = Field(
        default="second_brain_notes",
        description="Default ChromaDB collection name",
    )
    
    chroma_distance_metric: str = Field(
        default="cosine",
        description="Distance metric for similarity search",
    )
    
    # ============================================================================
    # Generation Settings
    # ============================================================================
    
    use_timestamp_dirs: bool = Field(
        default=True,
        description="Add timestamps to output directory names",
    )
    
    include_docker: bool = Field(
        default=True,
        description="Generate Docker configuration by default",
    )
    
    include_tests: bool = Field(
        default=True,
        description="Generate test structure by default",
    )
    
    backend_framework: str = Field(
        default="fastapi",
        description="Default backend framework",
    )
    
    frontend_framework: str = Field(
        default="react",
        description="Default frontend framework",
    )
    
    # ============================================================================
    # Performance Settings
    # ============================================================================
    
    enable_caching: bool = Field(
        default=True,
        description="Enable response caching",
    )
    
    cache_ttl_seconds: int = Field(
        default=3600,
        ge=0,
        description="Cache time-to-live in seconds",
    )
    
    max_concurrent_agents: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum concurrent agent operations",
    )
    
    # ============================================================================
    # Logging Settings
    # ============================================================================
    
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    
    log_to_file: bool = Field(
        default=True,
        description="Enable file logging",
    )
    
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format",
    )
    
    # ============================================================================
    # Feature Flags
    # ============================================================================
    
    enable_web_search: bool = Field(
        default=False,
        description="Enable web search capabilities",
    )
    
    enable_gmail_integration: bool = Field(
        default=False,
        description="Enable Gmail integration",
    )
    
    enable_calendar_integration: bool = Field(
        default=False,
        description="Enable Google Calendar integration",
    )
    
    enable_analytics: bool = Field(
        default=True,
        description="Enable usage analytics",
    )
    
    # ============================================================================
    # Validators
    # ============================================================================
    
    @field_validator('output_dir', 'data_dir', 'chroma_db_dir', 'notes_dir', 'logs_dir', 'cache_dir')
    @classmethod
    def create_directories(cls, v: Path) -> Path:
        """Ensure directories exist."""
        v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v
    
    @field_validator('backend_framework')
    @classmethod
    def validate_backend_framework(cls, v: str) -> str:
        """Validate backend framework."""
        valid_frameworks = ['fastapi', 'django', 'flask']
        v = v.lower()
        if v not in valid_frameworks:
            raise ValueError(f"backend_framework must be one of {valid_frameworks}")
        return v
    
    @field_validator('frontend_framework')
    @classmethod
    def validate_frontend_framework(cls, v: str) -> str:
        """Validate frontend framework."""
        valid_frameworks = ['react', 'nextjs', 'vue']
        v = v.lower()
        if v not in valid_frameworks:
            raise ValueError(f"frontend_framework must be one of {valid_frameworks}")
        return v
    
    # ============================================================================
    # Helper Methods
    # ============================================================================
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a specific provider.
        
        Args:
            provider: Provider name (google, openai, anthropic)
            
        Returns:
            API key if available, None otherwise
        """
        provider = provider.lower()
        if provider in ['google', 'gemini']:
            return self.google_api_key
        elif provider in ['openai', 'gpt']:
            return self.openai_api_key
        elif provider in ['anthropic', 'claude']:
            return self.anthropic_api_key
        return None
    
    def has_api_key(self, provider: str) -> bool:
        """Check if API key exists for provider."""
        return self.get_api_key(provider) is not None
    
    def get_model_config(self) -> dict:
        """Get model configuration as dictionary."""
        return {
            'model': self.default_model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
        }
    
    def to_dict(self) -> dict:
        """Convert settings to dictionary."""
        return self.model_dump()
    
    def save_to_env(self, file_path: Path = Path(".env")):
        """
        Save current settings to .env file.
        
        Args:
            file_path: Path to .env file
        """
        lines = []
        for key, value in self.model_dump().items():
            if value is not None:
                # Convert Path objects to strings
                if isinstance(value, Path):
                    value = str(value)
                # Skip empty strings
                if value == "":
                    continue
                # Format as ENV_VAR=value
                env_key = key.upper()
                lines.append(f"{env_key}={value}\n")
        
        file_path.write_text("".join(lines), encoding="utf-8")


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get application settings.
    
    Returns:
        Settings instance
    """
    return settings


def reload_settings() -> Settings:
    """
    Reload settings from environment/file.
    
    Returns:
        New settings instance
    """
    global settings
    settings = Settings()
    return settings
