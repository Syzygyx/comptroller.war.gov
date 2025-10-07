# Comptroller War Gov Historical Appropriation Data

This project automatically downloads, processes, and extracts historical appropriation data from comptroller.defense.gov. It converts PDF documents to structured CSV format using OCR technology and validates the results using LLM analysis.

## 🎯 Features

- **Automated PDF Download**: Scrapes comptroller.defense.gov for new appropriation documents
- **OCR Processing**: Converts PDF documents to structured CSV format
- **Nightly Updates**: GitHub Actions workflow runs daily to check for new documents
- **Progress Monitoring**: GitHub Pages site to browse results and monitor progress
- **LLM Validation**: Automated accuracy checking of extracted CSV data
- **Format Compliance**: CSV output matches StealthOCR format standards

## 📊 CSV Output Format

The system generates CSV files with the following standardized columns:

```csv
appropriation_category,appropriation code,appropriation activity,branch,fiscal_year_start,fiscal_year_end,budget_activity_number,budget_activity_title,pem,budget_title,program_base_congressional,program_base_dod,reprogramming_amount,revised_program_total,explanation,file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Tesseract OCR 4.0+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/comptroller.war.gov.git
cd comptroller.war.gov

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Usage

```bash
# Download and process all new PDFs
python src/main.py

# Download only (no OCR processing)
python src/download_pdfs.py

# Process existing PDFs
python src/process_pdfs.py

# Validate CSV results with LLM
python src/validate_csv.py
```

## 🏗️ Project Structure

```
comptroller.war.gov/
├── .github/
│   └── workflows/
│       └── nightly.yml          # GitHub Actions workflow
├── docs/                         # GitHub Pages site
│   ├── index.html
│   ├── browse.html
│   └── progress.html
├── src/
│   ├── download_pdfs.py         # PDF scraping and download
│   ├── ocr_processor.py         # OCR processing (from StealthOCR)
│   ├── csv_transformer.py       # CSV transformation
│   ├── llm_validator.py         # LLM validation
│   └── main.py                  # Main orchestration script
├── data/
│   ├── pdfs/                    # Downloaded PDFs
│   ├── csv/                     # Generated CSV files
│   └── metadata.json            # Tracking metadata
├── requirements.txt
├── README.md
└── .gitignore
```

## 🤖 Automated Workflow

The GitHub Actions workflow runs nightly at 2 AM UTC:

1. Checks comptroller.defense.gov for new documents
2. Downloads any new PDFs
3. Processes PDFs with OCR
4. Generates CSV files
5. Validates results with LLM
6. Updates GitHub Pages with new results
7. Commits changes to repository

## 📈 Progress Monitoring

Visit the GitHub Pages site to:
- View processing progress
- Browse all extracted CSV files
- Review validation reports
- Download individual or bulk CSV files
- View OCR accuracy metrics

## 🔍 OCR Technology

This project uses the same OCR technology as [StealthOCR](https://github.com/Syzygyx/StealthOCR):

- **Primary Engine**: Tesseract OCR
- **Secondary Engine**: EasyOCR
- **Image Processing**: OpenCV
- **Accuracy**: 95%+ for structured documents

## 🧠 LLM Validation

The system uses LLM technology to:
- Verify CSV data accuracy
- Check for missing or malformed data
- Validate financial amounts and calculations
- Flag potential OCR errors
- Generate quality reports

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Based on [StealthOCR](https://github.com/Syzygyx/StealthOCR) technology
- Data source: [Comptroller.defense.gov](https://comptroller.defense.gov)
- OCR engines: Tesseract, EasyOCR

## 📞 Support

For issues or questions:
- GitHub Issues: [Report bugs or request features](https://github.com/yourusername/comptroller.war.gov/issues)
- Documentation: See `/docs` folder

---

**Last Updated**: {{ current_date }}
**Status**: {{ build_status }}
