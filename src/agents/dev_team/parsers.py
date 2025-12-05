"""
TDD (Technical Design Document) Parser

This module provides utilities to parse Technical Design Documents from Phase 1 (Architect)
and extract actionable information for code generation.

Features:
- Sequential parsing (backward compatible)
- Parallel parsing (optimized for speed)
- Multi-provider LLM support via llm_factory
"""
import re
from typing import Dict, List, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Import new multi-model utilities
try:
    from src.core.llm_factory import get_llm
    from src.core.async_llm_executor import AsyncLLMExecutor
    MULTI_MODEL_AVAILABLE = True
except ImportError:
    MULTI_MODEL_AVAILABLE = False
    print("⚠️  Multi-model support not available. Using legacy Google Gemini only.")

# OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
# OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def parse_tdd_sections(tdd_content: str) -> Dict[str, str]:
    """
    Parse a TDD markdown document into its constituent sections.

    Args:
        tdd_content: Full TDD markdown content

    Returns:
        Dictionary mapping section names to their content
    """
    sections = {}

    # Pattern to match section headers (# 1. SECTION NAME or ## Section Name)
    section_pattern = r'^#+\s+(?:\d+\.\s+)?(.+?)$'

    lines = tdd_content.split('\n')
    current_section = None
    current_content = []

    for line in lines:
        # Check if this is a section header
        match = re.match(section_pattern, line)
        if match:
            # Save previous section
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()

            # Start new section
            current_section = match.group(1).strip().upper()
            current_content = []
        else:
            # Add to current section
            if current_section:
                current_content.append(line)

    # Save last section
    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()

    return sections

def extract_technology_stack(tdd_content: str) -> Dict[str, List[str]]:
    """
    Extract technology stack from TDD.

    Returns:
        Dict with keys: frontend, backend, database, devops, third_party
    """
    sections = parse_tdd_sections(tdd_content)
    tech_section = sections.get('TECHNOLOGY STACK', '')

    if not tech_section:
        return {
            'frontend': [],
            'backend': [],
            'database': [],
            'devops': [],
            'third_party': []
        }

    # Use LLM to extract structured tech stack - fast parsing model
    if MULTI_MODEL_AVAILABLE:
        llm = get_llm(task_type="parsing", temperature=0.1)
    else:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.1)

    prompt = f"""Extract the technology stack from this section and format as:
    FRONTEND: technology1, technology2
    BACKEND: technology1, technology2
    DATABASE: technology1, technology2
    DEVOPS: technology1, technology2
    THIRD_PARTY: technology1, technology2

    Technology Stack Section:
    {tech_section}

    Output only the formatted list above."""

    response = llm.invoke([("user", prompt)])
    content = response.content

    # Parse the response
    tech_stack = {
        'frontend': [],
        'backend': [],
        'database': [],
        'devops': [],
        'third_party': []
    }

    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('FRONTEND:'):
            tech_stack['frontend'] = [t.strip() for t in line.replace('FRONTEND:', '').split(',') if t.strip()]
        elif line.startswith('BACKEND:'):
            tech_stack['backend'] = [t.strip() for t in line.replace('BACKEND:', '').split(',') if t.strip()]
        elif line.startswith('DATABASE:'):
            tech_stack['database'] = [t.strip() for t in line.replace('DATABASE:', '').split(',') if t.strip()]
        elif line.startswith('DEVOPS:'):
            tech_stack['devops'] = [t.strip() for t in line.replace('DEVOPS:', '').split(',') if t.strip()]
        elif line.startswith('THIRD_PARTY:'):
            tech_stack['third_party'] = [t.strip() for t in line.replace('THIRD_PARTY:', '').split(',') if t.strip()]

    return tech_stack

