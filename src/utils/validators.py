"""
Input validation utilities for Second Brain Agent.

This module provides validation functions for various inputs including
job descriptions, TDD files, and configuration parameters.
"""

import re
from pathlib import Path
from typing import Tuple, List, Optional

from src.utils.exceptions import ValidationError


def validate_job_description(text: str, min_length: int = 50) -> Tuple[bool, str]:
    """
    Validate job description input.

    Args:
        text: The job description text
        min_length: Minimum required length in characters

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text or not text.strip():
        return False, "Job description cannot be empty"

    text = text.strip()

    if len(text) < min_length:
        return False, f"Job description too short (minimum {min_length} characters, got {len(text)})"

    # Check for common job posting keywords
    job_keywords = [
        "project",
        "build",
        "develop",
        "create",
        "requirements",
        "need",
        "looking for",
        "seeking",
        "application",
        "system",
        "website",
        "api",
        "backend",
        "frontend",
    ]

    text_lower = text.lower()
    if not any(keyword in text_lower for keyword in job_keywords):
        return (
            False,
            "Text doesn't appear to be a job description (missing common keywords like 'build', 'develop', 'requirements')",
        )

    return True, ""


def validate_tdd_file(file_path: Path, strict: bool = True) -> Tuple[bool, str]:
    """
    Validate Technical Design Document file.

    Args:
        file_path: Path to the TDD file
        strict: If True, require all sections; if False, just check basic validity

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)

    if not file_path.exists():
        return False, f"File not found: {file_path}"

    if not file_path.is_file():
        return False, f"Path is not a file: {file_path}"

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"Error reading file: {str(e)}"

    if len(content.strip()) < 100:
        return False, "TDD file appears to be too short or empty"

    if strict:
        # Check for required sections in a TDD
        required_keywords = ["architecture", "component", "api", "database", "stack"]
        content_lower = content.lower()

        missing = [kw for kw in required_keywords if kw not in content_lower]

        if missing:
            return (
                False,
                f"TDD file missing common sections. Expected keywords not found: {', '.join(missing)}",
            )

    return True, ""


def validate_output_directory(dir_path: Path, must_be_empty: bool = False) -> Tuple[bool, str]:
    """
    Validate output directory for code generation.

    Args:
        dir_path: Path to output directory
        must_be_empty: If True, require directory to be empty

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(dir_path, Path):
        dir_path = Path(dir_path)

    # Check if parent directory is writable
    parent = dir_path.parent
    if parent.exists() and not parent.is_dir():
        return False, f"Parent path is not a directory: {parent}"

    # If directory exists, check if we can write to it
    if dir_path.exists():
        if not dir_path.is_dir():
            return False, f"Path exists but is not a directory: {dir_path}"

        if must_be_empty and any(dir_path.iterdir()):
            return False, f"Directory is not empty: {dir_path}"

    return True, ""


def validate_model_name(model_name: str) -> Tuple[bool, str]:
    """
    Validate LLM model name format.

    Args:
        model_name: Model name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not model_name or not model_name.strip():
        return False, "Model name cannot be empty"

    # List of known valid model patterns
    valid_patterns = [
        r"^gemini-.*",  # Google Gemini models
        r"^gpt-.*",  # OpenAI GPT models
        r"^claude-.*",  # Anthropic Claude models
        r"^llama.*",  # Llama models (Ollama)
        r"^codellama.*",  # CodeLlama models (Ollama)
        r"^mistral.*",  # Mistral models
    ]

    if any(re.match(pattern, model_name) for pattern in valid_patterns):
        return True, ""

    return (
        False,
        f"Unknown model name format: {model_name}. Expected formats: gemini-*, gpt-*, claude-*, llama*, mistral*",
    )


def validate_api_key(api_key: str, provider: str = "generic") -> Tuple[bool, str]:
    """
    Validate API key format.

    Args:
        api_key: API key to validate
        provider: API provider name (google, openai, anthropic)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not api_key or not api_key.strip():
        return False, f"{provider.title()} API key cannot be empty"

    # Basic length check
    if len(api_key) < 10:
        return False, f"{provider.title()} API key appears to be too short"

    # Provider-specific validation
    if provider.lower() == "google" and not api_key.startswith("AI"):
        return False, "Google API keys typically start with 'AI'"

    if provider.lower() == "openai" and not api_key.startswith("sk-"):
        return False, "OpenAI API keys start with 'sk-'"

    if provider.lower() == "anthropic" and not api_key.startswith("sk-ant-"):
        return False, "Anthropic API keys start with 'sk-ant-'"

    return True, ""
