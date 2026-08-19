"""
Sitemap discovery for WHO.int.
Recursively parses sitemap.xml to discover all URLs.
"""
import httpx
from lxml import etree
from typing import List
import gzip
import config


def get_sitemap_urls(sitemap_url: str = config.WHO_SITEMAP_URL, filter_sections: bool = True) -> List[str]:
    """
    Recursively parse WHO sitemap(s) and extract all URLs.
    
    Args:
        sitemap_url: URL to the sitemap (can be a sitemap index or regular sitemap)
        filter_sections: If True, only return URLs matching config.URL_FILTERS
        
    Returns:
        List of discovered URLs
    """
    print(f"Fetching sitemap: {sitemap_url}")
    
    try:
        resp = httpx.get(
            sitemap_url, 
            timeout=config.REQUEST_TIMEOUT,
            headers={"User-Agent": config.USER_AGENT},
            follow_redirects=True
        )
        resp.raise_for_status()
    except httpx.HTTPError as e:
        print(f"Error fetching sitemap {sitemap_url}: {e}")
        return []
    
    # Check if content is gzipped
    content = resp.content
    if sitemap_url.endswith('.gz'):
        try:
            content = gzip.decompress(content)
        except Exception as e:
            print(f"Error decompressing gzipped sitemap: {e}")
            return []
    
    try:
        root = etree.fromstring(content)
    except etree.XMLSyntaxError as e:
        print(f"Error parsing sitemap XML: {e}")
        return []
    
    # Define XML namespace for sitemaps
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    
    # Check if this is a sitemap index (contains other sitemaps)
    sub_sitemaps = root.findall(".//sm:sitemap/sm:loc", ns)
    
    if sub_sitemaps:
        # This is a sitemap index - recursively fetch child sitemaps
        print(f"Found {len(sub_sitemaps)} sub-sitemaps")
        all_urls = []
        for sitemap_loc in sub_sitemaps:
            child_urls = get_sitemap_urls(sitemap_loc.text, filter_sections=False)
            all_urls.extend(child_urls)
        
        # Apply filtering only at the top level
        if filter_sections and config.URL_FILTERS:
            all_urls = [url for url in all_urls if any(filter_str in url for filter_str in config.URL_FILTERS)]
        
        return all_urls
    
    # This is a regular sitemap - extract URLs
    urls = [loc.text for loc in root.findall(".//sm:url/sm:loc", ns)]
    print(f"Found {len(urls)} URLs in sitemap")
    
    return urls


def filter_urls_by_section(urls: List[str], sections: List[str] = None) -> List[str]:
    """
    Filter URLs to only include those matching specified sections.
    
    Args:
        urls: List of URLs to filter
        sections: List of path segments to match (e.g. ["/news/", "/fact-sheets/"])
                 If None, uses config.URL_FILTERS
        
    Returns:
        Filtered list of URLs
    """
    if sections is None:
        sections = config.URL_FILTERS
    
    if not sections:
        return urls
    
    filtered = [url for url in urls if any(section in url for section in sections)]
    print(f"Filtered {len(urls)} URLs down to {len(filtered)} matching sections: {sections}")
    return filtered


if __name__ == "__main__":
    # Test the sitemap discovery
    print("Testing WHO sitemap discovery...")
    print(f"Sitemap URL: {config.WHO_SITEMAP_URL}")
    print(f"Filtering to sections: {config.URL_FILTERS}")
    
    urls = get_sitemap_urls()
    print(f"\nTotal URLs discovered: {len(urls)}")
    
    if urls:
        print("\nFirst 10 URLs:")
        for url in urls[:10]:
            print(f"  - {url}")
        
        # Show distribution by section
        print("\nDistribution by section:")
        for section in config.URL_FILTERS:
            count = sum(1 for url in urls if section in url)
            print(f"  {section}: {count} URLs")
