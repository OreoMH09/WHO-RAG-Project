"""
Vector store wrapper for ChromaDB.
Handles persistent storage and retrieval of document embeddings.
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import config


# Global client and collection instances
_client = None
_collection = None


def get_client():
    """
    Get or create the ChromaDB client (singleton pattern).
    
    Returns:
        ChromaDB client
    """
    global _client
    if _client is None:
        print(f"Initializing ChromaDB at: {config.CHROMA_DB_DIR}")
        # ChromaDB 0.3.x uses Client, not PersistentClient
        _client = chromadb.Client(
            Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(config.CHROMA_DB_DIR),
                anonymized_telemetry=False,
            )
        )
    return _client


def get_collection(reset: bool = False) -> chromadb.Collection:
    """
    Get or create the document collection.
    
    Args:
        reset: If True, delete and recreate the collection (WARNING: deletes all data!)
        
    Returns:
        ChromaDB collection
    """
    global _collection
    client = get_client()
    
    if reset:
        print(f"Resetting collection: {config.CHROMA_COLLECTION_NAME}")
        try:
            client.delete_collection(name=config.CHROMA_COLLECTION_NAME)
            print("Collection deleted")
        except Exception as e:
            print(f"No existing collection to delete: {e}")
        _collection = None
    
    if _collection is None:
        print(f"Loading collection: {config.CHROMA_COLLECTION_NAME}")
        _collection = client.get_or_create_collection(
            name=config.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": config.DISTANCE_METRIC}
        )
        count = _collection.count()
        print(f"Collection loaded. Document count: {count}")
    
    return _collection


def upsert_chunks(
    chunks: List[Dict[str, any]],
    embeddings: List[List[float]]
) -> None:
    """
    Insert or update chunks in the vector store.
    
    Args:
        chunks: List of chunk dictionaries with 'id', 'text', and 'metadata'
        embeddings: List of embedding vectors corresponding to chunks
    """
    if not chunks or not embeddings:
        print("No chunks to upsert")
        return
    
    if len(chunks) != len(embeddings):
        raise ValueError(f"Mismatch: {len(chunks)} chunks but {len(embeddings)} embeddings")
    
    collection = get_collection()
    
    print(f"Upserting {len(chunks)} chunks to vector store...")
    
    # Extract data for ChromaDB
    ids = [chunk["id"] for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    
    # Upsert in batches to avoid memory issues
    batch_size = 1000
    for i in range(0, len(chunks), batch_size):
        end_idx = min(i + batch_size, len(chunks))
        collection.upsert(
            ids=ids[i:end_idx],
            embeddings=embeddings[i:end_idx],
            documents=documents[i:end_idx],
            metadatas=metadatas[i:end_idx],
        )
        print(f"Upserted batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}")
    
    print(f"Successfully upserted {len(chunks)} chunks")
    print(f"Total documents in collection: {collection.count()}")


def query_vectors(
    query_embedding: List[float],
    top_k: int = config.DEFAULT_TOP_K,
    where: Optional[Dict] = None,
    where_document: Optional[Dict] = None
) -> Dict[str, any]:
    """
    Query the vector store with an embedding.
    
    Args:
        query_embedding: Query embedding vector
        top_k: Number of results to return
        where: Metadata filter (e.g. {"language": "en"})
        where_document: Document content filter (e.g. {"$contains": "malaria"})
        
    Returns:
        Dictionary with 'ids', 'documents', 'metadatas', and 'distances'
    """
    collection = get_collection()
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
        where_document=where_document,
    )
    
    return results


def get_by_ids(ids: List[str]) -> Dict[str, any]:
    """
    Retrieve specific documents by their IDs.
    
    Args:
        ids: List of document IDs
        
    Returns:
        Dictionary with 'ids', 'documents', 'metadatas', and 'embeddings'
    """
    collection = get_collection()
    return collection.get(ids=ids)


def delete_by_ids(ids: List[str]) -> None:
    """
    Delete specific documents by their IDs.
    
    Args:
        ids: List of document IDs to delete
    """
    collection = get_collection()
    collection.delete(ids=ids)
    print(f"Deleted {len(ids)} documents")


def get_collection_stats() -> Dict[str, any]:
    """
    Get statistics about the collection.
    
    Returns:
        Dictionary with collection statistics
    """
    collection = get_collection()
    count = collection.count()
    
    # Sample a few documents to show metadata structure
    sample = collection.get(limit=5) if count > 0 else {"metadatas": []}
    
    stats = {
        "name": config.CHROMA_COLLECTION_NAME,
        "total_documents": count,
        "distance_metric": config.DISTANCE_METRIC,
        "sample_metadata": sample["metadatas"][:3] if sample["metadatas"] else [],
    }
    
    return stats


def search_by_url(url: str) -> Dict[str, any]:
    """
    Find all chunks from a specific URL.
    
    Args:
        url: The URL to search for
        
    Returns:
        Dictionary with matching documents
    """
    collection = get_collection()
    results = collection.get(where={"url": url})
    return results


if __name__ == "__main__":
    # Test the vector store
    print("Testing ChromaDB vector store...")
    print("="*80)
    
    # Create test data
    test_chunks = [
        {
            "id": "test1",
            "text": "The World Health Organization is a specialized agency.",
            "metadata": {"url": "https://test.com/1", "title": "Test 1", "chunk_index": 0}
        },
        {
            "id": "test2",
            "text": "COVID-19 is caused by SARS-CoV-2 virus.",
            "metadata": {"url": "https://test.com/2", "title": "Test 2", "chunk_index": 0}
        },
        {
            "id": "test3",
            "text": "Malaria is transmitted by mosquitoes.",
            "metadata": {"url": "https://test.com/3", "title": "Test 3", "chunk_index": 0}
        },
    ]
    
    # Generate dummy embeddings (in real use, these come from embed.py)
    import numpy as np
    test_embeddings = [np.random.rand(768).tolist() for _ in test_chunks]
    
    print("\n1. Resetting collection...")
    get_collection(reset=True)
    
    print("\n2. Upserting test chunks...")
    upsert_chunks(test_chunks, test_embeddings)
    
    print("\n3. Collection statistics:")
    stats = get_collection_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n4. Querying with test embedding...")
    query_emb = np.random.rand(768).tolist()
    results = query_vectors(query_emb, top_k=2)
    
    print(f"Found {len(results['ids'][0])} results:")
    for i, (doc_id, doc, meta, dist) in enumerate(zip(
        results['ids'][0],
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    )):
        print(f"\nResult {i+1}:")
        print(f"  ID: {doc_id}")
        print(f"  Text: {doc[:60]}...")
        print(f"  Metadata: {meta}")
        print(f"  Distance: {dist:.4f}")
    
    print("\n5. Searching by URL...")
    url_results = search_by_url("https://test.com/1")
    print(f"Found {len(url_results['ids'])} chunks from URL")
    
    print("\n6. Retrieving by ID...")
    by_id = get_by_ids(["test1"])
    print(f"Retrieved: {by_id['documents'][0][:60]}...")
    
    print("\nTest complete!")
