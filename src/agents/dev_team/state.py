"""
Development Team State Definition

This module defines the state structure for the multi-agent development team workflow.
The state tracks the feature request decomposition, specialized code generation, and integration review process.

Phase 2 Enhancement: Now supports TDD input and actual file generation.
"""

from typing import TypedDict, List, Dict, Any, Optional

class DevTeamState(TypedDict):
    """
    State for the multi-agent development team workflow.

    Workflow:
    1. Tech Lead receives feature_request (or TDD) and decomposes it
    2. Frontend/Backend specialists work on their respective tasks
    3. Code Generator creates actual files
    4. Integration Reviewer validates the outputs
    """

    # ========== PHASE 1: ORIGINAL INPUTS ==========
    feature_request: str # High-level feature description from user

    # ========== PHASE 2: TDD INPUTS ==========
    tdd_content: Optional[str]                    # Full TDD markdown from Phase 1
    tdd_parsed: Optional[bool]                    # Whether TDD has been parsed
    project_metadata: Optional[Dict[str, str]]    # Project name, version, etc.
    project_type: Optional[str]                   # Project type: web_app, script, notebook, library, api
    tech_stack: Optional[Dict[str, List[str]]]    # frontend, backend, database, etc.
    features_to_implement: Optional[List[Dict[str, str]]]  # Extracted features
    api_specification: Optional[Dict[str, Any]]   # API endpoints, base_url, version
    data_model: Optional[Dict[str, Dict[str, str]]]  # Entity definitions
    security_requirements: Optional[List[str]]    # Security requirements
    implementation_phase: Optional[int]           # Which phase to implement (1, 2, or 3)

    # ========== TECH LEAD OUTPUTS ==========
    frontend_tasks: List[str]   # List of frontend tasks
    backend_tasks: List[str]    # List of backend tasks
    architecture_notes: str     # High-level architecture decisions

    # ========== FRONTEND SPECIALIST OUTPUTS ==========
    frontend_code: str          # Generated frontend code (markdown with code blocks)
    frontend_context: str       # Retrieved patterns from frontend_brain
    frontend_status: str        # Status: pending, in_progress, completed
    frontend_files: Optional[Dict[str, str]]  # PHASE 2: filepath -> code content

    # ========== BACKEND SPECIALIST OUTPUTS ==========
    backend_code: str           # Generated backend code (markdown with code blocks)
    backend_context: str        # Retrieved patterns from backend_brain
    backend_status: str         # Status: pending, in_progress, completed
    backend_files: Optional[Dict[str, str]]   # PHASE 2: filepath -> code content

    # ========== CODE GENERATOR OUTPUTS (PHASE 2) ==========
    config_files: Optional[Dict[str, str]]    # package.json, .env, docker-compose.yml
    database_files: Optional[Dict[str, str]]  # SQL migrations, schema
    test_files: Optional[Dict[str, str]]      # Test files
    generated_files: Optional[List[str]]      # List of all generated file paths

    # ========== INTEGRATION REVIEWER OUTPUTS ==========
    integration_review: str     # Review findings and recommendations
    issues_found: List[str]     # List of integration issues
    review_status: str          # Status: pass, needs_revision, fail

    # ========== CODE VALIDATION (PHASE 2) ==========
    validation_results: Optional[Dict[str, bool]]  # filepath -> is_valid
    validation_errors: Optional[Dict[str, List[str]]]  # filepath -> error messages
    validation_warnings: Optional[List[str]]  # Import validation warnings

    # ========== OUTPUT METADATA (PHASE 2) ==========
    output_directory: Optional[str]  # Where to write files
    files_written: Optional[int]     # Number of files successfully written

    # ========== EXECUTION & SELF-HEALING (PHASE 3) ==========
    execution_enabled: Optional[bool]  # Whether to execute and validate code
    execution_results: Optional[Dict[str, Dict[str, Any]]]  # filepath -> ExecutionResult
    execution_errors: Optional[Dict[str, List[str]]]  # filepath -> error messages
    fix_attempts: Optional[Dict[str, int]]  # filepath -> number of fix attempts
    max_fix_attempts: Optional[int]  # Maximum number of self-healing attempts
    self_healing_enabled: Optional[bool]  # Whether to auto-fix errors

    # ========== WORKFLOW METADATA ==========
    iteration_count: int        # Number of refinement iterations
    needs_revision: bool        # Whether code needs revision