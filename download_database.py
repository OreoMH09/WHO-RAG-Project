"""
Download and extract the pre-built ChromaDB database from GitHub Releases.
This runs automatically on Streamlit Cloud deployment.
"""
import os
import zipfile
import urllib.request
import shutil
from pathlib import Path


# Configuration
GITHUB_REPO = "OreoMH09/WHO-RAG-Project"
RELEASE_TAG = "v1.0-database"
DATABASE_ZIP = "chroma_db.zip"
DATABASE_DIR = Path("data/chroma_db")
DOWNLOAD_URL = f"https://github.com/{GITHUB_REPO}/releases/download/{RELEASE_TAG}/{DATABASE_ZIP}"


def database_exists():
    """Check if database already exists and is not empty."""
    if not DATABASE_DIR.exists():
        return False
    
    # Check if there are any files in the database directory
    parquet_files = list(DATABASE_DIR.rglob("*.parquet"))
    return len(parquet_files) > 0


def download_database():
    """Download the database from GitHub Releases."""
    print(f"📥 Downloading database from: {DOWNLOAD_URL}")
    
    # Create data directory if it doesn't exist
    Path("data").mkdir(exist_ok=True)
    
    # Download with progress
    def reporthook(count, block_size, total_size):
        if total_size > 0:
            percent = int(count * block_size * 100 / total_size)
            print(f"\rDownloading... {percent}%", end="", flush=True)
    
    try:
        urllib.request.urlretrieve(DOWNLOAD_URL, DATABASE_ZIP, reporthook)
        print("\n✅ Download complete!")
        return True
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        return False


def extract_database():
    """Extract the downloaded zip file."""
    print(f"📦 Extracting database to: {DATABASE_DIR}")
    
    try:
        # Remove existing database if present
        if DATABASE_DIR.exists():
            shutil.rmtree(DATABASE_DIR)
        
        # Extract
        with zipfile.ZipFile(DATABASE_ZIP, 'r') as zip_ref:
            zip_ref.extractall("data")
        
        print("✅ Extraction complete!")
        
        # Clean up zip file
        os.remove(DATABASE_ZIP)
        print("🧹 Cleaned up zip file")
        
        return True
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return False


def setup_database():
    """Main function to set up the database."""
    print("=" * 80)
    print("WHO RAG DATABASE SETUP")
    print("=" * 80)
    
    # Check if database already exists
    if database_exists():
        print("✅ Database already exists. Skipping download.")
        return True
    
    print("⚠️ Database not found. Starting download...")
    
    # Download
    if not download_database():
        print("❌ Failed to download database")
        return False
    
    # Extract
    if not extract_database():
        print("❌ Failed to extract database")
        return False
    
    # Verify
    if database_exists():
        print("=" * 80)
        print("✅ DATABASE SETUP COMPLETE!")
        print(f"📊 Database location: {DATABASE_DIR.absolute()}")
        print("=" * 80)
        return True
    else:
        print("❌ Database setup failed - files not found after extraction")
        return False


if __name__ == "__main__":
    import sys
    success = setup_database()
    sys.exit(0 if success else 1)
