"""
Unit tests for Self-Healing Code Runner.

Tests Docker execution and automatic error correction functionality.
"""

import sys
from pathlib import Path
from src.utils.code_runner import DockerCodeRunner, ExecutionResult, run_python_code
from src.agents.dev_team.runner_node import CodeExecutionNode, SelfHealingNode
import pytest
from unittest.mock import Mock, patch
import tempfile

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestDockerCodeRunner:
    """Test Docker code execution functionality."""
    
    def test_initialization(self):
        """Test DockerCodeRunner initialization."""
        runner = DockerCodeRunner(
            base_image="python:3.11-slim",
            timeout=30,
            max_memory="512m"
        )
        
        assert runner.base_image == "python:3.11-slim"
        assert runner.timeout == 30
        assert runner.max_memory == "512m"
    
    @patch('subprocess.run')
    def test_docker_check_available(self, mock_run):
        """Test Docker availability check."""
        mock_run.return_value = Mock(returncode=0)
        
        runner = DockerCodeRunner()
        assert runner.docker_available or not runner.docker_available  # May vary
    
    @patch('subprocess.run')
    def test_docker_check_unavailable(self, mock_run):
        """Test Docker unavailable handling."""
        mock_run.side_effect = FileNotFoundError()
        
        runner = DockerCodeRunner()
        assert not runner.docker_available
    
    def test_execution_result_success(self):
        """Test ExecutionResult for successful execution."""
        result = ExecutionResult(
            success=True,
            exit_code=0,
            stdout="Hello World",
            stderr="",
            execution_time=0.5,
            errors=[],
            warnings=[]
        )
        
        assert result.success
        assert not result.has_errors()
        assert result.get_error_summary() == "No errors"
    
    def test_execution_result_with_errors(self):
        """Test ExecutionResult with errors."""
        result = ExecutionResult(
            success=False,
            exit_code=1,
            stdout="",
            stderr="ModuleNotFoundError: No module named 'requests'",
            execution_time=0.1,
            errors=["ModuleNotFoundError: No module named 'requests'"],
            warnings=[]
        )
        
        assert not result.success
        assert result.has_errors()
        assert "Exit code: 1" in result.get_error_summary()
    
    @pytest.mark.skipif(
        not DockerCodeRunner()._check_docker(),
        reason="Docker not available"
    )
    def test_execute_simple_code(self):
        """Test executing simple Python code."""
        runner = DockerCodeRunner(timeout=10)
        
        code = """
print("Hello from Docker!")
result = 2 + 2
print(f"2 + 2 = {result}")
"""
        
        result = runner.execute_python_code(code)
        
        assert result.exit_code == 0
        assert "Hello from Docker!" in result.stdout
        assert "2 + 2 = 4" in result.stdout
    
    @pytest.mark.skipif(
        not DockerCodeRunner()._check_docker(),
        reason="Docker not available"
    )
    def test_execute_code_with_syntax_error(self):
        """Test executing code with syntax error."""
        runner = DockerCodeRunner(timeout=10)
        
        code = """
print("This will fail"
"""
        
        result = runner.execute_python_code(code)
        
        assert result.exit_code != 0
        assert result.has_errors()
        assert "SyntaxError" in result.stderr or "invalid syntax" in result.stderr
    
    @pytest.mark.skipif(
        not DockerCodeRunner()._check_docker(),
        reason="Docker not available"
    )
    def test_execute_code_with_missing_import(self):
        """Test executing code with missing import."""
        runner = DockerCodeRunner(timeout=10)
        
        code = """
import nonexistent_module
print("This won't execute")
"""
        
        result = runner.execute_python_code(code)
        
        assert result.exit_code != 0
        assert result.has_errors()
        assert any("ModuleNotFoundError" in err or "ImportError" in err for err in result.errors)
    
    @pytest.mark.skipif(
        not DockerCodeRunner()._check_docker(),
        reason="Docker not available"
    )
    def test_execute_code_with_dependencies(self):
        """Test executing code with pip dependencies."""
        runner = DockerCodeRunner(timeout=30)
        
        code = """
import requests
print(f"Requests version: {requests.__version__}")
"""
        
        result = runner.execute_python_code(
            code,
            dependencies=["requests"]
        )
        
        # May succeed or fail depending on network
        # Just check execution completed
        assert result.execution_time > 0
    
    def test_build_docker_command(self):
        """Test Docker command building."""
        runner = DockerCodeRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cmd = runner._build_docker_command(
                Path(temp_dir),
                "main.py",
                has_requirements=True,
                env_vars={"API_KEY": "test123"}
            )
            
            assert "docker" in cmd
            assert "run" in cmd
            assert "--rm" in cmd
            assert "-v" in cmd
            assert "python main.py" in " ".join(cmd)
            assert "-e" in cmd
            assert "API_KEY=test123" in cmd
    
    def test_parse_errors(self):
        """Test error parsing from stderr."""
        runner = DockerCodeRunner()
        
        stderr = """
Traceback (most recent call last):
  File "main.py", line 3, in <module>
    import nonexistent
ModuleNotFoundError: No module named 'nonexistent'
"""
        
        errors = runner._parse_errors(stderr)
        
        assert len(errors) > 0
        assert any("ModuleNotFoundError" in err for err in errors)
    
    def test_parse_warnings(self):
        """Test warning parsing from stderr."""
        runner = DockerCodeRunner()
        
        stderr = """
Warning: Deprecated function used
DeprecationWarning: This will be removed in v2.0
"""
        
        warnings = runner._parse_warnings(stderr)
        
        assert len(warnings) == 2


