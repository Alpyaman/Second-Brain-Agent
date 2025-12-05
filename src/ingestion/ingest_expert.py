"""
Expert Knowledge Ingestion Script

This script downloads and ingests high-quality open-source codebases to create specialized
knowledge bases for different engineering domains:

- Frontend Brain: Next.js, React, UI patterns (shadcn/ui, Vercel templates)
- Backend Brain: FastAPI, Django, API patterns, database schemas

This enables each agent in the multi-agent system to have domain-specific expertise.

Phase 3: Includes commit hash tracking and update detection for maintenance.
"""

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Set, Optional
from datetime import datetime

from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
CHROMA_DB_DIR = "src/data/chroma_db"

# Expert Templates: Curated repos for each domain
EXPERT_TEMPLATES = {
    "frontend": {
        "name": "Frontend Specialist",
        "collection": "frontend_brain",
        "recommended_repos": [
            {
                "name": "shadcn/ui",
                "url": "https://github.com/shadcn-ui/ui",
                "description": "High-quality React component library"
            },
            {
                "name": "Next.js Examples",
                "url": "https://github.com/vercel/next.js/tree/canary/examples",
                "description": "Official Next.js examples and patterns"
            },
            {
                "name": "T3 App",
                "url": "https://github.com/t3-oss/create-t3-app",
                "description": "Full-stack TypeScript template"
            }
        ],
        "file_extensions": [".ts", ".tsx", ".js", ".jsx", ".css", ".scss"],
        "exclude_patterns": {"node_modules", ".next", "dist", "build", ".git", "__pycache__"}
    },
    "backend": {
        "name": "Backend Specialist",
        "collection": "backend_brain",
        "recommended_repos": [
            {
                "name": "FastAPI Best Practices",
                "url": "https://github.com/zhanymkanov/fastapi-best-practices",
                "description": "FastAPI patterns and conventions"
            },
            {
                "name": "Full Stack FastAPI Template",
                "url": "https://github.com/tiangolo/full-stack-fastapi-template",
                "description": "Production-ready FastAPI template"
            },
            {
                "name": "Django REST Framework Tutorial",
                "url": "https://github.com/encode/django-rest-framework",
                "description": "Django REST patterns"
            }
        ],
        "file_extensions": [".py"],
        "exclude_patterns": {"venv", ".venv", "__pycache__", ".git", "node_modules", "dist", "build"}
    },
    "fullstack": {
        "name": "Full-Stack Specialist",
        "collection": "fullstack_brain",
        "recommended_repos": [
            {
                "name": "T3 Stack",
                "url": "https://github.com/t3-oss/create-t3-app",
                "description": "Full-stack TypeScript (Next.js + tRPC + Prisma)"
            },
            {
                "name": "FastAPI + React Template",
                "url": "https://github.com/tiangolo/full-stack-fastapi-template",
                "description": "FastAPI backend + React Frontend"
            }
        ],
        "file_extensions": [".py", ".ts", ".tsx", ".js", ".jsx"],
        "exclude_patterns": {"node_modules", ".next", "venv", ".venv", "dist", "build", ".git", "__pycache__"}
    }
}

def get_repository_commit_hash(repo_path: Path) -> Optional[str]:
    """
    Get the latest commit hash from a cloned repository.

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
        print(f"Warning: Could not get commit hash: {e}")
        return None


def clone_repository(repo_url: str, target_dir: Path) -> bool:
    """
    Clone a git repository to the target directory.
    
    Args:
        repo_url: Git repository URL
        target_dir: Directory to clone into

    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"Cloning repository: {repo_url}")
        print(f"Target directory: {target_dir}")

        subprocess.run(["git", "clone", "--depth", "1", repo_url, str(target_dir)], check=True, capture_output=True, text=True)

        print("Successfully cloned repository")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"Error cloning repository: {e.stderr}")
        return False
    except FileNotFoundError as e:
        print(f"Error: git is not installed or not in PATH: {e}")
        return False

def find_code_files(directory: Path, file_extensions: List[str], exclude_patterns: Set[str]) -> List[Path]:
    """
    Recursively find code files with specified extensions.

    Args:
        directory: Root directory to search
        file_extensions: List of file extensisons to include
        exclude_patterns: Patterns to exclude from search

    Returns:
        List of Path objects for found files.
    """
    code_files = []

    for file_path in directory.rglob("*"):
        # Skip excluded patterns
        if any(pattern in str(file_path) for pattern in exclude_patterns):
            continue

        # Check if file has desired extension
        if file_path.is_file() and file_path.suffix in file_extensions:
            code_files.append(file_path)

    return code_files

