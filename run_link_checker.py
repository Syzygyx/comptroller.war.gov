#!/usr/bin/env python3
"""
Simple Link Checker using Playwright
Checks all pages and links for 404s without requiring OpenRouter API
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List

from playwright.async_api import async_playwright, Browser, Page, BrowserContext


class LinkChecker:
    def __init__(self):
        self.base_url = "https://syzygyx.github.io/DD1414"
        self.pages_to_check = [
            "/",
            "/browse.html",
            "/dd1414_index.html", 
            "/dd1414_pdf_csv_comparison.html",
            "/dd1414_dashboard.html",
            "/dd1414_sankey.html",
            "/dd1414_timeline.html",
            "/dd1414_organizations.html",
            "/progress.html",
            "/sankey.html"
        ]
        self.results = []
        
    async def check_all_pages(self) -> Dict:
        """Check all pages and generate comprehensive report"""
        print("🔗 Starting Link Checker...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            try:
                for page_path in self.pages_to_check:
                    print(f"\n📄 Checking: {page_path}")
                    result = await self.check_single_page(context, page_path)
                    self.results.append(result)
                    await asyncio.sleep(1)  # Rate limiting
                    
            finally:
                await browser.close()
                
        return self.generate_report()
    
    async def check_single_page(self, context: BrowserContext, page_path: str) -> Dict:
        """Check a single page for broken links"""
        page = await context.new_page()
        
        try:
            # Navigate to page
            url = f"{self.base_url}{page_path}"
            print(f"  🌐 Loading: {url}")
            
            response = await page.goto(url, wait_until='networkidle', timeout=30000)
            if not response or response.status != 200:
                return {
                    'url': url,
                    'page_path': page_path,
                    'status': 'error',
                    'error': f'Failed to load page: {response.status if response else "No response"}',
                    'timestamp': datetime.now().isoformat(),
                    'broken_links': [],
                    'working_links': []
                }
            
            # Wait for page to fully load
            await page.wait_for_timeout(2000)
            
            # Check all links
            link_status = await self.check_all_links(page, url)
            
            return {
                'url': url,
                'page_path': page_path,
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'broken_links': link_status['broken'],
                'working_links': link_status['working'],
                'link_check_summary': link_status['summary']
            }
            
        except Exception as e:
            print(f"  ❌ Error checking {page_path}: {str(e)}")
            return {
                'url': f"{self.base_url}{page_path}",
                'page_path': page_path,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'broken_links': [],
                'working_links': []
            }
        finally:
            await page.close()
    
    async def check_all_links(self, page: Page, base_url: str) -> Dict:
        """Check all links on the page for 404s"""
        print(f"  🔗 Checking links...")
        
        # Get all links from the page
        links = await page.evaluate("""
            () => {
                const links = Array.from(document.querySelectorAll('a[href]')).map(a => ({
                    href: a.href,
                    text: a.textContent.trim(),
                    title: a.title || '',
                    target: a.target || '_self',
                    internal: a.href.includes(window.location.hostname)
                }));
                
                return links.filter(link => link.href && link.href.startsWith('http'));
            }
        """)
        
        broken_links = []
        working_links = []
        
        # Check each link
        for link in links:
            try:
                # Skip external links for now (focus on internal ones)
                if not link['internal']:
                    continue
                    
                print(f"    Checking: {link['href']}")
                
                # Create a new page to check the link
                link_page = await page.context.new_page()
                
                try:
                    response = await link_page.goto(link['href'], wait_until='networkidle', timeout=10000)
                    
                    if response and response.status == 200:
                        working_links.append({
                            'url': link['href'],
                            'text': link['text'],
                            'status': response.status,
                            'type': 'working'
                        })
                        print(f"      ✅ {response.status}")
                    else:
                        broken_links.append({
                            'url': link['href'],
                            'text': link['text'],
                            'status': response.status if response else 'timeout',
                            'type': 'broken',
                            'error': f"HTTP {response.status if response else 'timeout'}"
                        })
                        print(f"      ❌ {response.status if response else 'timeout'}")
                        
                except Exception as e:
                    broken_links.append({
                        'url': link['href'],
                        'text': link['text'],
                        'status': 'error',
                        'type': 'broken',
                        'error': str(e)
                    })
                    print(f"      ❌ Error: {str(e)}")
                finally:
                    await link_page.close()
                    
            except Exception as e:
                print(f"    ⚠️ Error checking link {link['href']}: {str(e)}")
                broken_links.append({
                    'url': link['href'],
                    'text': link['text'],
                    'status': 'error',
                    'type': 'broken',
                    'error': str(e)
                })
        
        # Also check for specific data files that should exist
        data_files_to_check = [
            '/data/csv/Reprogramming_Overview_extracted.csv',
            '/data/csv/dd1414_enhanced_data.csv',
            '/data/metadata.json',
            '/data/validation/validation_summary.json',
            '/data/embeddings/chunks.json',
            '/data/embeddings/embeddings.json'
        ]
        
        for data_file in data_files_to_check:
            try:
                data_url = f"{self.base_url}{data_file}"
                print(f"    Checking data file: {data_file}")
                
                data_page = await page.context.new_page()
                try:
                    response = await data_page.goto(data_url, wait_until='networkidle', timeout=10000)
                    
                    if response and response.status == 200:
                        working_links.append({
                            'url': data_url,
                            'text': f"Data file: {data_file}",
                            'status': response.status,
                            'type': 'data_file'
                        })
                        print(f"      ✅ Data file exists")
                    else:
                        broken_links.append({
                            'url': data_url,
                            'text': f"Data file: {data_file}",
                            'status': response.status if response else 'timeout',
                            'type': 'missing_data_file',
                            'error': f"Missing data file: {data_file}"
                        })
                        print(f"      ❌ Missing data file")
                        
                finally:
                    await data_page.close()
                    
            except Exception as e:
                print(f"    ⚠️ Error checking data file {data_file}: {str(e)}")
                broken_links.append({
                    'url': f"{self.base_url}{data_file}",
                    'text': f"Data file: {data_file}",
                    'status': 'error',
                    'type': 'missing_data_file',
                    'error': str(e)
                })
        
        summary = {
            'total_checked': len(links) + len(data_files_to_check),
            'working': len(working_links),
            'broken': len(broken_links),
            'broken_percentage': (len(broken_links) / (len(links) + len(data_files_to_check))) * 100 if (len(links) + len(data_files_to_check)) > 0 else 0
        }
        
        print(f"  📊 Link check complete: {summary['working']} working, {summary['broken']} broken")
        
        return {
            'broken': broken_links,
            'working': working_links,
            'summary': summary
        }
    
    def generate_report(self) -> Dict:
        """Generate comprehensive link check report"""
        successful_checks = [r for r in self.results if r['status'] == 'success']
        failed_checks = [r for r in self.results if r['status'] == 'error']
        
        # Analyze link health
        all_broken_links = []
        all_working_links = []
        total_links_checked = 0
        
        for result in successful_checks:
            if 'broken_links' in result:
                all_broken_links.extend(result['broken_links'])
            if 'working_links' in result:
                all_working_links.extend(result['working_links'])
            if 'link_check_summary' in result:
                total_links_checked += result['link_check_summary'].get('total_checked', 0)
        
        # Categorize broken links
        broken_by_type = {}
        for link in all_broken_links:
            link_type = link.get('type', 'unknown')
            if link_type not in broken_by_type:
                broken_by_type[link_type] = []
            broken_by_type[link_type].append(link)
        
        # Find most common broken links
        broken_urls = [link['url'] for link in all_broken_links]
        from collections import Counter
        most_broken = Counter(broken_urls).most_common(10)
        
        # Calculate health score
        health_score = 0
        if total_links_checked > 0:
            health_score = (len(all_working_links) / total_links_checked) * 100
        
        report = {
            'check_summary': {
                'total_pages_checked': len(self.results),
                'successful_checks': len(successful_checks),
                'failed_checks': len(failed_checks),
                'check_date': datetime.now().isoformat()
            },
            'link_analysis': {
                'total_links_checked': total_links_checked,
                'working_links': len(all_working_links),
                'broken_links': len(all_broken_links),
                'health_score': health_score,
                'broken_by_type': broken_by_type,
                'most_broken_links': most_broken,
                'critical_issues': [
                    link for link in all_broken_links 
                    if link.get('type') == 'missing_data_file'
                ]
            },
            'page_results': self.results
        }
        
        return report
    
    def save_report(self, report: Dict, filename: str = None):
        """Save link check report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"link_check_report_{timestamp}.json"
        
        # Ensure reports directory exists
        import os
        os.makedirs("reports", exist_ok=True)
        filepath = os.path.join("reports", filename)
        
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Report saved to: {filepath}")
        return filepath


