# Second-Brain-Agent

An AI-powered "Chief of Staff" and "Architect" agent built with LangGraph, ChromaDB, and HuggingFace models. This agent serves as your personal second brain, helping you manage knowledge, calendar, email, and architectural design.

**Key Features**:
- Uses local HuggingFace embeddings - no API keys required for ingestion
- Interactive Architect Mode - design systems aligned with your coding style
- Long-term memory - learns and respects your preferences
- Code-aware - understands your codebase patterns

## Project Structure

```
Second-Brain-Agent/
├── src/                    # Source code
│   ├── __init__.py
│   ├── config.py          # Configuration and environment variables
│   ├── state.py           # Agent state definition (TypedDict)
│   ├── graph.py           # LangGraph workflow and nodes
│   ├── architect_state.py # Architect session state definition
│   ├── architect_graph.py # Architect session workflow
│   ├── main.py            # CLI interface (recommended entry point)
│   ├── ingest_notes.py    # Script to ingest and index notes
│   ├── brain.py           # Query interface for your second brain
│   └── tools/             # External service integrations
│       ├── __init__.py
│       ├── memory.py           # Long-term memory and user preferences
│       ├── google_calendar.py  # Google Calendar integration
│       └── gmail.py            # Gmail integration (draft emails)
├── data/
│   ├── notes/             # Place your markdown/Notion notes here
│   ├── preferences.json   # User preferences and guidelines (auto-created)
│   └── chroma_db/         # ChromaDB vector store (auto-created)
├── chief_of_staff.py      # Simple runner script
├── architect.py           # Architect Mode interactive CLI
├── credentials.json       # Google OAuth credentials (you provide)
├── token.json             # Calendar auth token (gitignored)
├── gmail_token.json       # Gmail auth token (gitignored)
├── requirements.txt       # Python dependencies
├── .env                   # Your environment variables (create from .env.example)
├── .env.example          # Template for environment variables
├── GOOGLE_CALENDAR_SETUP.md  # Calendar API setup guide
└── GMAIL_SETUP.md            # Gmail API setup guide
```

## Setup Instructions

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

**For Phase 1 (Ingestion only):** Local embeddings work without any API keys!

**For Phase 2 (Querying):** You need a Google API key for Gemini:

```bash
cp .env.example .env
```

Edit `.env` and add your Google API key:
```
GOOGLE_API_KEY=your_actual_google_api_key_here
```

Get your free API key from: https://aistudio.google.com/app/apikey

### 4. Add Your Notes

Place your markdown files in the `data/notes/` directory. The agent will index and search through these files.

### 5. Ingest Your Content

The ingestion script can now handle both markdown notes and code:

**Ingest Markdown Notes:**
```bash
python src/ingest_notes.py
```

This will scan all `.md` and `.txt` files in `data/notes/`, chunk them, generate embeddings, and store them in ChromaDB.

**Ingest Code (Optional):**
```bash
# Ingest a codebase (e.g., your own project)
python src/ingest_notes.py --code /path/to/your/codebase

# Ingest both notes and code
python src/ingest_notes.py --code /path/to/codebase --notes

# Use custom collection name
python src/ingest_notes.py --code /path/to/codebase --collection my_project_code
```

The code ingestion:
- Uses Python-aware chunking (Language.PYTHON splitter)
- Extracts class and function names as metadata
- Stores in a separate `coding_brain` collection
- Excludes common directories (venv, __pycache__, .git, etc.)
- Parses Python files using AST for metadata extraction

This gives your agent technical context from your codebase!

### 6. Query Your Second Brain

Test querying your notes:

```bash
python src/brain.py
```

Or use it in your own code:

```python
from src.brain import query_second_brain

answer = query_second_brain("What are my thoughts on AI agents?")
print(answer)
```

### 7. (Optional) Configure Long-Term Memory

The agent includes a **long-term memory system** that stores your preferences and guidelines. These preferences are automatically injected into every query, ensuring the agent always respects your preferences.

**Save Preferences:**

```python
from src.tools.memory import save_preference

# Save coding preferences
save_preference('coding_style', 'Prefer functional programming over OOP')
save_preference('coding_style', 'Always use type hints in Python')

# Save communication preferences
save_preference('communication', 'Keep responses concise and actionable')
save_preference('communication', 'Use bullet points for lists')

# Save workflow preferences
save_preference('workflow', 'Daily standup is at 9:00 AM every day')
save_preference('workflow', 'I prefer morning meetings over afternoon meetings')
```

**View Preferences:**

```python
from src.tools.memory import list_preferences

# List all preferences
list_preferences()
```

**How It Works:**

When you query your second brain with `query_second_brain()`, the agent:
1. Fetches relevant preferences from `data/preferences.json`
2. Injects them into the system prompt automatically
3. Answers your question while respecting your preferences

**Example:**

```python
# After saving coding preference: "Prefer functional programming over OOP"

from src.brain import query_second_brain

answer = query_second_brain("How should I structure my new Python project?")
# The agent will recommend functional patterns based on your preference!
```

