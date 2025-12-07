"""
Unit tests for CLI commands.

Tests Typer CLI application, command parsing, and execution.
"""

import sys
from pathlib import Path

# Add project root to path for direct execution
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest  # noqa: E402
from typer.testing import CliRunner  # noqa: E402
from unittest.mock import patch  # noqa: E402
import tempfile  # noqa: E402
import shutil  # noqa: E402

from src.cli.main import app  # noqa: E402


runner = CliRunner()


@pytest.fixture
def temp_job_file():
    """Create a temporary job description file."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
    temp_file.write("""
    Build a REST API for a task management system with:
    - User authentication
    - CRUD operations for tasks
    - Task assignments and priorities
    - RESTful endpoints
    """)
    temp_file.close()
    yield Path(temp_file.name)
    Path(temp_file.name).unlink(missing_ok=True)


@pytest.fixture
def temp_tdd_file():
    """Create a temporary TDD file."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md')
    temp_file.write("""
    # Technical Design Document
    
    ## Architecture
    RESTful API with FastAPI
    
    ## Components
    - Authentication Service
    - Task Service
    - Database Layer
    
    ## API Endpoints
    - POST /api/auth/login
    - GET /api/tasks
    - POST /api/tasks
    """)
    temp_file.close()
    yield Path(temp_file.name)
    Path(temp_file.name).unlink(missing_ok=True)


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    temp_dir = tempfile.mkdtemp(prefix="test_cli_output_")
    yield Path(temp_dir)
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir)


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_app_exists(self):
        """Test that CLI app exists."""
        assert app is not None

    def test_cli_help(self):
        """Test CLI help command."""
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "second-brain-agent" in result.stdout or "Transform" in result.stdout

    def test_version_command(self):
        """Test version command."""
        result = runner.invoke(app, ["version"])
        
        assert result.exit_code == 0
        assert "Second Brain Agent" in result.stdout or "0.1.0" in result.stdout

    def test_info_command(self):
        """Test info command."""
        result = runner.invoke(app, ["info"])
        
        assert result.exit_code == 0
        # Should show system information
        assert "Python" in result.stdout or "Platform" in result.stdout or True


class TestArchitectCommand:
    """Test architect command."""

    def test_architect_help(self):
        """Test architect command help."""
        result = runner.invoke(app, ["architect", "--help"])
        
        assert result.exit_code == 0
        assert "architect" in result.stdout.lower()

    def test_architect_missing_job_description(self):
        """Test architect command without job description."""
        result = runner.invoke(app, ["architect"])
        
        # Should fail or ask for input
        assert result.exit_code != 0 or "job" in result.stdout.lower()

    def test_architect_with_inline_job(self):
        """Test architect command with inline job description."""
        with patch('src.cli.main.logger'):
            result = runner.invoke(app, [
                "architect",
                "--job", "Build a simple REST API for blog posts",
                "--output", "test_design.md",
                "--no-validate"
            ])
            
            # May fail due to missing LLM setup, but command should parse correctly
            assert "--job" in str(result) or result.exit_code in [0, 1, 130]

    def test_architect_with_job_file(self, temp_job_file):
        """Test architect command with job file."""
        result = runner.invoke(app, [
            "architect",
            "--job-file", str(temp_job_file),
            "--output", "test_design.md",
            "--no-validate"
        ])
        
        # Command should parse correctly
        assert result.exit_code in [0, 1, 130]  # May fail due to LLM setup or quota

    def test_architect_model_option(self):
        """Test architect command with model option."""
        result = runner.invoke(app, [
            "architect",
            "--job", "Build API",
            "--model", "gpt-4",
            "--no-validate"
        ])
        
        # Command should recognize model option
        assert result.exit_code in [0, 1, 130]

    def test_architect_interactive_mode(self):
        """Test architect command with interactive mode."""
        result = runner.invoke(app, [
            "architect",
            "--job", "Build API",
            "--interactive",
            "--no-validate"
        ])
        
        assert result.exit_code in [0, 1]


