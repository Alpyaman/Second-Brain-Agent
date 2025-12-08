#!/usr/bin/env python3
"""
Multi-Agent Development Team CLI

This CLI launches a software development team where each agent has:
- DISTINCT DATA: Specialized RAG collections (frontend_brain, backend_brain)
- DISTINCT CAPABILITIES: Domain-specific tools and expertise

This is NOT "just wrapping an LLM" - each agent learns from different codebases.

Usage:
    # Original workflow (Phase 1)
    python dev_team.py
    python dev_team.py --feature "Build a user authentication system"
    python dev_team.py --feature "Create a REST API for blog posts" --output code/

    # Phase 2: TDD to Code workflow
    python dev_team.py --tdd-file design.md --output-dir ./mvp
    python dev_team.py --tdd-file design.md --output-dir ./mvp --phase 1
"""

import argparse
import traceback
import time
from pathlib import Path
from src.agents.dev_team.graph import run_dev_team, run_dev_team_v2
from src.core.config import CHROMA_DB_DIR
from src.utils.analytics import get_analytics

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
        description="Multi-Agent Software Development Team (Phase 1 + Phase 2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:

        # PHASE 1: Original workflow (markdown output)
        python dev_team.py
        python dev_team.py --feature "Build a user authentication system"
        python dev_team.py --feature "Create a blog API" --output ./my_project/

        # PHASE 2: TDD to Code workflow (actual files)
        python dev_team.py --tdd-file design.md --output-dir ./mvp
        python dev_team.py --tdd-file design.md --output-dir ./mvp --phase 1

        # Complete pipeline (Phase 1 → Phase 2)
        python architect.py --job-description --goal "$(cat job.txt)" > tdd.md
        python dev_team.py --tdd-file tdd.md --output-dir ./prototype

        Expert Brains (Optional):
        For better code generation, ingest expert knowledge:

        Frontend: python src/ingest_expert.py --expert frontend --list
        Backend:  python src/ingest_expert.py --expert backend --list
        """
    )

    # Phase 1 arguments
    parser.add_argument("--feature", type=str, help="Feature request to implement (Phase 1)")

    parser.add_argument("--output", type=str, help="Output directory for markdown files (Phase 1)")

    # Phase 2 arguments
    parser.add_argument("--tdd-file", type=str, help="Path to Technical Design Document from Phase 1 (Phase 2)")

    parser.add_argument("--output-dir", type=str, help="Output directory for generated code files (Phase 2)")

    parser.add_argument("--phase", type=int, choices=[1, 2, 3], default=1, help="Implementation phase to generate (Phase 2): 1=MVP, 2=Extended, 3=Polish")

    args = parser.parse_args()

    # PHASE 2: TDD to Code workflow
    if args.tdd_file:
        print("\n" + "=" * 70)
        print("PHASE 2: RAPID PROTOTYPER - TDD to Code")
        print("=" * 70)
        print(f"\nTDD File: {args.tdd_file}")
        print(f"Implementation Phase: {args.phase}")
        print(f"Output Directory: {args.output_dir or './generated_project'}\n")

        try:
            # Read TDD file
            tdd_path = Path(args.tdd_file)
            if not tdd_path.exists():
                print(f"Error: TDD file not found: {args.tdd_file}")
                return

            with open(tdd_path, 'r', encoding='utf-8') as f:
                tdd_content = f.read()

            print("Launching Phase 2 development team...\n")

            # Track analytics
            analytics = get_analytics()
            start_time = time.time()
            
            try:
                # Run Phase 2 workflow
                result = run_dev_team_v2(
                    tdd_content=tdd_content,
                    implementation_phase=args.phase,
                    output_directory=args.output_dir or './generated_project'
                )
                
                # Track successful generation
                duration = time.time() - start_time
                tech_stack = result.get('tech_stack', {})
                analytics.track_generation(
                    project_name=result.get('project_metadata', {}).get('project_name', 'unknown'),
                    duration_seconds=duration,
                    tokens_used=result.get('total_tokens', 0),
                    estimated_cost=result.get('total_cost', 0.0),
                    success=True,
                    project_type=result.get('project_metadata', {}).get('project_type', 'unknown'),
                    framework=', '.join(tech_stack.get('backend', []) + tech_stack.get('frontend', [])),
                    cache_hits=result.get('cache_hits', 0),
                    cache_misses=result.get('cache_misses', 0),
                    llm_requests=result.get('llm_calls', 1)
                )
            except Exception as e:
                # Track failed generation
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
                raise

            # Display summary
            print("\n" + "=" * 70)
            print("PHASE 2: CODE GENERATION COMPLETE")
            print("=" * 70)

            if result.get('project_metadata'):
                print(f"\nProject: {result['project_metadata'].get('project_name', 'N/A')}")

            if result.get('tech_stack'):
                print("\nTech Stack:")
                for category, technologies in result['tech_stack'].items():
                    if technologies:
                        print(f"  {category.title()}: {', '.join(technologies)}")

            print(f"\nGenerated Files: {result.get('files_written', 0)}")
            print(f"Output Directory: {result.get('output_directory', 'N/A')}")

            if result.get('config_files'):
                print("\nConfiguration Files:")
                for filename in result['config_files'].keys():
                    print(f"  ✓ {filename}")

            print(f"\nIntegration Review: {result.get('review_status', 'N/A').upper()}")
            if result.get('issues_found'):
                print(f"Issues Found: {len(result['issues_found'])}")
                for i, issue in enumerate(result['issues_found'][:3], 1):
                    print(f"  {i}. {issue}")
 
            print("\n" + "=" * 70)
            print("✅ PROJECT READY!")
            print("=" * 70)
            print("\nNext steps:")
            print(f"  1. cd {result.get('output_directory', './generated_project')}")
            print("  2. Review the generated code")
            print("  3. Install dependencies (npm install / pip install -r requirements.txt)")
            print("  4. Run the project (docker-compose up / npm run dev)")
            print()

        except Exception as e:
            print(f"\nError in Phase 2 workflow: {e}")
            traceback.print_exc()

        return

    # PHASE 1: Original workflow
    if args.feature:
        print("\n" + "=" * 70)
        print("PHASE 1: MULTI-AGENT SOFTWARE DEVELOPMENT TEAM")
        print("=" * 70)
        print(f"\nFeature: {args.feature}\n")

        # Track analytics
        analytics = get_analytics()
        start_time = time.time()
        
        try:
            result = run_dev_team(args.feature)
            
            # Track successful generation
            duration = time.time() - start_time
            analytics.track_generation(
                project_name=args.feature[:50],
                duration_seconds=duration,
                tokens_used=result.get('total_tokens', 0),
                estimated_cost=result.get('total_cost', 0.0),
                success=result.get('review_status') != 'rejected',
                project_type='feature',
                framework='phase1',
                cache_hits=result.get('cache_hits', 0),
                cache_misses=result.get('cache_misses', 0),
                llm_requests=result.get('llm_calls', 1)
            )
        except Exception as e:
            # Track failed generation
            duration = time.time() - start_time
            analytics.track_generation(
                project_name=args.feature[:50],
                duration_seconds=duration,
                tokens_used=0,
                estimated_cost=0.0,
                success=False,
                project_type='feature',
                framework='phase1'
            )
            raise

        print("\n" + "=" * 70)
        print("DEVELOPMENT COMPLETE")
        print("=" * 70)
        print(f"\nReview Status: {result['review_status'].upper()}")
        print(f"Issues Found: {len(result['issues_found'])}")

        if args.output:
            output_dir = Path(args.output)
            save_output(result, output_dir)
        else:
            print("\nUse --output to save generated code to markdown files")

        return

    # Interactive mode (Phase 1)
    interactive_mode()


if __name__ == "__main__":
    main()