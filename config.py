"""
Configuration constants for the WHO RAG system.
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_HTML_DIR = DATA_DIR / "raw_html"
CLEAN_TEXT_DIR = DATA_DIR / "clean_text"
CHROMA_DB_DIR = DATA_DIR / "chroma_db"

# WHO.int URLs
WHO_BASE_URL = "https://www.who.int"
WHO_SITEMAP_URL = "http://www.who.int/sitemaps/sitemapindex.xml"

# Crawler settings
CRAWL_DELAY = 1.0  # seconds between requests (be polite!)
CONCURRENT_REQUESTS = 5
REQUEST_TIMEOUT = 30  # seconds
USER_AGENT = "who-rag-bot/1.0 (educational project; contact: your-email@example.com)"

# Filter which sections to crawl (to keep scope manageable)
# Focused on brain/neurological diseases
URL_FILTERS = [
    "/health-topics/dementia",
    "/health-topics/epilepsy",
    "/health-topics/alzheimer",
    "/health-topics/parkinson",
    "/health-topics/stroke",
    "/health-topics/mental-health",
    "/health-topics/brain",
    "/health-topics/neurological",
    "/news/item/dementia",
    "/news/item/epilepsy",
    "/news/item/alzheimer",
    "/news/item/stroke",
    "/news/item/mental",
    "/fact-sheets/detail/dementia",
    "/fact-sheets/detail/epilepsy",
    "/fact-sheets/detail/mental",
]

# Text processing
MIN_TEXT_LENGTH = 200  # minimum characters for a page to be considered valid
CHUNK_SIZE = 800  # tokens per chunk
CHUNK_OVERLAP = 120  # token overlap between chunks

# Embeddings
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"  # 768-dim, strong for retrieval
# Alternative: "all-MiniLM-L6-v2" (384-dim, faster but less accurate)
EMBEDDING_BATCH_SIZE = 32
NORMALIZE_EMBEDDINGS = True

# Vector database
CHROMA_COLLECTION_NAME = "who_health_docs"
DISTANCE_METRIC = "cosine"  # cosine similarity for normalized embeddings

# Search
DEFAULT_TOP_K = 5  # number of chunks to retrieve
HYBRID_SEARCH_WEIGHT = 0.5  # 0.5 = equal weight for vector and BM25

# LLM (Groq API)
GROQ_MODEL = "openai/gpt-oss-120b"  # OpenAI GPT OSS 120B (large, high quality)
# Alternative models:
# "openai/gpt-oss-20b" - Smaller, faster
# "qwen/qwen3.6-27b" - Qwen 3.6 27B
# "allam-2-7b" - Allam 2 7B (smaller)
MAX_TOKENS = 1000
TEMPERATURE = 0.0  # deterministic for factual Q&A

# Pages cache
PAGES_JSONL = CLEAN_TEXT_DIR / "pages.jsonl"

# Create directories if they don't exist
for directory in [RAW_HTML_DIR, CLEAN_TEXT_DIR, CHROMA_DB_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
