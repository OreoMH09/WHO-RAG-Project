# WHO.int RAG System — End-to-End Build Plan (for Kiro IDE)

A complete, vibe-codeable spec for scraping the WHO website, turning it into a
vector database, and building a semantic search + RAG pipeline on top of it.
Paste sections of this into Kiro's **Spec** mode (or use the whole file as a
steering doc) and let it generate the code.

---

## 0. Before You Start — Legal / Ethical Notes

- Check `https://www.who.int/robots.txt` and respect `Disallow` rules and crawl-delay.
- WHO is a UN agency; content is generally reusable for non-commercial/informational
  purposes but **check their terms of use** before any public-facing or commercial deployment.
- Rate-limit your crawler (1 request/sec is a safe default) — don't hammer their servers.
- Add a proper `User-Agent` string identifying your bot and a contact email.
- This is for a **personal/educational RAG project** — keep it non-commercial unless you've
  confirmed licensing.

---

## 1. High-Level Architecture

```
WHO.int  ──(crawl)──▶  Raw HTML  ──(clean+extract)──▶  Clean Text
                                                             │
                                                     (chunk into passages)
                                                             │
                                                     (embed each chunk)
                                                             │
                                                             ▼
                                                     Vector Database
                                                     (Chroma / Qdrant)
                                                             ▲
                                                             │
User Query ──(embed query)──▶ Semantic Search ──(top-k retrieve)──┘
                                                             │
                                                    (optional: rerank)
                                                             │
                                                    LLM (Claude API)
                                                             │
                                                    Answer + Citations
```

---

## 2. Tech Stack (recommended, all free/open-source except the LLM call)

| Layer | Tool | Why |
|---|---|---|
| Crawling | `httpx` + `BeautifulSoup4`, or `Scrapy` for scale | WHO pages are mostly static HTML; Scrapy if you want concurrency/politeness built-in |
| JS-rendered pages (if needed) | `Playwright` | Only if some sections are React/Vue-rendered |
| Sitemap discovery | `usp` (ultimate-sitemap-parser) or manual `requests` on `sitemap.xml` | WHO has sitemaps — much better than blind crawling |
| Text cleaning | `trafilatura` or `readability-lxml` | Strips nav/footer/boilerplate far better than raw BS4 |
| Chunking | `langchain-text-splitters` (`RecursiveCharacterTextSplitter`) or custom semantic chunker | Keeps chunks coherent |
| Embeddings | `sentence-transformers` (`BAAI/bge-base-en-v1.5` or `all-MiniLM-L6-v2`) — free, local | No API cost, runs offline |
| Vector DB | `ChromaDB` (simplest, local, persistent) — or `Qdrant` if you want production-grade + hybrid search | Chroma = fastest to vibe-code; Qdrant = better filtering/scaling |
| Hybrid search (optional) | `rank_bm25` combined with vector score | Improves recall on exact medical terms (e.g. "monkeypox") |
| Reranker (optional) | `cross-encoder/ms-marco-MiniLM-L-6-v2` via `sentence-transformers` | Reorders top-k for better precision |
| LLM for answer generation | Claude API (`claude-sonnet-4-6` or similar) | Final answer synthesis with citations |
| App/UI | `Streamlit` or `Gradio` | Fast local demo UI |
| Orchestration (optional) | Plain Python — avoid LangChain/LlamaIndex overhead unless you want it; this project is simple enough to hand-roll | Easier to debug in vibe-coding |

---

## 3. Project Structure

