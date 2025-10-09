#!/usr/bin/env python3
"""
Complete Site Scraper - Downloads ALL budget documents from comptroller.defense.gov
"""

import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path
import json
import time
from datetime import datetime
from typing import List, Dict, Set
import hashlib


class CompleteSiteScraper:
    """Comprehensive scraper for all comptroller.defense.gov budget documents"""
    
    def __init__(self, output_dir: str = 'data/pdfs'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        self.discovered_pdfs: Set[str] = set()
        self.downloaded_files: List[Dict] = []
        self.failed_downloads: List[Dict] = []
        
        # Base URLs to scrape
        self.base_urls = [
            'https://comptroller.defense.gov/Budget-Execution/',
            'https://comptroller.defense.gov/Portals/45/Documents/execution/',
        ]
        
        # Fiscal year pages to check
        self.fy_pages = []
        for year in range(2005, 2026):
            self.fy_pages.append(f'https://comptroller.defense.gov/BudgetExecution/ReprogrammingFY{year}.aspx')
    
    def discover_all_pdfs(self) -> List[Dict[str, str]]:
        """Discover all PDFs from all pages"""
        print("🔍 Discovering PDFs from all pages...")
        print("="*80)
        
        all_pdfs = []
        
        # Method 1: Direct Portals folder structure
        print("\n📁 Method 1: Checking Portals/45/Documents/execution/...")
        portals_pdfs = self._discover_from_portals()
        all_pdfs.extend(portals_pdfs)
        print(f"   Found: {len(portals_pdfs)} PDFs")
        
        # Method 2: Fiscal year pages
        print("\n📅 Method 2: Checking fiscal year pages (FY2005-FY2025)...")
        for fy_page in self.fy_pages:
            year = fy_page.split('FY')[1].split('.')[0]
            try:
                fy_pdfs = self._discover_from_page(fy_page)
                all_pdfs.extend(fy_pdfs)
                print(f"   FY{year}: {len(fy_pdfs)} PDFs")
                time.sleep(0.5)
            except Exception as e:
                print(f"   FY{year}: Error - {e}")
        
        # Method 3: Common document patterns
        print("\n🔗 Method 3: Trying known document patterns...")
        pattern_pdfs = self._discover_from_patterns()
        all_pdfs.extend(pattern_pdfs)
        print(f"   Found: {len(pattern_pdfs)} PDFs")
        
        # Deduplicate
        unique_pdfs = {}
        for pdf in all_pdfs:
            url = pdf['url']
            if url not in unique_pdfs:
                unique_pdfs[url] = pdf
        
        result = list(unique_pdfs.values())
        print(f"\n✅ Total unique PDFs discovered: {len(result)}")
        return result
    
    def _discover_from_portals(self) -> List[Dict[str, str]]:
        """Try common Portals folder structures"""
        pdfs = []
        
        # Known folder patterns
        folders = [
            'https://comptroller.defense.gov/Portals/45/Documents/execution/',
            'https://comptroller.defense.gov/Portals/45/Documents/execution/reprogramming/',
        ]
        
        # Add fiscal year subfolders
        for year in range(2005, 2026):
            folders.append(f'https://comptroller.defense.gov/Portals/45/Documents/execution/reprogramming/fy{year}/')
        
        for folder in folders:
            try:
                response = self.session.get(folder, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if '.pdf' in href.lower():
                            full_url = self._normalize_url(href, folder)
                            filename = full_url.split('/')[-1]
                            pdfs.append({
                                'url': full_url,
                                'filename': filename,
                                'source_page': folder
                            })
            except:
                pass
        
        return pdfs
    
    def _discover_from_page(self, page_url: str) -> List[Dict[str, str]]:
        """Discover PDFs from a specific page"""
        pdfs = []
        
        try:
            response = self.session.get(page_url, timeout=15)
            if response.status_code != 200:
                return pdfs
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '.pdf' in href.lower():
                    full_url = self._normalize_url(href, page_url)
                    filename = full_url.split('/')[-1]
                    
                    # Get link text for title
                    title = link.get_text(strip=True) or filename
                    
                    pdfs.append({
                        'url': full_url,
                        'filename': filename,
                        'title': title,
                        'source_page': page_url
                    })
        except Exception as e:
            pass
        
        return pdfs
    
    def _discover_from_patterns(self) -> List[Dict[str, str]]:
        """Try common document naming patterns"""
        pdfs = []
        base = 'https://comptroller.defense.gov/Portals/45/Documents/execution/'
        
        patterns = []
        
        # DD 1414 patterns (already have these)
        for year in range(2000, 2026):
            patterns.append(f'{base}FY_{year}_DD_1414_Base_for_Reprogramming_Actions.pdf')
        
        # Reprogramming action patterns
        for year in range(5, 26):  # 05-25
            year_str = f"{year:02d}"
            for num in range(1, 100):
                num_str = f"{num:02d}"
                # Internal Reprogramming (IR)
                patterns.append(f'{base}reprogramming/fy20{year_str}/{year_str}-{num_str}_IR.pdf')
                # Prior Approval (PA)
                patterns.append(f'{base}reprogramming/fy20{year_str}/{year_str}-{num_str}_PA.pdf')
                # Baseline Realignment (BRA)
                patterns.append(f'{base}reprogramming/fy20{year_str}/{year_str}-{num_str}_BRA.pdf')
        
        print(f"   Checking {len(patterns)} URL patterns...")
        
        # Test a sample to see if this approach works
        sample_size = min(100, len(patterns))
        for i, url in enumerate(patterns[:sample_size]):
            if i % 20 == 0:
                print(f"   Progress: {i}/{sample_size}...")
            
            try:
                response = self.session.head(url, timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    filename = url.split('/')[-1]
                    pdfs.append({
                        'url': url,
                        'filename': filename,
                        'source_page': 'pattern_match'
                    })
            except:
                pass
        
        return pdfs
    
    def _normalize_url(self, href: str, base_url: str) -> str:
        """Normalize relative URLs to absolute"""
        if href.startswith('http'):
            # Fix comptroller.war.gov to comptroller.defense.gov
            url = href.replace('comptroller.war.gov', 'comptroller.defense.gov')
            return url
        elif href.startswith('/'):
            return 'https://comptroller.defense.gov' + href
        else:
            return base_url.rstrip('/') + '/' + href.lstrip('/')
    
    def download_all(self, pdfs: List[Dict[str, str]], max_downloads: int = None):
        """Download all discovered PDFs"""
        print(f"\n📥 Starting downloads...")
        print("="*80)
        
        to_download = pdfs[:max_downloads] if max_downloads else pdfs
        
        for i, pdf in enumerate(to_download, 1):
            filename = pdf['filename']
            local_path = self.output_dir / filename
            
            # Skip if already exists
            if local_path.exists():
                print(f"[{i}/{len(to_download)}] ⏭️  {filename} (already exists)")
                continue
            
            print(f"[{i}/{len(to_download)}] 📄 {filename}")
            
            try:
                response = self.session.get(pdf['url'], timeout=30)
                response.raise_for_status()
                
                # Verify it's a PDF
                if len(response.content) < 1000:
                    print(f"   ⚠️  File too small, skipping")
                    self.failed_downloads.append({**pdf, 'error': 'File too small'})
                    continue
                
                # Save file
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                
                size_mb = len(response.content) / (1024 * 1024)
                print(f"   ✓ Downloaded {size_mb:.2f} MB")
                
                self.downloaded_files.append({
                    **pdf,
                    'local_path': str(local_path),
                    'size': len(response.content),
                    'downloaded_at': datetime.now().isoformat()
                })
                
                time.sleep(1)  # Be nice to server
                
            except Exception as e:
                print(f"   ✗ Error: {e}")
                self.failed_downloads.append({**pdf, 'error': str(e)})
        
        print(f"\n✅ Downloads complete!")
        print(f"   Downloaded: {len(self.downloaded_files)} files")
        print(f"   Failed: {len(self.failed_downloads)} files")
    
    def save_metadata(self):
        """Save download metadata"""
        metadata = {
            'last_scrape': datetime.now().isoformat(),
            'downloaded_files': self.downloaded_files,
            'failed_downloads': self.failed_downloads,
            'stats': {
                'total_downloaded': len(self.downloaded_files),
                'total_failed': len(self.failed_downloads),
                'total_size_mb': sum(f['size'] for f in self.downloaded_files) / (1024 * 1024)
            }
        }
        
        metadata_path = Path('data/scrape_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n💾 Metadata saved to: {metadata_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape all PDFs from comptroller.defense.gov')
    parser.add_argument('--max', type=int, help='Maximum files to download')
    parser.add_argument('--discover-only', action='store_true', help='Only discover URLs, don\'t download')
    
    args = parser.parse_args()
    
    print("="*80)
    print("🌐 COMPLETE COMPTROLLER.DEFENSE.GOV SCRAPER")
    print("="*80)
    
    scraper = CompleteSiteScraper()
    
    # Discover all PDFs
    pdfs = scraper.discover_all_pdfs()
    
    if args.discover_only:
        print("\n📋 Discovered PDFs:")
        for pdf in pdfs[:50]:  # Show first 50
            print(f"   {pdf['filename']}")
        if len(pdfs) > 50:
            print(f"   ... and {len(pdfs) - 50} more")
        return
    
    # Download all
    scraper.download_all(pdfs, max_downloads=args.max)
    scraper.save_metadata()
    
    print("\n" + "="*80)
    print("✅ SCRAPING COMPLETE!")
    print("="*80)
    print(f"\nResults:")
    print(f"  Total discovered: {len(pdfs)} PDFs")
    print(f"  Downloaded: {len(scraper.downloaded_files)} files")
    print(f"  Failed: {len(scraper.failed_downloads)} files")
    total_mb = sum(f['size'] for f in scraper.downloaded_files) / (1024 * 1024)
    print(f"  Total size: {total_mb:.2f} MB")


if __name__ == '__main__':
    main()
