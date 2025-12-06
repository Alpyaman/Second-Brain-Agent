"""
Unit tests for validation utilities.

Tests all validation functions to ensure proper input validation
and error handling.
"""

import pytest
from pathlib import Path

from src.utils.validators import (
    validate_job_description,
    validate_tdd_file,
    validate_output_directory,
    validate_model_name,
    validate_api_key,
)
from src.utils.exceptions import ValidationError


class TestJobDescriptionValidation:
    """Test job description validation."""

    def test_valid_job_description(self):
        """Test validation of a valid job description."""
        valid_desc = "Build a REST API project with authentication and database requirements"
        is_valid, error = validate_job_description(valid_desc)
        assert is_valid is True
        assert error == ""

    def test_empty_job_description(self):
        """Test validation fails for empty input."""
        is_valid, error = validate_job_description("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_short_job_description(self):
        """Test validation fails for too short input."""
        short_desc = "Build app"
        is_valid, error = validate_job_description(short_desc)
        assert is_valid is False
        assert "too short" in error

    def test_missing_keywords(self):
        """Test validation fails when job keywords are missing."""
        no_keywords = "Lorem ipsum dolor sit amet consectetur adipiscing elit sed do"
        is_valid, error = validate_job_description(no_keywords)
        assert is_valid is False
        assert "doesn't appear to be a job description" in error


class TestTDDFileValidation:
    """Test TDD file validation."""

    def test_valid_tdd_file(self, sample_tdd_file):
        """Test validation of a valid TDD file."""
        is_valid, error = validate_tdd_file(sample_tdd_file, strict=False)
        assert is_valid is True
        assert error == ""

    def test_nonexistent_file(self, temp_dir):
        """Test validation fails for non-existent file."""
        fake_file = temp_dir / "nonexistent.md"
        is_valid, error = validate_tdd_file(fake_file)
        assert is_valid is False
        assert "not found" in error

    def test_empty_file(self, temp_dir):
        """Test validation fails for empty file."""
        empty_file = temp_dir / "empty.md"
        empty_file.write_text("")
        is_valid, error = validate_tdd_file(empty_file)
        assert is_valid is False
        assert "too short or empty" in error


class TestModelNameValidation:
    """Test model name validation."""

    @pytest.mark.parametrize(
        "model_name",
        [
            "gemini-pro",
            "gemini-1.5-flash",
            "gpt-4",
            "gpt-3.5-turbo",
            "claude-3",
            "llama2",
            "codellama",
            "mistral",
        ],
    )
    def test_valid_model_names(self, model_name):
        """Test validation of valid model names."""
        is_valid, error = validate_model_name(model_name)
        assert is_valid is True
        assert error == ""

    def test_empty_model_name(self):
        """Test validation fails for empty model name."""
        is_valid, error = validate_model_name("")
        assert is_valid is False

    def test_invalid_model_name(self):
        """Test validation fails for invalid model name."""
        is_valid, error = validate_model_name("invalid-model-xyz")
        assert is_valid is False
        assert "Unknown model name" in error


class TestAPIKeyValidation:
    """Test API key validation."""

    def test_valid_google_key(self):
        """Test validation of valid Google API key."""
        is_valid, error = validate_api_key("AIzaSyDummyKeyForTesting123456789", "google")
        assert is_valid is True

    def test_valid_openai_key(self):
        """Test validation of valid OpenAI API key."""
        is_valid, error = validate_api_key("sk-dummy1234567890abcdef", "openai")
        assert is_valid is True

    def test_empty_api_key(self):
        """Test validation fails for empty API key."""
        is_valid, error = validate_api_key("", "google")
        assert is_valid is False

    def test_short_api_key(self):
        """Test validation fails for too short API key."""
        is_valid, error = validate_api_key("short", "google")
        assert is_valid is False
