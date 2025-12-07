"""
Architect Session LnagGraph Workflow

This module implements an interactive architectural design session that:
1. Retrieves relevant code examples from your codebase
2. Fetches your coding preferences
3. Generates a design document aligned with your style
4. Supports iterative refinement based on feedback

Features:
- Multi-provider LLM support via llm_factory
- Task-optimized model selection
- Backward compatible with legacy Google Gemini
"""

import os
from typing import Literal, Optional, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Import multi-model support
try:
    from src.core.llm_factory import get_llm
    MULTI_MODEL_AVAILABLE = True
except ImportError:
    MULTI_MODEL_AVAILABLE = False
    print("⚠️  Multi-model support not available in architect. Using legacy Google Gemini only.")
from langgraph.graph import StateGraph, END

from src.agents.architect.state import ArchitectState, ProjectType
from src.core.config import EMBEDDING_MODEL, CHROMA_DB_DIR
from dotenv import load_dotenv
from src.tools.memory import get_relevant_preferences

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def detect_project_type(goal: str, required_features: Optional[List[str]] = None) -> ProjectType:
    """
    Detect project type from job description and features.
    
    Returns: 'web_app', 'script', 'notebook', 'library', 'api', or 'unknown'
    """
    goal_lower = goal.lower()
    features_text = " ".join(required_features).lower() if required_features else ""
    combined = f"{goal_lower} {features_text}"
    
    # Keywords for each project type
    script_keywords = ['script', 'automation', 'fetch', 'process', 'analyze data', 'csv', 
                      'json endpoint', 'webhook', 'single-use', 'automate', 'cron job']
    notebook_keywords = ['jupyter', 'notebook', 'analysis', 'data analysis', 'csv analysis',
                        'compute', 'analyze', 'metrics', 'recommendations', 'insights']
    library_keywords = ['library', 'package', 'module', 'pip install', 'import', 'sdk']
    api_keywords = ['api', 'rest api', 'api endpoint', 'microservice', 'backend api', 
                   'service', 'endpoints']
    web_app_keywords = ['web app', 'website', 'frontend', 'user interface', 'ui', 
                       'login', 'registration', 'dashboard', 'admin panel', 'client-side',
                       'react', 'vue', 'angular', 'fastapi', 'django', 'flask',
                       'web application', 'web-based', 'browser', 'responsive',
                       'spa', 'single page application', 'full-stack', 'fullstack',
                       'microservices', 'message queue', 'kafka', 'rabbitmq',
                       'real-time', 'websocket', 'notification system', 'alert system']
    
    # Score each type
    scores = {
        'script': sum(1 for keyword in script_keywords if keyword in combined),
        'notebook': sum(1 for keyword in notebook_keywords if keyword in combined),
        'library': sum(1 for keyword in library_keywords if keyword in combined),
        'api': sum(1 for keyword in api_keywords if keyword in combined),
        'web_app': sum(1 for keyword in web_app_keywords if keyword in combined)
    }
    
    # Return type with highest score, or 'unknown' if no clear match
    max_score = max(scores.values())
    if max_score == 0:
        return 'unknown'
    
    # Priority rules for disambiguation:
    # 1. If mentions frontend frameworks (React/Vue/Angular) or FastAPI/Django -> web_app
    frontend_frameworks = ['react', 'vue', 'angular', 'svelte', 'next.js', 'nuxt']
    backend_frameworks = ['fastapi', 'django', 'flask', 'express']
    has_frontend = any(fw in combined for fw in frontend_frameworks)
    has_backend_framework = any(fw in combined for fw in backend_frameworks)
    has_dashboard = 'dashboard' in combined
    has_microservices = 'microservice' in combined or 'message queue' in combined
    
    if (has_frontend or (has_backend_framework and has_dashboard) or has_microservices) and scores['web_app'] > 0:
        return 'web_app'
    
    # 2. If script and notebook both have high scores, prefer notebook for analysis
    if scores['notebook'] >= 2 and scores['script'] >= 2:
        return 'notebook'
    
    # 3. Return highest scoring type
    for project_type, score in scores.items():
        if score == max_score:
            return project_type  # type: ignore
    
    return 'unknown'

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

    # Use LLM factory if available, otherwise fallback to Google Gemini
    if MULTI_MODEL_AVAILABLE:
        llm = get_llm(task_type="parsing")
    else:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.2)

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

    # Detect project type early
    project_type = detect_project_type(state['goal'])
    state['project_type'] = project_type
    print(f"Detected project type: {project_type}")

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

    # Get project type to adjust the prompt
    project_type = state.get('project_type', 'unknown')
    
    # Build the prompt based on whether this is initial or refinement
    if iteration == 1:
        # Adjust prompt based on project type
        if project_type == 'script':
            project_guidance = """
        **PROJECT TYPE: Python Automation Script**
        - Focus on standalone Python scripts, not web applications
        - No need for frontend/backend separation
        - Focus on: data fetching, processing, file I/O, webhooks
        - Output: Single or multiple Python files (.py), requirements.txt
        """
        elif project_type == 'notebook':
            project_guidance = """
        **PROJECT TYPE: Data Analysis Notebook**
        - Focus on Jupyter notebooks, data analysis, visualization
        - Include: data loading, analysis, metrics, visualizations
        - Output: .ipynb files, data processing scripts
        - Focus on pandas, matplotlib, data insights
        """
        elif project_type == 'library':
            project_guidance = """
        **PROJECT TYPE: Python Library/Package**
        - Focus on reusable modules, classes, functions
        - Include: package structure, setup.py, API design
        - Output: Package directory structure, setup.py, README
        """
        elif project_type == 'api':
            project_guidance = """
        **PROJECT TYPE: REST API/Backend Service**
        - Focus on API endpoints, backend logic, database
        - No frontend needed (API only)
        - Output: FastAPI/Flask routes, database models, requirements.txt
        """
        else:  # web_app or unknown
            project_guidance = """
        **PROJECT TYPE: Web Application**
        - Standard web app with frontend and backend
        - Include: UI components, API endpoints, database
        - Output: Frontend code, backend API, full-stack structure
        """
        
        # Initial design
        system_prompt = f"""You are an expert software architect creating a professional Technical Design Document.
        
        {project_guidance}

        Your task is to create a detailed, client-ready architectural design document that demonstrates:
        1. Deep understanding of the requirements
        2. Professional software engineering expertise
        3. Alignment with best practices and user's existing patterns
        4. Clear implementation roadmap

        **User's Coding Preferences:**
        {state['preferences']}

        **Code Examples from User's Codebase (for style alignment):**
        {state['code_examples']}

        Generate a PROFESSIONAL Technical Design Document. 
        
        **IMPORTANT**: Keep the document concise and focused. Maximum recommended length: 50,000 characters.
        Do NOT repeat sections or content. Each section should be clear and specific.
        
        Structure the document as follows:

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

    # Initialize LLM - use powerful model for reasoning/design tasks
    if MULTI_MODEL_AVAILABLE:
        llm = get_llm(task_type="reasoning")
    else:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.4)

    # Generate the design
    messages = [("system", system_prompt), ("user", user_prompt)]

    response = llm.invoke(messages)
    design = response.content

    # Apply size limits to prevent excessive output
    MAX_TDD_SIZE = 500000  # 500KB limit
    if len(design) > MAX_TDD_SIZE:
        print(f"⚠️  Warning: TDD is very large ({len(design)} chars), truncating to {MAX_TDD_SIZE} chars")
        design = design[:MAX_TDD_SIZE]
        design += "\n\n[Document truncated due to size limit]"
    
    # Check for repetition (simple heuristic: if same paragraph appears 3+ times)
    paragraphs = design.split('\n\n')
    if len(paragraphs) > 100:  # Very large number of paragraphs suggests repetition
        unique_paragraphs = set(paragraphs)
        if len(unique_paragraphs) < len(paragraphs) * 0.5:  # Less than 50% unique
            print("⚠️  Warning: Detected potential repetition in TDD, using unique content only")
            design = '\n\n'.join(unique_paragraphs)
    
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
        project_type=None,  # Will be detected during parsing
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