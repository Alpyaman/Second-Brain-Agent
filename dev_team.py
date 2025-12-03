#!/usr/bin/env python3
"""
Multi-Agent Development Team CLI

This CLI launches a software development team where each agent has:
- DISTINCT DATA: Specialized RAG collections (frontend_brain, backend_brain)
- DISTINCT CAPABILITIES: Domain-specific tools and expertise

This is NOT "just wrapping an LLM" - each agent learns from different codebases.

Usage:
    python dev_team.py
    python dev_team.py --feature "Build a user authentication system"
    python dev_team.py --feature "Create a REST API for blog posts" --output code/
"""

import argparse
import traceback
from pathlib import Path
from src.agents.dev_team.graph import run_dev_team
from core.confing import CHROMA_DB_DIR


def check_expert_brains():
    """
    Check if expert brains are initialized.
    Returns (frontend_ready, backend_ready)
    """
    chroma_path = Path(CHROMA_DB_DIR)

    if not chroma_path.exists():
        return False, False

    # Check for collections (basic check)
    # In production, you'd query the collections properly
    return True, True  # Simplified for now


def save_output(state: dict, output_dir: Path):
    """
    Save generated code to files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save frontend code
    frontend_file = output_dir / "frontend_implementation.md"
    with open(frontend_file, "w") as f:
        f.write("# Frontend Implementation\n\n")
        f.write("## Tasks\n\n")
        for task in state['frontend_tasks']:
            f.write(f"- {task}\n")
        f.write("\n## Generated Code\n\n")
        f.write(state['frontend_code'])

    # Save backend code
    backend_file = output_dir / "backend_implementation.md"
    with open(backend_file, "w") as f:
        f.write("# Backend Implementation\n\n")
        f.write("## Tasks\n\n")
        for task in state['backend_tasks']:
            f.write(f"- {task}\n")
        f.write("\n## Generated Code\n\n")
        f.write(state['backend_code'])

    # Save integration review
    review_file = output_dir / "integration_review.md"
    with open(review_file, "w") as f:
        f.write("# Integration Review\n\n")
        f.write(f"**Status**: {state['review_status']}\n\n")
        f.write("## Issues Found\n\n")
        if state['issues_found']:
            for issue in state['issues_found']:
                f.write(f"- {issue}\n")
        else:
            f.write("No issues found!\n")
        f.write("\n## Full Review\n\n")
        f.write(state['integration_review'])

    print(f"\n Output saved to: {output_dir.absolute()}")
    print(f"   - {frontend_file.name}")
    print(f"   - {backend_file.name}")
    print(f"   - {review_file.name}")


def interactive_mode():
    """
    Run interactive development session.
    """
    print("\n" + "=" * 70)
    print(" MULTI-AGENT SOFTWARE DEVELOPMENT TEAM")
    print("=" * 70)
    print("\nEach agent has:")
    print("   DISTINCT DATA: Queries specialized brain (frontend_brain, backend_brain)")
    print("   DISTINCT CAPABILITIES: Domain-specific tools and patterns")
    print("\nThis is NOT 'just wrapping an LLM'!\n")

    # Check if brains are ready
    frontend_ready, backend_ready = check_expert_brains()

    if not frontend_ready and not backend_ready:
        print("  WARNING: Expert brains not initialized")
        print("\n To get the full experience, ingest expert knowledge:")
        print("\n   Frontend Brain:")
        print("   python src/ingest_expert.py --expert frontend --list")
        print("\n   Backend Brain:")
        print("   python src/ingest_expert.py --expert backend --list")
        print("\nContinuing anyway (agents will work with limited context)...\n")

    # Get feature request
    print("=" * 70)
    print("What feature would you like to build?")
    print("=" * 70)
    print("\nExamples:")
    print("  - Build a user authentication system with JWT tokens")
    print("  - Create a blog API with posts, comments, and likes")
    print("  - Build a real-time chat application with WebSockets")
    print("  - Create a task management system with drag-and-drop")
    print()

    feature_request = input("Your feature request: ").strip()

    if not feature_request:
        print("No feature provided. Exiting.")
        return

    # Run the development team
    print("\n Launching development team...\n")

    try:
        result = run_dev_team(feature_request)

        # Display summary
        print("\n" + "=" * 70)
        print("DEVELOPMENT COMPLETE")
        print("=" * 70)

        print("\n Frontend Implementation:")
        print(f"   Tasks Completed: {len(result['frontend_tasks'])}")
        print(f"   Code Generated: {len(result['frontend_code'])} characters")

        print("\n Backend Implementation:")
        print(f"   Tasks Completed: {len(result['backend_tasks'])}")
        print(f"   Code Generated: {len(result['backend_code'])} characters")

        print("\n Integration Review:")
        print(f"   Status: {result['review_status'].upper()}")
        print(f"   Issues Found: {len(result['issues_found'])}")

        if result['issues_found']:
            print("\n   Issues:")
            for i, issue in enumerate(result['issues_found'][:5], 1):
                print(f"   {i}. {issue}")

        # Ask if user wants to save
        print("\n" + "=" * 70)
        save = input("\nSave output to files? (y/n): ").strip().lower()

        if save == 'y':
            output_dir = Path(input("Output directory [./dev_output]: ").strip() or "./dev_output")
            save_output(result, output_dir)

        print("\nSession complete!")
        print("=" * 70)

    except Exception as e:
        print(f"\nError: {e}")
        traceback.print_exc()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Software Development Team",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
            # Interactive mode
            python dev_team.py

            # Single feature mode
            python dev_team.py --feature "Build a user authentication system"

            # With output directory
            python dev_team.py --feature "Create a blog API" --output ./my_project/

            Expert Brains:
            Before running, it's recommended to ingest expert knowledge:

            Frontend: python src/ingest_expert.py --expert frontend --list
            Backend:  python src/ingest_expert.py --expert backend --list
        """
    )

    parser.add_argument("--feature", type=str, help="Feature request to implement")

    parser.add_argument("--output", type=str, help="Output directory for generated code")

    args = parser.parse_args()

    # Single feature mode
    if args.feature:
        print("\n" + "=" * 70)
        print("MULTI-AGENT SOFTWARE DEVELOPMENT TEAM")
        print("=" * 70)
        print(f"\nFeature: {args.feature}\n")

        result = run_dev_team(args.feature)

        print("\n" + "=" * 70)
        print("DEVELOPMENT COMPLETE")
        print("=" * 70)
        print(f"\nReview Status: {result['review_status'].upper()}")
        print(f"Issues Found: {len(result['issues_found'])}")

        if args.output:
            output_dir = Path(args.output)
            save_output(result, output_dir)
        else:
            print("\nUse --output to save generated code to files")

        return

    # Interactive mode
    interactive_mode()


if __name__ == "__main__":
    main()