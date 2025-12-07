"""
Chief of Staff Agent - Main Entry Point

This script demonstrates the full Chief of Staff agent workflow, combining calendar
awareness with knowledge base context to provide intelligent daily briefings.
"""

import sys
from pathlib import Path
import traceback

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.chief_of_staff.graph import create_agent_graph

def main():
    """Run the Chief of Staff agent."""
    print("=" * 70)
    print("Chief of Staff Agent - Your AI Executive Assistant")
    print("=" * 70,"\n")
    print("This agent will:")
    print("  1. Check your Google Calendar for today's events")
    print("  2. Query your knowledge base for relevant context")
    print("  3. Generate a personalized daily briefing\n")
    print("=" * 70,"\n")

    # Get user query (or use default)
    user_input = input("What would you like to know? (press Enter for daily briefing): ").strip()

    if not user_input:
        user_input = "Give me my daily briefing for today"

    print("\nStarting agent workflow...\n")

    # Create the agent
    agent = create_agent_graph()

    # Initial state
    initial_state = {
        "user_query": user_input,
        "calendar_events": "",
        "relevant_notes": "",
        "daily_plan": "",
        "triggered_actions": [],
        "messages": []
    }

    try:
        # Run the agent
        final_state = agent.invoke(initial_state)

        # Display the result
        print("\n","=" * 70)
        print("📋 YOUR DAILY BRIEFING")
        print("=" * 70,"\n")
        print(final_state["daily_plan"])
        print("\n","=" * 70)

    except Exception as e:
        print(f"\nError running agent: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()