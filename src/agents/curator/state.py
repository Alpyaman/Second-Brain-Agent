"""
Curator Agent State Definition

This module defines the state structure for the Curator Agent workflow using TypedDict.
The state tracks the progression through discovery, filtering, and ingestion steps.
"""

from typing import TypedDict, List, Dict, Any, Optional


class CuratorState(TypedDict):
    """
    State for the Curator Agent workflow.

    The Curator Agent discovers, filters, and ingests high-quality codebases into domain-specific brain collections.
    """

    # Input configuration
    mode: str  # "auto" (generate queries) or "manual" (use provided queries)
    domains: List[str]  # Domains to search: ["frontend", "backend", "fullstack"]
    custom_queries: Optional[List[str]]  # Optional user-provided queries
    max_results_per_query: int  # Maximum search results to process per query

    # Generated search queries
    search_queries: List[Dict[str, str]]  # List of {query, domain, description}

    # Search results
    raw_search_results: List[Dict[str, Any]]  # Raw results from web search

    # Filtered and categorized repositories
    assessed_repositories: List[Dict[str, Any]]  # Filtered GitHub repos with assessments

    # Repositories approved for ingestion
    approved_for_ingestion: List[Dict[str, Any]]  # Repos that meet quality threshold

    # Ingestion results
    ingestion_results: List[Dict[str, str]]  # Results from ingestion attempts

    # Status tracking
    status: str  # Current workflow status
    error: Optional[str]  # Error message if workflow fails