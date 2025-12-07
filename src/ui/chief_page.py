"""Chief of Staff Mode UI Page - Daily Briefings and Workflow Management."""

import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta
import json

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def render_chief_page(config: dict):
    """
    Render Chief of Staff mode page.
    
    Provides daily briefings, calendar integration, and task management.
    """
    st.markdown("# 🎯 Chief of Staff Mode")
    st.markdown("Your AI-powered daily briefing and workflow assistant")
    
    st.markdown("---")
    
    # Main tabs
    tabs = st.tabs(["📅 Daily Briefing", "📆 Calendar", "✉️ Email Drafts", "📋 Tasks"])
    
    with tabs[0]:
        render_daily_briefing()
    
    with tabs[1]:
        render_calendar_view()
    
    with tabs[2]:
        render_email_drafts()
    
    with tabs[3]:
        render_tasks()


def render_daily_briefing():
    """Render daily briefing section."""
    st.markdown("### 📅 Your Daily Briefing")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        briefing_date = st.date_input(
            "Briefing Date",
            value=datetime.now()
        )
    
    with col2:
        if st.button("🔄 Generate Briefing", type="primary"):
            with st.spinner("Generating your briefing..."):
                try:
                    # TODO: Call chief of staff agent
                    st.success("Briefing generated!")
                    
                    # Mock briefing for now
                    st.session_state.current_briefing = {
                        'date': briefing_date.isoformat(),
                        'content': generate_mock_briefing(briefing_date)
                    }
                except Exception as e:
                    st.error(f"Error generating briefing: {e}")
    
    # Display briefing
    if st.session_state.get('current_briefing'):
        briefing = st.session_state.current_briefing
        
        st.markdown("---")
        st.markdown(briefing['content'])


def render_calendar_view():
    """Render calendar integration view."""
    st.markdown("### 📆 Calendar Events")
    
    # Check if Google Calendar is configured
    token_file = Path("token.json")
    
    if not token_file.exists():
        st.warning("⚠️ Google Calendar not configured")
        st.info("""
        To enable calendar integration:
        1. Follow instructions in `GOOGLE_CALENDAR_SETUP.md`
        2. Authenticate and generate `token.json`
        3. Restart the dashboard
        """)
        return
    
    # Date range selector
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "From",
            value=datetime.now()
        )
    
    with col2:
        end_date = st.date_input(
            "To",
            value=datetime.now() + timedelta(days=7)
        )
    
    if st.button("📅 Fetch Events"):
        with st.spinner("Fetching calendar events..."):
            try:
                from src.tools.google_calendar import list_upcoming_events
                
                events = list_upcoming_events(max_results=20)
                
                if events:
                    st.success(f"Found {len(events)} events")
                    
                    for event in events:
                        with st.expander(f"📅 {event.get('summary', 'No title')}"):
                            st.markdown(f"**Start:** {event.get('start', {}).get('dateTime', 'N/A')}")
                            st.markdown(f"**End:** {event.get('end', {}).get('dateTime', 'N/A')}")
                            
                            if event.get('description'):
                                st.markdown(f"**Description:** {event['description']}")
                            
                            if event.get('location'):
                                st.markdown(f"**Location:** {event['location']}")
                else:
                    st.info("No upcoming events found")
            
            except Exception as e:
                st.error(f"Error fetching events: {e}")


def render_email_drafts():
    """Render email drafts section."""
    st.markdown("### ✉️ Email Draft Management")
    
    # Check if Gmail is configured
    token_file = Path("token.json")
    
    if not token_file.exists():
        st.warning("⚠️ Gmail not configured")
        st.info("""
        To enable Gmail integration:
        1. Follow instructions in `GMAIL_SETUP.md`
        2. Authenticate and generate `token.json`
        3. Restart the dashboard
        """)
        return
    
    # Create new draft
    with st.expander("✏️ Create New Draft", expanded=False):
        to_email = st.text_input("To:")
        subject = st.text_input("Subject:")
        body = st.text_area("Body:", height=200)
        
        if st.button("💾 Save Draft"):
            with st.spinner("Creating draft..."):
                try:
                    from src.tools.gmail import create_draft_email
                    
                    create_draft_email(
                        to=to_email,
                        subject=subject,
                        body=body
                    )
                    
                    st.success("✅ Draft created successfully!")
                except Exception as e:
                    st.error(f"Error creating draft: {e}")
    
    # List existing drafts
    st.markdown("---")
    st.markdown("**Your Drafts:**")
    
    if st.button("🔄 Refresh Drafts"):
        with st.spinner("Fetching drafts..."):
            try:
                from src.tools.gmail import list_drafts
                
                drafts = list_drafts(max_results=10)
                
                if drafts:
                    for draft in drafts:
                        message = draft.get('message', {})
                        headers = {h['name']: h['value'] for h in message.get('payload', {}).get('headers', [])}
                        
                        with st.expander(f"📧 {headers.get('Subject', 'No subject')}"):
                            st.markdown(f"**To:** {headers.get('To', 'N/A')}")
                            st.markdown(f"**Date:** {headers.get('Date', 'N/A')}")
                            st.markdown(f"**Draft ID:** {draft['id']}")
                else:
                    st.info("No drafts found")
            
            except Exception as e:
                st.error(f"Error fetching drafts: {e}")


