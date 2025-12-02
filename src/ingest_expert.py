"""
Expert Knowledge Ingestion Script

This script downloads and ingests high-quality open-source codebases to create specialized
knowledge bases for different engineering domains:

- Frontend Brain: Next.js, React, UI patterns (shadcn/ui, Vercel templates)
- Backend Brain: FastAPI, Django, API patterns, database schemas

This enables each agent in the multi-agent system to have domain-specific expertise.
"""

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Set, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from config import CHROMA_DB_DIR, EMBEDDING_MODEL


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
        "file_enxtensions": [".py"],
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

def load_code_documents(file_paths: List[Path], expert_type: str) -> List[Document]:
    """
    Load code files and create Document objects with metadata.

    Args:
        file_paths: List of code file paths to load
        expert_type: Type of expert

    Returns:
        List of Document objects with code content and metadata.
    """
    documents = []

    for file_path in file_paths:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            # Create document with metadata
            doc = Document(page_content=content, metadata={
                    "source": str(file_path),
                    "filename": file_path.name,
                    "file_type": file_path.suffix,
                    "expert_domain": expert_type,
                    "relative_path": str(file_path)
                }
            )
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

def ingest_expert_knowledge(expert_type: str, source_path: Optional[Path] = None, repo_url: Optional[str] = None, collection_name: Optional[str] = None):
    """
    Main ingestion pipeline for expert knowledge.

    Args:
        expert_type: Type of expert (frontend, backend, fullstack)
        source_path: Local path to codebase (optional)
        repo_url: Git repository URL to clone (optional)
        collection_name: Custom collection name (optional)
    """
    # Validate expert type
    if expert_type not in EXPERT_TEMPLATES:
        print(f"Unknown expert type: {expert_type}")
        print(f"Available types: {', '.join(EXPERT_TEMPLATES.keys())}")
        return
    
    expert = EXPERT_TEMPLATES[expert_type]
    collection = collection_name or expert['collection']

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
            return

    elif source_path:
        source_path = Path(source_path)
        if not source_path.exists():
            print(f"Error: Path does not exist: {source_path}")
            return
        if not source_path.is_dir():
            print(f"Error: Path is not a directory: {source_path}")
            return

    else:
        print("Error: Must provide either --repo or --path")
        return
    
    try:
        # Step 1: Find code files
        print(f"\nScanning directory: {source_path}")
        print(f"Looking for: {', '.join(expert['file_extensions'])}")

        code_files = find_code_files(source_path, expert['file_extensions'], expert['exclude_patterns'])

        if not code_files:
            print("No code files found matching criteria")
            return
    
        print(f"Found {len(code_files)} code file(s)\n")

        # Step 2: Load documents
        print("Loading code files")
        documents = load_code_documents(code_files, expert_type)
        print(f"Successfully loaded {len(documents)} file(s)\n")

        if not documents:
            print("No files were successfully loaded")
            return

        # Step 3: Chunk documents
        print("Chunking code (language-aware)...")
        chunks = chunk_code_documents(documents)
        print(f"Created {len(chunks)} total chunks\n")

        # Step 4:Ingest to expert brain
        vectorstore = ingest_to_expert_brain(chunks, collection)

        # Summary
        print("=" * 70)
        print("Expert Knowledge Ingestion Complete")
        print("=" * 70)
        print(f"Expert Domain:      {expert['name']}")
        print(f"Files Processed:   {len(documents)}")
        print(f"Chunks created:     {len(chunks)}")
        print(f"Collection Name:    {collection}")
        print(f"ChromaDB location:  {CHROMA_DB_DIR}")
        print(f"Vectors Stored:     {vectorstore._collection.count()}")
        print("\n This expert brain is now ready for specialized agent usage")
        print("=" * 70)

    finally:
        # Cleanup temp directory if created
        if temp_dir:
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

    parser.add_argument(type=str, required=True, choices=list(EXPERT_TEMPLATES.keys()), help="Type of expert knowledge to ingest")

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