```
who-rag/
├── .env                        # API keys (never commit)
├── requirements.txt
├── config.py                   # constants: base_url, chunk_size, model names
├── crawler/
│   ├── sitemap.py               # discover all URLs from sitemap(s)
│   ├── fetch.py                 # polite async fetcher w/ retries + rate limit
│   └── extract.py               # trafilatura-based clean text extraction
├── ingestion/
│   ├── chunk.py                  # text splitter
│   ├── embed.py                  # embedding model wrapper
│   └── build_index.py             # orchestrates crawl → clean → chunk → embed → store
├── search/
│   ├── vector_store.py            # Chroma/Qdrant client wrapper
│   ├── hybrid_search.py            # BM25 + vector fusion (optional)
│   └── rerank.py                    # cross-encoder reranking (optional)
├── rag/
│   ├── prompt_templates.py
│   └── generate.py                  # retrieval + Claude call + citation formatting
├── app.py                       # Streamlit/Gradio front end
├── data/
│   ├── raw_html/                 # cached raw pages
│   ├── clean_text/                # cleaned .txt/.jsonl per page
│   └── chroma_db/                 # persistent vector store
└── tests/
    └── test_retrieval.py
```

---

## 4. Step-by-Step Build

### Step 1 — Environment Setup
```bash
mkdir who-rag && cd who-rag
python -m venv venv && source venv/bin/activate     # or .\venv\Scripts\activate on Windows
pip install httpx beautifulsoup4 trafilatura sentence-transformers chromadb \
            rank_bm25 streamlit python-dotenv anthropic tqdm lxml
pip freeze > requirements.txt
```
Create `.env`:
```
ANTHROPIC_API_KEY=sk-ant-xxxx
```

### Step 2 — Discover URLs via Sitemap
WHO exposes sitemaps at paths like `https://www.who.int/sitemap.xml` (check for a
sitemap index that links to sub-sitemaps — news, health-topics, fact-sheets, etc).

```python
# crawler/sitemap.py
import httpx
from lxml import etree

def get_sitemap_urls(sitemap_url: str) -> list[str]:
    resp = httpx.get(sitemap_url, timeout=30)
    root = etree.fromstring(resp.content)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    # If it's a sitemap index, recurse into child sitemaps
    sub_sitemaps = root.findall(".//sm:sitemap/sm:loc", ns)
    if sub_sitemaps:
        urls = []
        for s in sub_sitemaps:
            urls.extend(get_sitemap_urls(s.text))
        return urls
    return [loc.text for loc in root.findall(".//sm:url/sm:loc", ns)]
```
Filter to the sections you care about (e.g. `/news/`, `/health-topics/`,
`/fact-sheets/`, `/emergencies/`) to keep scope manageable — the full site is huge.

### Step 3 — Polite Crawler
```python
# crawler/fetch.py
import httpx, asyncio, time

HEADERS = {"User-Agent": "who-rag-bot/1.0 (educational project; contact: you@email.com)"}

async def fetch_all(urls, concurrency=5, delay=1.0):
    sem = asyncio.Semaphore(concurrency)
    results = {}
    async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
        async def fetch_one(url):
            async with sem:
                try:
                    r = await client.get(url)
                    if r.status_code == 200:
                        results[url] = r.text
                    await asyncio.sleep(delay)
                except Exception as e:
                    print(f"failed {url}: {e}")
        await asyncio.gather(*(fetch_one(u) for u in urls))
    return results
```
Cache raw HTML to `data/raw_html/` (hash of URL as filename) so re-runs don't re-fetch.

### Step 4 — Clean Text Extraction
`trafilatura` handles WHO's boilerplate (nav, cookie banners, footers) far better
than manual BS4 tag-stripping.
```python
# crawler/extract.py
import trafilatura

def extract_clean_text(html: str, url: str) -> dict | None:
    text = trafilatura.extract(html, include_tables=True, include_links=False)
    if not text or len(text) < 200:
        return None
    metadata = trafilatura.extract_metadata(html)
    return {
        "url": url,
        "title": metadata.title if metadata else "",
        "text": text,
        "date": metadata.date if metadata else None,
    }
```
Save each as a line in `data/clean_text/pages.jsonl`.

### Step 5 — Chunking
Medical/health content works best with moderate chunk sizes (~500–800 tokens)
and overlap (~100 tokens) so context isn't cut mid-explanation.
```python
# ingestion/chunk.py
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=120,
    separators=["\n\n", "\n", ". ", " "],
)

def chunk_page(page: dict) -> list[dict]:
    chunks = splitter.split_text(page["text"])
    return [
        {
            "id": f"{page['url']}::chunk{i}",
            "text": c,
            "metadata": {"url": page["url"], "title": page["title"], "chunk_index": i},
        }
        for i, c in enumerate(chunks)
    ]
```

