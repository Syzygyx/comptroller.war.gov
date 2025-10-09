#!/usr/bin/env python3
"""
DD1414 Form Data Extractor

This script extracts structured data from DD1414 PDF forms and converts it to CSV format.
DD1414 forms are used for reprogramming actions in the Department of Defense.
"""

import os
import re
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import pandas as pd
from datetime import datetime
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DD1414Record:
    """Data structure for DD1414 form records"""
    # File information
    filename: str
    fiscal_year: str
    document_type: str  # Base, Call_Memo, etc.
    
    # Form identification
    form_number: str = "DD1414"
    form_title: str = "Reprogramming Action"
    
    # Date information
    submission_date: Optional[str] = None
    effective_date: Optional[str] = None
    fiscal_year_covered: Optional[str] = None
    
    # Organization information
    requesting_organization: Optional[str] = None
    approving_authority: Optional[str] = None
    
    # Financial information
    total_amount: Optional[float] = None
    amount_reprogrammed: Optional[float] = None
    source_fund: Optional[str] = None
    target_fund: Optional[str] = None
    
    # Reprogramming details
    reprogramming_type: Optional[str] = None
    justification: Optional[str] = None
    impact_statement: Optional[str] = None
    
    # Additional fields
    page_count: Optional[int] = None
    file_size: Optional[int] = None
    extraction_date: str = None
    
    def __post_init__(self):
        if self.extraction_date is None:
            self.extraction_date = datetime.now().isoformat()

