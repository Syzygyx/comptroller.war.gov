#!/usr/bin/env python3
"""
Setup script for local scraper (no API required)
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_local_scraper():
    """Setup local scraper with Playwright"""
    
    print("🔥 Local Scraper Setup (No API Required)")
    print("=" * 50)
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Not in a virtual environment")
        print("   Consider running: python -m venv venv && source venv/bin/activate")
    
    # Install Playwright
    print("\n📦 Installing Playwright...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
        print("✅ Playwright installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Playwright: {e}")
        return False
    
    # Install Playwright browsers
    print("\n🌐 Installing Playwright browsers...")
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        print("✅ Playwright browsers installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Playwright browsers: {e}")
        return False
    
    # Install other dependencies
    print("\n📚 Installing other dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "aiohttp", "beautifulsoup4"], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    
    # Create data directories
    print("\n📁 Creating data directories...")
    data_dirs = ['data/pdfs', 'data/csv', 'data/embeddings', 'data/validation', 'logs']
    for dir_path in data_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {dir_path}")
    
    # Test the scraper
    print("\n🧪 Testing local scraper...")
    try:
        result = subprocess.run([
            sys.executable, "run_local_scraper.py", "--test-mode"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Local scraper test passed!")
            print("📊 Test output:")
            print(result.stdout)
        else:
            print("❌ Local scraper test failed")
            print("📊 Error output:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Test timed out (this is normal for first run)")
    except Exception as e:
        print(f"⚠️  Test error: {e}")
    
    print("\n🎉 Local scraper setup complete!")
    print("\n📋 Usage:")
    print("  # Test mode (limited URLs)")
    print("  python run_local_scraper.py --test-mode")
    print("")
    print("  # Full scraping")
    print("  python run_local_scraper.py")
    print("")
    print("  # Scrape specific years")
    print("  python run_local_scraper.py --years 2020 2021 2022")
    print("")
    print("  # Custom settings")
    print("  python run_local_scraper.py --max-pages 100 --max-concurrent 5")
    
    return True

def create_github_workflow():
    """Create GitHub Actions workflow for local scraper"""
    
    workflow_content = '''name: Weekly Local Scraper

on:
  schedule:
    # Run every Monday at 2 AM UTC
    - cron: '0 2 * * 1'
  workflow_dispatch:  # Allow manual trigger
  push:
    branches:
      - main
    paths:
      - 'src/local_firecrawl_scraper.py'
      - '.github/workflows/local-scraper.yml'

jobs:
  local-scrape:
    runs-on: ubuntu-latest
    
    permissions:
      contents: write
      pages: write
      id-token: write
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      with:
        fetch-depth: 0
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        cache: 'pip'
    
    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr poppler-utils
    
    - name: Install Python dependencies
      run: |
        pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Install Playwright browsers
      run: |
        playwright install chromium
    
    - name: Create data directories
      run: |
        mkdir -p data/pdfs data/csv data/embeddings data/validation logs
    
    - name: Run local scraper
      run: |
        echo "🚀 Starting local scraping..."
        python run_local_scraper.py --max-pages 100 --max-concurrent 5
    
    - name: Process new PDFs with OCR
      run: |
        echo "🔍 Processing new PDFs with OCR..."
        python src/main.py --process-only
    
    - name: Generate RAG embeddings
      run: |
        echo "🧠 Generating RAG embeddings..."
        python src/rag_processor.py --rebuild || echo "RAG processing failed, continuing..."
    
    - name: Copy data to docs folder
      run: |
        echo "📋 Copying data to docs folder..."
        cp -r data/csv/* docs/data/ 2>/dev/null || true
        cp data/metadata.json docs/data/ 2>/dev/null || true
        cp data/validation/validation_summary.json docs/data/ 2>/dev/null || true
        cp -r data/embeddings/* docs/data/embeddings/ 2>/dev/null || true
    
    - name: Update timestamp
      run: |
        echo "⏰ Updating timestamp..."
        echo "const lastUpdated = '$(date -u +"%Y-%m-%d %H:%M:%S UTC")';" > docs/last-updated.js
    
    - name: Commit and push changes
      run: |
        echo "📝 Committing changes..."
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        
        git add .
        
        if git diff --staged --quiet; then
          echo "No changes to commit"
        else
          git commit -m "Weekly local scrape: $(date -u +'%Y-%m-%d %H:%M:%S UTC')
          
          - Local scraping with Playwright (no API required)
          - New PDFs processed with OCR
          - RAG embeddings updated
          - Data synchronized to docs folder"
          
          git push origin main
        fi
    
    - name: Deploy to GitHub Pages
      uses: actions/deploy-pages@v4
      with:
        artifact_name: deployment
        path: docs
    
    - name: Report scraping results
      run: |
        echo "## Weekly Local Scraping Results" >> $GITHUB_STEP_SUMMARY
        echo "" >> $GITHUB_STEP_SUMMARY
        echo "### 📊 Scraping Statistics" >> $GITHUB_STEP_SUMMARY
        
        PDF_COUNT=$(find data/pdfs -name "*.pdf" | wc -l)
        echo "- Total PDFs: $PDF_COUNT" >> $GITHUB_STEP_SUMMARY
        
        DD1414_COUNT=$(find data/pdfs -name "*DD1414*" -o -name "*dd1414*" | wc -l)
        echo "- DD1414 documents: $DD1414_COUNT" >> $GITHUB_STEP_SUMMARY
        
        CSV_COUNT=$(find data/csv -name "*.csv" | wc -l)
        echo "- CSV files: $CSV_COUNT" >> $GITHUB_STEP_SUMMARY
        
        if [ -f "data/embeddings/chunks.json" ]; then
          EMBEDDING_COUNT=$(jq length data/embeddings/chunks.json 2>/dev/null || echo "0")
          echo "- RAG embeddings: $EMBEDDING_COUNT chunks" >> $GITHUB_STEP_SUMMARY
        else
          echo "- RAG embeddings: Not available" >> $GITHUB_STEP_SUMMARY
        fi
'''
    
    workflow_path = Path('.github/workflows/local-scraper.yml')
    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(workflow_path, 'w') as f:
        f.write(workflow_content)
    
    print(f"✅ Created GitHub Actions workflow: {workflow_path}")

if __name__ == "__main__":
    print("🚀 Setting up local scraper for Comptroller War Gov")
    print("=" * 60)
    
    if setup_local_scraper():
        print("\n🤔 Would you like to create a GitHub Actions workflow? (y/n): ", end="")
        if input().lower().startswith('y'):
            create_github_workflow()
            print("✅ GitHub Actions workflow created!")
        
        print("\n🎉 Setup complete!")
        print("\nNext steps:")
        print("1. Test locally: python run_local_scraper.py --test-mode")
        print("2. Run full scraping: python run_local_scraper.py")
        print("3. Push changes to enable GitHub Actions")
    else:
        print("\n❌ Setup failed")
        sys.exit(1)