"""
Hybrid search combining vector similarity and BM25 keyword matching.
Provides better recall on exact terms while maintaining semantic understanding.
"""
from typing import List, Dict, Optional
from rank_bm25 import BM25Okapi
import numpy as np
from ingestion.embed import embed_query
from search.vector_store import query_vectors, get_collection
import config


# Global BM25 index
_bm25_index = None
_bm25_documents = None
_bm25_metadata = None


def build_bm25_index() -> None:
    """
    Build BM25 index from all documents in the vector store.
    Call this once after indexing documents or when collection changes.
    """
    global _bm25_index, _bm25_documents, _bm25_metadata
    
    print("Building BM25 index from vector store...")
    collection = get_collection()
    
    # Get all documents
    all_docs = collection.get()
    
    if not all_docs['documents']:
        print("No documents in collection. BM25 index not built.")
        return
    
    # Tokenize documents for BM25
    tokenized_docs = [doc.lower().split() for doc in all_docs['documents']]
    
    # Build BM25 index
    _bm25_index = BM25Okapi(tokenized_docs)
    _bm25_documents = all_docs['documents']
    _bm25_metadata = all_docs['metadatas']
    
    print(f"BM25 index built with {len(_bm25_documents)} documents")


def get_bm25_index():
    """Get or build the BM25 index (lazy loading)."""
    global _bm25_index
    if _bm25_index is None:
        build_bm25_index()
    return _bm25_index


def bm25_search(query: str, top_k: int = config.DEFAULT_TOP_K) -> List[Dict]:
    """
    Search using BM25 keyword matching.
    
    Args:
        query: Search query
        top_k: Number of results to return
        
    Returns:
        List of result dictionaries with text, metadata, and score
    """
    bm25 = get_bm25_index()
    
    if bm25 is None:
        print("BM25 index not available")
        return []
    
    # Tokenize query
    tokenized_query = query.lower().split()
    
    # Get BM25 scores
    scores = bm25.get_scores(tokenized_query)
    
    # Get top-k indices
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    # Build results
    results = []
    for idx in top_indices:
        if scores[idx] > 0:  # Only return documents with positive scores
            results.append({
                "text": _bm25_documents[idx],
                "metadata": _bm25_metadata[idx],
                "score": float(scores[idx]),
                "source": "bm25"
            })
    
    return results


def vector_search(query: str, top_k: int = config.DEFAULT_TOP_K) -> List[Dict]:
    """
    Search using vector similarity.
    
    Args:
        query: Search query
        top_k: Number of results to return
        
    Returns:
        List of result dictionaries with text, metadata, and score
    """
    # Generate query embedding
    query_embedding = embed_query(query)
    
    # Query vector store
    results = query_vectors(query_embedding, top_k=top_k)
    
    # Format results
    formatted_results = []
    for doc, meta, dist in zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    ):
        # Convert distance to similarity score (assuming cosine distance)
        # ChromaDB returns distance, we want similarity (1 - distance for cosine)
        score = 1.0 - dist
        
        formatted_results.append({
            "text": doc,
            "metadata": meta,
            "score": float(score),
            "source": "vector"
        })
    
    return formatted_results


def normalize_scores(results: List[Dict], score_key: str = "score") -> List[Dict]:
    """
    Normalize scores to 0-1 range using min-max normalization.
    
    Args:
        results: List of result dictionaries
        score_key: Key containing the score value
        
    Returns:
        Results with normalized scores
    """
    if not results:
        return results
    
    scores = [r[score_key] for r in results]
    min_score = min(scores)
    max_score = max(scores)
    
    # Avoid division by zero
    if max_score == min_score:
        for r in results:
            r[f"normalized_{score_key}"] = 1.0
        return results
    
    # Normalize
    for r in results:
        r[f"normalized_{score_key}"] = (r[score_key] - min_score) / (max_score - min_score)
    
    return results


