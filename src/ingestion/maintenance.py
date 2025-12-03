"""
Repository Maintenance Utilities

This module provides utilities for maintaining the Curator Agent's repository collections:
- Duplicate detection: Check if a repository is already ingested
- Update detection: Check if a repository has been updated since last ingestion
- Commit hash tracking: Store and retrieve the latest commit hash for repositories
- Collection management: List, update, and remove repositories

This is Phase 3 of the Curator Agent: Scheduling and Maintenance.
"""

import subprocess
from typing import Optional, Dict, List, Any
from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from core.config import CHROMA_DB_DIR, EMBEDDING_MODEL


def get_repository_commit_hash(repo_path: Path) -> Optional[str]:
    """
    Get the latest commit hash from a Git repository.

    Args:
        repo_path: Path to the cloned repository

    Returns:
        Commit hash string or None if failed
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error getting commit hash: {e}")
        return None


def get_repository_metadata(repo_url: str, collection_name: str) -> Optional[Dict[str, Any]]:
    """
    Check if a repository is already in the collection and get its metadata.

    Args:
        repo_url: GitHub repository URL
        collection_name: ChromaDB collection name

    Returns:
        Dict with repository metadata or None if not found:
        {
            'repo_url': str,
            'commit_hash': str,
            'ingestion_date': str,
            'files_count': int,
            'last_update_check': str
        }
    """
    try:
        # Initialize embeddings and vectorstore
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=str(CHROMA_DB_DIR)
        )

        # Query collection for this repository URL
        # ChromaDB metadata filtering
        collection = vectorstore._collection

        # Get all documents with this repo_url in metadata
        results = collection.get(
            where={"repo_url": repo_url},
            limit=1
        )

        if results and results['ids']:
            # Repository exists, extract metadata
            metadata = results['metadatas'][0] if results['metadatas'] else {}

            return {
                'repo_url': metadata.get('repo_url', repo_url),
                'commit_hash': metadata.get('commit_hash'),
                'ingestion_date': metadata.get('ingestion_date'),
                'files_count': metadata.get('files_count', 0),
                'last_update_check': metadata.get('last_update_check')
            }

        return None

    except Exception as e:
        print(f"Error checking repository metadata: {e}")
        return None


def check_repository_needs_update(repo_url: str, current_commit: str, collection_name: str) -> bool:
    """
    Check if a repository needs to be re-ingested based on commit hash.

    Args:
        repo_url: GitHub repository URL
        current_commit: Current commit hash of the repository
        collection_name: ChromaDB collection name

    Returns:
        True if repository needs update, False otherwise
    """
    existing_metadata = get_repository_metadata(repo_url, collection_name)

    if not existing_metadata:
        # Repository not found, needs ingestion
        return True

    stored_commit = existing_metadata.get('commit_hash')

    if not stored_commit:
        # No commit hash stored, assume needs update
        return True

    # Compare commit hashes
    return current_commit != stored_commit


def list_ingested_repositories(collection_name: str) -> List[Dict[str, Any]]:
    """
    List all repositories ingested into a collection.

    Args:
        collection_name: ChromaDB collection name

    Returns:
        List of repository metadata dictionaries
    """
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=str(CHROMA_DB_DIR)
        )

        collection = vectorstore._collection

        # Get all documents (this can be large, consider pagination)
        results = collection.get()

        # Extract unique repositories by URL
        repos = {}
        if results and results['metadatas']:
            for metadata in results['metadatas']:
                repo_url = metadata.get('repo_url')
                if repo_url and repo_url not in repos:
                    repos[repo_url] = {
                        'repo_url': repo_url,
                        'commit_hash': metadata.get('commit_hash'),
                        'ingestion_date': metadata.get('ingestion_date'),
                        'files_count': metadata.get('files_count', 0),
                        'expert_domain': metadata.get('expert_domain'),
                    }

        return list(repos.values())

    except Exception as e:
        print(f"Error listing repositories: {e}")
        return []


def remove_repository_from_collection(repo_url: str, collection_name: str) -> bool:
    """
    Remove all documents associated with a repository from a collection.

    Args:
        repo_url: GitHub repository URL to remove
        collection_name: ChromaDB collection name

    Returns:
        True if successful, False otherwise
    """
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=str(CHROMA_DB_DIR)
        )

        collection = vectorstore._collection

        # Get all document IDs for this repository
        results = collection.get(
            where={"repo_url": repo_url}
        )

        if results and results['ids']:
            # Delete all documents
            collection.delete(ids=results['ids'])
            print(f"Removed {len(results['ids'])} documents for {repo_url}")
            return True
        else:
            print(f"No documents found for {repo_url}")
            return False

    except Exception as e:
        print(f"Error removing repository: {e}")
        return False


def get_collection_stats(collection_name: str) -> Dict[str, Any]:
    """
    Get statistics about a collection.

    Args:
        collection_name: ChromaDB collection name

    Returns:
        Dict with collection statistics:
        {
            'total_documents': int,
            'total_repositories': int,
            'repositories': List[str],
            'collection_name': str,
            'storage_path': str
        }
    """
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=str(CHROMA_DB_DIR)
        )

        collection = vectorstore._collection

        # Get collection count
        total_docs = collection.count()

        # Get unique repositories
        repos = list_ingested_repositories(collection_name)
        repo_urls = [r['repo_url'] for r in repos if r.get('repo_url')]

        return {
            'total_documents': total_docs,
            'total_repositories': len(repo_urls),
            'repositories': repo_urls,
            'collection_name': collection_name,
            'storage_path': str(CHROMA_DB_DIR)
        }

    except Exception as e:
        print(f"Error getting collection stats: {e}")
        return {
            'total_documents': 0,
            'total_repositories': 0,
            'repositories': [],
            'collection_name': collection_name,
            'storage_path': str(CHROMA_DB_DIR),
            'error': str(e)
        }


# Example usage
if __name__ == "__main__":
    """Test repository maintenance utilities."""

    # Test collection stats
    print("Testing collection stats...")
    stats = get_collection_stats('frontend_brain')
    print(f"\nCollection: {stats['collection_name']}")
    print(f"Total documents: {stats['total_documents']}")
    print(f"Total repositories: {stats['total_repositories']}")
    print(f"Repositories: {stats['repositories']}")

    # Test list repositories
    print("\n\nTesting list repositories...")
    repos = list_ingested_repositories('frontend_brain')
    for repo in repos:
        print(f"\n{repo['repo_url']}")
        print(f"  Commit: {repo.get('commit_hash', 'N/A')}")
        print(f"  Ingested: {repo.get('ingestion_date', 'N/A')}")
        print(f"  Files: {repo.get('files_count', 'N/A')}")