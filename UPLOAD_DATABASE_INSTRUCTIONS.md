# 📤 Upload Database to GitHub Releases

## ✅ You Have:
- ✅ `chroma_db.zip` (12 MB) - Your full database with 1,074 documents
- ✅ Code pushed to GitHub
- ✅ Auto-download script ready

## 🎯 Next Steps:

### Step 1: Create a GitHub Release

1. **Go to your repo:** https://github.com/OreoMH09/WHO-RAG-Project

2. **Click "Releases"** (on the right side)

3. **Click "Create a new release"**

4. **Fill in the form:**
   - **Tag:** `v1.0-database`
   - **Release title:** `WHO Brain Disease Database - 1,074 Documents`
   - **Description:**
     ```
     Pre-built ChromaDB vector database for WHO Brain Disease RAG System
     
     Contains 1,074 document chunks from WHO sources on:
     - Dementia
     - Alzheimer's Disease
     - Parkinson's Disease
     - Epilepsy
     - Stroke
     - Mental Health
     
     This database is automatically downloaded by the Streamlit app on first run.
     ```

5. **Upload file:**
   - Drag and drop: `chroma_db.zip`
   - Wait for upload to complete

6. **Click "Publish release"**

### Step 2: Verify Upload

After publishing:
1. Go to: https://github.com/OreoMH09/WHO-RAG-Project/releases/tag/v1.0-database
2. You should see `chroma_db.zip` (12.06 MB)
3. Copy the download URL - should be:
   ```
   https://github.com/OreoMH09/WHO-RAG-Project/releases/download/v1.0-database/chroma_db.zip
   ```

### Step 3: Test on Streamlit Cloud

1. Go to your Streamlit app (or click "Reboot" if already deployed)
2. On first load, it will:
   - Download `chroma_db.zip` from GitHub Releases
   - Extract to `data/chroma_db/`
   - Takes ~1-2 minutes first time
3. Subsequent loads are instant (database is cached)

### Step 4: Test the App

Ask a question like:
```
What is dementia and what are its symptoms?
```

You should get:
- ✅ Detailed answer from Groq API
- ✅ Citations to WHO sources
- ✅ Source links

---

## 🎉 Done!

Your app is now fully functional with:
- ✅ 1,074 pre-indexed documents
- ✅ Auto-download on deployment
- ✅ No manual setup needed for users

---

## 📊 File Locations

**Local (Your Computer):**
```
C:\Users\Sanika Naik\OneDrive\Desktop\PROJECTS\WHORAG\
├── chroma_db.zip              ← Upload this to GitHub Releases
└── data\chroma_db\            ← Original database
```

**GitHub:**
```
https://github.com/OreoMH09/WHO-RAG-Project
├── Code (main branch)         ← Already pushed ✅
└── Releases
    └── v1.0-database
        └── chroma_db.zip      ← Upload here
```

**Streamlit Cloud:**
```
App downloads from GitHub Releases on first run
Caches in: data/chroma_db/
```

---

## ⚠️ Troubleshooting

### Issue: Download fails on Streamlit
**Solution:** Check the release tag is exactly `v1.0-database` (case-sensitive)

### Issue: Database not found after download
**Solution:** Check the zip contains `chroma_db/` folder at the root level

### Issue: App is slow on first load
**Expected!** First load downloads 12 MB and extracts. Takes ~1-2 minutes.

---

## 🔄 Updating the Database

If you rebuild the index later:

1. Compress new database:
   ```powershell
   Compress-Archive -Path "data\chroma_db" -DestinationPath "chroma_db_new.zip" -Force
   ```

2. Create new release (e.g., `v1.1-database`)

3. Update `download_database.py`:
   ```python
   RELEASE_TAG = "v1.1-database"
   ```

4. Commit and push

---

## 📝 Summary

**You need to do:**
1. ✅ Go to: https://github.com/OreoMH09/WHO-RAG-Project/releases/new
2. ✅ Tag: `v1.0-database`
3. ✅ Upload: `chroma_db.zip`
4. ✅ Publish release
5. ✅ Wait for Streamlit to reload (~2 min)
6. ✅ Test the app!

**Total time:** ~5 minutes to upload, ~2 minutes for app to download and extract

🚀 **Ready to upload? Go to the releases page now!**
