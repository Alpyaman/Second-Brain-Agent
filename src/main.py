"""
Second-Brain-Agent CLI

A command-line interface for your AI Chief of Staff agent.
Runs the morning briefing workflow and displays results.
"""

import sys
import argparse
import traceback

from graph import create_agent_graph
from tools.gmail import list_drafts


def print_banner():
    """Print the application banner."""
    print("=" * 70)
    print("Second Brain Agent: Your AI Chief of Staff")
    print("=" * 70, "\n")

def print_workflow_status():
    """Print workflow status information."""
    print("Running workflow:\n")
    print("1. Checking your Google Calendar...\n")
    print("2. Querying your knowledge base...\n")
    print("3. Generating your daily briefing...\n")
    print("4. Creating email drafts (if needed)...\n")
    print("-" * 70, "\n")

def run_morning_briefing(query: str = None) -> dict:
    """
    Run the morning briefing workflow.

    Args:
        query: Optional custom query (defaults to daily briefing)
    
    Returns:
        Final agent state with daily_plan
    """
    # Create the agent
    agent = create_agent_graph()

    # Initial state
    initial_state = {
        "user_query": query or "Give me my daily briefing for today",
        "calendar_events": "",
        "relevant_notes": "",
        "daily_plan": "",
        "messages": []
    }

    # Run the agent workflow
    final_state = agent.invoke(initial_state)

    return final_state

def display_briefing(briefing: str):
    """
    Display the daily briefing in a formatted way.

    Args:
        briefing: The daily briefing text
    """
    print("\n", "=" * 70)
    print("Your daily briefing")
    print("=" * 70, "\n")
    print(briefing)
    print("\n", "=" * 70, "\n")

def display_email_drafts():
    """Display information about created email drafts."""
    try:
        print("\nEmail Drafts Status")
        print("-" * 70)

        drafts = list_drafts(max_results=5)
        print(drafts)
        print("\nTip: Review and send drafts from Gmail: https://mail.google.com/mail/#drafts\n")

    except Exception as e:
        print(f"Could not list email drafts: {e}")
        print("(Gmail integration may not be set up)\n")

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Second-Brain-Agent: Your AI Chief of Staff",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        # Run default morning briefing
            python src/main.py

        # Custom query
            python src/main.py --query "What should I focus on this week?"

        # Skip email draft listing
            python src/main.py --no-emails
        """
    )

    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Custom query for the agent (default: daily briefing)"
    )

    parser.add_argument(
        "--no-emails",
        action="store_true",
        help="Skip listing email drafts"
    )

    parser.add_argument(
        "--brief",
        action="store_true",
        help="Brief mode: show only the briefing, no banners"
    )

    args = parser.parse_args()

    try:
        # Print banner unless in brief mode
        if not args.brief:
            print_banner()
            print_workflow_status()

        # Run the workflow
        final_state = run_morning_briefing(args.query)

        # Display the briefing
        briefing = final_state.get("daily_plan", "No briefing generated.")

        if args.brief:
            # Brief mode: just print the briefing
            print(briefing)
        else:
            # Full mode: formatted display
            display_briefing(briefing)

            # Show email drafts unless disabled
            if not args.no_emails:
                display_email_drafts()

        # Success
        return 0

    except KeyboardInterrupt:
        print("\n\nWorkflow interrupted by user.")
        return 130

    except Exception as e:
        print(f"\nError running workflow: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())