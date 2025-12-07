"""Architect Mode UI Page - Job Description → TDD Generator."""

import streamlit as st
from pathlib import Path
import tempfile
from datetime import datetime

from src.agents.architect.graph import run_architect_session
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def render_architect_page(config: dict):
    """
    Render Architect mode page.
    
    Allows users to input job descriptions and generate Technical Design Documents.
    """
    st.markdown("# 📐 Architect Mode")
    st.markdown("Transform job descriptions into professional Technical Design Documents")
    
    st.markdown("---")
    
    # Input section
    st.markdown("### 📝 Input Job Description")
    
    input_method = st.radio(
        "Input Method",
        ["Text Input", "File Upload", "Load Example"],
        horizontal=True
    )
    
    job_description = ""
    
    if input_method == "Text Input":
        job_description = st.text_area(
            "Paste your job description here",
            height=300,
            placeholder="""Example:
Build a REST API for a task management system with user authentication, 
task CRUD operations, and real-time notifications. Use FastAPI, PostgreSQL, 
and implement JWT authentication."""
        )
    
    elif input_method == "File Upload":
        uploaded_file = st.file_uploader(
            "Upload job description (.txt or .md)",
            type=['txt', 'md']
        )
        
        if uploaded_file:
            job_description = uploaded_file.read().decode('utf-8')
            st.success(f"Loaded {len(job_description)} characters from {uploaded_file.name}")
    
    else:  # Load Example
        examples_dir = Path("examples")
        
        if examples_dir.exists():
            example_files = list(examples_dir.glob("*.txt"))
            
            if example_files:
                selected_example = st.selectbox(
                    "Select an example",
                    example_files,
                    format_func=lambda x: x.name
                )
                
                if selected_example:
                    job_description = selected_example.read_text()
                    st.info(f"Loaded example: {selected_example.name}")
            else:
                st.warning("No example files found in examples/ directory")
        else:
            st.warning("examples/ directory not found")
    
    # Generation options
    st.markdown("### ⚙️ Generation Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        project_name = st.text_input(
            "Project Name",
            value="my-project",
            help="Name for the generated project"
        )
        
        interactive_mode = st.checkbox(
            "Interactive Mode",
            value=False,
            help="Pause for feedback during generation"
        )
    
    with col2:
        target_complexity = st.selectbox(
            "Target Complexity",
            ["Simple", "Moderate", "Complex"],
            index=1,
            help="Complexity level of the TDD"
        )
        
        include_diagrams = st.checkbox(
            "Include Diagrams",
            value=True,
            help="Generate architecture diagrams"
        )
    
    # Generate button
    st.markdown("---")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col2:
        generate_button = st.button(
            "🚀 Generate TDD",
            type="primary",
            use_container_width=True,
            disabled=not job_description or st.session_state.architect_running
        )
    
    # Generation logic
    if generate_button and job_description:
        st.session_state.architect_running = True
        
        with st.spinner("🤖 Architect agent is working..."):
            try:
                # Create temporary directory for output
                with tempfile.TemporaryDirectory() as temp_dir:
                    output_file = Path(temp_dir) / f"{project_name}_tdd.md"
                    
                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("Analyzing job description...")
                    progress_bar.progress(20)
                    
                    # Run architect session
                    result = run_architect_session(
                        job_description=job_description,
                        interactive=interactive_mode,
                        output_file=str(output_file)
                    )
                    
                    status_text.text("Generating TDD...")
                    progress_bar.progress(60)
                    
                    # Read generated TDD
                    if output_file.exists():
                        tdd_content = output_file.read_text()
                        st.session_state.generated_tdd = {
                            'content': tdd_content,
                            'project_name': project_name,
                            'timestamp': datetime.now().isoformat(),
                            'job_description': job_description
                        }
                        
                        progress_bar.progress(100)
                        status_text.text("✅ TDD generated successfully!")
                        
                        st.success("🎉 Technical Design Document generated successfully!")
                    else:
                        st.error("Failed to generate TDD - output file not found")
            
            except Exception as e:
                logger.error(f"Error generating TDD: {e}")
                st.error(f"❌ Error: {str(e)}")
            
            finally:
                st.session_state.architect_running = False
    
    # Display generated TDD
    if st.session_state.generated_tdd:
        st.markdown("---")
        st.markdown("### 📄 Generated Technical Design Document")
        
        tdd_data = st.session_state.generated_tdd
        
        # Metadata
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Project", tdd_data['project_name'])
        with col2:
            st.metric("Size", f"{len(tdd_data['content'])} chars")
        with col3:
            st.metric("Generated", tdd_data['timestamp'][:19])
        
        # TDD content
        tabs = st.tabs(["📖 Preview", "📝 Markdown", "💾 Export"])
        
        with tabs[0]:
            # Render markdown preview
            st.markdown(tdd_data['content'])
        
        with tabs[1]:
            # Show raw markdown
            st.code(tdd_data['content'], language='markdown')
        
        with tabs[2]:
            # Export options
            st.markdown("**Download Options:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="📥 Download Markdown",
                    data=tdd_data['content'],
                    file_name=f"{tdd_data['project_name']}_tdd.md",
                    mime="text/markdown"
                )
            
            with col2:
                # Save to docs directory
                if st.button("💾 Save to docs/"):
                    docs_dir = Path("docs")
                    docs_dir.mkdir(exist_ok=True)
                    
                    output_path = docs_dir / f"{tdd_data['project_name']}_tdd.md"
                    output_path.write_text(tdd_data['content'])
                    
                    st.success(f"✅ Saved to {output_path}")
            
            st.markdown("---")
            
            # Quick action: Go to Dev Team
            if st.button("➡️ Generate Code from this TDD", type="primary"):
                st.info("Switch to Dev Team mode in the sidebar to generate code!")
