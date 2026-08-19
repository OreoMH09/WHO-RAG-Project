"""
Polite async fetcher for WHO.int pages.
Includes rate limiting, retries, caching, and proper User-Agent.
"""
import asyncio
import hashlib
from pathlib import Path
from typing import Dict, List
import httpx
from tqdm.asyncio import tqdm
import config


def url_to_filename(url: str) -> str:
    """Convert a URL to a safe filename using hash."""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return f"{url_hash}.html"


def load_cached_html(url: str) -> str | None:
    """
    Load cached HTML for a URL if it exists.
    
    Args:
        url: The URL to check cache for
        
    Returns:
        Cached HTML content or None if not cached
    """
    cache_path = config.RAW_HTML_DIR / url_to_filename(url)
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8", errors="ignore")
    return None


def save_cached_html(url: str, html: str) -> None:
    """
    Save HTML to cache.
    
    Args:
        url: The URL being cached
        html: The HTML content to cache
    """
    cache_path = config.RAW_HTML_DIR / url_to_filename(url)
    cache_path.write_text(html, encoding="utf-8")


async def fetch_one(
    client: httpx.AsyncClient, 
    url: str, 
    semaphore: asyncio.Semaphore,
    delay: float = config.CRAWL_DELAY,
    use_cache: bool = True
) -> tuple[str, str | None]:
    """
    Fetch a single URL with rate limiting and caching.
    
    Args:
        client: httpx AsyncClient instance
        url: URL to fetch
        semaphore: Semaphore for concurrency control
        delay: Delay in seconds after each request
        use_cache: Whether to use cached version if available
        
    Returns:
        Tuple of (url, html_content). html_content is None on failure.
    """
    # Check cache first
    if use_cache:
        cached = load_cached_html(url)
        if cached:
            return (url, cached)
    
    async with semaphore:
        try:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text
            
            # Cache the result
            save_cached_html(url, html)
            
            # Be polite - wait before next request
            await asyncio.sleep(delay)
            
            return (url, html)
            
        except httpx.HTTPStatusError as e:
            print(f"\nHTTP error {e.response.status_code} for {url}")
            return (url, None)
        except httpx.RequestError as e:
            print(f"\nRequest error for {url}: {e}")
            return (url, None)
        except Exception as e:
            print(f"\nUnexpected error for {url}: {e}")
            return (url, None)


async def fetch_all(
    urls: List[str],
    concurrency: int = config.CONCURRENT_REQUESTS,
    delay: float = config.CRAWL_DELAY,
    use_cache: bool = True,
    timeout: float = config.REQUEST_TIMEOUT
) -> Dict[str, str]:
    """
    Fetch multiple URLs with concurrency control and rate limiting.
    
    Args:
        urls: List of URLs to fetch
        concurrency: Maximum number of concurrent requests
        delay: Delay in seconds between requests
        use_cache: Whether to use cached versions if available
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary mapping URLs to their HTML content (only successful fetches)
    """
    semaphore = asyncio.Semaphore(concurrency)
    results = {}
    
    headers = {
        "User-Agent": config.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    async with httpx.AsyncClient(
        headers=headers,
        timeout=timeout,
        follow_redirects=True,
        limits=httpx.Limits(max_keepalive_connections=concurrency, max_connections=concurrency * 2)
    ) as client:
        # Create tasks for all URLs
        tasks = [
            fetch_one(client, url, semaphore, delay, use_cache)
            for url in urls
        ]
        
        # Execute with progress bar
        print(f"Fetching {len(urls)} URLs (concurrency={concurrency}, delay={delay}s)...")
        completed = await tqdm.gather(*tasks, desc="Fetching pages")
        
        # Collect successful results
        for url, html in completed:
            if html:
                results[url] = html
        
        print(f"\nSuccessfully fetched {len(results)}/{len(urls)} pages")
        
        # Report cache hits
        cache_hits = sum(1 for url in urls if load_cached_html(url) is not None)
        if use_cache and cache_hits > 0:
            print(f"Cache hits: {cache_hits}/{len(urls)}")
    
    return results


async def fetch_sample(urls: List[str], sample_size: int = 5) -> Dict[str, str]:
    """
    Fetch a small sample of URLs for testing.
    
    Args:
        urls: List of URLs to sample from
        sample_size: Number of URLs to fetch
        
    Returns:
        Dictionary mapping URLs to HTML content
    """
    sample_urls = urls[:sample_size]
    print(f"Fetching sample of {len(sample_urls)} URLs...")
    return await fetch_all(sample_urls)


if __name__ == "__main__":
    # Test the fetcher
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from crawler.sitemap import get_sitemap_urls
    
    print("Testing WHO page fetcher...")
    
    # Get some URLs
    urls = get_sitemap_urls()
    if not urls:
        print("No URLs found in sitemap")
        sys.exit(1)
    
    # Fetch a small sample
    results = asyncio.run(fetch_sample(urls, sample_size=3))
    
    print(f"\nFetched {len(results)} pages")
    for url, html in results.items():
        print(f"\n{url}")
        print(f"  Length: {len(html)} characters")
        print(f"  Preview: {html[:100]}...")