def render_tasks():
    """Render task management section."""
    st.markdown("### 📋 Task Management")
    
    # Load tasks from preferences
    preferences_file = Path("data/preferences.json")
    tasks = []
    
    if preferences_file.exists():
        try:
            with open(preferences_file, 'r') as f:
                prefs = json.load(f)
                tasks = prefs.get('tasks', [])
        except Exception as e:
            logger.error(f"Error loading preferences: {e}")
            pass
    
    # Add new task
    with st.expander("➕ Add New Task", expanded=False):
        task_title = st.text_input("Task Title:")
        task_priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        task_due = st.date_input("Due Date", value=datetime.now())
        
        if st.button("➕ Add Task"):
            new_task = {
                'title': task_title,
                'priority': task_priority,
                'due_date': task_due.isoformat(),
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            
            tasks.append(new_task)
            save_tasks(tasks, preferences_file)
            
            st.success("✅ Task added!")
            st.rerun()
    
    # Display tasks
    st.markdown("---")
    st.markdown("**Your Tasks:**")
    
    if not tasks:
        st.info("No tasks yet. Add your first task above!")
        return
    
    # Filter tasks
    filter_status = st.multiselect(
        "Filter by Status",
        ["pending", "in_progress", "completed"],
        default=["pending", "in_progress"]
    )
    
    filtered_tasks = [t for t in tasks if t.get('status') in filter_status]
    
    # Group by priority
    high_priority = [t for t in filtered_tasks if t.get('priority') == 'High']
    medium_priority = [t for t in filtered_tasks if t.get('priority') == 'Medium']
    low_priority = [t for t in filtered_tasks if t.get('priority') == 'Low']
    
    # Display by priority
    for priority, task_list, color in [
        ("High Priority", high_priority, "🔴"),
        ("Medium Priority", medium_priority, "🟡"),
        ("Low Priority", low_priority, "🟢")
    ]:
        if task_list:
            st.markdown(f"**{color} {priority}:**")
            
            for i, task in enumerate(task_list):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    status_icon = "✅" if task.get('status') == 'completed' else "⏳"
                    st.markdown(f"{status_icon} {task['title']}")
                
                with col2:
                    st.caption(f"Due: {task.get('due_date', 'N/A')}")
                
                with col3:
                    if st.button("✓ Complete", key=f"complete_{i}_{priority}"):
                        task['status'] = 'completed'
                        save_tasks(tasks, preferences_file)
                        st.rerun()


def generate_mock_briefing(date):
    """Generate a mock daily briefing."""
    return f"""
## Good Morning! 👋

Here's your briefing for {date.strftime('%A, %B %d, %Y')}:

### 🎯 Today's Focus
- Complete Phase 3 implementation of Self-Healing Dev Team
- Review and merge pull requests
- Update documentation

### 📅 Calendar Highlights
- 10:00 AM - Team Standup
- 2:00 PM - Client Demo
- 4:00 PM - Code Review Session

### 📧 Email Summary
- 3 drafts pending review
- 2 important emails requiring response

### 💡 Recommendations
Based on your recent work:
- Consider adding integration tests for new self-healing feature
- Update README with Phase 3 features
- Schedule time for documentation review

### 📊 Yesterday's Achievements
- ✅ Implemented Docker code execution
- ✅ Created self-healing node
- ✅ Added comprehensive tests

Have a productive day! 🚀
"""


def save_tasks(tasks, preferences_file):
    """Save tasks to preferences file."""
    preferences_file.parent.mkdir(parents=True, exist_ok=True)
    
    prefs = {}
    if preferences_file.exists():
        with open(preferences_file, 'r') as f:
            prefs = json.load(f)
    
    prefs['tasks'] = tasks
    
    with open(preferences_file, 'w') as f:
        json.dump(prefs, f, indent=2)