### Step 6 — Embeddings
```python
# ingestion/embed.py
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-base-en-v1.5")  # 768-dim, strong for retrieval

def embed_texts(texts: list[str]) -> list[list[float]]:
    # bge models want a prefix for queries but not for passages
    return model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=True).tolist()

def embed_query(query: str) -> list[float]:
    prefixed = "Represent this sentence for searching relevant passages: " + query
    return model.encode([prefixed], normalize_embeddings=True).tolist()[0]
```

### Step 7 — Store in Chroma
```python
# search/vector_store.py
import chromadb

client = chromadb.PersistentClient(path="data/chroma_db")
collection = client.get_or_create_collection("who_health_docs", metadata={"hnsw:space": "cosine"})

def upsert_chunks(chunks: list[dict], embeddings: list[list[float]]):
    collection.upsert(
        ids=[c["id"] for c in chunks],
        embeddings=embeddings,
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )

def query(embedding: list[float], top_k=5, where: dict | None = None):
    return collection.query(query_embeddings=[embedding], n_results=top_k, where=where)
```

### Step 8 — Orchestrate the Full Ingestion
```python
# ingestion/build_index.py
import json, asyncio
from crawler.sitemap import get_sitemap_urls
from crawler.fetch import fetch_all
from crawler.extract import extract_clean_text
from ingestion.chunk import chunk_page
from ingestion.embed import embed_texts
from search.vector_store import upsert_chunks

async def main():
    urls = get_sitemap_urls("https://www.who.int/sitemap.xml")
    urls = [u for u in urls if "/news/" in u or "/fact-sheets/" in u or "/health-topics/" in u]
    print(f"Found {len(urls)} URLs to crawl")

    html_map = await fetch_all(urls)

    all_chunks = []
    with open("data/clean_text/pages.jsonl", "w") as f:
        for url, html in html_map.items():
            page = extract_clean_text(html, url)
            if not page:
                continue
            f.write(json.dumps(page) + "\n")
            all_chunks.extend(chunk_page(page))

    print(f"Total chunks: {len(all_chunks)}")
    texts = [c["text"] for c in all_chunks]
    embeddings = embed_texts(texts)
    upsert_chunks(all_chunks, embeddings)
    print("Indexing complete.")

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 9 — Semantic Search Function
```python
# search/hybrid_search.py (optional but recommended)
from rank_bm25 import BM25Okapi
from ingestion.embed import embed_query
from search.vector_store import query as vector_query

def semantic_search(user_query: str, top_k=5):
    q_emb = embed_query(user_query)
    results = vector_query(q_emb, top_k=top_k)
    return [
        {"text": doc, "url": meta["url"], "title": meta["title"], "score": 1 - dist}
        for doc, meta, dist in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        )
    ]
```
For hybrid search: run BM25 over the same chunk texts, normalize both score sets
(min-max), and combine as `0.5 * vector_score + 0.5 * bm25_score` (tune weights).

### Step 10 — RAG Answer Generation (Claude API)
```python
# rag/generate.py
import os
from anthropic import Anthropic
from search.hybrid_search import semantic_search

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """You are a health information assistant answering questions using
only the provided WHO source excerpts. Always cite sources by URL. If the excerpts
don't contain the answer, say so — do not use outside knowledge for medical facts."""

def answer_question(query: str, top_k=5):
    results = semantic_search(query, top_k=top_k)
    context = "\n\n".join(
        f"[Source {i+1}: {r['title']} — {r['url']}]\n{r['text']}"
        for i, r in enumerate(results)
    )
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}],
    )
    return {
        "answer": resp.content[0].text,
        "sources": [{"title": r["title"], "url": r["url"]} for r in results],
    }
```

### Step 11 — Simple UI
```python
# app.py
import streamlit as st
from rag.generate import answer_question

