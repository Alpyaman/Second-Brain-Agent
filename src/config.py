"""
Configuration module for Second-Brain-Agent.
Loads environment variables and provides configuration settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
NOTES_DIR = DATA_DIR / "notes"
CHROMA_DB_DIR = DATA_DIR / "chroma_db"

# Embedding Configuration (using local HuggingFace models)
# Popular options:
# - "all-MiniLM-L6-v2": Fast, lightweight (80MB), good for general use
# - "all-mpnet-base-v2": More accurate but slower (420MB)
# - "paraphrase-multilingual-MiniLM-L12-v2": For multilingual support
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# ChromaDB Configuration
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "second_brain_notes")

# Ensure data directories exist
NOTES_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)