# Project Structure

This document describes the organization of the Second-Brain-Agent codebase after the Phase 3 refactoring.

## Overview

The `src/` directory is organized into logical modules for better maintainability and clarity:

```
src/
├── agents/              # All agent implementations
│   ├── curator/         # Curator Agent (Phases 1-3)
│   ├── architect/       # Architect Agent
│   ├── dev_team/        # Dev Team Agent
│   └── chief_of_staff/  # Chief of Staff Agent
├── ingestion/           # Repository ingestion modules
├── core/                # Core utilities (config, brain)
└── tools/               # External service integrations
```

## Directory Structure

### `src/agents/` - Agent Implementations

All agentic workflows built with LangGraph.

#### `agents/curator/` - Curator Agent
Automated codebase discovery, filtering, and ingestion system.

- **`graph.py`**: LangGraph workflow with 4 nodes
  - generate_queries: Create targeted search queries
  - execute_searches: Perform web searches
  - filter_categorize: LLM-powered filtering
  - ingest_repos: Automated ingestion
- **`state.py`**: CuratorState TypedDict definition
- **`models.py`**: Pydantic models for structured output
  - RepositoryAssessment
  - CuratorFilterResult
  - SearchQuery
  - SearchQueryBatch

**Key Features**:
- Phase 1: Discovery & LLM filtering
- Phase 2: Orchestrated ingestion
- Phase 3: Scheduling & maintenance

#### `agents/architect/` - Architect Agent
Interactive design partner for system architecture.

- **`graph.py`**: Architect session workflow
- **`state.py`**: ArchitectState TypedDict

**Key Features**:
- Code context retrieval
- Preference-aligned design generation
- Interactive refinement loop

#### `agents/dev_team/` - Dev Team Agent
Multi-agent development team simulation.

- **`graph.py`**: Dev team coordination workflow
- **`state.py`**: DevTeamState TypedDict

#### `agents/chief_of_staff/` - Chief of Staff Agent
Personal assistant for calendar, email, and briefings.

- **`graph.py`**: Chief of staff workflow
- **`state.py`**: AgentState TypedDict
- **`runner.py`**: Simple runner script

**Key Features**:
- Google Calendar integration
- Gmail draft creation
- Daily briefings with context

### `src/ingestion/` - Ingestion Modules

All repository and notes ingestion functionality.

- **`ingest_expert.py`**: Expert knowledge ingestion
  - Clone and ingest GitHub repositories
  - Language-aware code chunking
  - Commit hash tracking (Phase 3)
  - Domain-specific collections (frontend_brain, backend_brain, fullstack_brain)

- **`ingest_notes.py`**: Markdown notes ingestion
  - Recursive markdown file discovery
  - Document chunking
  - ChromaDB storage

- **`dispatcher.py`**: Ingestion dispatcher API
  - `dispatch_ingestion()`: Single repository
  - `dispatch_batch_ingestion()`: Batch processing
  - Duplicate detection (Phase 3)
  - Update checking (Phase 3)
  - Smart re-ingestion

- **`maintenance.py`**: Repository maintenance utilities
  - `get_repository_metadata()`: Check if repo exists
  - `check_repository_needs_update()`: Compare commit hashes
  - `list_ingested_repositories()`: List all repos
  - `remove_repository_from_collection()`: Remove repo
  - `get_collection_stats()`: Collection statistics

### `src/core/` - Core Utilities

Shared configuration and brain query interface.

- **`config.py`**: Configuration and environment variables
  - Project paths (DATA_DIR, NOTES_DIR, CHROMA_DB_DIR)
  - Embedding model configuration
  - Collection names

- **`brain.py`**: Query interface for Second Brain
  - `query_second_brain()`: RAG-powered querying
  - Preference injection
  - Context-aware answers

### `src/tools/` - External Service Integrations

- **`google_calendar.py`**: Google Calendar API
  - `get_todays_events()`
  - `get_events_in_range()`

- **`gmail.py`**: Gmail API
  - `create_draft_email()`
  - `list_drafts()`

- **`memory.py`**: Long-term memory and preferences
  - `save_preference()`
  - `get_all_preferences()`
  - `list_preferences()`
  - `delete_preference()`

## Root-Level Scripts

### Agent Entry Points

- **`curator.py`**: Curator Agent CLI
  ```bash
  python curator.py --discover-only
  python curator.py --domains frontend backend
  ```

- **`schedule_curator.py`**: Automated scheduler for cron jobs
  ```bash
  python schedule_curator.py --log-file logs/curator.log
  ```

- **`architect.py`**: Architect Mode interactive CLI
  ```bash
  python architect.py --goal "Build a REST API"
  ```

- **`dev_team.py`**: Dev Team agent CLI
  ```bash
  python dev_team.py
  ```

