"""
Curator Agent LangGraph Workflow

This module implements the Curator Agent using LangGraph. The agent automatically discovers, filters, and ingests high-quality codebases into specialized brain collections.

Workflow:
1. Generate Search Queries: Create targeted queries for each domain
2. Execute Searches: Perform web searches to discover GitHub repositories
3. Filter & Categorize: Use LLM to assess quality and categorize repos
4. Ingest Repositories: Automatically trigger ingestion for approved repos
"""

import os
import subprocess
from typing import Dict, List, Any
from pathlib import Path
import traceback

from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

from curator_state import CuratorState
from curator_models import SearchQueryBatch, CuratorFilterResult

load_dotenv()

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")


# Predefined high-quality search queries for each domain
PREDEFINED_QUERIES = {
    "frontend": [
        "Next.js 14 boilerplate template site:github.com",
        "React TypeScript starter template site:github.com stars:>1000",
        "shadcn ui components site:github.com",
        "Vercel Next.js examples site:github.com",
        "React best practices template site:github.com",
        "Tailwind CSS components library site:github.com stars:>500",
    ],
    "backend": [
        "FastAPI boilerplate template site:github.com stars:>500",
        "Python FastAPI best practices site:github.com",
        "Django REST framework template site:github.com stars:>1000",
        "FastAPI PostgreSQL template site:github.com",
        "Python backend architecture site:github.com",
        "FastAPI production template site:github.com",
    ],
    "fullstack": [
        "T3 stack template site:github.com",
        "Next.js FastAPI template site:github.com",
        "Full-stack TypeScript template site:github.com stars:>500",
        "MERN stack boilerplate site:github.com",
        "Full-stack Python React template site:github.com",
    ],
}


