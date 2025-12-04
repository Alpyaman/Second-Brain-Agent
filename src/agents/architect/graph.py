"""
Architect Session LnagGraph Workflow

This module implements an interactive architectural design session that:
1. Retrieves relevant code examples from your codebase
2. Fetches your coding preferences
3. Generates a design document aligned with your style
4. Supports iterative refinement based on feedback
"""

import os
from typing import Literal
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langgraph.graph import StateGraph, END

from src.agents.architect.state import ArchitectState
from src.core.config import EMBEDDING_MODEL, CHROMA_DB_DIR
from dotenv import load_dotenv
from tools.memory import get_relevant_preferences

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def parse_job_description(state: ArchitectState) -> ArchitectState:
    """
    Parse a raw job description from Upwork/Freelancer to extract key requirements.

    This node uses LLM to structure unstructured job postings into actionable requirements.
    """
    if not state.get('is_job_description', False):
        # Not a job description, skip parsing
        print("Not a job description, skipping parsing...")
        return state

    print("Parsing job description to extract requirements...")

    llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.2)

    system_prompt = """You are an expert at analyzing freelance job postings and extracting structured requirements.

    Your task is to parse a raw job description and extract:
    1. Project Title: A clear, concise project name
    2. Project Description: High-level overview of what needs to be built
    3. Required Features: List of specific features/functionality mentioned
    4. Technical Requirements: Technologies, frameworks, or technical constraints mentioned
    5. Budget & Timeline: Any mentioned budget, deadline, or time constraints

    Output your analysis in a structured format with clear sections."""

    user_prompt = f"""Analyze this job posting and extract the key information:

    {state['goal']}

    Please provide a structured analysis."""

    messages = [("system", system_prompt), ("user", user_prompt)]
    response = llm.invoke(messages)

    # Store the parsed analysis (we'll use this to enhance the goal)
    parsed_content = response.content

    # Extract specific fields using another LLM call for structured extraction
    extraction_prompt = f"""From this analysis, extract ONLY the following in this exact format:

    {parsed_content}

    Format your response as:
    PROJECT_TITLE: [extracted title]
    DESCRIPTION: [brief description]
    FEATURES: [comma-separated list]
    TECH: [comma-separated list]
    TIMELINE: [extracted timeline/budget info]"""

    extraction_messages = [("user", extraction_prompt)]
    extraction_response = llm.invoke(extraction_messages)
    extracted = extraction_response.content

    # Parse the extracted fields
    project_title = ""
    project_description = ""
    required_features = []
    tech_requirements = []
    budget_timeline = ""

    for line in extracted.split('\n'):
        line = line.strip()
        if line.startswith('PROJECT_TITLE:'):
            project_title = line.replace('PROJECT_TITLE:', '').strip()
        elif line.startswith('DESCRIPTION:'):
            project_description = line.replace('DESCRIPTION:', '').strip()
        elif line.startswith('FEATURES:'):
            features_str = line.replace('FEATURES:', '').strip()
            required_features = [f.strip() for f in features_str.split(',') if f.strip()]
        elif line.startswith('TECH:'):
            tech_str = line.replace('TECH:', '').strip()
            tech_requirements = [t.strip() for t in tech_str.split(',') if t.strip()]
        elif line.startswith('TIMELINE:'):
            budget_timeline = line.replace('TIMELINE:', '').strip()

    # Update state
    state['project_title'] = project_title
    state['project_description'] = project_description
    state['required_features'] = required_features
    state['tech_requirements'] = tech_requirements
    state['budget_timeline'] = budget_timeline

    # Create a structured goal from the parsed information
    structured_goal = f"""Project: {project_title}

    Description: {project_description}

    Required Features:
    {chr(10).join(f'- {feature}' for feature in required_features)}

    Technical Requirements:
    {chr(10).join(f'- {tech}' for tech in tech_requirements)}

    Timeline/Budget: {budget_timeline}"""

    # Override the goal with structured version
    state['goal'] = structured_goal

    print(f"Parsed job description: {project_title}")
    print(f"Extracted {len(required_features)} features and {len(tech_requirements)} tech requirements")

    return state

def analyze_goal(state: ArchitectState) -> ArchitectState:
    """
    Analyze the architectural goal and extract key requirements.

    This node parses the high-level goal to understand what needs to be built.
    """
    print("Analyzing architectural goal...")
    print(f"Goal: {state['goal']}")

    # Initialize state fields if this is the first iteration
    if 'design_history' not in state or state['design_history'] is None:
        state['design_history'] = []
    if 'iteration_count' not in state or state['iteration_count'] is None:
        state['iteration_count'] = 0
    if 'refinement_needed' not in state:
        state['refinement_needed'] = False
    
    return state

