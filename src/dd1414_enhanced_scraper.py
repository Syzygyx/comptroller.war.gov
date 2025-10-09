#!/usr/bin/env python3
"""
Enhanced DD1414 Form Data Extractor with Advanced OCR

This script extracts structured data from DD1414 PDF forms using advanced OCR techniques
and improved pattern matching for better accuracy.
"""

import os
import re
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import fitz  # PyMuPDF
import pandas as pd
from datetime import datetime
import io
import numpy as np
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DD1414Record:
    """Enhanced data structure for DD1414 form records"""
    # File information
    filename: str
    fiscal_year: str
    document_type: str
    
    # Basic form info
    form_number: str = "DD1414"
    form_title: str = "Reprogramming Action"
    
    # Financial data
    total_amount: Optional[float] = None
    amount_reprogrammed: Optional[float] = None
    source_fund: Optional[str] = None
    target_fund: Optional[str] = None
    
    # Organization info
    requesting_organization: Optional[str] = None
    approving_authority: Optional[str] = None
    
    # Dates
    submission_date: Optional[str] = None
    effective_date: Optional[str] = None
    fiscal_year_covered: Optional[str] = None
    
    # Reprogramming details
    reprogramming_type: Optional[str] = None
    justification: Optional[str] = None
    impact_statement: Optional[str] = None
    
    # File metadata
    page_count: Optional[int] = None
    file_size: Optional[int] = None
    extraction_method: Optional[str] = None  # 'text', 'ocr', 'hybrid'
    confidence_score: Optional[float] = None
    
    # Additional extracted text
    extracted_text_sample: Optional[str] = None
    
    # Extraction date
    extraction_date: str = None
    
    def __post_init__(self):
        if self.extraction_date is None:
            self.extraction_date = datetime.now().isoformat()

