#!/usr/bin/env python3
"""
Aesthetic and Functional Page Evaluator using OpenRouter Multimodal
Evaluates every page on the site for visual design, usability, and functionality
"""

import asyncio
import base64
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import aiohttp
from playwright.async_api import async_playwright, Browser, Page, BrowserContext


class AestheticEvaluator:
    def __init__(self, openrouter_api_key: str):
        self.openrouter_api_key = openrouter_api_key
        self.base_url = "https://syzygyx.github.io/DD1414"
        self.pages_to_evaluate = [
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
        
    async def evaluate_all_pages(self) -> Dict:
        """Evaluate all pages and generate comprehensive report"""
        print("🎨 Starting Aesthetic and Functional Evaluation...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            try:
                for page_path in self.pages_to_evaluate:
                    print(f"\n📄 Evaluating: {page_path}")
                    result = await self.evaluate_single_page(context, page_path)
                    self.results.append(result)
                    await asyncio.sleep(2)  # Rate limiting
                    
            finally:
                await browser.close()
                
        return self.generate_report()
    
    async def evaluate_single_page(self, context: BrowserContext, page_path: str) -> Dict:
        """Evaluate a single page for aesthetics and functionality"""
        page = await context.new_page()
        
        try:
            # Navigate to page
            url = f"{self.base_url}{page_path}"
            print(f"  🌐 Loading: {url}")
            
            response = await page.goto(url, wait_until='networkidle', timeout=30000)
            if not response or response.status != 200:
                return {
                    'url': url,
                    'status': 'error',
                    'error': f'Failed to load page: {response.status if response else "No response"}',
                    'timestamp': datetime.now().isoformat(),
                    'broken_links': [],
                    'working_links': []
                }
            
            # Wait for page to fully load
            await page.wait_for_timeout(3000)
            
            # Check all links for 404s
            link_status = await self.check_all_links(page, url)
            
            # Take full page screenshot
            screenshot = await page.screenshot(full_page=True, type='png')
            screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')
            
            # Get page content and metadata
            page_content = await self.extract_page_content(page)
            
            # Evaluate with OpenRouter multimodal
            evaluation = await self.evaluate_with_openrouter(page_content, screenshot_b64, url)
            
            return {
                'url': url,
                'page_path': page_path,
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'page_content': page_content,
                'evaluation': evaluation,
                'broken_links': link_status['broken'],
                'working_links': link_status['working'],
                'link_check_summary': link_status['summary']
            }
            
        except Exception as e:
            print(f"  ❌ Error evaluating {page_path}: {str(e)}")
            return {
                'url': f"{self.base_url}{page_path}",
                'page_path': page_path,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        finally:
            await page.close()
    
    async def extract_page_content(self, page: Page) -> Dict:
        """Extract comprehensive page content and metadata"""
        try:
            # Get basic page info
            title = await page.title()
            
            # Get all text content
            text_content = await page.evaluate("""
                () => {
                    // Remove script and style elements
                    const scripts = document.querySelectorAll('script, style');
                    scripts.forEach(el => el.remove());
                    
                    // Get all text content
                    return document.body.innerText || document.body.textContent || '';
                }
            """)
            
            # Get page structure
            structure = await page.evaluate("""
                () => {
                    const elements = {
                        headings: Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6')).map(h => ({
                            tag: h.tagName,
                            text: h.textContent.trim(),
                            level: parseInt(h.tagName[1])
                        })),
                        links: Array.from(document.querySelectorAll('a')).map(a => ({
                            text: a.textContent.trim(),
                            href: a.href,
                            internal: a.href.includes(window.location.hostname)
                        })),
                        buttons: Array.from(document.querySelectorAll('button, .btn')).map(b => ({
                            text: b.textContent.trim(),
                            classes: b.className,
                            type: b.type || 'button'
                        })),
                        forms: Array.from(document.querySelectorAll('form')).map(f => ({
                            action: f.action,
                            method: f.method,
                            inputs: Array.from(f.querySelectorAll('input, select, textarea')).map(i => ({
                                type: i.type,
                                name: i.name,
                                placeholder: i.placeholder,
                                required: i.required
                            }))
                        })),
                        images: Array.from(document.querySelectorAll('img')).map(img => ({
                            src: img.src,
                            alt: img.alt,
                            width: img.width,
                            height: img.height
                        })),
                        tables: Array.from(document.querySelectorAll('table')).map(table => ({
                            rows: table.rows.length,
                            cells: table.cells ? table.cells.length : 0,
                            headers: Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim())
                        }))
                    };
                    return elements;
                }
            """)
            
            # Get CSS information
            css_info = await page.evaluate("""
                () => {
                    const styles = getComputedStyle(document.body);
                    return {
                        fontFamily: styles.fontFamily,
                        fontSize: styles.fontSize,
                        color: styles.color,
                        backgroundColor: styles.backgroundColor,
                        margin: styles.margin,
                        padding: styles.padding
                    };
                }
            """)
            
            # Check for interactive elements
            interactive_elements = await page.evaluate("""
                () => {
                    return {
                        clickableElements: document.querySelectorAll('a, button, [onclick], [role="button"]').length,
                        inputElements: document.querySelectorAll('input, select, textarea').length,
                        interactiveElements: document.querySelectorAll('[tabindex], [onclick], [onchange]').length
                    };
                }
            """)
            
            # Get viewport and layout info
            viewport_info = await page.evaluate("""
                () => {
                    return {
                        viewportWidth: window.innerWidth,
                        viewportHeight: window.innerHeight,
                        scrollWidth: document.documentElement.scrollWidth,
                        scrollHeight: document.documentElement.scrollHeight,
                        hasHorizontalScroll: document.documentElement.scrollWidth > window.innerWidth,
                        hasVerticalScroll: document.documentElement.scrollHeight > window.innerHeight
                    };
                }
            """)
            
            return {
                'title': title,
                'text_content': text_content[:5000],  # Limit text content
                'structure': structure,
                'css_info': css_info,
                'interactive_elements': interactive_elements,
                'viewport_info': viewport_info,
                'url': page.url
            }
            
        except Exception as e:
            print(f"  ⚠️ Error extracting page content: {str(e)}")
            return {'error': str(e)}
    
    async def check_all_links(self, page: Page, base_url: str) -> Dict:
        """Check all links on the page for 404s and accessibility"""
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
                
                // Also check for download links, buttons with hrefs, etc.
                const buttons = Array.from(document.querySelectorAll('button[data-href], [onclick*="window.open"]')).map(b => ({
                    href: b.dataset.href || b.getAttribute('onclick')?.match(/['"]([^'"]+)['"]/)?.[1] || '',
                    text: b.textContent.trim(),
                    title: b.title || '',
                    target: '_blank',
                    internal: b.dataset.href?.includes(window.location.hostname) || false
                }));
                
                return [...links, ...buttons].filter(link => link.href && link.href.startsWith('http'));
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
            '/data/embeddings/chunks.json'
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
    
    async def evaluate_with_openrouter(self, page_content: Dict, screenshot_b64: str, url: str) -> Dict:
        """Use OpenRouter multimodal to evaluate page aesthetics and functionality"""
        
        # Prepare the evaluation prompt
        prompt = f"""
        You are a UX/UI expert and web accessibility specialist. Please evaluate this webpage comprehensively.

        PAGE URL: {url}
        PAGE TITLE: {page_content.get('title', 'Unknown')}

        Please analyze both the visual screenshot and the page content to provide a detailed evaluation in the following areas:

        1. VISUAL DESIGN (0-10):
        - Color scheme and contrast
        - Typography and readability
        - Layout and spacing
        - Visual hierarchy
        - Brand consistency
        - Mobile responsiveness

        2. USER EXPERIENCE (0-10):
        - Navigation clarity
        - Information architecture
        - User flow and task completion
        - Error handling
        - Loading states
        - Interactive feedback

        3. ACCESSIBILITY (0-10):
        - Color contrast ratios
        - Keyboard navigation
        - Screen reader compatibility
        - Alt text for images
        - Form labels and structure
        - Focus indicators

        4. FUNCTIONALITY (0-10):
        - Working links and buttons
        - Form functionality
        - Interactive elements
        - Data loading and display
        - Error states
        - Performance

        5. CONTENT QUALITY (0-10):
        - Information clarity
        - Content organization
        - Data accuracy and completeness
        - Visual data representation
        - Help and documentation
        - Search functionality

        Please provide:
        - Numerical scores (0-10) for each category
        - Specific strengths and weaknesses
        - Actionable recommendations
        - Overall assessment
        - Priority fixes needed

        Be specific and reference visual elements you can see in the screenshot.
        """
        
        # Prepare the request payload
        payload = {
            "model": "openai/gpt-4o",  # Use GPT-4o for multimodal capabilities
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_b64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.3
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://comptroller.war.gov",
                    "X-Title": "Comptroller War Gov Evaluator"
                }
                
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result['choices'][0]['message']['content']
                        
                        # Parse the response to extract scores
                        scores = self.parse_evaluation_scores(content)
                        
                        return {
                            'raw_evaluation': content,
                            'scores': scores,
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'error': f"OpenRouter API error: {response.status} - {error_text}",
                            'timestamp': datetime.now().isoformat()
                        }
                        
        except Exception as e:
            return {
                'error': f"Error calling OpenRouter API: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def parse_evaluation_scores(self, content: str) -> Dict:
        """Parse numerical scores from the evaluation text"""
        scores = {}
        
        # Look for score patterns like "VISUAL DESIGN (0-10): 8.5" or "VISUAL DESIGN: 8/10"
        import re
        
        patterns = [
            r'VISUAL DESIGN.*?(\d+(?:\.\d+)?)',
            r'USER EXPERIENCE.*?(\d+(?:\.\d+)?)',
            r'ACCESSIBILITY.*?(\d+(?:\.\d+)?)',
            r'FUNCTIONALITY.*?(\d+(?:\.\d+)?)',
            r'CONTENT QUALITY.*?(\d+(?:\.\d+)?)'
        ]
        
        categories = ['visual_design', 'user_experience', 'accessibility', 'functionality', 'content_quality']
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    scores[categories[i]] = float(match.group(1))
                except ValueError:
                    scores[categories[i]] = 0
            else:
                scores[categories[i]] = 0
        
        # Calculate overall score
        if scores:
            scores['overall'] = sum(scores.values()) / len(scores)
        
        return scores
    
    def generate_report(self) -> Dict:
        """Generate comprehensive evaluation report"""
        successful_evaluations = [r for r in self.results if r['status'] == 'success']
        failed_evaluations = [r for r in self.results if r['status'] == 'error']
        
        # Calculate average scores across all pages
        all_scores = []
        for result in successful_evaluations:
            if 'evaluation' in result and 'scores' in result['evaluation']:
                all_scores.append(result['evaluation']['scores'])
        
        # Calculate averages
        avg_scores = {}
        if all_scores:
            for category in ['visual_design', 'user_experience', 'accessibility', 'functionality', 'content_quality']:
                category_scores = [s.get(category, 0) for s in all_scores if category in s]
                if category_scores:
                    avg_scores[category] = sum(category_scores) / len(category_scores)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(avg_scores, successful_evaluations)
        
        # Analyze link health
        link_analysis = self.analyze_link_health(successful_evaluations)
        
        report = {
            'evaluation_summary': {
                'total_pages_evaluated': len(self.results),
                'successful_evaluations': len(successful_evaluations),
                'failed_evaluations': len(failed_evaluations),
                'evaluation_date': datetime.now().isoformat(),
                'average_scores': avg_scores
            },
            'link_analysis': link_analysis,
            'page_evaluations': self.results,
            'recommendations': recommendations,
            'top_issues': self.identify_top_issues(successful_evaluations),
            'best_practices': self.identify_best_practices(successful_evaluations)
        }
        
        return report
    
    def analyze_link_health(self, evaluations: List[Dict]) -> Dict:
        """Analyze the health of all links across pages"""
        all_broken_links = []
        all_working_links = []
        total_links_checked = 0
        
        for evaluation in evaluations:
            if 'broken_links' in evaluation:
                all_broken_links.extend(evaluation['broken_links'])
            if 'working_links' in evaluation:
                all_working_links.extend(evaluation['working_links'])
            if 'link_check_summary' in evaluation:
                total_links_checked += evaluation['link_check_summary'].get('total_checked', 0)
        
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
        
        return {
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
        }
    
    def generate_recommendations(self, avg_scores: Dict, evaluations: List[Dict]) -> List[Dict]:
        """Generate actionable recommendations based on evaluation results"""
        recommendations = []
        
        # Low scoring categories
        for category, score in avg_scores.items():
            if score < 6:
                recommendations.append({
                    'priority': 'high',
                    'category': category,
                    'score': score,
                    'recommendation': f"Improve {category.replace('_', ' ').title()} - Current score: {score:.1f}/10"
                })
            elif score < 8:
                recommendations.append({
                    'priority': 'medium',
                    'category': category,
                    'score': score,
                    'recommendation': f"Enhance {category.replace('_', ' ').title()} - Current score: {score:.1f}/10"
                })
        
        return recommendations
    
    def identify_top_issues(self, evaluations: List[Dict]) -> List[str]:
        """Identify the most common issues across pages"""
        issues = []
        
        for evaluation in evaluations:
            if 'evaluation' in evaluation and 'raw_evaluation' in evaluation['evaluation']:
                content = evaluation['evaluation']['raw_evaluation'].lower()
                
                # Look for common issue patterns
                if 'contrast' in content and 'low' in content:
                    issues.append('Low color contrast')
                if 'navigation' in content and ('confusing' in content or 'unclear' in content):
                    issues.append('Navigation clarity issues')
                if 'mobile' in content and ('responsive' in content or 'mobile' in content):
                    issues.append('Mobile responsiveness concerns')
                if 'accessibility' in content and ('missing' in content or 'inadequate' in content):
                    issues.append('Accessibility gaps')
        
        # Count and return most common issues
        from collections import Counter
        issue_counts = Counter(issues)
        return [issue for issue, count in issue_counts.most_common(5)]
    
    def identify_best_practices(self, evaluations: List[Dict]) -> List[str]:
        """Identify best practices observed across pages"""
        practices = []
        
        for evaluation in evaluations:
            if 'evaluation' in evaluation and 'raw_evaluation' in evaluation['evaluation']:
                content = evaluation['evaluation']['raw_evaluation'].lower()
                
                # Look for positive patterns
                if 'clear' in content and 'navigation' in content:
                    practices.append('Clear navigation structure')
                if 'consistent' in content and 'design' in content:
                    practices.append('Consistent design system')
                if 'responsive' in content and 'mobile' in content:
                    practices.append('Good mobile responsiveness')
                if 'accessible' in content and 'good' in content:
                    practices.append('Strong accessibility features')
        
        # Count and return most common practices
        from collections import Counter
        practice_counts = Counter(practices)
        return [practice for practice, count in practice_counts.most_common(5)]
    
    async def save_report(self, report: Dict, filename: str = None):
        """Save evaluation report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"aesthetic_evaluation_report_{timestamp}.json"
        
        # Ensure reports directory exists
        os.makedirs("reports", exist_ok=True)
        filepath = os.path.join("reports", filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Report saved to: {filepath}")
        return filepath


async def main():
    """Main function to run the aesthetic evaluator"""
    # Get API key from environment
    openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
    if not openrouter_api_key:
        print("❌ Error: OPENROUTER_API_KEY environment variable not set")
        print("Please set your OpenRouter API key:")
        print("export OPENROUTER_API_KEY='your-api-key-here'")
        return
    
    # Create evaluator and run evaluation
    evaluator = AestheticEvaluator(openrouter_api_key)
    
    try:
        print("🚀 Starting comprehensive page evaluation...")
        report = await evaluator.evaluate_all_pages()
        
        # Save report
        report_file = await evaluator.save_report(report)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 EVALUATION SUMMARY")
        print("="*60)
        
        summary = report['evaluation_summary']
        print(f"📄 Pages Evaluated: {summary['total_pages_evaluated']}")
        print(f"✅ Successful: {summary['successful_evaluations']}")
        print(f"❌ Failed: {summary['failed_evaluations']}")
        
        if summary['average_scores']:
            print(f"\n📈 Average Scores:")
            for category, score in summary['average_scores'].items():
                print(f"  {category.replace('_', ' ').title()}: {score:.1f}/10")
        
        if report['recommendations']:
            print(f"\n🎯 Top Recommendations:")
            for rec in report['recommendations'][:3]:
                print(f"  {rec['priority'].upper()}: {rec['recommendation']}")
        
        # Link analysis summary
        if 'link_analysis' in report:
            link_analysis = report['link_analysis']
            print(f"\n🔗 Link Health Analysis:")
            print(f"  Total Links Checked: {link_analysis['total_links_checked']}")
            print(f"  Working Links: {link_analysis['working_links']}")
            print(f"  Broken Links: {link_analysis['broken_links']}")
            print(f"  Health Score: {link_analysis['health_score']:.1f}%")
            
            if link_analysis['critical_issues']:
                print(f"\n❌ Critical Issues (Missing Data Files):")
                for issue in link_analysis['critical_issues'][:5]:
                    print(f"  - {issue['url']}: {issue.get('error', 'Not found')}")
        
        print(f"\n📁 Full report saved to: {report_file}")
        
    except Exception as e:
        print(f"❌ Error during evaluation: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())