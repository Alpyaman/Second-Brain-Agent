"""
Custom exceptions for Second Brain Agent.

This module defines all custom exceptions used throughout the application
to provide clear error messages and better error handling.
"""


class SecondBrainError(Exception):
    """Base exception for all Second Brain Agent errors."""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class LLMError(SecondBrainError):
    """Raised when LLM API calls fail or return invalid responses."""

    pass


class ValidationError(SecondBrainError):
    """Raised when input validation fails."""

    pass


class OutputGenerationError(SecondBrainError):
    """Raised when code or document generation fails."""

    pass
"""
ConfigurationError: Raised for configuration issues
IngestError: Raised during code ingestion failures
BrainNotFoundError: Raised when expert brain collection doesn't exist
"""


class ConfigurationError(SecondBrainError):
    """Raised when configuration is invalid or missing."""

    pass


class IngestError(SecondBrainError):
    """Raised when code ingestion or embedding fails."""

    pass


class BrainNotFoundError(SecondBrainError):
    """Raised when a required expert brain collection is not found."""

    pass


class APIKeyError(SecondBrainError):
    """Raised when required API keys are missing or invalid."""

    pass


class FileOperationError(SecondBrainError):
    """Raised when file read/write operations fail."""

    pass


class TimeoutError(SecondBrainError):
    """Raised when operations exceed timeout limits."""

    pass
