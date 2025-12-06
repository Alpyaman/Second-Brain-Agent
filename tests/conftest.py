"""
Test configuration and shared fixtures for Second Brain Agent.

This module provides pytest configuration and common fixtures
used across all test suites.
"""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def sample_job_description():
    """Sample job description for testing."""
    return """
    Build a REST API for a blog platform with the following features:
    - User authentication and authorization
    - CRUD operations for blog posts
    - Comments system
    - Tags and categories
    - Search functionality
    
    Technical Requirements:
    - Backend: Python (FastAPI or Django)
    - Database: PostgreSQL
    - Authentication: JWT tokens
    - API Documentation: OpenAPI/Swagger
    """


@pytest.fixture
def sample_tdd_content():
    """Sample TDD content for testing."""
    return """
    # Technical Design Document: Blog API
    
    ## Architecture Overview
    RESTful API built with FastAPI and PostgreSQL
    
    ## Components
    - Authentication Service
    - Post Management Service
    - Comment Service
    
    ## API Endpoints
    - POST /api/auth/register
    - POST /api/auth/login
    - GET /api/posts
    - POST /api/posts
    """


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup after test
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def sample_tdd_file(temp_dir, sample_tdd_content):
    """Create a sample TDD file for testing."""
    tdd_file = temp_dir / "design.md"
    tdd_file.write_text(sample_tdd_content)
    return tdd_file


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_api_key_123")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "codellama")


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return {
        "design_document": "# Mock Design Document\nThis is a test design.",
        "frontend_tasks": ["Build UI", "Create components"],
        "backend_tasks": ["Setup API", "Create database schema"],
        "architecture_notes": "Simple REST API architecture",
    }
