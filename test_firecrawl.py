#!/usr/bin/env python3
"""
Test script for Firecrawl scraper
"""

import asyncio
import os
from src.firecrawl_scraper import FirecrawlComptrollerScraper

async def test_firecrawl():
    """Test the Firecrawl scraper with a limited scope"""
    
    print("🧪 Testing Firecrawl Scraper")
    print("=" * 40)
    
    # Check if API key is available
    if not os.getenv('FIRECRAWL_API_KEY'):
        print("❌ FIRECRAWL_API_KEY not found")
        print("   Please set it in your .env file:")
        print("   FIRECRAWL_API_KEY=your_key_here")
        return False
    
    try:
        # Create scraper instance
        scraper = FirecrawlComptrollerScraper(
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
            result = await scraper.scrape_url(url, max_pages=5)
            if result['success']:
                print(f"✅ {url}: {len(result.get('pdf_links', []))} PDFs found")
            else:
                print(f"❌ {url}: {result.get('error', 'Unknown error')}")
        
        print("\n🎉 Test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_firecrawl())
    exit(0 if success else 1)