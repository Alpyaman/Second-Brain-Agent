"""
Parent-Child Ingestion Pipeline

This module implements an advanced RAG ingestion strategy using Parent-Child retrieval.

Traditional RAG Problem:
- Retrieves small, context-less code snippets (5-10 lines)
- LLM can't understand patterns from fragmented code

Parent-Child Solution:
1. Parse code into complete functions/classes (Parents)
2. Generate concise summaries (Children)
3. Embed and search ONLY children
4. Return full parent code blocks to LLM

Result: LLM receives complete, contextual code blocks (50-500 lines)
instead of meaningless snippets.
"""

from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.core.config import CHROMA_DB_DIR, EMBEDDING_MODEL
from src.ingestion.parent_child_code_parser import create_parent_child_documents

def process_code_files_with_parent_child(file_paths: List[Path], expert_type: str, repo_url: Optional[str] = None, commit_hash: Optional[str] = None) -> Dict[str, List[Document]]:
    """
    Process code files using parent-child extraction.

    Args:
        file_paths: List of code file paths
        expert_type: Type of expert (frontend, backend, fullstack)
        repo_url: Optional repository URL
        commit_hash: Optional commit hash

    Returns:
        Dictionary with 'parents' and 'children' lists of Document objects
    """
    all_parents = []
    all_children = []
    fallback_chunks = []  # For unsupported file types

    ingestion_date = datetime.now().isoformat()

    print(f"\nProcessing {len(file_paths)} files with parent-child extraction...")

    for file_path in file_paths:
        try:
            # Read file
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Build metadata
            metadata = {"source": str(file_path), "filename": file_path.name, "file_type": file_path.suffix, "expert_domain": expert_type, "relative_path": str(file_path), "ingestion_date": ingestion_date}

            if repo_url:
                metadata["repo_url"] = repo_url
            if commit_hash:
                metadata["commit_hash"] = commit_hash

            # Extract parent-child pairs
            parents, children = create_parent_child_documents(code=content, file_metadata=metadata, file_extension=file_path.suffix)

            if parents and children:
                # Successful parent-child extraction
                all_parents.extend(parents)
                all_children.extend(children)
                print(f"   {file_path.name}: {len(parents)} code blocks extracted")
            else:
                # Fallback to traditional chunking for unsupported files
                # We'll use simple splitting as a fallback
                from langchain_text_splitters import RecursiveCharacterTextSplitter

                splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)

                doc = Document(page_content=content, metadata=metadata)
                chunks = splitter.split_documents([doc])
                fallback_chunks.extend(chunks)
                print(f"  - {file_path.name}: Using traditional chunking ({len(chunks)} chunks)")

        except Exception as e:
            print(f"  ✗ Error processing {file_path.name}: {e}")

    print("\nExtraction Summary:")
    print(f"  Parent documents (full code): {len(all_parents)}")
    print(f"  Child documents (summaries): {len(all_children)}")
    print(f"  Fallback chunks: {len(fallback_chunks)}")

    return {"parents": all_parents, "children": all_children, "fallback": fallback_chunks}

