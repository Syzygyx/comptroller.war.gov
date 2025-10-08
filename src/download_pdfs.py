#!/usr/bin/env python3
"""
PDF Download Script for comptroller.defense.gov
Downloads historical appropriation documents
"""

import os
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


class ComptrollerScraper:
    """Scrapes and downloads PDFs from comptroller.defense.gov"""
    
    BASE_URL = "https://comptroller.defense.gov"
    REPROGRAMMING_URLS = [
        "/Budget-Execution/Reprogramming/",
        "/Portals/45/Documents/execution/reprogramming/fy2025/",
        "/Portals/45/Documents/execution/reprogramming/fy2024/",
        "/Portals/45/Documents/execution/reprogramming/fy2023/",
        "/Portals/45/Documents/execution/reprogramming/fy2022/"
    ]
    
    def __init__(self, output_dir: str = "data/pdfs", metadata_file: str = "data/metadata.json"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = Path(metadata_file)
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.metadata = self._load_metadata()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def _load_metadata(self) -> Dict:
        """Load existing metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {
            'last_run': None,
            'downloaded_files': {},
            'total_files': 0,
            'failed_downloads': []
        }
    
    def _save_metadata(self):
        """Save metadata to file"""
        self.metadata['last_run'] = datetime.now().isoformat()
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def _get_file_hash(self, filepath: Path) -> str:
        """Calculate MD5 hash of file"""
        md5 = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
        return md5.hexdigest()
    
    def discover_pdf_links(self, url: str, visited: Set[str] = None) -> List[Dict[str, str]]:
        """Discover PDF links from a URL"""
        if visited is None:
            visited = set()
        
        if url in visited:
            return []
        
        visited.add(url)
        pdf_links = []
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links
            for link in soup.find_all('a', href=True):
                href = link['href']
                absolute_url = urljoin(url, href)
                
                # Check if it's a PDF
                if href.lower().endswith('.pdf'):
                    pdf_info = {
                        'url': absolute_url,
                        'filename': os.path.basename(urlparse(absolute_url).path),
                        'title': link.get_text(strip=True) or 'Untitled',
                        'source_page': url,
                        'discovered_at': datetime.now().isoformat()
                    }
                    pdf_links.append(pdf_info)
                
                # Recursively check reprogramming-related pages (limited depth)
                elif 'reprogramming' in href.lower() or 'execution' in href.lower():
                    if absolute_url.startswith(self.BASE_URL) and len(visited) < 50:
                        pdf_links.extend(self.discover_pdf_links(absolute_url, visited))
            
        except Exception as e:
            print(f"Error discovering links from {url}: {e}")
        
        return pdf_links
    
    def download_pdf(self, pdf_info: Dict[str, str]) -> bool:
        """Download a single PDF"""
        url = pdf_info['url']
        filename = pdf_info['filename']
        filepath = self.output_dir / filename
        
        # Check if already downloaded
        if filename in self.metadata['downloaded_files']:
            existing_info = self.metadata['downloaded_files'][filename]
            if filepath.exists() and existing_info.get('hash'):
                # File exists and has hash, skip
                return False
        
        try:
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            # Download with progress bar
            with open(filepath, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            
            # Calculate hash
            file_hash = self._get_file_hash(filepath)
            
            # Update metadata
            self.metadata['downloaded_files'][filename] = {
                **pdf_info,
                'hash': file_hash,
                'size': filepath.stat().st_size,
                'downloaded_at': datetime.now().isoformat(),
                'local_path': str(filepath)
            }
            self.metadata['total_files'] = len(self.metadata['downloaded_files'])
            
            return True
            
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            self.metadata['failed_downloads'].append({
                'url': url,
                'filename': filename,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            return False
    
    def run(self, max_downloads: int = None) -> Dict:
        """Run the scraper"""
        print("🔍 Discovering PDF links...")
        
        all_pdfs = []
        for url_path in self.REPROGRAMMING_URLS:
            url = urljoin(self.BASE_URL, url_path)
            pdfs = self.discover_pdf_links(url)
            all_pdfs.extend(pdfs)
        
        # Remove duplicates
        unique_pdfs = {pdf['url']: pdf for pdf in all_pdfs}
        pdfs = list(unique_pdfs.values())
        
        print(f"📊 Found {len(pdfs)} PDF documents")
        
        # Filter out already downloaded
        new_pdfs = [
            pdf for pdf in pdfs 
            if pdf['filename'] not in self.metadata['downloaded_files']
        ]
        
        print(f"📥 {len(new_pdfs)} new documents to download")
        
        if max_downloads:
            new_pdfs = new_pdfs[:max_downloads]
            print(f"⚠️  Limited to {max_downloads} downloads")
        
        # Download PDFs
        downloaded_count = 0
        for pdf in new_pdfs:
            if self.download_pdf(pdf):
                downloaded_count += 1
            time.sleep(2)  # Be respectful to the server
        
        # Save metadata
        self._save_metadata()
        
        results = {
            'total_discovered': len(pdfs),
            'new_documents': len(new_pdfs),
            'downloaded': downloaded_count,
            'failed': len(self.metadata['failed_downloads']),
            'metadata_file': str(self.metadata_file)
        }
        
        print(f"\n✅ Download complete!")
        print(f"   - Total discovered: {results['total_discovered']}")
        print(f"   - New documents: {results['new_documents']}")
        print(f"   - Successfully downloaded: {results['downloaded']}")
        print(f"   - Failed: {results['failed']}")
        
        return results


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Download PDFs from comptroller.defense.gov')
    parser.add_argument('--max', type=int, help='Maximum number of new downloads')
    parser.add_argument('--output', default='data/pdfs', help='Output directory')
    parser.add_argument('--metadata', default='data/metadata.json', help='Metadata file')
    
    args = parser.parse_args()
    
    scraper = ComptrollerScraper(
        output_dir=args.output,
        metadata_file=args.metadata
    )
    
    results = scraper.run(max_downloads=args.max)
    
    return 0 if results['failed'] == 0 else 1


if __name__ == '__main__':
    exit(main())
