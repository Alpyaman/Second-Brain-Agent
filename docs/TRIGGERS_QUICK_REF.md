# Cross-Agent Triggers: Quick Reference

**The Nervous System for Your Second Brain**

## What Are Triggers?

Automatic actions that happen when agents detect patterns in your calendar, emails, or notes.

**Example:** You schedule "Project Kickoff Meeting" → Architect automatically generates a project template before you arrive.

## Trigger Patterns

### 📅 Calendar Keywords → Agent Actions

| Keywords | Agent | Action | Auto? |
|----------|-------|--------|-------|
| kickoff, planning, design session | 🏗️ Architect | Generate project TDD | ⏸️ No |
| sprint planning, code review | 💻 Dev Team | Prepare review materials | ⏸️ No |
| research, learn, training | 📚 Curator | Discover resources | ✅ Yes |
| client meeting, demo | 👔 Chief | Prepare brief | ✅ Yes |

## Quick Start

### See It in Action
```bash
python demo_triggers.py
```

### Use It Automatically
```bash
# Run Chief of Staff daily briefing
python chief_of_staff.py

# Triggers detected and executed automatically!
```

## How It Works

```
Your Calendar: "Project Kickoff - New CRM System"
              ↓
Chief of Staff detects pattern
              ↓
Triggers Architect agent
              ↓
Architect generates TDD
              ↓
Saved to: docs/tdd_new_crm_system_20241207.md
              ↓
You arrive at meeting with complete design ready!
```

## Common Use Cases

### 1. Project Kickoff
**Problem:** Arrive unprepared  
**Solution:** TDD auto-generated from meeting title  
**Time Saved:** 30-60 minutes

### 2. Sprint Planning
**Problem:** "What did we do last sprint?"  
**Solution:** Dev Team compiles recent changes  
**Time Saved:** 20-30 minutes

### 3. Learning Session
**Problem:** Forget to research beforehand  
**Solution:** Curator discovers resources  
**Time Saved:** 15-30 minutes

### 4. Client Meeting
**Problem:** Scramble for context  
**Solution:** Chief compiles notes and brief  
**Time Saved:** 15-20 minutes

## Check Queue

```python
from src.tools.agent_triggers import get_queued_triggers

# See all pending triggers
triggers = get_queued_triggers()

for trigger in triggers:
    print(f"{trigger.target_agent}: {trigger.event_details['suggestion']}")
```

## Execute Manually

```python
from src.tools.agent_triggers import get_queued_triggers, execute_trigger
import asyncio

# Get high-priority triggers
triggers = get_queued_triggers(priority='high')

# Execute one
async def run():
    result = await execute_trigger(triggers[0])
    if result.success:
        print(f"Generated: {result.output['tdd_file']}")

asyncio.run(run())
```

## Where Are Files?

| File | Location | Purpose |
|------|----------|---------|
| Queue | `output/triggers/queued_triggers.json` | Pending triggers |
| History | `output/triggers/trigger_history.jsonl` | Execution log |
| Generated TDDs | `docs/tdd_*.md` | Architect output |

## Customize Patterns

Edit `src/tools/agent_triggers.py`:

```python
# Add your own keywords
custom_keywords = ['quarterly review', 'budget planning']

if any(keyword in event_title for keyword in custom_keywords):
    triggers.append(TriggerContext(
        target_agent=AgentType.CHIEF_OF_STAFF,
        event_details={'action': 'prepare_executive_brief'},
        priority='urgent',
        auto_execute=True
    ))
```

## Troubleshooting

### Triggers Not Detected?
1. Check keywords match event title
2. Add debug logging
3. Run demo to test patterns

### Triggers Not Executing?
1. Check `auto_execute` flag
2. Look in queue: `get_queued_triggers()`
3. Execute manually if needed

### Where Are My Generated Files?
```bash
# Check docs directory
ls docs/tdd_*.md

# Check trigger history
cat output/triggers/trigger_history.jsonl
```

## Dashboard Integration

In Streamlit dashboard (Chief of Staff page):

```python
# See triggered actions
st.session_state.get('triggered_actions', [])

# Approve and execute
if st.button("Execute"):
    result = asyncio.run(execute_trigger(trigger))
```

## Performance

| Operation | Time |
|-----------|------|
| Detect pattern | <100ms |
| Queue trigger | <10ms |
| Generate TDD | 2-3 sec |
| Discover resources | 1-2 sec |

## Learn More

- **Complete Guide:** [docs/CROSS_AGENT_TRIGGERS.md](CROSS_AGENT_TRIGGERS.md)
- **Implementation:** [docs/IMPLEMENTATION_CROSS_AGENT_TRIGGERS.md](IMPLEMENTATION_CROSS_AGENT_TRIGGERS.md)
- **Code:** [src/tools/agent_triggers.py](../src/tools/agent_triggers.py)
- **Tests:** [tests/unit/test_agent_triggers.py](../tests/unit/test_agent_triggers.py)

## Real Impact

**Before Triggers:**
- See meeting → Panic → Scramble → Arrive unprepared

**After Triggers:**
- See meeting → Agent works automatically → Arrive prepared → Impress everyone

**Bottom Line:** Never arrive at a meeting unprepared again. 🎯
