#!/bin/bash
# Setup script for comptroller.war.gov data extraction

echo "🚀 Setting up Comptroller War Gov Data Extraction"
echo "=================================================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo ""
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check for Tesseract
echo ""
echo "🔍 Checking for Tesseract OCR..."
if command -v tesseract &> /dev/null; then
    tesseract_version=$(tesseract --version 2>&1 | head -n 1)
    echo "✓ $tesseract_version"
else
    echo "⚠️  Tesseract not found. Please install it:"
    echo "   macOS: brew install tesseract"
    echo "   Ubuntu: sudo apt-get install tesseract-ocr"
    echo "   Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
fi

# Create directories
echo ""
echo "📁 Creating directories..."
mkdir -p data/pdfs
mkdir -p data/csv
mkdir -p data/validation
mkdir -p docs/data
echo "✓ Directories created"

# Copy .env.example to .env if not exists
echo ""
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✓ Created .env - Please edit with your API keys"
else
    echo "✓ .env file already exists"
fi

echo ""
echo "=================================================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys (if using LLM validation)"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run the pipeline: python src/main.py"
echo ""
echo "For more information, see README.md"
