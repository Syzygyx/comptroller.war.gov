#!/bin/bash
# Start chat server with RAG

echo "🚀 Starting Comptroller War Gov Chat Server"
echo "============================================"

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup.sh first"
    exit 1
fi

source venv/bin/activate

# Check if embeddings exist
if [ ! -f "data/embeddings/chunks.json" ]; then
    echo ""
    echo "📊 No embeddings found. Building from PDFs..."
    echo "   This will take a few minutes..."
    python src/rag_processor.py --rebuild
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to build embeddings"
        exit 1
    fi
fi

# Start server
echo ""
echo "🌐 Starting chat API server..."
echo "   Access at: http://localhost:5000/chat.html"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python src/chat_api.py --host 0.0.0.0 --port 5000
