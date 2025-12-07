"""
Second Brain Agent - Unified Streamlit Dashboard

A living, breathing interface that combines all agent modes:
- Architect: Job Description → TDD
- Dev Team: TDD → Code
- Chief of Staff: Daily briefings
- Brain Chat: Query your knowledge base
- Curator: Monitor repository discovery
"""

import streamlit as st
from pathlib import Path
import json
from datetime import datetime
import os
import sys

# Import agent functions
from src.agents.architect.graph import run_architect_session
from src.agents.dev_team.graph import run_dev_team_v2
from src.core.brain import query_second_brain
from src.utils.logger import setup_logger
from src.core.config import settings

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = setup_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Second Brain Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .mode-card {
        padding: 1.5rem;
        border-radius: 10px;
        background: #f8f9fa;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    .success-box {
        padding: 1rem;
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        color: #721c24;
    }
    .info-box {
        padding: 1rem;
        background: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        color: #0c5460;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'generated_tdd' not in st.session_state:
        st.session_state.generated_tdd = None
    
    if 'generated_code' not in st.session_state:
        st.session_state.generated_code = None
    
    if 'architect_running' not in st.session_state:
        st.session_state.architect_running = False
    
    if 'devteam_running' not in st.session_state:
        st.session_state.devteam_running = False
    
    if 'execution_results' not in st.session_state:
        st.session_state.execution_results = {}
    
    if 'curator_data' not in st.session_state:
        st.session_state.curator_data = None


def render_sidebar():
    """Render sidebar with mode selection and settings."""
    with st.sidebar:
        st.markdown("# 🧠 Second Brain")
        st.markdown("---")
        
        # Mode selection
        mode = st.radio(
            "Select Mode",
            ["🏠 Dashboard", "📐 Architect", "👨‍💻 Dev Team", "🎯 Chief of Staff", "💬 Brain Chat"],
            help="Choose which agent mode to use"
        )
        
        st.markdown("---")
        
        # Settings section
        with st.expander("⚙️ Settings", expanded=False):
            st.markdown("### Agent Configuration")
            
            # Model selection
            model_type = st.selectbox(
                "Model",
                ["gemini", "openai", "anthropic", "ollama"],
                index=0
            )
            
            # Temperature
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=0.7,
                step=0.1,
                help="Higher = more creative, Lower = more focused"
            )
            
            # Output directory
            output_dir = st.text_input(
                "Output Directory",
                value="./output",
                help="Where to save generated files"
            )
            
            # Execution settings
            st.markdown("### Execution Settings")
            execution_enabled = st.checkbox(
                "Enable Code Execution",
                value=True,
                help="Run generated code in Docker for validation"
            )
            
            self_healing = st.checkbox(
                "Enable Self-Healing",
                value=True,
                help="Automatically fix execution errors"
            )
            
            max_fix_attempts = st.number_input(
                "Max Fix Attempts",
                min_value=1,
                max_value=10,
                value=3,
                help="Maximum self-healing attempts"
            )
        
        st.markdown("---")
        
        # Status section
        with st.expander("📊 Status", expanded=True):
            # Check API keys
            api_keys_status = []
            if os.getenv("GOOGLE_API_KEY"):
                api_keys_status.append("✅ Google API")
            if os.getenv("OPENAI_API_KEY"):
                api_keys_status.append("✅ OpenAI API")
            
            if api_keys_status:
                st.success("API Keys:\n" + "\n".join(api_keys_status))
            else:
                st.warning("⚠️ No API keys configured")
            
            # Check data directories
            data_dir = Path("data")
            if data_dir.exists():
                notes_count = len(list((data_dir / "notes").glob("*.md"))) if (data_dir / "notes").exists() else 0
                st.info(f"📝 {notes_count} notes indexed")
            
            # Check output directory
            output_path = Path(output_dir)
            if output_path.exists():
                projects = len(list(output_path.iterdir()))
                st.info(f"📁 {projects} projects generated")
        
        return {
            'mode': mode,
            'model_type': model_type,
            'temperature': temperature,
            'output_dir': output_dir,
            'execution_enabled': execution_enabled,
            'self_healing': self_healing,
            'max_fix_attempts': max_fix_attempts
        }