def determine_language_splitter(file_extension: str) -> Optional[Language]:
    """
    Map file extension to LangChain Language enum.

    Args:
        file_extension: File extension (e.g., ".py")

    Returns:
        Language enum value or None for generic splitting
    """
    extension_map = {
        ".py": Language.PYTHON,
        ".js": Language.JS,
        ".jsx": Language.JS,
        ".ts": Language.TS,
        ".tsx": Language.TS,
        ".java": Language.JAVA,
        ".go": Language.GO,
        ".rs": Language.RUST,
        ".cpp": Language.CPP,
        ".c": Language.C,
    }

    return extension_map.get(file_extension)

def load_code_documents(file_paths: List[Path], expert_type: str, repo_url: Optional[str] = None, commit_hash: Optional[str] = None) -> List[Document]:
    """
    Load code files and create Document objects with metadata.

    Args:
        file_paths: List of code file paths to load
        expert_type: Type of expert
        repo_url: Optional GitHub repository URL (for tracking)
        commit_hash: Optional commit hash (for update detection)

    Returns:
        List of Document objects with code content and metadata.
    """
    documents = []
    ingestion_date = datetime.now().isoformat()

    for file_path in file_paths:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Create document with metadata
            metadata = {
                "source": str(file_path),
                "filename": file_path.name,
                "file_type": file_path.suffix,
                "expert_domain": expert_type,
                "relative_path": str(file_path),
                "ingestion_date": ingestion_date,
            }

            # Add repository tracking metadata if provided
            if repo_url:
                metadata["repo_url"] = repo_url
            if commit_hash:
                metadata["commit_hash"] = commit_hash

            doc = Document(page_content=content, metadata=metadata)
            documents.append(doc)

            # Print progress
            print(f"Loaded: {file_path.name}")

        except Exception as e:
            print(f"Error loading {file_path}: {e}")

    return documents

def chunk_code_documents(documents: List[Document]) -> List[Document]:
    """
    Split code documents using language-aware chunking.

    Args:
        documents: List of Document objects with code content.

    Returns:
        List of chunked Document objects.
    """
    chunks = []

    # Group documents by file extension for optimal splitting
    docs_by_extension = {}
    for doc in documents:
        ext = doc.metadata.get("file_type", "")
        if ext not in docs_by_extension:
            docs_by_extension[ext] = []
        docs_by_extension[ext].append(doc)
    
    # Process each group with appropriate splitter
    for ext, docs in docs_by_extension.items():
        language = determine_language_splitter(ext)

        if language:
            # Use language-specific splitter
            splitter = RecursiveCharacterTextSplitter.from_language(language=language, chunk_size=1500, chunk_overlap=200)
        
        else:
            # Use generic splitter for unknown file types
            splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
        
        doc_chunks = splitter.split_documents(docs)
        chunks.extend(doc_chunks)

        print(f"Chunked {len(docs)} {ext} file(s) -> {len(doc_chunks)} chunks")

    return chunks

def ingest_to_expert_brain(chunks: List[Document], collection_name: str) -> Chroma:
    """
    Generate embeddings and store chunks in a specialized expert collection.

    Args:
        chunks: List of Document chunks to ingest.
        collection_name: Name of the expert brain collection

    Returns:
        Chroma vectorstore instance
    """
    print(f"\nInitializing embeddings for '{collection_name}'...")
    print(f"Model: {EMBEDDING_MODEL}")

    # Initialize HuggingFace embeddings
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={'device': 'cpu'}, encode_kwargs={'normalize_embeddings': True})

    print("Generating embedding and storing in ChromaDB.")

    # Create or update ChromaDB collection
    vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings, collection_name=collection_name, persist_directory=str(CHROMA_DB_DIR))

    return vectorstore

def show_recommended_repos(expert_type: str):
    """Display recommended repositories for an expert type."""
    if expert_type not in EXPERT_TEMPLATES:
        print(f"Unknown expert type: {expert_type}")
        print(f"Available types: {', '.join(EXPERT_TEMPLATES.keys())}")
        return

    expert = EXPERT_TEMPLATES[expert_type]

    print("\n", "=" * 70)
    print(f"Recommended Repositories for {expert['name']}")
    print("=" * 70)

    for i, repo in enumerate(expert['recommended_repos'], 1):
        print(f"\n{i}. {repo['name']}")
        print(f"    URL: {repo['url']}")
        print(f"    Description: {repo['description']}")
    
    print("\n", "=" * 70)
    print("\nUsage:")
    print(f" python src/ingest_expert.py --expert {expert_type} --repo <URL>")
    print(f" python src/ingest_expert.py --expert {expert_type} --path /local/repo")
    print("=" * 70)

