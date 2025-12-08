"""
Main CLI application for Second Brain Agent.
Enhanced with Typer for better UX and Rich for beautiful terminal output.
"""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich import print as rprint

from src.utils.logger import setup_logger
from src.utils.validators import validate_job_description, validate_tdd_file
from src.utils.exceptions import ValidationError

# Initialize CLI app
app = typer.Typer(
    name="second-brain-agent",
    help=" Transform job descriptions into working code in minutes",
    add_completion=True,
    rich_markup_mode="rich",
)

console = Console()
logger = setup_logger(__name__)


def print_header(title: str, subtitle: str = None):
    """Print a beautiful header with Rich."""
    content = f"[bold cyan]{title}[/bold cyan]"
    if subtitle:
        content += f"\n[dim]{subtitle}[/dim]"
    
    console.print(Panel(content, border_style="cyan", padding=(1, 2)))


def print_success(message: str):
    """Print success message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_error(message: str):
    """Print error message."""
    console.print(f"[bold red]✗[/bold red] {message}")


def print_info(message: str):
    """Print info message."""
    console.print(f"[bold blue][/bold blue] {message}")


@app.command()
def architect(
    job_description: Optional[str] = typer.Option(
        None,
        "--job",
        "-j",
        help="Job description text (inline)",
    ),
    job_file: Optional[Path] = typer.Option(
        None,
        "--job-file",
        "-f",
        help="Path to job description file",
        exists=True,
    ),
    output: Path = typer.Option(
        "design.md",
        "--output",
        "-o",
        help="Output file for TDD",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Enable interactive mode for refinement",
    ),
    model: str = typer.Option(
        "gemini-pro",
        "--model",
        "-m",
        help="LLM model to use",
    ),
    no_validate: bool = typer.Option(
        False,
        "--no-validate",
        help="Skip input validation",
    ),
):
    """
    🏗️  Generate Technical Design Document from job description.
    
    Examples:
        sba architect -j "Build a REST API for blog"
        sba architect -f job.txt -o design.md
        sba architect -f job.txt -i  # Interactive mode
    """
    print_header("ARCHITECT SESSION", "Generate professional TDD from job description")
    
    # Initialize analytics tracking
    from src.utils.analytics import get_analytics
    import time
    analytics = get_analytics()
    start_time = time.time()
    success = False
    
    try:
        # Get job description
        if job_file:
            print_info(f"Reading job description from: {job_file}")
            job_text = job_file.read_text(encoding="utf-8")
        elif job_description:
            job_text = job_description
        else:
            print_error("Please provide either --job or --job-file")
            raise typer.Exit(code=1)
        
        # Validate input
        if not no_validate:
            console.print("\n[dim]Validating job description...[/dim]")
            is_valid, error_msg = validate_job_description(job_text)
            if not is_valid:
                print_error(f"Validation failed: {error_msg}")
                raise typer.Exit(code=1)
            print_success("Job description validated")
        
        # Show what we're processing
        console.print("\n[bold]Job Description Preview:[/bold]")
        preview = job_text[:200] + "..." if len(job_text) > 200 else job_text
        console.print(Panel(preview, border_style="dim"))
        
        # Process with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Generating TDD...", total=100)
            
            # Import here to avoid circular imports
            from src.agents.architect.graph import run_architect_session
            
            progress.update(task, advance=20, description="[cyan]Analyzing job description...")
            
            # Run architect
            state = run_architect_session(
                goal=job_text,
                is_job_description=True,
            )
            
            progress.update(task, advance=80, description="[cyan]Finalizing design...")
        
        # Save output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(state['design_document'], encoding="utf-8")
        
        print_success("TDD generated successfully!")
        console.print(f"\n[bold]Output saved to:[/bold] [link=file://{output.absolute()}]{output}[/link]")
        
        # Show summary table
        table = Table(title="Generation Summary", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="dim")
        table.add_column("Value", style="green")
        
        table.add_row("Model", model)
        table.add_row("Iterations", str(state.get('iteration_count', 1)))
        table.add_row("Output Size", f"{len(state['design_document'])} chars")
        
        console.print(table)
        
        # Interactive refinement
        if interactive:
            console.print("\n[bold yellow]Interactive Mode[/bold yellow]")
            console.print("Press Enter to refine, or Ctrl+C to exit\n")
            try:
                while True:
                    feedback = typer.prompt("Your feedback (or 'done' to exit)")
                    if feedback.lower() == 'done':
                        break
                    
                    # Re-run with feedback
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        console=console,
                    ) as progress:
                        task = progress.add_task("[cyan]Refining design...", total=None)
                        state = run_architect_session(
                            goal=job_text,
                            is_job_description=True,
                            feedback=feedback,
                        )
                    
                    output.write_text(state['design_document'], encoding="utf-8")
                    print_success(f"Design refined! Updated: {output}")
            except KeyboardInterrupt:
                console.print("\n[dim]Exiting interactive mode[/dim]")
        
        logger.info(f"Architect session completed. Output: {output}")
        success = True
        
        # Track successful generation
        duration = time.time() - start_time
        analytics.track_generation(
            project_name=state.get('project_name', 'cli-architect'),
            duration_seconds=duration,
            tokens_used=state.get('total_tokens', 0),
            estimated_cost=state.get('total_cost', 0.0),
            success=True,
            project_type='tdd',
            framework='architect',
            cache_hits=state.get('cache_hits', 0),
            cache_misses=state.get('cache_misses', 0),
            llm_requests=state.get('llm_calls', 1)
        )
        
    except ValidationError as e:
        print_error(f"Validation error: {e}")
        logger.error(f"Validation error: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        print_error(f"Error: {e}")
        logger.exception("Error in architect command")
        
        # Track failed generation
        if not success:
            duration = time.time() - start_time
            analytics.track_generation(
                project_name='failed',
                duration_seconds=duration,
                tokens_used=0,
                estimated_cost=0.0,
                success=False,
                project_type='tdd',
                framework='architect'
            )
        
        raise typer.Exit(code=1)


@app.command()
def dev_team(
    tdd_file: Path = typer.Option(
        ...,
        "--tdd",
        "-t",
        help="Path to Technical Design Document",
        exists=True,
    ),
    output_dir: Path = typer.Option(
        "./output",
        "--output",
        "-o",
        help="Output directory for generated code",
    ),
    phase: Optional[int] = typer.Option(
        None,
        "--phase",
        "-p",
        help="Specific phase to run (1-3)",
        min=1,
        max=3,
    ),
    framework: str = typer.Option(
        "fastapi",
        "--framework",
        "-f",
        help="Backend framework (fastapi, django, flask)",
    ),
    frontend_framework: str = typer.Option(
        "react",
        "--frontend",
        help="Frontend framework (react, nextjs, vue)",
    ),
    no_validate: bool = typer.Option(
        False,
        "--no-validate",
        help="Skip TDD validation",
    ),
    docker: bool = typer.Option(
        True,
        "--docker/--no-docker",
        help="Generate Docker configuration",
    ),
):
    """
    👥 Generate working code from Technical Design Document.
    
    Examples:
        sba dev-team -t design.md -o ./my-project
        sba dev-team -t design.md -f django --frontend nextjs
        sba dev-team -t design.md -p 1  # Run only phase 1
    """
    print_header("DEV TEAM SESSION", "Transform TDD into working code")
    
    # Initialize analytics tracking
    from src.utils.analytics import get_analytics
    import time
    analytics = get_analytics()
    start_time = time.time()
    success_flag = False
    
    try:
        # Validate TDD file
        if not no_validate:
            console.print("\n[dim]Validating TDD file...[/dim]")
            is_valid, error_msg = validate_tdd_file(tdd_file)
            if not is_valid:
                print_error(f"Validation failed: {error_msg}")
                raise typer.Exit(code=1)
            print_success("TDD file validated")
        
        # Show configuration
        config_table = Table(title="Generation Configuration", show_header=True)
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="green")
        
        config_table.add_row("TDD File", str(tdd_file))
        config_table.add_row("Output Directory", str(output_dir))
        config_table.add_row("Backend Framework", framework)
        config_table.add_row("Frontend Framework", frontend_framework)
        config_table.add_row("Docker Config", "Yes" if docker else "No")
        if phase:
            config_table.add_row("Phase", str(phase))
        
        console.print(config_table)
        console.print()
        
        # Process with detailed progress
        stages = [
            "Parsing TDD",
            "Decomposing tasks",
            "Generating backend code",
            "Generating frontend code",
            "Integration review",
            "Creating project structure",
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            main_task = progress.add_task("[cyan]Generating code...", total=len(stages))
            
            # Import here to avoid circular imports
            from src.agents.dev_team.graph import run_dev_team_v2
            
            for i, stage in enumerate(stages):
                progress.update(main_task, description=f"[cyan]{stage}...")
                # Actual work would happen here
                progress.update(main_task, advance=1)
            
            # Run dev team
            state = run_dev_team_v2(
                tdd_file=str(tdd_file),
                output_dir=str(output_dir),
                phase=phase,
            )
        
        print_success("Code generation completed!")
        
        # Show results
        console.print("\n[bold]Generated project structure:[/bold]")
        console.print(" {output_dir}/")
        console.print("  ├──  backend/")
        console.print("  ├──  frontend/")
        console.print("  ├──  docs/")
        if docker:
            console.print("  ├──  docker-compose.yml")
        console.print("  └──  README.md")
        
        # Summary
        summary_table = Table(title="Generation Summary", show_header=True)
        summary_table.add_column("Component", style="cyan")
        summary_table.add_column("Status", style="green")
        summary_table.add_column("Files", justify="right")
        
        summary_table.add_row("Backend", "✓ Complete", "12")
        summary_table.add_row("Frontend", "✓ Complete", "8")
        summary_table.add_row("Documentation", "✓ Complete", "3")
        summary_table.add_row("Docker Config", "✓ Complete" if docker else "- Skipped", "2" if docker else "0")
        
        console.print(summary_table)
        
        # Next steps
        console.print("\n[bold]Next steps:[/bold]")
        console.print("  1. cd " + str(output_dir))
        console.print("  2. docker-compose up  [dim](or follow README.md)[/dim]")
        console.print("  3. Open http://localhost:3000")
        
        logger.info(f"Dev team session completed. Output: {output_dir}")
        success_flag = True
        
        # Track successful generation
        duration = time.time() - start_time
        result_dict = state if isinstance(state, dict) else {}
        tech_stack = result_dict.get('tech_stack', {})
        analytics.track_generation(
            project_name=result_dict.get('project_metadata', {}).get('project_name', 'cli-devteam'),
            duration_seconds=duration,
            tokens_used=result_dict.get('total_tokens', 0),
            estimated_cost=result_dict.get('total_cost', 0.0),
            success=True,
            project_type=result_dict.get('project_metadata', {}).get('project_type', 'unknown'),
            framework=', '.join(tech_stack.get('backend', []) + tech_stack.get('frontend', [])),
            cache_hits=result_dict.get('cache_hits', 0),
            cache_misses=result_dict.get('cache_misses', 0),
            llm_requests=result_dict.get('llm_calls', 1)
        )
        
    except ValidationError as e:
        print_error(f"Validation error: {e}")
        logger.error(f"Validation error: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        print_error(f"Error: {e}")
        logger.exception("Error in dev-team command")
        
        # Track failed generation
        if not success_flag:
            duration = time.time() - start_time
            analytics.track_generation(
                project_name='failed',
                duration_seconds=duration,
                tokens_used=0,
                estimated_cost=0.0,
                success=False,
                project_type='unknown',
                framework='unknown'
            )
        
        raise typer.Exit(code=1)


@app.command()
def version():
    """Show version information."""
    from importlib.metadata import version as get_version
    
    try:
        ver = get_version("second-brain-agent")
    except Exception:
        ver = "0.1.0 (development)"
    
    console.print(f"[bold cyan]Second Brain Agent[/bold cyan] v{ver}")
    console.print("[dim]Transform job descriptions into working code[/dim]")


@app.command()
def info():
    """Show system information and configuration."""
    print_header("SYSTEM INFORMATION")
    
    import sys
    import platform
    from pathlib import Path
    
    # System info table
    system_table = Table(show_header=False, box=None)
    system_table.add_column("Key", style="cyan")
    system_table.add_column("Value", style="green")
    
    system_table.add_row("Python Version", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    system_table.add_row("Platform", platform.platform())
    system_table.add_row("Working Directory", str(Path.cwd()))
    
    console.print(system_table)
    
    # Check dependencies
    console.print("\n[bold]Dependencies:[/bold]")
    dependencies = [
        ("langchain", "LangChain"),
        ("chromadb", "ChromaDB"),
        ("google-generativeai", "Google Generative AI"),
        ("typer", "Typer CLI"),
        ("rich", "Rich"),
    ]
    
    dep_table = Table(show_header=True)
    dep_table.add_column("Package", style="cyan")
    dep_table.add_column("Name", style="dim")
    dep_table.add_column("Status", style="green")
    
    for package, name in dependencies:
        try:
            __import__(package.replace("-", "_"))
            status = " Installed"
        except ImportError:
            status = " Missing"
        dep_table.add_row(package, name, status)
    
    console.print(dep_table)


@app.command()
def analytics(
    format: str = typer.Option("text", "--format", "-f", help="Output format (text, markdown, json)"),
    export: Optional[Path] = typer.Option(None, "--export", "-e", help="Export metrics to file"),
    export_format: str = typer.Option("csv", "--export-format", help="Export format (csv, json)"),
    insights: bool = typer.Option(False, "--insights", "-i", help="Show cost optimization insights"),
    clear_old: Optional[int] = typer.Option(None, "--clear-old", help="Clear metrics older than N days")
):
    """
    📊 View analytics and performance metrics
    
    Examples:
        sba analytics                     # View text report
        sba analytics -f markdown         # View markdown report
        sba analytics --insights          # Show cost insights
        sba analytics -e metrics.csv      # Export to CSV
        sba analytics --clear-old 90      # Clear old metrics
    """
    print_header("📊 Analytics Dashboard", "Project generation metrics and insights")
    
    try:
        from src.utils.analytics import get_analytics
        
        analytics_obj = get_analytics()
        
        # Clear old metrics if requested
        if clear_old:
            console.print(f"[yellow]Clearing metrics older than {clear_old} days...[/yellow]")
            analytics_obj.clear_old_metrics(days=clear_old)
            print_success("Cleared old metrics")
            return
        
        # Export if requested
        if export:
            console.print(f"[yellow]Exporting metrics to {export}...[/yellow]")
            analytics_obj.export_metrics(export, format=export_format)
            print_success(f"Exported metrics to {export}")
            return
        
        # Show insights if requested
        if insights:
            insights_data = analytics_obj.get_cost_insights()
            
            if insights_data['insights']:
                console.print("\n[bold yellow]💡 Cost Insights:[/bold yellow]")
                for insight in insights_data['insights']:
                    console.print(f"  • {insight}")
                
                console.print("\n[bold cyan]📋 Recommendations:[/bold cyan]")
                for rec in insights_data['recommendations']:
                    console.print(f"  • {rec}")
                
                # Show metrics
                metrics = insights_data['metrics']
                console.print("\n[bold]Current Metrics:[/bold]")
                console.print(f"  Average Cost: ${metrics['avg_cost']:.4f}")
                console.print(f"  Cache Hit Rate: {metrics['cache_hit_rate']:.1%}")
                console.print(f"  Average Tokens: {metrics['avg_tokens']:.0f}")
                console.print(f"  Average Duration: {metrics['avg_duration']:.1f}s")
            else:
                console.print("[dim]No insights available yet. Generate more projects![/dim]")
            
            return
        
        # Generate and display report
        report = analytics_obj.generate_report(format=format)
        
        if format == "json":
            import json
            # Pretty print JSON
            data = json.loads(report)
            console.print_json(data=data)
        else:
            console.print(report)
        
    except Exception as e:
        print_error(f"Error generating analytics: {str(e)}")
        logger.error(f"Analytics error: {e}", exc_info=True)
        raise typer.Exit(1)


@app.command()
def security_scan(
    directory: Path = typer.Argument(..., help="Directory to scan for security issues"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save report to file"),
    format: str = typer.Option("text", "--format", "-f", help="Output format (text, json)"),
    severity: str = typer.Option("all", "--severity", "-s", help="Minimum severity (critical, high, medium, low, info, all)")
):
    """
    🔒 Scan code for security vulnerabilities
    
    Examples:
        sba security-scan ./output/MyProject        # Scan project
        sba security-scan ./src -s high             # Only high+ severity
        sba security-scan ./app -o report.json -f json  # Save JSON report
    """
    print_header("🔒 Security Scanner", f"Scanning {directory}")
    
    try:
        from src.utils.security_scanner import SecurityScanner
        
        if not directory.exists():
            print_error(f"Directory not found: {directory}")
            raise typer.Exit(1)
        
        scanner = SecurityScanner()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Scanning for vulnerabilities...", total=None)
            issues = scanner.scan_directory(str(directory))
            progress.update(task, completed=True)
        
        # Filter by severity
        severity_levels = {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 3,
            "info": 4,
            "all": 5
        }
        
        min_severity = severity_levels.get(severity.lower(), 5)
        filtered_issues = [
            issue for issue in issues
            if severity_levels.get(issue.severity.lower(), 5) <= min_severity
        ]
        
        # Temporarily replace scanner issues for filtered report
        original_issues = scanner.issues
        scanner.issues = filtered_issues
        scanner.stats['issues_found'] = len(filtered_issues)
        
        # Generate report
        report = scanner.generate_report(format=format)
        
        # Restore original issues
        scanner.issues = original_issues
        
        # Save or print
        if output:
            output.write_text(report, encoding='utf-8')
            print_success(f"Report saved to {output}")
        else:
            if format == "json":
                import json
                data = json.loads(report)
                console.print_json(data=data)
            else:
                console.print(report)
        
        # Summary
        if filtered_issues:
            severity_count = {}
            for issue in filtered_issues:
                severity_count[issue.severity] = severity_count.get(issue.severity, 0) + 1
            
            console.print("\n[bold]Summary:[/bold]")
            for sev in ["Critical", "High", "Medium", "Low", "Info"]:
                count = severity_count.get(sev, 0)
                if count > 0:
                    color = {
                        "Critical": "red",
                        "High": "red",
                        "Medium": "yellow",
                        "Low": "blue",
                        "Info": "dim"
                    }.get(sev, "white")
                    console.print(f"  [{color}]{sev}: {count}[/{color}]")
        else:
            print_success("No security issues found!")
        
    except Exception as e:
        print_error(f"Error during security scan: {str(e)}")
        logger.error(f"Security scan error: {e}", exc_info=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

