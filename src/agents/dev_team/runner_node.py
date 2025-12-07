"""
Self-Healing Code Runner Node for Dev Team Agent.

This module implements the "Runner Node" that executes generated code
in Docker containers and provides feedback for automatic error correction.
"""

from typing import Dict, List, Any
from pathlib import Path
import tempfile

from src.agents.dev_team.state import DevTeamState
from src.utils.code_runner import DockerCodeRunner
from src.utils.logger import setup_logger
from src.core.llm_factory import create_llm

logger = setup_logger(__name__)


class CodeExecutionNode:
    """Execute generated code and provide feedback for self-healing."""
    
    def __init__(
        self,
        max_fix_attempts: int = 3,
        execution_timeout: int = 30
    ):
        """
        Initialize code execution node.
        
        Args:
            max_fix_attempts: Maximum number of auto-fix attempts
            execution_timeout: Timeout for code execution in seconds
        """
        self.max_fix_attempts = max_fix_attempts
        self.runner = DockerCodeRunner(timeout=execution_timeout)
        self.llm = create_llm()
        logger.info(f"CodeExecutionNode initialized (max_attempts={max_fix_attempts})")
    
    def __call__(self, state: DevTeamState) -> DevTeamState:
        """
        Execute generated code and update state with results.
        
        Args:
            state: Current dev team state
            
        Returns:
            Updated state with execution results
        """
        if not state.get('execution_enabled', False):
            logger.info("Execution disabled, skipping runner node")
            return state
        
        if not self.runner.docker_available:
            logger.warning("Docker not available, skipping execution")
            state['execution_errors'] = {
                'system': ['Docker not available on this system']
            }
            return state
        
        logger.info("=== Starting Code Execution Phase ===")
        
        # Initialize execution tracking
        state['execution_results'] = state.get('execution_results', {})
        state['execution_errors'] = state.get('execution_errors', {})
        state['fix_attempts'] = state.get('fix_attempts', {})
        state['max_fix_attempts'] = self.max_fix_attempts
        
        # Execute backend code
        if state.get('backend_files'):
            self._execute_backend_files(state)
        
        # Execute frontend code (if applicable)
        if state.get('frontend_files'):
            self._execute_frontend_files(state)
        
        # Log summary
        self._log_execution_summary(state)
        
        # Check if any files need fixing
        needs_fixing = self._needs_self_healing(state)
        state['needs_revision'] = needs_fixing
        
        logger.info(f"=== Execution Phase Complete (needs_revision={needs_fixing}) ===")
        
        return state
    
    def _execute_backend_files(self, state: DevTeamState) -> None:
        """Execute backend Python files."""
        backend_files = state['backend_files']
        
        # Create temporary directory for execution
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write all backend files
            for filepath, content in backend_files.items():
                file_path = temp_path / filepath
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding='utf-8')
            
            # Identify entry points (main files)
            entry_points = self._identify_entry_points(backend_files)
            
            # Execute each entry point
            for entry_point in entry_points:
                self._execute_file(
                    state,
                    entry_point,
                    temp_path / entry_point,
                    file_type='backend'
                )
    
    def _execute_frontend_files(self, state: DevTeamState) -> None:
        """Execute frontend JavaScript/TypeScript files if possible."""
        # For now, focus on Python backend execution
        # Frontend execution would require Node.js Docker image
        logger.info("Frontend execution not yet implemented, skipping")
        pass
    
    def _identify_entry_points(self, files: Dict[str, str]) -> List[str]:
        """Identify which files are entry points (executable)."""
        entry_points = []
        
        for filepath in files.keys():
            filename = Path(filepath).name
            
            # Main files
            if filename in ['main.py', 'app.py', 'run.py', '__main__.py']:
                entry_points.append(filepath)
                continue
            
            # Files with if __name__ == '__main__'
            content = files[filepath]
            if '__name__' in content and '__main__' in content:
                entry_points.append(filepath)
        
        # If no entry points found, try any .py file in root
        if not entry_points:
            for filepath in files.keys():
                if '/' not in filepath and filepath.endswith('.py'):
                    entry_points.append(filepath)
                    break
        
        logger.info(f"Identified {len(entry_points)} entry points: {entry_points}")
        return entry_points
    
    def _execute_file(
        self,
        state: DevTeamState,
        filepath: str,
        file_path: Path,
        file_type: str = 'backend'
    ) -> None:
        """
        Execute a single file and store results.
        
        Args:
            state: Current state
            filepath: Relative filepath (for state tracking)
            file_path: Absolute path to file
            file_type: Type of file (backend/frontend)
        """
        logger.info(f"Executing: {filepath}")
        
        # Extract dependencies from requirements if available
        dependencies = self._extract_dependencies(state, file_type)
        
        # Execute file
        result = self.runner.execute_python_file(
            file_path,
            dependencies=dependencies
        )
        
        # Store results
        state['execution_results'][filepath] = {
            'success': result.success,
            'exit_code': result.exit_code,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'execution_time': result.execution_time,
            'errors': result.errors,
            'warnings': result.warnings
        }
        
        # Track errors for self-healing
        if result.has_errors():
            state['execution_errors'][filepath] = result.errors
            state['fix_attempts'][filepath] = state['fix_attempts'].get(filepath, 0)
            
            logger.warning(
                f"Execution failed for {filepath}: {result.get_error_summary()}"
            )
        else:
            logger.info(f"Execution successful for {filepath} ({result.execution_time:.2f}s)")
            
            # Remove from error tracking if it was there
            if filepath in state.get('execution_errors', {}):
                del state['execution_errors'][filepath]
    
    def _extract_dependencies(self, state: DevTeamState, file_type: str) -> List[str]:
        """Extract dependencies from tech stack or requirements."""
        dependencies = []
        
        tech_stack = state.get('tech_stack', {})
        
        if file_type == 'backend':
            backend_tech = tech_stack.get('backend', [])
            
            # Map common frameworks to pip packages
            framework_map = {
                'fastapi': ['fastapi', 'uvicorn', 'pydantic'],
                'flask': ['flask', 'flask-cors'],
                'django': ['django', 'djangorestframework'],
                'sqlalchemy': ['sqlalchemy', 'psycopg2-binary'],
                'pydantic': ['pydantic']
            }
            
            for tech in backend_tech:
                tech_lower = tech.lower()
                if tech_lower in framework_map:
                    dependencies.extend(framework_map[tech_lower])
        
        return list(set(dependencies))  # Remove duplicates
    
    def _needs_self_healing(self, state: DevTeamState) -> bool:
        """Check if any files need self-healing."""
        execution_errors = state.get('execution_errors', {})
        
        if not execution_errors:
            return False
        
        # Check if any files haven't exceeded max attempts
        fix_attempts = state.get('fix_attempts', {})
        
        for filepath in execution_errors.keys():
            attempts = fix_attempts.get(filepath, 0)
            if attempts < self.max_fix_attempts:
                return True
        
        return False
    
    def _log_execution_summary(self, state: DevTeamState) -> None:
        """Log summary of execution results."""
        results = state.get('execution_results', {})
        errors = state.get('execution_errors', {})
        
        total = len(results)
        success = sum(1 for r in results.values() if r['success'])
        failed = total - success
        
        logger.info(
            f"Execution Summary: {success}/{total} successful, {failed} failed"
        )
        
        if errors:
            logger.warning(f"Files with errors: {list(errors.keys())}")


