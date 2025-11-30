"""
Markdown Notes Ingestion Script

This script recursively scans the data/notes/ directory for markdown and text files, chunk
them, generates embedding, and stores them in ChromaDB for retrieval.
"""

from pathlib import Path
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
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

def main():
    """Main ingestion pipeline."""
    print("=" * 60)
    print("Second-Brain Agent: Markdown Notes Ingestion")
    print("=" * 60)

    # Step 1: Find markdown files
    print(f"\nScanning directory: {NOTES_DIR}")
    markdown_files = find_markdown_files(NOTES_DIR)

    if not markdown_files:
        print("No markdown or text files found in data/notes/")
        return
    
    print(f"Found {len(markdown_files)} file(s)\n")

    # Step 2: Load documents
    print("Loading documents")
    documents = load_documents(markdown_files)
    print(f"\nSuccessfully loaded {len(documents)} document(s)")

    if not documents:
        print("No documents were successfully loaded.")
        return
    
    # Step 3: Chunk documents
    print("\nChunking documents")
    chunks = chunk_documents(documents)
    print(f"Created {len(chunks)} chunk(s)")

    # Step 4: Ingest to ChromaDB
    vectorstore = ingest_to_chromadb(chunks)

    # Summary
    print("\n" + "=" * 60)
    print(f"INGESTION COMPLETE {vectorstore}")
    print("=" * 60)
    print("Summary:")
    print(f"   - Files processed: {len(documents)}")
    print(f"   - Total chunks created: {len(chunks)}")
    print(f"   - ChromaDB location: {CHROMA_DB_DIR}")
    print(f"   - Collection name: {COLLECTION_NAME}")
    print("\nYour notes are now indexed and ready for retrieval!")
    print("=" * 60)

if __name__ == "__main__":
    main()