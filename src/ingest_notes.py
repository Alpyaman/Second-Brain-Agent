"""
Notes and Code Ingestion Script

This script ingests both markdown notes and code files into ChromaDB:
- Markdown/text files go into 'ssecond_brain_notes' collection
- Code files go into 'coding_brain' collection with extracted metadata 
"""

import argparse
import ast
from pathlib import Path
from typing import List, Dict, Set

from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from config import NOTES_DIR, CHROMA_DB_DIR, COLLECTION_NAME, EMBEDDING_MODEL


def find_markdown_files(directory: Path) -> List[Path]:
    """
    Recursively find all .md and .txt files in the given directory.

    Args:
        directory: Path to search for files.

    Returns:
        List of Path objects for found files.
    """
    markdown_files = []

    for file_path in directory.rglob("*"):
        if file_path.is_file() and file_path.suffix in [".md", ".txt"]:
            markdown_files.append(file_path)

    return markdown_files

def load_documents(file_paths: List[Path]) -> List[Document]:
    """
    Load content from markdown files and create Document objects.

    Args:
        file_paths: List of file paths to load.

    Returns:
        List of Document objects with content and metadata
    """
    documents = []

    for file_path in file_paths:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Create document with metadata
            doc = Document(page_content=content, metadata={"source": str(file_path), "filename": file_path.name, "file_type": file_path.suffix})
            documents.append(doc)
            print(f"Loaded {file_path.name}")

        except Exception as e:
            print(f"Error loading {file_path}: {e}")

    return documents

