"""
Ingestion orchestrator for building the WHO document index.
Coordinates: crawl → extract → chunk → embed → store
"""
import asyncio
import json
from typing import List, Dict, Optional
from pathlib import Path
import config
from crawler.sitemap import get_sitemap_urls
from crawler.fetch import fetch_all
from crawler.extract import extract_batch
from ingestion.chunk import chunk_batch, get_chunk_stats, filter_chunks_by_length
from ingestion.embed import embed_batch_chunks
from search.vector_store import upsert_chunks, get_collection_stats, get_collection


def save_pages_to_jsonl(pages: Dict[str, Dict], filepath: Path = config.PAGES_JSONL) -> None:
    """
    Save extracted pages to JSONL file for caching.
    
    Args:
        pages: Dictionary mapping URLs to page data
        filepath: Path to JSONL file
    """
    print(f"\nSaving {len(pages)} pages to {filepath}...")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        for url, page_data in pages.items():
            f.write(json.dumps(page_data, ensure_ascii=False) + '\n')
    
    print(f"Saved to {filepath}")


def load_pages_from_jsonl(filepath: Path = config.PAGES_JSONL) -> List[Dict]:
    """
    Load previously extracted pages from JSONL file.
    
    Args:
        filepath: Path to JSONL file
        
    Returns:
        List of page data dictionaries
    """
    if not filepath.exists():
        print(f"No cached pages found at {filepath}")
        return []
    
    pages = []
    print(f"Loading pages from {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                pages.append(json.loads(line))
    
    print(f"Loaded {len(pages)} pages from cache")
    return pages


async def crawl_and_extract(
    urls: Optional[List[str]] = None,
    use_cache: bool = True,
    sample_size: Optional[int] = None
) -> List[Dict]:
    """
    Crawl URLs and extract clean text.
    
    Args:
        urls: List of URLs to crawl (if None, discovers from sitemap)
        use_cache: Whether to use cached HTML
        sample_size: If set, only process first N URLs (for testing)
        
    Returns:
        List of extracted page data dictionaries
    """
    # Discover URLs from sitemap if not provided
    if urls is None:
        print("Discovering URLs from sitemap...")
        urls = get_sitemap_urls()
        print(f"Found {len(urls)} URLs")
    
    # Limit to sample size if specified
    if sample_size and sample_size < len(urls):
        print(f"Limiting to sample of {sample_size} URLs")
        urls = urls[:sample_size]
    
    # Fetch HTML
    print("\n" + "="*80)
    print("STEP 1: Fetching HTML")
    print("="*80)
    html_map = await fetch_all(urls, use_cache=use_cache)
    
    # Extract text
    print("\n" + "="*80)
    print("STEP 2: Extracting clean text")
    print("="*80)
    pages = extract_batch(html_map)
    
    # Convert to list
    pages_list = list(pages.values())
    
    return pages_list


def process_and_index(
    pages: List[Dict],
    save_pages: bool = True,
    min_chunk_length: int = 50
) -> None:
    """
    Process pages into chunks, generate embeddings, and index them.
    
    Args:
        pages: List of page data dictionaries
        save_pages: Whether to save pages to JSONL cache
        min_chunk_length: Minimum chunk length to keep
    """
    if not pages:
        print("No pages to process")
        return
    
    # Save pages to cache
    if save_pages:
        pages_dict = {page['url']: page for page in pages}
        save_pages_to_jsonl(pages_dict)
    
    # Chunk the pages
    print("\n" + "="*80)
    print("STEP 3: Chunking documents")
    print("="*80)
    chunks = chunk_batch(pages)
    
    # Filter short chunks
    chunks = filter_chunks_by_length(chunks, min_length=min_chunk_length)
    
    # Show chunk statistics
    stats = get_chunk_stats(chunks)
    print("\nChunk statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.1f}")
        else:
            print(f"  {key}: {value}")
    
    # Generate embeddings
    print("\n" + "="*80)
    print("STEP 4: Generating embeddings")
    print("="*80)
    embeddings = embed_batch_chunks(chunks, show_progress=True)
    
    # Store in vector database
    print("\n" + "="*80)
    print("STEP 5: Storing in vector database")
    print("="*80)
    upsert_chunks(chunks, embeddings)
    
    # Show final statistics
    print("\n" + "="*80)
    print("INDEXING COMPLETE")
    print("="*80)
    final_stats = get_collection_stats()
    print("\nFinal collection statistics:")
    for key, value in final_stats.items():
        if key != "sample_metadata":
            print(f"  {key}: {value}")


async def build_index_from_scratch(
    reset_collection: bool = True,
    sample_size: Optional[int] = None,
    use_cache: bool = True
) -> None:
    """
    Build the entire index from scratch.
    
    Args:
        reset_collection: If True, clear existing collection before indexing
        sample_size: If set, only process first N URLs (for testing)
        use_cache: Whether to use cached HTML
    """
    print("="*80)
    print("WHO RAG SYSTEM - INDEX BUILDER")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  Sitemap: {config.WHO_SITEMAP_URL}")
    print(f"  Sections: {config.URL_FILTERS}")
    print(f"  Chunk size: {config.CHUNK_SIZE}")
    print(f"  Embedding model: {config.EMBEDDING_MODEL}")
    print(f"  Reset collection: {reset_collection}")
    print(f"  Sample size: {sample_size or 'ALL'}")
    print(f"  Use cache: {use_cache}")
    
    # Reset collection if requested
    if reset_collection:
        print("\nResetting vector database...")
        get_collection(reset=True)
    
    # Crawl and extract
    pages = await crawl_and_extract(
        urls=None,
        use_cache=use_cache,
        sample_size=sample_size
    )
    
    # Process and index
    process_and_index(pages, save_pages=True)
    
    print("\n" + "="*80)
    print("INDEX BUILD COMPLETE!")
    print("="*80)


async def build_index_from_cache() -> None:
    """
    Build index from previously cached pages (skip crawling).
    Useful for re-indexing with different chunk/embedding settings.
    """
    print("Building index from cached pages...")
    
    pages = load_pages_from_jsonl()
    
    if not pages:
        print("No cached pages found. Run build_index_from_scratch first.")
        return
    
    process_and_index(pages, save_pages=False)
    
    print("\nIndex build from cache complete!")


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "sample":
            # Build index from small sample for testing
            sample_size = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            print(f"Building index from sample of {sample_size} pages...")
            asyncio.run(build_index_from_scratch(
                reset_collection=True,
                sample_size=sample_size,
                use_cache=True
            ))
        
        elif command == "cache":
            # Build from cached pages
            asyncio.run(build_index_from_cache())
        
        elif command == "full":
            # Build full index
            print("Building FULL index (this may take a while)...")
            asyncio.run(build_index_from_scratch(
                reset_collection=True,
                sample_size=None,
                use_cache=True
            ))
        
        else:
            print(f"Unknown command: {command}")
            print("Usage: python -m ingestion.build_index [sample N | cache | full]")
            sys.exit(1)
    
    else:
        # Default: build from small sample
        print("No command specified. Building sample index...")
        print("Usage: python -m ingestion.build_index [sample N | cache | full]")
        print("\nBuilding sample of 5 pages...")
        asyncio.run(build_index_from_scratch(
            reset_collection=True,
            sample_size=5,
            use_cache=True
        ))
