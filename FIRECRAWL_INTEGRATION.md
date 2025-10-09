# Firecrawl Integration for Comptroller War Gov

This document describes the Firecrawl integration for comprehensive scraping of the comptroller.defense.gov website.

## 🔥 What is Firecrawl?

Firecrawl is a powerful web scraping service that:
- Handles JavaScript-heavy websites
- Provides comprehensive crawling capabilities
- Offers structured data extraction
- Supports both single-page and multi-page scraping

## 🚀 Setup

### 1. Get Firecrawl API Key

1. Visit [firecrawl.dev](https://firecrawl.dev)
2. Sign up for an account
3. Get your API key from the dashboard

### 2. Configure Local Environment

```bash
# Run the setup script
python setup_firecrawl.py

# Or manually add to .env file
echo "FIRECRAWL_API_KEY=your_key_here" >> .env
```

### 3. Configure GitHub Secrets

Add your Firecrawl API key to GitHub Secrets:
1. Go to: `https://github.com/Syzygyx/DD1414/settings/secrets/actions`
2. Click "New repository secret"
3. Name: `FIRECRAWL_API_KEY`
4. Value: Your Firecrawl API key

## 📊 Weekly Scraping Workflow

The Firecrawl scraper runs automatically every Monday at 2 AM UTC via GitHub Actions.

### What it does:

1. **Comprehensive Site Scraping**
   - Scrapes main reprogramming pages
   - Discovers all year-specific directories (1997-2025)
   - Handles JavaScript and dynamic content
   - Finds PDFs across the entire site

2. **PDF Discovery & Download**
   - Identifies all PDF documents
   - Downloads new PDFs automatically
   - Tracks download status and metadata
   - Handles duplicates and errors

3. **Processing Pipeline**
   - Runs OCR on new PDFs
   - Generates CSV data
   - Creates RAG embeddings
   - Updates validation reports

4. **Deployment**
   - Commits changes to repository
   - Deploys to GitHub Pages
   - Updates progress tracker
   - Reports results

### Target URLs Scraped:

- `https://comptroller.defense.gov/Budget-Execution/Reprogramming/`
- `https://comptroller.defense.gov/Portals/45/Documents/execution/reprogramming/`
- `https://comptroller.defense.gov/Budget-Execution/`
- `https://comptroller.defense.gov/Portals/45/Documents/execution/`
- `https://comptroller.defense.gov/Portals/45/Documents/`
- Year-specific URLs for 1997-2025

## 🧪 Testing

### Test Locally

```bash
# Test Firecrawl connection
python test_firecrawl.py

# Run limited scraping
python src/firecrawl_scraper.py --max-pages 10 --max-concurrent 3
```

### Test GitHub Actions

1. Go to the Actions tab in your repository
2. Click "Weekly Firecrawl Scraper"
3. Click "Run workflow"
4. Monitor the execution

## 📈 Monitoring

### Check Scraping Results

1. **GitHub Actions Logs**
   - View detailed execution logs
   - See PDF discovery and download stats
   - Monitor error handling

2. **Repository Changes**
   - New PDFs in `data/pdfs/`
   - Updated metadata in `data/metadata.json`
   - Progress updates in `docs/`

3. **Progress Tracker**
   - Visit the main page to see updated progress
   - Check the Gantt chart for completion status
   - Review DD1414 collection completeness

### Key Metrics

- **Total PDFs**: All documents discovered
- **DD1414 Documents**: Specific DD1414 forms
- **CSV Files**: Processed data files
- **RAG Embeddings**: Searchable document chunks
- **Coverage**: Years and document types covered

## 🔧 Configuration

### Scraper Settings

```python
# In src/firecrawl_scraper.py
max_pages_per_url = 100      # Max pages to scrape per URL
max_concurrent = 10          # Concurrent requests
max_depth = 3                # Crawling depth
```

### GitHub Actions Settings

```yaml
# In .github/workflows/firecrawl-scraper.yml
schedule:
  - cron: '0 2 * * 1'        # Every Monday at 2 AM UTC
```

## 🚨 Troubleshooting

### Common Issues

1. **API Key Not Found**
   - Check GitHub Secrets configuration
   - Verify .env file has correct key
   - Ensure key is valid and active

2. **Scraping Failures**
   - Check Firecrawl service status
   - Review rate limiting settings
   - Verify target URLs are accessible

3. **Download Errors**
   - Check network connectivity
   - Verify PDF URLs are valid
   - Review file permissions

4. **Processing Failures**
   - Check OCR dependencies
   - Verify LLM API keys
   - Review file formats

### Debug Commands

```bash
# Check Firecrawl connection
python -c "from firecrawl import FirecrawlApp; print('OK')"

# Test specific URL
python -c "
import asyncio
from src.firecrawl_scraper import FirecrawlComptrollerScraper
async def test():
    scraper = FirecrawlComptrollerScraper()
    result = await scraper.scrape_url('https://comptroller.defense.gov/Budget-Execution/Reprogramming/')
    print(result)
asyncio.run(test())
"

# Check scraping results
python analyze_scraping_coverage.py
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

1. **Monitor API Usage**
   - Check Firecrawl dashboard
   - Review rate limits
   - Update API key if needed

2. **Review Results**
   - Check for new document types
   - Verify data quality
   - Update scraping targets

3. **Optimize Performance**
   - Adjust concurrency settings
   - Update target URLs
   - Improve error handling

### Updates

- **Firecrawl API**: Keep library updated
- **Dependencies**: Regular security updates
- **Workflow**: Enhance based on results

## 📚 Resources

- [Firecrawl Documentation](https://docs.firecrawl.dev)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Comptroller.defense.gov](https://comptroller.defense.gov)
- [Project Repository](https://github.com/Syzygyx/DD1414)

## 🤝 Support

For issues with the Firecrawl integration:

1. Check the troubleshooting section
2. Review GitHub Actions logs
3. Test locally with debug commands
4. Open an issue in the repository

---

**Last Updated**: 2024-10-08
**Version**: 1.0.0
**Status**: Active