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
# Use direct GitHub download URL (more reliable)
DOWNLOAD_URL = f"https://github.com/{GITHUB_REPO}/releases/download/{RELEASE_TAG}/{DATABASE_ZIP}"

# Export for use in other modules
__all__ = ['setup_database', 'database_exists', 'DOWNLOAD_URL']


def database_exists():
    """Check if database already exists and is not empty."""
    if not DATABASE_DIR.exists():
        return False
    
    # Check if there are database files (chroma.sqlite3 or any db files)
    sqlite_file = DATABASE_DIR / "chroma.sqlite3"
    if sqlite_file.exists():
        return True
    
    # Also check for any files in subdirectories
    all_files = list(DATABASE_DIR.rglob("*.*"))
    return len(all_files) > 0


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
    
    # Try multiple times with increasing timeout
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"\nAttempt {attempt + 1}/{max_retries}...")
            
            # Add headers and increase timeout
            opener = urllib.request.build_opener()
            opener.addheaders = [
                ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
                ('Accept', '*/*')
            ]
            urllib.request.install_opener(opener)
            
            # Download with timeout
            urllib.request.urlretrieve(DOWNLOAD_URL, DATABASE_ZIP, reporthook)
            print("\n✅ Download complete!")
            return True
            
        except urllib.error.HTTPError as e:
            print(f"\n❌ HTTP Error {e.code}: {e.reason}")
            if e.code == 404:
                print(f"URL: {DOWNLOAD_URL}")
                print("💡 File not found in release. Check if it's uploaded correctly.")
                return False
            elif e.code == 403:
                print("💡 GitHub rate limit or access denied. Retrying...")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(5)
                    continue
                return False
        except urllib.error.URLError as e:
            print(f"\n❌ URL Error: {e.reason}")
            print("💡 Check your internet connection")
            if attempt < max_retries - 1:
                print("Retrying...")
                import time
                time.sleep(3)
                continue
            return False
        except Exception as e:
            print(f"\n❌ Download failed: {e}")
            if attempt < max_retries - 1:
                print("Retrying...")
                import time
                time.sleep(3)
                continue
            return False
    
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
        # Count files for verification
        all_files = list(DATABASE_DIR.rglob("*.*"))
        print(f"📊 Found {len(all_files)} files in database")
        return True
    
    print("⚠️ Database not found. Starting download...")
    print(f"📍 Download URL: {DOWNLOAD_URL}")
    print(f"📁 Target directory: {DATABASE_DIR}")
    
    # Download
    if not download_database():
        print("❌ Failed to download database")
        print("💡 Check if the release exists: https://github.com/OreoMH09/WHO-RAG-Project/releases/tag/v1.0-database")
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
        all_files = list(DATABASE_DIR.rglob("*.*"))
        print(f"📊 Total files: {len(all_files)}")
        print("=" * 80)
        return True
    else:
        print("❌ Database setup failed - files not found after extraction")
        print(f"📁 Checking what's in data/: {list(Path('data').iterdir())}")
        return False


if __name__ == "__main__":
    import sys
    success = setup_database()
    sys.exit(0 if success else 1)
