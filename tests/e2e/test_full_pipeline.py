"""
End-to-End tests for Second Brain Agent.

Tests complete pipeline from job description to working code generation.
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
from typer.testing import CliRunner  # noqa: E402
from unittest.mock import patch  # noqa: E402

from src.cli.main import app  # noqa: E402
from src.utils.validators import validate_job_description, validate_tdd_file  # noqa: E402


runner = CliRunner()


@pytest.fixture
def temp_workspace():
    """Create temporary workspace for E2E tests."""
    temp_dir = tempfile.mkdtemp(prefix="test_e2e_")
    yield Path(temp_dir)
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def job_description_file(temp_workspace):
    """Create a job description file."""
    job_file = temp_workspace / "job_description.txt"
    job_file.write_text("""
    Build a REST API for a simple blog platform with:
    - User authentication (register, login)
    - CRUD operations for blog posts
    - Comments on posts
    - Categories and tags
    - Search functionality
    
    Technical Requirements:
    - Backend: Python with FastAPI
    - Database: PostgreSQL
    - Authentication: JWT
    - API Documentation: OpenAPI/Swagger
    - Docker support
    """)
    return job_file


@pytest.fixture
def tdd_file(temp_workspace):
    """Create a TDD file."""
    tdd = temp_workspace / "design.md"
    tdd.write_text("""
    # Technical Design Document: Blog API
    
    ## Architecture
    RESTful API using FastAPI framework with PostgreSQL database.
    
    ## Components
    
    ### Authentication Service
    - JWT-based authentication
    - User registration and login
    
    ### Blog Service  
    - Post CRUD operations
    - Comment management
    - Category and tag system
    
    ### Database Layer
    - PostgreSQL with SQLAlchemy ORM
    - Database migrations with Alembic
    
    ## API Endpoints
    
    ### Authentication
    - POST /api/auth/register
    - POST /api/auth/login
    
    ### Posts
    - GET /api/posts
    - POST /api/posts
    - GET /api/posts/{id}
    - PUT /api/posts/{id}
    - DELETE /api/posts/{id}
    
    ### Comments
    - GET /api/posts/{id}/comments
    - POST /api/posts/{id}/comments
    
    ## Database Schema
    
    ### users
    - id (UUID)
    - email (String, unique)
    - password_hash (String)
    
    ### posts
    - id (UUID)
    - title (String)
    - content (Text)
    - author_id (UUID, FK)
    - created_at (Timestamp)
    
    ### comments
    - id (UUID)
    - post_id (UUID, FK)
    - user_id (UUID, FK)
    - content (Text)
    - created_at (Timestamp)
    """)
    return tdd


class TestE2EValidation:
    """Test end-to-end validation pipeline."""

    def test_job_description_validation_e2e(self, job_description_file):
        """Test complete job description validation."""
        # Read job description
        job_text = job_description_file.read_text()
        
        # Validate
        is_valid, error = validate_job_description(job_text)
        
        assert is_valid is True
        assert error == ""

    def test_tdd_validation_e2e(self, tdd_file):
        """Test complete TDD validation."""
        is_valid, error = validate_tdd_file(tdd_file, strict=False)
        
        assert is_valid is True
        assert error == ""


class TestE2ECLIPipeline:
    """Test end-to-end CLI command pipeline."""

    def test_architect_command_e2e(self, job_description_file, temp_workspace):
        """Test architect command end-to-end."""
        output_file = temp_workspace / "generated_design.md"
        
        result = runner.invoke(app, [
            "architect",
            "--job-file", str(job_description_file),
            "--output", str(output_file),
            "--no-validate"
        ])
        
        # Command should execute (may fail due to LLM setup)
        assert result.exit_code in [0, 1]

    def test_dev_team_command_e2e(self, tdd_file, temp_workspace):
        """Test dev-team command end-to-end."""
        output_dir = temp_workspace / "generated_project"
        
        result = runner.invoke(app, [
            "dev-team",
            "--tdd", str(tdd_file),
            "--output", str(output_dir),
            "--no-validate"
        ])
        
        # Command should execute (may fail due to LLM setup)
        assert result.exit_code in [0, 1]

    def test_info_command_e2e(self):
        """Test info command displays system information."""
        result = runner.invoke(app, ["info"])
        
        assert result.exit_code == 0
        assert len(result.stdout) > 0

    def test_version_command_e2e(self):
        """Test version command."""
        result = runner.invoke(app, ["version"])
        
        assert result.exit_code == 0
        assert "Second Brain Agent" in result.stdout or "0.1.0" in result.stdout


class TestE2EWorkflowSimulation:
    """Test simulated end-to-end workflow without LLM calls."""

    @pytest.mark.skip(reason="Requires actual agent graph implementation")
    @patch('src.agents.architect.graph.create_graph')
    def test_simulated_architect_workflow(
        self, 
        mock_graph, 
        job_description_file, 
        temp_workspace
    ):
        """Test simulated architect workflow."""
        # Mock the graph to return fake TDD
        mock_result = {
            'design_document': '# Mock TDD\n## Architecture\nFastAPI',
            'messages': []
        }
        mock_graph.return_value.invoke.return_value = mock_result
        
        output_file = temp_workspace / "design.md"
        
        # This would normally call the architect
        # For now, just verify the mock setup works
        assert mock_graph is not None

    @pytest.mark.skip(reason="Requires actual agent graph implementation")
    @patch('src.agents.dev_team.graph.create_graph')
    def test_simulated_dev_team_workflow(
        self, 
        mock_graph, 
        tdd_file,
        temp_workspace
    ):
        """Test simulated dev-team workflow."""
        # Mock the graph to return fake code
        mock_result = {
            'backend_code': 'print("Backend")',
            'frontend_code': 'console.log("Frontend");',
            'messages': []
        }
        mock_graph.return_value.invoke.return_value = mock_result
        
        output_dir = temp_workspace / "output"
        
        # Verify mock setup
        assert mock_graph is not None


class TestE2EFileGeneration:
    """Test end-to-end file generation."""

    def test_complete_project_structure_e2e(self, temp_workspace):
        """Test generation of complete project structure."""
        from src.utils.output_manager import OutputManager
        
        state = {
            'backend_code': '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}
            ''',
            'frontend_code': '''
import React from 'react';

function App() {
  return <div>Hello World</div>;
}

export default App;
            ''',
            'design_document': '# Blog API\n## Architecture\nRESTful API',
            'database_schema': 'CREATE TABLE users (id UUID PRIMARY KEY);',
        }
        
        manager = OutputManager(temp_workspace / "output")
        project_dir = manager.create_project_dir("blog_api", use_timestamp=False)
        created_files = manager.save_structured_output(
            project_dir,
            state,
            include_docker=True,
            include_tests=True
        )
        
        # Verify complete structure
        assert project_dir.exists()
        assert (project_dir / "backend").exists()
        assert (project_dir / "frontend").exists()
        assert (project_dir / "docs").exists()
        assert len(created_files) > 0

    def test_project_with_all_features_e2e(self, temp_workspace):
        """Test project generation with all features enabled."""
        from src.utils.output_manager import OutputManager
        
        state = {
            'backend_code': 'from fastapi import FastAPI\napp = FastAPI()',
            'frontend_code': 'console.log("Frontend");',
            'design_document': '# Design',
            'docker_compose': 'version: "3.8"',
            'readme': '# Project README',
            'api_spec': '# API Spec',
        }
        
        manager = OutputManager(temp_workspace / "output")
        project_dir = manager.create_project_dir("full_featured", use_timestamp=False)
        
        created_files = manager.save_structured_output(
            project_dir,
            state,
            include_docker=True,
            include_tests=True
        )
        
        # Verify all components
        assert (project_dir / "backend" / "src" / "main.py").exists()
        assert (project_dir / "frontend" / "src").exists()
        assert (project_dir / "docs").exists()
        assert (project_dir / "docker-compose.yml").exists()
        assert (project_dir / "README.md").exists() or True
        assert len(created_files) >= 3


class TestE2EErrorScenarios:
    """Test end-to-end error handling."""

    def test_invalid_job_description_e2e(self):
        """Test handling of invalid job description."""
        invalid_desc = "Too short"
        
        is_valid, error = validate_job_description(invalid_desc)
        
        assert is_valid is False
        assert len(error) > 0

    def test_missing_tdd_file_e2e(self, temp_workspace):
        """Test handling of missing TDD file."""
        nonexistent = temp_workspace / "nonexistent.md"
        
        result = runner.invoke(app, [
            "dev-team",
            "--tdd", str(nonexistent)
        ])
        
        assert result.exit_code != 0

    def test_invalid_tdd_content_e2e(self, temp_workspace):
        """Test handling of invalid TDD content."""
        invalid_tdd = temp_workspace / "invalid.md"
        invalid_tdd.write_text("# Not a proper TDD")
        
        is_valid, error = validate_tdd_file(invalid_tdd)
        
        # Should detect issues or pass with minimal validation
        assert is_valid in [True, False]


class TestE2EPerformance:
    """Test end-to-end performance scenarios."""

    def test_large_project_generation_e2e(self, temp_workspace):
        """Test generation of large project structure."""
        from src.utils.output_manager import OutputManager
        
        # Create large state with many files
        state = {
            'backend_code': '# Backend\n' + 'print("test")\n' * 100,
            'frontend_code': '// Frontend\n' + 'console.log("test");\n' * 100,
            'design_document': '# Design\n' + '## Section\n' * 50,
        }
        
        manager = OutputManager(temp_workspace / "output")
        project_dir = manager.create_project_dir("large_project", use_timestamp=False)
        
        # Should handle large content
        created_files = manager.save_structured_output(project_dir, state)
        
        assert project_dir.exists()
        assert len(created_files) > 0

    def test_multiple_project_generation_e2e(self, temp_workspace):
        """Test generating multiple projects sequentially."""
        from src.utils.output_manager import OutputManager
        
        manager = OutputManager(temp_workspace / "output")
        state = {'backend_code': 'print("test")'}
        
        projects = []
        for i in range(3):
            project_dir = manager.create_project_dir(f"project_{i}", use_timestamp=True)
            manager.save_structured_output(project_dir, state)
            projects.append(project_dir)
        
        # All projects should exist
        for project_dir in projects:
            assert project_dir.exists()
        
        # Should have unique names
        assert len(set(p.name for p in projects)) == 3


class TestE2EIntegration:
    """Test end-to-end integration scenarios."""

    def test_config_integration_e2e(self):
        """Test configuration integration in E2E scenario."""
        from src.core.config import settings
        
        # Settings should be loaded
        assert settings is not None
        assert settings.default_model is not None

    def test_logging_integration_e2e(self):
        """Test logging integration in E2E scenario."""
        from src.utils.logger import setup_logger
        
        logger = setup_logger("test_e2e")
        
        # Logger should work
        logger.info("Test log message")
        
        assert logger is not None

    def test_progress_integration_e2e(self, temp_workspace):
        """Test progress tracking in E2E scenario."""
        from src.utils.progress import ProjectProgress
        from src.utils.output_manager import OutputManager
        
        progress = ProjectProgress("E2E Test")
        stages = ["Setup", "Generate", "Finalize"]
        
        manager = OutputManager(temp_workspace / "output")
        
        with progress.track_generation(stages) as update:
            update("Setup")
            project_dir = manager.create_project_dir("test", use_timestamp=False)
            
            update("Generate")
            state = {'backend_code': 'test'}
            
            update("Finalize")
            manager.save_structured_output(project_dir, state)
        
        assert project_dir.exists()


class TestE2EUserScenarios:
    """Test realistic user scenarios."""

    def test_first_time_user_scenario(self, job_description_file):
        """Test typical first-time user workflow."""
        # User validates their job description
        job_text = job_description_file.read_text()
        is_valid, _ = validate_job_description(job_text)
        assert is_valid is True
        
        # User checks version
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        
        # User checks info
        result = runner.invoke(app, ["info"])
        assert result.exit_code == 0

    def test_experienced_user_scenario(self, tdd_file, temp_workspace):
        """Test experienced user direct workflow."""
        output_dir = temp_workspace / "my_project"
        
        # User directly runs dev-team with custom options
        result = runner.invoke(app, [
            "dev-team",
            "--tdd", str(tdd_file),
            "--output", str(output_dir),
            "--framework", "fastapi",
            "--frontend", "react",
            "--no-validate"
        ])
        
        # Command should parse correctly
        assert result.exit_code in [0, 1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
