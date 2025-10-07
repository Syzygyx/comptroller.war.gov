# Quick Start Guide

Get up and running with Comptroller War Gov Data Extraction in 5 minutes!

## 🚀 Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/comptroller.war.gov.git
cd comptroller.war.gov

# Run automated setup
chmod +x setup.sh
./setup.sh

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the pipeline!
python src/main.py --max-downloads 3
```

That's it! The system will download 3 PDFs, process them with OCR, and generate CSV files.

## 🔧 Option 2: Manual Setup

### Step 1: Prerequisites

```bash
# Install Python 3.9+
python3 --version

# Install Tesseract OCR
# macOS:
brew install tesseract

# Ubuntu/Debian:
sudo apt-get install tesseract-ocr poppler-utils

# Windows: Download from
# https://github.com/UB-Mannheim/tesseract/wiki
```

### Step 2: Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

### Step 3: Run Pipeline

```bash
# Download and process PDFs
python src/main.py --max-downloads 5
```

## 📊 View Results

After running, check:

- `data/pdfs/` - Downloaded PDF files
- `data/csv/` - Generated CSV files
- `data/metadata.json` - Processing metadata

## 🌐 Enable GitHub Pages (Optional)

For automated nightly runs and web dashboard:

1. Push code to GitHub:
   ```bash
   git remote add origin https://github.com/yourusername/comptroller.war.gov.git
   git push -u origin main
   ```

2. Enable GitHub Pages:
   - Go to Settings → Pages
   - Source: GitHub Actions
   - Save

3. Add API keys (optional for LLM validation):
   - Go to Settings → Secrets → Actions
   - Add `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

4. Workflow runs automatically at 2 AM UTC daily!

5. View dashboard at: `https://yourusername.github.io/comptroller.war.gov`

## 🎯 Common Commands

```bash
# Download PDFs only
python src/main.py --download-only

# Process existing PDFs
python src/main.py --process-only

# Skip LLM validation
python src/main.py --no-validate

# Limit downloads
python src/main.py --max-downloads 10

# Individual scripts
python src/download_pdfs.py --max 5
python src/ocr_processor.py document.pdf
python src/csv_transformer.py text.txt --output data.csv
```

## 🔍 Check Status

```bash
# View metadata
cat data/metadata.json | python -m json.tool

# Count PDFs
ls data/pdfs/*.pdf | wc -l

# Count CSVs
ls data/csv/*.csv | wc -l

# View validation summary
cat data/validation/validation_summary.json | python -m json.tool
```

## 🐛 Troubleshooting

### Tesseract Not Found

```bash
# Check installation
tesseract --version

# macOS: Add to PATH
export PATH="/opt/homebrew/bin:$PATH"

# Or specify in .env
echo 'TESSERACT_PATH=/opt/homebrew/bin/tesseract' >> .env
```

### Import Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### No PDFs Downloaded

The scraper respects rate limits and may find no new documents. This is normal!

To test with a specific PDF:
```bash
# Download a sample PDF manually
curl -o data/pdfs/test.pdf "https://comptroller.defense.gov/Portals/45/Documents/..."

# Process it
python src/main.py --process-only
```

## 📚 Next Steps

- Read [README.md](README.md) for detailed information
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
- See [CONTRIBUTING.md](CONTRIBUTING.md) to contribute

## 💡 Pro Tips

1. **Start Small**: Use `--max-downloads 3` for testing
2. **Check Logs**: Add `-v` or check output for debugging
3. **Save API Costs**: Use `--no-validate` during testing
4. **Monitor Progress**: Check `data/metadata.json` regularly
5. **Backup Data**: Run `tar -czf backup.tar.gz data/` before major updates

## 🎉 You're Ready!

You now have a fully functional automated data extraction pipeline for comptroller.defense.gov!

For questions or issues, open a GitHub issue or check the documentation.

Happy data extracting! 🚀
