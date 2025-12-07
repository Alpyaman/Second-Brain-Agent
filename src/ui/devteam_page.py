"""Dev Team Mode UI Page - TDD → Code Generator with Self-Healing."""

import streamlit as st
from pathlib import Path
import tempfile
from datetime import datetime
import shutil

from src.agents.dev_team.graph import run_dev_team_v2
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def render_devteam_page(config: dict):
    """
    Render Dev Team mode page.
    
    Generate working code from TDD, with optional execution and self-healing.
    """
    st.markdown("# 👨‍💻 Dev Team Mode")
    st.markdown("Transform Technical Design Documents into working code")
    
    st.markdown("---")
    
    # TDD Input section
    st.markdown("### 📄 Input Technical Design Document")
    
    input_method = st.radio(
        "TDD Source",
        ["Use Generated TDD", "Upload TDD", "Load from docs/"],
        horizontal=True
    )
    
    tdd_content = ""
    tdd_source = ""
    
    if input_method == "Use Generated TDD":
        if st.session_state.generated_tdd:
            tdd_content = st.session_state.generated_tdd['content']
            tdd_source = f"From Architect ({st.session_state.generated_tdd['project_name']})"
            
            st.success(f"✅ Using TDD: {st.session_state.generated_tdd['project_name']}")
            
            # Show preview
            with st.expander("Preview TDD"):
                st.markdown(tdd_content[:500] + "...")
        else:
            st.warning("No TDD generated yet. Use Architect mode first or upload a TDD file.")
    
    elif input_method == "Upload TDD":
        uploaded_file = st.file_uploader(
            "Upload TDD file (.md)",
            type=['md']
        )
        
        if uploaded_file:
            tdd_content = uploaded_file.read().decode('utf-8')
            tdd_source = uploaded_file.name
            st.success(f"Loaded {len(tdd_content)} characters from {uploaded_file.name}")
    
    else:  # Load from docs/
        docs_dir = Path("docs")
        
        if docs_dir.exists():
            tdd_files = list(docs_dir.glob("*_tdd.md"))
            
            if tdd_files:
                selected_tdd = st.selectbox(
                    "Select TDD file",
                    tdd_files,
                    format_func=lambda x: x.name
                )
                
                if selected_tdd:
                    tdd_content = selected_tdd.read_text()
                    tdd_source = selected_tdd.name
                    st.success(f"Loaded: {selected_tdd.name}")
            else:
                st.warning("No TDD files found in docs/ directory")
        else:
            st.warning("docs/ directory not found")
    
    # Generation options
    st.markdown("### ⚙️ Code Generation Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        implementation_phase = st.selectbox(
            "Implementation Phase",
            [1, 2, 3],
            index=0,
            help="Phase 1: Core features, Phase 2: Extended, Phase 3: Advanced"
        )
    
    with col2:
        include_docker = st.checkbox(
            "Include Docker Config",
            value=True,
            help="Generate Dockerfile and docker-compose.yml"
        )
    
    with col3:
        include_tests = st.checkbox(
            "Include Tests",
            value=True,
            help="Generate test files"
        )
    
    # Execution options
    st.markdown("### 🔧 Execution & Self-Healing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        execution_enabled = st.checkbox(
            "Execute Generated Code",
            value=config['execution_enabled'],
            help="Run code in Docker to validate"
        )
    
    with col2:
        self_healing_enabled = st.checkbox(
            "Enable Self-Healing",
            value=config['self_healing'] and execution_enabled,
            disabled=not execution_enabled,
            help="Automatically fix execution errors"
        )
    
    if execution_enabled:
        max_fix_attempts = st.slider(
            "Max Self-Healing Attempts",
            min_value=1,
            max_value=5,
            value=config['max_fix_attempts'],
            help="Maximum attempts to fix errors"
        )
    else:
        max_fix_attempts = 0
    
    # Output directory
    output_dir = st.text_input(
        "Output Directory",
        value=config['output_dir'],
        help="Where to save generated project"
    )
    
    # Generate button
    st.markdown("---")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col2:
        generate_button = st.button(
            "🚀 Generate Code",
            type="primary",
            use_container_width=True,
            disabled=not tdd_content or st.session_state.devteam_running
        )
    
    # Code generation logic
    if generate_button and tdd_content:
        st.session_state.devteam_running = True
        
        with st.spinner("👨‍💻 Dev Team agents are working..."):
            try:
                # Create output directory
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                
                # Progress tracking
                progress_container = st.container()
                
                with progress_container:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("📋 Parsing TDD...")
                    progress_bar.progress(10)
                    
                    # Save TDD to temporary file
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                        f.write(tdd_content)
                        tdd_file_path = f.name
                    
                    try:
                        status_text.text("👥 Tech Lead analyzing requirements...")
                        progress_bar.progress(20)
                        
                        # Run dev team
                        result = run_dev_team_v2(
                            tdd_file=tdd_file_path,
                            output_dir=str(output_path),
                            implementation_phase=implementation_phase,
                            include_docker=include_docker,
                            include_tests=include_tests,
                            execution_enabled=execution_enabled,
                            self_healing_enabled=self_healing_enabled,
                            max_fix_attempts=max_fix_attempts
                        )
                        
                        status_text.text("💻 Generating code...")
                        progress_bar.progress(60)
                        
                        # Check for execution results
                        if execution_enabled and result.get('execution_results'):
                            status_text.text("🔧 Executing and validating code...")
                            progress_bar.progress(80)
                            
                            st.session_state.execution_results = result['execution_results']
                        
                        progress_bar.progress(100)
                        status_text.text("✅ Code generation complete!")
                        
                        # Store results
                        st.session_state.generated_code = {
                            'output_dir': str(output_path),
                            'timestamp': datetime.now().isoformat(),
                            'tdd_source': tdd_source,
                            'phase': implementation_phase,
                            'files_generated': result.get('files_written', 0),
                            'execution_enabled': execution_enabled,
                            'execution_results': result.get('execution_results', {})
                        }
                        
                        st.success("🎉 Code generated successfully!")
                        
                    finally:
                        # Clean up temp file
                        Path(tdd_file_path).unlink(missing_ok=True)
            
            except Exception as e:
                logger.error(f"Error generating code: {e}")
                st.error(f"❌ Error: {str(e)}")
            
            finally:
                st.session_state.devteam_running = False
    
    # Display results
    if st.session_state.generated_code:
        st.markdown("---")
        st.markdown("### 📦 Generated Project")
        
        code_data = st.session_state.generated_code
        
        # Metadata
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Files Generated", code_data.get('files_generated', 0))
        with col2:
            st.metric("Phase", code_data.get('phase', 1))
        with col3:
            st.metric("Location", "output/")
        with col4:
            execution_status = "✅ Executed" if code_data.get('execution_enabled') else "⏭️ Skipped"
            st.metric("Execution", execution_status)
        
        # Tabs for different views
        tabs = st.tabs(["📂 File Browser", "🔧 Execution Results", "📊 Project Stats", "💾 Export"])
        
        with tabs[0]:
            render_file_browser(code_data['output_dir'])
        
        with tabs[1]:
            if code_data.get('execution_results'):
                render_execution_results(code_data['execution_results'])
            else:
                st.info("Code execution was not enabled for this generation.")
        
        with tabs[2]:
            render_project_stats(code_data['output_dir'])
        
        with tabs[3]:
            render_export_options(code_data['output_dir'])