def ingest_with_parent_child(parent_docs: List[Document], child_docs: List[Document], fallback_docs: List[Document], collection_name: str) -> Dict[str, any]:
    """
    Ingest documents using parent-child strategy.

    Strategy:
    1. Store ALL documents (parents, children, fallback) in the SAME collection
    2. Children and fallback get embedded (used for search)
    3. Parents are stored but NOT embedded (metadata only)
    4. When child is retrieved, we'll fetch its parent using parent_id

    Args:
        parent_docs: Full code block documents
        child_docs: Summary documents (will be embedded)
        fallback_docs: Traditional chunks for unsupported files
        collection_name: ChromaDB collection name

    Returns:
        Dictionary with ingestion statistics
    """
    print(f"\nIngesting to collection: {collection_name}")
    print("=" * 70)

    # Initialize embeddings
    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={'device': 'cpu'}, encode_kwargs={'normalize_embeddings': True})

    # Combine documents for ingestion
    # We'll embed children + fallback (search documents)
    # Parents will be stored separately with a special collection
    search_documents = child_docs + fallback_docs

    print(f"\nEmbedding {len(search_documents)} search documents...")
    print("  (These will be used for vector similarity search)")

    # Create/update main collection with search documents
    vectorstore = Chroma.from_documents(documents=search_documents, embedding=embeddings, collection_name=collection_name, persist_directory=str(CHROMA_DB_DIR))

    # Store parents in a separate collection for lookup
    parent_collection_name = f"{collection_name}_parents"

    print(f"\nStoring {len(parent_docs)} parent documents in: {parent_collection_name}")
    print("  (These provide full context when children are retrieved)")

    if parent_docs:
        # We need to embed parents too to store them, but we won't search this collection
        # Instead we'll use metadata lookup
        parent_vectorstore = Chroma.from_documents(documents=parent_docs, embedding=embeddings, collection_name=parent_collection_name, persist_directory=str(CHROMA_DB_DIR))

    print("\n" + "=" * 70)
    print("INGESTION COMPLETE")
    print("=" * 70)
    print(f"{len(parent_vectorstore)}, {len(vectorstore)}")

    return {"children_embedded": len(child_docs), "parents_stored": len(parent_docs), "fallback_chunks": len(fallback_docs), "total_search_documents": len(search_documents), "collection_name": collection_name, "parent_collection_name": parent_collection_name if parent_docs else None}

def retrieve_with_parent_lookup(query: str, collection_name: str, k: int = 5) -> List[Document]:
    """
    Retrieve documents using parent-child strategy.

    Process:
    1. Search children collection (summaries)
    2. Extract parent_ids from retrieved children
    3. Fetch full parent documents
    4. Return parents (full code context) instead of children

    Args:
        query: Search query
        collection_name: Main collection name
        k: Number of results

    Returns:
        List of parent Documents with full code context
    """
    # Initialize embeddings
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={'device': 'cpu'}, encode_kwargs={'normalize_embeddings': True})

    # Search children collection
    print(f"\nSearching children summaries in: {collection_name}")
    child_vectorstore = Chroma(collection_name=collection_name, embedding_function=embeddings, persist_directory=str(CHROMA_DB_DIR))

    # Retrieve child documents
    child_results = child_vectorstore.similarity_search(query, k=k)

    if not child_results:
        return []

    print(f"Found {len(child_results)} relevant summaries")

    # Extract parent IDs
    parent_ids = []
    fallback_docs = []

    for doc in child_results:
        if doc.metadata.get("is_child"):
            # This is a child document - needs parent lookup
            parent_id = doc.metadata.get("parent_id")
            if parent_id:
                parent_ids.append(parent_id)
        else:
            # This is a fallback chunk - use as-is
            fallback_docs.append(doc)

    if not parent_ids:
        # No parent-child documents, return fallback chunks
        return fallback_docs

    # Fetch parent documents
    print(f"Fetching {len(parent_ids)} parent documents...")
    parent_collection_name = f"{collection_name}_parents"

    try:
        parent_vectorstore = Chroma(collection_name=parent_collection_name, embedding_function=embeddings, persist_directory=str(CHROMA_DB_DIR))

        # Retrieve parents by filtering on parent_id
        all_parents = []
        for parent_id in parent_ids:
            # Get documents where parent_id matches
            results = parent_vectorstore.get(where={"parent_id": parent_id})

            if results and results['documents']:
                # Reconstruct Document objects
                for i, doc_content in enumerate(results['documents']):
                    metadata = results['metadatas'][i] if results.get('metadatas') else {}
                    parent_doc = Document(page_content=doc_content, metadata=metadata)
                    all_parents.append(parent_doc)

        print(f"Retrieved {len(all_parents)} parent documents (full code context)")

        # Combine parents and fallback docs
        return all_parents + fallback_docs

    except Exception as e:
        print(f"Error fetching parents: {e}")
        print("Falling back to child summaries")
        return child_results

if __name__ == "__main__":
    print("Parent-Child Ingestion Module")
    print("=" * 70)
    print("This module implements advanced RAG with parent-child retrieval.")
    print("\nKey Features:")
    print("   Extracts complete functions/classes (parents)")
    print("   Generates searchable summaries (children)")
    print("   Returns full code context to LLM")
    print("\nImport this module in your ingestion pipeline to enable parent-child RAG.")