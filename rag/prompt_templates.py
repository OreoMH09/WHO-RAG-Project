"""
Prompt templates for RAG answer generation.
"""

SYSTEM_PROMPT = """You are a health information assistant answering questions using WHO (World Health Organization) source material.

Key guidelines:
1. Answer ONLY using information from the provided source excerpts
2. ALWAYS cite sources by number (e.g., [1], [2]) in your answer
3. If the excerpts don't contain enough information to answer the question, say so clearly
4. Do not use outside knowledge for medical facts - stick to the sources
5. Be precise and factual - this is health information
6. If sources disagree or are unclear, mention this
7. Keep answers concise but complete

Format your citations inline like this: "COVID-19 is caused by SARS-CoV-2 [1]."
"""


def build_context(results: list[dict]) -> str:
    """
    Build context string from search results.
    
    Args:
        results: List of search result dictionaries with 'text', 'metadata', and 'score'
        
    Returns:
        Formatted context string with numbered sources
    """
    if not results:
        return "No relevant sources found."
    
    context_parts = []
    
    for i, result in enumerate(results, 1):
        metadata = result['metadata']
        title = metadata.get('title', 'Untitled')
        url = metadata.get('url', 'Unknown URL')
        text = result['text']
        
        context_parts.append(
            f"[Source {i}: {title}]\n"
            f"URL: {url}\n"
            f"Content: {text}\n"
        )
    
    return "\n".join(context_parts)


def build_user_prompt(question: str, context: str) -> str:
    """
    Build the user prompt with context and question.
    
    Args:
        question: User's question
        context: Context string from search results
        
    Returns:
        Formatted user prompt
    """
    return f"""Context from WHO sources:

{context}

Question: {question}

Please answer the question using only the information from the sources above. Cite sources using [1], [2], etc."""


def build_messages(question: str, results: list[dict]) -> list[dict]:
    """
    Build complete message list for Claude API.
    
    Args:
        question: User's question
        results: Search results
        
    Returns:
        List of message dictionaries for Claude API
    """
    context = build_context(results)
    user_prompt = build_user_prompt(question, context)
    
    return [
        {
            "role": "user",
            "content": user_prompt
        }
    ]


def extract_sources_from_results(results: list[dict]) -> list[dict]:
    """
    Extract clean source list from search results.
    
    Args:
        results: Search results
        
    Returns:
        List of source dictionaries with title, url, and score
    """
    sources = []
    
    for i, result in enumerate(results, 1):
        metadata = result['metadata']
        sources.append({
            "number": i,
            "title": metadata.get('title', 'Untitled'),
            "url": metadata.get('url', 'Unknown URL'),
            "score": result.get('score', 0.0),
            "date": metadata.get('date', ''),
        })
    
    return sources
