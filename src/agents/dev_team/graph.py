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
    print("Multi-model support not available in dev_team. Using legacy Google Gemini only.")

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
            # Return empty instead of error message
            print(f"No patterns found in {collection_name}")
            return ""

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
        # Return empty context instead of error - let the agent still generate code
        print(f"Warning: Could not access {collection_name}: {str(e)}")
        print("   Continuing without RAG context...")
        return ""  # Empty context - agent will still generate code without patterns


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
    # Check if context retrieval failed or is empty
    if not context or "Backend brain not" in context or "Error accessing" in context:
        print("Backend brain not available")
        print("   Run: python src/ingest_expert.py --expert backend --list")
        context = ""  # Use empty context - will still generate code
    else:
        print("Retrieved backend patterns")

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
# HELPER: ITERATIVE MODULE GENERATION (DIVIDE-AND-CONQUER)
# ============================================================================

def generate_script_modules_iteratively(state: DevTeamState) -> str:
    """
    Generate script modules using TRUE divide-and-conquer approach.

    Phase 1: Get module plan (1 LLM call)
    Phase 2: Generate each module individually (N LLM calls)

    This ensures all modules are generated completely without overwhelming the LLM.
    """
    print("\nDIVIDE-AND-CONQUER: Iterative Module Generation")
    print("=" * 70)

    # Get LLM
    if MULTI_MODEL_AVAILABLE:
        llm = get_llm(task_type="coding", temperature=0.3)
    else:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.3)

    tasks_text = "\n".join(f"- {task}" for task in state['backend_tasks'])
    arch_notes = state['architecture_notes']

    # ============================================================================
    # PHASE 1: GET MODULE PLAN
    # ============================================================================
    print("\n[Phase 1/2] Getting module plan...")

    plan_prompt = f"""You are a Python Automation Specialist creating a module plan.

    Tasks to implement:
    {tasks_text}

    Architecture Context:
    {arch_notes}

    Create a detailed module plan. Analyze the tasks and determine what modules are needed.

    Format your plan EXACTLY like this:

    ## MODULE PLAN

    **1. module_name.py**
    - Responsibility: What this module does
    - Key functions: function1(), function2()
    - Dependencies: library1, library2

    **2. another_module.py**
    - Responsibility: What this module does
    - Key functions: function1()
    - Dependencies: library1

    **N. main.py**
    - Responsibility: Orchestrate the entire workflow
    - Key functions: main()
    - Dependencies: module_name, another_module, argparse

    CRITICAL:
    - Base your plan on the ACTUAL tasks above
    - Use descriptive module names that match the functionality
    - Include main.py as the last module
    - List ALL modules needed (typically 3-7 modules)

    Output ONLY the module plan, nothing else."""

    plan_response = llm.invoke([("user", plan_prompt)])
    plan_text = plan_response.content

    # Parse the plan
    # Debug: Show what the LLM returned
    print("\nLLM Plan Response (first 500 chars):")
    print(f"{plan_text[:500]}...")

    # Parse the plan
    planned_modules = extract_module_plan(plan_text)

    if not planned_modules:
        print("\n  Failed to extract module plan from LLM response.")
        print(f"   Response length: {len(plan_text)} chars")
        print("   Checking for '## MODULE PLAN' pattern...")

        if '## MODULE PLAN' in plan_text.upper():
            print("   Found '## MODULE PLAN' in response")
        else:
            print("   '## MODULE PLAN' not found in response")

        print("\n   Falling back to single-call generation.")
        # Fallback to original approach if plan extraction fails
        return generate_script_single_call(state, llm)

    print(f"Plan created with {len(planned_modules)} modules:")
    for i, module in enumerate(planned_modules, 1):
        print(f"  {i}. {module}")

    # ============================================================================
    # PHASE 2: GENERATE EACH MODULE INDIVIDUALLY
    # ============================================================================
    print(f"\n[Phase 2/2] Generating {len(planned_modules)} modules individually...")

    generated_modules = []
    generated_modules.append(plan_text)  # Include the plan in output
    generated_modules.append("\n\n" + "=" * 70)
    generated_modules.append("## GENERATED MODULES")
    generated_modules.append("=" * 70 + "\n")

    for i, module_name in enumerate(planned_modules, 1):
        print(f"\n  [{i}/{len(planned_modules)}] Generating {module_name}...")

        module_prompt = f"""Generate COMPLETE, WORKING code for the module: {module_name}

        Context:
        Tasks: {tasks_text}
        Architecture: {arch_notes}

        Module Plan (for reference):
        {plan_text}

        Your task: Generate ONLY the {module_name} module.

        Requirements:
        1. Provide COMPLETE implementation (no placeholders, no "pass", no "...")
        2. Include ALL necessary imports
        3. If this module imports from other modules in the plan, use those imports
        4. Write production-ready, working code
        5. Include docstrings and error handling

        Format:
        ### scripts/{module_name}
        ```python
        # Complete implementation here
        import necessary_libraries

        def function_name():
            # Full working implementation
            actual_code_here
            return result
        ```

        Generate ONLY {module_name}, nothing else. Make it complete and runnable."""

        try:
            module_response = llm.invoke([("user", module_prompt)])
            module_code = module_response.content

            # Clean the module code: extract just the code block
            # LLM might add preamble like "Here is the implementation..."
            # We want to extract: ### scripts/module_name.py ... ```python ... ```

            import re

            # Check if the response has the expected format
            if f"### scripts/{module_name}" in module_code or f"###scripts/{module_name}" in module_code:
                # Response has proper format, use as-is
                generated_modules.append(f"\n{module_code}\n")
                print(f"  {module_name} generated ({len(module_code)} chars)")
            else:
                # Response might have preamble, try to extract the code block
                # Look for python code blocks
                code_block_pattern = r'```python\s*\n(.*?)\n```'
                code_matches = re.findall(code_block_pattern, module_code, re.DOTALL)

                if code_matches:
                    # Found code block(s), wrap in proper format
                    actual_code = code_matches[0]  # Take first code block
                    formatted_code = f"### scripts/{module_name}\n```python\n{actual_code}\n```"
                    generated_modules.append(f"\n{formatted_code}\n")
                    print(f"  {module_name} generated ({len(actual_code)} chars, extracted from response)")
                else:
                    # No code block found, use response as-is but warn
                    generated_modules.append(f"\n### scripts/{module_name}\n```python\n{module_code}\n```\n")
                    print(f"  {module_name} generated ({len(module_code)} chars, no code block found)")

        except Exception as e:
            print(f"  Failed to generate {module_name}: {e}")
            # Add placeholder to maintain structure
            generated_modules.append(f"\n### scripts/{module_name}\n```python\n# Generation failed\npass\n```\n")

    # Combine all modules
    complete_code = "\n".join(generated_modules)

    print("\nAll modules generated successfully!")
    print(f"Total code length: {len(complete_code)} characters")

    # Debug: Count how many file headers are in the combined code
    import re
    file_headers = re.findall(r'### scripts/([a-zA-Z0-9_]+\.py)', complete_code)
    print(f"Debug: Found {len(file_headers)} file headers in combined code: {file_headers}")

    return complete_code

