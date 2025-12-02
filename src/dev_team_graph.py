"""
Multi-Agent Development Team LangGraph Workflow

This module implements a software development team where each agent has:
1. DISTINCT DATA: Specialized RAG collections (frontend_brain, backend_brain)
2. DISTINCT CAPABILITIES: Domain-specific tools and expertise

This is NOT "just wrapping an LLM" - each agent learns from different codebases.
"""

import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

from dev_team_state import DevTeamState
from config import EMBEDDING_MODEL, CHROMA_DB_DIR

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")


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
    - Frontend tasks (UI, components, client-side logic)
    - Backend tasks (API endpoints, database, business logic)
    - Architecture notes (how components integrate)

    This is the "orchestrator" that enables specialization.
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

    # Build prompt for decomposition
    system_prompt = """You are a Tech Lead responsible for decomposing feature requests into frontend and backend tasks.
        Your job is to analyze the feature and:
        1. Identify what needs to be built on the frontend (UI, components, client logic)
        2. Identify what needs to be built on the backend (APIs, database, business logic)
        3. Describe how they integrate (architecture notes)

        Be specific and actionable. Each task should be clear enough for a specialist to implement independently."""

    user_prompt = f"""Feature Request: {state['feature_request']}
        Please decompose this into:
        1. Frontend Tasks: List of specific frontend work items
        2. Backend Tasks: List of specific backend work items
        3. Architecture Notes: How the frontend and backend integrate

        Format your response as:
        FRONTEND_TASKS:
        - Task 1
        - Task 2

        BACKEND_TASKS:
        - Task 1
        - Task 2

        ARCHITECTURE:
        High-level integration notes
    """

    # Generate decomposition
    llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=0.3)
    response = llm.invoke([("system", system_prompt), ("user", user_prompt)])
    decomposition = response.content

    # Parse response (simple parsing - can be improved)
    frontend_tasks = []
    backend_tasks = []
    architecture_notes = ""

    lines = decomposition.split('\n')
    current_section = None

    for line in lines:
        line = line.strip()
        if 'FRONTEND_TASKS' in line.upper():
            current_section = 'frontend'
        elif 'BACKEND_TASKS' in line.upper():
            current_section = 'backend'
        elif 'ARCHITECTURE' in line.upper():
            current_section = 'architecture'
        elif line.startswith('-') or line.startswith('*'):
            task = line.lstrip('-*').strip()
            if current_section == 'frontend':
                frontend_tasks.append(task)
            elif current_section == 'backend':
                backend_tasks.append(task)
        elif current_section == 'architecture' and line:
            architecture_notes += line + "\n"

    # Update state
    state['frontend_tasks'] = frontend_tasks if frontend_tasks else ["Implement frontend for: " + state['feature_request']]
    state['backend_tasks'] = backend_tasks if backend_tasks else ["Implement backend for: " + state['feature_request']]
    state['architecture_notes'] = architecture_notes or "Frontend calls backend APIs."

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
    """
    print("\n" + "=" * 70)
    print("FRONTEND SPECIALIST: Implementing UI")
    print("=" * 70)

    state['frontend_status'] = 'in_progress'

    # Combine tasks into a single query
    tasks_summary = " + ".join(state['frontend_tasks'])
    print(f"Tasks: {tasks_summary}\n")

    # CRITICAL: Query frontend_brain (NOT backend_brain!)
    print("Retrieving patterns from frontend_brain...")
    context = query_expert_brain(query=tasks_summary, collection_name="frontend_brain", k=5)
    state['frontend_context'] = context

    if "No patterns found" in context or "Error accessing" in context:
        print("Frontend brain not available")
        print("   Run: python src/ingest_expert.py --expert frontend --list")
        state['frontend_code'] = "# Frontend brain not initialized. Please ingest expert knowledge."
        state['frontend_status'] = 'completed'
        return state

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

        Provide the complete implementation with file structure."""

    llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=0.3)
    response = llm.invoke([("system", system_prompt), ("user", user_prompt)])

    state['frontend_code'] = response.content
    state['frontend_status'] = 'completed'

    print(f"Generated frontend code ({len(state['frontend_code'])} characters)")

    return state


# ============================================================================
# NODE 3: BACKEND DEVELOPER
# ============================================================================

def backend_developer(state: DevTeamState) -> DevTeamState:
    """
    Backend Specialist implements API/server-side features.

    KEY: Queries backend_brain (FastAPI, Django patterns) for context.
    This gives it DISTINCT expertise from frontend developer.
    """
    print("\n" + "=" * 70)
    print("BACKEND SPECIALIST: Implementing API")
    print("=" * 70)

    state['backend_status'] = 'in_progress'

    # Combine tasks into a single query
    tasks_summary = " + ".join(state['backend_tasks'])
    print(f"Tasks: {tasks_summary}\n")

    # CRITICAL: Query backend_brain (NOT frontend_brain!)
    print("Retrieving patterns from backend_brain...")
    context = query_expert_brain(query=tasks_summary, collection_name="backend_brain", k=5)
    state['backend_context'] = context

    if "No patterns found" in context or "Error accessing" in context:
        print("Backend brain not available")
        print("   Run: python src/ingest_expert.py --expert backend --list")
        state['backend_code'] = "# Backend brain not initialized. Please ingest expert knowledge."
        state['backend_status'] = 'completed'
        return state

    print("✓ Retrieved backend patterns\n")

    # Generate backend code using retrieved patterns
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

        Provide the complete implementation with file structure."""

    llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=0.3)
    response = llm.invoke([("system", system_prompt), ("user", user_prompt)])

    state['backend_code'] = response.content
    state['backend_status'] = 'completed'

    print(f"Generated backend code ({len(state['backend_code'])} characters)")

    return state


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

    llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=0.2)
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
# GRAPH CONSTRUCTION
# ============================================================================

def create_dev_team_graph() -> StateGraph:
    """
    Create the Multi-Agent Development Team LangGraph workflow.

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


# ============================================================================
# MAIN EXECUTION FUNCTION
# ============================================================================

def run_dev_team(feature_request: str) -> DevTeamState:
    """
    Run the multi-agent development team on a feature request.

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