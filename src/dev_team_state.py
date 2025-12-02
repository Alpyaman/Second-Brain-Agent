"""
Development Team State Definition

This module defines the state structure for the multi-agent development team work flow.
The state tracks the feature request decomposition, specialized code generation, and
integration review process.
"""

from typing import TypedDict, List

class DevTeamState(TypedDict):
    """
    State for the multi-agent development team workflow.

    Workflow:
    1. Tech Lead receives feature_request and decomposes it
    2. Frontend/Backend specialists work on their respective tasks
    3. Integration Reviewer validates the outputs
    """

    # Input
    feature_request: str # High-level feature description from user

    # Tech Lead outputs
    frontend_tasks: List[str]   # List of frontend tasks
    backend_tasks: List[str]    # List of backend tasks
    architecture_notes: str     # High-level architecture decisions

    # Frontend Specialist outputs
    frontend_code: str          # Generated frontend code
    frontend_context: str       # Retrieved patterns from frontend_brain
    frontend_status: str        # Status: pending, in_progress, completed

    # Backend Specialist outputs
    backend_code: str           # Generated backend code
    backend_context: str        # Retrieved patterns from backend_brain
    backend_status: str         # Status: pending, in_progress, completed

    # Integration Reviewer outputs
    integration_review: str     # Review findings and recommendations
    issues_found: List[str]     # List of integration issues
    review_status: str          # Status: pass, needs_revision, fail

    # Metadata
    iteration_count: int        # Number of refinement iterations
    needs_revision: bool        # Whether code needs revision