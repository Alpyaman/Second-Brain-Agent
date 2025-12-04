"""
Second-Brain-Agent Unified CLI

A unified command-line interface for all Second Brain agent functionality.
Uses --mode argument to select different agent capabilities:

- briefing:  Run morning briefing workflow (Chief of Staff)
- query:     Query any brain collection (notes, code brains, etc.)
- dev-team:  Multi-agent software development team
- architect: Interactive architectural design sessions
- curator:   Automated codebase discovery and ingestion

Usage:
    # Morning briefing
    python src/main.py --mode briefing

    # Query your notes
    python src/main.py --mode query --brain notes --query "What are my goals?"

    # Query frontend knowledge
    python src/main.py --mode query --brain frontend_brain --query "React patterns"

    # Dev team
    python src/main.py --mode dev-team --feature "Build auth system"

    # Architect
    python src/main.py --mode architect --goal "Build chat app"

    # Curator
    python src/main.py --mode curator --domains frontend backend
"""

import sys
import os
import argparse
import traceback
from pathlib import Path
from dotenv import load_dotenv
from core.config import CHROMA_DB_DIR, EMBEDDING_MODEL

load_dotenv()

# Import agent-specific modules (lazy loading to improve startup time)
def import_chief_of_staff():
    from agents.chief_of_staff.graph import create_agent_graph
    from tools.gmail import list_drafts
    return create_agent_graph, list_drafts

def import_dev_team():
    from agents.dev_team.graph import run_dev_team
    return run_dev_team

def import_architect():
    from agents.architect.graph import run_architect_session
    return run_architect_session

def import_curator():
    from agents.curator.graph import run_curator_agent
    return run_curator_agent


# ============================================================================
# CORE FUNCTIONALITY: Query Any Brain
# ============================================================================

def query_brain(collection_name: str, query: str, k: int = 5) -> str:
    """
    Query any brain collection using RAG.

    Args:
        collection_name: Name of the ChromaDB collection to query
                        (e.g., "second_brain_notes", "frontend_brain", "backend_brain")
        query: The question to ask
        k: Number of relevant chunks to retrieve

    Returns:
        A synthesized answer based on the retrieved context
    """
    from langchain_ollama import ChatOllama
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_chroma import Chroma
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from tools.memory import get_relevant_preferences
    from ingestion.parent_child_ingestion import retrieve_with_parent_lookup

    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "codellama")
    USE_PARENT_CHILD = os.getenv("USE_PARENT_CHILD_RAG", "true").lower() == "true"

    print(f"\nQuerying brain: {collection_name}")
    print(f"Query: {query}\n")

    # Fetch user preferences (only for notes brain)
    preferences = ""
    if collection_name == "second_brain_notes":
        print("Fetching user preferences...")
        preferences = get_relevant_preferences(query)

    # Initialize embeddings
    print(f"Loading embeddings: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    # Connect to ChromaDB collection
    print(f"Connecting to ChromaDB collection: {collection_name}")
    try:
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=str(CHROMA_DB_DIR)
        )
    except Exception as e:
        return f"Error: Could not connect to collection '{collection_name}'. Make sure it exists.\nDetails: {e}"

    # Perform similarity search
    print("Searching for relevant information...")

    # Use parent-child retrieval for code brains if enabled
    if USE_PARENT_CHILD and "brain" in collection_name and collection_name != "second_brain_notes":
        print("Using Parent-Child-RAG (retrieving full context)...")
        relevant_docs = retrieve_with_parent_lookup(query, collection_name, k=k)
    else:
        # Traditional retrieval for notes or when parent-child is disabled
        relevant_docs = vectorstore.similarity_search(query, k=k)

    if not relevant_docs:
        return f"No relevant information found in '{collection_name}' for your query."

    # Display retrieved documents
    print(f"\n✅ Found {len(relevant_docs)} relevant chunk(s):\n")
    for i, doc in enumerate(relevant_docs, 1):
        source = doc.metadata.get('filename', doc.metadata.get('source', 'unknown'))
        preview = doc.page_content[:100].replace('\n', ' ')
        print(f"  {i}. {source}: {preview}...")

    # Prepare context
    context = "\n\n---\n\n".join([doc.page_content for doc in relevant_docs])

    # Build system prompt based on collection type
    if "brain" in collection_name and collection_name != "second_brain_notes":
        # Code brain - more technical and STRICT about using only provided code

        system_prompt = f"""You are an expert code analyst with access to a specialized codebase ({collection_name}).

CRITICAL RULES:
1. ONLY analyze the SPECIFIC CODE provided in the context below
2. DO NOT provide generic programming knowledge or patterns you know about
3. DO NOT mention patterns/libraries unless they appear in the provided code
4. Quote actual code snippets from the context to support your analysis
5. If the code doesn't show a pattern, say "I don't see that in the provided code"

Your task:
- Analyze the ACTUAL code structure, patterns, and implementations shown
- Identify specific components, functions, and their relationships
- Note how they're implemented (not how they could be implemented)
- Provide file names and line examples from the context

Be specific, precise, and grounded in the actual code provided."""

        # Notes brain - more conversational
        system_prompt = """You are a helpful assistant that answers questions based ONLY on the provided context from the user's personal notes.

Guidelines:
- Answer the question using ONLY information from the context provided
- If the context contains relevant information, provide a clear, concise answer
- If the answer is NOT in the context, say: "I don't have that in your notes."
- Do not use external knowledge or make assumptions
- Cite specific details when possible
- Be conversational but accurate"""

    # Inject preferences if available
    if preferences:
        system_prompt += f"\n\n{preferences}"

    # Create prompt template
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", """Context:
{context}

