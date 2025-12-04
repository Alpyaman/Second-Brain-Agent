"""
Architect Agent - Job Description to Technical Design Document

This module provides the Instant Consultant functionality that transforms
raw job descriptions into professional Technical Design Documents.
"""

# Lazy imports to avoid dependency issues
def __getattr__(name):
    if name == 'run_architect_session':
        from src.agents.architect.graph import run_architect_session
        return run_architect_session
    elif name == 'create_architect_graph':
        from src.agents.architect.graph import create_architect_graph
        return create_architect_graph
    elif name == 'ArchitectState':
        from src.agents.architect.state import ArchitectState
        return ArchitectState
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    'run_architect_session',
    'create_architect_graph',
    'ArchitectState'
]