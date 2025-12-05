"""
Multi-Agent Development Team LangGraph Workflow

This module implements a software development team where each agent has:
1. DISTINCT DATA: Specialized RAG collections (frontend_brain, backend_brain)
2. DISTINCT CAPABILITIES: Domain-specific tools and expertise

This is NOT "just wrapping an LLM" - each agent learns from different codebases.

Features:
- Multi-provider LLM support via llm_factory
- Task-optimized model selection (parsing, coding, review)
- Backward compatible with legacy Google Gemini
"""

import os
from typing import List, Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from src.agents.dev_team.state import DevTeamState
from src.core.config import EMBEDDING_MODEL, CHROMA_DB_DIR

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Import multi-model support
try:
    from src.core.llm_factory import get_llm
    MULTI_MODEL_AVAILABLE = True
except ImportError:
    MULTI_MODEL_AVAILABLE = False
    print("⚠️  Multi-model support not available in dev_team. Using legacy Google Gemini only.")

# ============================================================================
# PYDANTIC MODELS FOR STRUCTURED OUTPUT
# ============================================================================

class TechLeadDecomposition(BaseModel):
    """
    Structured output from Tech Lead for feature decomposition.

    This ensures Gemini always returns valid structured data, preventing
    parsing failures from markdown formatting or preamble text.
    """

    frontend_tasks: List[str] = Field(description="List of specific frontend work items (UI, components, client-side logic)")

    backend_tasks: List[str] = Field(description="List of specific backend work items (API endpoints, database, business logic)")

    architecture_notes: str = Field(description="High-level description of how frontend and backend integrate")

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def query_expert_brain(query: str, collection_name: str, k: int = 5) -> str:
    """
    Query a specialized expert brain collection.

    This is the KEY function that makes each agent different - they query
    different collections and learn from different codebases.

    Args:
        query: Search query
        collection_name: Expert brain to query (frontend_brain, backend_brain)
        k: Number of results to retrieve

    Returns:
        Formatted context string with retrieved patterns
    """
    try:
        # Initialize embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        # Connect to specialized brain
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=str(CHROMA_DB_DIR)
        )

        # Retrieve relevant patterns
        results = vectorstore.similarity_search(query, k=k)

        if not results:
            return f"No patterns found in {collection_name}. Please ingest expert knowledge first."

        # Format retrieved patterns
        context_parts = []
        for i, doc in enumerate(results, 1):
            filename = doc.metadata.get('filename', 'unknown')
            file_type = doc.metadata.get('file_type', '')
            content = doc.page_content[:800]  # Limit to 800 chars per pattern

            context_parts.append(
                f"**Pattern {i}** (from {filename}):\n```{file_type}\n{content}\n```"
            )

        return "\n\n".join(context_parts)

    except Exception as e:
        return f"Error accessing {collection_name}: {str(e)}\nPlease run: python src/ingest_expert.py --expert <type> --list"


# ============================================================================
# NODE 1: TECH LEAD (DISPATCHER)
# ============================================================================

def tech_lead_dispatcher(state: DevTeamState) -> DevTeamState:
    """
    Tech Lead analyzes the feature request and decomposes it into:
    - Frontend tasks (UI, components, client-side logic) - for web apps
    - Backend tasks (API endpoints, database, business logic) - for web apps
    - Script tasks - for script/notebook projects
    - Architecture notes (how components integrate)

    Uses Pydantic structured output to ensure reliable parsing.
    Adapts based on project type.
    """
    print("\n" + "=" * 70)
    print("TECH LEAD: Analyzing Feature Request")
    print("=" * 70)
    print(f"Request: {state['feature_request']}\n")

    # Initialize state fields
    if 'iteration_count' not in state or state['iteration_count'] is None:
        state['iteration_count'] = 0
    if 'needs_revision' not in state:
        state['needs_revision'] = False

    # Get project type
    project_type = state.get('project_type', 'web_app')
    
    # Adjust prompt based on project type
    if project_type in ['script', 'notebook']:
        # For scripts/notebooks, don't split into frontend/backend
        system_prompt = """You are a Tech Lead responsible for decomposing feature requests into implementation tasks.
        This is a Python script/notebook project, NOT a web application.
        
        Your job is to analyze the feature and:
        1. Identify Python script tasks (data fetching, processing, file I/O, analysis)
        2. Identify notebook tasks (if applicable: data analysis, visualization, metrics)
        3. Identify configuration/setup tasks (requirements.txt, environment setup)
        4. Describe the workflow and data flow

        Do NOT create frontend/backend tasks. This is a standalone script/notebook project.
        Focus on Python scripts, data processing, and analysis tasks.

        Return your analysis as structured JSON with:
        - frontend_tasks: [] (empty array for script projects)
        - backend_tasks: array of Python script/analysis tasks
        - architecture_notes: string describing the script workflow and data flow"""

        user_prompt = f"""Feature Request: {state['feature_request']}
        This is a {project_type} project. Decompose into Python script/analysis tasks.
        Do NOT split into frontend/backend - this is NOT a web application."""
    elif project_type == 'api':
        # API-only projects
        system_prompt = """You are a Tech Lead responsible for decomposing feature requests into backend tasks.
        This is an API/backend-only project, NO frontend.
        
        Your job is to analyze the feature and:
        1. Identify backend tasks only (API endpoints, database, business logic)
        2. Describe API structure and endpoints

        Return your analysis as structured JSON with:
        - frontend_tasks: [] (empty array - no frontend)
        - backend_tasks: array of API/backend work items
        - architecture_notes: string describing API structure"""
        
        user_prompt = f"""Feature Request: {state['feature_request']}
        This is an API-only project. Decompose into backend/API tasks only. No frontend tasks."""
    else:
        # Default: web app
        system_prompt = """You are a Tech Lead responsible for decomposing feature requests into frontend and backend tasks.
        Your job is to analyze the feature and:
        1. Identify what needs to be built on the frontend (UI, components, client logic)
        2. Identify what needs to be built on the backend (APIs, database, business logic)
        3. Describe how they integrate (architecture notes)

        Be specific and actionable. Each task should be clear enough for a specialist to implement independently.

        Return your analysis as structured JSON with:
        - frontend_tasks: array of frontend work items
        - backend_tasks: array of backend work items
        - architecture_notes: string describing integration"""

        user_prompt = f"""Feature Request: {state['feature_request']}
        Decompose this feature into frontend tasks, backend tasks, and architecture notes."""

    # Use structured output with Pydantic model - reasoning task
    if MULTI_MODEL_AVAILABLE:
        llm = get_llm(task_type="reasoning", temperature=0.3)
    else:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.3)
    structured_llm = llm.with_structured_output(TechLeadDecomposition)

    # Generate decomposition with guaranteed structure
    try:
        decomposition = structured_llm.invoke([("system", system_prompt), ("user", user_prompt)])

        # Update state with structured data
        state['frontend_tasks'] = decomposition.frontend_tasks if decomposition.frontend_tasks else ["Implement frontend for: " + state['feature_request']]

        state['backend_tasks'] = decomposition.backend_tasks if decomposition.backend_tasks else ["Implement backend for: " + state['feature_request']]

        state['architecture_notes'] = decomposition.architecture_notes or "Frontend calls backend APIs."

    except Exception as e:
        # Fallback in case of any issues
        print(f"Warning: Structured output failed ({e}). Using fallback.")
        state['frontend_tasks'] = ["Implement frontend for: " + state['feature_request']]
        state['backend_tasks'] = ["Implement backend for: " + state['feature_request']]
        state['architecture_notes'] = "Frontend calls backend APIs."

    state['frontend_status'] = 'pending'
    state['backend_status'] = 'pending'

    print(f"Frontend Tasks ({len(state['frontend_tasks'])}):")
    for task in state['frontend_tasks']:
        print(f"  - {task}")

    print(f"\nBackend Tasks ({len(state['backend_tasks'])}):")
    for task in state['backend_tasks']:
        print(f"  - {task}")

    print("\nArchitecture Notes:")
    print(f"  {state['architecture_notes'][:200]}...")

    return state


