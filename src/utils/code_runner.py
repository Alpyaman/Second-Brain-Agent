"""
Docker Code Execution Runner for Self-Healing Dev Team.

This module provides sandboxed code execution in Docker containers,
capturing stdout, stderr, and exit codes to provide feedback to the agent.
"""

import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ExecutionResult:
    """Result of code execution in Docker container."""
    
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    errors: List[str]
    warnings: List[str]
    
    def has_errors(self) -> bool:
        """Check if execution had errors."""
        return not self.success or self.exit_code != 0 or bool(self.errors)
    
    def get_error_summary(self) -> str:
        """Get human-readable error summary."""
        if not self.has_errors():
            return "No errors"
        
        summary = []
        if self.exit_code != 0:
            summary.append(f"Exit code: {self.exit_code}")
        if self.stderr:
            summary.append(f"Stderr: {self.stderr[:500]}")
        if self.errors:
            summary.append(f"Errors: {', '.join(self.errors[:3])}")
        
        return " | ".join(summary)


class DockerCodeRunner:
    """Execute code in isolated Docker containers for testing and validation."""
    
    def __init__(
        self,
        base_image: str = "python:3.11-slim",
        timeout: int = 30,
        max_memory: str = "512m",
        network_disabled: bool = False
    ):
        """
        Initialize Docker code runner.
        
        Args:
            base_image: Docker base image to use
            timeout: Execution timeout in seconds
            max_memory: Maximum memory limit
            network_disabled: Whether to disable network access
        """
        self.base_image = base_image
        self.timeout = timeout
        self.max_memory = max_memory
        self.network_disabled = network_disabled
        
        # Check Docker availability
        if not self._check_docker():
            logger.warning("Docker not available - execution features will be disabled")
            self.docker_available = False
        else:
            self.docker_available = True
            logger.info(f"Docker runner initialized with image: {base_image}")
    
    def _check_docker(self) -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def execute_python_file(
        self,
        file_path: Path,
        dependencies: Optional[List[str]] = None,
        env_vars: Optional[Dict[str, str]] = None
    ) -> ExecutionResult:
        """
        Execute a Python file in a Docker container.
        
        Args:
            file_path: Path to Python file
            dependencies: List of pip packages to install
            env_vars: Environment variables to set
            
        Returns:
            ExecutionResult with execution details
        """
        if not self.docker_available:
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="Docker not available",
                execution_time=0.0,
                errors=["Docker not available on this system"],
                warnings=[]
            )
        
        # Create temporary directory for execution
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Copy file to temp directory
            code_file = temp_path / file_path.name
            shutil.copy2(file_path, code_file)
            
            # Create requirements.txt if dependencies provided
            if dependencies:
                requirements = temp_path / "requirements.txt"
                requirements.write_text("\n".join(dependencies))
            
            # Build Docker command
            cmd = self._build_docker_command(
                temp_path,
                code_file.name,
                has_requirements=bool(dependencies),
                env_vars=env_vars
            )
            
            # Execute
            return self._execute_command(cmd)
    
    def execute_python_code(
        self,
        code: str,
        filename: str = "main.py",
        dependencies: Optional[List[str]] = None,
        env_vars: Optional[Dict[str, str]] = None
    ) -> ExecutionResult:
        """
        Execute Python code string in a Docker container.
        
        Args:
            code: Python code to execute
            filename: Name for the temporary file
            dependencies: List of pip packages to install
            env_vars: Environment variables to set
            
        Returns:
            ExecutionResult with execution details
        """
        if not self.docker_available:
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="Docker not available",
                execution_time=0.0,
                errors=["Docker not available on this system"],
                warnings=[]
            )
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write code to file
            code_file = temp_path / filename
            code_file.write_text(code, encoding='utf-8')
            
            # Create requirements.txt if dependencies provided
            if dependencies:
                requirements = temp_path / "requirements.txt"
                requirements.write_text("\n".join(dependencies))
            
            # Build Docker command
            cmd = self._build_docker_command(
                temp_path,
                filename,
                has_requirements=bool(dependencies),
                env_vars=env_vars
            )
            
            # Execute
            return self._execute_command(cmd)
    
    def execute_project(
        self,
        project_dir: Path,
        entry_point: str = "main.py",
        install_command: Optional[str] = None
    ) -> ExecutionResult:
        """
        Execute a complete project in a Docker container.
        
        Args:
            project_dir: Path to project directory
            entry_point: Entry point file to execute
            install_command: Custom install command (e.g., "pip install -e .")
            
        Returns:
            ExecutionResult with execution details
        """
        if not self.docker_available:
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="Docker not available",
                execution_time=0.0,
                errors=["Docker not available on this system"],
                warnings=[]
            )
        
        # Build Docker command for project
        cmd = self._build_project_command(
            project_dir,
            entry_point,
            install_command
        )
        
        # Execute
        return self._execute_command(cmd)
    
    def _build_docker_command(
        self,
        work_dir: Path,
        filename: str,
        has_requirements: bool = False,
        env_vars: Optional[Dict[str, str]] = None
    ) -> List[str]:
        """Build Docker run command."""
        cmd = [
            "docker", "run",
            "--rm",  # Remove container after execution
            f"--memory={self.max_memory}",
            "--cpus=1",
            "-v", f"{work_dir}:/app",
            "-w", "/app"
        ]
        
        # Add environment variables
        if env_vars:
            for key, value in env_vars.items():
                cmd.extend(["-e", f"{key}={value}"])
        
        # Disable network if requested
        if self.network_disabled:
            cmd.extend(["--network", "none"])
        
        # Add image
        cmd.append(self.base_image)
        
        # Build execution command
        exec_cmd = []
        if has_requirements:
            exec_cmd.append("pip install -q -r requirements.txt && ")
        exec_cmd.append(f"python {filename}")
        
        cmd.extend(["sh", "-c", "".join(exec_cmd)])
        
        return cmd
    
    def _build_project_command(
        self,
        project_dir: Path,
        entry_point: str,
        install_command: Optional[str]
    ) -> List[str]:
        """Build Docker command for project execution."""
        cmd = [
            "docker", "run",
            "--rm",
            f"--memory={self.max_memory}",
            "--cpus=1",
            "-v", f"{project_dir}:/app",
            "-w", "/app"
        ]
        
        if self.network_disabled:
            cmd.extend(["--network", "none"])
        
        cmd.append(self.base_image)
        
        # Build execution command
        exec_cmd = []
        if install_command:
            exec_cmd.append(f"{install_command} && ")
        elif (project_dir / "requirements.txt").exists():
            exec_cmd.append("pip install -q -r requirements.txt && ")
        exec_cmd.append(f"python {entry_point}")
        
        cmd.extend(["sh", "-c", "".join(exec_cmd)])
        
        return cmd
    
    def _execute_command(self, cmd: List[str]) -> ExecutionResult:
        """Execute Docker command and capture results."""
        import time
        
        start_time = time.time()
        
        try:
            logger.info(f"Executing: {' '.join(cmd[:8])}...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            execution_time = time.time() - start_time
            
            # Parse output for errors and warnings
            errors = self._parse_errors(result.stderr)
            warnings = self._parse_warnings(result.stderr)
            
            success = result.returncode == 0 and not errors
            
            logger.info(
                f"Execution completed: exit_code={result.returncode}, "
                f"time={execution_time:.2f}s, errors={len(errors)}"
            )
            
            return ExecutionResult(
                success=success,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=execution_time,
                errors=errors,
                warnings=warnings
            )
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            logger.warning(f"Execution timed out after {self.timeout}s")
            
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Execution timed out after {self.timeout} seconds",
                execution_time=execution_time,
                errors=[f"Timeout after {self.timeout}s"],
                warnings=[]
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Execution failed: {e}")
            
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=execution_time,
                errors=[str(e)],
                warnings=[]
            )
    
    def _parse_errors(self, stderr: str) -> List[str]:
        """Parse stderr for error messages."""
        errors = []
        
        error_patterns = [
            "Error:",
            "Exception:",
            "Traceback",
            "ModuleNotFoundError",
            "ImportError",
            "SyntaxError",
            "NameError",
            "TypeError",
            "ValueError"
        ]
        
        for line in stderr.split("\n"):
            for pattern in error_patterns:
                if pattern in line:
                    errors.append(line.strip())
                    break
        
        return errors
    
    def _parse_warnings(self, stderr: str) -> List[str]:
        """Parse stderr for warning messages."""
        warnings = []
        
        for line in stderr.split("\n"):
            if "Warning:" in line or "warning:" in line:
                warnings.append(line.strip())
        
        return warnings


# Global instance
docker_runner = DockerCodeRunner()


# Convenience functions

def run_python_code(
    code: str,
    dependencies: Optional[List[str]] = None,
    timeout: int = 30
) -> ExecutionResult:
    """
    Run Python code in Docker container.
    
    Args:
        code: Python code to execute
        dependencies: List of pip packages
        timeout: Timeout in seconds
        
    Returns:
        ExecutionResult
    """
    runner = DockerCodeRunner(timeout=timeout)
    return runner.execute_python_code(code, dependencies=dependencies)


def run_python_file(
    file_path: Path,
    dependencies: Optional[List[str]] = None,
    timeout: int = 30
) -> ExecutionResult:
    """
    Run Python file in Docker container.
    
    Args:
        file_path: Path to Python file
        dependencies: List of pip packages
        timeout: Timeout in seconds
        
    Returns:
        ExecutionResult
    """
    runner = DockerCodeRunner(timeout=timeout)
    return runner.execute_python_file(file_path, dependencies=dependencies)
