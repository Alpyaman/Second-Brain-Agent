"""
Ingestion Dispatcher Module

This module provides a clean API for dispatching repository ingestion tasks.
It wraps the ingest_expert.py functionality and provides structured results.

The Ingestion Dispatcher is Node 2 in the Curator Agent auto-ingestion graph:
  Node 1: Curator Agent (search & filter) -> Node 2: Ingestion Dispatcher (ingest)
"""

from typing import Dict, List, Any

from ingest_expert import ingest_expert_knowledge, EXPERT_TEMPLATES


def dispatch_ingestion(repo_url: str, target_collection: str, expert_type: str = None, verbose: bool = False) -> Dict[str, Any]:
    """
    Dispatch a single repository ingestion task.

    Args:
        repo_url: GitHub repository URL to clone and ingest
        target_collection: Target ChromaDB collection name
        expert_type: Optional expert type override (auto-detected from collection if not provided)
        verbose: Whether to print detailed progress messages

    Returns:
        Dict with ingestion results:
        {
            'success': bool,
            'expert_type': str,
            'collection': str,
            'repo_url': str,
            'files_processed': int,
            'chunks_created': int,
            'vectors_stored': int,
            'error': str or None
        }
    """
    # Auto-detect expert type from collection name if not provided
    if not expert_type:
        expert_type = _detect_expert_type_from_collection(target_collection)

        if not expert_type:
            return {
                'success': False,
                'expert_type': None,
                'collection': target_collection,
                'repo_url': repo_url,
                'files_processed': 0,
                'chunks_created': 0,
                'vectors_stored': 0,
                'error': f'Could not detect expert type from collection: {target_collection}'
            }

    # Call the ingestion function
    return ingest_expert_knowledge(
        expert_type=expert_type,
        repo_url=repo_url,
        collection_name=target_collection,
        verbose=verbose
    )


def dispatch_batch_ingestion(
    repositories: List[Dict[str, str]],
    verbose: bool = False
) -> List[Dict[str, Any]]:
    """
    Dispatch a batch of repository ingestion tasks.

    Args:
        repositories: List of repository dictionaries with keys:
            - url: GitHub repository URL
            - target_collection: Target ChromaDB collection
            - expert_type: (optional) Expert type override
        verbose: Whether to print detailed progress messages

    Returns:
        List of ingestion result dictionaries
    """
    results = []

    if verbose:
        print(f"\n{'=' * 70}")
        print(f"BATCH INGESTION: {len(repositories)} repositories")
        print(f"{'=' * 70}\n")

    for i, repo in enumerate(repositories, 1):
        url = repo.get('url')
        collection = repo.get('target_collection')
        expert_type = repo.get('expert_type')

        if verbose:
            print(f"[{i}/{len(repositories)}] Ingesting: {url}")
            print(f"    Collection: {collection}")

        result = dispatch_ingestion(
            repo_url=url,
            target_collection=collection,
            expert_type=expert_type,
            verbose=verbose
        )

        results.append(result)

        if verbose:
            if result['success']:
                print(f"    Success: {result['vectors_stored']} vectors stored")
            else:
                print(f"    Failed: {result['error']}")
            print()

    # Print summary
    if verbose:
        success_count = sum(1 for r in results if r['success'])
        failed_count = len(results) - success_count

        print(f"{'=' * 70}")
        print("BATCH INGESTION SUMMARY")
        print(f"{'=' * 70}")
        print(f"Total repositories: {len(results)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {failed_count}")
        print(f"{'=' * 70}\n")

    return results


def _detect_expert_type_from_collection(collection_name: str) -> str:
    """
    Auto-detect expert type from collection name.

    Args:
        collection_name: ChromaDB collection name

    Returns:
        Expert type string or None if not detected
    """
    # Direct mapping
    collection_to_expert = {
        'frontend_brain': 'frontend',
        'backend_brain': 'backend',
        'fullstack_brain': 'fullstack',
    }

    if collection_name in collection_to_expert:
        return collection_to_expert[collection_name]

    # Fuzzy matching
    collection_lower = collection_name.lower()

    if 'frontend' in collection_lower or 'front-end' in collection_lower:
        return 'frontend'
    elif 'backend' in collection_lower or 'back-end' in collection_lower:
        return 'backend'
    elif 'fullstack' in collection_lower or 'full-stack' in collection_lower:
        return 'fullstack'

    return None


def get_supported_expert_types() -> List[str]:
    """
    Get list of supported expert types.

    Returns:
        List of expert type strings
    """
    return list(EXPERT_TEMPLATES.keys())


def get_collection_for_expert_type(expert_type: str) -> str:
    """
    Get the default collection name for an expert type.

    Args:
        expert_type: Expert type (frontend, backend, fullstack)

    Returns:
        Default collection name or None if expert type is invalid
    """
    if expert_type in EXPERT_TEMPLATES:
        return EXPERT_TEMPLATES[expert_type]['collection']
    return None


# Example usage
if __name__ == "__main__":
    """Test the ingestion dispatcher with example data."""

    # Test single ingestion
    print("Testing single repository ingestion...\n")

    result = dispatch_ingestion(
        repo_url="https://github.com/shadcn-ui/ui",
        target_collection="frontend_brain",
        verbose=True
    )

    print(f"\nResult: {result}")

    # Test batch ingestion
    print("\n\nTesting batch repository ingestion...\n")

    repositories = [
        {
            'url': 'https://github.com/shadcn-ui/ui',
            'target_collection': 'frontend_brain',
        },
        {
            'url': 'https://github.com/tiangolo/fastapi-template',
            'target_collection': 'backend_brain',
        },
    ]

    results = dispatch_batch_ingestion(repositories, verbose=True)

    print("\nBatch Results:")
    for r in results:
        print(f"  {r['repo_url']}: {'✅ Success' if r['success'] else '❌ Failed'}")