"""
State definition for the Architect Session workflow.

This module defines the TypedDict state usade by the Architect Session LangGraph.
"""

from typing import TypedDict, List, Optional

class ArchitectState(TypedDict):
    """State for the Architect Session workflow."""

    # User input
    goal: str # High-level architectural goal

    # Retrieved context
    code_examples: str
    preferences: str

    # Generated outputs
    design_document: str
    design_history: List[str]

    # Iteration Control
    feedback: Optional[str] # User feedback on the design
    iteration_count: int # Number of design iterations
    refinement_needed: bool # Whether more refinement is needed