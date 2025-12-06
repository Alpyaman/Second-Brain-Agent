"""
Unit tests for custom exceptions.

Tests exception hierarchy and error message formatting.
"""

import pytest
from src.utils.exceptions import (
    SecondBrainError,
    LLMError,
    ValidationError,
    OutputGenerationError,
    ConfigurationError,
    IngestError,
)


class TestExceptionHierarchy:
    """Test exception inheritance and basic functionality."""

    def test_base_exception(self):
        """Test SecondBrainError base exception."""
        error = SecondBrainError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_exception_with_details(self):
        """Test exception with additional details."""
        error = SecondBrainError("Test error", details={"key": "value", "count": 42})
        assert "Test error" in str(error)
        assert "key=value" in str(error)
        assert "count=42" in str(error)

    def test_llm_error_inheritance(self):
        """Test LLMError inherits from SecondBrainError."""
        error = LLMError("LLM call failed")
        assert isinstance(error, SecondBrainError)
        assert isinstance(error, Exception)

    def test_validation_error_inheritance(self):
        """Test ValidationError inherits from SecondBrainError."""
        error = ValidationError("Invalid input")
        assert isinstance(error, SecondBrainError)

    def test_output_generation_error(self):
        """Test OutputGenerationError."""
        error = OutputGenerationError("Code generation failed", details={"phase": "backend"})
        assert "Code generation failed" in str(error)
        assert "phase=backend" in str(error)


class TestExceptionRaising:
    """Test raising and catching exceptions."""

    def test_raise_and_catch_llm_error(self):
        """Test raising and catching LLMError."""
        with pytest.raises(LLMError) as exc_info:
            raise LLMError("API timeout")
        assert "API timeout" in str(exc_info.value)

    def test_raise_validation_error(self):
        """Test raising ValidationError."""
        with pytest.raises(ValidationError):
            raise ValidationError("Invalid job description")

    def test_catch_as_base_exception(self):
        """Test catching specific exception as base SecondBrainError."""
        with pytest.raises(SecondBrainError):
            raise LLMError("Test")
