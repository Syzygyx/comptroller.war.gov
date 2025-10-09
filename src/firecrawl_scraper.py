#!/usr/bin/env python3
"""
Firecrawl-based scraper for comptroller.defense.gov
Comprehensive site scraping with proper JavaScript handling
"""

import os
import json
import asyncio
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Optional
from urllib.parse import urljoin, urlparse

from firecrawl import FirecrawlApp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FirecrawlComptrollerScraper:
    """Comprehensive scraper using Firecrawl for comptroller.defense.gov"""
    
    def __init__(self, output_dir: str = "data/pdfs", metadata_file: str = "data/metadata.json"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = Path(metadata_file)
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize Firecrawl
        api_key = os.getenv('FIRECRAWL_API_KEY')
        if not api_key:
            print("⚠️  FIRECRAWL_API_KEY not found in environment")
            print("   Get your API key from: https://firecrawl.dev")
            print("   Add it to your .env file: FIRECRAWL_API_KEY=your_key_here")
            raise ValueError("FIRECRAWL_API_KEY is required")
        
        self.app = FirecrawlApp(api_key=api_key)
        
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
                return json.load(f)
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
    
    async def scrape_url(self, url: str, max_pages: int = 100) -> Dict:
        """Scrape a single URL and discover PDFs"""
        print(f"🔍 Scraping: {url}")
        
        try:
            # Use Firecrawl to scrape the URL
            scrape_result = self.app.scrape_url(
                url=url,
                params={
                    'formats': ['markdown', 'html'],
                    'onlyMainContent': False,
                    'includeTags': ['a', 'link'],
                    'maxPages': max_pages,
                    'crawlOptions': {
                        'allowExternalLinks': True,
                        'maxDepth': 3,
                        'limit': max_pages
                    }
                }
            )
            
            if scrape_result.get('success'):
                # Extract PDF links from the scraped content
                pdf_links = self._extract_pdf_links(scrape_result, url)
                
                self.metadata['scraping_stats']['pages_scraped'] += 1
                self.metadata['scraped_urls'].add(url)
                
                return {
                    'success': True,
                    'pdf_links': pdf_links,
                    'pages_found': len(scrape_result.get('data', {}).get('links', [])),
                    'content_length': len(scrape_result.get('data', {}).get('markdown', ''))
                }
            else:
                print(f"❌ Failed to scrape {url}: {scrape_result.get('error', 'Unknown error')}")
                self.metadata['scraping_stats']['errors'] += 1
                return {'success': False, 'error': scrape_result.get('error', 'Unknown error')}
                
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            self.metadata['scraping_stats']['errors'] += 1
            return {'success': False, 'error': str(e)}
    
    def _extract_pdf_links(self, scrape_result: Dict, base_url: str) -> List[Dict]:
        """Extract PDF links from scraped content"""
        pdf_links = []
        
        # Extract from HTML content
        html_content = scrape_result.get('data', {}).get('html', '')
        if html_content:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                href = link['href']
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
        
        # Extract from markdown content
        markdown_content = scrape_result.get('data', {}).get('markdown', '')
        if markdown_content:
            import re
            # Find markdown links to PDFs
            pdf_pattern = r'\[([^\]]*)\]\(([^)]*\.pdf)\)'
            matches = re.findall(pdf_pattern, markdown_content, re.IGNORECASE)
            
            for title, href in matches:
                absolute_url = urljoin(base_url, href)
                pdf_info = {
                    'url': absolute_url,
                    'filename': os.path.basename(urlparse(absolute_url).path),
                    'title': title or 'Untitled',
                    'source_page': base_url,
                    'discovered_at': datetime.now().isoformat()
                }
                pdf_links.append(pdf_info)
        
        return pdf_links
    
    async def download_pdf(self, pdf_info: Dict) -> bool:
        """Download a single PDF"""
        url = pdf_info['url']
        filename = pdf_info['filename']
        
        # Skip if already downloaded
        if filename in self.metadata.get('downloaded_files', {}):
            print(f"⏭️  Skipping {filename} (already downloaded)")
            return True
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
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
        print("🚀 Starting comprehensive Firecrawl scraping...")
        print(f"📊 Target URLs: {len(self.target_urls)}")
        print(f"📊 Max pages per URL: {max_pages_per_url}")
        print(f"📊 Max concurrent requests: {max_concurrent}")
        
        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_with_semaphore(url):
            async with semaphore:
                return await self.scrape_url(url, max_pages_per_url)
        
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
    
    parser = argparse.ArgumentParser(description='Comprehensive Firecrawl scraper for comptroller.defense.gov')
    parser.add_argument('--max-pages', type=int, default=50, help='Max pages per URL')
    parser.add_argument('--max-concurrent', type=int, default=5, help='Max concurrent requests')
    parser.add_argument('--output-dir', default='data/pdfs', help='Output directory for PDFs')
    parser.add_argument('--metadata-file', default='data/metadata.json', help='Metadata file')
    
    args = parser.parse_args()
    
    scraper = FirecrawlComptrollerScraper(
        output_dir=args.output_dir,
        metadata_file=args.metadata_file
    )
    
    try:
        results = await scraper.run_comprehensive_scrape(
            max_pages_per_url=args.max_pages,
            max_concurrent=args.max_concurrent
        )
        
        if results['success']:
            print("\n🎉 Comprehensive scraping completed successfully!")
        else:
            print("\n❌ Scraping completed with errors")
            
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))