class DD1414Scraper:
    """Main scraper class for DD1414 forms"""
    
    def __init__(self, input_dir: str = "data/pdfs", output_dir: str = "data/dd1414_csv"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # DD1414 specific patterns
        self.dd1414_patterns = {
            'fiscal_year': r'FY\s*(\d{4})',
            'submission_date': r'Submission\s*Date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            'effective_date': r'Effective\s*Date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            'total_amount': r'Total\s*Amount[:\s]*\$?([\d,]+\.?\d*)',
            'amount_reprogrammed': r'Amount\s*Reprogrammed[:\s]*\$?([\d,]+\.?\d*)',
            'requesting_org': r'Requesting\s*Organization[:\s]*([^\n\r]+)',
            'approving_auth': r'Approving\s*Authority[:\s]*([^\n\r]+)',
            'source_fund': r'Source\s*Fund[:\s]*([^\n\r]+)',
            'target_fund': r'Target\s*Fund[:\s]*([^\n\r]+)',
            'reprogramming_type': r'Reprogramming\s*Type[:\s]*([^\n\r]+)',
            'justification': r'Justification[:\s]*([^\n\r]+)',
            'impact_statement': r'Impact\s*Statement[:\s]*([^\n\r]+)',
        }
        
        # Common DD1414 field patterns
        self.field_patterns = {
            'date_patterns': [
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
                r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}'
            ],
            'amount_patterns': [
                r'\$?([\d,]+\.?\d*)\s*(?:million|billion|thousand)?',
                r'Amount[:\s]*\$?([\d,]+\.?\d*)',
                r'Total[:\s]*\$?([\d,]+\.?\d*)'
            ],
            'organization_patterns': [
                r'(Department of Defense|DOD|DoD)',
                r'(Army|Navy|Air Force|Marine Corps)',
                r'(Office of the Secretary|OSD)',
                r'(Comptroller|DFAS)',
                r'(Defense Logistics Agency|DLA)',
                r'(Defense Intelligence Agency|DIA)'
            ]
        }
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF using PyMuPDF"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text += page.get_text()
            
            doc.close()
            return text
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def extract_text_with_ocr(self, pdf_path: Path) -> str:
        """Extract text from PDF using OCR (for scanned documents)"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                # Convert page to image
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Convert to PIL Image
                image = Image.open(io.BytesIO(img_data))
                
                # Extract text using OCR
                page_text = pytesseract.image_to_string(image)
                text += page_text + "\n"
            
            doc.close()
            return text
        except Exception as e:
            logger.error(f"Error with OCR extraction from {pdf_path}: {e}")
            return ""
    
    def parse_dd1414_data(self, text: str, filename: str) -> DD1414Record:
        """Parse DD1414 form data from extracted text"""
        
        # Extract basic info from filename
        fiscal_year = self.extract_fiscal_year_from_filename(filename)
        document_type = self.extract_document_type_from_filename(filename)
        
        # Initialize record
        record = DD1414Record(
            filename=filename,
            fiscal_year=fiscal_year,
            document_type=document_type
        )
        
        # Extract data using patterns
        for field, pattern in self.dd1414_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                
                # Map to record fields
                if field == 'fiscal_year':
                    record.fiscal_year_covered = value
                elif field == 'submission_date':
                    record.submission_date = value
                elif field == 'effective_date':
                    record.effective_date = value
                elif field == 'total_amount':
                    record.total_amount = self.parse_amount(value)
                elif field == 'amount_reprogrammed':
                    record.amount_reprogrammed = self.parse_amount(value)
                elif field == 'requesting_org':
                    record.requesting_organization = value
                elif field == 'approving_auth':
                    record.approving_authority = value
                elif field == 'source_fund':
                    record.source_fund = value
                elif field == 'target_fund':
                    record.target_fund = value
                elif field == 'reprogramming_type':
                    record.reprogramming_type = value
                elif field == 'justification':
                    record.justification = value
                elif field == 'impact_statement':
                    record.impact_statement = value
        
        # Extract additional data using fallback patterns
        self.extract_additional_data(text, record)
        
        return record
    
    def extract_fiscal_year_from_filename(self, filename: str) -> str:
        """Extract fiscal year from filename"""
        match = re.search(r'FY_(\d{4})', filename)
        return match.group(1) if match else "Unknown"
    
    def extract_document_type_from_filename(self, filename: str) -> str:
        """Extract document type from filename"""
        if 'Base_for_Reprogramming_Actions' in filename:
            return 'Base_for_Reprogramming_Actions'
        elif 'Call_Memo' in filename:
            return 'Call_Memo'
        elif 'Service_Call_Memo' in filename:
            return 'Service_Call_Memo'
        elif 'Defense_Wide_Call_Memo' in filename:
            return 'Defense_Wide_Call_Memo'
        else:
            return 'Unknown'
    
    def parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse amount string to float"""
        try:
            # Remove commas and dollar signs
            cleaned = re.sub(r'[,$]', '', amount_str)
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    
    def extract_additional_data(self, text: str, record: DD1414Record):
        """Extract additional data using fallback patterns"""
        
        # Try to find dates
        for pattern in self.field_patterns['date_patterns']:
            matches = re.findall(pattern, text)
            if matches and not record.submission_date:
                record.submission_date = matches[0]
                break
        
        # Try to find amounts
        for pattern in self.field_patterns['amount_patterns']:
            matches = re.findall(pattern, text)
            if matches and not record.total_amount:
                try:
                    record.total_amount = self.parse_amount(matches[0])
                    break
                except:
                    continue
        
        # Try to find organizations
        for pattern in self.field_patterns['organization_patterns']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches and not record.requesting_organization:
                record.requesting_organization = matches[0]
                break
    
    def process_dd1414_pdf(self, pdf_path: Path) -> Optional[DD1414Record]:
        """Process a single DD1414 PDF file"""
        logger.info(f"Processing DD1414 PDF: {pdf_path.name}")
        
        try:
            # Get file info
            file_size = pdf_path.stat().st_size
            
            # Extract text
            text = self.extract_text_from_pdf(pdf_path)
            
            # If text extraction failed, try OCR
            if not text.strip():
                logger.info(f"Text extraction failed, trying OCR for {pdf_path.name}")
                text = self.extract_text_with_ocr(pdf_path)
            
            if not text.strip():
                logger.warning(f"No text extracted from {pdf_path.name}")
                return None
            
            # Parse the data
            record = self.parse_dd1414_data(text, pdf_path.name)
            
            # Add file metadata
            record.file_size = file_size
            record.page_count = self.get_page_count(pdf_path)
            
            logger.info(f"Successfully processed {pdf_path.name}")
            return record
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {e}")
            return None
    
    def get_page_count(self, pdf_path: Path) -> Optional[int]:
        """Get page count of PDF"""
        try:
            doc = fitz.open(pdf_path)
            count = doc.page_count
            doc.close()
            return count
        except:
            return None
    
    def find_dd1414_pdfs(self) -> List[Path]:
        """Find all DD1414 PDF files"""
        pattern = "FY_*_DD_1414_*.pdf"
        return list(self.input_dir.glob(pattern))
    
    def save_to_csv(self, records: List[DD1414Record], output_file: str = "dd1414_data.csv"):
        """Save records to CSV file"""
        output_path = self.output_dir / output_file
        
        if not records:
            logger.warning("No records to save")
            return
        
        # Convert to list of dictionaries
        data = [asdict(record) for record in records]
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(records)} records to {output_path}")
        
        # Also save as JSON for backup
        json_path = self.output_dir / "dd1414_data.json"
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved JSON backup to {json_path}")
    
    def run_scraper(self, test_mode: bool = False):
        """Run the DD1414 scraper"""
        logger.info("Starting DD1414 scraper...")
        
        # Find DD1414 PDFs
        pdf_files = self.find_dd1414_pdfs()
        logger.info(f"Found {len(pdf_files)} DD1414 PDF files")
        
        if test_mode:
            pdf_files = pdf_files[:3]  # Test with first 3 files
            logger.info(f"Test mode: Processing only {len(pdf_files)} files")
        
        # Process each PDF
        records = []
        for pdf_path in pdf_files:
            record = self.process_dd1414_pdf(pdf_path)
            if record:
                records.append(record)
        
        # Save results
        if records:
            self.save_to_csv(records)
            
            # Print summary
            logger.info(f"\n📊 DD1414 Scraping Summary:")
            logger.info(f"Total files processed: {len(pdf_files)}")
            logger.info(f"Successful extractions: {len(records)}")
            logger.info(f"Success rate: {len(records)/len(pdf_files)*100:.1f}%")
            
            # Show sample data
            if records:
                logger.info(f"\n📋 Sample Record:")
                sample = records[0]
                logger.info(f"  File: {sample.filename}")
                logger.info(f"  FY: {sample.fiscal_year}")
                logger.info(f"  Type: {sample.document_type}")
                logger.info(f"  Amount: ${sample.total_amount}")
                logger.info(f"  Organization: {sample.requesting_organization}")
        else:
            logger.warning("No records extracted")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DD1414 Form Data Extractor")
    parser.add_argument("--input-dir", default="data/pdfs", help="Input directory containing PDFs")
    parser.add_argument("--output-dir", default="data/dd1414_csv", help="Output directory for CSV files")
    parser.add_argument("--test", action="store_true", help="Test mode (process only first 3 files)")
    
    args = parser.parse_args()
    
    # Create scraper
    scraper = DD1414Scraper(args.input_dir, args.output_dir)
    
    # Run scraper
    scraper.run_scraper(test_mode=args.test)

if __name__ == "__main__":
    main()