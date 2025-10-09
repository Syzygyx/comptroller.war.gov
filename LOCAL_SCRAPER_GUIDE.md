# Local Scraper Guide (No API Required)

This guide explains how to use the local scraper that runs completely offline without requiring any API keys.

## 🔥 What is the Local Scraper?

The local scraper is a Firecrawl-style scraper that:
- Uses Playwright for JavaScript-heavy websites
- Runs completely locally (no API required)
- Handles dynamic content and complex navigation
- Discovers and downloads PDFs automatically
- Works offline after initial setup

## 🚀 Quick Start

### 1. Setup

```bash
# Run the setup script
python setup_local_scraper.py
```

This will:
- Install Playwright and dependencies
- Install browser binaries
- Create necessary directories
- Test the scraper

### 2. Test the Scraper

```bash
# Test with limited URLs
python run_local_scraper.py --test-mode
```

### 3. Run Full Scraping

```bash
# Full scraping
python run_local_scraper.py

# Scrape specific years
python run_local_scraper.py --years 2020 2021 2022

# Custom settings
python run_local_scraper.py --max-pages 100 --max-concurrent 5
```

## 📊 Features

### Comprehensive Site Scraping
- Scrapes main reprogramming pages
- Discovers all year-specific directories (1997-2025)
- Handles JavaScript and dynamic content
- Finds PDFs across the entire site

### PDF Discovery & Download
- Identifies all PDF documents
- Downloads new PDFs automatically
- Tracks download status and metadata
- Handles duplicates and errors

### Local Processing
- No API keys required
- Runs completely offline
- Uses Playwright for browser automation
- Async processing for efficiency

## 🛠️ Configuration

### Command Line Options

```bash
python run_local_scraper.py [OPTIONS]

Options:
  --max-pages INT        Max pages per URL (default: 50)
  --max-concurrent INT   Max concurrent requests (default: 3)
  --output-dir PATH      Output directory for PDFs (default: data/pdfs)
  --metadata-file PATH   Metadata file (default: data/metadata.json)
  --test-mode           Run in test mode with limited URLs
  --years INT [INT ...]  Specific years to scrape
```

### Target URLs

The scraper automatically targets:
- `https://comptroller.defense.gov/Budget-Execution/Reprogramming/`
- `https://comptroller.defense.gov/Portals/45/Documents/execution/reprogramming/`
- `https://comptroller.defense.gov/Budget-Execution/`
- `https://comptroller.defense.gov/Portals/45/Documents/execution/`
- `https://comptroller.defense.gov/Portals/45/Documents/`
- Year-specific URLs for 1997-2025

## 🧪 Testing

### Test Connection

```bash
# Test Playwright installation
python -c "from playwright.async_api import async_playwright; print('Playwright OK')"

# Test scraper
python test_local_scraper.py
```

### Test Specific URLs

```bash
# Test with limited scope
python run_local_scraper.py --test-mode

# Test specific years
python run_local_scraper.py --years 2024 --max-pages 10
```

## 📈 Monitoring

### Check Results

1. **PDFs Downloaded**: Check `data/pdfs/` directory
2. **Metadata**: Review `data/metadata.json`
3. **Logs**: Check console output for errors
4. **Progress**: Monitor download statistics

### Key Metrics

- **Total PDFs**: All documents discovered
- **DD1414 Documents**: Specific DD1414 forms
- **Download Success Rate**: Successful vs failed downloads
- **Coverage**: Years and document types covered

## 🔧 Troubleshooting

### Common Issues

1. **Playwright Not Installed**
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **Browser Installation Failed**
   ```bash
   # On macOS
   brew install playwright
   
   # On Ubuntu
   sudo apt-get install playwright
   ```

3. **Permission Errors**
   ```bash
   chmod +x run_local_scraper.py
   chmod +x test_local_scraper.py
   ```

4. **Memory Issues**
   - Reduce `--max-concurrent` (default: 3)
   - Reduce `--max-pages` (default: 50)

5. **Network Timeouts**
   - Check internet connection
   - Verify target URLs are accessible
   - Increase timeout in code if needed

### Debug Commands

```bash
# Check Playwright installation
python -c "import playwright; print('OK')"

# Test specific URL
python -c "
import asyncio
from src.local_firecrawl_scraper import LocalFirecrawlScraper
async def test():
    scraper = LocalFirecrawlScraper()
    result = await scraper.scrape_url_with_playwright('https://comptroller.defense.gov/Budget-Execution/Reprogramming/')
    print(result)
asyncio.run(test())
"

# Check scraping results
python analyze_scraping_coverage.py
```

## 🚀 GitHub Actions Integration

### Automatic Weekly Runs

The local scraper can be integrated with GitHub Actions for automatic weekly runs:

1. **Workflow File**: `.github/workflows/local-scraper.yml`
2. **Schedule**: Every Monday at 2 AM UTC
3. **No API Keys Required**: Runs completely locally

### Manual Trigger

```bash
# Trigger manually via GitHub Actions
gh workflow run "Weekly Local Scraper"
```

## 📊 Expected Results

### After First Run

- **PDFs**: 1000+ documents discovered
- **DD1414**: Complete historical coverage (1997-2025)
- **Processing**: OCR and CSV generation
- **RAG**: Searchable document embeddings
- **Deployment**: Updated GitHub Pages site

### Weekly Updates

- **New PDFs**: Any newly published documents
- **Updated Data**: Fresh CSV and RAG data
- **Progress**: Updated completion percentages
- **Reports**: Weekly scraping statistics

## 🔄 Maintenance

### Regular Tasks

1. **Update Dependencies**
   ```bash
   pip install --upgrade playwright aiohttp beautifulsoup4
   ```

2. **Update Browsers**
   ```bash
   playwright install chromium
   ```

3. **Review Results**
   - Check for new document types
   - Verify data quality
   - Update scraping targets

### Performance Optimization

- **Concurrency**: Adjust `--max-concurrent` based on system resources
- **Pages**: Adjust `--max-pages` based on available time
- **Memory**: Monitor memory usage during large scrapes
- **Storage**: Ensure sufficient disk space for PDFs

## 📚 Advanced Usage

### Custom Scraping

```python
from src.local_firecrawl_scraper import LocalFirecrawlScraper
import asyncio

async def custom_scrape():
    scraper = LocalFirecrawlScraper()
    
    # Scrape specific URL
    result = await scraper.scrape_url_with_playwright(
        "https://comptroller.defense.gov/Budget-Execution/Reprogramming/",
        max_pages=10
    )
    
    print(f"Found {len(result['pdf_links'])} PDFs")

asyncio.run(custom_scrape())
```

### Batch Processing

```bash
# Scrape years in batches
python run_local_scraper.py --years 1997 1998 1999 2000 2001
python run_local_scraper.py --years 2002 2003 2004 2005 2006
python run_local_scraper.py --years 2007 2008 2009 2010 2011
# ... and so on
```

## 🤝 Support

For issues with the local scraper:

1. Check the troubleshooting section
2. Run the test script
3. Review console output for errors
4. Check Playwright installation
5. Open an issue in the repository

## 📋 Requirements

- Python 3.11+
- Playwright
- aiohttp
- beautifulsoup4
- Sufficient disk space for PDFs
- Stable internet connection

---

**Last Updated**: 2024-10-08
**Version**: 1.0.0
**Status**: Active