class DD1414EnhancedScraper:
    """Enhanced scraper for DD1414 forms with advanced OCR"""
    
    def __init__(self, input_dir: str = "data/pdfs", output_dir: str = "data/dd1414_csv"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Enhanced patterns for DD1414 forms
        self.patterns = {
            # Financial patterns
            'amount': [
                r'\$?([\d,]+\.?\d*)\s*(?:million|billion|thousand)?',
                r'Amount[:\s]*\$?([\d,]+\.?\d*)',
                r'Total[:\s]*\$?([\d,]+\.?\d*)',
                r'Reprogram[:\s]*\$?([\d,]+\.?\d*)',
                r'Value[:\s]*\$?([\d,]+\.?\d*)',
                r'Cost[:\s]*\$?([\d,]+\.?\d*)',
                r'Budget[:\s]*\$?([\d,]+\.?\d*)',
                r'Funding[:\s]*\$?([\d,]+\.?\d*)',
                r'Allocation[:\s]*\$?([\d,]+\.?\d*)',
                r'Transfer[:\s]*\$?([\d,]+\.?\d*)'
            ],
            
            # Date patterns
            'date': [
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
                r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
                r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
                r'Submission\s+Date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'Effective\s+Date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'Date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ],
            
            # Organization patterns
            'organization': [
                r'(Department of Defense|DOD|DoD)',
                r'(Office of the Secretary|OSD)',
                r'(Army|Navy|Air Force|Marine Corps)',
                r'(Comptroller|DFAS)',
                r'(Defense Logistics Agency|DLA)',
                r'(Defense Intelligence Agency|DIA)',
                r'(Defense Advanced Research Projects Agency|DARPA)',
                r'(Defense Contract Management Agency|DCMA)',
                r'(Defense Information Systems Agency|DISA)',
                r'(Defense Security Cooperation Agency|DSCA)',
                r'(Defense Threat Reduction Agency|DTRA)',
                r'(Missile Defense Agency|MDA)',
                r'(National Geospatial-Intelligence Agency|NGA)',
                r'(National Security Agency|NSA)',
                r'(Pentagon Force Protection Agency|PFPA)'
            ],
            
            # Reprogramming patterns
            'reprogramming_type': [
                r'Reprogramming\s+Type[:\s]*([^\n\r]+)',
                r'Type[:\s]*([^\n\r]+)',
                r'(Congressional|Administrative|Emergency|Routine)\s+Reprogramming',
                r'(Base|Call|Omnibus)\s+Reprogramming'
            ],
            
            # Fund patterns
            'fund': [
                r'Source\s+Fund[:\s]*([^\n\r]+)',
                r'Target\s+Fund[:\s]*([^\n\r]+)',
                r'From[:\s]*([^\n\r]+)',
                r'To[:\s]*([^\n\r]+)',
                r'Account[:\s]*([^\n\r]+)',
                r'Program[:\s]*([^\n\r]+)'
            ],
            
            # Justification patterns
            'justification': [
                r'Justification[:\s]*([^\n\r]+)',
                r'Reason[:\s]*([^\n\r]+)',
                r'Purpose[:\s]*([^\n\r]+)',
                r'Rationale[:\s]*([^\n\r]+)'
            ]
        }
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR accuracy"""
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            # Apply slight blur to reduce noise
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            # Resize if too small
            width, height = image.size
            if width < 1000 or height < 1000:
                scale_factor = max(1000 / width, 1000 / height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            return image
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}")
            return image
    
    def extract_text_with_enhanced_ocr(self, pdf_path: Path) -> Tuple[str, float]:
        """Extract text using enhanced OCR with confidence scoring"""
        try:
            doc = fitz.open(pdf_path)
            full_text = ""
            confidence_scores = []
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                
                # Convert page to image with high resolution
                mat = fitz.Matrix(3.0, 3.0)  # 3x zoom for better OCR
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Convert to PIL Image
                image = Image.open(io.BytesIO(img_data))
                
                # Preprocess image
                processed_image = self.preprocess_image(image)
                
                # Extract text using OCR with confidence
                try:
                    # Try with confidence data
                    data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)
                    page_text = ""
                    page_confidence = []
                    
                    for i, conf in enumerate(data['conf']):
                        if int(conf) > 30:  # Only include high-confidence text
                            page_text += data['text'][i] + " "
                            page_confidence.append(int(conf))
                    
                    full_text += page_text + "\n"
                    if page_confidence:
                        confidence_scores.extend(page_confidence)
                        
                except:
                    # Fallback to basic OCR
                    page_text = pytesseract.image_to_string(processed_image)
                    full_text += page_text + "\n"
                    confidence_scores.append(50)  # Default confidence
            
            doc.close()
            
            # Calculate average confidence
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
            return full_text.strip(), avg_confidence
            
        except Exception as e:
            logger.error(f"Enhanced OCR failed for {pdf_path}: {e}")
            return "", 0.0
    
    def extract_text_hybrid(self, pdf_path: Path) -> Tuple[str, str, float]:
        """Hybrid text extraction: try text first, then OCR"""
        try:
            # First try direct text extraction
            doc = fitz.open(pdf_path)
            text = ""
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text += page.get_text()
            
            doc.close()
            
            if text.strip():
                return text, "text", 100.0
            
            # If no text, try OCR
            logger.info(f"Direct text extraction failed, trying OCR for {pdf_path.name}")
            ocr_text, confidence = self.extract_text_with_enhanced_ocr(pdf_path)
            return ocr_text, "ocr", confidence
            
        except Exception as e:
            logger.error(f"Hybrid extraction failed for {pdf_path}: {e}")
            return "", "failed", 0.0
    
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
        """Parse amount string to float with better handling"""
        try:
            # Remove common prefixes and suffixes
            cleaned = re.sub(r'[,$\s]', '', amount_str)
            
            # Handle million, billion, thousand
            if 'million' in amount_str.lower():
                cleaned = cleaned.replace('million', '')
                multiplier = 1000000
            elif 'billion' in amount_str.lower():
                cleaned = cleaned.replace('billion', '')
                multiplier = 1000000000
            elif 'thousand' in amount_str.lower():
                cleaned = cleaned.replace('thousand', '')
                multiplier = 1000
            else:
                multiplier = 1
            
            # Extract number
            number_match = re.search(r'(\d+\.?\d*)', cleaned)
            if number_match:
                return float(number_match.group(1)) * multiplier
            
            return None
        except (ValueError, TypeError):
            return None
    
    def extract_enhanced_data(self, text: str, filename: str, method: str, confidence: float) -> DD1414Record:
        """Extract enhanced data from DD1414 form text"""
        
        # Extract basic info from filename
        fiscal_year = self.extract_fiscal_year_from_filename(filename)
        document_type = self.extract_document_type_from_filename(filename)
        
        # Initialize record
        record = DD1414Record(
            filename=filename,
            fiscal_year=fiscal_year,
            document_type=document_type,
            extraction_method=method,
            confidence_score=confidence
        )
        
        # Extract amounts with better pattern matching
        amounts = []
        for pattern in self.patterns['amount']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                amount = self.parse_amount(match)
                if amount and amount > 0:
                    amounts.append(amount)
        
        if amounts:
            # Sort amounts and assign
            amounts.sort(reverse=True)
            record.total_amount = amounts[0]
            if len(amounts) > 1:
                record.amount_reprogrammed = amounts[1]
        
        # Extract dates with better pattern matching
        dates = []
        for pattern in self.patterns['date']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        if dates:
            record.submission_date = dates[0]
            if len(dates) > 1:
                record.effective_date = dates[1]
        
        # Extract organization with better pattern matching
        for pattern in self.patterns['organization']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                record.requesting_organization = match.group(1)
                break
        
        # Extract reprogramming type
        for pattern in self.patterns['reprogramming_type']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                record.reprogramming_type = match.group(1).strip()
                break
        
        # Extract fund information
        for pattern in self.patterns['fund']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if 'source' in pattern.lower():
                    record.source_fund = match.group(1).strip()
                elif 'target' in pattern.lower():
                    record.target_fund = match.group(1).strip()
                break
        
        # Extract justification
        for pattern in self.patterns['justification']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                record.justification = match.group(1).strip()
                break
        
        # Store sample of extracted text
        record.extracted_text_sample = text[:1000] + "..." if len(text) > 1000 else text
        
        return record
    
    def process_dd1414_pdf(self, pdf_path: Path) -> Optional[DD1414Record]:
        """Process a single DD1414 PDF file with enhanced extraction"""
        logger.info(f"Processing: {pdf_path.name}")
        
        try:
            # Get file info
            file_size = pdf_path.stat().st_size
            
            # Extract text using hybrid method
            text, method, confidence = self.extract_text_hybrid(pdf_path)
            
            if not text.strip():
                logger.warning(f"No text extracted from {pdf_path.name}")
                return None
            
            # Parse the data
            record = self.extract_enhanced_data(text, pdf_path.name, method, confidence)
            
            # Add file metadata
            record.file_size = file_size
            record.page_count = self.get_page_count(pdf_path)
            
            logger.info(f"Successfully processed {pdf_path.name} using {method} (confidence: {confidence:.1f}%)")
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
    
    def save_to_csv(self, records: List[DD1414Record], output_file: str = "dd1414_enhanced_data.csv"):
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
        json_path = self.output_dir / "dd1414_enhanced_data.json"
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved JSON backup to {json_path}")
        
        # Print enhanced summary
        self.print_enhanced_summary(df)
    
    def print_enhanced_summary(self, df: pd.DataFrame):
        """Print enhanced summary statistics"""
        logger.info(f"\n📊 Enhanced DD1414 Data Summary:")
        logger.info(f"Total records: {len(df)}")
        logger.info(f"Fiscal years covered: {sorted(df['fiscal_year'].unique())}")
        logger.info(f"Document types: {df['document_type'].value_counts().to_dict()}")
        
        # Extraction method summary
        if 'extraction_method' in df.columns:
            method_counts = df['extraction_method'].value_counts()
            logger.info(f"Extraction methods: {method_counts.to_dict()}")
        
        # Confidence summary
        if 'confidence_score' in df.columns:
            conf_scores = df['confidence_score'].dropna()
            if len(conf_scores) > 0:
                logger.info(f"Average confidence: {conf_scores.mean():.1f}%")
                logger.info(f"Min confidence: {conf_scores.min():.1f}%")
                logger.info(f"Max confidence: {conf_scores.max():.1f}%")
        
        # Financial summary
        total_amounts = df['total_amount'].dropna()
        if len(total_amounts) > 0:
            logger.info(f"Total amounts found: {len(total_amounts)}")
            logger.info(f"Average amount: ${total_amounts.mean():,.2f}")
            logger.info(f"Max amount: ${total_amounts.max():,.2f}")
            logger.info(f"Min amount: ${total_amounts.min():,.2f}")
            logger.info(f"Total value: ${total_amounts.sum():,.2f}")
        
        # Organization summary
        orgs = df['requesting_organization'].dropna()
        if len(orgs) > 0:
            logger.info(f"Organizations found: {orgs.value_counts().to_dict()}")
        
        # Reprogramming type summary
        if 'reprogramming_type' in df.columns:
            types = df['reprogramming_type'].dropna()
            if len(types) > 0:
                logger.info(f"Reprogramming types: {types.value_counts().to_dict()}")
    
    def run_enhanced_scraper(self, test_mode: bool = False):
        """Run the enhanced DD1414 scraper"""
        logger.info("Starting enhanced DD1414 scraper...")
        
        # Find DD1414 PDFs
        pdf_files = self.find_dd1414_pdfs()
        logger.info(f"Found {len(pdf_files)} DD1414 PDF files")
        
        if test_mode:
            pdf_files = pdf_files[:5]  # Test with first 5 files
            logger.info(f"Test mode: Processing only {len(pdf_files)} files")
        
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
    
    parser = argparse.ArgumentParser(description="Enhanced DD1414 Form Data Extractor")
    parser.add_argument("--input-dir", default="data/pdfs", help="Input directory containing PDFs")
    parser.add_argument("--output-dir", default="data/dd1414_csv", help="Output directory for CSV files")
    parser.add_argument("--test", action="store_true", help="Test mode (process only first 5 files)")
    
    args = parser.parse_args()
    
    # Create scraper
    scraper = DD1414EnhancedScraper(args.input_dir, args.output_dir)
    
    # Run scraper
    scraper.run_enhanced_scraper(test_mode=args.test)

if __name__ == "__main__":
    main()