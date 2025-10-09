#!/bin/bash
# Deployment script for GitHub Actions

echo "🚀 Starting Comptroller War Gov Deployment..."

# Set up environment
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/pdfs data/csv data/embeddings data/validation docs/data/embeddings

# Download PDFs if needed
echo "📥 Checking for PDFs..."
if [ $(find data/pdfs -name "*.pdf" | wc -l) -lt 5 ]; then
    echo "📥 Downloading PDFs..."
    python src/main.py --max-downloads 10
else
    echo "✅ PDFs already exist"
fi

# Process PDFs
echo "🔍 Processing PDFs with OCR..."
python src/main.py --process-only

# Generate RAG embeddings
echo "🧠 Generating RAG embeddings..."
python src/rag_processor.py --rebuild || echo "⚠️ RAG processing failed, continuing..."

# Copy data to docs
echo "📋 Copying data to docs folder..."
cp -r data/csv/* docs/data/ 2>/dev/null || true
cp data/metadata.json docs/data/ 2>/dev/null || true
cp data/validation/validation_summary.json docs/data/ 2>/dev/null || true
cp -r data/embeddings/* docs/data/embeddings/ 2>/dev/null || true

# Update timestamp
echo "⏰ Updating timestamp..."
echo "const lastUpdated = '$(date -u +"%Y-%m-%d %H:%M:%S UTC")';" > docs/last-updated.js

echo "✅ Deployment preparation complete!"
echo "🌐 Application ready at: https://syzygyx.github.io/DD1414/"
echo "💬 Chat API available at: /api/chat-widget"