# ============================================================================
# NODE 2: FRONTEND DEVELOPER
# ============================================================================

def frontend_developer(state: DevTeamState) -> DevTeamState:
    """
    Frontend Specialist implements UI/client-side features.

    KEY: Queries frontend_brain (shadcn/ui, Next.js patterns) for context.
    This gives it DISTINCT expertise from backend developer.
    
    SKIPS execution for script/notebook/api projects (no frontend needed).
    """
    # Skip frontend generation for non-web-app projects
    project_type = state.get('project_type', 'web_app')
    if project_type in ['script', 'notebook', 'library', 'api']:
        print("\n" + "=" * 70)
        print("FRONTEND SPECIALIST: Skipping (not a web app project)")
        print("=" * 70)
        print(f"Project type: {project_type} - No frontend needed")
        return {
            'frontend_code': '# No frontend needed for this project type',
            'frontend_status': 'skipped',
            'frontend_context': 'Project type does not require frontend'
        }
    
    print("\n" + "=" * 70)
    print("FRONTEND SPECIALIST: Implementing UI")
    print("=" * 70)

    # Combine tasks into a single query
    tasks_summary = " + ".join(state['frontend_tasks'])
    print(f"Tasks: {tasks_summary}\n")

    # CRITICAL: Query frontend_brain (NOT backend_brain!)
    print("Retrieving patterns from frontend_brain...")
    context = query_expert_brain(query=tasks_summary, collection_name="frontend_brain", k=5)

    if "No patterns found" in context or "Error accessing" in context:
        print("Frontend brain not available")
        print("   Run: python src/ingest_expert.py --expert frontend --list")
        # Return only the keys this node modifies to avoid parallel update conflicts
        return {
            'frontend_code': "# Frontend brain not initialized. Please ingest expert knowledge.",
            'frontend_status': 'completed',
            'frontend_context': context
        }

    print("Retrieved frontend patterns\n")

    # Generate frontend code using retrieved patterns
    system_prompt = """You are a Frontend Specialist with expertise in React, Next.js, and TypeScript.

        You have access to high-quality patterns from production codebases (shadcn/ui, Vercel templates).
        Use these patterns to generate clean, modern, type-safe frontend code."""

    user_prompt = f"""Tasks:
        {chr(10).join(f"- {task}" for task in state['frontend_tasks'])}

        Architecture Context:
        {state['architecture_notes']}

        Retrieved Patterns from frontend_brain:
        {context}

        Generate production-ready frontend code that:
        1. Follows the patterns shown above
        2. Is type-safe (TypeScript)
        3. Is modular and reusable
        4. Handles errors gracefully
        5. Includes clear API integration points

        IMPORTANT: Format each file as a code block with the file path in a header:
        ### app/components/ProductList.tsx
        ```typescript
        // File content here
        ```

        Provide the complete implementation with file structure."""

    # Use coding-optimized model for frontend generation
    if MULTI_MODEL_AVAILABLE:
        llm = get_llm(task_type="coding", temperature=0.3)
    else:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.3)
    response = llm.invoke([("system", system_prompt), ("user", user_prompt)])

    frontend_code = response.content
    print(f"Generated frontend code ({len(frontend_code)} characters)")

    # Return only the keys this node modifies to avoid parallel update conflicts
    return {
        'frontend_code': frontend_code,
        'frontend_status': 'completed',
        'frontend_context': context
    }


