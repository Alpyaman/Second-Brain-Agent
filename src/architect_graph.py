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
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langgraph.graph import StateGraph, END

from architect_state import ArchitectState
from config import EMBEDDING_MODEL, CHROMA_DB_DIR
from dotenv import load_dotenv
from tools.memory import get_relevant_preferences

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")

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
        system_prompt = f"""You are an expert software architect helping design a system.
        
        Your task is to create a detailed architectural design document based on:
        1. The user's high-level goal
        2. Examples from their existing codebase (to match their coding style)
        3. Their stated preferences
        
        **User Preferences:**
        {state['preferences']}

        **Code Examples from User's Codebase:**
        {state['code_examples']}

        Generate a comprehensive design document with:
        - **Overview**: High-level description of the system.
        - **Architecture**: System components and their interactions
        - **Technology Stack**: Recommended technologies (based on user's existing stack)
        - **Data Model**: Key entities and relationships
        - **API Design**: Key endpoints/interfaces (if applicable)
        - **Code Structure**: Recommended directory/module organization
        - **Implementation Plan**: Phased approach to building this
        
        Use the user's existing code patterns and preferences as a guide. Be specific and actionable."""

        user_prompt = f"""Goal: {state['goal']}
        Please generate an architectural design document for this goal."""

    else:
        # Refinement based on feedback
        system_prompt = f"""You are an expert software architect refining a design based on user feedback.
        **Previous Design:**
        {state['design_history'][-1] if state['design_history'] else 'N/A'}

        **User Feedback:**
        {state['feedback']}

        **User Preferences:**
        {state['preferences']}

        **Code Examples from User's Codebase:**
        {state['code_examples']}

        Refine the architectural design based on the feedback. Maintain the overall structure but adjust:
        - Components, patterns, or approaches the user wants changed
        - Any clarifications or additions requested
        - Better alignment with their preferences or code style
        
        Generate the refined design document with the same structure:
        - Overview
        - Architecture
        - Technology Stack
        - Data Model
        - API Design
        - Code Structure
        - Implementation Plan"""

        user_prompt = f"""Goal: {state['goal']}

        Please refine the design based on my feedback."""

    # Initialize Gemini
    llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=0.4)

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
    1. anaylze_goal -> retrieve_context -> generate design
    2. If feedback provided -> generate_design (refinement)
    3. Otherwise -> END
    """
    # Create the graph
    workflow = StateGraph(ArchitectState)

    # Add nodes
    workflow.add_node("analyze_goal", analyze_goal)
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("generate_design", generate_design)

    # Define edges
    workflow.set_entry_point("analyze_goal")
    workflow.add_edge("analyze_goal", "retrieve_context")
    workflow.add_edge("retrieve_context", "generate_design")

    # Conditional edge: refine or end
    workflow.add_conditional_edges("generate_design", should_refine, {"refine": "generate_design", "end": END})
    
    return workflow.compile()

def run_architect_session(goal:str, feedback: str = None) -> ArchitectState:
    """
    Run an Architect Session for the given goal.

    Args:
        goal: High-level architectural goal
        feedback: Optional feedback for refinement

    Returns:
        The final state with design document
    """
    # Create the graph
    app = create_architect_graph()

    # Initialize state
    initial_state = ArchitectState(goal=goal, code_examples="", preferences="",
        design_document="", design_history="", feedback=feedback, iteration_count=0, refinement_needed=False)
    
    # Run the workflow
    final_state = app.invoke(initial_state)

    return final_state