def render_file_browser(output_dir: str):
    """Render file browser for generated project."""
    project_path = Path(output_dir)
    
    if not project_path.exists():
        st.warning("Project directory not found")
        return
    
    st.markdown("**Project Structure:**")
    
    # Get all files
    all_files = sorted(project_path.rglob("*"))
    files = [f for f in all_files if f.is_file() and not f.name.startswith('.')]
    
    # Group by directory
    directories = {}
    for file in files:
        rel_path = file.relative_to(project_path)
        dir_name = str(rel_path.parent) if rel_path.parent != Path('.') else "Root"
        
        if dir_name not in directories:
            directories[dir_name] = []
        directories[dir_name].append(file)
    
    # Display by directory
    for dir_name, dir_files in sorted(directories.items()):
        with st.expander(f"📁 {dir_name} ({len(dir_files)} files)"):
            for file in dir_files:
                rel_path = file.relative_to(project_path)
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    if st.button(f"📄 {rel_path}", key=f"view_{rel_path}"):
                        # Show file content
                        content = file.read_text()
                        st.code(content, language=file.suffix[1:] if file.suffix else 'text')
                
                with col2:
                    st.caption(f"{file.stat().st_size} bytes")


def render_execution_results(execution_results: dict):
    """Render execution results with errors and fixes."""
    st.markdown("**Code Execution Results:**")
    
    if not execution_results:
        st.info("No execution results available.")
        return
    
    # Summary
    total = len(execution_results)
    successful = sum(1 for r in execution_results.values() if r.get('success', False))
    failed = total - successful
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Files", total)
    with col2:
        st.metric("Successful", successful, delta=successful - failed if successful > failed else None)
    with col3:
        st.metric("Failed", failed, delta=failed - successful if failed > successful else None)
    
    # Detailed results
    st.markdown("---")
    
    for filepath, result in execution_results.items():
        success = result.get('success', False)
        icon = "✅" if success else "❌"
        
        with st.expander(f"{icon} {filepath}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Exit Code:** {result.get('exit_code', 'N/A')}")
                st.markdown(f"**Execution Time:** {result.get('execution_time', 0):.2f}s")
            
            with col2:
                st.markdown(f"**Status:** {'Success' if success else 'Failed'}")
                st.markdown(f"**Errors:** {len(result.get('errors', []))}")
            
            # Stdout
            if result.get('stdout'):
                st.markdown("**Output:**")
                st.code(result['stdout'], language='text')
            
            # Stderr/Errors
            if result.get('errors'):
                st.markdown("**Errors:**")
                for error in result['errors']:
                    st.error(error)
            
            # Warnings
            if result.get('warnings'):
                st.markdown("**Warnings:**")
                for warning in result['warnings']:
                    st.warning(warning)


