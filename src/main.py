#!/usr/bin/env python3
"""
Main orchestration script for comptroller.war.gov data extraction
Downloads PDFs, runs OCR, generates CSV, and validates results
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any

from download_pdfs import ComptrollerScraper
from ocr_processor import OCRProcessor
from csv_transformer import CSVTransformer
from llm_validator import LLMValidator


def load_config() -> Dict[str, Any]:
    """Load configuration from environment"""
    return {
        'ocr_engine': os.getenv('OCR_ENGINE', 'tesseract'),
        'llm_provider': os.getenv('LLM_PROVIDER', 'openai'),
        'llm_model': os.getenv('LLM_MODEL'),
        'max_downloads': int(os.getenv('MAX_CONCURRENT_DOWNLOADS', '10')),
        'validate_with_llm': os.getenv('ANTHROPIC_API_KEY') or os.getenv('OPENAI_API_KEY'),
    }


def main():
    parser = argparse.ArgumentParser(
        description='Download and process comptroller.war.gov appropriation documents'
    )
    parser.add_argument('--download-only', action='store_true',
                       help='Only download PDFs, skip processing')
    parser.add_argument('--process-only', action='store_true',
                       help='Only process existing PDFs, skip download')
    parser.add_argument('--no-validate', action='store_true',
                       help='Skip LLM validation')
    parser.add_argument('--max-downloads', type=int,
                       help='Maximum number of new downloads')
    parser.add_argument('--pdf-dir', default='data/pdfs',
                       help='PDF directory')
    parser.add_argument('--csv-dir', default='data/csv',
                       help='CSV output directory')
    parser.add_argument('--validation-dir', default='data/validation',
                       help='Validation output directory')
    
    args = parser.parse_args()
    config = load_config()
    
    print("=" * 80)
    print("Comptroller.war.gov Data Extraction Pipeline")
    print("=" * 80)
    
    # Step 1: Download PDFs
    if not args.process_only:
        print("\n📥 Step 1: Downloading PDFs...")
        scraper = ComptrollerScraper(
            output_dir=args.pdf_dir,
            metadata_file='data/metadata.json'
        )
        download_results = scraper.run(max_downloads=args.max_downloads or config['max_downloads'])
        
        if download_results['downloaded'] == 0 and not args.download_only:
            print("No new documents to process.")
            if download_results['failed'] == 0:
                return 0
    
    if args.download_only:
        print("\n✅ Download complete!")
        return 0
    
    # Step 2: Find PDFs to process
    print("\n🔍 Step 2: Finding PDFs to process...")
    pdf_dir = Path(args.pdf_dir)
    pdf_files = list(pdf_dir.glob('*.pdf'))
    
    if not pdf_files:
        print("No PDF files found!")
        return 1
    
    print(f"Found {len(pdf_files)} PDF files")
    
    # Load metadata to check what's already processed
    metadata_file = Path('data/metadata.json')
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Ensure processed_files key exists
        if 'processed_files' not in metadata:
            metadata['processed_files'] = {}
        
        processed_files = metadata.get('processed_files', {})
        
        # Filter to unprocessed files
        pdf_files = [
            pdf for pdf in pdf_files 
            if pdf.name not in processed_files or not processed_files[pdf.name].get('csv_generated')
        ]
        
        if not pdf_files:
            print("All PDFs already processed!")
            return 0
        
        print(f"{len(pdf_files)} PDFs need processing")
    else:
        metadata = {'processed_files': {}}
    
    # Step 3: OCR Processing
    print(f"\n📄 Step 3: Running OCR on {len(pdf_files)} PDFs...")
    processor = OCRProcessor(engine=config['ocr_engine'])
    ocr_results = processor.batch_process([str(pdf) for pdf in pdf_files], use_ocr=True)
    
    # Step 4: CSV Transformation
    print(f"\n📊 Step 4: Transforming to CSV...")
    transformer = CSVTransformer()
    csv_files = transformer.batch_transform(ocr_results, output_dir=args.csv_dir)
    
    print(f"✓ Generated {len(csv_files)} CSV files")
    
    # Step 5: LLM Validation
    if not args.no_validate and config['validate_with_llm']:
        print(f"\n🤖 Step 5: Validating with LLM...")
        try:
            validator = LLMValidator(
                provider=config['llm_provider'],
                model=config['llm_model']
            )
            validation_reports = validator.batch_validate(
                csv_files, ocr_results, 
                output_dir=args.validation_dir
            )
            
            # Update metadata with processing status
            for pdf_file, csv_file, report in zip(pdf_files, csv_files, validation_reports):
                metadata['processed_files'][pdf_file.name] = {
                    'pdf_path': str(pdf_file),
                    'csv_path': csv_file,
                    'csv_generated': True,
                    'validated': True,
                    'validation_passed': report['passed'],
                    'accuracy_score': report['overall_score'],
                    'processed_at': report['timestamp']
                }
            
        except Exception as e:
            print(f"⚠️  LLM validation failed: {e}")
            print("Continuing without validation...")
            
            # Update metadata without validation
            for pdf_file, csv_file in zip(pdf_files, csv_files):
                metadata['processed_files'][pdf_file.name] = {
                    'pdf_path': str(pdf_file),
                    'csv_path': csv_file,
                    'csv_generated': True,
                    'validated': False
                }
    else:
        print("\n⏩ Skipping LLM validation")
        
        # Update metadata without validation
        for pdf_file, csv_file in zip(pdf_files, csv_files):
            metadata['processed_files'][pdf_file.name] = {
                'pdf_path': str(pdf_file),
                'csv_path': csv_file,
                'csv_generated': True,
                'validated': False
            }
    
    # Save updated metadata
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "=" * 80)
    print("✅ Pipeline Complete!")
    print("=" * 80)
    print(f"   PDFs processed: {len(pdf_files)}")
    print(f"   CSV files generated: {len(csv_files)}")
    print(f"   Output directory: {args.csv_dir}")
    
    return 0


if __name__ == '__main__':
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
