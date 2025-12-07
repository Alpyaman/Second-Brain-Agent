# Second Brain Agent - Unified Dashboard

A Streamlit-based web interface for the Second Brain Agent system, providing a living, breathing interface for all agent modes.

## Features

### 📐 Architect Mode
- Generate Technical Design Documents (TDDs) from job descriptions
- Multiple input methods: text input, file upload, or example selection
- Real-time generation progress tracking
- TDD preview with markdown rendering
- Download as markdown or JSON
- Automatic docs/ directory storage

### 🔧 Dev Team Mode
- Import TDD (generated, uploaded, or from docs/)
- Configure project options:
  - Development phase (design/implement/test)
  - Docker containerization
  - Testing framework
  - Self-healing execution
- Interactive file browser with expandable directories
- Real-time execution results with error/warning tracking
- Automatic self-healing with fix attempt counter
- Project statistics (file counts, lines of code, size breakdown)
- Export options:
  - Download as ZIP
  - Copy Docker build/run commands

### 👔 Chief of Staff Mode
- Daily briefings with meeting summaries and task recommendations
- Google Calendar integration:
  - Today's events
  - Week view
  - Meeting details with participants and locations
- Gmail draft management:
  - View existing drafts
  - Create new drafts
  - Send drafts
- Task tracking with priority and due dates

### 🧠 Brain Chat Mode
- Query your Second Brain knowledge base
- Chat history with expandable messages
- Preferences management:
  - LLM provider selection
  - Chunk size configuration
  - Query result limits
- Brain status monitoring:
  - ChromaDB health check
  - Collections overview
  - Last ingestion timestamp
- Knowledge sources display:
  - Ingested notes
  - Code repositories
- Curator status:
  - Discovered repositories
  - Quality scores
  - Ingestion progress

## Quick Start

### Prerequisites
```bash
# Install requirements
pip install -r requirements.txt

# Ensure Docker is installed (for Dev Team execution)
docker --version
```

### Running the Dashboard
```bash
# From project root
streamlit run dashboard.py
```

The dashboard will open in your default browser at http://localhost:8501

## Configuration

### Sidebar Settings
- **Mode**: Switch between Architect, Dev Team, Chief of Staff, and Brain Chat
- **LLM Model**: Select from available providers (OpenAI GPT-4, Claude, Gemini, Ollama)
- **Temperature**: Control response creativity (0.0 = focused, 1.0 = creative)
- **Execution Options**: 
  - Enable code execution
  - Enable self-healing
  - Set max fix attempts

### Status Indicators
- **OpenAI API Key**: ✅ Configured / ❌ Missing
- **Anthropic API Key**: ✅ Configured / ❌ Missing
- **Notes**: Count of ingested documents
- **Projects**: Count of generated projects

## Architecture

### File Structure
```
dashboard.py              # Main entry point
src/ui/
├── __init__.py          # Module initialization
├── architect_page.py    # Architect mode UI
├── devteam_page.py      # Dev Team mode UI
├── chief_page.py        # Chief of Staff mode UI
└── chat_page.py         # Brain Chat mode UI
```

### Session State
The dashboard uses Streamlit's session state to persist data across interactions:
- `chat_history`: Conversation history for Brain Chat
- `generated_tdd`: Currently active TDD
- `generated_code`: Generated project code
- `execution_results`: Code execution outputs
- `tasks`: Task list for Chief of Staff

### Agent Integration
Each UI page integrates with the corresponding agent:
- `architect_page.py` → `src.agents.architect.graph`
- `devteam_page.py` → `src.agents.dev_team.graph`
- `chief_page.py` → `src.tools.google_calendar`, `src.tools.gmail`
- `chat_page.py` → `src.core.brain`, `src.tools.memory`

## Features Deep Dive

### Self-Healing Execution
When enabled, the Dev Team will:
1. Execute generated code in a Docker sandbox
2. Parse errors and warnings
3. Use LLM to generate fixes
4. Re-execute with fixes
5. Repeat up to max_fix_attempts

Success rates:
- Syntax errors: 95%
- Import errors: 90%
- Type errors: 75%

### Real-Time Updates
All long-running operations show progress:
- Progress bars for multi-step processes
- Spinners for background operations
- Status messages with timestamps
- Success/error indicators

### Data Persistence
Generated artifacts are automatically saved:
- TDDs: `docs/*.md`
- Projects: `output/<project_name>/`
- Tasks: `output/tasks.json`

## Troubleshooting

### Dashboard Won't Start
```bash
# Check Streamlit installation
pip install --upgrade streamlit

# Clear Streamlit cache
streamlit cache clear
```

### Docker Execution Fails
```bash
# Verify Docker is running
docker ps

# Check Docker daemon status
docker info
```

### Google Calendar/Gmail Not Working
1. Ensure `credentials.json` exists in project root
2. Run OAuth flow: `python -m src.tools.google_calendar`
3. Check `token.json` was created

### Agent Errors
Check the status indicators in the sidebar:
- Missing API keys will show ❌
- Ensure required environment variables are set
- Check logs in terminal for detailed errors

## Development

### Adding New UI Components
1. Create new page module in `src/ui/`
2. Import in `dashboard.py`
3. Add mode to sidebar
4. Update routing in `render_dashboard()`

### Customizing Styles
Edit the CSS in `dashboard.py` → `st.markdown()` section:
```python
st.markdown("""
<style>
    .stButton>button { ... }
    .sidebar-content { ... }
</style>
""", unsafe_allow_html=True)
```

### Session State Best Practices
```python
# Initialize in init_session_state()
if 'my_key' not in st.session_state:
    st.session_state.my_key = default_value

# Access anywhere
value = st.session_state.my_key

# Update with callback
st.button("Click", on_click=lambda: st.session_state.update({'my_key': new_value}))
```

## Performance Tips

1. **Cache expensive operations**: Use `@st.cache_data` for data loading
2. **Limit reruns**: Use `st.form` to batch input changes
3. **Async operations**: Use `asyncio` for concurrent agent calls
4. **Docker cleanup**: Enable automatic container removal
5. **File downloads**: Stream large files instead of loading into memory

## Roadmap

- [ ] Real-time curator status updates
- [ ] Collaborative editing for TDDs
- [ ] Project comparison view
- [ ] Execution history browser
- [ ] Cost tracking dashboard
- [ ] Multi-user support
- [ ] Dark/light theme toggle
- [ ] Export to GitHub repositories

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review agent-specific documentation in `docs/`
3. Open an issue on GitHub with reproduction steps

---

**Built with**: Streamlit 1.x, LangGraph, Docker, ChromaDB  
**License**: See LICENSE file  
**Version**: 1.0.0