**Management Functions:**

```python
from src.tools.memory import (
    save_preference,
    get_all_preferences,
    list_preferences,
    delete_preference,
    clear_preferences
)

# Save a preference
save_preference('category', 'Your preference rule here')

# Get all preferences as dict
prefs = get_all_preferences()

# Display formatted preferences
list_preferences()

# Delete a specific preference
delete_preference('category', 0)  # Delete first preference in 'category'

# Clear all preferences in a category
clear_preferences('category')

# Clear ALL preferences
clear_preferences()
```

### 8. (Optional) Set Up Google Calendar Integration

To give your agent the ability to see your schedule:

1. **Follow the detailed setup guide**: [GOOGLE_CALENDAR_SETUP.md](GOOGLE_CALENDAR_SETUP.md)
   - Create a Google Cloud Project
   - Enable Google Calendar API
   - Download `credentials.json`

2. **Test the calendar integration**:
   ```bash
   python src/tools/google_calendar.py
   ```

3. **Use in your code**:
   ```python
   from src.tools.google_calendar import get_todays_events, get_events_in_range

   # Get today's events
   events = get_todays_events()
   print(events)

   # Get next 7 days of events
   upcoming = get_events_in_range(days_ahead=7)
   print(upcoming)
   ```

**Note**: Calendar integration provides **read-only** access to your calendar for privacy.

### 9. (Optional) Set Up Gmail Integration

To give your agent the ability to draft emails:

1. **Follow the detailed setup guide**: [GMAIL_SETUP.md](GMAIL_SETUP.md)
   - Enable Gmail API in your Google Cloud Project
   - Add Gmail scope to OAuth consent screen
   - Authenticate and generate Gmail token

2. **Test the Gmail integration**:
   ```bash
   python src/tools/gmail.py
   ```

3. **Use in your code**:
   ```python
   from src.tools.gmail import create_draft_email, list_drafts

   # Create a draft email
   create_draft_email(
       to="colleague@example.com",
       subject="Follow-up on Project Discussion",
       body="Hi,\n\nFollowing up on our conversation..."
   )

   # List current drafts
   drafts = list_drafts()
   print(drafts)
   ```

**Note**: Gmail integration only creates **drafts** - emails are never sent automatically. You review and send manually from Gmail.

### 10. Run Your Chief of Staff Agent

**Option 1: CLI Tool (Recommended)**

The main CLI interface with formatted output and options:

```bash
# Default morning briefing
python src/main.py

# Custom query
python src/main.py --query "What should I focus on this week?"

# Brief mode (just the briefing text)
python src/main.py --brief

# Skip email draft listing
python src/main.py --no-emails
```

**Option 2: Simple Runner**

Alternatively, use the simple runner script:

```bash
python chief_of_staff.py
```

Both will:
1. Check your Google Calendar for today's events
2. Extract keywords and query your knowledge base for context
3. Generate a personalized daily briefing with Gemini
4. Automatically create draft emails when appropriate (if Gmail is set up)
5. List email drafts created for your review

Example briefing:
```
YOUR DAILY BRIEFING

## Today's Schedule
- 9:00 AM: Team Standup
- 11:00 AM: Meeting with Ryan - React Migration Discussion
- 2:00 PM: Q4 Project Review

## Key Context from Your Notes
### Ryan
Your notes mention Ryan is the tech lead for the React migration project
and prefers component-based architecture with TypeScript.

### Q4 Project Review
Related to the roadmap you documented last week. The project deadline
is approaching next month.

## Priorities
1. Prepare React migration talking points for Ryan meeting
2. Review Q4 roadmap progress before afternoon meeting
3. Follow up with team on yesterday's action items

**Email Drafts Created**: 1
- Draft to Ryan: "React Migration Discussion Prep"
```

The agent will create draft emails in your Gmail when it identifies follow-ups, confirmations, or preparations you should send. All emails stay as drafts for your review!

### 11. Architect Mode - Interactive Design Sessions

The **Architect Mode** transforms your agent from a virtual assistant into a design partner. It analyzes your existing codebase, understands your coding style, and helps you design new systems aligned with your preferences.

**What It Does:**
- Retrieves relevant code patterns from your `coding_brain` collection
- Fetches your coding preferences from long-term memory
- Generates detailed architectural design documents
- Supports iterative refinement based on your feedback

**Interactive Mode (Recommended):**

```bash
python architect.py
```

This launches an interactive session where you can:
1. Describe your architectural goal
2. Review the generated design document
3. Provide feedback for refinement
4. Iterate until satisfied
5. Save the final design to a file

**Single Run Mode:**

```bash
# Generate a design for a specific goal
python architect.py --goal "Build a real-time chat application with WebSockets"

# Non-interactive (one-shot generation)
python architect.py --goal "Build a REST API for a blog platform" --no-interactive
```

**Example Session:**

