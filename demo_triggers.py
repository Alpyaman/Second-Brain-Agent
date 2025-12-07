"""
Cross-Agent Trigger Demo

Demonstrates the "nervous system" in action:
- Calendar events automatically trigger appropriate agents
- Architect pre-generates project templates
- Dev Team prepares review materials
- Curator discovers learning resources
"""

import asyncio
from src.tools.agent_triggers import (
    detect_calendar_triggers,
    queue_trigger,
    get_queued_triggers,
    execute_trigger,
    AgentType
)


def demo_trigger_detection():
    """Demonstrate automatic trigger detection from calendar events."""
    print("=" * 80)
    print("CROSS-AGENT TRIGGER SYSTEM DEMO")
    print("=" * 80)
    print("\n🧠 The Nervous System: Agents automatically trigger each other\n")
    
    # Simulate a day's calendar events
    calendar_events = [
        {
            "title": "E-commerce Platform - Project Kickoff",
            "description": "Initial planning session for new online store. Discuss features, architecture, timeline.",
            "time": "9:00 AM"
        },
        {
            "title": "Sprint 23 Planning Meeting",
            "description": "Plan next two weeks of development work",
            "time": "11:00 AM"
        },
        {
            "title": "Research: React Server Components",
            "description": "Learn about RSC architecture and best practices",
            "time": "2:00 PM"
        },
        {
            "title": "Client Demo - Progress Review",
            "description": "Show current features to stakeholder, gather feedback",
            "time": "4:00 PM"
        }
    ]
    
    print("📅 Today's Calendar:\n")
    for event in calendar_events:
        print(f"  {event['time']} - {event['title']}")
    
    print("\n" + "=" * 80)
    print("ANALYZING CALENDAR FOR TRIGGER PATTERNS...")
    print("=" * 80 + "\n")
    
    all_triggers = []
    
    for event in calendar_events:
        print(f"\n📌 Analyzing: {event['title']}")
        print(f"   Time: {event['time']}")
        
        triggers = detect_calendar_triggers(
            event_title=event['title'],
            event_description=event['description']
        )
        
        if triggers:
            print(f"   ✅ Detected {len(triggers)} trigger(s):")
            for trigger in triggers:
                all_triggers.append(trigger)
                
                # Determine icon based on agent
                icons = {
                    'architect': '🏗️',
                    'dev_team': '💻',
                    'curator': '📚',
                    'chief_of_staff': '👔'
                }
                icon = icons.get(trigger.target_agent.value, '🔧')
                
                print(f"\n      {icon} Target: {trigger.target_agent.value.upper()}")
                print(f"      Action: {trigger.event_details.get('action', 'N/A')}")
                print(f"      Suggestion: {trigger.event_details.get('suggestion', 'N/A')}")
                print(f"      Priority: {trigger.priority.upper()}")
                print(f"      Auto-Execute: {'Yes ✓' if trigger.auto_execute else 'No (requires approval)'}")
                
                # Queue the trigger
                queue_trigger(trigger)
        else:
            print("   ℹ️  No triggers detected")
    
    print("\n" + "=" * 80)
    print(f"TRIGGER SUMMARY: {len(all_triggers)} triggers detected and queued")
    print("=" * 80 + "\n")
    
    return all_triggers


def demo_trigger_queue():
    """Demonstrate trigger queue management."""
    print("\n" + "=" * 80)
    print("TRIGGER QUEUE MANAGEMENT")
    print("=" * 80 + "\n")
    
    # Get all queued triggers
    all_triggers = get_queued_triggers()
    print(f"📋 Total queued triggers: {len(all_triggers)}\n")
    
    # Group by agent
    by_agent = {}
    for trigger in all_triggers:
        agent = trigger.target_agent.value
        if agent not in by_agent:
            by_agent[agent] = []
        by_agent[agent].append(trigger)
    
    for agent, triggers in by_agent.items():
        icons = {
            'architect': '🏗️',
            'dev_team': '💻',
            'curator': '📚',
            'chief_of_staff': '👔'
        }
        icon = icons.get(agent, '🔧')
        
        print(f"{icon} {agent.upper()}: {len(triggers)} trigger(s)")
        for trigger in triggers:
            print(f"   → {trigger.event_details.get('event_title', 'Unknown')}")
            print(f"     Priority: {trigger.priority}, Auto: {trigger.auto_execute}")
    
    # Show auto-execute vs manual
    print("\n" + "-" * 80)
    auto_triggers = [t for t in all_triggers if t.auto_execute]
    manual_triggers = [t for t in all_triggers if not t.auto_execute]
    
    print(f"\n⚡ Auto-Execute: {len(auto_triggers)} trigger(s)")
    for trigger in auto_triggers:
        print(f"   ✓ {trigger.target_agent.value}: {trigger.event_details.get('action')}")
    
    print(f"\n👤 Requires Approval: {len(manual_triggers)} trigger(s)")
    for trigger in manual_triggers:
        print(f"   ⏸️  {trigger.target_agent.value}: {trigger.event_details.get('action')}")


