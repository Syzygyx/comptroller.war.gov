#!/usr/bin/env python3
"""
OCR Processor - Adapted from StealthOCR
Extracts text from PDF documents using Tesseract and EasyOCR
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

import cv2
import numpy as np
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from PyPDF2 import PdfReader

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False


class OCRProcessor:
    """Multi-engine OCR processor for PDF documents"""
    
    def __init__(self, engine: str = 'tesseract', tesseract_path: Optional[str] = None):
        """
        Initialize OCR processor
        
        Args:
            engine: OCR engine to use ('tesseract', 'easyocr', or 'both')
            tesseract_path: Path to Tesseract executable (auto-detected on macOS)
        """
        self.engine = engine
        
        # Configure Tesseract
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        else:
            # Auto-detect on macOS
            self._auto_detect_tesseract()
        
        # Initialize EasyOCR if needed
        self.easyocr_reader = None
        if engine in ['easyocr', 'both']:
            if EASYOCR_AVAILABLE:
                print("Initializing EasyOCR (this may take a moment)...")
                self.easyocr_reader = easyocr.Reader(['en'], gpu=False)
            else:
                print("Warning: EasyOCR not available, falling back to Tesseract")
                self.engine = 'tesseract'
    
    def _auto_detect_tesseract(self):
        """Auto-detect Tesseract installation on macOS"""
        possible_paths = [
            '/opt/homebrew/bin/tesseract',
            '/usr/local/bin/tesseract',
            '/usr/bin/tesseract'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"Tesseract found at: {path}")
                return
        
        # Try to find in PATH
        try:
            result = subprocess.run(['which', 'tesseract'], 
                                  capture_output=True, text=True, check=True)
            path = result.stdout.strip()
            if path:
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"Tesseract found at: {path}")
                return
        except subprocess.CalledProcessError:
            pass
        
        print("Warning: Tesseract not found. Please install or specify path.")
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        return thresh
    
    def extract_text_tesseract(self, image: Union[str, np.ndarray]) -> str:
        """
        Extract text using Tesseract OCR
        
        Args:
            image: Image path or numpy array
            
        Returns:
            Extracted text
        """
        if isinstance(image, str):
            image = cv2.imread(image)
        
        # Preprocess image
        processed = self.preprocess_image(image)
        
        # Extract text
        text = pytesseract.image_to_string(processed, config='--psm 1')
        
        return text.strip()
    
    def extract_text_easyocr(self, image: Union[str, np.ndarray]) -> str:
        """
        Extract text using EasyOCR
        
        Args:
            image: Image path or numpy array
            
        Returns:
            Extracted text
        """
        if not self.easyocr_reader:
            raise RuntimeError("EasyOCR not initialized")
        
        # EasyOCR can handle both paths and numpy arrays
        results = self.easyocr_reader.readtext(image)
        
        # Combine all detected text
        text = ' '.join([detection[1] for detection in results])
        
        return text.strip()
    
    def extract_text_from_image(self, image: Union[str, np.ndarray]) -> str:
        """
        Extract text from image using configured engine
        
        Args:
            image: Image path or numpy array
            
        Returns:
            Extracted text
        """
        if self.engine == 'tesseract':
            return self.extract_text_tesseract(image)
        elif self.engine == 'easyocr':
            return self.extract_text_easyocr(image)
        elif self.engine == 'both':
            # Try Tesseract first, fall back to EasyOCR if needed
            try:
                text_tesseract = self.extract_text_tesseract(image)
                if len(text_tesseract) > 50:  # Tesseract got good results
                    return text_tesseract
                # Try EasyOCR for better results
                return self.extract_text_easyocr(image)
            except Exception as e:
                print(f"Tesseract failed, trying EasyOCR: {e}")
                return self.extract_text_easyocr(image)
        else:
            raise ValueError(f"Unknown engine: {self.engine}")
    
    def extract_from_pdf(self, pdf_path: str, use_ocr: bool = True) -> Dict[str, Any]:
        """
        Extract text from PDF document
        
        Args:
            pdf_path: Path to PDF file
            use_ocr: Whether to use OCR (True) or try text extraction first (False)
            
        Returns:
            Dictionary with extracted text and metadata
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        print(f"Processing: {pdf_path.name}")
        
        result = {
            'file': pdf_path.name,
            'path': str(pdf_path),
            'text': '',
            'pages_processed': 0,
            'engine': self.engine,
            'method': 'ocr' if use_ocr else 'text_extraction'
        }
        
        # Try text extraction first (faster)
        if not use_ocr:
            try:
                reader = PdfReader(str(pdf_path))
                text = ''
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
                
                if len(text.strip()) > 100:  # Got meaningful text
                    result['text'] = text.strip()
                    result['pages_processed'] = len(reader.pages)
                    result['character_count'] = len(result['text'])
                    result['word_count'] = len(result['text'].split())
                    print(f"✓ Text extraction successful: {result['character_count']} characters")
                    return result
                else:
                    print("Text extraction yielded insufficient text, switching to OCR...")
            except Exception as e:
                print(f"Text extraction failed: {e}, switching to OCR...")
        
        # Use OCR
        try:
            # Convert PDF to images
            print("Converting PDF to images...")
            images = convert_from_path(str(pdf_path), dpi=300)
            
            print(f"Processing {len(images)} pages with OCR...")
            all_text = []
            
            for i, image in enumerate(images, 1):
                print(f"  Page {i}/{len(images)}...", end=' ')
                
                # Convert PIL Image to numpy array
                opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                
                # Extract text
                page_text = self.extract_text_from_image(opencv_image)
                all_text.append(f"\n--- Page {i} ---\n{page_text}")
                
                print(f"✓ ({len(page_text)} chars)")
            
            result['text'] = '\n'.join(all_text).strip()
            result['pages_processed'] = len(images)
            result['character_count'] = len(result['text'])
            result['word_count'] = len(result['text'].split())
            result['line_count'] = len(result['text'].split('\n'))
            
            print(f"✅ OCR complete: {result['character_count']} characters, {result['word_count']} words")
            
        except Exception as e:
            print(f"❌ Error processing PDF: {e}")
            result['error'] = str(e)
        
        return result
    
    def batch_process(self, pdf_paths: List[str], use_ocr: bool = True) -> List[Dict[str, Any]]:
        """
        Process multiple PDF files
        
        Args:
            pdf_paths: List of PDF file paths
            use_ocr: Whether to use OCR
            
        Returns:
            List of results for each PDF
        """
        results = []
        
        for i, pdf_path in enumerate(pdf_paths, 1):
            print(f"\n[{i}/{len(pdf_paths)}] Processing {pdf_path}...")
            result = self.extract_from_pdf(pdf_path, use_ocr=use_ocr)
            results.append(result)
        
        return results


def main():
    """Main entry point for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract text from PDF using OCR')
    parser.add_argument('pdf', help='Path to PDF file')
    parser.add_argument('--engine', choices=['tesseract', 'easyocr', 'both'], 
                       default='tesseract', help='OCR engine to use')
    parser.add_argument('--no-ocr', action='store_true', 
                       help='Try text extraction first')
    parser.add_argument('--output', help='Output text file')
    
    args = parser.parse_args()
    
    processor = OCRProcessor(engine=args.engine)
    result = processor.extract_from_pdf(args.pdf, use_ocr=not args.no_ocr)
    
    if 'error' in result:
        print(f"Error: {result['error']}")
        return 1
    
    print(f"\nExtracted text:")
    print("=" * 80)
    print(result['text'][:500] + "..." if len(result['text']) > 500 else result['text'])
    print("=" * 80)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(result['text'])
        print(f"\n✓ Saved to: {args.output}")
    
    return 0


if __name__ == '__main__':
    exit(main())
