"""
Text chunking for optimal embedding and retrieval.
Uses recursive character splitting with overlap to maintain context.
"""
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
import config


# Initialize the text splitter with configured parameters
splitter = RecursiveCharacterTextSplitter(
    chunk_size=config.CHUNK_SIZE,
    chunk_overlap=config.CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""],
    length_function=len,
    is_separator_regex=False,
)


def chunk_page(page_data: Dict[str, any]) -> List[Dict[str, any]]:
    """
    Split a page's text into chunks with metadata.
    
    Args:
        page_data: Dictionary containing 'text', 'url', 'title', and other metadata
        
    Returns:
        List of chunk dictionaries, each with:
        - id: unique identifier (url::chunk{index})
        - text: chunk content
        - metadata: url, title, chunk_index, and source metadata
    """
    text = page_data.get("text", "")
    url = page_data.get("url", "")
    
    if not text:
        return []
    
    # Split the text into chunks
    chunks_text = splitter.split_text(text)
    
    # Create chunk dictionaries with metadata
    chunks = []
    for i, chunk_text in enumerate(chunks_text):
        chunk = {
            "id": f"{url}::chunk{i}",
            "text": chunk_text,
            "metadata": {
                "url": url,
                "title": page_data.get("title", ""),
                "chunk_index": i,
                "total_chunks": len(chunks_text),
                "date": page_data.get("date", ""),
                "language": page_data.get("language", "en"),
                "sitename": page_data.get("sitename", "WHO"),
            }
        }
        chunks.append(chunk)
    
    return chunks


def chunk_batch(pages: List[Dict[str, any]]) -> List[Dict[str, any]]:
    """
    Chunk a batch of pages.
    
    Args:
        pages: List of page data dictionaries
        
    Returns:
        Flat list of all chunks from all pages
    """
    all_chunks = []
    
    print(f"Chunking {len(pages)} pages...")
    
    for page_data in pages:
        chunks = chunk_page(page_data)
        all_chunks.extend(chunks)
    
    print(f"Created {len(all_chunks)} chunks from {len(pages)} pages")
    print(f"Average chunks per page: {len(all_chunks) / len(pages):.1f}")
    
    return all_chunks


def get_chunk_stats(chunks: List[Dict[str, any]]) -> Dict[str, any]:
    """
    Calculate statistics about chunks.
    
    Args:
        chunks: List of chunk dictionaries
        
    Returns:
        Dictionary with statistics
    """
    if not chunks:
        return {
            "total_chunks": 0,
            "avg_length": 0,
            "min_length": 0,
            "max_length": 0,
            "total_chars": 0,
        }
    
    lengths = [len(chunk["text"]) for chunk in chunks]
    
    return {
        "total_chunks": len(chunks),
        "avg_length": sum(lengths) / len(lengths),
        "min_length": min(lengths),
        "max_length": max(lengths),
        "total_chars": sum(lengths),
    }


def filter_chunks_by_length(
    chunks: List[Dict[str, any]], 
    min_length: int = 50,
    max_length: int = None
) -> List[Dict[str, any]]:
    """
    Filter out chunks that are too short or too long.
    
    Args:
        chunks: List of chunk dictionaries
        min_length: Minimum character length
        max_length: Maximum character length (None for no limit)
        
    Returns:
        Filtered list of chunks
    """
    filtered = []
    
    for chunk in chunks:
        text_len = len(chunk["text"])
        if text_len < min_length:
            continue
        if max_length and text_len > max_length:
            continue
        filtered.append(chunk)
    
    removed = len(chunks) - len(filtered)
    if removed > 0:
        print(f"Filtered out {removed} chunks (too short or too long)")
    
    return filtered


if __name__ == "__main__":
    # Test chunking
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    # Create a sample page
    sample_page = {
        "url": "https://www.who.int/test",
        "title": "Test Page",
        "text": """
        The World Health Organization (WHO) is a specialized agency of the United Nations 
        responsible for international public health.
        
        The WHO was established on 7 April 1948. Headquartered in Geneva, Switzerland, 
        it has six regional offices and 150 field offices worldwide.
        
        The WHO's broad mandate includes advocating for universal healthcare, monitoring 
        public health risks, coordinating responses to health emergencies, and promoting 
        human health and well-being.
        
        The organization has played a leading role in several public health achievements, 
        most notably the eradication of smallpox, the near-eradication of polio, and the 
        development of an Ebola vaccine.
        
        Its current priorities include communicable diseases, particularly HIV/AIDS, 
        Ebola, COVID-19, malaria and tuberculosis; non-communicable diseases such as 
        heart disease and cancer; healthy diet, nutrition, and food security; occupational 
        health; and substance abuse.
        """ * 5,  # Repeat to make it longer
        "date": "2024-01-15",
        "language": "en",
        "sitename": "WHO"
    }
    
    print("Testing text chunking...")
    print(f"Original text length: {len(sample_page['text'])} characters")
    print(f"Chunk size: {config.CHUNK_SIZE}, Overlap: {config.CHUNK_OVERLAP}")
    print("="*80)
    
    # Chunk the page
    chunks = chunk_page(sample_page)
    
    print(f"\nCreated {len(chunks)} chunks")
    print("\nChunk statistics:")
    stats = get_chunk_stats(chunks)
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.1f}")
        else:
            print(f"  {key}: {value}")
    
    # Display first few chunks
    print("\n" + "="*80)
    print("First 3 chunks:")
    print("="*80)
    
    for i, chunk in enumerate(chunks[:3]):
        print(f"\nChunk {i} (ID: {chunk['id']}):")
        print(f"Length: {len(chunk['text'])} characters")
        print(f"Metadata: {chunk['metadata']}")
        print(f"Text preview:\n{chunk['text'][:200]}...")
        print("-"*80)
