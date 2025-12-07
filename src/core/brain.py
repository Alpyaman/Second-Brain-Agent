"""
Second Brain Query Module

This module provides the ability to query your second brain using RAG.
It retrieves relevant from ChromaDB and uses Gemini to synthesize answers based on the
retrieved context.
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

from src.core.config import EMBEDDING_MODEL, CHROMA_DB_DIR, COLLECTION_NAME
from src.tools.memory import get_relevant_preferences

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def query_second_brain(query: str, k: int = 5) -> str:
    """
    Query your second brain and get an answer based on your notes.

    Args:
        query: The question to ask your second brain
        k: Number of relevant chunks to retrieve
    
    Returns:
        A synthesized answer based on the retrieved notes, or a message indicating the
        informatin wasn't found in the notes.
    """
    # Fetch user preferences for personalization
    print("Fetching user preferences...")
    preferences = get_relevant_preferences(query)

    # Initialize embeddings
    print(f"Loading embeddings model: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={'device': 'cpu'}, encode_kwargs={'normalize_embeddings': True})

    # Connect to existing ChromaDB
    print(f"Connecting to ChromaDB at: {CHROMA_DB_DIR}")
    vectorstore = Chroma(collection_name=COLLECTION_NAME, embedding_function=embeddings, persist_directory=str(CHROMA_DB_DIR))

    # Perform similarity search
    print(f"Searching for: '{query}'")
    relevant_docs = vectorstore.similarity_search(query, k=k)

    if not relevant_docs:
        return "I don't have that in your Second Brain records."
    
    # Print retrieved documents for transparency
    print(f"\nFound {len(relevant_docs)} relevant chunk(s)")
    for i, doc in enumerate(relevant_docs, 1):
        source = doc.metadata.get('filename', 'unknown')
        preview = doc.page_content[:100].replace('\n', ' ')
        print(f"{i}. {source}: {preview}")

    # Prepare context from retrieved documents
    context = "\n\n---\n\n".join([doc.page_content for doc in relevant_docs])

    # Build system prompt with optional preferences

    system_prompt = """You are a helpful assistant that answers questions based ONLY on the provided context from the user's personal notes (their "Second Brain").

Guidelines:
- Answer the question using ONLY information from the context provided
- If the context contains relevant information, provide a clear, concise answer
- If the answer is NOT in the context, respond with: "I don't have that in your Second Brain records."
- Do not use external knowledge or make assumptions beyond what's in the context
- Cite specific details from the notes when possible
- Be conversational but accurate"""

    # Inject user preferences if available
    if preferences:
        system_prompt += f"\n\n{preferences}"

    # Create prompt template
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user","""Context from my notes:
        {context}
        ---
        Question: {query}
        Answer:""")
    ])

    # Initialize Gemini Model
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.3)

    # Create chain
    chain = prompt_template | llm | StrOutputParser()

    # Generate answer
    print("Generating answer\n")
    answer = chain.invoke({"context": context, "query": query})

    return answer

if __name__ == "__main__":
    """Test the query function with a dummy query."""
    print("=" * 60)
    print("Second-Brain-Agent: Query Test")
    print("=" * 60)
    print()

    # Test query
    test_query = "What is the Second-Brain-Agent project about?"

    print(f"Query: {test_query}\n")
    print("-" * 60)

    answer = query_second_brain(test_query)

    print("-" * 60)
    print("\nAnswer:")
    print(answer)
    print("\n" + "=" * 60)