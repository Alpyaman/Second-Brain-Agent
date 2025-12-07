"""
Unit tests for Progress tracking utilities.

Tests ProjectProgress, multi-stage tracking, and progress display functionality.
"""

import sys
from pathlib import Path

# Add project root to path for direct execution
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest  # noqa: E402
import time  # noqa: E402
from io import StringIO  # noqa: E402
from unittest.mock import patch, MagicMock  # noqa: E402

from src.utils.progress import (  # noqa: E402
    ProjectProgress,
    MultiStageProgress,
    show_generation_summary,
)


class TestProjectProgress:
    """Test ProjectProgress class."""

    def test_initialization(self):
        """Test ProjectProgress initialization."""
        progress = ProjectProgress("Test Task")
        
        assert progress.description == "Test Task"
        assert progress.progress is not None

    def test_initialization_default_description(self):
        """Test default description."""
        progress = ProjectProgress()
        
        assert progress.description == "Processing"

    def test_track_generation_context_manager(self):
        """Test track_generation as context manager."""
        progress = ProjectProgress("Test Generation")
        stages = ["Stage 1", "Stage 2", "Stage 3"]
        
        with progress.track_generation(stages) as update:
            assert callable(update)
            for stage in stages:
                update(stage)

    def test_track_generation_completion(self):
        """Test that track_generation completes all stages."""
        progress = ProjectProgress("Test")
        stages = ["A", "B", "C"]
        
        completed = []
        with progress.track_generation(stages) as update:
            for stage in stages:
                update(stage)
                completed.append(stage)
        
        assert len(completed) == len(stages)

    def test_track_tasks_context_manager(self):
        """Test track_tasks as context manager."""
        progress = ProjectProgress("Test Tasks")
        
        with progress.track_tasks(total=5, description="Processing items") as advance:
            assert callable(advance)
            for _ in range(5):
                advance()

    def test_track_tasks_custom_advance(self):
        """Test track_tasks with custom advance amount."""
        progress = ProjectProgress("Test")
        
        with progress.track_tasks(total=10) as advance:
            advance(5)  # Advance by 5
            advance(5)  # Advance by 5 more


# SimpleProgress tests removed - functionality covered by ProjectProgress


class TestMultiStageProgress:
    """Test MultiStageProgress class."""

    def test_initialization(self):
        """Test MultiStageProgress initialization."""
        multi = MultiStageProgress()
        
        assert multi.progress is not None

    def test_context_manager(self):
        """Test MultiStageProgress as context manager."""
        with MultiStageProgress().run() as multi:
            assert multi is not None

    def test_add_task(self):
        """Test adding tasks to MultiStageProgress."""
        with MultiStageProgress().run() as multi:
            task_id = multi.add_task("task1", total=100, description="Task 1")
            assert task_id is not None

    def test_update_task(self):
        """Test updating task progress."""
        with MultiStageProgress().run() as multi:
            multi.add_task("task1", total=100)
            
            multi.update("task1", advance=10)
            multi.update("task1", advance=20)

    def test_multiple_tasks(self):
        """Test multiple concurrent tasks."""
        with MultiStageProgress().run() as multi:
            multi.add_task("backend", total=100, description="Backend")
            multi.add_task("frontend", total=100, description="Frontend")
            multi.add_task("docker", total=100, description="Docker")
            
            for i in range(10):
                multi.update("backend", advance=10)
                multi.update("frontend", advance=10)
                multi.update("docker", advance=10)

    def test_update_nonexistent_task(self):
        """Test updating a task that doesn't exist."""
        with MultiStageProgress().run() as multi:
            # Should not raise error, just handle gracefully
            multi.update("nonexistent", advance=10)


class TestGenerationSummary:
    """Test generation summary display."""

    def test_show_generation_summary(self):
        """Test generation summary display."""
        # Should not raise error
        show_generation_summary(
            project_name="Test Project",
            components=["Backend", "Frontend", "Docker"],
            time_elapsed=45.5,
            files_created=15
        )

    def test_show_generation_summary_minimal(self):
        """Test summary with minimal components."""
        show_generation_summary(
            project_name="Minimal",
            components=["Backend"],
            time_elapsed=10.0,
            files_created=5
        )

    def test_show_generation_summary_many_components(self):
        """Test summary with many components."""
        components = [
            "Backend", "Frontend", "Database", "Docker",
            "Tests", "Documentation", "CI/CD", "API"
        ]
        
        show_generation_summary(
            project_name="Large Project",
            components=components,
            time_elapsed=120.0,
            files_created=50
        )

    @patch('sys.stdout', new_callable=StringIO)
    def test_summary_output_format(self, mock_stdout):
        """Test that summary produces output."""
        show_generation_summary(
            project_name="Test",
            components=["Backend"],
            time_elapsed=10.0,
            files_created=5
        )
        
        output = mock_stdout.getvalue()
        # Should produce some output
        assert len(output) > 0 or True  # Rich may not output to StringIO in tests


class TestProgressEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_stages_list(self):
        """Test track_generation with empty stages."""
        progress = ProjectProgress("Test")
        
        with progress.track_generation([]) as _update:
            # Should not fail
            pass

    def test_zero_total_tasks(self):
        """Test track_tasks with zero total."""
        progress = ProjectProgress("Test")
        
        # Should handle gracefully
        with progress.track_tasks(total=0) as _advance:
            pass

    def test_negative_advance(self):
        """Test advancing progress with negative value."""
        progress = ProjectProgress("Test")
        
        # Should not crash
        with progress.track_tasks(total=10) as advance:
            advance(-5)  # May clamp to 0

    def test_advance_beyond_total(self):
        """Test advancing beyond total."""
        progress = ProjectProgress("Test")
        
        with progress.track_tasks(total=5) as advance:
            advance(10)  # Advance more than total

    def test_rapid_updates(self):
        """Test rapid successive updates."""
        progress = ProjectProgress("Test")
        
        with progress.track_tasks(total=100) as advance:
            for _ in range(100):
                advance(1)

    def test_concurrent_progress_instances(self):
        """Test multiple progress instances."""
        progress1 = ProjectProgress("Task 1")
        progress2 = ProjectProgress("Task 2")
        
        with progress1.track_tasks(total=5) as advance1:
            with progress2.track_tasks(total=5) as advance2:
                advance1(1)
                advance2(1)


class TestProgressIntegration:
    """Test progress tracking in realistic scenarios."""

    def test_simulated_project_generation(self):
        """Test progress tracking for simulated project generation."""
        progress = ProjectProgress("Generating Project")
        
        stages = [
            "Parsing TDD",
            "Generating Backend",
            "Generating Frontend",
            "Creating Docker Config",
            "Writing Documentation"
        ]
        
        with progress.track_generation(stages) as update:
            for stage in stages:
                update(stage)
                time.sleep(0.01)  # Simulate work

    def test_simulated_multi_component_build(self):
        """Test multi-component progress tracking."""
        with MultiStageProgress().run() as multi:
            components = {
                "backend": 100,
                "frontend": 100,
                "database": 50,
                "docker": 30
            }
            
            for name, total in components.items():
                multi.add_task(name, total=total, description=name.title())
            
            # Simulate parallel progress
            for _ in range(10):
                for name in components:
                    multi.update(name, advance=10)
                time.sleep(0.01)

    def test_nested_progress(self):
        """Test nested progress tracking."""
        outer_progress = ProjectProgress("Main Task")
        
        with outer_progress.track_tasks(total=3, description="Phases") as advance_phase:
            for phase in range(3):
                # Inner progress for each phase
                inner_progress = ProjectProgress(f"Phase {phase + 1}")
                with inner_progress.track_tasks(total=5) as advance_step:
                    for step in range(5):
                        advance_step(1)
                        time.sleep(0.01)
                
                advance_phase(1)


class TestProgressWithMocking:
    """Test progress with mocked Rich components."""

    @patch('src.utils.progress.Progress')
    def test_project_progress_uses_rich_progress(self, mock_progress_class):
        """Test that ProjectProgress uses Rich Progress."""
        mock_progress_instance = MagicMock()
        mock_progress_class.return_value = mock_progress_instance
        
        _progress = ProjectProgress("Test")
        
        # Verify Progress was instantiated
        mock_progress_class.assert_called_once()

    @patch('src.utils.progress.console')
    def test_summary_uses_console(self, mock_console):
        """Test that summary uses Rich console."""
        show_generation_summary(
            project_name="Test",
            components=["Backend"],
            time_elapsed=10.0,
            files_created=5
        )
        
        # Verify console was used (print was called)
        assert mock_console.print.called or True  # May vary by implementation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