---

Question: {query}

Answer:""")
    ])

    # Initialize LLM
    print(f"\nInitializing {OLLAMA_MODEL}...")
    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.3
    )

    # Create chain
    chain = prompt_template | llm | StrOutputParser()

    # Generate answer
    print("Generating answer...\n")
    answer = chain.invoke({"context": context, "query": query})

    return answer


# ============================================================================
# MODE: Briefing (Chief of Staff)
# ============================================================================

def run_briefing_mode(args):
    """Run morning briefing workflow."""
    create_agent_graph, list_drafts = import_chief_of_staff()

    if not args.brief:
        print("=" * 70)
        print("Second Brain Agent: Morning Briefing")
        print("=" * 70, "\n")
        print("Running workflow:\n")
        print("1. Checking your Google Calendar...\n")
        print("2. Querying your knowledge base...\n")
        print("3. Generating your daily briefing...\n")
        print("4. Creating email drafts (if needed)...\n")
        print("-" * 70, "\n")

    # Create the agent
    agent = create_agent_graph()

    # Initial state
    initial_state = {
        "user_query": args.query or "Give me my daily briefing for today",
        "calendar_events": "",
        "relevant_notes": "",
        "daily_plan": "",
        "messages": []
    }

    # Run the agent
    final_state = agent.invoke(initial_state)

    # Display briefing
    briefing = final_state.get("daily_plan", "No briefing generated.")

    if args.brief:
        print(briefing)
    else:
        print("\n", "=" * 70)
        print("Your Daily Briefing")
        print("=" * 70, "\n")
        print(briefing)
        print("\n", "=" * 70, "\n")

        # Show email drafts unless disabled
        if not args.no_emails:
            try:
                print("\nEmail Drafts Status")
                print("-" * 70)
                drafts = list_drafts(max_results=5)
                print(drafts)
                print("\nReview drafts: https://mail.google.com/mail/#drafts\n")
            except Exception as e:
                print(f"Could not list email drafts: {e}")
                print("(Gmail integration may not be set up)\n")

    return 0


# ============================================================================
# MODE: Query Any Brain
# ============================================================================

def run_query_mode(args):
    """Query any brain collection."""
    if not args.query:
        print("Error: --query is required for query mode")
        print("\nExample: python src/main.py --mode query --brain notes --query 'What are my goals?'")
        return 1

    brain = args.brain or "notes"

    # Map friendly names to collection names
    collection_map = {
        "notes": "second_brain_notes",
        "frontend": "frontend_brain",
        "frontend_brain": "frontend_brain",
        "backend": "backend_brain",
        "backend_brain": "backend_brain",
        "fullstack": "fullstack_brain",
        "fullstack_brain": "fullstack_brain",
    }

    collection_name = collection_map.get(brain, brain)

    # Query the brain
    answer = query_brain(collection_name, args.query, k=args.k)

    # Display answer
    print("\n" + "=" * 70)
    print("ANSWER")
    print("=" * 70 + "\n")
    print(answer)
    print("\n" + "=" * 70)

    return 0


# ============================================================================
# MODE: Dev Team
# ============================================================================

def run_dev_team_mode(args):
    """Run multi-agent development team."""
    run_dev_team = import_dev_team()

    if not args.feature:
        print("Error: --feature is required for dev-team mode")
        print("\nExample: python src/main.py --mode dev-team --feature 'Build user authentication'")
        return 1

    print("\n" + "=" * 70)
    print("MULTI-AGENT SOFTWARE DEVELOPMENT TEAM")
    print("=" * 70)
    print(f"\nFeature: {args.feature}\n")

    # Run development team
    result = run_dev_team(args.feature)

    # Display summary
    print("\n" + "=" * 70)
    print("DEVELOPMENT COMPLETE")
    print("=" * 70)

    print("\n Frontend Implementation:")
    print(f"   Tasks: {len(result['frontend_tasks'])}")
    print(f"   Code: {len(result['frontend_code'])} chars")

    print("\n Backend Implementation:")
    print(f"   Tasks: {len(result['backend_tasks'])}")
    print(f"   Code: {len(result['backend_code'])} chars")

    print("\n Integration Review:")
    print(f"   Status: {result['review_status'].upper()}")
    print(f"   Issues: {len(result['issues_found'])}")

    if result['issues_found'] and not args.brief:
        print("\n   Top Issues:")
        for i, issue in enumerate(result['issues_found'][:3], 1):
            print(f"   {i}. {issue}")

    # Save output if requested
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save files
        (output_dir / "frontend.md").write_text("# Frontend\n\n## Tasks\n" + "\n".join(f"- {t}" for t in result['frontend_tasks']) + f"\n\n## Code\n\n{result['frontend_code']}")
        (output_dir / "backend.md").write_text("# Backend\n\n## Tasks\n" + "\n".join(f"- {t}" for t in result['backend_tasks']) + f"\n\n## Code\n\n{result['backend_code']}")
        (output_dir / "review.md").write_text(f"# Integration Review\n\n**Status**: {result['review_status']}\n\n" + "## Issues\n" + "\n".join(f"- {i}" for i in result['issues_found']) + f"\n\n{result['integration_review']}")

        print(f"\nOutput saved to: {output_dir.absolute()}")

    print("\n" + "=" * 70)

    return 0


# ============================================================================
# MODE: Architect
# ============================================================================

def run_architect_mode(args):
    """Run architectural design session."""
    run_architect_session = import_architect()

    if not args.goal:
        print("Error: --goal is required for architect mode")
        print("\nExample: python src/main.py --mode architect --goal 'Build a real-time chat app'")
        return 1

    print("\n" + "=" * 70)
    print("🏗️  ARCHITECT SESSION")
    print("=" * 70)
    print(f"\nGoal: {args.goal}\n")

    # Run architect
    state = run_architect_session(goal=args.goal)

    # Display design
    print("\n" + "=" * 70)
    print(f"ARCHITECTURAL DESIGN DOCUMENT (v{state['iteration_count']})")
    print("=" * 70 + "\n")
    print(state['design_document'])
    print("\n" + "=" * 70)

    # Save if requested
    if args.output:
        output_file = Path(args.output)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(
            f"# Architectural Design Document\n\n**Goal:** {args.goal}\n\n" +
            f"**Version:** {state['iteration_count']}\n\n---\n\n{state['design_document']}"
        )
        print(f"\nDesign saved to: {output_file.absolute()}")

    return 0


# ============================================================================
# MODE: Curator
# ============================================================================

def run_curator_mode(args):
    """Run curator agent for codebase discovery and ingestion."""
    run_curator_agent = import_curator()

    print("\n" + "=" * 70)
    print("CURATOR AGENT: AUTOMATED CODEBASE DISCOVERY")
    print("=" * 70)
    print(f"Domains: {', '.join(args.domains)}")
    print(f"Max Results: {args.max_results_curator}")
    print(f"Discover Only: {args.discover_only}")
    print("=" * 70)

    # Confirmation for ingestion
    if not args.discover_only and not args.yes:
        print("\nWARNING: Ingestion enabled - will clone and ingest repos")
        response = input("Proceed? (y/N): ")
        if response.lower() not in ["y", "yes"]:
            args.discover_only = True
            print("Switched to discovery-only mode")

    # Run curator
    final_state = run_curator_agent(
        mode=args.curator_mode,
        domains=args.domains,
        max_results_per_query=args.max_results_curator,
        skip_ingestion=args.discover_only,
    )

    # Display results
    assessed = final_state.get("assessed_repositories", [])
    approved = final_state.get("approved_for_ingestion", [])

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"\nRepositories Assessed: {len(assessed)}")
    print(f"Repositories Approved: {len(approved)}")

    if not args.discover_only:
        results = final_state.get("ingestion_results", [])
        success = sum(1 for r in results if r["status"] == "success")
        print(f"Successfully Ingested: {success}/{len(results)}")

        if success > 0:
            total_vectors = sum(r.get("vectors_stored", 0) for r in results if r["status"] == "success")
            print(f"Total Vectors Stored: {total_vectors}")

    print("=" * 70)

    return 0


# ============================================================================
# Main CLI Parser
# ============================================================================

def main():
    """Main CLI entry point with mode-based routing."""

    parser = argparse.ArgumentParser(
        description="Second-Brain-Agent: Unified CLI for all agent functionality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
MODES:
  briefing   Morning briefing workflow (Chief of Staff agent)
  query      Query any brain collection (notes, code brains)
  dev-team   Multi-agent software development team
  architect  Interactive architectural design sessions
  curator    Automated codebase discovery and ingestion

EXAMPLES:
  # Morning briefing
  python src/main.py --mode briefing
  python src/main.py --mode briefing --query "What's my focus this week?"

  # Query brains
  python src/main.py --mode query --brain notes --query "What are my goals?"
  python src/main.py --mode query --brain frontend --query "React best practices"
  python src/main.py --mode query --brain backend --query "FastAPI patterns"

  # Development team
  python src/main.py --mode dev-team --feature "Build authentication"
  python src/main.py --mode dev-team --feature "Create blog API" --output ./code

  # Architect
  python src/main.py --mode architect --goal "Build chat app"
  python src/main.py --mode architect --goal "Design microservices" --output design.md

  # Curator
  python src/main.py --mode curator --domains frontend backend
  python src/main.py --mode curator --domains frontend --discover-only

NOTES:
  - Default mode is 'briefing' if not specified
  - Most modes require GOOGLE_API_KEY in .env file
  - Query mode can access: notes, frontend, backend, fullstack brains
        """
    )

    # Core arguments
    parser.add_argument(
        "--mode", "-m",
        type=str,
        choices=["briefing", "query", "dev-team", "architect", "curator"],
        default="briefing",
        help="Agent mode to run (default: briefing)"
    )

    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Query string (used by briefing and query modes)"
    )

    parser.add_argument(
        "--brief",
        action="store_true",
        help="Brief output mode (minimal formatting)"
    )

    # Query mode specific
    parser.add_argument(
        "--brain", "-b",
        type=str,
        help="Brain collection to query (notes, frontend, backend, fullstack)"
    )

    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Number of relevant chunks to retrieve (default: 5)"
    )

    # Dev team mode specific
    parser.add_argument(
        "--feature", "-f",
        type=str,
        help="Feature to implement (dev-team mode)"
    )

    # Architect mode specific
    parser.add_argument(
        "--goal", "-g",
        type=str,
        help="Architectural goal (architect mode)"
    )

    # Curator mode specific
    parser.add_argument(
        "--domains",
        type=str,
        nargs="+",
        choices=["frontend", "backend", "fullstack"],
        default=["frontend", "backend"],
        help="Domains to curate (curator mode)"
    )

    parser.add_argument(
        "--curator-mode",
        type=str,
        choices=["manual", "auto"],
        default="manual",
        help="Curator query mode (manual=predefined, auto=LLM-generated)"
    )

    parser.add_argument(
        "--max-results-curator",
        type=int,
        default=5,
        help="Max results per curator query (default: 5)"
    )

    parser.add_argument(
        "--discover-only",
        action="store_true",
        help="Curator: discover only, don't ingest"
    )

    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Auto-confirm prompts"
    )

    # Common arguments
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file/directory for results"
    )

    parser.add_argument(
        "--no-emails",
        action="store_true",
        help="Skip email draft listing (briefing mode)"
    )

    args = parser.parse_args()

    try:
        # Route to appropriate mode
        if args.mode == "briefing":
            return run_briefing_mode(args)
        elif args.mode == "query":
            return run_query_mode(args)
        elif args.mode == "dev-team":
            return run_dev_team_mode(args)
        elif args.mode == "architect":
            return run_architect_mode(args)
        elif args.mode == "curator":
            return run_curator_mode(args)
        else:
            print(f"Error: Unknown mode '{args.mode}'")
            return 1

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 130

    except Exception as e:
        print(f"\nError: {e}")
        if not args.brief:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())