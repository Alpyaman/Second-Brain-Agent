"""
Re-ingest Code Brains with Parent-Child RAG

This script re-ingests your code brains using the advanced Parent-Child RAG strategy.

Why re-ingest?
- Your current code brains use simple chunking (tiny 5-10 line snippets)
- Parent-Child RAG extracts complete functions/classes (50-500 lines)
- LLM receives full context instead of meaningless fragments

How it works:
1. Reads your existing ChromaDB collections
2. Extracts original repository information
3. Re-clones and processes with parent-child extraction
4. Replaces old collections with enhanced versions

Usage:
    # Re-ingest all code brains
    python reingest_with_parent_child.py

    # Re-ingest specific brain
    python reingest_with_parent_child.py --brain frontend_brain

    # Dry run (show what would be done)
    python reingest_with_parent_child.py --dry-run
"""

import argparse
import sys
import tempfile
import subprocess
from pathlib import Path
from typing import List, Set

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from src.core.config import CHROMA_DB_DIR, EMBEDDING_MODEL
from ingestion.parent_child_code_parser import process_code_files_with_parent_child, ingest_with_parent_child

def get_repositories_from_collection(collection_name: str) -> List[dict]:
    """
    Extract repository information from existing collection.

    Args:
        collection_name: ChromaDB collection name

    Returns:
        List of dicts with repo_url and commit_hash
    """
    print(f"\nAnalyzing collection: {collection_name}")

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={'device': 'cpu'}, encode_kwargs={'normalize_embeddings': True})

    try:
        vectorstore = Chroma(collection_name=collection_name, embedding_function=embeddings, persist_directory=str(CHROMA_DB_DIR))

        # Get all documents to extract unique repos
        collection = vectorstore._collection
        all_data = collection.get()

        if not all_data or not all_data.get('metadatas'):
            print("    Collection is empty")
            return []

        # Extract unique repositories
        repos = {}
        for metadata in all_data['metadatas']:
            repo_url = metadata.get('repo_url')
            if repo_url:
                if repo_url not in repos:
                    repos[repo_url] = {'repo_url': repo_url, 'commit_hash': metadata.get('commit_hash'), 'expert_domain': metadata.get('expert_domain'), 'files_count': 0}
                repos[repo_url]['files_count'] += 1

        repo_list = list(repos.values())
        print(f"   Found {len(repo_list)} repositories")

        for repo in repo_list:
            print(f"    - {repo['repo_url']} ({repo['files_count']} chunks)")

        return repo_list

    except Exception as e:
        print(f"   Error: {e}")
        return []

def clone_repository(repo_url: str, target_dir: Path) -> bool:
    """Clone a git repository."""
    try:
        print(f"  Cloning: {repo_url}")
        subprocess.run(["git", "clone", "--depth", "1", repo_url, str(target_dir)], check=True, capture_output=True, text=True)
        return True

    except subprocess.CalledProcessError as e:
        print(f"   Clone failed: {e.stderr}")
        return False

def find_code_files(directory: Path, file_extensions: List[str], exclude_patterns: Set[str]) -> List[Path]:
    """Find code files in directory."""
    code_files = []

    for file_path in directory.rglob("*"):
        # Skip excluded patterns
        if any(pattern in str(file_path) for pattern in exclude_patterns):
            continue

        # Check file extension
        if file_path.is_file() and file_path.suffix in file_extensions:
            code_files.append(file_path)

    return code_files

