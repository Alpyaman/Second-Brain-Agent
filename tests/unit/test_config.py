"""
Unit tests for configuration module.

Tests Pydantic settings validation and configuration loading.
"""

import sys
from pathlib import Path

# Add project root to path for direct execution
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest  # noqa: E402 - Import after path modification
from src.core.config import Settings, settings  # noqa: E402


class TestSettingsValidation:
    """Test configuration validation."""

    def test_default_settings(self):
        """Test default settings are loaded correctly."""
        config = Settings()
        assert config.default_model == "gemini-pro"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.enable_cache is True

    def test_log_level_validation(self):
        """Test log level validation."""
        # Valid log levels
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            config = Settings(log_level=level)
            assert config.log_level == level

        # Case insensitive
        config = Settings(log_level="info")
        assert config.log_level == "INFO"

        # Invalid log level
        with pytest.raises(ValueError):
            Settings(log_level="INVALID")

    def test_model_name_validation(self):
        """Test model name validation."""
        # Valid model name
        config = Settings(default_model="gpt-4")
        assert config.default_model == "gpt-4"

        # Empty model name should raise error
        with pytest.raises(ValueError):
            Settings(default_model="")

    def test_temperature_bounds(self):
        """Test temperature is within valid range."""
        # Valid temperatures
        config = Settings(temperature=0.0)
        assert config.temperature == 0.0

        config = Settings(temperature=2.0)
        assert config.temperature == 2.0

        # Invalid temperature (out of range)
        with pytest.raises(ValueError):
            Settings(temperature=-0.1)

        with pytest.raises(ValueError):
            Settings(temperature=2.1)

    def test_max_tokens_bounds(self):
        """Test max_tokens is within valid range."""
        # Valid max_tokens
        config = Settings(max_tokens=1000)
        assert config.max_tokens == 1000

        # Invalid max_tokens
        with pytest.raises(ValueError):
            Settings(max_tokens=0)

        with pytest.raises(ValueError):
            Settings(max_tokens=100001)

    def test_directories_creation(self):
        """Test that required directories are created."""
        config = Settings()
        
        # Check directories exist
        assert config.output_dir.exists()
        assert config.chroma_db_dir.exists()
        assert config.notes_dir.exists()
        assert config.cache_dir.exists()
        assert config.log_dir.exists()

    def test_get_api_key(self):
        """Test API key retrieval."""
        config = Settings(
            google_api_key="test_google_key",
            openai_api_key="test_openai_key"
        )

        assert config.get_api_key("google") == "test_google_key"
        assert config.get_api_key("openai") == "test_openai_key"
        assert config.get_api_key("anthropic") is None
        assert config.get_api_key("invalid") is None

    def test_get_model_config(self):
        """Test model configuration dictionary."""
        config = Settings(
            default_model="gpt-4",
            temperature=0.5,
            max_tokens=2048,
            top_p=0.95
        )

        model_config = config.get_model_config()
        assert model_config["model"] == "gpt-4"
        assert model_config["temperature"] == 0.5
        assert model_config["max_tokens"] == 2048
        assert model_config["top_p"] == 0.95


class TestGlobalSettings:
    """Test global settings instance."""

    def test_global_settings_exists(self):
        """Test global settings instance is available."""
        assert settings is not None
        assert isinstance(settings, Settings)

    def test_backward_compatibility_constants(self):
        """Test backward compatibility constants."""
        from src.core.config import (
            PROJECT_ROOT,
            NOTES_DIR,
            CHROMA_DB_DIR,
            EMBEDDING_MODEL,
            COLLECTION_NAME
        )

        assert PROJECT_ROOT == settings.project_root
        assert NOTES_DIR == settings.notes_dir
        assert CHROMA_DB_DIR == settings.chroma_db_dir
        assert EMBEDDING_MODEL == settings.embedding_model
        assert COLLECTION_NAME == settings.collection_name


class TestPathSettings:
    """Test path-related settings."""

    def test_paths_are_path_objects(self):
        """Test that all path settings are Path objects."""
        config = Settings()

        assert isinstance(config.project_root, Path)
        assert isinstance(config.output_dir, Path)
        assert isinstance(config.chroma_db_dir, Path)
        assert isinstance(config.notes_dir, Path)
        assert isinstance(config.cache_dir, Path)
        assert isinstance(config.log_dir, Path)

    def test_custom_paths(self):
        """Test custom path configuration."""
        config = Settings(
            output_dir="./custom_output",
            cache_dir="./custom_cache"
        )

        assert config.output_dir == Path("./custom_output")
        assert config.cache_dir == Path("./custom_cache")