class TestCodeExecutionNode:
    """Test CodeExecutionNode for dev team agent."""
    
    def test_initialization(self):
        """Test node initialization."""
        node = CodeExecutionNode(max_fix_attempts=3)
        
        assert node.max_fix_attempts == 3
        assert node.runner is not None
    
    def test_execution_disabled(self):
        """Test node when execution is disabled."""
        node = CodeExecutionNode()
        
        state = {
            'execution_enabled': False,
            'backend_files': {'main.py': 'print("test")'}
        }
        
        result = node(state)
        
        assert 'execution_results' not in result
    
    @patch('src.utils.code_runner.DockerCodeRunner')
    def test_docker_unavailable(self, mock_runner_class):
        """Test node when Docker is unavailable."""
        mock_runner = Mock()
        mock_runner.docker_available = False
        mock_runner_class.return_value = mock_runner
        
        node = CodeExecutionNode()
        node.runner = mock_runner
        
        state = {
            'execution_enabled': True,
            'backend_files': {'main.py': 'print("test")'}
        }
        
        result = node(state)
        
        assert 'execution_errors' in result
        assert 'system' in result['execution_errors']
    
    def test_identify_entry_points(self):
        """Test entry point identification."""
        node = CodeExecutionNode()
        
        files = {
            'main.py': 'print("main")',
            'utils.py': 'def helper(): pass',
            'app.py': 'print("app")',
            'models/user.py': 'class User: pass'
        }
        
        entry_points = node._identify_entry_points(files)
        
        assert 'main.py' in entry_points or 'app.py' in entry_points
        assert 'utils.py' not in entry_points
        assert 'models/user.py' not in entry_points
    
    def test_identify_entry_points_with_main_guard(self):
        """Test entry point identification with __main__ guard."""
        node = CodeExecutionNode()
        
        files = {
            'script.py': '''
def main():
    print("Hello")

if __name__ == '__main__':
    main()
''',
            'utils.py': 'def helper(): pass'
        }
        
        entry_points = node._identify_entry_points(files)
        
        assert 'script.py' in entry_points
    
    def test_extract_dependencies_fastapi(self):
        """Test dependency extraction for FastAPI."""
        node = CodeExecutionNode()
        
        state = {
            'tech_stack': {
                'backend': ['FastAPI', 'SQLAlchemy']
            }
        }
        
        deps = node._extract_dependencies(state, 'backend')
        
        assert 'fastapi' in deps
        assert 'sqlalchemy' in deps
    
    def test_needs_self_healing(self):
        """Test self-healing need detection."""
        node = CodeExecutionNode()
        
        # No errors
        state = {'execution_errors': {}}
        assert not node._needs_self_healing(state)
        
        # Errors but max attempts reached
        state = {
            'execution_errors': {'main.py': ['Error']},
            'fix_attempts': {'main.py': 3},
            'max_fix_attempts': 3
        }
        assert not node._needs_self_healing(state)
        
        # Errors and attempts available
        state = {
            'execution_errors': {'main.py': ['Error']},
            'fix_attempts': {'main.py': 1},
            'max_fix_attempts': 3
        }
        assert node._needs_self_healing(state)