# ============================================================================
# NODE 3: BACKEND DEVELOPER
# ============================================================================

def backend_developer(state: DevTeamState) -> DevTeamState:
    """
    Backend Specialist implements API/server-side features.

    KEY: Queries backend_brain (FastAPI, Django patterns) for context.
    This gives it DISTINCT expertise from frontend developer.
    """
    # Get project type
    project_type = state.get('project_type', 'web_app')
    
    print("\n" + "=" * 70)
    if project_type in ['script', 'notebook']:
        print("BACKEND SPECIALIST: Implementing Python Scripts")
    else:
        print("BACKEND SPECIALIST: Implementing API")
    print("=" * 70)

   # Combine tasks into a single query
    tasks_summary = " + ".join(state['backend_tasks'])
    print(f"Tasks: {tasks_summary}\n")

    # For script/notebook, adjust approach (don't query FastAPI patterns)
    if project_type in ['script', 'notebook']:
        print("(Skipping backend_brain query for script/notebook project)")
        context = "Generating standalone Python scripts"
    else:
        # CRITICAL: Query backend_brain (NOT frontend_brain!)
        print("Retrieving patterns from backend_brain...")
        context = query_expert_brain(query=tasks_summary, collection_name="backend_brain", k=5)

    if "No patterns found" in context or "Error accessing" in context:
        print("Backend brain not available")
        print("   Run: python src/ingest_expert.py --expert backend --list")
        # Return only the keys this node modifies to avoid parallel update conflicts
        return {
            'backend_code': "# Backend brain not initialized. Please ingest expert knowledge.",
            'backend_status': 'completed',
            'backend_context': context
        }

        if "No patterns found" in context or "Error accessing" in context:
            print("Backend brain not available")
            print("   Run: python src/ingest_expert.py --expert backend --list")
            return {
                'backend_code': "# Backend brain not initialized. Please ingest expert knowledge.",
                'backend_status': 'completed',
                'backend_context': context
            }

        print("✓ Retrieved backend patterns\n")

    # Generate code - adjust prompt based on project type
    if project_type == 'notebook':
        system_prompt = """You are a Python Data Analysis Specialist.
        Generate Jupyter notebook code cells for data analysis, CSV processing, and metrics computation.
        Use pandas, matplotlib, and data analysis best practices."""
        
        user_prompt = f"""Tasks:
        {chr(10).join(f"- {task}" for task in state['backend_tasks'])}

        Architecture Context:
        {state['architecture_notes']}

        Generate Python code for data analysis:
        1. CSV data loading and cleaning
        2. Metrics computation (Open Rate, CTR, Error Rate)
        3. Campaign impact analysis (pre/post comparison)
        4. Visualizations and insights
        5. Clear, commented code

        Format files as:
        ### scripts/promo_code_assigner.py
        ```python
        # Code here
        ```
        
        ### notebooks/campaign_analysis.ipynb
        ```python
        # Jupyter notebook cells here
        ```"""
        
    elif project_type == 'script':
        system_prompt = """You are a Python Automation Specialist.
        Generate standalone Python scripts for automation, data fetching, and processing.
        Focus on: requests library, JSON processing, file I/O, error handling."""
        
        user_prompt = f"""Tasks:
        {chr(10).join(f"- {task}" for task in state['backend_tasks'])}

        Architecture Context:
        {state['architecture_notes']}

        Generate production-ready Python scripts:
        1. Fetch data from JSON endpoints using requests library
        2. Process and transform data (handle nulls, inconsistent types)
        3. Apply business rules and eligibility logic
        4. Assign unique promo codes by tier and city
        5. Handle errors and edge cases robustly
        6. Send POST requests to webhooks
        7. Use requests, json, pandas libraries

        Format files as:
        ### scripts/promo_code_assigner.py
        ```python
        # Complete script implementation
        ```"""
        
    else:
        # Default: API/Backend
        system_prompt = """You are a Backend Specialist with expertise in Python, FastAPI, and REST APIs.
        You have access to high-quality patterns from production codebases (FastAPI templates, Django patterns).
        Use these patterns to generate clean, performant, secure backend code."""

        user_prompt = f"""Tasks:
        {chr(10).join(f"- {task}" for task in state['backend_tasks'])}

        Architecture Context:
        {state['architecture_notes']}

        Retrieved Patterns from backend_brain:
        {context}

        Generate production-ready backend code that:
        1. Follows the patterns shown above
        2. Is type-safe (Pydantic models)
        3. Has proper error handling
        4. Includes input validation
        5. Has clear database integration
        6. Follows REST best practices

        IMPORTANT: Format each file as a code block with the file path in a header:
        ### app/core/config.py
        ```python
        # File content here
        ```

        Provide the complete implementation with file structure."""

    # Use coding-optimized model for backend generation
    if MULTI_MODEL_AVAILABLE:
        llm = get_llm(task_type="coding", temperature=0.3)
    else:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.3)
    response = llm.invoke([("system", system_prompt), ("user", user_prompt)])

    backend_code = response.content
    print(f"Generated backend code ({len(backend_code)} characters)")

    # Return only the keys this node modifies to avoid parallel update conflicts
    return {
        'backend_code': backend_code,
        'backend_status': 'completed',
        'backend_context': context
    }


# ============================================================================
# NODE 4: INTEGRATION REVIEWER
# ============================================================================

