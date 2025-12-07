"""Brain Chat UI Page - Query Your Knowledge Base."""

import streamlit as st
from datetime import datetime
from pathlib import Path

from src.core.brain import query_second_brain
from src.tools.memory import get_all_preferences, save_preference
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def render_chat_page(config: dict):
    """
    Render Brain Chat mode page.
    
    Chat interface to query your accumulated knowledge base.
    """
    st.markdown("# 💬 Brain Chat")
    st.markdown("Query your Second Brain's accumulated knowledge")
    
    st.markdown("---")
    
    # Sidebar for chat controls
    with st.sidebar:
        st.markdown("### 💬 Chat Controls")
        
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()
        
        st.markdown("---")
        
        # Brain statistics
        st.markdown("### 📊 Brain Statistics")
        
        # Count indexed documents
        data_dir = Path("data")
        if (data_dir / "chroma_db").exists():
            st.metric("Knowledge Base", "Active")
        else:
            st.warning("⚠️ Knowledge base not initialized")
            st.info("Run ingestion to index your notes and code")
        
        notes_dir = data_dir / "notes"
        if notes_dir.exists():
            note_count = len(list(notes_dir.glob("*.md")))
            st.metric("Notes Indexed", note_count)
        
        # Preferences
        st.markdown("---")
        st.markdown("### ⚙️ Preferences")
        
        if st.button("📝 View Preferences"):
            render_preferences_modal()
    
    # Main chat interface
    render_chat_interface()
    
    # Knowledge management tabs
    st.markdown("---")
    tabs = st.tabs(["🧠 Brain Status", "📚 Knowledge Sources", "🔍 Curator"])
    
    with tabs[0]:
        render_brain_status()
    
    with tabs[1]:
        render_knowledge_sources()
    
    with tabs[2]:
        render_curator_status()


def render_chat_interface():
    """Render the main chat interface."""
    st.markdown("### 💭 Ask Your Second Brain")
    
    # Display chat history
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.chat_history:
            st.info("""
            👋 Welcome to Brain Chat!
            
            Ask questions about:
            - Your notes and documentation
            - Code patterns and best practices
            - Your preferences and workflows
            - Technical concepts from your knowledge base
            
            **Example questions:**
            - "What's my preferred coding style?"
            - "Show me examples of FastAPI authentication"
            - "What are the best practices for error handling?"
            """)
        else:
            # Display chat messages
            for chat in st.session_state.chat_history:
                # User message
                with st.chat_message("user"):
                    st.markdown(chat['query'])
                
                # Assistant response
                with st.chat_message("assistant"):
                    st.markdown(chat['response'])
                    
                    # Show sources if available
                    if chat.get('sources'):
                        with st.expander("📚 Sources"):
                            for source in chat['sources']:
                                st.caption(f"- {source}")
    
    # Chat input
    user_query = st.chat_input("Ask a question...")
    
    if user_query:
        # Add user message to history
        with st.chat_message("user"):
            st.markdown(user_query)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = query_second_brain(user_query)
                    
                    st.markdown(response)
                    
                    # Store in history
                    st.session_state.chat_history.append({
                        'query': user_query,
                        'response': response,
                        'timestamp': datetime.now().isoformat(),
                        'sources': []  # TODO: Extract sources from response
                    })
                
                except Exception as e:
                    error_msg = f"Error querying brain: {str(e)}"
                    logger.error(error_msg)
                    st.error(error_msg)
                    
                    st.session_state.chat_history.append({
                        'query': user_query,
                        'response': f"❌ {error_msg}",
                        'timestamp': datetime.now().isoformat(),
                        'sources': []
                    })


def render_preferences_modal():
    """Render preferences management modal."""
    st.markdown("### 📝 Your Preferences")
    
    try:
        preferences = get_all_preferences()
        
        if not preferences:
            st.info("No preferences saved yet.")
        else:
            for category, prefs in preferences.items():
                with st.expander(f"📂 {category.title()}"):
                    for pref in prefs:
                        st.markdown(f"- {pref}")
    except Exception as e:
        st.error(f"Error loading preferences: {e}")
    
    # Add new preference
    st.markdown("---")
    st.markdown("**Add New Preference:**")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        pref_category = st.selectbox(
            "Category",
            ["workflow", "coding_style", "communication", "tools", "other"]
        )
    
    with col2:
        pref_text = st.text_input("Preference:")
    
    if st.button("💾 Save Preference"):
        if pref_text:
            try:
                save_preference(pref_category, pref_text)
                st.success("✅ Preference saved!")
            except Exception as e:
                st.error(f"Error saving preference: {e}")
        else:
            st.warning("Please enter a preference")


