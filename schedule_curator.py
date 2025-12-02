"""
Curator Agent Scheduler

This script is designed to be run via cron jobs or task schedulers to automatically discover and ingest new high-quality repositories on a recurring basis.

Phase 3: Scheduling and Maintenance

Usage:
    # Run with default settings (discovery + ingestion)
    python schedule_curator.py

    # Discovery only
    python schedule_curator.py --discover-only

    # Force re-ingestion of all repos
    python schedule_curator.py --force-update

    # Target specific domains
    python schedule_curator.py --domains frontend backend

Example Cron Jobs:
    # Run daily at 2 AM
    0 2 * * * cd /path/to/Second-Brain-Agent && python schedule_curator.py >> logs/curator.log 2>&1

    # Run weekly on Sundays at 3 AM
    0 3 * * 0 cd /path/to/Second-Brain-Agent && python schedule_curator.py >> logs/curator.log 2>&1

    # Discovery only, every Monday at 1 AM
    0 1 * * 1 cd /path/to/Second-Brain-Agent && python schedule_curator.py --discover-only >> logs/curator_discovery.log 2>&1
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
import json

from src.agents.curator.graph import run_curator_agent


def log_message(message: str, log_file: Path = None):
    """Log a message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "a") as f:
            f.write(log_entry + "\n")


def main():
    """Main scheduler entry point."""
    parser = argparse.ArgumentParser(
        description="Curator Agent Scheduler - Automated repository discovery and ingestion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
            # Run with default settings
            python schedule_curator.py

            # Discovery only (no ingestion)
            python schedule_curator.py --discover-only

            # Force re-ingestion of all repositories
            python schedule_curator.py --force-update

            # Target specific domains
            python schedule_curator.py --domains frontend backend

            # Write results to JSON file
            python schedule_curator.py --output results.json

            Cron Examples:
            # Daily at 2 AM
            0 2 * * * cd /path/to/Second-Brain-Agent && python schedule_curator.py >> logs/curator.log 2>&1

            # Weekly on Sundays at 3 AM
            0 3 * * 0 cd /path/to/Second-Brain-Agent && python schedule_curator.py >> logs/curator.log 2>&1
        """
    )

    parser.add_argument("--mode", type=str, choices=["manual", "auto"], default="manual", help="Query generation mode (default: manual)")

    parser.add_argument("--domains", type=str, nargs="+", choices=["frontend", "backend", "fullstack"], default=["frontend", "backend"], help="Domains to search (default: frontend backend)")

    parser.add_argument("--max-results", type=int, default=5, help="Maximum results per query (default: 5)")

    parser.add_argument("--discover-only", action="store_true", help="Only discover, don't ingest")

    parser.add_argument("--force-update", action="store_true", help="Force re-ingestion even if repositories are up-to-date")

    parser.add_argument("--output", type=str, help="Write results to JSON file")

    parser.add_argument("--log-file", type=str, help="Path to log file")

    args = parser.parse_args()

    # Setup logging
    log_file = Path(args.log_file) if args.log_file else None

    log_message("=" * 70, log_file)
    log_message("CURATOR AGENT SCHEDULER STARTED", log_file)
    log_message("=" * 70, log_file)
    log_message(f"Mode: {args.mode}", log_file)
    log_message(f"Domains: {', '.join(args.domains)}", log_file)
    log_message(f"Max Results: {args.max_results}", log_file)
    log_message(f"Discover Only: {args.discover_only}", log_file)
    log_message(f"Force Update: {args.force_update}", log_file)
    log_message("=" * 70, log_file)

    try:
        # Run curator agent
        final_state = run_curator_agent(
            mode=args.mode,
            domains=args.domains,
            max_results_per_query=args.max_results,
            skip_ingestion=args.discover_only,
        )

        # Log results
        log_message("\n" + "=" * 70, log_file)
        log_message("CURATOR AGENT COMPLETED", log_file)
        log_message("=" * 70, log_file)

        assessed = final_state.get("assessed_repositories", [])
        approved = final_state.get("approved_for_ingestion", [])

        log_message(f"Repositories assessed: {len(assessed)}", log_file)
        log_message(f"Repositories approved: {len(approved)}", log_file)

        if not args.discover_only:
            ingestion_results = final_state.get("ingestion_results", [])
            success_count = sum(1 for r in ingestion_results if r["status"] == "success")
            skipped_count = sum(1 for r in ingestion_results if r.get("skipped", False))

            log_message(f"Repositories ingested: {success_count}", log_file)
            log_message(f"Repositories skipped (up-to-date): {skipped_count}", log_file)

            if success_count > 0:
                total_vectors = sum(
                    r.get("vectors_stored", 0)
                    for r in ingestion_results
                    if r["status"] == "success"
                )
                log_message(f"Total vectors stored: {total_vectors}", log_file)

        # Save results to JSON if requested
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w") as f:
                json.dump(final_state, f, indent=2, default=str)

            log_message(f"Results saved to: {output_path}", log_file)

        log_message("=" * 70, log_file)
        log_message("Scheduler completed successfully", log_file)

        return 0

    except Exception as e:
        log_message("=" * 70, log_file)
        log_message(f"ERROR: {str(e)}", log_file)
        log_message("=" * 70, log_file)

        import traceback
        traceback.print_exc()

        return 1


if __name__ == "__main__":
    sys.exit(main())