def integration_reviewer(state: DevTeamState) -> DevTeamState:
    """
    Integration Reviewer validates that frontend and backend work together.

    Checks:
    - API endpoint consistency
    - Data model alignment
    - Error handling compatibility
    - Type safety across boundaries
    """
    print("\n" + "=" * 70)
    print("INTEGRATION REVIEWER: Validating Integration")
    print("=" * 70)

    # Check if both specialists completed their work
    if state['frontend_status'] != 'completed' or state['backend_status'] != 'completed':
        print("Waiting for frontend and backend to complete...")
        state['review_status'] = 'pending'
        return state

    # Build review prompt
    system_prompt = """You are an Integration Reviewer responsible for ensuring frontend and backend work together seamlessly.
        Your job is to analyze both implementations and identify:
        1. API endpoint mismatches (frontend calls endpoints that don't exist)
        2. Data model inconsistencies (field names, types, structure)
        3. Error handling gaps (uncaught errors, missing validation)
        4. Type safety issues (TypeScript vs Pydantic model alignment)
        5. Missing integrations (features mentioned but not implemented)

        Be thorough and specific. Provide actionable feedback."""

    user_prompt = f"""Feature Request:
        {state['feature_request']}

        Architecture Notes:
        {state['architecture_notes']}

        Frontend Implementation:
        {state['frontend_code'][:2000]}...

        Backend Implementation:
        {state['backend_code'][:2000]}...

        Please review the integration and provide:
        1. ISSUES: List of integration problems found
        2. RECOMMENDATIONS: How to fix each issue
        3. STATUS: pass (good to ship), needs_revision (minor fixes), fail (major issues)

        Format:
        ISSUES:
        - Issue 1
        - Issue 2

        RECOMMENDATIONS:
        - Fix 1
        - Fix 2

        STATUS: [pass/needs_revision/fail]
    """

    # Use review-optimized model for integration review
    if MULTI_MODEL_AVAILABLE:
        llm = get_llm(task_type="review", temperature=0.2)
    else:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.2)
    response = llm.invoke([("system", system_prompt), ("user", user_prompt)])

    review_content = response.content
    state['integration_review'] = review_content

    # Parse issues and status
    issues = []
    status = "pass"  # Default

    lines = review_content.split('\n')
    current_section = None

    for line in lines:
        line_upper = line.strip().upper()
        if 'ISSUES:' in line_upper:
            current_section = 'issues'
        elif 'RECOMMENDATIONS:' in line_upper:
            current_section = 'recommendations'
        elif 'STATUS:' in line_upper:
            if 'NEEDS_REVISION' in line_upper or 'NEEDS REVISION' in line_upper:
                status = 'needs_revision'
            elif 'FAIL' in line_upper:
                status = 'fail'
            else:
                status = 'pass'
        elif (line.strip().startswith('-') or line.strip().startswith('*')) and current_section == 'issues':
            issue = line.strip().lstrip('-*').strip()
            if issue:
                issues.append(issue)

    state['issues_found'] = issues
    state['review_status'] = status

    print(f"\nReview Status: {status.upper()}")
    if issues:
        print(f"Issues Found: {len(issues)}")
        for issue in issues[:3]:  # Show first 3
            print(f"  - {issue}")
    else:
        print("No integration issues found!")

    return state