st.title("WHO Health Info — Semantic Search & RAG")
query = st.text_input("Ask a health question:")
if query:
    with st.spinner("Searching WHO knowledge base..."):
        result = answer_question(query)
    st.write(result["answer"])
    st.subheader("Sources")
    for s in result["sources"]:
        st.markdown(f"- [{s['title']}]({s['url']})")
```
Run with: `streamlit run app.py`

### Step 12 — Evaluation (don't skip this)
Build a small test set of ~20 known WHO facts (e.g. "What is the WHO definition of
health?", "What are malaria symptoms?") with expected source pages, and check:
- **Retrieval hit rate**: is the right page in top-5 results?
- **Answer faithfulness**: does the answer match the source, no hallucination?

```python
# tests/test_retrieval.py
from search.hybrid_search import semantic_search

test_cases = [
    {"query": "malaria symptoms", "expected_url_substring": "malaria"},
    {"query": "how is COVID-19 transmitted", "expected_url_substring": "covid"},
]

for case in test_cases:
    results = semantic_search(case["query"], top_k=5)
    hit = any(case["expected_url_substring"] in r["url"] for r in results)
    print(f"{case['query']}: {'PASS' if hit else 'FAIL'}")
```

---

## 5. Extra Features (Recommended Upgrades)

| Feature | Benefit | Effort |
|---|---|---|
| **Reranking with cross-encoder** | Boosts precision of top-3 results significantly | Low — one extra model call |
| **Hybrid search (BM25 + vector)** | Better recall on drug names, disease codes, exact terms | Medium |
| **Metadata filtering** (e.g. by date, page type) | "Only show fact sheets from 2024+" | Low, Chroma supports `where=` |
| **Incremental re-indexing** | Only re-crawl pages whose `last_modified` in sitemap changed | Medium |
| **Query expansion** (ask Claude to rewrite vague queries) | Improves recall for short/ambiguous queries | Low |
| **Answer citation highlighting** | Show exact chunk text used, not just URL | Low |
| **Multi-turn conversation memory** | Follow-up questions ("what about children?") | Medium |
| **Language filtering** | WHO site is multilingual — filter to English pages only during crawl | Low |
| **Caching layer** | Cache repeated queries/answers to cut API cost | Low |

---

## 6. Using Kiro IDE Specifically

Kiro works best when you give it **specs**, not just prompts. Suggested workflow:

1. **Create a new Kiro spec** named `who-rag` and paste in Section 3 (Project
   Structure) as the file tree, and Section 4 as the task breakdown — Kiro will
   turn each numbered step into a checkable task.
2. Use **Kiro's steering docs** (`.kiro/steering/`) to lock in conventions:
   - `tech.md` → paste Section 2 (tech stack table) so Kiro doesn't substitute
     different libraries mid-project.
   - `structure.md` → paste Section 3 folder layout.
   - `product.md` → one paragraph describing the goal ("semantic search + RAG
     over WHO.int health content, cited answers only").
3. Let Kiro generate one file at a time, in dependency order: `config.py` →
   `crawler/*` → `ingestion/*` → `search/*` → `rag/*` → `app.py`.
4. After each generated file, run it standalone before moving to the next step
   (e.g. test the crawler on 5 URLs before running the full sitemap).
5. Use Kiro's **hooks** feature to auto-run `pytest tests/` after any change to
   `search/` or `rag/` files, catching retrieval regressions early.

---

## 7. Realistic Scope Warning

WHO.int has tens of thousands of pages across many languages. For a first working
version:
- Limit to English pages only.
- Limit to 2–3 sections (e.g. `/news/`, `/fact-sheets/`, `/health-topics/`) —
  likely a few thousand pages, which is very manageable for local embeddings.
- You can always expand the crawl scope later since the pipeline is incremental.

---

## 8. Suggested requirements.txt
```
httpx
beautifulsoup4
lxml
trafilatura
langchain-text-splitters
sentence-transformers
chromadb
rank_bm25
streamlit
python-dotenv
anthropic
tqdm
```
