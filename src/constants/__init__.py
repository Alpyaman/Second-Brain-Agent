"""
Constants and enumerations for Second Brain Agent.

This module contains all application-wide constants, default values,
and enumerations to avoid magic strings and improve maintainability.
"""

from enum import Enum
from pathlib import Path


# ============================================================================
# Project Structure Constants
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = SRC_DIR / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
OUTPUT_DIR = PROJECT_ROOT / "output"


# ============================================================================
# Agent Types
# ============================================================================


class AgentType(str, Enum):
    """Types of agents in the system."""

    ARCHITECT = "architect"
    TECH_LEAD = "tech_lead"
    FRONTEND = "frontend"
    BACKEND = "backend"
    DEVOPS = "devops"
    REVIEWER = "reviewer"
    CURATOR = "curator"


# ============================================================================
# LLM Provider Types
# ============================================================================


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    GOOGLE = "google"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"


# ============================================================================
# Model Names
# ============================================================================


class ModelName(str, Enum):
    """Common model names."""

    # Google Models
    GEMINI_PRO = "gemini-pro"
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"

    # OpenAI Models
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"

    # Ollama Models
    LLAMA2 = "llama2"
    CODELLAMA = "codellama"
    MISTRAL = "mistral"


# ============================================================================
# Project Types
# ============================================================================


class ProjectType(str, Enum):
    """Types of projects that can be generated."""

    REST_API = "rest_api"
    WEB_APP = "web_app"
    MOBILE_APP = "mobile_app"
    CLI_TOOL = "cli_tool"
    DATA_PIPELINE = "data_pipeline"
    ML_MODEL = "ml_model"
    MICROSERVICE = "microservice"


class Framework(str, Enum):
    """Supported frameworks."""

    # Backend
    FASTAPI = "fastapi"
    DJANGO = "django"
    FLASK = "flask"
    EXPRESS = "express"

    # Frontend
    REACT = "react"
    NEXTJS = "nextjs"
    VUE = "vue"
    ANGULAR = "angular"


class Database(str, Enum):
    """Supported databases."""

    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    SQLITE = "sqlite"
    REDIS = "redis"


# ============================================================================
# Default Configuration Values
# ============================================================================

DEFAULT_MODEL = ModelName.GEMINI_PRO
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 4096
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Timeout values (in seconds)
DEFAULT_LLM_TIMEOUT = 120
DEFAULT_EMBEDDING_TIMEOUT = 60

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Chunk sizes for processing
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200

# Collection names for vector stores
COLLECTION_FRONTEND = "frontend_brain"
COLLECTION_BACKEND = "backend_brain"
COLLECTION_NOTES = "second_brain_notes"


# ============================================================================
# File Extensions
# ============================================================================

CODE_EXTENSIONS = [
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".cpp",
    ".c",
    ".h",
]

DOCUMENT_EXTENSIONS = [".md", ".txt", ".pdf", ".docx"]

IGNORED_DIRECTORIES = ["node_modules", "__pycache__", ".git", ".venv", "venv", "dist", "build"]