def hybrid_search(
    query: str,
    top_k: int = config.DEFAULT_TOP_K,
    vector_weight: float = config.HYBRID_SEARCH_WEIGHT,
    rerank: bool = True
) -> List[Dict]:
    """
    Hybrid search combining vector similarity and BM25.
    
    Args:
        query: Search query
        top_k: Number of final results to return
        vector_weight: Weight for vector scores (0-1). BM25 weight = 1 - vector_weight
        rerank: Whether to rerank final results by combined score
        
    Returns:
        List of result dictionaries sorted by combined score
    """
    # Get results from both methods (get more than top_k for better fusion)
    retrieval_k = min(top_k * 3, 50)
    
    vector_results = vector_search(query, top_k=retrieval_k)
    bm25_results = bm25_search(query, top_k=retrieval_k)
    
    # Normalize scores
    vector_results = normalize_scores(vector_results, "score")
    bm25_results = normalize_scores(bm25_results, "score")
    
    # Combine results by URL (same document may appear in both)
    combined = {}
    
    # Add vector results
    for result in vector_results:
        url = result["metadata"]["url"]
        chunk_idx = result["metadata"]["chunk_index"]
        key = f"{url}::{chunk_idx}"
        
        combined[key] = {
            "text": result["text"],
            "metadata": result["metadata"],
            "vector_score": result["normalized_score"],
            "bm25_score": 0.0,
        }
    
    # Add BM25 results
    for result in bm25_results:
        url = result["metadata"]["url"]
        chunk_idx = result["metadata"]["chunk_index"]
        key = f"{url}::{chunk_idx}"
        
        if key in combined:
            # Document appeared in both - update BM25 score
            combined[key]["bm25_score"] = result["normalized_score"]
        else:
            # Document only in BM25 results
            combined[key] = {
                "text": result["text"],
                "metadata": result["metadata"],
                "vector_score": 0.0,
                "bm25_score": result["normalized_score"],
            }
    
    # Calculate combined scores
    bm25_weight = 1.0 - vector_weight
    results = []
    
    for key, data in combined.items():
        combined_score = (
            vector_weight * data["vector_score"] +
            bm25_weight * data["bm25_score"]
        )
        
        results.append({
            "text": data["text"],
            "metadata": data["metadata"],
            "score": combined_score,
            "vector_score": data["vector_score"],
            "bm25_score": data["bm25_score"],
            "source": "hybrid"
        })
    
    # Sort by combined score
    if rerank:
        results.sort(key=lambda x: x["score"], reverse=True)
    
    # Return top-k
    return results[:top_k]


def semantic_search(
    query: str,
    top_k: int = config.DEFAULT_TOP_K,
    method: str = "hybrid"
) -> List[Dict]:
    """
    Main search interface. Choose search method.
    
    Args:
        query: Search query
        top_k: Number of results to return
        method: Search method - "vector", "bm25", or "hybrid"
        
    Returns:
        List of result dictionaries with text, metadata, and score
    """
    if method == "vector":
        return vector_search(query, top_k=top_k)
    elif method == "bm25":
        return bm25_search(query, top_k=top_k)
    elif method == "hybrid":
        return hybrid_search(query, top_k=top_k)
    else:
        raise ValueError(f"Unknown search method: {method}. Use 'vector', 'bm25', or 'hybrid'")


if __name__ == "__main__":
    # Test search functionality
    print("Testing semantic search...")
    print("="*80)
    
    # Check if collection has documents
    from search.vector_store import get_collection_stats
    stats = get_collection_stats()
    
    if stats["total_documents"] == 0:
        print("No documents in collection. Please run ingestion first:")
        print("  python -m ingestion.build_index sample 5")
        exit(1)
    
    print(f"Collection has {stats['total_documents']} documents")
    
    # Test queries
    test_queries = [
        "What is COVID-19?",
        "malaria symptoms",
        "WHO headquarters location",
    ]
    
    for query in test_queries:
        print("\n" + "="*80)
        print(f"Query: {query}")
        print("="*80)
        
        # Test different methods
        for method in ["vector", "hybrid"]:
            print(f"\n--- {method.upper()} SEARCH ---")
            results = semantic_search(query, top_k=3, method=method)
            
            for i, result in enumerate(results):
                print(f"\nResult {i+1} (score: {result['score']:.4f}):")
                print(f"  URL: {result['metadata']['url']}")
                print(f"  Title: {result['metadata']['title']}")
                print(f"  Text: {result['text'][:150]}...")
                if "vector_score" in result:
                    print(f"  Vector: {result['vector_score']:.4f}, BM25: {result['bm25_score']:.4f}")
