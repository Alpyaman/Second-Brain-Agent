"""
Unit tests for OutputManager.

Tests project directory creation, structured output generation,
and file organization functionality.
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
import json  # noqa: E402
from datetime import datetime  # noqa: E402

from src.utils.output_manager import OutputManager, create_project_output  # noqa: E402


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory for testing."""
    temp_dir = tempfile.mkdtemp(prefix="test_output_")
    yield Path(temp_dir)
    # Cleanup
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_state():
    """Sample state dictionary for testing."""
    return {
        'backend_code': '# Backend code\nprint("Hello Backend")',
        'frontend_code': '// Frontend code\nconsole.log("Hello Frontend");',
        'design_document': '# Design Document\n## Architecture\nRESTful API',
        'database_schema': 'CREATE TABLE users (id INT PRIMARY KEY);',
        'api_spec': '# API Specification\n## Endpoints\n- GET /users',
        'docker_compose': 'version: "3.8"\nservices:\n  backend:\n    build: ./backend',
        'readme': '# Project README\n## Getting Started',
    }


class TestOutputManager:
    """Test OutputManager class."""

    def test_initialization(self, temp_output_dir):
        """Test OutputManager initialization."""
        manager = OutputManager(temp_output_dir)
        
        assert manager.base_dir == temp_output_dir
        assert temp_output_dir.exists()

    def test_initialization_creates_base_dir(self):
        """Test that initialization creates base directory."""
        temp_dir = Path(tempfile.gettempdir()) / "test_new_output"
        
        # Ensure it doesn't exist
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        
        manager = OutputManager(temp_dir)
        
        assert temp_dir.exists()
        
        # Cleanup
        shutil.rmtree(temp_dir)

    def test_create_project_dir_with_timestamp(self, temp_output_dir):
        """Test creating project directory with timestamp."""
        manager = OutputManager(temp_output_dir)
        
        project_dir = manager.create_project_dir("test_project", use_timestamp=True)
        
        assert project_dir.exists()
        assert project_dir.parent == temp_output_dir
        assert "test_project" in project_dir.name
        # Check timestamp format (YYYYMMDD_HHMMSS)
        assert "_" in project_dir.name

    def test_create_project_dir_without_timestamp(self, temp_output_dir):
        """Test creating project directory without timestamp."""
        manager = OutputManager(temp_output_dir)
        
        project_dir = manager.create_project_dir("test_project", use_timestamp=False)
        
        assert project_dir.exists()
        assert project_dir.name == "test_project"

    def test_create_project_dir_idempotent(self, temp_output_dir):
        """Test that creating same directory twice doesn't fail."""
        manager = OutputManager(temp_output_dir)
        
        project_dir1 = manager.create_project_dir("test_project", use_timestamp=False)
        project_dir2 = manager.create_project_dir("test_project", use_timestamp=False)
        
        assert project_dir1 == project_dir2
        assert project_dir1.exists()


class TestStructuredOutput:
    """Test structured output generation."""

    def test_save_structured_output_basic(self, temp_output_dir, sample_state):
        """Test basic structured output generation."""
        manager = OutputManager(temp_output_dir)
        project_dir = manager.create_project_dir("test_project", use_timestamp=False)
        
        created_files = manager.save_structured_output(project_dir, sample_state)
        
        # Check that key files were created
        assert 'backend_code' in created_files
        assert 'readme' in created_files
        
        # Check directory structure
        assert (project_dir / "backend").exists()
        assert (project_dir / "frontend").exists()
        assert (project_dir / "docs").exists()

    def test_backend_structure(self, temp_output_dir, sample_state):
        """Test backend directory structure."""
        manager = OutputManager(temp_output_dir)
        project_dir = manager.create_project_dir("test_project", use_timestamp=False)
        
        manager.save_structured_output(project_dir, sample_state)
        
        backend_dir = project_dir / "backend"
        assert backend_dir.exists()
        assert (backend_dir / "src").exists()
        assert (backend_dir / "src" / "main.py").exists()
        
        # Verify content
        content = (backend_dir / "src" / "main.py").read_text()
        assert "Backend code" in content

    def test_frontend_structure(self, temp_output_dir, sample_state):
        """Test frontend directory structure."""
        manager = OutputManager(temp_output_dir)
        project_dir = manager.create_project_dir("test_project", use_timestamp=False)
        
        manager.save_structured_output(project_dir, sample_state)
        
        frontend_dir = project_dir / "frontend"
        assert frontend_dir.exists()
        assert (frontend_dir / "src").exists()
        assert (frontend_dir / "src" / "App.tsx").exists()
        
        # Verify content
        content = (frontend_dir / "src" / "App.tsx").read_text()
        assert "Frontend code" in content

    def test_docs_structure(self, temp_output_dir, sample_state):
        """Test documentation directory structure."""
        manager = OutputManager(temp_output_dir)
        project_dir = manager.create_project_dir("test_project", use_timestamp=False)
        
        manager.save_structured_output(project_dir, sample_state)
        
        docs_dir = project_dir / "docs"
        assert docs_dir.exists()
        assert (docs_dir / "DESIGN.md").exists()
        
        # Verify content
        content = (docs_dir / "DESIGN.md").read_text()
        assert "Design Document" in content

    def test_docker_configuration(self, temp_output_dir, sample_state):
        """Test Docker configuration generation."""
        manager = OutputManager(temp_output_dir)
        project_dir = manager.create_project_dir("test_project", use_timestamp=False)
        
        manager.save_structured_output(
            project_dir, 
            sample_state, 
            include_docker=True
        )
        
        assert (project_dir / "docker-compose.yml").exists()
        
        # Verify content
        content = (project_dir / "docker-compose.yml").read_text()
        assert "version:" in content or "services:" in content

    def test_no_docker_configuration(self, temp_output_dir, sample_state):
        """Test that Docker files are not created when disabled."""
        manager = OutputManager(temp_output_dir)
        project_dir = manager.create_project_dir("test_project", use_timestamp=False)
        
        manager.save_structured_output(
            project_dir, 
            sample_state, 
            include_docker=False
        )
        
        # Docker files should not exist
        assert not (project_dir / "docker-compose.yml").exists()

    def test_tests_structure(self, temp_output_dir, sample_state):
        """Test test directory structure creation."""
        manager = OutputManager(temp_output_dir)
        project_dir = manager.create_project_dir("test_project", use_timestamp=False)
        
        manager.save_structured_output(
            project_dir, 
            sample_state, 
            include_tests=True
        )
        
        # Check test directories (only backend tests are created)
        backend_tests = project_dir / "backend" / "tests"
        backend_test_file = project_dir / "backend" / "tests" / "test_api.py"
        
        assert backend_tests.exists()
        assert backend_test_file.exists()
        
        # Frontend tests are not created by default
        frontend_tests = project_dir / "frontend" / "tests"
        assert not frontend_tests.exists()

    def test_no_tests_structure(self, temp_output_dir, sample_state):
        """Test that test directories are not created when disabled."""
        manager = OutputManager(temp_output_dir)
        project_dir = manager.create_project_dir("test_project", use_timestamp=False)
        
        manager.save_structured_output(
            project_dir, 
            sample_state, 
            include_tests=False
        )
        
        # Test directories should not exist
        backend_tests = project_dir / "backend" / "tests"
        assert not backend_tests.exists()


