"""
Freelance Workflow - Rapid Proposal Generator

This script helps you respond to Upwork/Freelancer job postings faster
by generating technical proposals, architecture plans, and time estimates.

Usage:
    python freelance_workflow.py --job "path/to/job_description.txt"
"""

import sys
from pathlib import Path
import time
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

logger = get_logger(__name__)
console = Console()


class FreelanceProposalGenerator:
    """Generate compelling technical proposals for freelance jobs."""
    
    def __init__(self):
        self.console = Console()
    
    def generate_proposal(self, job_description: str, client_name: str = "Client") -> dict:
        """
        Generate a complete proposal package including:
        - Technical approach
        - Time estimate
        - Cost breakdown
        - Risk assessment
        - Portfolio examples
        """
        from src.agents.architect.graph import run_architect_graph
        
        console.print("\n[bold cyan]🚀 Generating Freelance Proposal...[/bold cyan]\n")
        
        # Step 1: Generate Technical Design Document
        console.print("📋 Step 1: Analyzing requirements...")
        start_time = time.time()
        
        tdd = run_architect_graph(job_description)
        
        console.print(f"✓ Technical analysis complete ({time.time() - start_time:.1f}s)\n")
        
        # Step 2: Extract key information for proposal
        console.print("📊 Step 2: Creating project breakdown...")
        
        proposal = self._create_proposal_structure(tdd, job_description, client_name)
        
        console.print("✓ Proposal structure created\n")
        
        # Step 3: Generate time and cost estimates
        console.print("💰 Step 3: Calculating estimates...")
        
        estimates = self._calculate_estimates(tdd)
        proposal.update(estimates)
        
        console.print("✓ Estimates calculated\n")
        
        return proposal
    
    def _create_proposal_structure(self, tdd: dict, job_desc: str, client_name: str) -> dict:
        """Create proposal structure from TDD."""
        
        # Extract components from TDD
        design_doc = tdd.get('design_document', '')
        
        return {
            'client_name': client_name,
            'job_description': job_desc,
            'technical_approach': design_doc,
            'generated_at': datetime.now().isoformat(),
        }
    
    def _calculate_estimates(self, tdd: dict) -> dict:
        """Calculate time and cost estimates based on project complexity."""
        
        # Analyze complexity
        design_doc = tdd.get('design_document', '')
        
        # Count components (rough heuristic)
        components = len([line for line in design_doc.split('\n') if '##' in line or '###' in line])
        
        # Estimate based on complexity
        if components < 5:
            complexity = "Low"
            min_hours = 20
            max_hours = 40
        elif components < 10:
            complexity = "Medium"
            min_hours = 40
            max_hours = 80
        else:
            complexity = "High"
            min_hours = 80
            max_hours = 160
        
        # Calculate timeline
        hours_per_day = 6  # Assuming part-time freelancing
        min_days = min_hours / hours_per_day
        max_days = max_hours / hours_per_day
        
        min_weeks = min_days / 5
        max_weeks = max_days / 5
        
        # Calculate dates
        start_date = datetime.now()
        min_completion = start_date + timedelta(days=min_days)
        max_completion = start_date + timedelta(days=max_days)
        
        return {
            'complexity': complexity,
            'estimated_hours_min': min_hours,
            'estimated_hours_max': max_hours,
            'estimated_weeks_min': round(min_weeks, 1),
            'estimated_weeks_max': round(max_weeks, 1),
            'earliest_completion': min_completion.strftime('%Y-%m-%d'),
            'latest_completion': max_completion.strftime('%Y-%m-%d'),
            'milestones': self._generate_milestones(min_weeks, max_weeks),
        }
    
    def _generate_milestones(self, min_weeks: float, max_weeks: float) -> list:
        """Generate project milestones."""
        avg_weeks = (min_weeks + max_weeks) / 2
        
        if avg_weeks <= 2:
            return [
                {"name": "Week 1", "deliverable": "Core functionality + basic UI", "percentage": 70},
                {"name": "Week 2", "deliverable": "Testing, documentation, deployment", "percentage": 30},
            ]
        elif avg_weeks <= 4:
            return [
                {"name": "Week 1-2", "deliverable": "Backend API + Database", "percentage": 40},
                {"name": "Week 3", "deliverable": "Frontend + Integration", "percentage": 40},
                {"name": "Week 4", "deliverable": "Testing + Deployment", "percentage": 20},
            ]
        else:
            return [
                {"name": "Week 1-2", "deliverable": "Architecture + Core Backend", "percentage": 30},
                {"name": "Week 3-4", "deliverable": "API Development", "percentage": 30},
                {"name": "Week 5-6", "deliverable": "Frontend Development", "percentage": 25},
                {"name": "Week 7+", "deliverable": "Testing, QA, Deployment", "percentage": 15},
            ]
    
    def display_proposal(self, proposal: dict):
        """Display proposal in terminal with rich formatting."""
        
        console.print("\n")
        console.print(Panel.fit(
            "[bold green]✓ PROPOSAL GENERATED SUCCESSFULLY[/bold green]",
            border_style="green"
        ))
        console.print("\n")
        
        # Summary Table
        table = Table(title="📊 Project Summary", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Complexity", proposal['complexity'])
        table.add_row("Estimated Hours", f"{proposal['estimated_hours_min']}-{proposal['estimated_hours_max']} hours")
        table.add_row("Estimated Timeline", f"{proposal['estimated_weeks_min']}-{proposal['estimated_weeks_max']} weeks")
        table.add_row("Earliest Completion", proposal['earliest_completion'])
        table.add_row("Latest Completion", proposal['latest_completion'])
        
        console.print(table)
        console.print("\n")
        
        # Milestones
        milestone_table = Table(title="🎯 Project Milestones", show_header=True, header_style="bold cyan")
        milestone_table.add_column("Phase", style="cyan")
        milestone_table.add_column("Deliverable", style="white")
        milestone_table.add_column("% of Project", justify="right", style="green")
        
        for milestone in proposal['milestones']:
            milestone_table.add_row(
                milestone['name'],
                milestone['deliverable'],
                f"{milestone['percentage']}%"
            )
        
        console.print(milestone_table)
        console.print("\n")
    
    def save_proposal(self, proposal: dict, output_dir: Path = None):
        """Save proposal to markdown file."""
        
        if output_dir is None:
            output_dir = Path("proposals")
        
        output_dir.mkdir(exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"proposal_{timestamp}.md"
        filepath = output_dir / filename
        
        # Generate markdown content
        content = self._generate_proposal_markdown(proposal)
        
        filepath.write_text(content, encoding='utf-8')
        
        console.print(f"[bold green]✓[/bold green] Proposal saved to: [cyan]{filepath}[/cyan]")
        
        return filepath
    
    def _generate_proposal_markdown(self, proposal: dict) -> str:
        """Generate proposal in markdown format."""
        
        md = f"""# Technical Proposal

**Generated:** {proposal['generated_at']}
**Client:** {proposal['client_name']}

---

## Executive Summary

I am excited to submit my proposal for your project. After analyzing your requirements, I have developed a comprehensive technical approach that will deliver a robust, scalable solution.

**Project Timeline:** {proposal['estimated_weeks_min']}-{proposal['estimated_weeks_max']} weeks
**Estimated Effort:** {proposal['estimated_hours_min']}-{proposal['estimated_hours_max']} hours
**Complexity Level:** {proposal['complexity']}

---

## Technical Approach

{proposal['technical_approach']}

---

## Project Milestones & Deliverables

"""
        
        for milestone in proposal['milestones']:
            md += f"### {milestone['name']} ({milestone['percentage']}% of project)\n"
            md += f"**Deliverable:** {milestone['deliverable']}\n\n"
        
        md += f"""---

## Timeline

- **Start Date:** As soon as hired
- **Earliest Completion:** {proposal['earliest_completion']}
- **Latest Completion:** {proposal['latest_completion']}

---

## Why Choose Me?

✅ **Technical Expertise:** Full-stack development with modern frameworks
✅ **AI-Assisted Development:** Leveraging cutting-edge AI tools for faster delivery
✅ **Quality Assurance:** Comprehensive testing and documentation
✅ **Clear Communication:** Regular updates and transparent progress tracking
✅ **Production-Ready Code:** Clean, maintainable, and scalable architecture

---

## Next Steps

1. Schedule a brief call to discuss requirements in detail
2. Finalize scope and timeline
3. Begin development immediately upon agreement
4. Deliver milestones on schedule with regular progress updates

I'm ready to start immediately and deliver a high-quality solution that exceeds your expectations.

Looking forward to working together!
"""
        
        return md


def main():
    """Main entry point for freelance workflow."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate freelance proposals quickly")
    parser.add_argument("--job", "-j", required=True, help="Path to job description file")
    parser.add_argument("--client", "-c", default="Client", help="Client name")
    parser.add_argument("--output", "-o", default="proposals", help="Output directory")
    
    args = parser.parse_args()
    
    # Read job description
    job_file = Path(args.job)
    if not job_file.exists():
        console.print(f"[red]Error: Job file not found: {job_file}[/red]")
        sys.exit(1)
    
    job_description = job_file.read_text(encoding='utf-8')
    
    # Generate proposal
    generator = FreelanceProposalGenerator()
    proposal = generator.generate_proposal(job_description, args.client)
    
    # Display proposal
    generator.display_proposal(proposal)
    
    # Save proposal
    output_dir = Path(args.output)
    generator.save_proposal(proposal, output_dir)
    
    console.print("\n[bold cyan]💡 Pro Tips:[/bold cyan]")
    console.print("  1. Customize the saved proposal with your personal touch")
    console.print("  2. Add relevant portfolio examples")
    console.print("  3. Adjust pricing based on your hourly rate")
    console.print("  4. Copy the technical approach to show expertise")
    console.print("  5. Use the timeline to set realistic expectations\n")


if __name__ == "__main__":
    main()
