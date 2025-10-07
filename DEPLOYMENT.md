# Deployment Guide

This guide covers deploying the Comptroller War Gov Data Extraction system with GitHub Actions and GitHub Pages.

## Prerequisites

- GitHub account
- Repository with this code
- (Optional) OpenAI or Anthropic API key for LLM validation

## GitHub Repository Setup

### 1. Create Repository

```bash
git init
git add .
git commit -m "Initial commit: Comptroller War Gov data extraction system"
git branch -M main
git remote add origin https://github.com/yourusername/comptroller.war.gov.git
git push -u origin main
```

### 2. Configure GitHub Secrets

Go to your repository Settings → Secrets and variables → Actions

Add the following secrets:

- `OPENAI_API_KEY` (optional): Your OpenAI API key
- `ANTHROPIC_API_KEY` (optional): Your Anthropic API key

**Note**: At least one API key is required for LLM validation. If neither is provided, validation will be skipped.

### 3. Enable GitHub Pages

1. Go to Settings → Pages
2. Source: Select "GitHub Actions"
3. Save

Your site will be available at: `https://yourusername.github.io/comptroller.war.gov`

## GitHub Actions Workflow

The workflow (`.github/workflows/nightly.yml`) runs:

- **Scheduled**: Every day at 2 AM UTC
- **Manual**: Via workflow_dispatch
- **On Push**: When code is pushed to main branch

### Workflow Steps

1. **Download PDFs**: Scrapes comptroller.defense.gov for new documents
2. **OCR Processing**: Extracts text from PDFs using Tesseract
3. **CSV Generation**: Transforms OCR text to structured CSV
4. **LLM Validation**: (Optional) Validates accuracy with AI
5. **Deploy**: Updates GitHub Pages with new data

### Manual Trigger

To manually trigger the workflow:

1. Go to Actions tab
2. Select "Nightly Data Update"
3. Click "Run workflow"
4. Select branch and run

## Local Development

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/comptroller.war.gov.git
cd comptroller.war.gov

# Run setup script
chmod +x setup.sh
./setup.sh

# Activate virtual environment
source venv/bin/activate
```

### Configuration

Edit `.env` file:

```bash
# LLM API Keys (optional, for validation)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# LLM Configuration
LLM_PROVIDER=openai  # or anthropic
LLM_MODEL=gpt-4-turbo-preview

# OCR Configuration
OCR_ENGINE=tesseract  # or easyocr or both
```

### Running Locally

```bash
# Full pipeline (download, process, validate)
python src/main.py

# Download only
python src/main.py --download-only

# Process existing PDFs only
python src/main.py --process-only

# Skip validation
python src/main.py --no-validate

# Limit downloads
python src/main.py --max-downloads 5
```

### Individual Scripts

```bash
# Download PDFs
python src/download_pdfs.py --max 10

# Process single PDF
python src/ocr_processor.py path/to/document.pdf --output output.txt

# Transform to CSV
python src/csv_transformer.py output.txt --output output.csv

# Validate CSV
python src/llm_validator.py output.csv --ocr-json ocr_result.json
```

## Monitoring

### GitHub Pages Dashboard

Visit your GitHub Pages site to:

- View processing statistics
- Browse extracted data
- Download CSV files
- Check validation reports

### GitHub Actions Logs

View detailed logs in the Actions tab:

1. Go to Actions
2. Select a workflow run
3. Click on job steps to see logs

### Metadata

Check `data/metadata.json` for:

- Downloaded files
- Processing status
- Validation results
- Timestamps

## Troubleshooting

### Workflow Fails

**Issue**: OCR processing fails  
**Solution**: Check Tesseract installation in workflow logs

**Issue**: API rate limit exceeded  
**Solution**: Reduce `max_downloads` in workflow or add delay

**Issue**: LLM validation fails  
**Solution**: Check API key secrets, or disable validation with `--no-validate`

### GitHub Pages Not Updating

1. Check Actions workflow succeeded
2. Verify Pages is enabled in Settings
3. Check deployment job logs
4. Clear browser cache

### Local Issues

**Issue**: Tesseract not found  
**Solution**: Install Tesseract OCR (see README.md)

**Issue**: Import errors  
**Solution**: Activate virtual environment and reinstall dependencies

**Issue**: Permission denied  
**Solution**: Make scripts executable with `chmod +x script.sh`

## Performance Optimization

### For Large Batches

```bash
# Increase batch size in .env
BATCH_SIZE=20
MAX_CONCURRENT_DOWNLOADS=5

# Use faster OCR engine
OCR_ENGINE=tesseract  # Faster than easyocr
```

### For Better Accuracy

```bash
# Use both OCR engines
OCR_ENGINE=both

# Use more powerful LLM
LLM_MODEL=gpt-4-turbo-preview  # or claude-3-opus-20240229
```

## Costs

### GitHub Actions

- Free tier: 2,000 minutes/month
- This workflow: ~10-20 minutes/run
- Daily runs: ~300-600 minutes/month (within free tier)

### LLM API

- OpenAI GPT-4: ~$0.03-0.06 per validation
- Anthropic Claude: ~$0.015-0.075 per validation
- Daily cost: $0.30-$0.60 (assuming 10 files/day)
- Monthly: ~$9-18

### OCR

- Tesseract: Free and open source
- EasyOCR: Free and open source

## Security

### API Keys

- Never commit API keys to repository
- Use GitHub Secrets for sensitive data
- Rotate keys regularly

### Data Privacy

- Review PDFs before public GitHub Pages deployment
- Consider private repository for sensitive data
- PDFs are not committed to repository (in .gitignore)

## Backup and Recovery

### Data Backup

```bash
# Backup data directory
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Restore from backup
tar -xzf backup-20250107.tar.gz
```

### GitHub Branches

```bash
# Create backup branch before major changes
git checkout -b backup-$(date +%Y%m%d)
git push origin backup-$(date +%Y%m%d)
```

## Support

For issues or questions:

- GitHub Issues: Report bugs or request features
- Documentation: Check README.md and CONTRIBUTING.md
- Workflow Logs: Check Actions tab for detailed logs

---

**Last Updated**: 2025-10-07