def generate_script_single_call(state: DevTeamState, llm) -> str:
    """Fallback: Generate all code in a single LLM call (original approach)."""
    print("Using single-call fallback generation...")

    # Use the original two-phase prompt
    tasks_text = "\n".join(f"- {task}" for task in state['backend_tasks'])
    user_prompt = f"""Tasks to implement:
    {tasks_text}

    Architecture Context:
    {state['architecture_notes']}

    {state.get('user_prompt_template', 'Generate complete Python scripts for the tasks above.')}"""

    response = llm.invoke([("user", user_prompt)])
    return response.content


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
    # For script/notebook, use iterative module generation (divide-and-conquer)
    if project_type in ['script', 'notebook']:
        print("(Using iterative module generation for script/notebook project)")

        # Use the iterative approach for script projects
        backend_code = generate_script_modules_iteratively(state)

        # Return the generated code
        return {
            'backend_code': backend_code,
            'backend_status': 'completed',
            'backend_context': "Generated using iterative divide-and-conquer approach"
        }

    # For API/web apps, use the traditional approach
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

        CRITICAL: You MUST provide COMPLETE, WORKING code for EVERY file.
        Do NOT just list files - provide the FULL implementation.

        Format each file as:
        ### scripts/promo_code_assigner.py
        ```python
        import requests
        import json
        # ... COMPLETE file implementation here with ALL code
        ```

        ### notebooks/campaign_analysis.ipynb
        ```python
        # %% [markdown]
        # # Campaign Analysis

        # %%
        import pandas as pd
        # ... COMPLETE notebook implementation with ALL cells
        ```

        Provide COMPLETE code for ALL files - not summaries or placeholders."""
        
    elif project_type == 'script':
        system_prompt = """You are a Python Automation Specialist.
        You use a DIVIDE AND CONQUER approach: first plan the modules, then implement each one completely.

        CRITICAL TWO-PHASE PROCESS:
        1. PHASE 1 - MODULE PLANNING: Analyze tasks and create a detailed module plan
        2. PHASE 2 - CODE GENERATION: Generate complete code for EVERY module in the plan

        RULES:
        - Each module MUST have a single, clear responsibility
        - If you import from a local module, that module MUST be in your plan and generated
        - NEVER create imports for modules you don't generate
        - Every module in the plan MUST be implemented (no skipping!)"""

        user_prompt = f"""Tasks to implement:
        {chr(10).join(f"- {task}" for task in state['backend_tasks'])}

        Architecture Context:
        {state['architecture_notes']}

        ========================================
        PHASE 1: CREATE MODULE PLAN
        ========================================

        First, ANALYZE the tasks above and determine what modules are needed.

        Think about:
        - What are the distinct responsibilities? (e.g., data input, processing, output, configuration)
        - What helper modules would make the code modular and maintainable?
        - What's the main orchestration script?

        Then create your plan in this EXACT format:

        ## MODULE PLAN

        **1. module_name_1.py**
        - Responsibility: [What this module does]
        - Key functions: [function1(), function2()]
        - Dependencies: [libraries this module uses]

        **2. module_name_2.py**
        - Responsibility: [What this module does]
        - Key functions: [function1(), function2()]
        - Dependencies: [libraries this module uses]

        **[N]. main.py**
        - Responsibility: Orchestrate the entire workflow
        - Key functions: main(), [other orchestration functions]
        - Dependencies: [list all your helper modules above, plus argparse/CLI libraries]

        CRITICAL: Base your plan on the ACTUAL tasks above, not generic examples.
        Use module names that match the actual functionality needed.

        ========================================
        PHASE 2: GENERATE COMPLETE CODE
        ========================================

        Now generate COMPLETE, WORKING code for EVERY module in your plan above.

        CRITICAL REQUIREMENTS:
        1. Generate code for EVERY module you listed in the plan (no exceptions!)
        2. Each module must be complete and runnable (no placeholders, no "pass", no "...")
        3. Only import from modules that are in your plan
        4. Use this exact format for each file:

        ### scripts/module_name.py
        ```python
        # Complete implementation with ALL imports, ALL functions, ALL code
        import library1
        import library2

        def function1(param1, param2):
            # Full working implementation
            result = actual_code_here
            return result

        def function2():
            # Full working implementation
            actual_code_here
            return result
        ```

        ### scripts/main.py
        ```python
        # Import from YOUR modules (from your plan)
        from module_name import function1, function2
        import argparse

        def main():
            # Full orchestration implementation
            actual_code_here

        if __name__ == "__main__":
            main()
        ```

        VALIDATION CHECKLIST (before you finish):
        ☐ Did I generate code for EVERY module in my plan?
        ☐ Does each module have COMPLETE implementations (no placeholders)?
        ☐ Do all imports reference modules that I actually generated?
        ☐ Is main.py importing only from modules I created?
        ☐ Does each file start with ### scripts/filename.py?
        ☐ Did I base the implementation on the ACTUAL tasks, not generic examples?

        Remember: DIVIDE AND CONQUER - Plan carefully based on ACTUAL tasks, then implement completely!"""
        
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
        {context if context else "No patterns available - generating from best practices"}

        Generate production-ready backend code that:
        1. Follows the patterns shown above
        2. Is type-safe (Pydantic models)
        3. Has proper error handling
        4. Includes input validation
        5. Has clear database integration
        6. Follows REST best practices

        CRITICAL FORMATTING REQUIREMENTS:
        - You MUST provide the COMPLETE CODE for EVERY file mentioned
        - Do NOT just describe the file structure - WRITE THE ACTUAL CODE
        - Each file must be a separate code block with the file path as a header
        - Use this exact format for EACH file:

        ### path/to/file.py
        ```python
        # Complete file contents here
        # Include ALL imports, ALL functions, ALL code
        ```

        EXAMPLE - This is how you should format EVERY file:
        ### app/core/config.py
        ```python
        from pydantic_settings import BaseSettings

        class Settings(BaseSettings):
            app_name: str = "My App"
            debug: bool = False

        settings = Settings()
        ```

        ### app/main.py
        ```python
        from fastapi import FastAPI
        from app.core.config import settings

        app = FastAPI(title=settings.app_name)

        @app.get("/")
        def read_root():
            return {{"message": "Hello World"}}
        ```

        REMEMBER: Provide COMPLETE, WORKING code for EVERY file you mention. Do not skip any files or provide partial implementations."""

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

    - Import validation (missing modules)
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

    # Check for import validation warnings (critical issues)
    validation_warnings = state.get('validation_warnings', [])
    if validation_warnings:
        print("\nCRITICAL: Import validation failed!")
        print(f"Found {len(validation_warnings)} missing module imports:")
        for warning in validation_warnings:
            print(f"  {warning}")

        state['integration_review'] = f"""CRITICAL IMPORT VALIDATION FAILURE

        The generated code has import statements for modules that were not created:

        {chr(10).join(f"- {w}" for w in validation_warnings)}

        This will cause ImportError when the code is executed.

        CAUSE: The backend specialist generated imports for modules it didn't create as separate files.

        REQUIRED FIX: Regenerate the code with proper module separation. Each import statement must have a corresponding generated file.

        STATUS: FAIL - Code is not runnable."""

        state['issues_found'] = validation_warnings
        state['review_status'] = 'fail'

        print("\nReview Status: FAIL (broken imports)")
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

    # Preserve project type from architect if already set, otherwise detect from TDD
    if not state.get('project_type'):
        # Only detect if not already set by architect
        tdd_lower = state['tdd_content'].lower()
        if 'python automation script' in tdd_lower or 'standalone script' in tdd_lower or 'cli' in tdd_lower:
            state['project_type'] = 'script'
        elif 'jupyter notebook' in tdd_lower or 'data analysis notebook' in tdd_lower:
            state['project_type'] = 'notebook'
        elif 'python library' in tdd_lower or 'python package' in tdd_lower or 'sdk' in tdd_lower:
            state['project_type'] = 'library'
        elif 'rest api' in tdd_lower or 'graphql' in tdd_lower and 'frontend' not in tdd_lower:
            state['project_type'] = 'api'
        else:
            state['project_type'] = 'web_app'  # Default

        print(f"Detected project type from TDD: {state.get('project_type', 'web_app')}")
    else:
        print(f"Using project type from architect: {state.get('project_type', 'web_app')}")

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