```
ARCHITECT SESSION

Your Goal: Build a real-time chat application with WebSockets

Analyzing architectural goal...
Retrieving code context and preferences...
   Fetching coding preferences...
   Searching coding_brain for relevant patterns...
   Found 8 relevant code examples
Generating architectural design...
   Design v1 generated

📐 ARCHITECTURAL DESIGN DOCUMENT (v1)

# Real-Time Chat Application Architecture

## Overview
A WebSocket-based real-time chat application with...

[Design continues...]

Options:
  1. Provide feedback and refine the design
  2. Save design to file
  3. Exit

Your choice (1-3): 1

Provide your feedback:
> Make the architecture more modular
> Use Redis for message queuing
> Add authentication with JWT

Refining Design Based on Feedback...
   Design v2 generated

[Refined design shows...]
```

**How It Works:**

1. **Code Context Retrieval**: Searches your `coding_brain` collection for similar patterns and structures you've used before
2. **Preference Alignment**: Fetches your coding preferences (e.g., "Prefer functional programming," "Always use type hints")
3. **Design Generation**: Creates a detailed architecture using Gemini, guided by your existing code style
4. **Iterative Refinement**: You provide feedback, and the design is refined while maintaining consistency

**Generated Design Document Includes:**
- **Overview**: High-level system description
- **Architecture**: Component interactions and diagrams
- **Technology Stack**: Recommended technologies based on your existing stack
- **Data Model**: Key entities and relationships
- **API Design**: Endpoints and interfaces
- **Code Structure**: Directory and module organization matching your style
- **Implementation Plan**: Phased development approach

**Prerequisites:**
- Code ingestion completed (`python src/ingest_notes.py --code /path/to/your/codebase`)
- Coding preferences saved (optional, but enhances alignment)
- `GOOGLE_API_KEY` configured in `.env`

**Use Cases:**
- Designing new microservices within an existing system
- Planning architectural changes or refactoring
- Creating technical design documents for team review
- Exploring different architectural approaches aligned with your style
- Learning best practices from your own codebase

## Development Roadmap

### Phase 1: The "Librarian" (Knowledge Base)
- Ingest and index markdown/Notion notes
- Build vector search capabilities with ChromaDB
- Implement retrieval-augmented generation (RAG)
- Query interface with Gemini-powered synthesis

### Phase 2: The "Eyes" (Calendar Integration)
- Connect to Google Calendar (read-only)
- Query today's calendar events
- Query upcoming events (next N days)
- OAuth 2.0 authentication flow
- Detailed setup documentation

### Phase 3: The "Chief of Staff" (LangGraph Orchestration)
- Define agent state with TypedDict
- Create LangGraph workflow with three nodes:
  - check_schedule: Retrieve calendar events
  - consult_brain: Extract keywords and query knowledge base
  - draft_briefing: Generate personalized daily briefing
- Keyword extraction from calendar events
- Context-aware briefing generation
- End-to-end agent workflow

### Phase 4: The "Hands" (Email Drafting)
- Gmail API integration with OAuth 2.0
- Create draft emails (compose-only access)
- Intelligent email suggestion from briefings
- Automatic parsing and draft creation
- Safe draft-only mode (no automatic sending)
- Integration with LangGraph workflow

### Phase 5: The "Memory" (Long-Term User Preferences)
- User preference storage system
- Category-based preference organization
- Automatic preference injection into queries
- Preference management functions (save, list, delete, clear)
- JSON-based persistence in data/preferences.json
- Integration with brain.py query interface

### Phase 6: The "Architect" (Interactive Design Partner)
- Architect Session LangGraph workflow
- Code context retrieval from coding_brain collection
- Preference-aligned design generation
- Interactive refinement loop with feedback
- Comprehensive design document generation
- CLI interface with interactive and single-run modes
- Design versioning and history tracking
- Export designs to markdown files

### Phase 7: The "Future" (Advanced Automation)
- Automatic email sending with confirmation
- Task management integration (Todoist, Asana, etc.)
- Calendar event creation and modification
- Multi-day planning and scheduling
- Slack/Teams integration
- Meeting notes and summary generation
- Proactive "Shadow Mode" with weekly planning
- Recursive planning and goal alignment

## Technologies

- **LangGraph**: Orchestration framework for LLM workflows
- **ChromaDB**: Vector database for semantic search
- **HuggingFace Transformers**: Local embedding models (no API needed for ingestion!)
- **Google Gemini**: Fast, powerful LLM for answer synthesis
- **Google Calendar API**: Read-only calendar access for scheduling awareness
- **Gmail API**: Draft email creation (compose-only, safe mode)
- **LangChain**: Framework for building LLM applications

## Hybrid Approach: Local + Cloud

This project uses a smart hybrid approach:

### Local (Phase 1 - Ingestion)
**HuggingFace embeddings** run locally - no API needed
**Privacy** - Notes never leave your machine during indexing
**No costs** - Embeddings are free and offline
**Fast** - No network latency for vector generation

### Cloud (Phase 2+ - Querying)
**Gemini 2.0 Flash** for answer synthesis
**Fast responses** - Optimized for speed
**Smart context** - Only retrieved chunks are sent, not your entire knowledge base
**Accurate answers** - Powered by state-of-the-art LLM