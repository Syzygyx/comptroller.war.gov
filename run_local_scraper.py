#!/usr/bin/env python3
"""
Local scraper runner - no API required
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from local_firecrawl_scraper import LocalFirecrawlScraper

async def main():
    """Run the local scraper"""
    
    parser = argparse.ArgumentParser(description='Run local scraper (no API required)')
    parser.add_argument('--max-pages', type=int, default=50, help='Max pages per URL')
    parser.add_argument('--max-concurrent', type=int, default=3, help='Max concurrent requests')
    parser.add_argument('--output-dir', default='data/pdfs', help='Output directory for PDFs')
    parser.add_argument('--metadata-file', default='data/metadata.json', help='Metadata file')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode with limited URLs')
    parser.add_argument('--years', nargs='+', type=int, help='Specific years to scrape (e.g., --years 2020 2021 2022)')
    
    args = parser.parse_args()
    
    print("🔥 Local Scraper (No API Required)")
    print("=" * 40)
    
    try:
        # Create scraper instance
        scraper = LocalFirecrawlScraper(
            output_dir=args.output_dir,
            metadata_file=args.metadata_file
        )
        
        # Filter URLs by years if specified
        if args.years:
            print(f"🎯 Filtering to years: {args.years}")
            filtered_urls = []
            for url in scraper.target_urls:
                for year in args.years:
                    if f"fy{year}" in url:
                        filtered_urls.append(url)
                        break
            scraper.target_urls = filtered_urls
            print(f"📊 Filtered to {len(scraper.target_urls)} URLs")
        
        if args.test_mode:
            print("🧪 Running in test mode...")
            # Test with just a few URLs
            test_urls = [
                "https://comptroller.defense.gov/Budget-Execution/Reprogramming/",
                "https://comptroller.defense.gov/Portals/45/Documents/execution/reprogramming/fy2024/"
            ]
            
            for url in test_urls:
                result = await scraper.scrape_url_with_playwright(url, max_pages=5)
                if result['success']:
                    print(f"✅ {url}: {len(result.get('pdf_links', []))} PDFs found")
                else:
                    print(f"❌ {url}: {result.get('error', 'Unknown error')}")
        else:
            print("🚀 Running full local scraping...")
            # Run comprehensive scraping
            results = await scraper.run_comprehensive_scrape(
                max_pages_per_url=args.max_pages,
                max_concurrent=args.max_concurrent
            )
            
            if results['success']:
                print("\n🎉 Local scraping completed successfully!")
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