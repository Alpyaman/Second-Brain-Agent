"""
State definition for the Architect Session workflow.

This module defines the TypedDict state usade by the Architect Session LangGraph.
"""

from typing import TypedDict, List, Optional, Literal

# Project types
ProjectType = Literal["web_app", "script", "notebook", "library", "api", "unknown"]

class ArchitectState(TypedDict):
    """State for the Architect Session workflow."""

    # User input
    goal: str # High-level architectural goal or raw job description
    is_job_description: Optional[bool] # Flag indicating if input is a job posting

    # Parsed job description fields (if applicable)
    project_title: Optional[str]
    project_description: Optional[str]
    required_features: Optional[List[str]]
    tech_requirements: Optional[List[str]]
    budget_timeline: Optional[str]
    project_type: Optional[ProjectType] # Detected project type: web_app, script, notebook, library, api

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