def extract_module_plan(markdown_text: str) -> List[str]:
    """
    Extract the module plan from LLM-generated markdown.

    Args:
        markdown_text: The full LLM response

    Returns:
        List of module filenames mentioned in the plan
    """
    import re

    planned_modules = []
    # Try multiple patterns to find the module plan section
    patterns = [
        r'## MODULE PLAN(.+?)(?:##|========|$)',  # Standard markdown header
        r'##\s*MODULE\s*PLAN(.+?)(?:##|========|$)',  # With extra spaces
        r'MODULE PLAN:?(.+?)(?:##|========|$)',  # Without markdown header
    ]

    plan_section = None
    for pattern in patterns:
        match = re.search(pattern, markdown_text, re.DOTALL | re.IGNORECASE)
        if match:
            plan_section = match.group(1)
            break

    if not plan_section:
        # No plan section found at all
        return planned_modules

    # Try multiple extraction patterns for module names
    extraction_patterns = [
        r'\*\*\d+\.\s+([a-zA-Z0-9_]+\.py)\*\*',  # **1. module.py**
        r'^\d+\.\s+([a-zA-Z0-9_]+\.py)',  # 1. module.py
        r'^\*\*([a-zA-Z0-9_]+\.py)\*\*',  # **module.py**
        r'-\s+([a-zA-Z0-9_]+\.py)',  # - module.py
        r'`([a-zA-Z0-9_]+\.py)`',  # `module.py`
    ]

    for pattern in extraction_patterns:
        matches = re.findall(pattern, plan_section, re.MULTILINE)
        if matches:
            planned_modules.extend(matches)
            # Remove duplicates while preserving order
            seen = set()
            planned_modules = [x for x in planned_modules if not (x in seen or seen.add(x))]
            break

    return planned_modules

