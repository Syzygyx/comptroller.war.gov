#!/usr/bin/env python3
"""
Local Firecrawl-style scraper using Playwright
No API required - runs completely locally
"""

import os
import json
import asyncio
import hashlib
import aiohttp
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Optional
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup

from playwright.async_api import async_playwright


class LocalFirecrawlScraper:
    """Local scraper that mimics Firecrawl functionality using Playwright"""
    
    def __init__(self, output_dir: str = "data/pdfs", metadata_file: str = "data/metadata.json"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = Path(metadata_file)
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing metadata
        self.metadata = self._load_metadata()
        
        # Target URLs for comprehensive scraping
        self.target_urls = [
            "https://comptroller.defense.gov/Budget-Execution/Reprogramming/",
            "https://comptroller.defense.gov/Portals/45/Documents/execution/reprogramming/",
            "https://comptroller.defense.gov/Budget-Execution/",
            "https://comptroller.defense.gov/Portals/45/Documents/execution/",
            "https://comptroller.defense.gov/Portals/45/Documents/",
        ]
        
        # Additional year-specific URLs
        for year in range(1997, 2026):
            self.target_urls.extend([
                f"https://comptroller.defense.gov/Portals/45/Documents/execution/reprogramming/fy{year}/",
                f"https://comptroller.defense.gov/Budget-Execution/Reprogramming/fy{year}/",
                f"https://comptroller.defense.gov/Portals/45/Documents/execution/reprogramming/archive/fy{year}/",
            ])
    
    def _load_metadata(self) -> Dict:
        """Load existing metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
                # Ensure scraping_stats exists
                if 'scraping_stats' not in metadata:
                    metadata['scraping_stats'] = {
                        'pages_scraped': 0,
                        'pdfs_found': 0,
                        'pdfs_downloaded': 0,
                        'errors': 0
                    }
                return metadata
        return {
            'last_run': None,
            'scraped_urls': set(),
            'pdf_urls': set(),
            'total_pdfs': 0,
            'failed_downloads': [],
            'scraping_stats': {
                'pages_scraped': 0,
                'pdfs_found': 0,
                'pdfs_downloaded': 0,
                'errors': 0
            }
        }
    
    def _save_metadata(self):
        """Save metadata to file"""
        self.metadata['last_run'] = datetime.now().isoformat()
        # Convert sets to lists for JSON serialization
        metadata_to_save = self.metadata.copy()
        metadata_to_save['scraped_urls'] = list(metadata_to_save['scraped_urls'])
        metadata_to_save['pdf_urls'] = list(metadata_to_save['pdf_urls'])
        
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata_to_save, f, indent=2)
    
    def _get_file_hash(self, filepath: Path) -> str:
        """Calculate MD5 hash of file"""
        md5 = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
        return md5.hexdigest()
    
    async def scrape_url_with_playwright(self, url: str, max_pages: int = 100) -> Dict:
        """Scrape a single URL using Playwright"""
        print(f"🔍 Scraping with Playwright: {url}")
        
        try:
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = await context.new_page()
                
                # Set up console and network monitoring
                console_messages = []
                network_requests = []
                
                page.on("console", lambda msg: console_messages.append({
                    "type": msg.type,
                    "text": msg.text,
                    "location": msg.location
                }))
                
                page.on("request", lambda req: network_requests.append({
                    "url": req.url,
                    "method": req.method,
                    "resource_type": req.resource_type
                }))
                
                # Navigate to page
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Wait for dynamic content to load
                await page.wait_for_timeout(3000)
                
                # Get page content
                html_content = await page.content()
                
                # Extract PDF links
                pdf_links = self._extract_pdf_links_from_html(html_content, url)
                
                # Look for additional pages/links to crawl
                additional_links = await self._find_additional_links(page, url, max_pages)
                
                await browser.close()
                
                self.metadata['scraping_stats']['pages_scraped'] += 1
                self.metadata['scraped_urls'].add(url)
                
                return {
                    'success': True,
                    'pdf_links': pdf_links,
                    'additional_links': additional_links,
                    'pages_found': len(additional_links),
                    'content_length': len(html_content),
                    'console_messages': console_messages,
                    'network_requests': len(network_requests)
                }
                
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            self.metadata['scraping_stats']['errors'] += 1
            return {'success': False, 'error': str(e)}
    
    def _extract_pdf_links_from_html(self, html_content: str, base_url: str) -> List[Dict]:
        """Extract PDF links from HTML content"""
        pdf_links = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all links
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Check if it's a PDF
                if href.lower().endswith('.pdf'):
                    absolute_url = urljoin(base_url, href)
                    pdf_info = {
                        'url': absolute_url,
                        'filename': os.path.basename(urlparse(absolute_url).path),
                        'title': link.get_text(strip=True) or 'Untitled',
                        'source_page': base_url,
                        'discovered_at': datetime.now().isoformat()
                    }
                    pdf_links.append(pdf_info)
            
            # Also check for direct PDF links in text content
            import re
            pdf_pattern = r'href=["\']([^"\']*\.pdf)["\']'
            matches = re.findall(pdf_pattern, html_content, re.IGNORECASE)
            
            for pdf_url in matches:
                absolute_url = urljoin(base_url, pdf_url)
                pdf_info = {
                    'url': absolute_url,
                    'filename': os.path.basename(urlparse(absolute_url).path),
                    'title': 'Discovered PDF',
                    'source_page': base_url,
                    'discovered_at': datetime.now().isoformat()
                }
                pdf_links.append(pdf_info)
                
        except Exception as e:
            print(f"⚠️  Error parsing HTML: {e}")
        
        return pdf_links
    
    async def _find_additional_links(self, page, base_url: str, max_pages: int) -> List[str]:
        """Find additional links to crawl"""
        additional_links = []
        
        try:
            # Look for links that might contain more content
            links = await page.query_selector_all('a[href]')
            
            for link in links:
                href = await link.get_attribute('href')
                if href:
                    absolute_url = urljoin(base_url, href)
                    
                    # Only include links from the same domain
                    if 'comptroller.defense.gov' in absolute_url:
                        # Skip certain patterns
                        if any(skip in absolute_url.lower() for skip in [
                            'javascript:', 'mailto:', '#', 'tel:', 'fax:'
                        ]):
                            continue
                        
                        additional_links.append(absolute_url)
                        
                        if len(additional_links) >= max_pages:
                            break
                            
        except Exception as e:
            print(f"⚠️  Error finding additional links: {e}")
        
        return additional_links
    
    async def download_pdf(self, pdf_info: Dict) -> bool:
        """Download a single PDF"""
        url = pdf_info['url']
        filename = pdf_info['filename']
        
        # Skip if already downloaded
        if filename in self.metadata.get('downloaded_files', {}):
            print(f"⏭️  Skipping {filename} (already downloaded)")
            return True
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        filepath = self.output_dir / filename
                        
                        # Download file
                        with open(filepath, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        
                        # Verify file
                        if filepath.exists() and filepath.stat().st_size > 0:
                            file_hash = self._get_file_hash(filepath)
                            
                            # Update metadata
                            if 'downloaded_files' not in self.metadata:
                                self.metadata['downloaded_files'] = {}
                            
                            self.metadata['downloaded_files'][filename] = {
                                'url': url,
                                'downloaded_at': datetime.now().isoformat(),
                                'file_size': filepath.stat().st_size,
                                'file_hash': file_hash,
                                'title': pdf_info.get('title', ''),
                                'source_page': pdf_info.get('source_page', '')
                            }
                            
                            self.metadata['scraping_stats']['pdfs_downloaded'] += 1
                            print(f"✅ Downloaded: {filename}")
                            return True
                        else:
                            print(f"❌ Downloaded file is empty: {filename}")
                            return False
                    else:
                        print(f"❌ Failed to download {filename}: HTTP {response.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ Error downloading {filename}: {e}")
            self.metadata['failed_downloads'].append({
                'url': url,
                'filename': filename,
                'error': str(e),
                'failed_at': datetime.now().isoformat()
            })
            return False
    
    async def run_comprehensive_scrape(self, max_pages_per_url: int = 50, max_concurrent: int = 5):
        """Run comprehensive scraping of the entire site"""
        print("🚀 Starting comprehensive local scraping...")
        print(f"📊 Target URLs: {len(self.target_urls)}")
        print(f"📊 Max pages per URL: {max_pages_per_url}")
        print(f"📊 Max concurrent requests: {max_concurrent}")
        
        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_with_semaphore(url):
            async with semaphore:
                return await self.scrape_url_with_playwright(url, max_pages_per_url)
        
        # Scrape all URLs
        tasks = [scrape_with_semaphore(url) for url in self.target_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect all PDF links
        all_pdf_links = []
        for i, result in enumerate(results):
            if isinstance(result, dict) and result.get('success'):
                all_pdf_links.extend(result.get('pdf_links', []))
                print(f"✅ {self.target_urls[i]}: {len(result.get('pdf_links', []))} PDFs found")
            elif isinstance(result, Exception):
                print(f"❌ {self.target_urls[i]}: {result}")
            else:
                print(f"❌ {self.target_urls[i]}: {result}")
        
        # Remove duplicates
        unique_pdfs = {pdf['url']: pdf for pdf in all_pdf_links}
        pdfs_to_download = list(unique_pdfs.values())
        
        print(f"\n📊 Found {len(pdfs_to_download)} unique PDFs")
        self.metadata['scraping_stats']['pdfs_found'] = len(pdfs_to_download)
        
        # Download PDFs
        if pdfs_to_download:
            print(f"\n📥 Downloading {len(pdfs_to_download)} PDFs...")
            
            # Create semaphore for downloads
            download_semaphore = asyncio.Semaphore(max_concurrent)
            
            async def download_with_semaphore(pdf_info):
                async with download_semaphore:
                    return await self.download_pdf(pdf_info)
            
            # Download all PDFs
            download_tasks = [download_with_semaphore(pdf) for pdf in pdfs_to_download]
            download_results = await asyncio.gather(*download_tasks, return_exceptions=True)
            
            successful_downloads = sum(1 for result in download_results if result is True)
            print(f"✅ Successfully downloaded {successful_downloads}/{len(pdfs_to_download)} PDFs")
        
        # Save metadata
        self._save_metadata()
        
        # Print final stats
        stats = self.metadata['scraping_stats']
        print(f"\n📈 Final Statistics:")
        print(f"  Pages scraped: {stats['pages_scraped']}")
        print(f"  PDFs found: {stats['pdfs_found']}")
        print(f"  PDFs downloaded: {stats['pdfs_downloaded']}")
        print(f"  Errors: {stats['errors']}")
        
        return {
            'success': True,
            'pages_scraped': stats['pages_scraped'],
            'pdfs_found': stats['pdfs_found'],
            'pdfs_downloaded': stats['pdfs_downloaded'],
            'errors': stats['errors']
        }

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Local Firecrawl-style scraper for comptroller.defense.gov')
    parser.add_argument('--max-pages', type=int, default=50, help='Max pages per URL')
    parser.add_argument('--max-concurrent', type=int, default=5, help='Max concurrent requests')
    parser.add_argument('--output-dir', default='data/pdfs', help='Output directory for PDFs')
    parser.add_argument('--metadata-file', default='data/metadata.json', help='Metadata file')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode with limited URLs')
    
    args = parser.parse_args()
    
    scraper = LocalFirecrawlScraper(
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
            result = await scraper.scrape_url_with_playwright(url, max_pages=5)
            if result['success']:
                print(f"✅ {url}: {len(result.get('pdf_links', []))} PDFs found")
            else:
                print(f"❌ {url}: {result.get('error', 'Unknown error')}")
    else:
        try:
            results = await scraper.run_comprehensive_scrape(
                max_pages_per_url=args.max_pages,
                max_concurrent=args.max_concurrent
            )
            
            if results['success']:
                print("\n🎉 Local scraping completed successfully!")
            else:
                print("\n❌ Scraping completed with errors")
                
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))