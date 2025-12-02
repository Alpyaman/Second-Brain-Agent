#!/usr/bin/env python
"""
Curator Agent CLI

Command-line interface for the Curator Agent, which automatically discovers, filters, and ingests high-quality codebases into your Second Brain collections.

Usage:
    # Discover and ingest repositories for both frontend and backend
    python curator.py

    # Discover only (no ingestion)
    python curator.py --discover-only

    # Target specific domains
    python curator.py --domains frontend backend

    # Use LLM to generate custom queries
    python curator.py --mode auto

    # Add custom search queries
    python curator.py --query "React server components site:github.com"

Examples:
    # Quick discovery for frontend repos
    python curator.py --domains frontend --discover-only

    # Full workflow with custom query
    python curator.py --query "FastAPI authentication template site:github.com"

    # LLM-generated queries for backend
    python curator.py --mode auto --domains backend
"""

import argparse
import sys
import traceback
from src.agents.curator.graph import run_curator_agent


def main():
    """CLI entry point for the Curator Agent."""

    parser = argparse.ArgumentParser(
        description="Curator Agent: Automated codebase discovery and ingestion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
            # Discover and ingest repositories (default: frontend + backend)
            python curator.py

            # Discovery only (no ingestion)
            python curator.py --discover-only

            # Target specific domains
            python curator.py --domains frontend backend fullstack

            # Use LLM to generate custom queries
            python curator.py --mode auto

            # Add custom search queries
            python curator.py --query "React server components site:github.com"

            # Quick frontend discovery
            python curator.py --domains frontend --discover-only

            Domains:
            - frontend:  React, Next.js, Vue, UI libraries, CSS frameworks
            - backend:   Python, FastAPI, Django, Node.js, API patterns
            - fullstack: Combined frontend/backend templates

            Modes:
            - manual: Use predefined high-quality queries (default, recommended)
            - auto:   Use LLM to generate custom queries (requires GOOGLE_API_KEY)
        """
    )

    parser.add_argument("--mode", type=str, choices=["manual", "auto"], default="manual", help="Query generation mode: 'manual' uses predefined queries, 'auto' uses LLM (default: manual)")

    parser.add_argument("--domains", type=str, nargs="+", choices=["frontend", "backend", "fullstack"], default=["frontend", "backend"], help="Domains to search (default: frontend backend)")

    parser.add_argument("--query", type=str, action="append", dest="queries", help="Add custom search query (can be used multiple times)")

    parser.add_argument("--max-results", type=int, default=5, help="Maximum results to process per query (default: 5)")

    parser.add_argument("--discover-only", action="store_true", help="Only discover and assess repos, don't ingest (useful for testing)")

    args = parser.parse_args()

    # Display configuration
    print("\n" + "=" * 70)
    print("CURATOR AGENT")
    print("=" * 70)
    print(f"Mode:              {args.mode}")
    print(f"Domains:           {', '.join(args.domains)}")
    print(f"Max Results:       {args.max_results}")
    print(f"Discover Only:     {args.discover_only}")

    if args.queries:
        print(f"Custom Queries:    {len(args.queries)}")
        for q in args.queries:
            print(f"  - {q}")

    print("=" * 70)

    # Confirmation prompt if ingestion is enabled
    if not args.discover_only:
        print("\nWARNING: Ingestion is ENABLED")
        print("   This will automatically clone and ingest approved repositories.")
        print("   This may take significant time and disk space.")
        response = input("\nProceed with ingestion? (y/N): ")

        if response.lower() not in ["y", "yes"]:
            print("\n✅ Switching to discovery-only mode")
            args.discover_only = True

    # Run the curator agent
    try:
        final_state = run_curator_agent(
            mode=args.mode,
            domains=args.domains,
            custom_queries=args.queries,
            max_results_per_query=args.max_results,
            skip_ingestion=args.discover_only,
        )

        # Display results
        print("\n" + "=" * 70)
        print("RESULTS")
        print("=" * 70)

        assessed = final_state.get("assessed_repositories", [])
        approved = final_state.get("approved_for_ingestion", [])

        if assessed:
            print("\nApproved Repositories:")
            for i, repo in enumerate(approved, 1):
                print(f"\n{i}. {repo['url']}")
                print(f"   Quality:      {repo['quality_score']}/10")
                print(f"   Category:     {repo['category']}")
                print(f"   Collection:   {repo['target_collection']}")
                print(f"   Technologies: {', '.join(repo['technologies'])}")

            print(f"\nFiltered Out: {len(assessed) - len(approved)} repositories")

        if not args.discover_only:
            ingestion_results = final_state.get("ingestion_results", [])
            if ingestion_results:
                success = sum(1 for r in ingestion_results if r["status"] == "success")
                print("\nIngestion Results:")
                print(f"   Successful: {success}/{len(ingestion_results)}")

                if success < len(ingestion_results):
                    print("\n   Failed ingestions:")
                    for r in ingestion_results:
                        if r["status"] != "success":
                            print(f"   - {r['url']}: {r['message'][:100]}")

        print("\n" + "=" * 70)
        print("Curator Agent completed successfully!")
        print("=" * 70)

    except KeyboardInterrupt:
        print("\n\nCurator Agent interrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"\nError running Curator Agent: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()