def reingest_collection(collection_name: str, dry_run: bool = False) -> dict:
    """
    Re-ingest a collection with parent-child RAG.

    Args:
        collection_name: Name of collection to re-ingest
        dry_run: If True, only show what would be done

    Returns:
        Dictionary with re-ingestion statistics
    """
    print("\n" + "=" * 70)
    print(f"RE-INGESTING: {collection_name}")
    print("=" * 70)

    # Get repositories from existing collection
    repos = get_repositories_from_collection(collection_name)

    if not repos:
        print("No repositories found in collection")
        return {"status": "skipped", "reason": "no_repos"}

    if dry_run:
        print("\n DRY RUN MODE - No changes will be made")
        print(f"\nWould re-ingest {len(repos)} repositories:")
        for repo in repos:
            print(f"  - {repo['repo_url']}")
        return {"status": "dry_run", "repos_count": len(repos)}

    # Determine file extensions based on collection type
    if "frontend" in collection_name:
        file_extensions = [".ts", ".tsx", ".js", ".jsx", ".css", ".scss"]
        exclude_patterns = {"node_modules", ".next", "dist", "build", ".git"}
    elif "backend" in collection_name:
        file_extensions = [".py"]
        exclude_patterns = {"venv", ".venv", "__pycache__", ".git", "dist"}
    else:
        file_extensions = [".py", ".ts", ".tsx", ".js", ".jsx"]
        exclude_patterns = {"node_modules", ".next", "venv", ".venv", "dist", ".git"}

    # Process each repository
    all_parents = []
    all_children = []
    all_fallback = []

    for repo in repos:
        print(f"\nProcessing repository: {repo['repo_url']}")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Clone repository
            if not clone_repository(repo['repo_url'], temp_path):
                print("  Skipping due to clone failure")
                continue

            # Find code files
            code_files = find_code_files(temp_path, file_extensions, exclude_patterns)
            print(f"  Found {len(code_files)} code files")

            # Process with parent-child extraction
            result = process_code_files_with_parent_child(file_paths=code_files, expert_type=repo.get('expert_domain', 'unknown'), repo_url=repo['repo_url'], commit_hash=repo.get('commit_hash'))

            all_parents.extend(result['parents'])
            all_children.extend(result['children'])
            all_fallback.extend(result['fallback'])

    # Clear old collection and ingest new data
    print(f"\nClearing old collection: {collection_name}")

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={'device': 'cpu'}, encode_kwargs={'normalize_embeddings': True})

    # Delete old collection
    try:
        old_vectorstore = Chroma(collection_name=collection_name, embedding_function=embeddings, persist_directory=str(CHROMA_DB_DIR))

        old_vectorstore.delete_collection()
        print("   Old collection deleted")
    except Exception as e:
        print(f"    Could not delete old collection: {e}")

    # Ingest with parent-child
    ingest_result = ingest_with_parent_child(parent_docs=all_parents, child_docs=all_children, fallback_docs=all_fallback, collection_name=collection_name)

    return {"status": "success", "repos_count": len(repos), **ingest_result}

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Re-ingest code brains with Parent-Child RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Re-ingest all code brains
  python reingest_with_parent_child.py

  # Re-ingest specific brain
  python reingest_with_parent_child.py --brain frontend_brain

  # Dry run
  python reingest_with_parent_child.py --dry-run

After re-ingestion:
  Your queries will retrieve full functions/classes (50-500 lines)
  instead of tiny snippets (5-10 lines).

  Test with:
  python src/main.py --mode query --brain frontend --query "React patterns"
        """
    )

    parser.add_argument("--brain", type=str, choices=["frontend_brain", "backend_brain", "fullstack_brain", "all"], default="all", help="Which brain to re-ingest (default: all)")

    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")

    args = parser.parse_args()

    print("=" * 70)
    print("PARENT-CHILD RAG RE-INGESTION")
    print("=" * 70)
    print("\nThis will re-ingest your code brains with advanced RAG.")
    print("\nBenefits:")
    print("   Retrieve complete functions/classes (not tiny snippets)")
    print("   LLM receives full code context (50-500 lines)")
    print("   Better pattern recognition and code understanding")

    if not args.dry_run:
        print("\nWARNING: This will replace your existing collections!")
        response = input("\nProceed? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("Cancelled.")
            return 0

    # Determine which collections to process
    if args.brain == "all":
        collections = ["frontend_brain", "backend_brain", "fullstack_brain"]
    else:
        collections = [args.brain]

    # Process each collection
    results = {}
    for collection in collections:
        result = reingest_collection(collection, dry_run=args.dry_run)
        results[collection] = result

    # Summary
    print("\n" + "=" * 70)
    print("RE-INGESTION SUMMARY")
    print("=" * 70)

    for collection, result in results.items():
        status = result.get('status', 'unknown')
        print(f"\n{collection}: {status.upper()}")

        if status == "success":
            print(f"  Repositories: {result.get('repos_count', 0)}")
            print(f"  Parents (full code): {result.get('parents_stored', 0)}")
            print(f"  Children (summaries): {result.get('children_embedded', 0)}")
            print(f"  Fallback chunks: {result.get('fallback_chunks', 0)}")

    if not args.dry_run:
        print("\nRe-ingestion complete!")
        print("\nTest your enhanced RAG:")
        print("  python src/main.py --mode query --brain frontend --query 'React patterns'")
        print("\nThe LLM will now receive full code context instead of snippets!")

    return 0

if __name__ == "__main__":
    sys.exit(main())