# ============================================================================
# PHASE 2 NODES: CODE GENERATION & FILE WRITING
# ============================================================================
def parse_tdd_node(state: DevTeamState) -> DevTeamState:
    """
    Parse TDD content if provided (Phase 2).

    If TDD is provided, extracts: tech stack, features, API specs, data models.
    Otherwise, skips parsing and continues with original workflow.
    """
    if not state.get('tdd_content'):
        print("\nNo TDD provided, using feature_request workflow")
        return state

    print("\n" + "=" * 70)
    print("TDD PARSER: Extracting Requirements from Technical Design Document")
    print("=" * 70)

    from src.agents.dev_team.parsers import parse_tdd_to_state

    # Get project type for parsing
    project_type = state.get('project_type', 'web_app')
    
    # Parse TDD into structured data (pass project_type for better feature extraction)
    parsed_data = parse_tdd_to_state(
        state['tdd_content'],
        phase=state.get('implementation_phase', 1),
        project_type=project_type
    )

    # Update state with parsed data
    for key, value in parsed_data.items():
        state[key] = value

    # Detect project type from TDD or architect state
    # Check TDD content for project type indicators
    tdd_lower = state['tdd_content'].lower()
    if 'python automation script' in tdd_lower or 'standalone script' in tdd_lower:
        state['project_type'] = 'script'
    elif 'jupyter notebook' in tdd_lower or 'data analysis notebook' in tdd_lower:
        state['project_type'] = 'notebook'
    elif 'library' in tdd_lower or 'package' in tdd_lower:
        state['project_type'] = 'library'
    elif 'api' in tdd_lower and 'frontend' not in tdd_lower:
        state['project_type'] = 'api'
    else:
        state['project_type'] = 'web_app'  # Default
    
    print(f"Detected project type: {state.get('project_type', 'web_app')}")

    # Create a feature_request from TDD features for backward compatibility
    # But validate that features match project type
    if state.get('features_to_implement'):
        features = state['features_to_implement']
        feature_names = [f['feature_name'] for f in features if f.get('feature_name')]
        
        # Validate features match project type (catch wrong extraction)
        project_type = state.get('project_type', 'web_app')
        auth_keywords = ['registration', 'login', 'authentication', 'jwt', 'user auth']
        web_app_keywords = ['frontend', 'ui', 'component', 'react', 'vue']
        
        # Check if extracted features are wrong for this project type
        features_text = ' '.join(feature_names).lower()
        has_auth_features = any(kw in features_text for kw in auth_keywords)
        has_web_app_features = any(kw in features_text for kw in web_app_keywords)
        
        # If script/notebook but extracted auth/web app features, use fallback
        if project_type in ['script', 'notebook'] and (has_auth_features or has_web_app_features):
            print(f" Warning: Extracted features ({', '.join(feature_names[:3])}) don't match project type ({project_type})")
            print("   Using fallback: building feature request from TDD content")
            
            # Build feature request from TDD content (Requirements section or Implementation Plan)
            fallback_request = None
            
            # Try to extract from TDD Requirements or Implementation Plan
            tdd_content = state.get('tdd_content', '')
            if 'promo code' in tdd_content.lower() or 'automation' in tdd_content.lower():
                if 'promo code assignment' in tdd_content.lower():
                    fallback_request = "Implement: Promo code assignment script with JSON endpoint fetching, eligibility rules, and webhook posting"
                elif 'campaign analysis' in tdd_content.lower() or 'csv' in tdd_content.lower():
                    fallback_request = "Implement: Campaign impact analysis with CSV processing, metrics computation (Open Rate, CTR, Error Rate), and recommendations"
                else:
                    fallback_request = "Implement: Python automation script for data fetching, processing, and analysis"
            elif 'notebook' in tdd_content.lower() or 'jupyter' in tdd_content.lower():
                fallback_request = "Implement: Jupyter notebook for data analysis, CSV processing, and campaign metrics computation"
            else:
                # Generic fallback based on project type
                if project_type == 'notebook':
                    fallback_request = "Implement: Data analysis notebook with CSV processing, metrics computation, and visualization"
                elif project_type == 'script':
                    fallback_request = "Implement: Python automation script for data processing and task automation"
                else:
                    fallback_request = f"Implement: {project_type.replace('_', ' ').title()} project tasks"
            
            state['feature_request'] = fallback_request
            print(f"   Fallback feature_request: {fallback_request}")
            
            # Also replace the wrong features with correct ones
            # Build new features list from fallback
            if project_type == 'notebook':
                state['features_to_implement'] = [
                    {
                        'feature_name': 'Promo Code Assignment Script',
                        'description': 'Build Python script to fetch JSON endpoints, apply eligibility rules, assign promo codes',
                        'priority': 'high',
                        'phase': '1'
                    },
                    {
                        'feature_name': 'Campaign Impact Analysis',
                        'description': 'Compute Open Rate, CTR, Error Rate per campaign and analyze pre/post impact',
                        'priority': 'high',
                        'phase': '1'
                    }
                ]
            elif project_type == 'script':
                state['features_to_implement'] = [
                    {
                        'feature_name': 'Data Fetching Script',
                        'description': 'Fetch data from JSON endpoints and process',
                        'priority': 'high',
                        'phase': '1'
                    },
                    {
                        'feature_name': 'Data Processing Script',
                        'description': 'Apply business rules, transform data, handle errors',
                        'priority': 'high',
                        'phase': '1'
                    }
                ]
        else:
            # Features look correct, use them
            state['feature_request'] = f"Implement: {', '.join(feature_names[:3])}"

        print(f"\nExtracted {len(features)} features from TDD")
        if feature_names and not (project_type in ['script', 'notebook'] and (has_auth_features or has_web_app_features)):
            print(f"Features: {', '.join(feature_names[:3])}")
        print(f"Implementation Phase: {state.get('implementation_phase', 1)}")
        print(f"Tech Stack: {state.get('tech_stack', {})}")

    return state

def extract_code_node(state: DevTeamState) -> DevTeamState:
    """
    Extract code blocks from LLM-generated markdown into file dictionaries (Phase 2).

    Parses frontend_code and backend_code markdown, extracting:
    - Code blocks by language
    - File path markers
    - Organizing into proper file structure
    """
    print("\n" + "=" * 70)
    print("CODE EXTRACTOR: Organizing Code into Files")
    print("=" * 70)

    from src.agents.dev_team.code_generator import extract_and_organize_code

    # Extract frontend files
    if state.get('frontend_code') and state['frontend_code'].strip():
        print("\nExtracting frontend files...")
        try:
            frontend_files = extract_and_organize_code(
                state['frontend_code'],
                language='typescript',
                base_path='frontend/src'
            )
            state['frontend_files'] = frontend_files
            print(f"✓ Extracted {len(frontend_files)} frontend files")
        except Exception as e:
            print(f"Error extracting frontend files: {e}")
            state['frontend_files'] = {}
    else:
        state['frontend_files'] = {}

    # Extract backend files
    if state.get('backend_code') and state['backend_code'].strip():
        print("\nExtracting backend files...")
        try:
            # Debug: Show first 500 chars of backend code to diagnose extraction issues
            backend_code_preview = state['backend_code'][:500]
            if len(state['backend_code']) > 500:
                backend_code_preview += "..."
            print(f"   Backend code preview: {backend_code_preview}")
            
            backend_files = extract_and_organize_code(
                state['backend_code'],
                language='python',
                base_path='backend/src'
            )
            state['backend_files'] = backend_files
            if len(backend_files) == 0:
                print(f"⚠️  Warning: No backend files extracted from {len(state['backend_code'])} characters")
                print("   This usually means code blocks lack file paths or proper formatting")
                # Try extracting without language filter as fallback
                from src.agents.dev_team.code_generator import extract_code_blocks
                code_blocks = extract_code_blocks(state['backend_code'])
                print(f"   Found {len(code_blocks)} total code blocks")
                for i, (lang, path, code) in enumerate(code_blocks[:3], 1):
                    print(f"   Block {i}: lang={lang}, path={path or '(none)'}, code_len={len(code)}")
            else:
                print(f"✓ Extracted {len(backend_files)} backend files")
        except Exception as e:
            print(f"Error extracting backend files: {e}")
            import traceback
            traceback.print_exc()
            state['backend_files'] = {}
    else:
        if not state.get('backend_code'):
            print("\nNo backend_code in state - backend developer may not have generated code")
        state['backend_files'] = {}

    total_files = len(state.get('frontend_files', {})) + len(state.get('backend_files', {}))
    print(f"\nTotal code files extracted: {total_files}")

    return state