def retrieve_context(state: ArchitectState) -> ArchitectState:
    """
    Retrieve relevant code examples from the coding_brain collection and user preferences
    from memory.
    """
    print("Retrieving code context and preferences...")

    # Fetch user preferences
    print("Fetching coding preferences...")
    preferences = get_relevant_preferences(state['goal'])
    state['preferences'] = preferences if preferences else "No specific preferences found."

    # Retrieve relevant code examples from coding_brain
    try:
        print(f"Searching coding_brain for: '{state['goal']}'")

        # Initialize embeddings
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={'device': 'cpu'}, encode_kwargs={'normalize_embeddings': True})

        # Connect to coding_brain collection
        vectorstore = Chroma(collection_name="coding_brain", embedding_function=embeddings, persist_directory=str(CHROMA_DB_DIR))

        # Perform similarity search
        relevant_docs = vectorstore.similarity_search(state['goal'], k=8)

        if relevant_docs:
            print(f"Found {len(relevant_docs)} relevant code examples")

            # Format code examples with metadata
            code_examples = []
            for i, doc in enumerate(relevant_docs, 1):
                file_path = doc.metadata.get('file_path', 'unknown')
                classes = doc.metadata.get('classes', [])
                functions = doc.metadata.get('functions', [])

                example = f"**Example {i}** (from {file_path})\n"
                if classes:
                    example += f"Classes {', '.join(classes)}\n"
                if functions:
                    example += f"Functions: {', '.join(functions)}\n"
                example += f"```python\n{doc.page_content}\n```\n"

                code_examples.append(example)
            
            state['code_examples'] = "\n\n".join(code_examples)
        else:
            print("No code examples found in coding_brain")
            state['code_examples'] = "No relevant code examples found in your codebase."

    except Exception as e:
        print(f"Could not retrieve from coding_brain: {e}")
        state['code_examples'] = "No code context available (codin_brain collection not found)."

    return state

def generate_design(state: ArchitectState) -> ArchitectState:
    """
    Generate an architectural design document based on:
    - The user's goal
    - Their existing codebase patterns
    - Their coding preferences
    """
    print("Generating architectural design...")

    state['iteration_count'] += 1
    iteration = state['iteration_count']

    # Build the prompt based on whether this is initial or refinement
    if iteration == 1:
        # Initial design
        system_prompt = f"""You are an expert software architect creating a professional Technical Design Document.

        Your task is to create a detailed, client-ready architectural design document that demonstrates:
        1. Deep understanding of the requirements
        2. Professional software engineering expertise
        3. Alignment with best practices and user's existing patterns
        4. Clear implementation roadmap

        **User's Coding Preferences:**
        {state['preferences']}

        **Code Examples from User's Codebase (for style alignment):**
        {state['code_examples']}

        Generate a PROFESSIONAL Technical Design Document with the following structure:

        # 1. EXECUTIVE SUMMARY
        - Brief overview of the project (2-3 paragraphs)
        - Key objectives and success criteria
        - Expected business value and impact

        # 2. REQUIREMENTS ANALYSIS
        - Functional requirements (what the system must do)
        - Non-functional requirements (performance, scalability, security)
        - Constraints and assumptions

        # 3. SYSTEM ARCHITECTURE
        - High-level architecture diagram description
        - System components and their responsibilities
        - Component interactions and data flow
        - Architectural patterns and rationale

        # 4. TECHNOLOGY STACK
        - Recommended technologies with justification
        - Frontend technologies (if applicable)
        - Backend technologies
        - Database and storage solutions
        - DevOps and deployment tools
        - Third-party services and integrations

        # 5. DATA MODEL
        - Key entities and their attributes
        - Entity relationships (ERD description)
        - Data access patterns
        - Indexing and optimization strategies

        # 6. API DESIGN (if applicable)
        - RESTful API endpoints or GraphQL schema
        - Request/response formats
        - Authentication and authorization
        - Rate limiting and security measures

        # 7. CODE STRUCTURE & ORGANIZATION
        - Directory structure
        - Module organization
        - Naming conventions
        - Code organization principles

        # 8. SECURITY CONSIDERATIONS
        - Authentication and authorization strategy
        - Data encryption (at rest and in transit)
        - Input validation and sanitization
        - Security best practices

        # 9. SCALABILITY & PERFORMANCE
        - Expected load and growth projections
        - Scalability strategies
        - Caching strategies
        - Performance optimization approaches

        # 10. IMPLEMENTATION PLAN
        - Phase 1: Core foundation and MVP features
        - Phase 2: Extended features
        - Phase 3: Optimization and polish
        - Timeline estimates for each phase
        - Key milestones and deliverables

        # 11. TESTING STRATEGY
        - Unit testing approach
        - Integration testing
        - End-to-end testing
        - Performance testing

        # 12. DEPLOYMENT & OPERATIONS
        - Deployment pipeline
        - Monitoring and logging
        - Backup and disaster recovery
        - Maintenance considerations

        # 13. RISKS & MITIGATION
        - Technical risks
        - Project risks
        - Mitigation strategies

        Make it professional, comprehensive, and client-ready. Use specific technical details where appropriate."""

        user_prompt = f"""Project Goal/Requirements: {state['goal']}

        Please generate a comprehensive Technical Design Document for this project."""

    else:
        # Refinement based on feedback
        system_prompt = f"""You are an expert software architect refining a Technical Design Document based on client feedback.

        **Previous Design:**
        {state['design_history'][-1] if state['design_history'] else 'N/A'}

        **Client Feedback:**
        {state['feedback']}

        **User's Coding Preferences:**
        {state['preferences']}

        **Code Examples from User's Codebase:**
        {state['code_examples']}

        Refine the Technical Design Document based on the feedback while maintaining professional quality.

        Address the feedback by:
        - Adjusting components, patterns, or approaches as requested
        - Adding clarifications or additional details
        - Improving alignment with client preferences
        - Enhancing technical depth where needed

        Maintain the comprehensive structure:
        1. Executive Summary
        2. Requirements Analysis
        3. System Architecture
        4. Technology Stack
        5. Data Model
        6. API Design
        7. Code Structure & Organization
        8. Security Considerations
        9. Scalability & Performance
        10. Implementation Plan
        11. Testing Strategy
        12. Deployment & Operations
        13. Risks & Mitigation

        Keep it professional and client-ready."""

        user_prompt = f"""Project Goal: {state['goal']}

        Please refine the Technical Design Document based on the feedback provided."""

    # Initialize Gemini
    llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.4)

    # Generate the design
    messages = [("system", system_prompt), ("user", user_prompt)]

    response = llm.invoke(messages)
    design = response.content

    # Store in history and current state
    state['design_history'].append(design)
    state['design_document'] = design

    print(f"Design v{iteration} generated {len(design)} characters.")

    return state