class TestMetadataAndManifest:
    """Test metadata and file manifest generation."""

    def test_save_project_metadata(self, temp_output_dir, sample_state):
        """Test project metadata generation."""
        manager = OutputManager(temp_output_dir)
        project_dir = manager.create_project_dir("test_project", use_timestamp=False)
        
        manager.save_structured_output(project_dir, sample_state)
        
        metadata_file = project_dir / ".sba_metadata.json"
        assert metadata_file.exists()
        
        # Load and verify metadata
        metadata = json.loads(metadata_file.read_text())
        assert "project_name" in metadata
        assert "created_at" in metadata
        assert "components" in metadata

    def test_metadata_content(self, temp_output_dir, sample_state):
        """Test metadata content is correct."""
        manager = OutputManager(temp_output_dir)
        project_dir = manager.create_project_dir("my_project", use_timestamp=False)
        
        manager.save_structured_output(project_dir, sample_state)
        
        metadata_file = project_dir / ".sba_metadata.json"
        metadata = json.loads(metadata_file.read_text())
        
        assert metadata["project_name"] == "my_project"
        assert isinstance(metadata["components"], list)
        assert len(metadata["components"]) > 0

    @pytest.mark.skip(reason="File manifest not yet implemented")
    def test_file_manifest(self, temp_output_dir, sample_state):
        """Test file manifest generation."""
        manager = OutputManager(temp_output_dir)
        project_dir = manager.create_project_dir("test_project", use_timestamp=False)
        
        manager.save_structured_output(project_dir, sample_state)
        
        manifest_file = project_dir / "FILE_MANIFEST.md"
        assert manifest_file.exists()
        
        content = manifest_file.read_text()
        assert "backend/" in content
        assert "frontend/" in content


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_create_project_output(self, temp_output_dir, sample_state):
        """Test create_project_output convenience function."""
        project_dir = create_project_output(
            project_name="test_project",
            state=sample_state,
            output_dir=temp_output_dir
        )
        
        assert project_dir.exists()
        assert (project_dir / "backend").exists()
        assert (project_dir / "frontend").exists()

    def test_create_project_output_default_dir(self, sample_state):
        """Test create_project_output with default output directory."""
        # Use a unique name to avoid conflicts
        project_name = f"test_project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        project_dir = create_project_output(
            project_name=project_name,
            state=sample_state
        )
        
        assert project_dir.exists()
        
        # Cleanup
        if project_dir.exists():
            shutil.rmtree(project_dir)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_state(self, temp_output_dir):
        """Test handling of empty state dictionary."""
        manager = OutputManager(temp_output_dir)
        project_dir = manager.create_project_dir("test_project", use_timestamp=False)
        
        # Should not raise error
        created_files = manager.save_structured_output(project_dir, {})
        
        # Basic structure should still be created
        assert (project_dir / "backend").exists()
        assert (project_dir / "frontend").exists()

    def test_special_characters_in_project_name(self, temp_output_dir):
        """Test project names with special characters."""
        manager = OutputManager(temp_output_dir)
        
        # Most special characters should work
        project_dir = manager.create_project_dir("test-project_123", use_timestamp=False)
        
        assert project_dir.exists()

    def test_long_project_name(self, temp_output_dir):
        """Test very long project name."""
        manager = OutputManager(temp_output_dir)
        
        long_name = "a" * 200
        project_dir = manager.create_project_dir(long_name, use_timestamp=False)
        
        assert project_dir.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
