"""
User Preferences and Long-Term Memory

This module manages user preferences and long-term memory for the agent.
Preferences are stored persistently and injected into queries for personalized responses.
"""

import json
import datetime
from typing import Dict, List

from src.core.config import DATA_DIR

# Preferences storage path
PREFERENCES_FILE = DATA_DIR / "preferences.json"

def load_preferences() -> Dict[str, List[Dict]]:
    """
    Load all preferences from storage.

    Returns:
        Dictionary with categoriees as keys and lists of preference dicts as values
    """
    if not PREFERENCES_FILE.exists():
        return {}
    
    try:
        with open(PREFERENCES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading preferences: {e}")
        return {}

def save_preferences(preferences: Dict[str, List[Dict]]):
    """
    Save all preferences to storage.

    Args:
        preferences: Dictionary of categorized preferences
    """
    try:
        # Ensure data directory exists
        PREFERENCES_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(PREFERENCES_FILE, 'w', encoding='utf-8') as f:
            json.dump(preferences, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving preferences: {e}")

def save_preference(category: str, rule: str) -> str:
    """
    Save a user preference or rule.

    Args:
        category: Category of the preference (e.g., 'coding_style', 'communication', 'workflow')
        rule: The preference rule or guideline

    Returns:
        Confirmation message

    Examples:
        save_preference('coding_style', 'Prefer functional programming over OOP')
        save_preference('communication', 'Be concise and direct, avoid verbose explanations')
        save_preference('workflow', 'Always run tests before committing)
    """
    preferences = load_preferences()

    # Initialize category if it doesn't exist
    if category not in preferences:
        preferences[category] = []
    
    # Create preference entry
    preference_entry = {'rule': rule, 'created_at': datetime.now().isoformat(), 'last_used': datetime.now().isoformat()}

    # Add to preferences
    preferences[category].append(preference_entry)

    # Save
    save_preferences(preferences)

    print(f"Preference saved in category '{category}'")
    print(f"Rule: {rule}")

    return f"Preferences saved successfully in '{category}'"

def get_all_preferences() -> Dict[str, List[str]]:
    """
    Get all preferences organized by category.

    Returns:
        Dictionary with categories as keys and lists of rule strings as values
    """
    preferences = load_preferences()

    # Extract just the rules (not metadata)
    result = {}
    for category, prefs in preferences.items():
        result[category] = [p['rule'] for p in prefs]

    return result

def get_preferences_by_category(category: str) -> List[str]:
    """
    Get preferences for a specific category.

    Args:
        category: Category name

    Returns:
        List of preference rules
    """
    preferences = load_preferences()
    if category in preferences:
        return [p['rule'] for p in preferences[category]]
    return []

def get_relevant_preferences(query: str = None) -> str:
    """
    Get preferences relevant to a query, formatted for injection into prompts.

    Args:
        query: Optional query to determine relevance (currently returns all)

    Returns:
        Formatted string of preferences for system prompt
    """
    preferences = get_all_preferences()

    if not preferences:
        return ""

    # Format preferences for prompt injection
    lines = ["**User Preferences and Guidelines:**"]
    lines.append("")

    for category, rules in preferences.items():
        if rules:
            # Capitalize category for display
            display_category = category.replace('_', ' ').title()
            lines.append(f"**{display_category}:**")
            for rule in rules:
                lines.append(f"- {rule}")
            lines.append("")

    return "\n".join(lines)

def list_preferences() -> str:
    """
    List all saved preferences in a formatted way.

    Returns:
        Formatted string of all preferences
    """
    preferences = get_all_preferences()

    if not preferences:
        return "No preferences saved yet."

    lines = ["Saved Preferences:"]
    lines.append("")

    for category, rules in preferences.items():
        display_category = category.replace('_', ' ').title()
        lines.append(f"**{display_category}** ({len(rules)} rule(s)):")
        for i, rule in enumerate(rules, 1):
            lines.append(f"  {i}. {rule}")
        lines.append("")

    return "\n".join(lines)

def delete_preference(category: str, rule_index: int) -> str:
    """
    Delete a specific preference by category and index.

    Args:
        category: Category name
        rule_index: Index of the rule to delete (1-based)

    Returns:
        Confirmation message
    """
    preferences = load_preferences()

    if category not in preferences:
        return f"Category '{category}' not found"

    if rule_index < 1 or rule_index > len(preferences[category]):
        return f"Invalid rule index: {rule_index}"

    # Remove the preference (convert from 1-based to 0-based index)
    removed = preferences[category].pop(rule_index - 1)

    # Remove empty categories
    if not preferences[category]:
        del preferences[category]

    save_preferences(preferences)

    return f"Deleted preference: {removed['rule']}"

def clear_preferences(category: str = None) -> str:
    """
    Clear all preferences or preferences in a specific category.

    Args:
        category: Optional category to clear (if None, clears all)

    Returns:
        Confirmation message
    """
    if category:
        preferences = load_preferences()
        if category in preferences:
            count = len(preferences[category])
            del preferences[category]
            save_preferences(preferences)
            return f"Cleared {count} preference(s) from category '{category}'"
        else:
            return f"Category '{category}' not found"
    else:
        # Clear all
        save_preferences({})
        return "Cleared all preferences"

if __name__ == "__main__":
    """Test preference management."""
    print("=" * 60)
    print("User Preferences - Test Suite")
    print("=" * 60)
    print()

    # Test saving preferences
    print("Testing save_preference():")
    save_preference('coding_style', 'Prefer functional programming over OOP')
    save_preference('coding_style', 'Use descriptive variable names')
    save_preference('communication', 'Be concise and direct')
    save_preference('workflow', 'Always run tests before committing')
    print()

    # Test listing
    print("=" * 60)
    print("Testing list_preferences():")
    print(list_preferences())
    print()

    # Test getting formatted preferences
    print("=" * 60)
    print("Testing get_relevant_preferences():")
    print(get_relevant_preferences())
    print()

    print("=" * 60)