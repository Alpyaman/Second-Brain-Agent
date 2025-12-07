"""
Progress tracking utilities using Rich for beautiful terminal output.
Provides consistent progress indicators across the application.
"""

from typing import List, Callable, Any
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from contextlib import contextmanager

console = Console()


class ProjectProgress:
    """
    Track project generation progress with rich visual feedback.
    
    Features:
    - Multi-stage progress tracking
    - Nested progress bars
    - Status messages
    - Time estimates
    """
    
    def __init__(self, description: str = "Processing"):
        """
        Initialize progress tracker.
        
        Args:
            description: Main task description
        """
        self.description = description
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        )
    
    @contextmanager
    def track_generation(self, stages: List[str]):
        """
        Track multi-stage code generation with progress bar.
        
        Args:
            stages: List of stage descriptions
            
        Yields:
            Function to update current stage
            
        Example:
            stages = ["Parse TDD", "Generate Backend", "Generate Frontend"]
            with progress.track_generation(stages) as update:
                for stage in stages:
                    update(stage)
                    # ... do work ...
        """
        with self.progress:
            task_id = self.progress.add_task(
                f"[cyan]{self.description}",
                total=len(stages)
            )
            
            def update_stage(stage: str, advance: int = 1):
                """Update current stage and advance progress."""
                self.progress.update(
                    task_id,
                    description=f"[cyan]{stage}",
                    advance=advance
                )
            
            yield update_stage
            
            # Complete the task
            self.progress.update(task_id, completed=len(stages))
    
    @contextmanager
    def track_tasks(self, total: int, description: str = None):
        """
        Track a fixed number of tasks.
        
        Args:
            total: Total number of tasks
            description: Optional description
            
        Yields:
            Function to advance progress
            
        Example:
            with progress.track_tasks(10, "Processing files") as advance:
                for file in files:
                    # ... process file ...
                    advance()
        """
        desc = description or self.description
        
        with self.progress:
            task_id = self.progress.add_task(f"[cyan]{desc}", total=total)
            
            def advance(amount: int = 1):
                """Advance progress by specified amount."""
                self.progress.update(task_id, advance=amount)
            
            yield advance
    
    @contextmanager
    def track_indefinite(self, description: str = None):
        """
        Track an indefinite task (spinner only, no bar).
        
        Args:
            description: Task description
            
        Yields:
            Function to update description
            
        Example:
            with progress.track_indefinite("Loading") as update:
                # ... do work ...
                update("Still loading...")
        """
        desc = description or self.description
        
        with self.progress:
            task_id = self.progress.add_task(f"[cyan]{desc}", total=None)
            
            def update_desc(new_desc: str):
                """Update task description."""
                self.progress.update(task_id, description=f"[cyan]{new_desc}")
            
            yield update_desc


class MultiStageProgress:
    """
    Track multiple concurrent progress tasks.
    Useful for parallel agent operations.
    """
    
    def __init__(self):
        """Initialize multi-stage progress tracker."""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        )
        self.tasks = {}
    
    def add_task(self, name: str, total: int = 100, description: str = None) -> int:
        """
        Add a new task to track.
        
        Args:
            name: Task name (identifier)
            total: Total units for task
            description: Display description
            
        Returns:
            Task ID
        """
        desc = description or name
        task_id = self.progress.add_task(f"[cyan]{desc}", total=total)
        self.tasks[name] = task_id
        return task_id
    
    def update(self, name: str, advance: int = 1, description: str = None):
        """
        Update a task's progress.
        
        Args:
            name: Task name
            advance: Amount to advance
            description: Optional new description
        """
        if name in self.tasks:
            kwargs = {'advance': advance}
            if description:
                kwargs['description'] = f"[cyan]{description}"
            self.progress.update(self.tasks[name], **kwargs)
    
    def complete(self, name: str):
        """Mark a task as complete."""
        if name in self.tasks:
            self.progress.update(self.tasks[name], completed=100)
    
    def start(self):
        """Start the progress display."""
        self.progress.start()
    
    def stop(self):
        """Stop the progress display."""
        self.progress.stop()
    
    @contextmanager
    def run(self):
        """Context manager for multi-stage progress."""
        with self.progress:
            yield self