def generate_scaffolding_node(state: DevTeamState) -> DevTeamState:
    """
    Generate project scaffolding and configuration files (Phase 2).

    Creates: .gitignore, README.md, package.json, requirements.txt, docker-compose.yml
    """
    print("\n" + "=" * 70)
    print("SCAFFOLDER: Generating Project Configuration")
    print("=" * 70)

    from src.agents.dev_team.code_generator import generate_gitignore, generate_readme

    config_files = {}
    tech_stack = state.get('tech_stack', {'frontend': [], 'backend': [], 'database': []})
    
    # If tech_stack is empty, try to infer from generated files
    if not any(tech_stack.values()):
        print("\n Tech stack empty, inferring from generated files...")
        tech_stack = infer_tech_stack_from_files(state)
        if any(tech_stack.values()):
            print(f"✓ Inferred tech stack: {tech_stack}")
            state['tech_stack'] = tech_stack

    # Generate .gitignore
    print("\nGenerating .gitignore...")
    config_files['.gitignore'] = generate_gitignore(tech_stack)

    # Generate README.md
    print("Generating README.md...")
    project_name = state.get('project_metadata', {}).get('project_name', 'Generated Project')
    features = state.get('features_to_implement', [])
    config_files['README.md'] = generate_readme(project_name, tech_stack, features)

    # Check if we have frontend files
    frontend_files = state.get('frontend_files', {})
    has_frontend = bool(frontend_files)
    
    # Check if we have backend files
    backend_files = state.get('backend_files', {})
    has_backend = bool(backend_files)
    
    # Generate package.json (if Node.js/React frontend)
    has_frontend_tech = any('react' in str(t).lower() or 'node' in str(t).lower() or 'next' in str(t).lower()
           for tech_list in tech_stack.values() for t in tech_list)
    
    # Check file extensions for frontend
    has_frontend_files = any(
        f.endswith(('.tsx', '.jsx', '.ts', '.js')) or 'frontend' in f.lower()
        for f in frontend_files.keys()
    )
    
    if has_frontend_tech or has_frontend_files:
        print("Generating frontend/package.json...")
        config_files['frontend/package.json'] = generate_package_json(state, tech_stack)

    # Generate requirements.txt (if Python backend)
    has_backend_tech = any('python' in str(t).lower() or 'fastapi' in str(t).lower() or 'django' in str(t).lower()
           for tech_list in tech_stack.values() for t in tech_list)
    
    # Check file extensions for backend
    has_backend_files = any(
        f.endswith('.py') or 'backend' in f.lower()
        for f in backend_files.keys()
    )
    
    if has_backend_tech or has_backend_files:
        print("Generating backend/requirements.txt...")
        config_files['backend/requirements.txt'] = generate_requirements_txt(state, tech_stack)

    # Generate docker-compose.yml (if we have frontend or backend)
    has_docker_tech = any('docker' in str(t).lower() for tech_list in tech_stack.values() for t in tech_list)
    
    if has_docker_tech or (has_frontend and has_backend):
        print("Generating docker-compose.yml...")
        config_files['docker-compose.yml'] = generate_docker_compose(state, tech_stack)

    state['config_files'] = config_files
    print(f"\n✓ Generated {len(config_files)} configuration files")

    return state

def infer_tech_stack_from_files(state: DevTeamState) -> Dict[str, List[str]]:
    """Infer technology stack from generated file extensions and content."""
    tech_stack = {'frontend': [], 'backend': [], 'database': [], 'devops': [], 'third_party': []}
    
    frontend_files = state.get('frontend_files', {})
    backend_files = state.get('backend_files', {})
    
    # Analyze frontend files
    for filepath in frontend_files.keys():
        if filepath.endswith('.tsx') or filepath.endswith('.jsx'):
            if 'react' not in tech_stack['frontend']:
                tech_stack['frontend'].append('React')
            if 'typescript' not in tech_stack['frontend'] and filepath.endswith('.tsx'):
                tech_stack['frontend'].append('TypeScript')
        elif filepath.endswith('.ts') or filepath.endswith('.js'):
            if 'TypeScript' not in tech_stack['frontend'] and filepath.endswith('.ts'):
                tech_stack['frontend'].append('TypeScript')
            if 'Node.js' not in tech_stack['frontend'] and filepath.endswith('.js'):
                tech_stack['frontend'].append('Node.js')
    
    # Analyze backend files
    for filepath in backend_files.keys():
        if filepath.endswith('.py'):
            if 'Python' not in tech_stack['backend']:
                tech_stack['backend'].append('Python')
            # Check for FastAPI
            content = backend_files.get(filepath, '').lower()
            if 'fastapi' in content and 'FastAPI' not in tech_stack['backend']:
                tech_stack['backend'].append('FastAPI')
            elif 'django' in content and 'Django' not in tech_stack['backend']:
                tech_stack['backend'].append('Django')
    
    # If we have both frontend and backend, suggest Docker
    if (tech_stack['frontend'] or frontend_files) and (tech_stack['backend'] or backend_files):
        tech_stack['devops'].append('Docker')
    
    return tech_stack