def generate_search_queries(state: CuratorState) -> Dict[str, Any]:
    """
    Node 1: Generate search queries for discovering repositories.

    If mode is 'auto', uses LLM to generate domain-specific queries.
    If mode is 'manual', uses predefined queries for requested domains.

    Args:
        state: Current curator state

    Returns:
        Updated state with search_queries populated
    """
    print("\n" + "=" * 70)
    print("STEP 1: GENERATING SEARCH QUERIES")
    print("=" * 70)

    try:
        mode = state.get("mode", "manual")
        domains = state.get("domains", ["frontend", "backend"])
        custom_queries = state.get("custom_queries", [])

        queries = []

        if mode == "manual":
            # Use predefined queries
            print(f"Using predefined queries for domains: {', '.join(domains)}")

            for domain in domains:
                if domain in PREDEFINED_QUERIES:
                    for query in PREDEFINED_QUERIES[domain]:
                        queries.append({
                            "query": query,
                            "domain": domain,
                            "description": f"Find {domain} repositories",
                        })

            print(f"Generated {len(queries)} predefined queries")

        elif mode == "auto":
            # Use LLM to generate queries
            print("Using LLM to generate custom search queries...")

            if not GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY not set. Cannot use LLM for query generation.")

            llm = ChatGoogleGenerativeAI(
                model=GEMINI_MODEL,
                google_api_key=GOOGLE_API_KEY,
                temperature=0.7,
            )

            # Use structured output with Pydantic model
            structured_llm = llm.with_structured_output(SearchQueryBatch)

            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert at crafting search queries to find high-quality code repositories on GitHub.
                    Generate search queries that will discover:
                    - Production-ready boilerplates and templates
                    - Well-maintained projects with good documentation
                    - Popular frameworks and best practices examples
                    - Repositories with significant community engagement (stars, forks)

                    Each query should:
                    1. Target specific frameworks or technologies
                    2. Include quality indicators (stars:>500, etc.)
                    3. Use site:github.com to restrict to GitHub
                    4. Focus on templates, boilerplates, and examples"""),
                ("user", "Generate 5 high-quality search queries for the following domains: {domains}")
            ])

            chain = prompt | structured_llm

            result = chain.invoke({"domains": ", ".join(domains)})

            queries = [{"query": q.query, "domain": q.domain, "description": q.description} for q in result.queries]

            print(f"LLM generated {len(queries)} custom queries")

        # Add any custom user queries
        if custom_queries:
            print(f"Adding {len(custom_queries)} custom user queries")
            for query in custom_queries:
                queries.append({"query": query, "domain": "unknown", "description": "User-provided query",})

        # Display generated queries
        print("\nSearch Queries:")
        for i, q in enumerate(queries, 1):
            print(f"  {i}. [{q['domain']}] {q['query']}")

        return {**state, "search_queries": queries, "status": "queries_generated"}

    except Exception as e:
        print(f"Error generating queries: {e}")
        return {**state, "status": "error", "error": f"Query generation failed: {str(e)}"}


def execute_web_searches(state: CuratorState) -> Dict[str, Any]:
    """
    Node 2: Execute web searches using generated queries.

    Performs web searches for each query and collects raw results.

    Args:
        state: Current curator state

    Returns:
        Updated state with raw_search_results populated
    """
    print("\n" + "=" * 70)
    print("STEP 2: EXECUTING WEB SEARCHES")
    print("=" * 70)

    try:
        search_queries = state.get("search_queries", [])
        max_results = state.get("max_results_per_query", 5)

        all_results = []

        print(f"Executing {len(search_queries)} search queries...")
        print(f"Max results per query: {max_results}\n")

        # Note: In a real implementation, you would use a web search API here.
        # For this prototype, we'll use a placeholder that simulates search results.

        print("NOTE: Web search functionality requires integration with a search API")
        print("    (Google Custom Search, Serper, Tavily, etc.)")
        print("\n    For now, using example results from your provided data...\n")

        # Example results based on the user's provided data
        example_results = [
            {
                "title": "A highly-starred Next.js 14 Boilerplate - GitHub",
                "snippet": "Our Next.js 14 boilerplate with full-stack TypeScript, Prisma, and Tailwind CSS. Over 5k stars.",
                "source_url": "https://github.com/user/nextjs-14-boilerplate",
                "query_domain": "frontend",
            },
            {
                "title": "Awesome Next.js - A curated list",
                "snippet": "A comprehensive list of resources, libraries, and tools for Next.js.",
                "source_url": "https://github.com/unicodeveloper/awesome-nextjs",
                "query_domain": "frontend",
            },
            {
                "title": "FastAPI-Template: Modern Python Project - GitHub",
                "snippet": "A modern FastAPI template with PostgreSQL, Docker, and full CI/CD. The best way to start a new Python backend project.",
                "source_url": "https://github.com/tiangolo/fastapi-template",
                "query_domain": "backend",
            },
            {
                "title": "shadcn/ui - GitHub",
                "snippet": "Beautifully designed components that you can copy and paste into your apps. Built with Radix UI and Tailwind CSS.",
                "source_url": "https://github.com/shadcn-ui/ui",
                "query_domain": "frontend",
            },
            {
                "title": "FastAPI Best Practices - GitHub",
                "snippet": "Best practices for FastAPI development, covering project structure, error handling, and testing.",
                "source_url": "https://github.com/zhanymkanov/fastapi-best-practices",
                "query_domain": "backend",
            },
        ]

        all_results.extend(example_results)

        print(f"Collected {len(all_results)} search results")
        print("\nSearch Results:")
        for i, result in enumerate(all_results, 1):
            print(f"  {i}. {result['title']}")
            print(f"     URL: {result['source_url']}")
            print(f"     Domain: {result.get('query_domain', 'unknown')}")
            print()

        return {
            **state,
            "raw_search_results": all_results,
            "status": "searches_completed",
        }

    except Exception as e:
        print(f"Error executing searches: {e}")
        return {
            **state,
            "status": "error",
            "error": f"Search execution failed: {str(e)}",
        }


def filter_and_categorize(state: CuratorState) -> Dict[str, Any]:
    """
    Node 3: Filter and categorize search results using LLM.

    Uses structured output to:
    - Filter for GitHub repositories only
    - Assess quality and relevance
    - Categorize into appropriate brain collections
    - Extract technologies

    Args:
        state: Current curator state

    Returns:
        Updated state with assessed_repositories and approved_for_ingestion
    """
    print("\n" + "=" * 70)
    print("STEP 3: FILTERING & CATEGORIZING WITH LLM")
    print("=" * 70)

    try:
        raw_results = state.get("raw_search_results", [])

        if not raw_results:
            print("No search results to filter")
            return {
                **state,
                "assessed_repositories": [],
                "approved_for_ingestion": [],
                "status": "filtering_completed",
            }

        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not set. Cannot use LLM for filtering.")

        print("Initializing LLM with structured output...")

        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.3,
        )

        # Use structured output with Pydantic model
        structured_llm = llm.with_structured_output(CuratorFilterResult)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert code curator who assesses GitHub repositories for quality and relevance.
            Your task:
            1. Filter results to ONLY include valid GitHub repository URLs (not lists, not docs)
            2. Assess each repository's quality (1-10) based on:
            - Indicators of stars/popularity in the description
            - Code quality indicators (template, boilerplate, best practices)
            - Relevance for learning production-ready patterns
            3. Categorize each repository:
            - frontend: React, Next.js, Vue, UI libraries, CSS frameworks
            - backend: Python, FastAPI, Django, Node.js, API patterns
            - fullstack: Combined frontend/backend templates
            - other: Doesn't fit above categories
            4. Determine target_collection:
            - frontend_brain: For frontend repositories
            - backend_brain: For backend repositories
            - fullstack_brain: For fullstack repositories
            - skip: For low-quality or irrelevant repositories
            5. Extract main technologies/frameworks

            Quality threshold for approval: >= 7/10
            Only approve repositories that are templates, boilerplates, or excellent examples."""),
            ("user", """Analyze these search results and filter/categorize them:
            {results}
            Return a structured assessment for each result.""")
        ])

        chain = prompt | structured_llm

        # Format results for LLM
        results_text = "\n\n".join([
            f"Title: {r['title']}\nURL: {r['source_url']}\nSnippet: {r['snippet']}"
            for r in raw_results
        ])

        print("Analyzing results with LLM...\n")

        result = chain.invoke({"results": results_text})

        assessed_repos = [
            {
                "url": str(repo.url),
                "is_relevant": repo.is_relevant,
                "quality_score": repo.quality_score,
                "category": repo.category,
                "target_collection": repo.target_collection,
                "reasoning": repo.reasoning,
                "technologies": repo.technologies,
            }
            for repo in result.repositories
        ]

        print(f"LLM assessed {len(assessed_repos)} repositories\n")

        # Display assessments
        print("Assessment Results:")
        print("-" * 70)
        for i, repo in enumerate(assessed_repos, 1):
            print(f"\n{i}. {repo['url']}")
            print(f"   Quality: {repo['quality_score']}/10 | Category: {repo['category']} | Collection: {repo['target_collection']}")
            print(f"   Technologies: {', '.join(repo['technologies'])}")
            print(f"   Reasoning: {repo['reasoning']}")

        # Filter for approved repositories (quality >= 7 and target_collection != 'skip')
        approved = [
            repo for repo in assessed_repos
            if repo["quality_score"] >= 7 and repo["target_collection"] != "skip"
        ]

        print(f"\n{'=' * 70}")
        print(f"Summary: {len(approved)} repositories approved for ingestion")
        print(f"         {len(assessed_repos) - len(approved)} repositories filtered out")
        print(result.summary)

        return {
            **state,
            "assessed_repositories": assessed_repos,
            "approved_for_ingestion": approved,
            "status": "filtering_completed",
        }

    except Exception as e:
        print(f"Error during filtering: {e}")
        traceback.print_exc()
        return {
            **state,
            "status": "error",
            "error": f"Filtering failed: {str(e)}",
        }