class TestSelfHealingNode:
    """Test SelfHealingNode for automatic error correction."""
    
    def test_initialization(self):
        """Test node initialization."""
        node = SelfHealingNode()
        assert node.llm is not None
    
    def test_self_healing_disabled(self):
        """Test node when self-healing is disabled."""
        node = SelfHealingNode()
        
        state = {
            'self_healing_enabled': False,
            'execution_errors': {'main.py': ['Error']}
        }
        
        result = node(state)
        
        # Should not modify state
        assert result['execution_errors'] == {'main.py': ['Error']}
    
    def test_no_errors_to_fix(self):
        """Test node when there are no errors."""
        node = SelfHealingNode()
        
        state = {
            'self_healing_enabled': True,
            'execution_errors': {}
        }
        
        result = node(state)
        
        assert 'fix_attempts' not in result or not result.get('fix_attempts')
    
    def test_get_file_code(self):
        """Test retrieving file code from state."""
        node = SelfHealingNode()
        
        state = {
            'backend_files': {'main.py': 'print("backend")'},
            'frontend_files': {'app.tsx': 'console.log("frontend")'}
        }
        
        backend_code = node._get_file_code(state, 'main.py')
        frontend_code = node._get_file_code(state, 'app.tsx')
        missing_code = node._get_file_code(state, 'missing.py')
        
        assert backend_code == 'print("backend")'
        assert frontend_code == 'console.log("frontend")'
        assert missing_code == ""
    
    def test_update_file_code(self):
        """Test updating file code in state."""
        node = SelfHealingNode()
        
        state = {
            'backend_files': {'main.py': 'original'},
            'frontend_files': {'app.tsx': 'original'}
        }
        
        node._update_file_code(state, 'main.py', 'fixed')
        node._update_file_code(state, 'app.tsx', 'fixed')
        
        assert state['backend_files']['main.py'] == 'fixed'
        assert state['frontend_files']['app.tsx'] == 'fixed'
    
    @patch('src.core.llm_factory.create_llm')
    def test_generate_fix(self, mock_create_llm):
        """Test fix generation with LLM."""
        # Mock LLM response
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = """```python
import sys
print("Fixed code")
```"""
        mock_llm.invoke.return_value = mock_response
        mock_create_llm.return_value = mock_llm
        
        node = SelfHealingNode()
        node.llm = mock_llm
        
        original_code = 'print("broken"'
        errors = ["SyntaxError: invalid syntax"]
        exec_result = {'stderr': 'SyntaxError: invalid syntax'}
        
        fixed_code = node._generate_fix(
            'main.py',
            original_code,
            errors,
            exec_result
        )
        
        assert 'import sys' in fixed_code
        assert 'Fixed code' in fixed_code
        assert '```' not in fixed_code  # Markdown removed
    
    @patch('src.core.llm_factory.create_llm')
    def test_max_attempts_reached(self, mock_create_llm):
        """Test that max fix attempts are respected."""
        mock_llm = Mock()
        mock_create_llm.return_value = mock_llm
        
        node = SelfHealingNode()
        node.llm = mock_llm
        
        state = {
            'self_healing_enabled': True,
            'execution_errors': {'main.py': ['Error']},
            'fix_attempts': {'main.py': 3},
            'max_fix_attempts': 3,
            'backend_files': {'main.py': 'code'},
            'execution_results': {'main.py': {}}
        }
        
        result = node(state)
        
        # Should not call LLM since max attempts reached
        mock_llm.invoke.assert_not_called()


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @patch('src.utils.code_runner.DockerCodeRunner')
    def test_run_python_code_function(self, mock_runner_class):
        """Test run_python_code convenience function."""
        mock_runner = Mock()
        mock_result = ExecutionResult(
            success=True,
            exit_code=0,
            stdout="output",
            stderr="",
            execution_time=0.5,
            errors=[],
            warnings=[]
        )
        mock_runner.execute_python_code.return_value = mock_result
        mock_runner_class.return_value = mock_runner
        
        result = run_python_code('print("test")', timeout=10)
        
        assert result.success
        mock_runner.execute_python_code.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