def show_generation_summary(
    project_name: str,
    components: List[str],
    time_elapsed: float,
    files_created: int,
):
    """
    Display a beautiful summary of code generation.
    
    Args:
        project_name: Name of generated project
        components: List of generated components
        time_elapsed: Time taken in seconds
        files_created: Number of files created
    """
    table = Table(title=f" {project_name} - Generation Complete", show_header=True)
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    
    for component in components:
        table.add_row(component, "✓ Complete")
    
    console.print(table)
    
    # Statistics
    stats_table = Table(show_header=False, box=None)
    stats_table.add_column("Metric", style="dim")
    stats_table.add_column("Value", style="bold green")
    
    stats_table.add_row("Time Elapsed", f"{time_elapsed:.2f}s")
    stats_table.add_row("Files Created", str(files_created))
    stats_table.add_row("Components", str(len(components)))
    
    console.print(Panel(stats_table, title=" Statistics", border_style="green"))


def show_agent_activity(agents: List[dict]):
    """
    Display live agent activity status.
    
    Args:
        agents: List of agent dictionaries with 'name', 'status', 'task'
    """
    table = Table(title=" Agent Activity", show_header=True)
    table.add_column("Agent", style="cyan")
    table.add_column("Status", style="yellow")
    table.add_column("Current Task", style="dim")
    
    for agent in agents:
        status_icon = "🟢" if agent['status'] == 'active' else "⚪"
        table.add_row(
            agent['name'],
            f"{status_icon} {agent['status']}",
            agent.get('task', '-')
        )
    
    console.print(table)


@contextmanager
def spinner(text: str):
    """
    Simple spinner context manager.
    
    Args:
        text: Text to display next to spinner
        
    Example:
        with spinner("Loading data"):
            # ... do work ...
    """
    with console.status(f"[cyan]{text}...", spinner="dots"):
        yield


def track_function(description: str, stages: List[str]):
    """
    Decorator to track function execution with progress.
    
    Args:
        description: Function description
        stages: List of stage descriptions
        
    Example:
        @track_function("Processing data", ["Load", "Transform", "Save"])
        def process_data():
            yield "Load"
            # ... load ...
            yield "Transform"
            # ... transform ...
            yield "Save"
            # ... save ...
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            progress = ProjectProgress(description)
            with progress.track_generation(stages) as update:
                result = None
                for stage in func(*args, **kwargs):
                    if isinstance(stage, str):
                        update(stage)
                    else:
                        result = stage
                return result
        return wrapper
    return decorator


# Example usage functions for testing
def example_simple_progress():
    """Example: Simple progress tracking."""
    progress = ProjectProgress("Generating Code")
    stages = [
        "Parsing TDD",
        "Generating Backend",
        "Generating Frontend",
        "Creating Docker Config",
        "Finalizing"
    ]
    
    with progress.track_generation(stages) as update:
        import time
        for stage in stages:
            update(stage)
            time.sleep(1)  # Simulate work


def example_multi_stage():
    """Example: Multiple concurrent tasks."""
    multi = MultiStageProgress()
    
    with multi.run():
        # Add tasks
        multi.add_task("backend", total=100, description="Backend Generation")
        multi.add_task("frontend", total=100, description="Frontend Generation")
        multi.add_task("docker", total=100, description="Docker Configuration")
        
        # Simulate work
        import time
        for i in range(100):
            multi.update("backend", advance=1)
            multi.update("frontend", advance=1)
            multi.update("docker", advance=1)
            time.sleep(0.05)


def example_summary():
    """Example: Generation summary display."""
    show_generation_summary(
        project_name="My Awesome Project",
        components=["Backend", "Frontend", "Docker", "Tests", "Docs"],
        time_elapsed=45.3,
        files_created=23
    )


if __name__ == "__main__":
    # Run examples
    console.print("[bold]Simple Progress Example:[/bold]")
    example_simple_progress()
    
    console.print("\n[bold]Multi-Stage Progress Example:[/bold]")
    example_multi_stage()
    
    console.print("\n[bold]Summary Example:[/bold]")
    example_summary()