def render_project_stats(output_dir: str):
    """Render project statistics."""
    project_path = Path(output_dir)
    
    if not project_path.exists():
        st.warning("Project directory not found")
        return
    
    # Count files by type
    file_types = {}
    total_lines = 0
    total_size = 0
    
    for file in project_path.rglob("*"):
        if file.is_file() and not file.name.startswith('.'):
            ext = file.suffix or 'no extension'
            file_types[ext] = file_types.get(ext, 0) + 1
            
            total_size += file.stat().st_size
            
            # Count lines for text files
            if ext in ['.py', '.js', '.ts', '.tsx', '.jsx', '.md', '.txt', '.yml', '.yaml', '.json']:
                try:
                    lines = len(file.read_text().splitlines())
                    total_lines += lines
                except Exception as e:
                    st.warning(f"Could not read {file}: {e}")
                    pass
    
    # Display stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Files", sum(file_types.values()))
    
    with col2:
        st.metric("Lines of Code", f"{total_lines:,}")
    
    with col3:
        st.metric("Total Size", f"{total_size / 1024:.1f} KB")
    
    st.markdown("---")
    st.markdown("**Files by Type:**")
    
    # Chart of file types
    import pandas as pd
    
    df = pd.DataFrame(list(file_types.items()), columns=['Extension', 'Count'])
    df = df.sort_values('Count', ascending=False)
    
    st.bar_chart(df.set_index('Extension'))


def render_export_options(output_dir: str):
    """Render export and deployment options."""
    project_path = Path(output_dir)
    
    if not project_path.exists():
        st.warning("Project directory not found")
        return
    
    st.markdown("### 📦 Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Download Project:**")
        
        if st.button("💾 Create ZIP Archive"):
            with st.spinner("Creating archive..."):
                # Create ZIP file
                zip_path = Path(tempfile.gettempdir()) / f"{project_path.name}.zip"
                
                shutil.make_archive(
                    str(zip_path.with_suffix('')),
                    'zip',
                    project_path
                )
                
                if zip_path.exists():
                    with open(zip_path, 'rb') as f:
                        st.download_button(
                            label="📥 Download ZIP",
                            data=f.read(),
                            file_name=zip_path.name,
                            mime="application/zip"
                        )
    
    with col2:
        st.markdown("**Quick Actions:**")
        
        if st.button("📂 Open in File Explorer"):
            st.info(f"Project location: {project_path.absolute()}")
        
        if st.button("🐳 Show Docker Commands"):
            st.code(f"""# Navigate to project
cd {project_path.absolute()}

# Build and run with Docker
docker-compose up --build

# Or run backend only
cd backend
docker build -t {project_path.name}-backend .
docker run -p 8000:8000 {project_path.name}-backend
""", language='bash')
