#!/usr/bin/env python3
"""
Test script for local scraper
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from local_firecrawl_scraper import LocalFirecrawlScraper

async def test_local_scraper():
    """Test the local scraper with a limited scope"""
    
    print("🧪 Testing Local Scraper")
    print("=" * 30)
    
    try:
        # Create scraper instance
        scraper = LocalFirecrawlScraper(
            output_dir="test_pdfs",
            metadata_file="test_metadata.json"
        )
        
        # Test with just a few URLs
        test_urls = [
            "https://comptroller.defense.gov/Budget-Execution/Reprogramming/",
            "https://comptroller.defense.gov/Portals/45/Documents/execution/reprogramming/fy2024/"
        ]
        
        print(f"🔍 Testing with {len(test_urls)} URLs...")
        
        # Scrape test URLs
        for url in test_urls:
            result = await scraper.scrape_url_with_playwright(url, max_pages=5)
            if result['success']:
                print(f"✅ {url}: {len(result.get('pdf_links', []))} PDFs found")
                print(f"   Additional links: {len(result.get('additional_links', []))}")
                print(f"   Content length: {result.get('content_length', 0)}")
            else:
                print(f"❌ {url}: {result.get('error', 'Unknown error')}")
        
        print("\n🎉 Test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_local_scraper())
    exit(0 if success else 1)