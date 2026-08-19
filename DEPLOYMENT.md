# 🚀 Deployment Guide

This guide shows how to deploy the WHO Brain Disease RAG system **without exposing your API keys**.

## 🌟 Option 1: Streamlit Cloud (Recommended - FREE)

### Step 1: Push to GitHub (Without .env)

```powershell
# Initialize git
git init
git add .
git commit -m "WHO Brain Disease RAG System"

# Add remote (replace YOUR-USERNAME)
git remote add origin https://github.com/YOUR-USERNAME/WHO-Brain-Disease-RAG.git

# Push
git branch -M main
git push -u origin main
```

**✅ Your `.env` file will NOT be pushed** (it's in `.gitignore`)

### Step 2: Deploy on Streamlit Cloud

1. **Go to**: https://share.streamlit.io
2. **Sign in** with GitHub
3. **Click**: "New app"
4. **Select**:
   - Repository: `YOUR-USERNAME/WHO-Brain-Disease-RAG`
   - Branch: `main`
   - Main file: `app.py`

5. **Add Secrets** (Important!):
   - Click "Advanced settings"
   - Go to "Secrets" section
   - Add:
     ```toml
     GROQ_API_KEY = "gsk_your_actual_key_here"
     ```

6. **Click**: "Deploy!"

### Step 3: Wait for Build

- First deployment: ~5-10 minutes (installs dependencies)
- Subsequent deploys: ~2-3 minutes

### Step 4: Access Your App

Your app will be live at:
```
https://YOUR-USERNAME-who-brain-disease-rag-app-xxxxx.streamlit.app
```

---

## 🔒 How Secrets Work

### Local Development (Your Computer):
```
App reads from: .env file
Location: C:\Users\...\WHORAG\.env
Security: Never pushed to GitHub
```

### Cloud Deployment (Streamlit):
```
App reads from: Streamlit Secrets
Location: Streamlit Cloud dashboard
Security: Encrypted by Streamlit
```

### Code Handles Both:
```python
try:
    import streamlit as st
    api_key = st.secrets.get("GROQ_API_KEY")  # Cloud
except:
    api_key = os.getenv("GROQ_API_KEY")       # Local
```

---

## 📦 Option 2: Hugging Face Spaces (Alternative - FREE)

### Step 1: Create Space

1. Go to: https://huggingface.co/spaces
2. Click "Create new Space"
3. Choose:
   - Name: `who-brain-disease-rag`
   - SDK: `Streamlit`
   - Visibility: Public or Private

### Step 2: Add Secrets

1. Go to Settings → Repository secrets
2. Add secret:
   - Name: `GROQ_API_KEY`
   - Value: `gsk_your_key_here`

### Step 3: Push Code

```powershell
git remote add hf https://huggingface.co/spaces/YOUR-USERNAME/who-brain-disease-rag
git push hf main
```

### Step 4: Create packages.txt

Create `packages.txt` with system dependencies:
```
build-essential
```

---

## 🐳 Option 3: Docker + Any Cloud

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy app files (but not .env!)
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run app
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

### Deploy with Environment Variables

**Railway, Render, or DigitalOcean:**
- Add `GROQ_API_KEY` as environment variable in dashboard
- App reads from `os.getenv("GROQ_API_KEY")`

---

## ⚠️ Important: Data Files

### What Gets Deployed:
- ✅ Python code
- ✅ `requirements.txt`
- ✅ `.env.template` (template only)
- ✅ `README.md`

### What Does NOT Get Deployed:
- ❌ `.env` (your secrets)
- ❌ `venv/` (virtual environment)
- ❌ `data/` (cached pages and database)

### Building Index on Deployment:

The deployed app will **NOT have the indexed data**. You have 2 options:

#### Option A: Pre-built Index (Recommended)
1. Build index locally:
   ```powershell
   python -m ingestion.build_index full
   ```

2. Upload `data/chroma_db/` to cloud storage (e.g., AWS S3)

3. Download on app startup

#### Option B: Build on First Run
- Let users build the index when they first use the app
- Takes 10 minutes on first run
- Index persists in Streamlit Cloud

---

## 🔐 Security Checklist

Before deploying:

### ✅ DO:
- [ ] Add `.env` to `.gitignore`
- [ ] Use `.env.template` with placeholder values
- [ ] Add secrets in deployment platform
- [ ] Test locally before deploying
- [ ] Verify `.env` is NOT in git:
  ```powershell
  git status | Select-String ".env"
  ```

### ❌ DON'T:
- [ ] Commit `.env` file
- [ ] Hardcode API keys in code
- [ ] Push API keys in comments
- [ ] Share your `.env` file

---

## 🧪 Test Before Deploy

### Local Test:
```powershell
streamlit run app.py
```

### Verify Secrets Work:
```python
# In Python console:
import streamlit as st
try:
    key = st.secrets["GROQ_API_KEY"]
    print("✅ Secrets work!")
except:
    print("❌ Add secrets to .streamlit/secrets.toml")
```

---

## 📊 Deployment Comparison

| Platform | Cost | Speed | Secrets | Database |
|----------|------|-------|---------|----------|
| **Streamlit Cloud** | FREE | Fast | Built-in | Persistent |
| Hugging Face | FREE | Medium | Built-in | Persistent |
| Railway | $5/mo | Fast | Built-in | Persistent |
| Render | FREE tier | Slow | Built-in | Temporary |
| Heroku | $7/mo | Medium | Built-in | Persistent |

**Recommended: Streamlit Cloud** ⭐

---

## 🆘 Troubleshooting

### "API key not found" on deployment
- Check secrets are added in platform dashboard
- Verify secret name is exactly `GROQ_API_KEY`
- Restart app after adding secrets

### "No documents in collection"
- Index not deployed (expected)
- Users need to build index on first run
- Or: pre-build and upload to cloud storage

### "Module not found"
- Check all dependencies in `requirements.txt`
- Some packages need system dependencies

---

## 🎉 Success!

Once deployed:
1. ✅ Your app is live at a public URL
2. ✅ API keys are secure (not in code)
3. ✅ Others can use it without your keys
4. ✅ Free hosting (Streamlit Cloud)

**Share your app URL with others!**

---

## 📝 Quick Deploy Checklist

```
[ ] Code pushed to GitHub (without .env)
[ ] Streamlit Cloud account created
[ ] App deployed
[ ] GROQ_API_KEY added to secrets
[ ] App tested and working
[ ] URL shared!
```

**Ready to deploy? Start with Streamlit Cloud!** 🚀
