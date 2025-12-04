"""
Multi-Agent System

This package contains all specialized agents:
- Architect: Job Description -> Technical Design Document
- Dev Team: TDD -> Working Code
- Curator: Automated codebase discovery
- Chief of Staff: Daily briefings and scheduling
"""

from src.agents import architect
from src.agents import dev_team
from src.agents import curator
from src.agents import chief_of_staff

__all__ = [
    'architect',
    'dev_team',
    'curator',
    'chief_of_staff'
]