async def main():
    """Main function to run the link checker"""
    checker = LinkChecker()
    
    try:
        print("🚀 Starting comprehensive link checking...")
        report = await checker.check_all_pages()
        
        # Save report
        report_file = checker.save_report(report)
        
        # Print summary
        print("\n" + "="*60)
        print("🔗 LINK CHECK SUMMARY")
        print("="*60)
        
        summary = report['check_summary']
        print(f"📄 Pages Checked: {summary['total_pages_checked']}")
        print(f"✅ Successful: {summary['successful_checks']}")
        print(f"❌ Failed: {summary['failed_checks']}")
        
        # Link analysis summary
        link_analysis = report['link_analysis']
        print(f"\n🔗 Link Health Analysis:")
        print(f"  Total Links Checked: {link_analysis['total_links_checked']}")
        print(f"  Working Links: {link_analysis['working_links']}")
        print(f"  Broken Links: {link_analysis['broken_links']}")
        print(f"  Health Score: {link_analysis['health_score']:.1f}%")
        
        if link_analysis['critical_issues']:
            print(f"\n❌ Critical Issues (Missing Data Files):")
            for issue in link_analysis['critical_issues']:
                print(f"  - {issue['url']}: {issue.get('error', 'Not found')}")
        
        if link_analysis['most_broken_links']:
            print(f"\n🔍 Most Common Broken Links:")
            for url, count in link_analysis['most_broken_links'][:5]:
                print(f"  - {url} (broken {count} times)")
        
        print(f"\n📁 Full report saved to: {report_file}")
        
    except Exception as e:
        print(f"❌ Error during link checking: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())