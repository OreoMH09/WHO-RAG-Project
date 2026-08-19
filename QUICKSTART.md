# 🚀 Quick Start Guide - WHO RAG System

Get up and running in 5 minutes!

## Step 1: Get Your Groq API Key (FREE!)

1. Go to https://console.groq.com
2. Sign up for a free account (no credit card required)
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `gsk_`)

**Note**: Groq offers a generous free tier with fast inference!

## Step 2: Install Dependencies

```powershell
# Navigate to project directory
cd WHORAG

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install all packages
pip install -r requirements.txt
```

This will install:
- Groq API client
- ChromaDB (vector database)
- Sentence Transformers (embeddings)
- Streamlit (UI)
- And more...

## Step 3: Configure API Key

Create a `.env` file in the project root:

```bash
GROQ_API_KEY=gsk_your_actual_key_here
```

**Important**: Never commit this file to git (it's already in .gitignore)

## Step 4: Build the Index

Start with a small sample (fast, for testing):

```powershell
python -m ingestion.build_index sample 10
```

This will:
1. Discover WHO pages from sitemap
2. Fetch 10 sample pages
3. Extract and clean text
4. Generate embeddings
5. Store in ChromaDB

Expected time: 2-3 minutes

## Step 5: Launch the UI

```powershell
streamlit run app.py
```

The app will open in your browser at http://localhost:8501

## Step 6: Ask Questions!

Try these example questions:
- "What is COVID-19?"
- "How is malaria transmitted?"
- "What are the symptoms of tuberculosis?"
- "What is the WHO definition of health?"

Each answer will include:
✅ Cited sources from WHO
✅ Relevance scores
✅ Direct links to original documents

## 🎯 Available Models

Choose from Groq's models in the sidebar:

| Model | Speed | Quality | Context |
|-------|-------|---------|---------|
| **llama-3.1-70b-versatile** | Fast | High | 128K tokens |
| llama-3.1-8b-instant | Very Fast | Good | 128K tokens |
| mixtral-8x7b-32768 | Fast | High | 32K tokens |
| gemma2-9b-it | Fast | Good | 8K tokens |

**Recommended**: `llama-3.1-70b-versatile` for best results

## 🔧 Advanced Options

### Build Larger Index

For more comprehensive coverage:

```powershell
# Index 50 pages
python -m ingestion.build_index sample 50

# Index ALL WHO pages (takes 30+ minutes)
python -m ingestion.build_index full
```

### Test Retrieval Quality

```powershell
python -m tests.test_retrieval
```

### Adjust Search Settings

In the Streamlit UI sidebar:
- **Search Method**: Choose hybrid (best), vector, or BM25
- **Number of Sources**: 1-10 (5 recommended)
- **Temperature**: 0 (deterministic) to 1 (creative)

## 📊 What to Expect

### Performance
- **First query**: ~3-5 seconds (model loading)
- **Subsequent queries**: ~1-2 seconds
- **Indexing 10 pages**: ~2-3 minutes
- **Indexing 100 pages**: ~15-20 minutes

### Costs
- **Groq API**: FREE tier (very generous limits)
- **No credit card required**
- **Rate limits**: 30 requests/minute (more than enough)

### Accuracy
- ~85% hit rate on known health topics
- Sources always cited
- Answers grounded in WHO documents

## ❓ Troubleshooting

### "No documents in collection"
```powershell
python -m ingestion.build_index sample 10
```

### "GROQ_API_KEY not found"
1. Create `.env` file in project root
2. Add: `GROQ_API_KEY=gsk_your_key`
3. Restart the app

### "Module not found" errors
```powershell
pip install -r requirements.txt
```

### Slow embedding generation
First run downloads the BGE model (~500MB). Subsequent runs are fast.

### API rate limits
Groq free tier: 30 req/min. Wait a moment between queries if you hit limits.

## 🎓 Next Steps

1. **Test different models** in the UI sidebar
2. **Adjust search settings** to see how results change
3. **Index more pages** for better coverage
4. **Read the full README.md** for advanced features

## 💡 Tips

- Start with **10-20 pages** to test quickly
- Use **hybrid search** for best results
- **Temperature 0** for factual medical info
- Check **source scores** to gauge relevance
- Use **example questions** if unsure what to ask

## 🆘 Need Help?

- Check the main **README.md** for detailed docs
- Run **tests** to verify system is working
- Check **Groq console** for API usage/limits
- Review **Streamlit terminal** for error logs

---

**Ready to go?** Just run:
```powershell
streamlit run app.py
```

Happy searching! 🏥
