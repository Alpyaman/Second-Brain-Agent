"""
Core Configuration Module

Provides centralized configuration and environment variable management.
"""

from src.core.config import (
    CHROMA_DB_DIR,
    EMBEDDING_MODEL
)

__all__ = [
    'CHROMA_DB_DIR',
    'EMBEDDING_MODEL'
]