- **`chief_of_staff.py`**: Simple Chief of Staff runner
  ```bash
  python chief_of_staff.py
  ```

### Recommended Entry Point

- **`src/main.py`**: Main CLI with formatted output
  ```bash
  python src/main.py --query "What should I focus on today?"
  ```

## Import Patterns

After refactoring, imports follow these patterns:

### Core Utilities
```python
from core.config import CHROMA_DB_DIR, EMBEDDING_MODEL
from core.brain import query_second_brain
```

### Agent Modules
```python
# Curator
from agents.curator.graph import run_curator_agent
from agents.curator.state import CuratorState
from agents.curator.models import RepositoryAssessment

# Architect
from agents.architect.graph import create_architect_graph
from agents.architect.state import ArchitectState

# Dev Team
from agents.dev_team.graph import create_dev_team_graph
from agents.dev_team.state import DevTeamState

# Chief of Staff
from agents.chief_of_staff.graph import create_graph
from agents.chief_of_staff.state import AgentState
```

### Ingestion Modules
```python
from ingestion.ingest_expert import ingest_expert_knowledge
from ingestion.ingest_notes import main as ingest_notes
from ingestion.dispatcher import dispatch_ingestion, dispatch_batch_ingestion
from ingestion.maintenance import (
    get_repository_metadata,
    check_repository_needs_update,
    list_ingested_repositories
)
```

### Tools
```python
from tools.google_calendar import get_todays_events
from tools.gmail import create_draft_email
from tools.memory import save_preference, get_all_preferences
```

## Data Organization

```
data/
├── notes/              # Markdown notes for ingestion
├── preferences.json    # User preferences and guidelines
└── chroma_db/          # ChromaDB vector store
    ├── second_brain_notes/    # Notes collection
    ├── coding_brain/          # User's codebase
    ├── frontend_brain/        # Frontend expert knowledge
    ├── backend_brain/         # Backend expert knowledge
    └── fullstack_brain/       # Full-stack expert knowledge
```

## Logs and Output

```
logs/
├── curator.log         # Curator Agent logs
├── curator_discovery.log
├── frontend.log
└── backend.log
```

## Benefits of This Structure

### 1. **Clear Separation of Concerns**
- Agents are isolated in their own modules
- Ingestion logic is centralized
- Core utilities are shared across agents

### 2. **Easy Navigation**
- Find agent-specific code in `agents/<agent_name>/`
- Find ingestion logic in `ingestion/`
- Find core utilities in `core/`

### 3. **Scalability**
- Easy to add new agents (create `agents/new_agent/`)
- Easy to add new ingestion sources
- Easy to add new tools

### 4. **Maintainability**
- Related code is grouped together
- Import statements are clear and explicit
- Each module has a single responsibility

### 5. **Testability**
- Each module can be tested independently
- Clear boundaries between components
- Easy to mock dependencies

## Adding New Agents

To add a new agent:

1. Create `src/agents/my_agent/` directory
2. Add `__init__.py`, `graph.py`, `state.py`
3. Implement your LangGraph workflow in `graph.py`
4. Define state in `state.py`
5. Create root-level entry point `my_agent.py`

Example:
```python
# src/agents/my_agent/graph.py
from langgraph.graph import StateGraph, END
from agents.my_agent.state import MyAgentState

def create_my_agent_graph():
    workflow = StateGraph(MyAgentState)
    # Add nodes...
    return workflow.compile()
```

## Migration Guide

If you're updating existing code that uses old import paths:

| Old Import | New Import |
|------------|------------|
| `from config import ...` | `from core.config import ...` |
| `from brain import ...` | `from core.brain import ...` |
| `from curator_graph import ...` | `from agents.curator.graph import ...` |
| `from curator_state import ...` | `from agents.curator.state import ...` |
| `from curator_models import ...` | `from agents.curator.models import ...` |
| `from ingest_expert import ...` | `from ingestion.ingest_expert import ...` |
| `from ingestion_dispatcher import ...` | `from ingestion.dispatcher import ...` |
| `from repository_maintenance import ...` | `from ingestion.maintenance import ...` |

## Development Workflow

### Running Tests
```bash
# Test ingestion
python -m src.ingestion.ingest_notes

# Test curator
python curator.py --discover-only

# Test brain query
python -m src.core.brain
```

### Development Mode
```bash
# Install in development mode
pip install -e .

# Now you can import from anywhere
from src.core.brain import query_second_brain
from src.agents.curator.graph import run_curator_agent
```

## Documentation

- **Main README**: [README.md](README.md)
- **Curator Agent**: [CURATOR_AGENT.md](CURATOR_AGENT.md)
- **Scheduling**: [SCHEDULING.md](SCHEDULING.md)
- **Project Structure**: This document

---

**Last Updated**: Phase 3 Refactoring (December 2025)

For questions or contributions, refer to the main [README.md](README.md).