def write_files_node(state: DevTeamState) -> DevTeamState:
    """
    Write all generated files to disk (Phase 2).

    Creates directory structure and writes:
    - Frontend files
    - Backend files
    - Configuration files
    - Database files
    - Test files
    """
    print("\n" + "=" * 70)
    print("FILE WRITER: Writing Files to Disk")
    print("=" * 70)

    from pathlib import Path

    output_dir = state.get('output_directory', './generated_project')
    output_path = Path(output_dir)

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput directory: {output_path.absolute()}")

    # Collect all files (handle None values with or {})
    all_files = {}
    all_files.update(state.get('frontend_files') or {})
    all_files.update(state.get('backend_files') or {})
    all_files.update(state.get('config_files') or {})
    all_files.update(state.get('database_files') or {})
    all_files.update(state.get('test_files') or {})

    if not all_files:
        print("\n⚠ No files to write!")
        state['files_written'] = 0
        state['generated_files'] = []
        return state

    written_files = []

    print(f"\nWriting {len(all_files)} files...\n")

    for filepath, content in all_files.items():
        try:
            full_path = output_path / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

            written_files.append(str(full_path))
            print(f"  ✓ {filepath}")

        except Exception as e:
            print(f"  ✗ {filepath}: {e}")

    state['generated_files'] = written_files
    state['files_written'] = len(written_files)

    print(f"\n{'=' * 70}")
    print(f"✅ Successfully generated {len(written_files)} files in {output_dir}/")
    print(f"{'=' * 70}\n")

    return state

# Helper functions for scaffolding

def generate_package_json(state: DevTeamState, tech_stack: dict) -> str:
    """Generate package.json for frontend."""
    project_name = state.get('project_metadata', {}).get('project_name', 'frontend-app')
    safe_name = project_name.lower().replace(' ', '-').replace('_', '-')

    # Determine framework
    is_react = any('react' in str(t).lower() for tech_list in tech_stack.values() for t in tech_list)
    is_next = any('next' in str(t).lower() for tech_list in tech_stack.values() for t in tech_list)
    is_typescript = any('typescript' in str(t).lower() for tech_list in tech_stack.values() for t in tech_list)

    dependencies = {}
    dev_dependencies = {}
    scripts = {}

    if is_next:
        dependencies["next"] = "^14.0.0"
        dependencies["react"] = "^18.2.0"
        dependencies["react-dom"] = "^18.2.0"
        scripts["dev"] = "next dev"
        scripts["build"] = "next build"
        scripts["start"] = "next start"
    elif is_react:
        dependencies["react"] = "^18.2.0"
        dependencies["react-dom"] = "^18.2.0"
        dependencies["react-scripts"] = "5.0.1"
        scripts["start"] = "react-scripts start"
        scripts["build"] = "react-scripts build"
        scripts["test"] = "react-scripts test"

    if is_typescript:
        dev_dependencies["typescript"] = "^5.0.0"
        dev_dependencies["@types/react"] = "^18.2.0"
        dev_dependencies["@types/react-dom"] = "^18.2.0"
        dev_dependencies["@types/node"] = "^20.0.0"

    import json
    return json.dumps({
        "name": safe_name,
        "version": "0.1.0",
        "private": True,
        "scripts": scripts,
        "dependencies": dependencies,
        "devDependencies": dev_dependencies
    }, indent=2)

def generate_requirements_txt(state: DevTeamState, tech_stack: dict) -> str:
    """Generate requirements.txt for backend."""
    requirements = []

    # Determine framework
    is_fastapi = any('fastapi' in str(t).lower() for tech_list in tech_stack.values() for t in tech_list)
    is_django = any('django' in str(t).lower() for tech_list in tech_stack.values() for t in tech_list)

    if is_fastapi:
        requirements.extend([
            "fastapi==0.104.1",
            "uvicorn[standard]==0.24.0",
            "pydantic==2.5.0",
            "python-multipart==0.0.6"
        ])
    elif is_django:
        requirements.extend([
            "Django==4.2.0",
            "djangorestframework==3.14.0"
        ])

    # Database
    databases = tech_stack.get('database', [])
    if any('postgresql' in str(db).lower() for db in databases):
        requirements.append("psycopg2-binary==2.9.9")
        if is_fastapi:
            requirements.append("sqlalchemy==2.0.23")
    elif any('mongodb' in str(db).lower() for db in databases):
        requirements.append("pymongo==4.6.0")

    # Common utilities
    requirements.extend([
        "python-dotenv==1.0.0",
        "pytest==7.4.3"
    ])

    return '\n'.join(requirements) + '\n'

def generate_docker_compose(state: DevTeamState, tech_stack: dict) -> str:
    """Generate docker-compose.yml."""
    services = []

    # Backend service
    if tech_stack.get('backend'):
        services.append("""  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/appdb
    depends_on:
      - db
    volumes:
      - ./backend:/app
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload""")

    # Frontend service
    if tech_stack.get('frontend'):
        services.append("""  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev""")

    # Database service
    databases = tech_stack.get('database', [])
    if any('postgresql' in str(db).lower() for db in databases):
        services.append("""  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=appdb
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data""")

    volumes_section = ""
    if any('postgresql' in str(db).lower() for db in databases):
        volumes_section = "\nvolumes:\n  postgres_data:"

    return f"""version: '3.8'

services:
{chr(10).join(services)}
{volumes_section}
"""


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def create_dev_team_graph() -> StateGraph:
    """
    Create the Multi-Agent Development Team LangGraph workflow (Original - Phase 1).

 

    Workflow:

    1. Tech Lead decomposes feature request

    2. Frontend and Backend specialists work in parallel

    3. Integration Reviewer validates the integration

    4. End

    """

    workflow = StateGraph(DevTeamState)

 

    # Add nodes

    workflow.add_node("tech_lead", tech_lead_dispatcher)

    workflow.add_node("frontend_dev", frontend_developer)

    workflow.add_node("backend_dev", backend_developer)

    workflow.add_node("reviewer", integration_reviewer)

 

    # Define workflow

    workflow.set_entry_point("tech_lead")

 

    # After tech lead, both specialists work in parallel

    workflow.add_edge("tech_lead", "frontend_dev")

    workflow.add_edge("tech_lead", "backend_dev")

 

    # Both must complete before review

    workflow.add_edge("frontend_dev", "reviewer")

    workflow.add_edge("backend_dev", "reviewer")

 

    # Review ends the workflow

    workflow.add_edge("reviewer", END)

 

    return workflow.compile()

 

 