def should_refine(state: ArchitectState) -> Literal["refine", "end"]:
    """
    Decision node: determine if refinement is needed based on feedback.
    """
    if state.get('feedback') and state ['feedback'].strip():
        return "refine"
    return "end"

def create_architect_graph() -> StateGraph:
    """
    Create the Architect Session LangGraph workflow.

    Workflow:
    1. parse_job_description (if applicable) -> analyze_goal -> retrieve_context -> generate_design
    2. If feedback provided -> generate_design (refinement)
    3. Otherwise -> END
    """
    # Create the graph
    workflow = StateGraph(ArchitectState)

    # Add nodes
    workflow.add_node("parse_job_description", parse_job_description)
    workflow.add_node("analyze_goal", analyze_goal)
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("generate_design", generate_design)

    # Define edges
    workflow.set_entry_point("parse_job_description")
    workflow.add_edge("parse_job_description", "analyze_goal")
    workflow.add_edge("analyze_goal", "retrieve_context")
    workflow.add_edge("retrieve_context", "generate_design")

    # Conditional edge: refine or end
    workflow.add_conditional_edges("generate_design", should_refine, {"refine": "generate_design", "end": END})

    return workflow.compile()

def run_architect_session(goal: str, feedback: str = None, is_job_description: bool = False) -> ArchitectState:
    """
    Run an Architect Session for the given goal or job description.

    Args:
        goal: High-level architectural goal or raw job description
        feedback: Optional feedback for refinement
        is_job_description: Flag indicating if the input is a job posting (enables parsing)

    Returns:
        The final state with design document
    """
    # Create the graph
    app = create_architect_graph()

    # Initialize state
    initial_state = ArchitectState(
        goal=goal,
        is_job_description=is_job_description,
        project_title=None,
        project_description=None,
        required_features=None,
        tech_requirements=None,
        budget_timeline=None,
        code_examples="",
        preferences="",
        design_document="",
        design_history=[],
        feedback=feedback,
        iteration_count=0,
        refinement_needed=False
    )

    # Run the workflow
    final_state = app.invoke(initial_state)

    return final_state