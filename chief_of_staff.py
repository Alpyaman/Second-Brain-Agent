"""
Chief of Staff Agent - Your AI Executive Assistant

This script provides intelligent daily briefings by combining:
- Google Calendar events
- Knowledge base context from your notes
- Cross-agent trigger detection (automatic coordination)

Usage:
    python chief_of_staff.py
    python chief_of_staff.py --query "What's on my schedule today?"

The Chief of Staff will:
1. Check your Google Calendar for today's events
2. Detect patterns that trigger other agents (e.g., "Project Kickoff" → trigger Architect)
3. Query your knowledge base for relevant context
4. Execute auto-triggers (low-risk actions)
5. Generate a personalized daily briefing with action items
"""

import os
import sys
import argparse
from pathlib import Path
from src.agents.chief_of_staff.graph import create_agent_graph
from dotenv import load_dotenv
import traceback

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def print_section_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def main():
    """Run the Chief of Staff agent."""
    parser = argparse.ArgumentParser(
        description="Chief of Staff Agent - Daily Briefings with Cross-Agent Triggers"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="Give me my daily briefing for today",
        help="Your query or request (default: daily briefing)"
    )
    parser.add_argument(
        "--no-triggers",
        action="store_true",
        help="Disable cross-agent trigger detection"
    )
    
    args = parser.parse_args()
    
    print_section_header("Chief of Staff Agent - Your AI Executive Assistant")
    
    if not GOOGLE_API_KEY:
        print("\n⚠️  Warning: GOOGLE_API_KEY not set in .env file")
        print("   Some features may not work (calendar integration, LLM generation)")
        print("   Get your API key from: https://aistudio.google.com/app/apikey\n")
    
    print("\n🧠 This agent will:")
    print("  1. Check your Google Calendar for today's events")
    print("  2. Detect patterns for cross-agent triggers (e.g., 'Project Kickoff')")
    print("  3. Query your knowledge base for relevant context")
    print("  4. Execute auto-triggers for low-risk actions")
    print("  5. Generate a personalized daily briefing")
    
    if args.no_triggers:
        print("\n⚠️  Cross-agent triggers disabled (--no-triggers flag)")
    
    print_section_header("Starting Agent Workflow")
    
    try:
        # Create the agent
        agent = create_agent_graph()
        
        # Initial state
        initial_state = {
            "user_query": args.query,
            "calendar_events": "",
            "relevant_notes": "",
            "daily_plan": "",
            "triggered_actions": [] if not args.no_triggers else None,
            "messages": []
        }
        
        print(f"\n💬 Query: {args.query}\n")
        
        # Run the agent
        final_state = agent.invoke(initial_state)
        
        # Display the result
        print_section_header("📋 YOUR DAILY BRIEFING")
        print("\n" + final_state["daily_plan"])
        
        # Display triggered actions if any
        if not args.no_triggers and final_state.get("triggered_actions"):
            triggered = final_state["triggered_actions"]
            print_section_header(f"🔔 Triggered Actions ({len(triggered)} detected)")
            
            for i, action in enumerate(triggered, 1):
                print(f"\n[{i}] {action['event_title']}")
                print(f"    → Agent: {action['target_agent']}")
                print(f"    → Action: {action['action']}")
                print(f"    → Suggestion: {action['suggestion']}")
                print(f"    → Priority: {action['priority']}")
                
                if action.get('auto_execute'):
                    print("    ✅ Auto-executed")
                else:
                    print("    ⏸️  Queued for approval")
            
            print("\n💡 Tip: Check queued triggers with:")
            print("   python -c \"from src.tools.agent_triggers import get_queued_triggers; print(get_queued_triggers())\"")
        
        print("\n" + "=" * 80)
        print("✅ Briefing complete!")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print_section_header("❌ Error Running Agent")
        print(f"\n{e}")
        print("\nTraceback:")
        traceback.print_exc()
        print("\n" + "=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
