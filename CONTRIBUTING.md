# Contributing to Comptroller War Gov Data Extraction

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/comptroller.war.gov.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate the virtual environment: `source venv/bin/activate`
5. Install dependencies: `pip install -r requirements.txt`

## Development Setup

### Prerequisites

- Python 3.9+
- Tesseract OCR 4.0+
- Git

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` with your API keys and configuration.

## Making Changes

1. Create a new branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Test your changes locally
4. Commit with clear messages: `git commit -m "Add feature: description"`
5. Push to your fork: `git push origin feature/your-feature-name`
6. Create a Pull Request

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small

## Testing

Before submitting a PR:

1. Test the download script: `python src/download_pdfs.py --max 1`
2. Test OCR processing: `python src/ocr_processor.py path/to/test.pdf`
3. Test CSV transformation: `python src/csv_transformer.py path/to/test.txt`
4. Run the full pipeline: `python src/main.py --download-only`

## Documentation

- Update README.md if you add new features
- Add comments for complex logic
- Update docstrings when changing function signatures

## Pull Request Process

1. Ensure all tests pass
2. Update documentation as needed
3. Add a clear description of changes
4. Reference any related issues
5. Wait for review and address feedback

## Reporting Issues

When reporting issues, please include:

- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages and logs

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Maintain a positive environment

## Questions?

Feel free to open an issue for questions or discussion.

Thank you for contributing!
