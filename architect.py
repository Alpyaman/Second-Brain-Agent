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
import sys
from pathlib import Path
from src.agents.architect.graph import run_architect_session
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

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

def interactive_mode():
    """Run an interactive architect session with multiple iterations."""
    print_section_header("🏗️  ARCHITECT SESSION - Interactive Mode")

    print("Welcome to Architect Session! I'll help you design your system based on")
    print("your existing codebase patterns and coding preferences.\n")

    # Get the architectural goal
    print("What would you like to build?")
    print("Example: 'Build a real-time chat application with WebSockets'")
    print()
    goal = input("Your Goal: ").strip()

    if not goal:
        print("No goal provided. Exiting.")
        return

    # Run initial design generation
    print()
    print_section_header("Generating Initial Design")

    state = run_architect_session(goal=goal)

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
            filename = f"design_document_{state['iteration_count']}.md"
            filepath = Path(filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("Architectural Design Document\n\n")
                f.write(f"**Goal:** {goal}\n\n")
                f.write(f"**Version:** {state['iteration_count']}\n\n")
                f.write("---\n\n")
                f.write(state['design_document'])

            print(f"\nDesign saved to: {filepath.absolute()}")
        elif choice == "3":
            print("\nExiting Architect Session. Happy building!")
            break

        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def single_run_mode(goal: str):
    """Run a single architect session without interaction."""
    print_section_header("🏗️  ARCHITECT SESSION - Single Run Mode")

    print(f"Goal: {goal}\n")

    # Run design generation
    state = run_architect_session(goal=goal)

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

        # Non-interactive mode
        python architect.py --goal "Build a real-time chat app" --no-interactive
        """
    )

    parser.add_argument("--goal", type=str, help="High-level architectural goal (e.g., 'Build a real-time chat application')")

    parser.add_argument("--no-interactive", action="store_true", help="Run in non-interactive mode (single generation, no refinement)")

    args = parser.parse_args()

    # Check if API key is set
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY is not set.")
        print("Please add it to your .env file to use Architect Session.")
        sys.exit(1)

    # Determine mode
    if args.goal and args.no_interactive:
        # Single run mode
        single_run_mode(args.goal)
    elif args.goal:
        # Interactive mode with initial goal
        print_section_header("🏗️  ARCHITECT SESSION")
        print(f"Initial Goal: {args.goal}\n")

        state = run_architect_session(goal=args.goal)
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
            state = run_architect_session(goal=args.goal, feedback=feedback)

            print_design_document(state['design_document'], state['iteration_count'])

    else:
        # Fully interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()