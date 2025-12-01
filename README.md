# Second-Brain-Agent

An AI-powered "Chief of Staff" agent built with LangGraph, ChromaDB, and HuggingFace models. This agent serves as your personal second brain, helping you manage knowledge, calendar, and email.

**Key Feature**: Uses local HuggingFace embeddings - no API keys required for Phase 1!

## Project Structure

```
Second-Brain-Agent/
├── src/                    # Source code
│   ├── __init__.py
│   ├── config.py          # Configuration and environment variables
│   ├── state.py           # Agent state definition (TypedDict)
│   ├── graph.py           # LangGraph workflow and nodes
│   ├── main.py            # CLI interface (recommended entry point)
│   ├── ingest_notes.py    # Script to ingest and index notes
│   ├── brain.py           # Query interface for your second brain
│   └── tools/             # External service integrations
│       ├── __init__.py
│       ├── google_calendar.py  # Google Calendar integration
│       └── gmail.py            # Gmail integration (draft emails)
├── data/
│   ├── notes/             # Place your markdown/Notion notes here
│   └── chroma_db/         # ChromaDB vector store (auto-created)
├── chief_of_staff.py      # Simple runner script
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

### 5. Ingest Your Notes

Run the ingestion script to index your notes:

```bash
python src/ingest_notes.py
```

This will scan all `.md` and `.txt` files in `data/notes/`, chunk them, generate embeddings, and store them in ChromaDB.

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

### 7. (Optional) Set Up Google Calendar Integration

To give your agent the ability to see your schedule:

1. **Follow the setup guide**:
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

### 8. (Optional) Set Up Gmail Integration

To give your agent the ability to draft emails:

1. **Follow the setup guide**:
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

### 9. Run Your Chief of Staff Agent

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

### Phase 5: The "Future" (Advanced Automation)
- Automatic email sending with confirmation
- Task management integration (Todoist, Asana, etc.)
- Calendar event creation and modification
- Multi-day planning and scheduling
- Slack/Teams integration
- Meeting notes and summary generation

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
**Gemini 2.5 Flash** for answer synthesis
**Fast responses** - Optimized for speed
**Smart context** - Only retrieved chunks are sent, not your entire knowledge base
**Accurate answers** - Powered by state-of-the-art LLM