async def demo_trigger_execution():
    """Demonstrate trigger execution (mocked)."""
    print("\n" + "=" * 80)
    print("TRIGGER EXECUTION SIMULATION")
    print("=" * 80 + "\n")
    
    # Get high-priority triggers
    high_priority = get_queued_triggers(priority='high')
    
    if not high_priority:
        print("ℹ️  No high-priority triggers to execute")
        return
    
    print(f"🎯 Executing {len(high_priority)} high-priority trigger(s)...\n")
    
    for i, trigger in enumerate(high_priority[:3], 1):  # Limit to first 3
        print(f"\n[{i}/{min(3, len(high_priority))}] Executing: {trigger.target_agent.value}")
        print(f"     Event: {trigger.event_details.get('event_title')}")
        print(f"     Action: {trigger.event_details.get('action')}")
        
        if trigger.target_agent == AgentType.ARCHITECT:
            print("\n     🏗️  Triggering Architect Agent...")
            print("     → Analyzing meeting details")
            print("     → Detecting project type")
            print("     → Querying knowledge base for preferences")
            print("     → Generating Technical Design Document")
            
            # In real scenario: result = await execute_trigger(trigger)
            # For demo, simulate success
            print("\n     ✅ Success!")
            print("     📄 TDD saved to: docs/tdd_ecommerce_platform_20241207.md")
            print("     ⏱️  Execution time: 2.3s")
            print("\n     Preview:")
            print("     " + "-" * 70)
            print("     # Technical Design Document: E-commerce Platform")
            print("     ")
            print("     ## Project Overview")
            print("     Building a modern e-commerce platform with...")
            print("     " + "-" * 70)
        
        elif trigger.target_agent == AgentType.CURATOR:
            print("\n     📚 Triggering Curator Agent...")
            print("     → Searching GitHub for: React Server Components")
            print("     → Found 12 relevant repositories")
            print("     → Ingesting documentation and examples")
            print("     → Updating knowledge base")
            
            print("\n     ✅ Auto-executed!")
            print("     📊 Ingested 5 repositories, 234 documents")
            print("     ⏱️  Execution time: 1.8s")
        
        elif trigger.target_agent == AgentType.CHIEF_OF_STAFF:
            print("\n     👔 Triggering Chief of Staff...")
            print("     → Querying notes for: Client ABC")
            print("     → Compiling project history")
            print("     → Generating meeting brief")
            print("     → Creating email draft")
            
            print("\n     ✅ Auto-executed!")
            print("     📧 Email draft created in Gmail")
            print("     📋 Meeting brief ready")
            print("     ⏱️  Execution time: 1.2s")


def demo_real_world_scenario():
    """Show a complete real-world scenario."""
    print("\n\n" + "=" * 80)
    print("REAL-WORLD SCENARIO: Monday Morning")
    print("=" * 80)
    
    print("""
🌅 7:30 AM - You open your laptop

📱 Your Chief of Staff agent checks your calendar:
   - 9:00 AM: E-commerce Platform - Project Kickoff
   - 11:00 AM: Sprint Planning
   - 2:00 PM: Research: React Server Components
   - 4:00 PM: Client Demo

🧠 Nervous System activates:

   [BEFORE 9:00 AM MEETING]
   🏗️  Architect Agent (triggered):
      → Analyzes meeting title: "E-commerce Platform - Project Kickoff"
      → Generates complete TDD with:
         - Project structure
         - Technology stack recommendations
         - Implementation phases
         - Testing strategy
      → Saves to docs/tdd_ecommerce_platform_20241207.md
      ✅ READY FOR MEETING

   [BEFORE 11:00 AM MEETING]
   💻 Dev Team Agent (triggered):
      → Analyzes last sprint's work
      → Summarizes completed features
      → Identifies blockers
      → Calculates velocity metrics
      ✅ DATA READY FOR PLANNING

   [BEFORE 2:00 PM SESSION]
   📚 Curator Agent (auto-executed):
      → Searches for "React Server Components"
      → Discovers top GitHub repositories
      → Ingests documentation and examples
      → Adds to your knowledge base
      ✅ LEARNING MATERIALS READY

   [BEFORE 4:00 PM DEMO]
   👔 Chief of Staff (auto-executed):
      → Queries notes for client context
      → Compiles project timeline
      → Drafts follow-up email
      → Prepares talking points
      ✅ MEETING PREP COMPLETE

🎯 Result:
   - You enter EVERY meeting fully prepared
   - Zero time wasted on "what did we do last week?"
   - Learning resources curated before you need them
   - Client context at your fingertips

⏰ Time saved: 2-3 hours of prep work automated
🧠 Mental load: Reduced by eliminating "don't forget to..."
🚀 Productivity: Agents work while you sleep/commute
""")


def main():
    """Run the complete demo."""
    # Phase 1: Detect triggers from calendar
    all_triggers = demo_trigger_detection()
    
    # Phase 2: Show queue management
    demo_trigger_queue()
    
    # Phase 3: Simulate execution
    asyncio.run(demo_trigger_execution())
    
    # Phase 4: Real-world scenario
    demo_real_world_scenario()
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print("\n📚 Learn more: docs/CROSS_AGENT_TRIGGERS.md")
    print("🧪 Run tests: pytest tests/unit/test_agent_triggers.py")
    print("🚀 Try it live: python chief_of_staff.py\n")


if __name__ == "__main__":
    main()
