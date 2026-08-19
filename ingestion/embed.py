"""
Embedding generation using sentence-transformers.
Handles both passage encoding and query encoding with appropriate prefixes.
"""
from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np
import config


# Global model instance (loaded once)
_model = None


def get_model() -> SentenceTransformer:
    """
    Get or load the embedding model (singleton pattern).
    
    Returns:
        SentenceTransformer model instance
    """
    global _model
    if _model is None:
        print(f"Loading embedding model: {config.EMBEDDING_MODEL}")
        _model = SentenceTransformer(config.EMBEDDING_MODEL)
        print(f"Model loaded. Embedding dimension: {_model.get_sentence_embedding_dimension()}")
    return _model


def embed_texts(texts: List[str], show_progress: bool = True) -> List[List[float]]:
    """
    Generate embeddings for a list of passages/documents.
    
    Args:
        texts: List of text strings to embed
        show_progress: Whether to show progress bar
        
    Returns:
        List of embedding vectors (each vector is a list of floats)
    """
    if not texts:
        return []
    
    model = get_model()
    
    print(f"Generating embeddings for {len(texts)} texts...")
    
    # For BGE models, passages don't need a prefix
    # Only queries need the special prefix
    embeddings = model.encode(
        texts,
        normalize_embeddings=config.NORMALIZE_EMBEDDINGS,
        batch_size=config.EMBEDDING_BATCH_SIZE,
        show_progress_bar=show_progress,
        convert_to_numpy=True,
    )
    
    # Convert to list of lists for JSON serialization
    embeddings_list = embeddings.tolist()
    
    print(f"Generated {len(embeddings_list)} embeddings")
    
    return embeddings_list


def embed_query(query: str) -> List[float]:
    """
    Generate embedding for a search query.
    Uses a special prefix for BGE models to optimize retrieval.
    
    Args:
        query: Query string
        
    Returns:
        Embedding vector as list of floats
    """
    model = get_model()
    
    # BGE models benefit from this prefix for queries
    # See: https://huggingface.co/BAAI/bge-base-en-v1.5
    if "bge" in config.EMBEDDING_MODEL.lower():
        prefixed_query = f"Represent this sentence for searching relevant passages: {query}"
    else:
        prefixed_query = query
    
    embedding = model.encode(
        [prefixed_query],
        normalize_embeddings=config.NORMALIZE_EMBEDDINGS,
        convert_to_numpy=True,
    )
    
    return embedding[0].tolist()


def embed_batch_chunks(chunks: List[dict], show_progress: bool = True) -> List[List[float]]:
    """
    Generate embeddings for a batch of chunks.
    
    Args:
        chunks: List of chunk dictionaries (each with 'text' field)
        show_progress: Whether to show progress bar
        
    Returns:
        List of embedding vectors
    """
    texts = [chunk["text"] for chunk in chunks]
    return embed_texts(texts, show_progress=show_progress)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    Assumes vectors are already normalized if config.NORMALIZE_EMBEDDINGS is True.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score (0 to 1 for normalized vectors)
    """
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)
    
    if config.NORMALIZE_EMBEDDINGS:
        # If vectors are normalized, dot product = cosine similarity
        return float(np.dot(vec1_np, vec2_np))
    else:
        # Calculate cosine similarity manually
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        return float(dot_product / (norm1 * norm2))


if __name__ == "__main__":
    # Test embeddings
    print("Testing embedding generation...")
    print("="*80)
    
    # Test passages
    test_passages = [
        "The World Health Organization is a specialized agency of the United Nations.",
        "COVID-19 is caused by the SARS-CoV-2 virus.",
        "Malaria is transmitted by mosquitoes and is preventable.",
    ]
    
    print("\nGenerating passage embeddings...")
    passage_embeddings = embed_texts(test_passages, show_progress=True)
    
    print(f"\nEmbedding dimension: {len(passage_embeddings[0])}")
    print(f"First embedding preview: {passage_embeddings[0][:5]}...")
    
    # Test query
    test_query = "What is malaria?"
    print(f"\nGenerating query embedding for: '{test_query}'")
    query_embedding = embed_query(test_query)
    
    print(f"Query embedding dimension: {len(query_embedding)}")
    print(f"Query embedding preview: {query_embedding[:5]}...")
    
    # Test similarity
    print("\n" + "="*80)
    print("Testing cosine similarity with query...")
    print("="*80)
    
    for i, passage in enumerate(test_passages):
        sim = cosine_similarity(query_embedding, passage_embeddings[i])
        print(f"\nPassage {i+1}: {passage[:60]}...")
        print(f"Similarity: {sim:.4f}")
    
    # Test batch chunk embedding
    print("\n" + "="*80)
    print("Testing batch chunk embedding...")
    print("="*80)
    
    test_chunks = [
        {"id": "1", "text": test_passages[0], "metadata": {}},
        {"id": "2", "text": test_passages[1], "metadata": {}},
        {"id": "3", "text": test_passages[2], "metadata": {}},
    ]
    
    chunk_embeddings = embed_batch_chunks(test_chunks, show_progress=True)
    print(f"\nGenerated {len(chunk_embeddings)} chunk embeddings")