def ingest_expert_knowledge(expert_type: str, source_path: Optional[Path] = None, repo_url: Optional[str] = None, collection_name: Optional[str] = None, verbose: bool = True):
    """
    Main ingestion pipeline for expert knowledge.

    Args:
        expert_type: Type of expert (frontend, backend, fullstack)
        source_path: Local path to codebase (optional)
        repo_url: Git repository URL to clone (optional)
        collection_name: Custom collection name (optional)
        verbose: Whether to print progress messages (default: True)

    Returns:
        Dict with ingestion results:
        {
            'success': bool,
            'expert_type': str,
            'collection': str,
            'repo_url': str or None,
            'files_processed': int,
            'chunks_created': int,
            'vectors_stored': int,
            'error': str or None
        }
    """
    # Validate expert type
    if expert_type not in EXPERT_TEMPLATES:
        error_msg = f"Unknown expert type: {expert_type}"
        if verbose:
            print(error_msg)
            print(f"Available types: {', '.join(EXPERT_TEMPLATES.keys())}")
        return {
            'success': False,
            'expert_type': expert_type,
            'collection': None,
            'repo_url': repo_url,
            'files_processed': 0,
            'chunks_created': 0,
            'vectors_stored': 0,
            'error': error_msg
        }
    
    expert = EXPERT_TEMPLATES[expert_type]
    collection = collection_name or expert['collection']

    if verbose:
        print("\n", "=" * 70)
        print(f"Expert Knowledge Ingestion: {expert['name']}")
        print("=" * 70)

    # Determine source directory
    temp_dir = None
    if repo_url:
        # Clone repository to temp directory
        temp_dir = tempfile.mkdtemp(prefix=f"{expert_type}_repo_")
        source_path = Path(temp_dir)

        if not clone_repository(repo_url, source_path):
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {
                'success': False,
                'expert_type': expert_type,
                'collection': collection,
                'repo_url': repo_url,
                'files_processed': 0,
                'chunks_created': 0,
                'vectors_stored': 0,
                'error': 'Failed to clone repository'
            }

    elif source_path:
        source_path = Path(source_path)
        if not source_path.exists():
            error_msg = f"Path does not exist: {source_path}"
            if verbose:
                print(f"Error: {error_msg}")
            return {
                'success': False,
                'expert_type': expert_type,
                'collection': collection,
                'repo_url': repo_url,
                'files_processed': 0,
                'chunks_created': 0,
                'vectors_stored': 0,
                'error': error_msg
            }
        if not source_path.is_dir():
            error_msg = f"Path is not a directory: {source_path}"
            if verbose:
                print(f"Error: {error_msg}")
            return {
                'success': False,
                'expert_type': expert_type,
                'collection': collection,
                'repo_url': repo_url,
                'files_processed': 0,
                'chunks_created': 0,
                'vectors_stored': 0,
                'error': error_msg
            }

    else:
        error_msg = "Must provide either repo_url or source_path"
        if verbose:
            print(f"Error: {error_msg}")
        return {
            'success': False,
            'expert_type': expert_type,
            'collection': collection,
            'repo_url': repo_url,
            'files_processed': 0,
            'chunks_created': 0,
            'vectors_stored': 0,
            'error': error_msg
        }
    
    try:
        # Step 0: Get commit hash for tracking (Phase 3: Maintenance)
        commit_hash = None
        if repo_url and source_path:
            commit_hash = get_repository_commit_hash(source_path)
            if commit_hash and verbose:
                print(f"Repository commit hash: {commit_hash[:8]}...")

        # Step 1: Find code files
        if verbose:
            print(f"\nScanning directory: {source_path}")
            print(f"Looking for: {', '.join(expert['file_extensions'])}")

        code_files = find_code_files(source_path, expert['file_extensions'], expert['exclude_patterns'])

        if not code_files:
            error_msg = "No code files found matching criteria"
            if verbose:
                print(error_msg)
            return {
                'success': False,
                'expert_type': expert_type,
                'collection': collection,
                'repo_url': repo_url,
                'commit_hash': commit_hash,
                'files_processed': 0,
                'chunks_created': 0,
                'vectors_stored': 0,
                'error': error_msg
            }

        if verbose:
            print(f"Found {len(code_files)} code file(s)\n")

        # Step 2: Load documents with metadata (Phase 3: includes commit hash)
        if verbose:
            print("Loading code files")
        documents = load_code_documents(code_files, expert_type, repo_url=repo_url, commit_hash=commit_hash)
        if verbose:
            print(f"Successfully loaded {len(documents)} file(s)\n")

        if not documents:
            error_msg = "No files were successfully loaded"
            if verbose:
                print(error_msg)
            return {
                'success': False,
                'expert_type': expert_type,
                'collection': collection,
                'repo_url': repo_url,
                'files_processed': 0,
                'chunks_created': 0,
                'vectors_stored': 0,
                'error': error_msg
            }

        # Step 3: Chunk documents
        if verbose:
            print("Chunking code (language-aware)...")
        chunks = chunk_code_documents(documents)
        if verbose:
            print(f"Created {len(chunks)} total chunks\n")

        # Step 4: Ingest to expert brain
        vectorstore = ingest_to_expert_brain(chunks, collection)
        vectors_stored = vectorstore._collection.count()

        # Summary
        if verbose:
            print("=" * 70)
            print("Expert Knowledge Ingestion Complete")
            print("=" * 70)
            print(f"Expert Domain:      {expert['name']}")
            print(f"Files Processed:   {len(documents)}")
            print(f"Chunks created:     {len(chunks)}")
            print(f"Collection Name:    {collection}")
            print(f"ChromaDB location:  {CHROMA_DB_DIR}")
            print(f"Vectors Stored:     {vectors_stored}")
            print("\n This expert brain is now ready for specialized agent usage")
            print("=" * 70)

        return {
            'success': True,
            'expert_type': expert_type,
            'collection': collection,
            'repo_url': repo_url,
            'commit_hash': commit_hash,
            'files_processed': len(documents),
            'chunks_created': len(chunks),
            'vectors_stored': vectors_stored,
            'error': None
        }

    except Exception as e:
        error_msg = f"Ingestion failed: {str(e)}"
        if verbose:
            print(f"\nError: {error_msg}")
            import traceback
            traceback.print_exc()
        return {
            'success': False,
            'expert_type': expert_type,
            'collection': collection,
            'repo_url': repo_url,
            'commit_hash': None,
            'files_processed': 0,
            'chunks_created': 0,
            'vectors_stored': 0,
            'error': error_msg
        }

    finally:
        # Cleanup temp directory if created
        if temp_dir:
            if verbose:
                print("\nCleaning up temporary directory...")
            shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """CLI entry point for expert knowledge ingestion."""
    parser = argparse.ArgumentParser(
        description="Ingest expert knowledge from high-quality codebases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
            # Show recommended repos for frontend
            python src/ingest_expert.py -expert frontend --list

            # Clone and ingest shadcn/ui for frontend specialist
            python src/ingest_expert.py -expert frontend --repo https://github.com/shadcn-ui/ui

            # Ingest local FastAPI project for backend specialist
            python src/ingest_expert.py --expert backend --path /path/to/fastapi-project

            # Custom collection name
            python src/ingest_expert.py --expert frontend --repo <URL> --collection my_frontend_brain

            Available Expert Types:
                - frontend:     React, Next.js, TypeScript, UI patterns
                - backend:      Python, FastAPI, Django, API patterns
                - fullstack:    Full-stack patterns (frontend + backend)
        """
    )

    parser.add_argument("--expert", type=str, required=True, choices=list(EXPERT_TEMPLATES.keys()), help="Type of expert knowledge to ingest")

    parser.add_argument("--repo", type=str, help="Git repository URL to clone and ingest")

    parser.add_argument("--path", type=str, help="Local path to codebase directory")

    parser.add_argument("--collection", type=str, help="Custom collection name (default: <expert>_brain)")

    parser.add_argument("--list", action="store_true", help="List of recommended repositories for the expert type")

    args = parser.parse_args()

    # Show recommended repos if requested
    if args.list:
        show_recommended_repos(args.expert)
        return
    
    # Validate that either repo or path is provided
    if not args.repo and not args.path:
        print("Error: Must provide either --repo or --path")
        print("\nUse --list to see recommended repositories:")
        return
    
    # Run ingestion
    ingest_expert_knowledge(expert_type=args.expert, source_path=Path(args.path) if args.path else None, repo_url=args.repo, collection_name=args.collection)

if __name__ == "__main__":
    main()