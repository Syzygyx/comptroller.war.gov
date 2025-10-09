#!/usr/bin/env python3
"""
Manual Firecrawl scraper runner
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from firecrawl_scraper import FirecrawlComptrollerScraper

async def main():
    """Run the Firecrawl scraper manually"""
    
    parser = argparse.ArgumentParser(description='Run Firecrawl scraper manually')
    parser.add_argument('--max-pages', type=int, default=50, help='Max pages per URL')
    parser.add_argument('--max-concurrent', type=int, default=5, help='Max concurrent requests')
    parser.add_argument('--output-dir', default='data/pdfs', help='Output directory for PDFs')
    parser.add_argument('--metadata-file', default='data/metadata.json', help='Metadata file')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode with limited URLs')
    
    args = parser.parse_args()
    
    print("🔥 Firecrawl Manual Scraper")
    print("=" * 40)
    
    # Check if API key is available
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv('FIRECRAWL_API_KEY'):
        print("❌ FIRECRAWL_API_KEY not found")
        print("   Please run: python setup_firecrawl.py")
        return 1
    
    try:
        # Create scraper instance
        scraper = FirecrawlComptrollerScraper(
            output_dir=args.output_dir,
            metadata_file=args.metadata_file
        )
        
        if args.test_mode:
            print("🧪 Running in test mode...")
            # Test with just a few URLs
            test_urls = [
                "https://comptroller.defense.gov/Budget-Execution/Reprogramming/",
                "https://comptroller.defense.gov/Portals/45/Documents/execution/reprogramming/fy2024/"
            ]
            
            for url in test_urls:
                result = await scraper.scrape_url(url, max_pages=5)
                if result['success']:
                    print(f"✅ {url}: {len(result.get('pdf_links', []))} PDFs found")
                else:
                    print(f"❌ {url}: {result.get('error', 'Unknown error')}")
        else:
            print("🚀 Running full scraping...")
            # Run comprehensive scraping
            results = await scraper.run_comprehensive_scrape(
                max_pages_per_url=args.max_pages,
                max_concurrent=args.max_concurrent
            )
            
            if results['success']:
                print("\n🎉 Scraping completed successfully!")
                print(f"📊 Pages scraped: {results['pages_scraped']}")
                print(f"📊 PDFs found: {results['pdfs_found']}")
                print(f"📊 PDFs downloaded: {results['pdfs_downloaded']}")
                print(f"📊 Errors: {results['errors']}")
            else:
                print("\n❌ Scraping completed with errors")
                return 1
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))