def chunk_documents(documents: List[Document]) -> List[Document]:
    """
    Split documents into smaller chunks for better retrieval.

    Args:
        documents: List of Document objects to chunk

    Returns:
        List of chunked Document objects
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len, separators=["\n\n", "\n", " ", ""])

    chunks = text_splitter.split_documents(documents)
    return chunks

def ingest_to_chromadb(chunks: List[Document]) -> Chroma:
    """
    Generate embeddings and store chunks in ChromaDB.

    Args:
        chunks: List of Document chunks to ingest.

    Returns:
        Chroma vectorstore instance
    """
    print("\nGenerating embeddings and storing in ChromaDB")

    # Initialize embeddings
    embeddings = HuggingFaceEmbeddings(model=EMBEDDING_MODEL, model_kwargs={'device': 'cpu'}, encode_kwargs={'normalize_embeddings': True})

    # Create or update ChromaDB collection
    vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings, collection_name=COLLECTION_NAME, persist_directory=str(CHROMA_DB_DIR))

    return vectorstore

def find_python_files(directory: Path, exclude_patterns: Set[str] = None) -> List[Path]:
    """
    Recursively find all .py files in the given directory.

    Args:
        directory: Path to search for files
        exclude_patterns: Set of patterns to exclude
    
    Returns:
        List of Path objects for found Python Files
    """
    if exclude_patterns is None:
        exclude_patterns = {'__pycache__', '.venv', 'venv', '.git', 'node_modules', 'dist', 'build'}

    python_files = []

    for file_path in directory.rglob("*.py"):
        # Check if any exclude pattern is in the path
        if any(pattern in str(file_path) for pattern in exclude_patterns):
            continue

        if file_path.is_file():
            python_files.append(file_path)

    return python_files

def extract_code_metadata(file_path: Path) -> Dict[str, List[str]]:
    """
    Extract class and function names from Python code using AST parsing.

    Args:
        file_path: Path to Python file

    Returns:
        Dictionary with 'classes' and 'functions' lists
    """
    metadata = {'classes': [], 'functions': []}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse the Python code into an AST
        tree = ast.parse(content)

        # Walk through the AST and extract definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                metadata["classes"].append(node.name)
            elif isinstance(node, ast.FunctionDef):
                # Only top-level functions
                if isinstance(node, ast.FunctionDef):
                    metadata["functions"].append(node.name)

    except Exception as e:
        print(f"Could not parse {file_path.name}: {e}")

    return metadata

def load_code_documents(file_paths: List[Path]) -> List[Document]:
    """
    Load Python files and create Document object with metadata.

    Args:
        file_paths: List of Python file paths to load

    Returns:
        List of Document objects with code content and metadata
    """
    documents = []

    for file_path in file_paths:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract code metadata
            code_metadata = extract_code_metadata(file_path)

            # Create document with enriched metadata
            doc = Document(
                page_content=content,
                metadata={
                    "source": str(file_path),
                    "filename": file_path.name,
                    "file_type": ".py",
                    "language": "python",
                    "classes": ", ".join(code_metadata['classes']) if code_metadata["classes"] else "none",
                    "functions": ", ".join(code_metadata['functions'][:10]) if code_metadata["functions"] else "none",
                }
            )
            documents.append(doc)

            # Print summary
            classes_str = f"{len(code_metadata['classes'])} classes" if code_metadata['classes'] else "no classes"
            funcs_str = f"{len(code_metadata['functions'])} functions" if code_metadata['functions'] else "no functions"
            print(f"Loaded: {file_path.name} ({classes_str}, {funcs_str})")

        except Exception as e:
            print(f"Error loading {file_path}: {e}")

    return documents

def chunkn_code_documents(documents: List[Document]) -> List[Document]:
    """
    Split code documents using Python-aware chunking.

    Args:
        documents: List of Document objects with code content

    Returns:
        List of chunked Document object.
    """
    # Use Python-specific splitter that understands code structure
    python_splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.PYTHON, chunk_size=1000, chunk_overlap=200
    )
    
    chunks = python_splitter.split_documents(documents)
    return chunks

def ingest_to_chromadb_collection(chunks: List[Document], collection_name: str) -> Chroma:
    """
    Generate embeddings and store chunks in a specific ChromaDB collection.

    Args:
        chunks: List of Document chunks to ingest.
        collection_name: Name of the ChromaDB collection

    Returns:
        Chroma vectorstore instance
    """
    print(f"\nInitializing HuggingFace embeddings for '{collection_name}'...")
    print(f"Model: {EMBEDDING_MODEL}")

    # Initialize HuggingFace embeddings
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={'device': 'cpu'}, encode_kwargs={'normalize_embeddings': True})

    print("Generating embeddings and storing in ChromaDB.")

    # Create or update ChromaDB collection
    vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings, collection_name=collection_name, persist_directory=str(CHROMA_DB_DIR))

    return vectorstore

def ingest_codebase(directory: Path, collection_name: str= "coding_brain"):
    """
    Ingest a codebase directory into ChromaDB.

    Args:
        directory: Path to the codebase directory.
        collection_name: Name for the ChromaDB collection (default: "coding_brain")
    """
    print("=" * 60)
    print("Second-Brain-Agent: Code Ingestion")
    print("=" * 60)

    # Step 1: Find python files
    print(f"\nScanning directory: {directory}")
    python_files = find_python_files(directory)

    if not python_files:
        print("No python files found")
        return
    
    print(f"Found {len(python_files)} Python file(s)\n")

    # Step 2: Load code documents with metadata
    print("Loading code files...")
    documents = load_code_documents(python_files)
    print(f"\nSuccessfully loaded {len(documents)} file(s)")

    if not documents:
        print("No code files were successfully loaded.")
        return
    
    # Step 3: Chunk code
    print("\nChunking code (Python-aware)...")
    chunks = chunkn_code_documents(documents)
    print(f"Created {len(chunks)} chunk(s)")

    # Step 4: Ingest to ChromaDB
    vectorstore = ingest_to_chromadb_collection(chunks, collection_name)

    # Summary
    print("\n", "=" * 60)
    print("Code Ingestion Complete")
    print("=" * 60)
    print("Summary:\n")
    print(f"- Python files processed: {len(documents)}\n")
    print(f"- Total chunks created: {len(chunks)}\n")
    print(f"- ChromaDB location: {CHROMA_DB_DIR}\n")
    print(f"- Collection name: {collection_name}\n")
    print(f"- Code's ingested to ChromaDB: {len(vectorstore)}")
    print("Your codebase is now indexed and ready for retrieval!")
    print("=" * 60)

def main():
    """Main ingestion pipeline for notes and optionally code."""
    parser = argparse.ArgumentParser(
        description="Ingest notes and code into Second-Brain-Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
            # Ingest markdown notes
            python src/ingest_notes.py

            # Ingest code from a directory
            python src/ingest_notes.py --code /path/to/codebase

            # Ingest both notes and code
            python src/ingest_notes.py --code /path/to/codebase --notes
        """
    )

    parser.add_argument("--code", type=str, help="Path to codebase directory to ingest")

    parser.add_argument("--notes", action="store_true", help="Ingest markdown notes (default if no --code specified)")

    parser.add_argument("--collection", type=str, default="coding_brain", help="Collection name for code (default: coding_brain)")

    args = parser.parse_args()

    # Determine what to ingest
    ingest_notes = args.notes or not args.code
    ingest_code = args.code is not None

    # Ingest notes if requested or if nothing else specified
    if ingest_notes:
        print("=" * 60)
        print("Second-Brain-Agent: Markdown Notes Ingestion")
        print("=" * 60)

        # Step 1: Find markdown files
        print(f"\nScanning directory: {NOTES_DIR}")
        markdown_files = find_markdown_files(NOTES_DIR)

        if not markdown_files:
            print("No markdown or text files found in data/notes/")
            print("Please add some .md or .txt files and try again.")
        else:
            print(f"Found {len(markdown_files)} file(s)\n")

            # Step 2: Load documents
            print("Loading documents...")
            documents = load_documents(markdown_files)
            print(f"\nSuccessfully loaded {len(documents)} document(s)")

            if documents:
                # Step 3: Chunk documents
                print("\nChunking documents...")
                chunks = chunk_documents(documents)
                print(f"Created {len(chunks)} chunk(s)")

                # Step 4: Ingest to ChromaDB
                vectorstore = ingest_to_chromadb(chunks)

                # Summary
                print("\n" + "=" * 60)
                print("INGESTION COMPLETE")
                print("=" * 60)
                print("Summary:")
                print(f"   - Files processed: {len(documents)}")
                print(f"   - Total chunks created: {len(chunks)}")
                print(f"   - ChromaDB location: {CHROMA_DB_DIR}")
                print(f"   - Collection name: {COLLECTION_NAME}")
                print(f"    - Ingested to ChromaDB: {len(vectorstore)}")
                print("\nYour notes are now indexed and ready for retrieval!")
                print("=" * 60)
            else:
                print("No documents were successfully loaded.")

        print()  # Add spacing

    # Ingest code if requested
    if ingest_code:
        code_dir = Path(args.code)
        if not code_dir.exists():
            print(f"Error: Directory not found: {code_dir}")
        elif not code_dir.is_dir():
            print(f"Error: Not a directory: {code_dir}")
        else:
            ingest_codebase(code_dir, args.collection)

if __name__ == "__main__":
    main()