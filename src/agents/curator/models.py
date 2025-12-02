"""
Pydantic Models for Curator Agent

This module defines structured data models for the Curator Agent's LLM outputs, ensuring consistent and validated responses when filtering and categorizing repositories.
"""

from typing import List, Literal
from pydantic import BaseModel, Field, HttpUrl


class RepositoryAssessment(BaseModel):
    """Assessment of a single repository's quality and relevance."""

    url: HttpUrl = Field(description="The GitHub repository URL")

    is_relevant: bool = Field(description="Whether this repository is relevant for learning high-quality code patterns")

    quality_score: int = Field(ge=1, le=10, description="Quality score from 1-10 based on: stars, activity, code quality indicators")

    category: Literal["frontend", "backend", "fullstack", "other"] = Field(description="The domain category this repository belongs to")

    target_collection: Literal["frontend_brain", "backend_brain", "fullstack_brain", "skip"] = Field(description="Which ChromaDB collection should store this repository")

    reasoning: str = Field(description="Brief explanation of the assessment and categorization")

    technologies: List[str] = Field(default_factory=list, description="Main technologies/frameworks identified in the repository")


class CuratorFilterResult(BaseModel):
    """Result of filtering and categorizing search results."""

    repositories: List[RepositoryAssessment] = Field(description="List of assessed repositories from search results")

    summary: str = Field(description="Brief summary of the filtering results")


class SearchQuery(BaseModel):
    """A search query for discovering repositories."""

    query: str = Field(description="The search query string")

    domain: Literal["frontend", "backend", "fullstack"] = Field(description="The domain this query targets")

    description: str = Field(description="What this query is trying to find")


class SearchQueryBatch(BaseModel):
    """A batch of search queries for repository discovery."""

    queries: List[SearchQuery] = Field(
        description="List of search queries to execute"
    )