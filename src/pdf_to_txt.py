#!/usr/bin/env python3
"""
PDF to TXT extractor (no OCR)
- Uses PyPDF2 text extraction to produce .txt files from PDFs
- Designed to work even when Tesseract/Poppler are unavailable

Usage:
  python3 src/pdf_to_txt.py --input data/pdfs --output data/txt
  python3 src/pdf_to_txt.py --input data/pdfs/file.pdf --output data/txt/file.txt
"""

import sys
import argparse
from pathlib import Path
from typing import List
from PyPDF2 import PdfReader


def extract_text_from_pdf(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    pages_text: List[str] = []
    for i, page in enumerate(reader.pages, 1):
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""
        pages_text.append(f"\n--- Page {i} ---\n{page_text}")
    return "\n".join(pages_text).strip()


def process_file(input_pdf: Path, output_txt: Path) -> None:
    output_txt.parent.mkdir(parents=True, exist_ok=True)
    text = extract_text_from_pdf(input_pdf)
    output_txt.write_text(text)
    print(f"✓ Wrote TXT: {output_txt}")


def process_directory(input_dir: Path, output_dir: Path) -> None:
    pdf_files = sorted(input_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDFs found in {input_dir}")
        return
    output_dir.mkdir(parents=True, exist_ok=True)
    for pdf_file in pdf_files:
        out_file = output_dir / (pdf_file.stem + ".txt")
        process_file(pdf_file, out_file)


def main():
    parser = argparse.ArgumentParser(description="Extract text from PDFs without OCR")
    parser.add_argument("--input", required=True, help="Input PDF file or directory")
    parser.add_argument("--output", required=True, help="Output TXT file or directory")

    args = parser.parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if input_path.is_dir():
        process_directory(input_path, output_path)
    else:
        process_file(input_path, output_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