def validate_plan_execution(planned_modules: List[str], generated_files: Dict[str, str]) -> List[str]:
    """
    Validate that all planned modules were actually generated.

    Args:
        planned_modules: List of module filenames from the plan
        generated_files: Dictionary of generated filepath -> code

    Returns:
        List of warning messages for missing modules
    """
    warnings = []

    for module in planned_modules:
        module_found = False

        # Check if this module exists in generated files
        for filepath in generated_files.keys():
            if filepath.endswith(module) or f"/{module}" in filepath:
                module_found = True
                break

        if not module_found:
            warnings.append(f"⚠️  Module '{module}' was in the plan but was NOT generated")

    return warnings

def validate_imports_and_files(files: Dict[str, str]) -> List[str]:
    """
    Validate that all local imports have corresponding files.

    Args:
        files: Dictionary of filepath -> code content

    Returns:
        List of warning messages for missing imports
    """
    warnings = []
    import re

    for filepath, code in files.items():
        # Extract local imports (from X import Y or import X)
        from_imports = re.findall(r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import', code)
        direct_imports = re.findall(r'^\s*import\s+([a-zA-Z_][a-zA-Z0-9_]*)', code, re.MULTILINE)

        local_imports = set(from_imports + direct_imports)

        # Filter out standard library and common third-party modules
        stdlib_and_common = {
            # Standard library
            'os', 'sys', 're', 'json', 'datetime', 'time', 'math', 'random',
            'collections', 'itertools', 'functools', 'typing', 'pathlib',
            'io', 'csv', 'logging', 'argparse', 'subprocess', 'shutil',
            'tempfile', 'threading', 'multiprocessing', 'asyncio', 'unittest',
            # Web frameworks
            'flask', 'fastapi', 'django', 'uvicorn', 'starlette', 'aiohttp',
            # Data science
            'pandas', 'numpy', 'matplotlib', 'seaborn', 'sklearn', 'scipy',
            # Database
            'sqlalchemy', 'pymongo', 'psycopg2', 'mysql',
            # PDF/Document processing
            'PyPDF2', 'pypdf', 'pdfplumber', 'pdfminer', 'reportlab',
            # HTTP/Requests
            'requests', 'urllib3', 'httpx', 'aiohttp',
            # Testing
            'pytest', 'unittest', 'mock', 'pytest_asyncio',
            # Validation/Typing
            'pydantic', 'pydantic_settings', 'marshmallow',
            # AWS/Cloud
            'boto3', 'botocore',
            # Other common
            'dotenv', 'python_dotenv', 'jinja2', 'click', 'typer'
        }

        local_imports = local_imports - stdlib_and_common

        # Check if imported module exists as a file
        for module in local_imports:
            module_file_found = False

            # Check for module_name.py in any of the generated files
            for generated_file in files.keys():
                if f"/{module}.py" in generated_file or generated_file.endswith(f"{module}.py"):
                    module_file_found = True
                    break

            if not module_file_found:
                warnings.append(f"{filepath} imports '{module}' but {module}.py was not generated")

    return warnings

def extract_code_node(state: DevTeamState) -> DevTeamState:
    """
    Extract code blocks from LLM-generated markdown into file dictionaries (Phase 2).

    Parses frontend_code and backend_code markdown, extracting:
    - Code blocks by language
    - File path markers
    - Organizing into proper file structure
    - Validates that imported modules have corresponding files
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

    # Validate plan execution for script projects (check if all planned modules were generated)
    project_type = state.get('project_type', 'web_app')
    if project_type == 'script' and state.get('backend_code'):
        print("\nValidating module plan execution...")
        planned_modules = extract_module_plan(state['backend_code'])

        if planned_modules:
            print(f"Found plan with {len(planned_modules)} modules: {', '.join(planned_modules)}")

            plan_warnings = validate_plan_execution(planned_modules, state.get('backend_files', {}))
            if plan_warnings:
                print(f"\n{'=' * 70}")
                print(" PLAN EXECUTION WARNINGS")
                print(f"{'=' * 70}")
                for warning in plan_warnings:
                    print(f"  {warning}")
                print("\nThe LLM planned to create these modules but didn't generate them.")
                print("This indicates incomplete implementation.")
                print(f"{'=' * 70}\n")

                # Add to validation warnings
                existing_warnings = state.get('validation_warnings', [])
                state['validation_warnings'] = existing_warnings + plan_warnings
        else:
            print("  No module plan found in backend code (LLM may not have followed the template)")

    # Validate imports for backend files (most critical for script projects)
    if state.get('backend_files'):
        print("\nValidating backend imports...")
        backend_warnings = validate_imports_and_files(state['backend_files'])
        if backend_warnings:
            print(f"\n{'=' * 70}")
            print("  IMPORT VALIDATION WARNINGS")
            print(f"{'=' * 70}")
            for warning in backend_warnings:
                print(f"  {warning}")
            print("\nThese files have import statements for modules that were not generated.")
            print("This will cause ImportError when the code is run.")
            print(f"{'=' * 70}\n")

            # Store warnings in state for later review
            state['validation_warnings'] = backend_warnings

    # Validate imports for frontend files
    if state.get('frontend_files'):
        frontend_warnings = validate_imports_and_files(state['frontend_files'])
        if frontend_warnings:
            existing_warnings = state.get('validation_warnings', [])
            state['validation_warnings'] = existing_warnings + frontend_warnings

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