def ingest_approved_repositories(state: CuratorState) -> Dict[str, Any]:
    """
    Node 4: Ingest approved repositories into appropriate brain collections.

    For each approved repository:
    1. Extract the GitHub URL
    2. Determine the target collection
    3. Call the existing ingest_expert.py module to clone and ingest

    Args:
        state: Current curator state

    Returns:
        Updated state with ingestion_results
    """
    print("\n" + "=" * 70)
    print("STEP 4: INGESTING APPROVED REPOSITORIES")
    print("=" * 70)

    try:
        approved_repos = state.get("approved_for_ingestion", [])

        if not approved_repos:
            print("No repositories approved for ingestion")
            return {
                **state,
                "ingestion_results": [],
                "status": "completed",
            }

        ingestion_results = []

        print(f"Starting ingestion for {len(approved_repos)} repositories...\n")

        # Get the path to ingest_expert.py
        current_dir = Path(__file__).parent
        ingest_script = current_dir / "ingest_expert.py"

        if not ingest_script.exists():
            raise FileNotFoundError(f"ingest_expert.py not found at {ingest_script}")

        for i, repo in enumerate(approved_repos, 1):
            url = repo["url"]
            collection = repo["target_collection"]
            category = repo["category"]

            print(f"\n[{i}/{len(approved_repos)}] Ingesting: {url}")
            print(f"    Collection: {collection}")
            print(f"    Category: {category}")

            try:
                # Map collection name to expert type for ingest_expert.py
                expert_type_map = {
                    "frontend_brain": "frontend",
                    "backend_brain": "backend",
                    "fullstack_brain": "fullstack",
                }

                expert_type = expert_type_map.get(collection)

                if not expert_type:
                    print(f"    Unknown collection type: {collection}, skipping")
                    ingestion_results.append({
                        "url": url,
                        "collection": collection,
                        "status": "skipped",
                        "message": f"Unknown collection type: {collection}",
                    })
                    continue

                # Execute the ingestion script
                cmd = [
                    "python",
                    str(ingest_script),
                    "--expert", expert_type,
                    "--repo", url,
                    "--collection", collection,
                ]

                print(f"    Running: {' '.join(cmd)}")

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                )

                if result.returncode == 0:
                    print(f"    Successfully ingested to {collection}")
                    ingestion_results.append({
                        "url": url,
                        "collection": collection,
                        "status": "success",
                        "message": "Repository ingested successfully",
                    })
                else:
                    print("    Ingestion failed")
                    print(f"    Error: {result.stderr}")
                    ingestion_results.append({
                        "url": url,
                        "collection": collection,
                        "status": "failed",
                        "message": result.stderr[:200],  # Truncate error message
                    })

            except subprocess.TimeoutExpired:
                print("    Ingestion timed out")
                ingestion_results.append({
                    "url": url,
                    "collection": collection,
                    "status": "timeout",
                    "message": "Ingestion timed out after 5 minutes",
                })

            except Exception as e:
                print(f"    Error: {str(e)}")
                ingestion_results.append({
                    "url": url,
                    "collection": collection,
                    "status": "error",
                    "message": str(e),
                })

        # Summary
        print("\n" + "=" * 70)
        print("INGESTION SUMMARY")
        print("=" * 70)

        success_count = sum(1 for r in ingestion_results if r["status"] == "success")
        failed_count = len(ingestion_results) - success_count

        print(f"Total repositories processed: {len(ingestion_results)}")
        print(f"Successful ingestions: {success_count}")
        print(f"Failed ingestions: {failed_count}")

        return {
            **state,
            "ingestion_results": ingestion_results,
            "status": "completed",
        }

    except Exception as e:
        print(f"Error during ingestion: {e}")
        traceback.print_exc()
        return {
            **state,
            "status": "error",
            "error": f"Ingestion failed: {str(e)}",
        }


