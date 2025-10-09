#!/usr/bin/env python3
"""
Fast DD1414 Form Data Extractor

This script quickly extracts key data from DD1414 PDF forms and converts it to CSV format.
Optimized for speed by focusing on essential fields and using efficient text extraction.
"""

import os
import re
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import fitz  # PyMuPDF
import pandas as pd
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DD1414Record:
    """Data structure for DD1414 form records"""
    # File information
    filename: str
    fiscal_year: str
    document_type: str
    
    # Basic form info
    form_number: str = "DD1414"
    form_title: str = "Reprogramming Action"
    
    # Key financial data
    total_amount: Optional[float] = None
    amount_reprogrammed: Optional[float] = None
    
    # Organization info
    requesting_organization: Optional[str] = None
    
    # Dates
    submission_date: Optional[str] = None
    effective_date: Optional[str] = None
    
    # File metadata
    page_count: Optional[int] = None
    file_size: Optional[int] = None
    extraction_date: str = None
    
    # Additional extracted text (for manual review)
    extracted_text_sample: Optional[str] = None
    
    def __post_init__(self):
        if self.extraction_date is None:
            self.extraction_date = datetime.now().isoformat()

class DD1414FastScraper:
    """Fast scraper for DD1414 forms"""
    
    def __init__(self, input_dir: str = "data/pdfs", output_dir: str = "data/dd1414_csv"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Optimized patterns for key data
        self.patterns = {
            'amount': [
                r'\$?([\d,]+\.?\d*)\s*(?:million|billion|thousand)?',
                r'Amount[:\s]*\$?([\d,]+\.?\d*)',
                r'Total[:\s]*\$?([\d,]+\.?\d*)',
                r'Reprogram[:\s]*\$?([\d,]+\.?\d*)'
            ],
            'date': [
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
                r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}'
            ],
            'organization': [
                r'(Department of Defense|DOD|DoD)',
                r'(Army|Navy|Air Force|Marine Corps)',
                r'(Office of the Secretary|OSD)',
                r'(Comptroller|DFAS)',
                r'(Defense Logistics Agency|DLA)',
                r'(Defense Intelligence Agency|DIA)'
            ]
        }
    
    def extract_text_fast(self, pdf_path: Path) -> str:
        """Fast text extraction using PyMuPDF only"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            # Extract text from first few pages only (most important info is usually at the beginning)
            max_pages = min(5, doc.page_count)
            for page_num in range(max_pages):
                page = doc[page_num]
                text += page.get_text()
            
            doc.close()
            return text
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
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
    
    def extract_key_data(self, text: str, filename: str) -> DD1414Record:
        """Extract key data from DD1414 form text"""
        
        # Extract basic info from filename
        fiscal_year = self.extract_fiscal_year_from_filename(filename)
        document_type = self.extract_document_type_from_filename(filename)
        
        # Initialize record
        record = DD1414Record(
            filename=filename,
            fiscal_year=fiscal_year,
            document_type=document_type
        )
        
        # Extract amounts
        amounts = []
        for pattern in self.patterns['amount']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                amount = self.parse_amount(match)
                if amount and amount > 0:
                    amounts.append(amount)
        
        if amounts:
            # Use the largest amount as total_amount
            record.total_amount = max(amounts)
            if len(amounts) > 1:
                # Use second largest as amount_reprogrammed
                amounts.sort(reverse=True)
                record.amount_reprogrammed = amounts[1]
        
        # Extract dates
        dates = []
        for pattern in self.patterns['date']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        if dates:
            record.submission_date = dates[0]
            if len(dates) > 1:
                record.effective_date = dates[1]
        
        # Extract organization
        for pattern in self.patterns['organization']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                record.requesting_organization = match.group(1)
                break
        
        # Store sample of extracted text for manual review
        record.extracted_text_sample = text[:500] + "..." if len(text) > 500 else text
        
        return record
    
    def process_dd1414_pdf(self, pdf_path: Path) -> Optional[DD1414Record]:
        """Process a single DD1414 PDF file"""
        logger.info(f"Processing: {pdf_path.name}")
        
        try:
            # Get file info
            file_size = pdf_path.stat().st_size
            
            # Extract text (fast method)
            text = self.extract_text_fast(pdf_path)
            
            if not text.strip():
                logger.warning(f"No text extracted from {pdf_path.name}")
                return None
            
            # Parse the data
            record = self.extract_key_data(text, pdf_path.name)
            
            # Add file metadata
            record.file_size = file_size
            record.page_count = self.get_page_count(pdf_path)
            
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
    
    def save_to_csv(self, records: List[DD1414Record], output_file: str = "dd1414_fast_data.csv"):
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
        json_path = self.output_dir / "dd1414_fast_data.json"
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved JSON backup to {json_path}")
        
        # Print summary statistics
        self.print_summary(df)
    
    def print_summary(self, df: pd.DataFrame):
        """Print summary statistics"""
        logger.info(f"\n📊 DD1414 Data Summary:")
        logger.info(f"Total records: {len(df)}")
        logger.info(f"Fiscal years covered: {sorted(df['fiscal_year'].unique())}")
        logger.info(f"Document types: {df['document_type'].value_counts().to_dict()}")
        
        # Financial summary
        total_amounts = df['total_amount'].dropna()
        if len(total_amounts) > 0:
            logger.info(f"Total amounts found: {len(total_amounts)}")
            logger.info(f"Average amount: ${total_amounts.mean():,.2f}")
            logger.info(f"Max amount: ${total_amounts.max():,.2f}")
            logger.info(f"Min amount: ${total_amounts.min():,.2f}")
        
        # Organization summary
        orgs = df['requesting_organization'].dropna()
        if len(orgs) > 0:
            logger.info(f"Organizations found: {orgs.value_counts().to_dict()}")
    
    def run_scraper(self):
        """Run the fast DD1414 scraper"""
        logger.info("Starting fast DD1414 scraper...")
        
        # Find DD1414 PDFs
        pdf_files = self.find_dd1414_pdfs()
        logger.info(f"Found {len(pdf_files)} DD1414 PDF files")
        
        # Process each PDF
        records = []
        for i, pdf_path in enumerate(pdf_files, 1):
            logger.info(f"Processing {i}/{len(pdf_files)}: {pdf_path.name}")
            record = self.process_dd1414_pdf(pdf_path)
            if record:
                records.append(record)
        
        # Save results
        if records:
            self.save_to_csv(records)
            logger.info(f"\n✅ Successfully processed {len(records)} out of {len(pdf_files)} files")
        else:
            logger.warning("No records extracted")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fast DD1414 Form Data Extractor")
    parser.add_argument("--input-dir", default="data/pdfs", help="Input directory containing PDFs")
    parser.add_argument("--output-dir", default="data/dd1414_csv", help="Output directory for CSV files")
    
    args = parser.parse_args()
    
    # Create scraper
    scraper = DD1414FastScraper(args.input_dir, args.output_dir)
    
    # Run scraper
    scraper.run_scraper()

if __name__ == "__main__":
    main()