def create_dev_team_graph_v2() -> StateGraph:
    """
    Create the Phase 2 Enhanced Development Team LangGraph workflow.

    Workflow:
    1. Parse TDD (if provided) to extract requirements
    2. Tech Lead decomposes into tasks
    3. Frontend and Backend specialists generate code in parallel
    4. Extract code blocks into file dictionaries
    5. Generate project scaffolding (configs, README, etc.)
    6. Integration Reviewer validates
    7. Write all files to disk
    8. End
    """
    workflow = StateGraph(DevTeamState)

    # Add all nodes (original + Phase 2)
    workflow.add_node("parse_tdd", parse_tdd_node)  # NEW
    workflow.add_node("tech_lead", tech_lead_dispatcher)
    workflow.add_node("frontend_dev", frontend_developer)
    workflow.add_node("backend_dev", backend_developer)
    workflow.add_node("extract_code", extract_code_node)  # NEW
    workflow.add_node("generate_scaffolding", generate_scaffolding_node)  # NEW
    workflow.add_node("reviewer", integration_reviewer)
    workflow.add_node("write_files", write_files_node)  # NEW

    # Define Phase 2 workflow
    workflow.set_entry_point("parse_tdd")

    # Parse TDD -> Tech Lead
    workflow.add_edge("parse_tdd", "tech_lead")

    # Tech Lead -> Both specialists (parallel)
    workflow.add_edge("tech_lead", "frontend_dev")
    workflow.add_edge("tech_lead", "backend_dev")

    # Both specialists -> Extract Code
    workflow.add_edge("frontend_dev", "extract_code")
    workflow.add_edge("backend_dev", "extract_code")

    # Extract Code -> Generate Scaffolding
    workflow.add_edge("extract_code", "generate_scaffolding")

    # Generate Scaffolding -> Integration Review
    workflow.add_edge("generate_scaffolding", "reviewer")

    # Integration Review -> Write Files
    workflow.add_edge("reviewer", "write_files")

    # Write Files -> END
    workflow.add_edge("write_files", END)

    return workflow.compile()


# ============================================================================
# MAIN EXECUTION FUNCTIONS
# ============================================================================

def run_dev_team(feature_request: str) -> DevTeamState:
    """
    Run the multi-agent development team on a feature request (Original - Phase 1).

    Args:
        feature_request: High-level feature description

    Returns:
        Final state with generated code and review
    """
    # Create graph
    app = create_dev_team_graph()

    # Initialize state
    initial_state = DevTeamState(
        feature_request=feature_request,
        frontend_tasks=[],
        backend_tasks=[],
        architecture_notes="",
        frontend_code="",
        frontend_context="",
        frontend_status="pending",
        backend_code="",
        backend_context="",
        backend_status="pending",
        integration_review="",
        issues_found=[],
        review_status="pending",
        iteration_count=0,
        needs_revision=False
    )

    # Run workflow
    final_state = app.invoke(initial_state)

    return final_state

def run_dev_team_v2(feature_request: str = "", tdd_content: str = "", implementation_phase: int = 1, output_directory: str = "./generated_project", project_type: Optional[str] = None) -> DevTeamState:
    """
    Run the Phase 2 Enhanced development team (TDD → Code Files).

    Args:
        feature_request: High-level feature description (optional if TDD provided)
        tdd_content: Full TDD markdown from Phase 1 (optional)
        implementation_phase: Which phase to implement (1, 2, or 3)
        output_directory: Where to write generated files
        project_type: Project type from architect (web_app, script, notebook, etc.)

    Returns:
        Final state with generated files written to disk
    """
    # Create Phase 2 graph
    app = create_dev_team_graph_v2()

    # Initialize state with all required and optional fields
    initial_state = DevTeamState(
        # Phase 1 fields
        feature_request=feature_request or "",
        frontend_tasks=[],
        backend_tasks=[],
        architecture_notes="",
        frontend_code="",
        frontend_context="",
        frontend_status="pending",
        backend_code="",
        backend_context="",
        backend_status="pending",
        integration_review="",
        issues_found=[],
        review_status="pending",
        iteration_count=0,
        needs_revision=False,
        # Phase 2 fields
        tdd_content=tdd_content,
        tdd_parsed=False,
        project_metadata=None,
        project_type=project_type,  # Set project type if provided
        tech_stack=None,
        features_to_implement=None,
        api_specification=None,
        data_model=None,
        security_requirements=None,
        implementation_phase=implementation_phase,
        frontend_files=None,
        backend_files=None,
        config_files=None,
        database_files=None,
        test_files=None,
        generated_files=None,
        validation_results=None,
        validation_errors=None,
        output_directory=output_directory,
        files_written=None
    )

    # Run Phase 2 workflow
    final_state = app.invoke(initial_state)

    return final_state


if __name__ == "__main__":
    # Test with a simple feature request
    print("\n" + "=" * 70)
    print("MULTI-AGENT DEVELOPMENT TEAM - TEST RUN")
    print("=" * 70)

    test_feature = "Build a user authentication system with email/password login, JWT tokens, and a protected dashboard"

    result = run_dev_team(test_feature)

    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"\nReview Status: {result['review_status']}")
    print(f"Issues Found: {len(result['issues_found'])}")
    print("\nFrontend Code Preview:")
    print(result['frontend_code'][:500] + "...")
    print("\nBackend Code Preview:")
    print(result['backend_code'][:500] + "...")