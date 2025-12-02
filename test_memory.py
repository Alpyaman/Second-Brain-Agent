"""
Test script for the long-term memory system.

This script demonstrates saving and retrieving user preferences
that are automatically injected into all queries.
"""

from src.tools.memory import (save_preference, list_preferences, get_all_preferences, clear_preferences)
from src.core.brain import query_second_brain

def main():
    print("=" * 70)
    print("Long-Term Memory System Test")
    print("=" * 70)
    print()

    # Clear any existing preferences for a clean test
    print("Clearing existing preferences...")
    clear_preferences()
    print()

    # Save some test preferences
    print("Saving test preferences...")
    print("-" * 70)

    save_preference('coding_style', 'Prefer functional programming over OOP')
    save_preference('coding_style', 'Always use type hints in Python')
    save_preference('coding_style', 'Keep functions small and focused')

    save_preference('communication', 'Keep responses concise and actionable')
    save_preference('communication', 'Use bullet points for lists')

    save_preference('workflow', 'Daily standup is at 9:00 AM')
    save_preference('workflow', 'Prefer morning meetings over afternoon meetings')

    print()

    # Display saved preferences
    print("=" * 70)
    print("Saved Preferences")
    print("=" * 70)
    list_preferences()
    print()

    # Get preferences as dict
    print("=" * 70)
    print("Preferences as Dictionary")
    print("=" * 70)
    prefs = get_all_preferences()
    for category, rules in prefs.items():
        print(f"\n{category.replace('_', ' ').title()}:")
        for i, pref in enumerate(rules, 1):
            print(f"  {i}. {pref['rule']}")
    print()

    # Test query with preferences (requires notes to be ingested and API key set)
    print("=" * 70)
    print("Testing Query with Preferences Injection")
    print("=" * 70)
    print()

    try:
        print("Query: 'What are best practices for Python development?'")
        print("-" * 70)
        answer = query_second_brain("What are best practices for Python development?")
        print()
        print("Answer:")
        print(answer)
        print()
        print("The agent should respect your coding_style preferences!")
    except Exception as e:
        print(f"Query test skipped: {e}")
        print("   (Make sure you have ingested notes and set GOOGLE_API_KEY)")

    print()
    print("=" * 70)
    print("Memory system test complete!")
    print("=" * 70)
    print()
    print("Your preferences are stored in: data/preferences.json")
    print("They will be automatically injected into all future queries!")
    print()

if __name__ == "__main__":
    main()