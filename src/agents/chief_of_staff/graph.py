"""
LangGraph Agent Workflow

This module defines the Chief of Staff agent workflow using LangGraph.
It orchestrates calendar checkingü knowledge base queries, and briefing generation.
"""

import os
import re
from typing import Any, Dict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END

from src.agents.chief_of_staff.state import AgentState
from tools.google_calendar import get_todays_event
from tools.gmail import create_draft_email
from src.core.brain import query_second_brain
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")

def check_schedule(state: AgentState) -> Dict[str, Any]:
    """
    Node 1: Check today's calendar schedule.

    Retrieves today's events from Google Calendar and updates the state.

    Args:
        state: Current agent state

    Returns:
        Updated state with calendar_events populated
    """
    print("[Node: check_schedule] Fetching today's calendar events...")

    calendar_events = get_todays_event()

    print(f"Calendar events retrieved:\n{calendar_events}\n")

    return {"calendar_events": calendar_events}

def consult_brain(state: AgentState) -> Dict[str, Any]:
    """
    Node 2: Consult the knowledge base for relevant context.

    Extract keywords from calendar events (people names, project titles, etc.) and queries
    the second brain to get relevant context about them.

    Args:
        state: Current agent state with calendar_events

    Returns:
        Updated state with relevant_notes populated
    """
    print("[Node: consult_brain] Extracting context from knowledge base...")

    calendar_events = state.get("calendar_events", "")

    if not calendar_events or "No events" in calendar_events:
        print("No calendar events to analyze.")
        return {"relevant_notes": "No calendar events scheduled, so no specific context needed from notes."}
    

    # Extract potential keywords from calendar events
    # Look for capitalized words (likely names, projects, or important terms)
    keywords = extract_keywords_from_calendar(calendar_events)

    print(f"Extracted keywords: {', '.join(keywords) if keywords else 'None'}")

    if not keywords:
        print("No specific keywords found in calendar")
        return {"relevant_notes": "No specific topics or people identified from calendar events."}
    
    # Query the brain for each keyword
    all_notes = []
    for keyword in keywords[:5]: # Limit to top 5 keywords to avoid too many queries
        print(f"Querying brain for: '{keyword}'")
        try:
            notes = query_second_brain(f"What do I know about {keyword}?", k=3)
            if notes and "I don't have that in your Second Brain records" not in notes:
                all_notes.append(f"### Context for '{keyword}':\n{notes}")
        except Exception as e:
            print(f"Error querying for '{keyword}': {e}")

    if not all_notes:
        relevant_notes = "No relevant information found in your notes for today's calendar topics."
    else:
        relevant_notes = "\n\n".join(all_notes)
    
    print(f"Retrieved {len(all_notes)} relevant note sections\n")

    return {"relevant_notes": relevant_notes}

def extract_keywords_from_calendar(calendar_text: str) -> list[str]:
    """
    Extract potential keywords from calendar event text.

    Looks for:
    - Capitalized words (names, projects, companies)
    - Common meeting types
    - Location names

    Args:
        calendar_text: Calendar events as formatted text

    Returns:
        List of extracted keywords
    """
    # Remove common time indicators and formatting
    cleaned_text = re.sub(r'\d{1,2}:\d{2}\s*(AM|PM)', '', calendar_text)
    cleaned_text = re.sub(r'[📅📆📍•-]', '', cleaned_text)

    # Find capitalized words (potential names, projects, etc.)
    # Match words that start with capital letter and have at least 2+ chars
    capitalized_words = re.findall(r'\b[A-Z][a-z]{2,}\b', cleaned_text)

    # Remove common words that aren't useful
    stop_words = {
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December',
        'Meeting', 'Call', 'Events', 'Today', 'Conference', 'Room', 'Zoom',
        'Team', 'Daily', 'Weekly', 'Monthly', 'Standup', 'Review'
    }

    keywords = [word for word in capitalized_words if word not in stop_words]

    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for word in keywords:
        if word.lower() not in seen:
            seen.add(word.lower())
            unique_keywords.append(word)

    return unique_keywords

def parse_and_create_email_drafts(text: str) -> int:
    """
    Parse email suggestions from briefing text and create Gmail drafts.

    Looks for emails in the format:
    ---DRAFT_EMAIL---
    TO: recipient@example.com
    SUBJECT: Subject line
    BODY:
    Email body...
    ---END_EMAIL---

    Args:
        text: Briefing text that may contain email suggestions

    Returns:
        Number of email drafts created
    """
    # Find all email blocks
    email_pattern = r'---DRAFT_EMAIL---\s*\n(.*?)\n---END_EMAIL---'
    email_blocks = re.findall(email_pattern, text, re.DOTALL)

    if not email_blocks:
        return 0

    print(f"\n[Email Drafts] Found {len(email_blocks)} suggested email(s)")

    drafts_created = 0
    for i, block in enumerate(email_blocks, 1):
        try:
            # Parse TO, SUBJECT, BODY
            to_match = re.search(r'TO:\s*(.+)', block)
            subject_match = re.search(r'SUBJECT:\s*(.+)', block)
            body_match = re.search(r'BODY:\s*\n(.*)', block, re.DOTALL)

            if not (to_match and subject_match and body_match):
                print(f"Email {i}: Missing required fields, skipping")
                continue

            to = to_match.group(1).strip()
            subject = subject_match.group(1).strip()
            body = body_match.group(1).strip()

            print(f"\n   Creating draft {i}:")
            print(f"   To: {to}")
            print(f"   Subject: {subject}")

            # Create the draft
            result = create_draft_email(to, subject, body)

            if "successfully" in result:
                drafts_created += 1
            else:
                print(f"Failed to create draft: {result}")

        except Exception as e:
            print(f"Error processing email {i}: {e}")

    return drafts_created