class SelfHealingNode:
    """Automatically fix code based on execution errors."""
    
    def __init__(self):
        """Initialize self-healing node."""
        self.llm = create_llm()
        logger.info("SelfHealingNode initialized")
    
    def __call__(self, state: DevTeamState) -> DevTeamState:
        """
        Attempt to fix code based on execution errors.
        
        Args:
            state: Current dev team state
            
        Returns:
            Updated state with fixed code
        """
        if not state.get('self_healing_enabled', True):
            logger.info("Self-healing disabled, skipping")
            return state
        
        execution_errors = state.get('execution_errors', {})
        if not execution_errors:
            logger.info("No execution errors to fix")
            return state
        
        logger.info("=== Starting Self-Healing Phase ===")
        
        fix_attempts = state.get('fix_attempts', {})
        max_attempts = state.get('max_fix_attempts', 3)
        
        # Attempt to fix each file with errors
        for filepath, errors in execution_errors.items():
            attempts = fix_attempts.get(filepath, 0)
            
            if attempts >= max_attempts:
                logger.warning(
                    f"Skipping {filepath}: max attempts ({max_attempts}) reached"
                )
                continue
            
            logger.info(f"Attempting to fix {filepath} (attempt {attempts + 1}/{max_attempts})")
            
            # Get original code
            original_code = self._get_file_code(state, filepath)
            if not original_code:
                logger.error(f"Could not find original code for {filepath}")
                continue
            
            # Get execution results for context
            exec_result = state['execution_results'].get(filepath, {})
            
            # Generate fix
            fixed_code = self._generate_fix(
                filepath,
                original_code,
                errors,
                exec_result
            )
            
            if fixed_code:
                # Update code in state
                self._update_file_code(state, filepath, fixed_code)
                
                # Increment attempt counter
                fix_attempts[filepath] = attempts + 1
                
                logger.info(f"Generated fix for {filepath}")
            else:
                logger.error(f"Failed to generate fix for {filepath}")
        
        state['fix_attempts'] = fix_attempts
        
        logger.info("=== Self-Healing Phase Complete ===")
        
        return state
    
    def _get_file_code(self, state: DevTeamState, filepath: str) -> str:
        """Get code for a file from state."""
        # Check backend files
        if filepath in state.get('backend_files', {}):
            return state['backend_files'][filepath]
        
        # Check frontend files
        if filepath in state.get('frontend_files', {}):
            return state['frontend_files'][filepath]
        
        return ""
    
    def _update_file_code(self, state: DevTeamState, filepath: str, code: str) -> None:
        """Update code for a file in state."""
        # Update backend files
        if filepath in state.get('backend_files', {}):
            state['backend_files'][filepath] = code
            return
        
        # Update frontend files
        if filepath in state.get('frontend_files', {}):
            state['frontend_files'][filepath] = code
            return
    
    def _generate_fix(
        self,
        filepath: str,
        original_code: str,
        errors: List[str],
        exec_result: Dict[str, Any]
    ) -> str:
        """
        Generate fixed code using LLM.
        
        Args:
            filepath: File path
            original_code: Original code that failed
            errors: List of error messages
            exec_result: Full execution result
            
        Returns:
            Fixed code or empty string if failed
        """
        error_summary = "\n".join(errors)
        stderr = exec_result.get('stderr', '')
        
        prompt = f"""You are a debugging expert. Fix the following Python code that failed execution.

        **File:** {filepath}

        **Original Code:**
        ```python
        {original_code}
        ```

        **Execution Errors:**
        {error_summary}

        **Full Stderr:**
        ```
        {stderr[:1000]}
        ```

        **Task:** Fix the code to resolve these errors. Common issues to check:
        1. Missing imports (ModuleNotFoundError, ImportError)
        2. Syntax errors
        3. Type errors
        4. Undefined variables or functions
        5. Logic errors

        **Instructions:**
        - Provide ONLY the fixed code, no explanations
        - Keep the same structure and functionality
        - Add any missing imports at the top
        - Fix syntax and runtime errors
        - Ensure the code will execute successfully

        **Fixed Code:**
        ```python"""

        try:
            response = self.llm.invoke(prompt)
            
            # Extract code from response
            fixed_code = response.content if hasattr(response, 'content') else str(response)
            
            # Remove markdown code blocks if present
            if '```python' in fixed_code:
                parts = fixed_code.split('```python')
                if len(parts) > 1:
                    fixed_code = parts[1].split('```')[0].strip()
            elif '```' in fixed_code:
                parts = fixed_code.split('```')
                if len(parts) > 1:
                    fixed_code = parts[1].strip()
            
            return fixed_code
            
        except Exception as e:
            logger.error(f"Error generating fix: {e}")
            return ""


# Node instances
code_execution_node = CodeExecutionNode()
self_healing_node = SelfHealingNode()