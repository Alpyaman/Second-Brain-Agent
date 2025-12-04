"""
Architect Session - Interactive Architectural Design Tool

This script provides an interactive session where you can:
1. Describe a high-level architectural goal
2. Get a design document based on your existing codebase and preferences
3. Provide feedback and iterate on the design

Usage:
    python architect.py
    python architect.py --goal "Build a real-time chat application"
"""

import os
import argparse
from pathlib import Path
from src.agents.architect.graph import run_architect_session
from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "codellama")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")

def print_section_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def print_design_document(design: str, iteration: int):
    """Print the design document with formatting."""
    print_section_header(f"ARCHITECTURAL DESIGN DOCUMENT (v{iteration})")
    print(design)
    print("\n" + "=" * 80)

def interactive_mode(is_job_description: bool = False):
    """Run an interactive architect session with multiple iterations."""
    if is_job_description:
        print_section_header("  ARCHITECT SESSION - Job Description Mode")
        print("Welcome to the Instant Consultant! Paste a job description from Upwork/Freelancer,")
        print("and I'll create a professional Technical Design Document for you.\n")
    else:
        print_section_header("  ARCHITECT SESSION - Interactive Mode")
        print("Welcome to Architect Session! I'll help you design your system based on")
        print("your existing codebase patterns and coding preferences.\n")

    # Get the input
    if is_job_description:
        print("Paste the job description below (press Enter, then Ctrl+D or Ctrl+Z to finish):")
        print()
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        goal = "\n".join(lines).strip()
    else:
        print("What would you like to build?")
        print("Example: 'Build a real-time chat application with WebSockets'")
        print()
        goal = input("Your Goal: ").strip()

    if not goal:
        print("No input provided. Exiting.")
        return

    # Run initial design generation
    print()
    if is_job_description:
        print_section_header("Analyzing Job Description & Generating Design")
    else:
        print_section_header("Generating Initial Design")

    state = run_architect_session(goal=goal, is_job_description=is_job_description)

    # Display the initial design
    print_design_document(state['design_document'], state['iteration_count'])

    # Iteration loop
    while True:
        print("\n" + "-" * 80)
        print("Options:")
        print("  1. Provide feedback and refine the design")
        print("  2. Save design to file")
        print("  3. Exit")
        print("-" * 80)

        choice = input("\nYour choice (1-3): ").strip()

        if choice == "1":
            # Get feedback
            print("\nProvide your feedback on the design:")
            print("Example: 'Make it more modular' or 'Use FastAPI instead of Flask'")
            print("(Press Enter twice to finish)")
            print()

            feedback_lines = []
            while True:
                line = input()
                if not line:
                    break
                feedback_lines.append(line)

            feedback = "\n".join(feedback_lines).strip()

            if not feedback:
                print("No feedback provided. Skipping refinement.")
                continue

            # Run refinement
            print()
            print_section_header("Refining Design Based on Feedback")

            state['feedback'] = feedback
            state = run_architect_session(goal=goal, feedback=feedback)

            # Display refined design
            print_design_document(state['design_document'], state['iteration_count'])

        elif choice == "2":
            # Save to file
            if is_job_description and state.get('project_title'):
                # Use project title for filename if available
                safe_title = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in state['project_title'])
                safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
                filename = f"TDD_{safe_title}_v{state['iteration_count']}.md"
            else:
                filename = f"design_document_{state['iteration_count']}.md"

            filepath = Path(filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                if is_job_description:
                    f.write("# Technical Design Document\n\n")
                    if state.get('project_title'):
                        f.write(f"**Project:** {state['project_title']}\n\n")
                else:
                    f.write("# Architectural Design Document\n\n")
                    f.write(f"**Goal:** {goal}\n\n")

                f.write(f"**Version:** {state['iteration_count']}\n")
                f.write(f"**Generated:** {Path.cwd()}\n\n")
                f.write("---\n\n")
                f.write(state['design_document'])

            print(f"\n✓ Design saved to: {filepath.absolute()}")
        elif choice == "3":
            print("\nExiting Architect Session. Happy building!")
            break

        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def single_run_mode(goal: str, is_job_description: bool = False):
    """Run a single architect session without interaction."""
    if is_job_description:
        print_section_header("  INSTANT CONSULTANT - Job Description Mode")
        print("Generating professional Technical Design Document from job posting...\n")
    else:
        print_section_header("  ARCHITECT SESSION - Single Run Mode")
        print(f"Goal: {goal}\n")

    # Run design generation
    state = run_architect_session(goal=goal, is_job_description=is_job_description)

    # Display the design
    print_design_document(state['design_document'], state['iteration_count'])

    # Offer to save
    print("\nSave this design to a file? (y/n): ", end="")
    save = input().strip().lower()

    if save == 'y':
        filename = "design_document.md"
        filepath = Path(filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("Architectural Design Document\n\n")
            f.write(f"**Goal:** {goal}\n\n")
            f.write("---\n\n")
            f.write(state['design_document'])

        print(f"Design saved to: {filepath.absolute()}")

def main():
    """Main entry point for the Architect Session CLI."""
    parser = argparse.ArgumentParser(
        description="Architect Session - Interactive Architectural Design Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        # Interactive mode (recommended)
        python architect.py

        # Single run with a goal
        python architect.py --goal "Build a REST API for a blog platform"

        # Job description mode (Instant Consultant)
        python architect.py --job-description --goal "$(cat job_posting.txt)"

        # Interactive job description mode
        python architect.py --job-description

        # Non-interactive mode
        python architect.py --goal "Build a real-time chat app" --no-interactive
        """
    )

    parser.add_argument("--goal", type=str, help="High-level architectural goal or job description text")

    parser.add_argument("--job-description", action="store_true", help="Enable job description mode (parses Upwork/Freelancer job postings)")

    parser.add_argument("--no-interactive", action="store_true", help="Run in non-interactive mode (single generation, no refinement)")

    args = parser.parse_args()

    # Check if ollama is configured
    print(f"Using Ollama model: {OLLAMA_MODEL}")
    print(f"Ollama base URL: {OLLAMA_BASE_URL}\n")

    # Determine mode
    if args.goal and args.no_interactive:
        # Single run mode
        single_run_mode(args.goal, is_job_description=args.job_description)

    elif args.goal:
        # Interactive mode with initial goal
        if args.job_description:
            print_section_header("  INSTANT CONSULTANT - Job Description Mode")
            print("Analyzing job posting and generating Technical Design Document...\n")
        else:
            print_section_header("  ARCHITECT SESSION")
            print(f"Initial Goal: {args.goal}\n")

        state = run_architect_session(goal=args.goal, is_job_description=args.job_description)
        print_design_document(state['design_document'], state['iteration_count'])

        # Continue with interactive refinement
        while True:
            print("\nProvide feedback to refine (or press Enter to finish): ")
            feedback = input().strip()

            if not feedback:
                print("Design complete!")
                break

            print()
            print_section_header("Refining Design")

            state['feedback'] = feedback
            state = run_architect_session(goal=args.goal, feedback=feedback, is_job_description=args.job_description)

            print_design_document(state['design_document'], state['iteration_count'])

    else:
        # Fully interactive mode
        interactive_mode(is_job_description=args.job_description)

if __name__ == "__main__":
    main()