def remove_email_markers(text: str) -> str:
    """
    Remove email draft markers from the briefing text.

    Args:
        text: Briefing text with email markers

    Returns:
        Clean briefing text without email markers
    """
    # Remove all email blocks
    pattern = r'---DRAFT_EMAIL---.*?---END_EMAIL---'
    cleaned = re.sub(pattern, '', text, flags=re.DOTALL)
    # Remove excessive whitespace
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()

def draft_briefing(state: AgentState) -> Dict[str, Any]:
    """
    Node 3: Draft a morning briefing using Gemini.

    Takes calendar events and relevant notes to create a personalized
    daily briefing with context and recommendations.

    Args:
        state: Current agent state with calendar_events and relevant_notes

    Returns:
        Updated state with daily_plan populated
    """
    print("[Node: draft_briefing] Generating morning briefing with Gemini...")

    calendar_events = state.get("calendar_events", "No events scheduled")
    relevant_notes = state.get("relevant_notes", "No relevant context found")
    user_query = state.get("user_query", "Give me my daily briefing")

    if not GOOGLE_API_KEY:
        error_msg = "Error: GOOGLE_API_KEY not set. Cannot generate briefing."
        print(error_msg)
        return {"daily_plan": error_msg}

    # Create the briefing prompt
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """You are an AI Chief of Staff assistant. Your role is to provide concise,
        actionable daily briefings that combine calendar information with relevant knowledge from the user's notes.

        Guidelines:
        - Be concise but insightful
        - Highlight important connections between calendar events and notes
        - Provide specific recommendations or reminders
        - Use a professional but friendly tone
        - Structure the briefing clearly with sections
        - If you find relevant context from notes, mention it specifically (e.g., "Your notes mention that Ryan prefers React")
        - Prioritize what's most important for the day
        - If you identify that the user should send an email (follow-up, preparation, confirmation, etc.), suggest it using the special format below

        Email Suggestion Format:
        If you think an email should be sent, add a section at the end with:
        ---DRAFT_EMAIL---
        TO: recipient@example.com
        SUBJECT: Email subject here
        BODY:
        Email body content here...
        ---END_EMAIL---

        You can suggest multiple emails by repeating this format."""),

                ("user", """Please create my daily briefing.

        User's Request: {user_query}

        TODAY'S SCHEDULE:
        {calendar_events}

        RELEVANT CONTEXT FROM MY NOTES:
        {relevant_notes}

        Create a structured morning briefing that:
        1. Summarizes today's schedule
        2. Provides relevant context from my notes for each event
        3. Suggests priorities or preparation items
        4. Highlights any important connections or insights
        5. If you notice I should send any emails (follow-ups, meeting prep, confirmations, etc.), suggest draft emails using the special format

        Format the briefing clearly with headers and bullet points.""")
    ])

    # Initialize Gemini
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.7,
    )

    # Create chain
    chain = prompt_template | llm | StrOutputParser()

    # Generate briefing
    try:
        daily_plan = chain.invoke({
            "user_query": user_query,
            "calendar_events": calendar_events,
            "relevant_notes": relevant_notes
        })

        print("Morning briefing generated")

        # Check if the briefing includes email suggestions
        emails_created = parse_and_create_email_drafts(daily_plan)

        if emails_created:
            # Remove email markers from the final briefing
            daily_plan = remove_email_markers(daily_plan)
            # Add summary of created drafts
            daily_plan += f"\n\n **Email Drafts Created**: {emails_created}"

        return {"daily_plan": daily_plan}

    except Exception as e:
        error_msg = f"Error generating briefing: {e}"
        print(error_msg)
        return {"daily_plan": error_msg}

def create_agent_graph() -> StateGraph:
    """
    Create the LangGraph workflow for the Chief of Staff agent.

    The workflow consists of three sequential nodes:
    1. check_schedule: Retrieve today's calendar events
    2. consult_brain: Query knowledge base for relevant context
    3. draft_briefing: Generate personalized daily briefing

    Returns:
        Compiled StateGraph ready for execution
    """
    # Create the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("check_schedule", check_schedule)
    workflow.add_node("consult_brain", consult_brain)
    workflow.add_node("draft_briefing", draft_briefing)

    # Define the workflow edges (sequential execution)
    workflow.set_entry_point("check_schedule")
    workflow.add_edge("check_schedule", "consult_brain")
    workflow.add_edge("consult_brain", "draft_briefing")
    workflow.add_edge("draft_briefing", END)

    # Compile the graph
    app = workflow.compile()

    return app

if __name__ == "__main__":
    """Test the agent graph with a sample query."""
    print("=" * 70)
    print("Chief of Staff Agent - LangGraph Workflow Test")
    print("=" * 70,"\n")

    # Create the agent
    agent = create_agent_graph()

    # Initial state
    initial_state = {
        "user_query": "Give me my daily briefing",
        "calendar_events": "",
        "relevant_notes": "",
        "daily_plan": "",
        "messages": []
    }

    # Run the agent
    print("Starting agent workflow...\n")
    final_state = agent.invoke(initial_state)

    # Display the result
    print("=" * 70)
    print("FINAL DAILY BRIEFING")
    print("=" * 70,"\n")
    print(final_state["daily_plan"])
    print("=" * 70, "\n")