def render_dashboard():
    """Render main dashboard overview."""
    st.markdown('<h1 class="main-header">🧠 Second Brain Agent</h1>', unsafe_allow_html=True)
    
    # Welcome message
    st.markdown("""
    ### Welcome to Your AI-Powered Development Assistant
    
    Transform job descriptions into working code, manage your daily workflow, 
    and leverage your accumulated knowledge base—all in one unified interface.
    """)
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Projects Generated", len(list(Path("output").iterdir())) if Path("output").exists() else 0)
    
    with col2:
        st.metric("Notes Indexed", len(list(Path("data/notes").glob("*.md"))) if Path("data/notes").exists() else 0)
    
    with col3:
        st.metric("Brain Queries", len(st.session_state.chat_history))
    
    with col4:
        # Check if curator has run
        curator_status = "Active" if st.session_state.curator_data else "Idle"
        st.metric("Curator Status", curator_status)
    
    st.markdown("---")
    
    # Recent activity
    st.markdown("### 📊 Recent Activity")
    
    tabs = st.tabs(["Generated Projects", "Chat History", "System Logs"])
    
    with tabs[0]:
        render_recent_projects()
    
    with tabs[1]:
        render_chat_history()
    
    with tabs[2]:
        render_system_logs()


def render_recent_projects():
    """Render list of recently generated projects."""
    output_dir = Path("output")
    
    if not output_dir.exists():
        st.info("No projects generated yet. Use Architect + Dev Team mode to create your first project!")
        return
    
    projects = sorted(output_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not projects:
        st.info("No projects found.")
        return
    
    for project in projects[:5]:  # Show last 5
        with st.expander(f"📁 {project.name}"):
            metadata_file = project / ".sba_metadata.json"
            
            if metadata_file.exists():
                metadata = json.loads(metadata_file.read_text())
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Created:** {metadata.get('created_at', 'Unknown')}")
                    st.markdown(f"**Files:** {len(metadata.get('components', []))}")
                
                with col2:
                    st.markdown(f"**Iteration:** {metadata.get('state_summary', {}).get('iteration_count', 1)}")
                    st.markdown(f"**Status:** {metadata.get('state_summary', {}).get('review_status', 'N/A')}")
            
            # Show file tree
            st.markdown("**File Structure:**")
            files = list(project.rglob("*"))
            for file in files[:10]:  # Limit to 10 files
                if file.is_file():
                    rel_path = file.relative_to(project)
                    st.text(f"  └─ {rel_path}")


def render_chat_history():
    """Render brain chat history."""
    if not st.session_state.chat_history:
        st.info("No chat history yet. Use Brain Chat mode to start asking questions!")
        return
    
    for i, chat in enumerate(reversed(st.session_state.chat_history[-10:])):  # Show last 10
        with st.expander(f"💬 {chat['query'][:50]}..."):
            st.markdown(f"**Query:** {chat['query']}")
            st.markdown(f"**Response:** {chat['response'][:300]}...")
            st.caption(f"Asked at: {chat.get('timestamp', 'Unknown')}")


def render_system_logs():
    """Render recent system logs."""
    log_file = Path("logs/app.log")
    
    if not log_file.exists():
        st.info("No logs available.")
        return
    
    # Read last 50 lines
    with open(log_file, 'r') as f:
        lines = f.readlines()[-50:]
    
    log_text = "".join(lines)
    st.code(log_text, language="log")


def main():
    """Main application entry point."""
    init_session_state()
    
    # Render sidebar and get settings
    config = render_sidebar()
    
    # Route to appropriate page based on mode
    if config['mode'] == "🏠 Dashboard":
        render_dashboard()
    
    elif config['mode'] == "📐 Architect":
        from src.ui.architect_page import render_architect_page
        render_architect_page(config)
    
    elif config['mode'] == "👨‍💻 Dev Team":
        from src.ui.devteam_page import render_devteam_page
        render_devteam_page(config)
    
    elif config['mode'] == "🎯 Chief of Staff":
        from src.ui.chief_page import render_chief_page
        render_chief_page(config)
    
    elif config['mode'] == "💬 Brain Chat":
        from src.ui.chat_page import render_chat_page
        render_chat_page(config)


if __name__ == "__main__":
    main()