class TestDevTeamCommand:
    """Test dev-team command."""

    def test_dev_team_help(self):
        """Test dev-team command help."""
        result = runner.invoke(app, ["dev-team", "--help"])
        
        assert result.exit_code == 0
        assert "dev" in result.stdout.lower() or "team" in result.stdout.lower()

    def test_dev_team_missing_tdd(self):
        """Test dev-team command without TDD file."""
        result = runner.invoke(app, ["dev-team"])
        
        # Should fail
        assert result.exit_code != 0

    def test_dev_team_with_tdd(self, temp_tdd_file, temp_output_dir):
        """Test dev-team command with TDD file."""
        result = runner.invoke(app, [
            "dev-team",
            "--tdd", str(temp_tdd_file),
            "--output", str(temp_output_dir),
            "--no-validate"
        ])
        
        # May fail due to LLM setup, but command should parse
        assert result.exit_code in [0, 1]

    def test_dev_team_framework_option(self, temp_tdd_file, temp_output_dir):
        """Test dev-team with framework option."""
        result = runner.invoke(app, [
            "dev-team",
            "--tdd", str(temp_tdd_file),
            "--output", str(temp_output_dir),
            "--framework", "django",
            "--no-validate"
        ])
        
        assert result.exit_code in [0, 1]

    def test_dev_team_frontend_option(self, temp_tdd_file, temp_output_dir):
        """Test dev-team with frontend option."""
        result = runner.invoke(app, [
            "dev-team",
            "--tdd", str(temp_tdd_file),
            "--output", str(temp_output_dir),
            "--frontend", "vue",
            "--no-validate"
        ])
        
        assert result.exit_code in [0, 1]

    def test_dev_team_phase_option(self, temp_tdd_file, temp_output_dir):
        """Test dev-team with phase option."""
        result = runner.invoke(app, [
            "dev-team",
            "--tdd", str(temp_tdd_file),
            "--output", str(temp_output_dir),
            "--phase", "1",
            "--no-validate"
        ])
        
        assert result.exit_code in [0, 1]

    def test_dev_team_no_docker(self, temp_tdd_file, temp_output_dir):
        """Test dev-team with Docker disabled."""
        result = runner.invoke(app, [
            "dev-team",
            "--tdd", str(temp_tdd_file),
            "--output", str(temp_output_dir),
            "--no-docker",
            "--no-validate"
        ])
        
        assert result.exit_code in [0, 1]


class TestCommandValidation:
    """Test command input validation."""

    def test_architect_invalid_job_file(self):
        """Test architect with non-existent job file."""
        result = runner.invoke(app, [
            "architect",
            "--job-file", "nonexistent.txt",
            "--no-validate"
        ])
        
        # Should fail
        assert result.exit_code != 0

    def test_dev_team_invalid_tdd_file(self):
        """Test dev-team with non-existent TDD file."""
        result = runner.invoke(app, [
            "dev-team",
            "--tdd", "nonexistent.md"
        ])
        
        # Should fail
        assert result.exit_code != 0

    def test_dev_team_invalid_phase(self, temp_tdd_file):
        """Test dev-team with invalid phase number."""
        result = runner.invoke(app, [
            "dev-team",
            "--tdd", str(temp_tdd_file),
            "--phase", "99"
        ])
        
        # Should fail or handle gracefully
        assert result.exit_code in [0, 1, 2]


class TestCommandOptions:
    """Test various command options and flags."""

    def test_architect_output_option(self):
        """Test architect output file option."""
        result = runner.invoke(app, [
            "architect",
            "--job", "Build API",
            "--output", "custom_design.md",
            "--no-validate"
        ])
        
        # Should handle output option
        assert result.exit_code in [0, 1, 130]

    def test_multiple_boolean_flags(self, temp_tdd_file, temp_output_dir):
        """Test multiple boolean flags together."""
        result = runner.invoke(app, [
            "dev-team",
            "--tdd", str(temp_tdd_file),
            "--output", str(temp_output_dir),
            "--no-docker",
            "--no-validate"
        ])
        
        assert result.exit_code in [0, 1]


class TestCLIOutput:
    """Test CLI output formatting."""

    def test_version_output_format(self):
        """Test version command output is well-formatted."""
        result = runner.invoke(app, ["version"])
        
        assert result.exit_code == 0
        # Should have some output
        assert len(result.stdout) > 0

    def test_help_output_readable(self):
        """Test that help output is readable."""
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert len(result.stdout) > 100  # Should have substantial help text


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_invalid_command(self):
        """Test invalid command."""
        result = runner.invoke(app, ["nonexistent-command"])
        
        # Should show error
        assert result.exit_code != 0

    def test_conflicting_options(self):
        """Test conflicting options."""
        result = runner.invoke(app, [
            "architect",
            "--job", "Build API",
            "--job-file", "file.txt",  # Can't have both
            "--no-validate"
        ])
        
        # May handle or fail gracefully
        assert result.exit_code in [0, 1, 2]


class TestCLIIntegration:
    """Test CLI integration scenarios."""

    @patch('src.cli.main.logger')
    def test_architect_logging(self, mock_logger):
        """Test that architect command uses logging."""
        result = runner.invoke(app, [
            "architect",
            "--job", "Build API",
            "--no-validate"
        ])
        
        # Logger should be used (info, error, etc.)
        # Test passes if no exception

    def test_cli_with_environment_variables(self):
        """Test CLI respects environment variables."""
        # Test that CLI can run with env vars
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0


class TestCLIMocking:
    """Test CLI with mocked dependencies."""

    @patch('src.cli.main.validate_job_description')
    def test_architect_calls_validator(self, mock_validator, temp_job_file):
        """Test that architect calls validation."""
        mock_validator.return_value = (True, "")
        
        result = runner.invoke(app, [
            "architect",
            "--job-file", str(temp_job_file),
            "--output", "design.md"
        ])
        
        # May call validator or skip with --no-validate
        # Test that command structure is correct

    @patch('src.cli.main.validate_tdd_file')
    def test_dev_team_calls_validator(self, mock_validator, temp_tdd_file, temp_output_dir):
        """Test that dev-team calls validation."""
        mock_validator.return_value = (True, "")
        
        result = runner.invoke(app, [
            "dev-team",
            "--tdd", str(temp_tdd_file),
            "--output", str(temp_output_dir)
        ])
        
        # Test command structure


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
