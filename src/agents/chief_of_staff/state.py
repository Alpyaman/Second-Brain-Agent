"""
Agent State Definition

This module defines the state structure for the LangGraph agent workflow.
The state tracks the agent's progress through the decision-making process.
"""

from typing import Annotated, List, TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    State object for t he Chief oof Staff agent.

    This state is passed between nodes in the LangGrap workflow, allowing each node to read
    and update the agent's context.
    """

    # User's query / request
    user_query: str

    # Calendar events retrieved from Google Calendar
    calendar_events: str

    # Relevant notes retrieved from the knowledge base
    relevant_notes: str

    # Final daily briefing/plan output
    daily_plan: str

    # Chat history for multi-turn conversations
    # Using Annotated with add_messages for proper message handling
    messages: Annotated[List, add_messages]