def extract_api_endpoints(tdd_content: str) -> List[Dict[str, str]]:
    """
    Extract API endpoint specifications from TDD.

    Returns:
        List of dicts with keys: method, path, description, request, response
    """
    sections = parse_tdd_sections(tdd_content)
    api_section = sections.get('API DESIGN', '')

    if not api_section:
        return []

    # Use LLM to extract API endpoints - fast parsing model
    if MULTI_MODEL_AVAILABLE:
        llm = get_llm(task_type="parsing", temperature=0.1)
    else:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.1)

    prompt = f"""Extract all API endpoints from this section. For each endpoint, provide:
    METHOD: GET/POST/PUT/DELETE/PATCH
    PATH: /api/endpoint
    DESCRIPTION: What the endpoint does
    REQUEST: Request body/params
    RESPONSE: Response format

    Format each endpoint like:
    ---
    METHOD: POST
    PATH: /api/users
    DESCRIPTION: Create a new user
    REQUEST: {{"email": string, "password": string}}
    RESPONSE: {{"id": int, "email": string, "created_at": datetime}}
    ---

    API Design Section:
    {api_section}

    Output only the formatted endpoints."""

    response = llm.invoke([("user", prompt)])
    content = response.content

    # Parse endpoints
    endpoints = []
    endpoint_blocks = content.split('---')

    for block in endpoint_blocks:
        if not block.strip():
            continue

        endpoint = {}
        for line in block.split('\n'):
            line = line.strip()
            if line.startswith('METHOD:'):
                endpoint['method'] = line.replace('METHOD:', '').strip()
            elif line.startswith('PATH:'):
                endpoint['path'] = line.replace('PATH:', '').strip()
            elif line.startswith('DESCRIPTION:'):
                endpoint['description'] = line.replace('DESCRIPTION:', '').strip()
            elif line.startswith('REQUEST:'):
                endpoint['request'] = line.replace('REQUEST:', '').strip()
            elif line.startswith('RESPONSE:'):
                endpoint['response'] = line.replace('RESPONSE:', '').strip()

        if endpoint.get('method') and endpoint.get('path'):
            endpoints.append(endpoint)

    return endpoints

def extract_data_model(tdd_content: str) -> Dict[str, Dict[str, str]]:
    """
    Extract data model/entities from TDD.

    Returns:
        Dict mapping entity names to their field definitions
        Example: {"User": {"id": "int", "email": "string", "created_at": "datetime"}}
    """
    sections = parse_tdd_sections(tdd_content)
    data_section = sections.get('DATA MODEL', '')

    if not data_section:
        return {}

    # Use LLM to extract data model - fast parsing model
    if MULTI_MODEL_AVAILABLE:
        llm = get_llm(task_type="parsing", temperature=0.1)
    else:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.1)

    prompt = f"""Extract all entities and their fields from this data model section.
    Format each entity like:
    ---
    ENTITY: EntityName
    FIELD: field_name type (description)
    FIELD: another_field type (description)
    ---

    Data Model Section:
    {data_section}

    Output only the formatted entities."""

    response = llm.invoke([("user", prompt)])
    content = response.content

    # Parse entities
    data_model = {}
    entity_blocks = content.split('---')

    for block in entity_blocks:
        if not block.strip():
            continue

        entity_name = None
        fields = {}

        for line in block.split('\n'):
            line = line.strip()
            if line.startswith('ENTITY:'):
                entity_name = line.replace('ENTITY:', '').strip()
            elif line.startswith('FIELD:'):
                field_info = line.replace('FIELD:', '').strip()
                # Parse "field_name type (description)"
                parts = field_info.split(' ', 1)
                if len(parts) >= 2:
                    field_name = parts[0]
                    field_type = parts[1].split('(')[0].strip()
                    fields[field_name] = field_type

        if entity_name and fields:
            data_model[entity_name] = fields

    return data_model

