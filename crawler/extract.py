"""
Text extraction and cleaning using trafilatura.
Strips navigation, footers, and boilerplate from HTML.
"""
import trafilatura
from typing import Dict, Optional
from datetime import datetime
import config


def extract_clean_text(html: str, url: str) -> Optional[Dict[str, any]]:
    """
    Extract clean text and metadata from HTML.
    
    Args:
        html: Raw HTML content
        url: Source URL (for metadata)
        
    Returns:
        Dictionary with url, title, text, date, and other metadata, or None if extraction fails
    """
    # Extract main content text
    text = trafilatura.extract(
        html,
        include_tables=True,  # Include tables (useful for health data)
        include_links=False,  # Don't include link markup
        include_images=False,  # Don't include image markup
        include_formatting=False,  # Plain text output
        no_fallback=False,  # Allow fallback extraction methods
    )
    
    # Validate text quality
    if not text:
        return None
    
    if len(text) < config.MIN_TEXT_LENGTH:
        return None
    
    # Extract metadata
    metadata = trafilatura.extract_metadata(html)
    
    # Build result dictionary
    result = {
        "url": url,
        "text": text.strip(),
        "text_length": len(text),
    }
    
    # Add metadata fields if available
    if metadata:
        result["title"] = metadata.title or ""
        result["author"] = metadata.author or ""
        result["date"] = metadata.date or ""
        result["description"] = metadata.description or ""
        result["sitename"] = metadata.sitename or "WHO"
        result["language"] = metadata.language or "en"
    else:
        result["title"] = ""
        result["author"] = ""
        result["date"] = ""
        result["description"] = ""
        result["sitename"] = "WHO"
        result["language"] = "en"
    
    # Add extraction timestamp
    result["extracted_at"] = datetime.now().isoformat()
    
    return result


def extract_batch(html_map: Dict[str, str]) -> Dict[str, Dict]:
    """
    Extract clean text from a batch of HTML documents.
    
    Args:
        html_map: Dictionary mapping URLs to HTML content
        
    Returns:
        Dictionary mapping URLs to extracted page data (only successful extractions)
    """
    results = {}
    successful = 0
    failed = 0
    
    print(f"Extracting text from {len(html_map)} pages...")
    
    for url, html in html_map.items():
        page_data = extract_clean_text(html, url)
        if page_data:
            results[url] = page_data
            successful += 1
        else:
            failed += 1
            print(f"Failed to extract text from: {url}")
    
    print(f"Successfully extracted {successful}/{len(html_map)} pages")
    if failed > 0:
        print(f"Failed extractions: {failed}")
    
    return results


def get_text_stats(page_data: Dict[str, any]) -> str:
    """
    Get readable statistics about extracted text.
    
    Args:
        page_data: Extracted page data dictionary
        
    Returns:
        Formatted statistics string
    """
    text = page_data.get("text", "")
    words = len(text.split())
    lines = len(text.splitlines())
    
    stats = [
        f"URL: {page_data.get('url', 'N/A')}",
        f"Title: {page_data.get('title', 'N/A')}",
        f"Date: {page_data.get('date', 'N/A')}",
        f"Length: {page_data.get('text_length', 0)} chars",
        f"Words: {words}",
        f"Lines: {lines}",
        f"Language: {page_data.get('language', 'N/A')}",
    ]
    
    return "\n".join(stats)


if __name__ == "__main__":
    # Test the text extraction
    import asyncio
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from crawler.sitemap import get_sitemap_urls
    from crawler.fetch import fetch_sample
    
    print("Testing text extraction...")
    
    # Get some URLs and fetch them
    urls = get_sitemap_urls()
    if not urls:
        print("No URLs found")
        sys.exit(1)
    
    html_map = asyncio.run(fetch_sample(urls, sample_size=3))
    
    if not html_map:
        print("No pages fetched")
        sys.exit(1)
    
    # Extract text from fetched pages
    print("\n" + "="*80)
    print("Extracting text...")
    print("="*80)
    
    results = extract_batch(html_map)
    
    # Display results
    for url, page_data in results.items():
        print("\n" + "-"*80)
        print(get_text_stats(page_data))
        print("-"*80)
        print("\nText preview (first 500 chars):")
        print(page_data["text"][:500])
        print("...")
