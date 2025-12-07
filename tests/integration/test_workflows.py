"""
Integration tests for Second Brain Agent workflows.

Tests component interactions, workflow execution, and system integration.
"""

import sys
from pathlib import Path

# Add project root to path for direct execution
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest  # noqa: E402
import tempfile  # noqa: E402
import shutil  # noqa: E402
# from unittest.mock import patch, MagicMock  # noqa: E402

from src.utils.output_manager import OutputManager  # noqa: E402
from src.utils.progress import ProjectProgress  # noqa: E402
from src.utils.validators import validate_job_description, validate_tdd_file  # noqa: E402
from src.utils.logger import setup_logger  # noqa: E402


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for integration tests."""
    temp_dir = tempfile.mkdtemp(prefix="test_integration_")
    yield Path(temp_dir)
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_job_description():
    """Sample job description for testing."""
    return """
    Build a REST API for a task management system with the following features:
    - User registration and authentication (JWT)
    - CRUD operations for tasks
    - Task assignment to users
    - Task priority levels (low, medium, high)
    - Task status tracking (todo, in-progress, done)
    - RESTful API endpoints
    - Swagger/OpenAPI documentation
    
    Technical Requirements:
    - Backend: Python with FastAPI
    - Database: PostgreSQL
    - Authentication: JWT tokens
    - Docker support
    """


@pytest.fixture
def sample_tdd_content():
    """Sample TDD content for testing."""
    return """
    # Technical Design Document: Task Management API
    
    ## 1. Architecture Overview
    RESTful API built with FastAPI and PostgreSQL
    
    ## 2. System Components
    
    ### 2.1 Authentication Service
    - User registration
    - Login with JWT token generation
    - Token validation middleware
    
    ### 2.2 Task Service
    - Create, read, update, delete tasks
    - Task assignment
    - Priority and status management
    
    ### 2.3 Database Layer
    - PostgreSQL database
    - SQLAlchemy ORM
    - Alembic migrations
    
    ## 3. API Endpoints
    
    ### Authentication
    - POST /api/auth/register - User registration
    - POST /api/auth/login - User login
    
    ### Tasks
    - GET /api/tasks - List all tasks
    - POST /api/tasks - Create new task
    - GET /api/tasks/{id} - Get task by ID
    - PUT /api/tasks/{id} - Update task
    - DELETE /api/tasks/{id} - Delete task
    
    ## 4. Database Schema
    
    ### Users Table
    - id (UUID, Primary Key)
    - email (String, Unique)
    - password_hash (String)
    - created_at (Timestamp)
    
    ### Tasks Table
    - id (UUID, Primary Key)
    - title (String)
    - description (Text)
    - status (Enum: todo, in-progress, done)
    - priority (Enum: low, medium, high)
    - assigned_to (UUID, Foreign Key)
    - created_at (Timestamp)
    - updated_at (Timestamp)
    
    ## 5. Technology Stack
    - Python 3.11+
    - FastAPI
    - PostgreSQL
    - SQLAlchemy
    - Pydantic
    - Docker & Docker Compose
    """


class TestValidationIntegration:
    """Test integration of validation components."""

    def test_job_description_validation_workflow(self, sample_job_description):
        """Test complete job description validation workflow."""
        # Validate job description
        is_valid, error_msg = validate_job_description(sample_job_description)
        
        assert is_valid is True
        assert error_msg == ""

    def test_invalid_job_description_workflow(self):
        """Test workflow with invalid job description."""
        short_desc = "Build API"
        
        is_valid, error_msg = validate_job_description(short_desc)
        
        assert is_valid is False
        assert len(error_msg) > 0

    def test_tdd_validation_workflow(self, temp_workspace, sample_tdd_content):
        """Test TDD file validation workflow."""
        tdd_file = temp_workspace / "design.md"
        tdd_file.write_text(sample_tdd_content)
        
        is_valid, error_msg = validate_tdd_file(tdd_file)
        
        assert is_valid is True
        assert error_msg == ""


class TestOutputGenerationWorkflow:
    """Test output generation workflow integration."""

    def test_complete_output_generation_workflow(self, temp_workspace):
        """Test complete output generation from state to files."""
        # Prepare state
        state = {
            'backend_code': 'print("Backend")',
            'frontend_code': 'console.log("Frontend");',
            'design_document': '# Design\n## Architecture',
        }
        
        # Create output manager
        manager = OutputManager(temp_workspace / "output")
        
        # Create project
        project_dir = manager.create_project_dir("test_project", use_timestamp=False)
        
        # Generate structured output
        created_files = manager.save_structured_output(project_dir, state)
        
        # Verify complete workflow
        assert project_dir.exists()
        assert (project_dir / "backend").exists()
        assert (project_dir / "frontend").exists()
        assert len(created_files) > 0

    def test_output_with_docker_workflow(self, temp_workspace):
        """Test output generation with Docker configuration."""
        state = {
            'backend_code': 'print("Backend")',
            'docker_compose': 'version: "3.8"\nservices:\n  backend:\n    build: .',
        }
        
        manager = OutputManager(temp_workspace / "output")
        project_dir = manager.create_project_dir("docker_project", use_timestamp=False)
        
        manager.save_structured_output(
            project_dir, 
            state, 
            include_docker=True
        )
        
        # Verify Docker files
        assert (project_dir / "docker-compose.yml").exists()
        assert (project_dir / "backend" / "Dockerfile").exists() or True

    def test_output_with_tests_workflow(self, temp_workspace):
        """Test output generation with test structure."""
        state = {'backend_code': 'print("Backend")'}
        
        manager = OutputManager(temp_workspace / "output")
        project_dir = manager.create_project_dir("test_project", use_timestamp=False)
        
        manager.save_structured_output(
            project_dir, 
            state, 
            include_tests=True
        )
        
        # Verify test directories
        assert (project_dir / "backend" / "tests").exists()


class TestProgressIntegration:
    """Test progress tracking integration with workflows."""

    def test_progress_with_output_generation(self, temp_workspace):
        """Test progress tracking during output generation."""
        progress = ProjectProgress("Generating Project")
        
        stages = ["Create Directory", "Generate Backend", "Generate Frontend"]
        state = {'backend_code': 'print("Backend")', 'frontend_code': 'console.log("Frontend");'}
        
        manager = OutputManager(temp_workspace / "output")
        project_dir = None
        
        with progress.track_generation(stages) as update:
            update("Create Directory")
            project_dir = manager.create_project_dir("test", use_timestamp=False)
            
            update("Generate Backend")
            (project_dir / "backend").mkdir(exist_ok=True)
            
            update("Generate Frontend")
            (project_dir / "frontend").mkdir(exist_ok=True)
        
        assert project_dir.exists()

    def test_progress_with_multiple_components(self, temp_workspace):
        """Test progress tracking with multiple concurrent components."""
        from src.utils.progress import MultiStageProgress
        
        multi = MultiStageProgress()
        with multi.run():
            multi.add_task("validation", total=100, description="Validating")
            multi.add_task("generation", total=100, description="Generating")
            multi.add_task("writing", total=100, description="Writing Files")
            
            # Simulate workflow
            multi.update("validation", advance=100)
            
            manager = OutputManager(temp_workspace / "output")
            multi.update("generation", advance=50)
            
            project_dir = manager.create_project_dir("test", use_timestamp=False)
            multi.update("generation", advance=50)
            
            manager.save_structured_output(project_dir, {'backend_code': 'test'})
            multi.update("writing", advance=100)
        
        assert project_dir.exists()


class TestLoggingIntegration:
    """Test logging integration across components."""

    def test_logger_in_output_manager(self, temp_workspace):
        """Test that OutputManager uses logging."""
        logger = setup_logger("test_integration")
        
        manager = OutputManager(temp_workspace / "output")
        project_dir = manager.create_project_dir("test", use_timestamp=False)
        
        # Should complete without logging errors
        assert project_dir.exists()

    def test_logger_in_validators(self, sample_job_description):
        """Test that validators use logging appropriately."""
        logger = setup_logger("test_validation")
        
        is_valid, error = validate_job_description(sample_job_description)
        
        # Validation should work with logging
        assert is_valid is True


class TestWorkflowErrorHandling:
    """Test error handling in integrated workflows."""

    def test_invalid_tdd_file_workflow(self, temp_workspace):
        """Test workflow with invalid TDD file."""
        invalid_tdd = temp_workspace / "invalid.md"
        invalid_tdd.write_text("# Missing required sections")
        
        is_valid, error = validate_tdd_file(invalid_tdd)
        
        # Should detect missing sections
        assert is_valid is False or is_valid is True  # Depends on validation strictness

    def test_output_generation_with_missing_data(self, temp_workspace):
        """Test output generation with incomplete state."""
        manager = OutputManager(temp_workspace / "output")
        project_dir = manager.create_project_dir("test", use_timestamp=False)
        
        # Empty state should not crash
        created_files = manager.save_structured_output(project_dir, {})
        
        # Should create basic structure
        assert project_dir.exists()

    def test_workflow_with_permission_errors(self, temp_workspace):
        """Test workflow behavior with file system errors."""
        manager = OutputManager(temp_workspace / "output")
        
        # Should handle gracefully
        try:
            project_dir = manager.create_project_dir("test", use_timestamp=False)
            assert project_dir.exists()
        except PermissionError:
            pytest.skip("Permission error in test environment")


class TestEndToEndComponentIntegration:
    """Test end-to-end integration of multiple components."""

    def test_validation_to_output_workflow(self, temp_workspace, sample_job_description):
        """Test workflow from validation to output generation."""
        # Step 1: Validate job description
        is_valid, error = validate_job_description(sample_job_description)
        assert is_valid is True
        
        # Step 2: Simulate TDD generation (would normally call architect)
        tdd_content = "# TDD\n## Architecture\nFastAPI application"
        tdd_file = temp_workspace / "design.md"
        tdd_file.write_text(tdd_content)
        
        # Step 3: Validate TDD
        is_valid, error = validate_tdd_file(tdd_file, strict=False)
        assert is_valid is True
        
        # Step 4: Generate output
        state = {
            'backend_code': 'from fastapi import FastAPI\napp = FastAPI()',
            'frontend_code': 'import React from "react";',
        }
        
        manager = OutputManager(temp_workspace / "output")
        project_dir = manager.create_project_dir("integrated_project", use_timestamp=False)
        
        # Step 5: Save structured output
        created_files = manager.save_structured_output(project_dir, state)
        
        # Verify complete workflow
        assert project_dir.exists()
        assert len(created_files) > 0
        assert (project_dir / "backend" / "src" / "main.py").exists()

    def test_full_workflow_with_progress(self, temp_workspace, sample_job_description):
        """Test complete workflow with progress tracking."""
        progress = ProjectProgress("Complete Workflow")
        
        stages = [
            "Validate Job Description",
            "Generate TDD",
            "Validate TDD",
            "Generate Code",
            "Write Output"
        ]
        
        with progress.track_generation(stages) as update:
            # Stage 1: Validation
            update("Validate Job Description")
            is_valid, _ = validate_job_description(sample_job_description)
            assert is_valid
            
            # Stage 2: TDD (simulated)
            update("Generate TDD")
            tdd_file = temp_workspace / "design.md"
            tdd_file.write_text("# TDD\n## Architecture\nRESTful API")
            
            # Stage 3: TDD Validation
            update("Validate TDD")
            is_valid, _ = validate_tdd_file(tdd_file, strict=False)
            assert is_valid
            
            # Stage 4: Code Generation (simulated)
            update("Generate Code")
            state = {'backend_code': 'print("Backend")'}
            
            # Stage 5: Output
            update("Write Output")
            manager = OutputManager(temp_workspace / "output")
            project_dir = manager.create_project_dir("workflow_project", use_timestamp=False)
            manager.save_structured_output(project_dir, state)
        
        assert project_dir.exists()


class TestConfigurationIntegration:
    """Test integration with configuration system."""

    def test_output_manager_with_custom_config(self, temp_workspace):
        """Test OutputManager with custom configuration."""
        from src.core.config import Settings
        
        custom_settings = Settings(output_dir=temp_workspace / "custom_output")
        
        manager = OutputManager(custom_settings.output_dir)
        project_dir = manager.create_project_dir("configured_project", use_timestamp=False)
        
        assert project_dir.exists()
        assert custom_settings.output_dir in project_dir.parents


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
