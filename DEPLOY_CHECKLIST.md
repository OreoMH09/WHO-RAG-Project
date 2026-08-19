# ✅ Deployment Checklist

## Before Pushing to GitHub

- [ ] **Verify .env is ignored**
  ```powershell
  git status | Select-String ".env"
  # Should show NOTHING or only ".env.template"
  ```

- [ ] **Check .gitignore includes:**
  - [x] `.env`
  - [x] `venv/`
  - [x] `data/`
  - [x] `.streamlit/secrets.toml`

- [ ] **Test app locally**
  ```powershell
  streamlit run app.py
  ```

## Push to GitHub

```powershell
# Initialize
git init

# Add files (respects .gitignore)
git add .

# Commit
git commit -m "WHO Brain Disease RAG System - Initial commit"

# Add remote (replace YOUR-USERNAME)
git remote add origin https://github.com/YOUR-USERNAME/WHO-Brain-Disease-RAG.git

# Push
git branch -M main
git push -u origin main
```

## Deploy on Streamlit Cloud

1. **Go to**: https://share.streamlit.io

2. **Create New App:**
   - Repository: `YOUR-USERNAME/WHO-Brain-Disease-RAG`
   - Branch: `main`
   - Main file path: `app.py`

3. **Add Secrets (IMPORTANT!):**
   Click "Advanced settings" → "Secrets"
   
   Add:
   ```toml
   GROQ_API_KEY = "gsk_your_actual_key_here"
   ```

4. **Click "Deploy"**

5. **Wait 5-10 minutes** for first build

## After Deployment

- [ ] **Test the live app**
  - Visit your app URL
  - Try asking: "What is dementia?"
  - Verify sources appear

- [ ] **Check secrets work**
  - If you get "API key not found" → Add secrets again
  - Restart app after adding secrets

- [ ] **Build index (if needed)**
  - Index is NOT deployed (too large)
  - Option 1: Let it run empty (explains to users)
  - Option 2: Build index in cloud on first run

## Verify Security

- [ ] **Check GitHub repo:**
  - Visit your repo
  - Click through files
  - **Verify .env is NOT visible** ✅

- [ ] **Check deployed app:**
  - API key is hidden
  - Only reads from Streamlit secrets
  - No keys in logs

## Share Your App! 🎉

Your app URL:
```
https://YOUR-USERNAME-who-brain-disease-rag-app-xxxxx.streamlit.app
```

Share with:
- [ ] On LinkedIn
- [ ] On Twitter
- [ ] In your portfolio
- [ ] With friends/colleagues

## Troubleshooting

### Problem: "API key not found"
**Solution:**
1. Go to Streamlit Cloud dashboard
2. Click your app → Settings → Secrets
3. Add `GROQ_API_KEY = "gsk_..."`
4. Restart app

### Problem: "No documents in collection"
**Expected!** Database not deployed (too large).

**Options:**
1. Users can run indexing themselves
2. Or: Pre-build index and host on cloud storage

### Problem: "Module not found"
**Solution:**
1. Check `requirements.txt` has all dependencies
2. Re-deploy

### Problem: Slow first load
**Normal!** First deployment:
- Downloads ~500MB of models
- Takes 5-10 minutes
- Subsequent loads are fast

## 🎯 Done!

- ✅ Code on GitHub (without secrets)
- ✅ App deployed on Streamlit Cloud
- ✅ Secrets secured
- ✅ App is live and shareable!

**Congratulations on deploying your RAG system!** 🚀