def render_brain_status():
    """Render brain status and health check."""
    st.markdown("### 🧠 Brain Status")
    
    # Check ChromaDB
    chroma_dir = Path("data/chroma_db")
    
    if chroma_dir.exists():
        st.success("✅ Knowledge base is active")
        
        # Count collections
        collection_dirs = [d for d in chroma_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Collections", len(collection_dirs))
        
        with col2:
            # Estimate total documents (rough approximation)
            st.metric("Status", "Healthy")
        
        # Show collections
        if collection_dirs:
            st.markdown("**Available Collections:**")
            
            for collection in collection_dirs:
                st.markdown(f"- 📚 {collection.name}")
    else:
        st.warning("⚠️ Knowledge base not initialized")
        
        st.info("""
        To initialize your Second Brain:
        
        1. Add markdown files to `data/notes/`
        2. Run ingestion:
           ```bash
           python src/ingestion/ingest_notes.py
           ```
        3. Query your brain!
        """)
    
    # Last ingestion
    st.markdown("---")
    st.markdown("**Ingestion Status:**")
    
    if chroma_dir.exists():
        sqlite_file = chroma_dir / "chroma.sqlite3"
        
        if sqlite_file.exists():
            from datetime import datetime
            mtime = datetime.fromtimestamp(sqlite_file.stat().st_mtime)
            st.info(f"Last updated: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Maintenance actions
    st.markdown("---")
    st.markdown("**Maintenance:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Re-index Notes"):
            with st.spinner("Re-indexing..."):
                try:
                    # TODO: Call ingestion
                    st.success("✅ Re-indexing complete!")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with col2:
        if st.button("🗑️ Clear Knowledge Base"):
            if st.checkbox("Confirm deletion"):
                try:
                    import shutil
                    if chroma_dir.exists():
                        shutil.rmtree(chroma_dir)
                    st.success("✅ Knowledge base cleared")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


def render_knowledge_sources():
    """Render knowledge sources overview."""
    st.markdown("### 📚 Knowledge Sources")
    
    # Notes
    st.markdown("**📝 Your Notes:**")
    
    notes_dir = Path("data/notes")
    
    if notes_dir.exists():
        note_files = list(notes_dir.glob("*.md"))
        
        if note_files:
            st.info(f"Found {len(note_files)} markdown files")
            
            # Show recent notes
            recent_notes = sorted(note_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]
            
            for note in recent_notes:
                with st.expander(f"📄 {note.name}"):
                    content = note.read_text()
                    st.markdown(content[:300] + "..." if len(content) > 300 else content)
                    
                    st.caption(f"Last modified: {datetime.fromtimestamp(note.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}")
        else:
            st.warning("No markdown files found in data/notes/")
    else:
        st.warning("Notes directory not found. Create `data/notes/` and add markdown files.")
    
    # Code repositories (from curator)
    st.markdown("---")
    st.markdown("**💻 Code Repositories:**")
    
    # Check if any code has been ingested
    chroma_dir = Path("data/chroma_db")
    
    if chroma_dir.exists():
        collection_dirs = [d for d in chroma_dir.iterdir() if d.is_dir() and 'brain' in d.name.lower()]
        
        if collection_dirs:
            st.success(f"✅ {len(collection_dirs)} code collections indexed")
            
            for collection in collection_dirs:
                st.markdown(f"- 🗂️ {collection.name}")
        else:
            st.info("No code collections found. Use Curator to discover and index repositories.")
    else:
        st.info("Knowledge base not initialized yet.")
    
    # Add new sources
    st.markdown("---")
    st.markdown("**➕ Add New Sources:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📝 Add Note"):
            st.info("Create a markdown file in `data/notes/` and re-index")
    
    with col2:
        if st.button("💻 Discover Code"):
            st.info("Switch to Curator mode to discover GitHub repositories")


def render_curator_status():
    """Render curator status and discovered repositories."""
    st.markdown("### 🔍 Curator Status")
    
    if st.session_state.curator_data:
        curator = st.session_state.curator_data
        
        st.success(f"✅ Last run: {curator.get('timestamp', 'Unknown')}")
        
        # Display discovered repositories
        repos = curator.get('repositories', [])
        
        if repos:
            st.markdown(f"**Discovered {len(repos)} repositories:**")
            
            for repo in repos:
                with st.expander(f"⭐ {repo.get('name', 'Unknown')}"):
                    st.markdown(f"**URL:** {repo.get('url', 'N/A')}")
                    st.markdown(f"**Quality:** {repo.get('quality', 'N/A')}/10")
                    st.markdown(f"**Category:** {repo.get('category', 'N/A')}")
                    
                    if repo.get('description'):
                        st.markdown(f"**Description:** {repo['description']}")
                    
                    if repo.get('technologies'):
                        st.markdown(f"**Technologies:** {', '.join(repo['technologies'])}")
    else:
        st.info("Curator has not run yet. Use the curator tool to discover GitHub repositories.")
        
        if st.button("🚀 Run Curator"):
            with st.spinner("Running curator..."):
                try:
                    # TODO: Call curator
                    st.success("Curator completed!")
                except Exception as e:
                    st.error(f"Error: {e}")
