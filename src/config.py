"""
Configuration module for Second-Brain-Agent.
Loads environment variables and provides configuration settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Validate required environment variables
if not GOOGLE_API_KEY:
    raise ValueError("Google API key is not set. Please add it to your .env file.")

# Project Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
NOTES_DIR = PROJECT_ROOT / "notes"
CHROMA_DB_DIR = PROJECT_ROOT / "chroma_db"

# Model Configuration
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

# ChromaDB Configuration
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "second_brain_notes")

# Ensure data directories exist
NOTES_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)