def extract_features_to_implement(tdd_content: str, phase: Optional[int] = 1, project_type: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Extract specific features to implement from TDD implementation plan.

    Args:
        tdd_content: Full TDD markdown
        phase: Which implementation phase to extract (1, 2, or 3). If None, extracts all.
        project_type: Project type (web_app, script, notebook, etc.) to guide extraction

    Returns:
        List of dicts with keys: feature_name, description, priority, phase
    """
    sections = parse_tdd_sections(tdd_content)
    impl_section = sections.get('IMPLEMENTATION PLAN', '')

    if not impl_section:
        # Fallback to requirements
        impl_section = sections.get('REQUIREMENTS ANALYSIS', '')

    if not impl_section:
        return []

    # Use LLM to extract features - fast parsing model
    if MULTI_MODEL_AVAILABLE:
        llm = get_llm(task_type="parsing", temperature=0.1)
    else:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.1)

    phase_filter = f"Focus on Phase {phase} features only." if phase else "Extract features from all phases."
    
    # Add project type context to avoid wrong defaults
    project_type_guidance = ""
    if project_type == 'script':
        project_type_guidance = "\n\nIMPORTANT: This is a Python script/automation project. Extract features related to scripts, data processing, automation tasks. Do NOT extract web app features like authentication, registration, or UI components."
    elif project_type == 'notebook':
        project_type_guidance = "\n\nIMPORTANT: This is a data analysis notebook project. Extract features related to data analysis, CSV processing, metrics computation, visualizations. Do NOT extract web app features like authentication or API endpoints."
    elif project_type == 'library':
        project_type_guidance = "\n\nIMPORTANT: This is a Python library/package project. Extract features related to reusable modules, functions, classes. Do NOT extract web app features."
    elif project_type == 'api':
        project_type_guidance = "\n\nIMPORTANT: This is an API/backend-only project. Extract features related to API endpoints, backend logic, database. Do NOT extract frontend UI features."

    prompt = f"""Extract implementable features from this implementation plan.
    {phase_filter}
    {project_type_guidance}

    Extract ONLY features that are actually mentioned in the implementation plan.
    Do NOT add generic features like "User Authentication" unless explicitly mentioned.
    Focus on the specific requirements and features described.

    For each feature, provide:
    FEATURE: Feature name
    DESCRIPTION: What needs to be built
    PRIORITY: high/medium/low
    PHASE: 1/2/3

    Format each feature like:
    ---
    FEATURE: Promo Code Assignment Script
    DESCRIPTION: Build Python script to fetch JSON endpoints, apply eligibility rules, assign promo codes
    PRIORITY: high
    PHASE: 1
    ---

    Implementation Plan:
    {impl_section[:10000]}  # Limit to first 10KB to avoid token limits

    Output only the formatted features."""

    response = llm.invoke([("user", prompt)])
    content = response.content

    # Parse features
    features = []
    feature_blocks = content.split('---')

    for block in feature_blocks:
        if not block.strip():
            continue

        feature = {}
        for line in block.split('\n'):
            line = line.strip()
            if line.startswith('FEATURE:'):
                feature['feature_name'] = line.replace('FEATURE:', '').strip()
            elif line.startswith('DESCRIPTION:'):
                feature['description'] = line.replace('DESCRIPTION:', '').strip()
            elif line.startswith('PRIORITY:'):
                feature['priority'] = line.replace('PRIORITY:', '').strip()
            elif line.startswith('PHASE:'):
                feature['phase'] = line.replace('PHASE:', '').strip()

        if feature.get('feature_name'):
            features.append(feature)

    return features

def extract_security_requirements(tdd_content: str) -> List[str]:
    """
    Extract security requirements from TDD.

    Returns:
        List of security requirements
    """
    sections = parse_tdd_sections(tdd_content)
    security_section = sections.get('SECURITY CONSIDERATIONS', '')

    if not security_section:
        return []

    # Extract bullet points or paragraphs as requirements
    requirements = []
    lines = security_section.split('\n')

    for line in lines:
        line = line.strip()
        if line.startswith('-') or line.startswith('*') or line.startswith('•'):
            requirements.append(line.lstrip('-*• ').strip())
        elif line and len(line) > 20 and not line.startswith('#'):
            # Paragraph describing a requirement
            requirements.append(line)

    return requirements

def extract_project_metadata(tdd_content: str) -> Dict[str, str]:
    """
    Extract project metadata from TDD header.

    Returns:
        Dict with keys: project_name, version, generated_date
    """
    metadata = {
        'project_name': 'Unnamed Project',
        'version': '1',
        'generated_date': 'Unknown'
    }

    lines = tdd_content.split('\n')
    for line in lines[:20]:  # Check first 20 lines for metadata
        line = line.strip()
        if line.startswith('**Project:**'):
            metadata['project_name'] = line.replace('**Project:**', '').strip()
        elif line.startswith('**Version:**'):
            metadata['version'] = line.replace('**Version:**', '').strip()
        elif line.startswith('**Generated:**'):
            metadata['generated_date'] = line.replace('**Generated:**', '').strip()

    return metadata

def parse_tdd_to_state(tdd_content: str, phase: Optional[int] = 1, project_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Parse a complete TDD document into a state dictionary for the dev_team agent.

    Args:
        tdd_content: Full TDD markdown content
        phase: Which implementation phase to focus on (1, 2, or 3)
        project_type: Project type to guide feature extraction

    Returns:
        Dictionary with parsed TDD information ready for dev_team state
    """
    # Check if parallel parsing is enabled
    use_parallel = os.getenv("ENABLE_PARALLEL_PARSING", "true").lower() == "true"

    if use_parallel and MULTI_MODEL_AVAILABLE:
        return parse_tdd_to_state_parallel(tdd_content, phase, project_type)
    else:
        return parse_tdd_to_state_sequential(tdd_content, phase, project_type)


def parse_tdd_to_state_sequential(tdd_content: str, phase: Optional[int] = 1, project_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Sequential (legacy) parsing - processes one extraction at a time.
    """
    print("Parsing TDD document...")

    # Extract all components (pass project_type to feature extraction)
    metadata = extract_project_metadata(tdd_content)
    tech_stack = extract_technology_stack(tdd_content)
    features = extract_features_to_implement(tdd_content, phase, project_type)
    api_endpoints = extract_api_endpoints(tdd_content)
    data_model = extract_data_model(tdd_content)
    security_reqs = extract_security_requirements(tdd_content)

    print(f"Extracted: {len(features)} features, {len(api_endpoints)} API endpoints, {len(data_model)} entities")

    return {
        'project_metadata': metadata,
        'tech_stack': tech_stack,
        'features_to_implement': features,
        'api_specification': {
            'endpoints': api_endpoints,
            'base_url': '/api',  # Default, can be customized
            'version': 'v1'
        },
        'data_model': data_model,
        'security_requirements': security_reqs,
        'implementation_phase': phase,
        'tdd_parsed': True
    }


def parse_tdd_to_state_parallel(tdd_content: str, phase: Optional[int] = 1, project_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Parallel (optimized) parsing - processes multiple extractions simultaneously.

    This can reduce parsing time by 50-70% by running independent LLM calls in parallel.
    """
    print("Parsing TDD document (parallel mode)...")

    # Metadata and security don't need LLM, extract immediately
    metadata = extract_project_metadata(tdd_content)
    security_reqs = extract_security_requirements(tdd_content)

    # Define parallel tasks for LLM-based extraction
    with AsyncLLMExecutor(max_workers=4) as executor:
        tasks = [
            lambda: extract_technology_stack(tdd_content),
            lambda: extract_features_to_implement(tdd_content, phase, project_type),
            lambda: extract_api_endpoints(tdd_content),
            lambda: extract_data_model(tdd_content)
        ]

        task_names = [
            "Extract Technology Stack",
            "Extract Features",
            "Extract API Endpoints",
            "Extract Data Model"
        ]

        # Run all extractions in parallel
        results = executor.run_parallel(tasks, task_names=task_names)

        tech_stack, features, api_endpoints, data_model = results

    print(f"Extracted: {len(features)} features, {len(api_endpoints)} API endpoints, {len(data_model)} entities")

    return {
        'project_metadata': metadata,
        'tech_stack': tech_stack,
        'features_to_implement': features,
        'api_specification': {
            'endpoints': api_endpoints,
            'base_url': '/api',  # Default, can be customized
            'version': 'v1'
        },
        'data_model': data_model,
        'security_requirements': security_reqs,
        'implementation_phase': phase,
        'tdd_parsed': True
    }