"""
Answer generation using Groq API with retrieval-augmented generation.
"""
import os
from groq import Groq
from dotenv import load_dotenv
from typing import Dict, Optional
import config
from search.hybrid_search import semantic_search
from rag.prompt_templates import (
    SYSTEM_PROMPT,
    build_messages,
    extract_sources_from_results
)

# Try to use Streamlit secrets first (for cloud deployment), then fall back to .env (for local)
try:
    import streamlit as st
    api_key = st.secrets.get("GROQ_API_KEY")
except:
    # Load from .env for local development
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")

# Global client
_client = None


def get_client() -> Groq:
    """Get or create Groq client (singleton pattern)."""
    global _client
    if _client is None:
        # Use the api_key loaded at module level
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found. "
                "For local: Create a .env file with your API key. "
                "For deployment: Add GROQ_API_KEY to Streamlit secrets."
            )
        _client = Groq(api_key=api_key)
    return _client


def answer_question(
    question: str,
    top_k: int = config.DEFAULT_TOP_K,
    search_method: str = "hybrid",
    model: str = config.GROQ_MODEL,
    max_tokens: int = config.MAX_TOKENS,
    temperature: float = config.TEMPERATURE
) -> Dict[str, any]:
    """
    Answer a question using RAG with WHO sources.
    
    Args:
        question: User's question
        top_k: Number of source documents to retrieve
        search_method: Search method to use ("vector", "bm25", or "hybrid")
        model: Groq model to use
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0 = deterministic)
        
    Returns:
        Dictionary with:
        - question: The original question
        - answer: Generated answer with citations
        - sources: List of source documents used
        - search_method: Method used for retrieval
        - model: Model used for generation
    """
    # Retrieve relevant sources
    print(f"Searching for relevant sources (method: {search_method}, top_k: {top_k})...")
    results = semantic_search(question, top_k=top_k, method=search_method)
    
    if not results:
        return {
            "question": question,
            "answer": "I couldn't find any relevant information in the WHO knowledge base to answer this question.",
            "sources": [],
            "search_method": search_method,
            "model": model
        }
    
    print(f"Found {len(results)} relevant sources")
    
    # Build messages for Groq
    messages = build_messages(question, results)
    
    # Add system prompt as first message
    messages_with_system = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + messages
    
    # Generate answer
    print(f"Generating answer with {model}...")
    client = get_client()
    
    response = client.chat.completions.create(
        model=model,
        messages=messages_with_system,
        max_tokens=max_tokens,
        temperature=temperature
    )
    
    # Extract answer text
    answer = response.choices[0].message.content
    
    # Extract source metadata
    sources = extract_sources_from_results(results)
    
    print("Answer generated successfully")
    
    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "search_method": search_method,
        "model": model,
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
    }


def answer_with_conversation_history(
    question: str,
    conversation_history: list[dict],
    top_k: int = config.DEFAULT_TOP_K,
    search_method: str = "hybrid"
) -> Dict[str, any]:
    """
    Answer a question with conversation history for follow-up questions.
    
    Args:
        question: Current question
        conversation_history: List of previous messages (role, content pairs)
        top_k: Number of source documents to retrieve
        search_method: Search method to use
        
    Returns:
        Dictionary with answer and sources
    """
    # For now, retrieve based only on current question
    # Future enhancement: expand query based on conversation context
    results = semantic_search(question, top_k=top_k, method=search_method)
    
    if not results:
        return {
            "question": question,
            "answer": "I couldn't find any relevant information in the WHO knowledge base to answer this question.",
            "sources": [],
            "search_method": search_method,
        }
    
    # Build messages with conversation history
    from rag.prompt_templates import build_context
    context = build_context(results)
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(conversation_history)
    messages.append({
        "role": "user",
        "content": f"""Context from WHO sources:

{context}

Question: {question}

Please answer the question using only the information from the sources above. Cite sources using [1], [2], etc."""
    })
    
    # Generate answer
    client = get_client()
    response = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=messages,
        max_tokens=config.MAX_TOKENS,
        temperature=config.TEMPERATURE
    )
    
    answer = response.choices[0].message.content
    sources = extract_sources_from_results(results)
    
    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "search_method": search_method,
    }


if __name__ == "__main__":
    # Test answer generation
    import sys
    
    # Check for API key
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY not found in environment")
        print("Please create a .env file with your API key:")
        print("  GROQ_API_KEY=gsk_xxxx")
        sys.exit(1)
    
    # Check if index exists
    from search.vector_store import get_collection_stats
    stats = get_collection_stats()
    
    if stats["total_documents"] == 0:
        print("No documents in collection. Please run ingestion first:")
        print("  python -m ingestion.build_index sample 5")
        sys.exit(1)
    
    print("="*80)
    print("WHO RAG SYSTEM - Answer Generation Test")
    print("="*80)
    print(f"Collection: {stats['total_documents']} documents")
    print()
    
    # Test questions
    test_questions = [
        "What is COVID-19?",
        "How is malaria transmitted?",
        "What are the symptoms of tuberculosis?",
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*80}")
        print(f"Question {i}: {question}")
        print('='*80)
        
        try:
            result = answer_question(
                question,
                top_k=3,
                search_method="hybrid"
            )
            
            print(f"\nAnswer:\n{result['answer']}")
            
            print(f"\n\nSources:")
            for source in result['sources']:
                print(f"  [{source['number']}] {source['title']}")
                print(f"      {source['url']}")
                print(f"      Score: {source['score']:.4f}")
            
            print(f"\n\nUsage:")
            print(f"  Prompt tokens: {result['usage']['prompt_tokens']}")
            print(f"  Completion tokens: {result['usage']['completion_tokens']}")
            print(f"  Total tokens: {result['usage']['total_tokens']}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