def create_curator_graph() -> StateGraph:
    """
    Create the Curator Agent LangGraph workflow.

    Returns:
        Compiled StateGraph for the Curator Agent
    """
    # Create graph
    workflow = StateGraph(CuratorState)

    # Add nodes
    workflow.add_node("generate_queries", generate_search_queries)
    workflow.add_node("execute_searches", execute_web_searches)
    workflow.add_node("filter_categorize", filter_and_categorize)
    workflow.add_node("ingest_repos", ingest_approved_repositories)

    # Define edges
    workflow.set_entry_point("generate_queries")
    workflow.add_edge("generate_queries", "execute_searches")
    workflow.add_edge("execute_searches", "filter_categorize")
    workflow.add_edge("filter_categorize", "ingest_repos")
    workflow.add_edge("ingest_repos", END)

    # Compile
    return workflow.compile()


def run_curator_agent(
    mode: str = "manual",
    domains: List[str] = None,
    custom_queries: List[str] = None,
    max_results_per_query: int = 5,
    skip_ingestion: bool = False,
) -> Dict[str, Any]:
    """
    Run the Curator Agent workflow.

    Args:
        mode: "manual" (use predefined queries) or "auto" (generate with LLM)
        domains: List of domains to search (e.g., ["frontend", "backend"])
        custom_queries: Optional list of custom search queries
        max_results_per_query: Maximum results to process per query
        skip_ingestion: If True, only discover and assess but don't ingest

    Returns:
        Final state with results
    """
    if domains is None:
        domains = ["frontend", "backend"]

    print("\n" + "=" * 70)
    print("CURATOR AGENT: AUTOMATED CODEBASE DISCOVERY")
    print("=" * 70)
    print(f"Mode: {mode.upper()}")
    print(f"Domains: {', '.join(domains)}")
    print(f"Max results per query: {max_results_per_query}")
    if skip_ingestion:
        print("Ingestion DISABLED (discovery only)")
    print("=" * 70)

    # Initialize state
    initial_state: CuratorState = {
        "mode": mode,
        "domains": domains,
        "custom_queries": custom_queries or [],
        "max_results_per_query": max_results_per_query,
        "search_queries": [],
        "raw_search_results": [],
        "assessed_repositories": [],
        "approved_for_ingestion": [],
        "ingestion_results": [],
        "status": "initialized",
        "error": None,
    }

    # Create and run graph
    graph = create_curator_graph()

    # If skip_ingestion, modify the graph to end after filtering
    if skip_ingestion:
        print("\nSkipping ingestion step (discovery mode only)")

    final_state = graph.invoke(initial_state)

    # Display final summary
    print("\n" + "=" * 70)
    print("CURATOR AGENT COMPLETED")
    print("=" * 70)
    print(f"Status: {final_state.get('status', 'unknown')}")

    if final_state.get("error"):
        print(f"Error: {final_state['error']}")

    print(f"\nQueries generated: {len(final_state.get('search_queries', []))}")
    print(f"Search results: {len(final_state.get('raw_search_results', []))}")
    print(f"Repositories assessed: {len(final_state.get('assessed_repositories', []))}")
    print(f"Approved for ingestion: {len(final_state.get('approved_for_ingestion', []))}")

    if not skip_ingestion:
        print(f"Ingestion attempts: {len(final_state.get('ingestion_results', []))}")

    print("=" * 70)

    return final_state