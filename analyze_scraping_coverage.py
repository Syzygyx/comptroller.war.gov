#!/usr/bin/env python3
"""
Analyze scraping coverage and identify missing content
"""

import os
import re
import requests
from collections import defaultdict
from datetime import datetime
from pathlib import Path

def analyze_scraping_coverage():
    """Analyze what we scraped vs what's available"""
    
    print("🔍 Scraping Coverage Analysis")
    print("=" * 50)
    
    # Check what we have
    pdf_files = list(Path('data/pdfs').glob('*.pdf'))
    print(f"📁 Total PDFs downloaded: {len(pdf_files)}")
    
    # Analyze by year
    years = defaultdict(list)
    for pdf_file in pdf_files:
        filename = pdf_file.name
        year_match = re.search(r'(\d{4})', filename)
        if year_match:
            year = int(year_match.group(1))
            years[year].append(filename)
    
    print(f"\n📅 Years covered: {sorted(years.keys())}")
    print(f"📊 Year range: {min(years.keys())} - {max(years.keys())}")
    
    # Check for DD1414 specifically
    dd1414_files = [f for f in pdf_files if 'dd' in f.name.lower() and '1414' in f.name.lower()]
    print(f"\n📋 DD1414 documents: {len(dd1414_files)}")
    
    # Check what the scraper was configured to scrape
    print(f"\n🎯 Scraper Configuration:")
    print("Target URLs:")
    print("  • https://comptroller.defense.gov/Budget-Execution/Reprogramming/")
    print("  • https://comptroller.defense.gov/Portals/45/Documents/execution/reprogramming/fy2025/")
    print("  • https://comptroller.defense.gov/Portals/45/Documents/execution/reprogramming/fy2024/")
    print("  • https://comptroller.defense.gov/Portals/45/Documents/execution/reprogramming/fy2023/")
    print("  • https://comptroller.defense.gov/Portals/45/Documents/execution/reprogramming/fy2022/")
    
    # Check if we're missing earlier years
    current_year = datetime.now().year
    expected_years = list(range(1997, current_year + 1))
    missing_years = [y for y in expected_years if y not in years]
    
    print(f"\n❌ Missing years: {missing_years}")
    
    # Check if there are additional URLs we should be scraping
    print(f"\n🔍 Checking for additional content...")
    
    # Check main reprogramming page
    try:
        response = requests.get("https://comptroller.defense.gov/Budget-Execution/Reprogramming/", timeout=10)
        if response.status_code == 200:
            content = response.text
            # Look for additional year links
            year_links = re.findall(r'href="[^"]*fy(\d{4})[^"]*"', content, re.IGNORECASE)
            available_years = set(int(year) for year in year_links)
            print(f"📊 Years found on main page: {sorted(available_years)}")
            
            # Check for missing years that might be available
            potentially_available = available_years.intersection(set(missing_years))
            if potentially_available:
                print(f"🎯 Potentially available missing years: {sorted(potentially_available)}")
        else:
            print(f"❌ Could not access main page: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking main page: {e}")
    
    # Check if we have comprehensive coverage for the years we do have
    print(f"\n📊 Coverage Analysis for Available Years:")
    for year in sorted(years.keys()):
        files = years[year]
        print(f"  FY {year}: {len(files)} files")
        
        # Check for different document types
        doc_types = set()
        for file in files:
            if 'dd' in file.lower() and '1414' in file.lower():
                doc_types.add('DD1414')
            elif 'call' in file.lower() and 'memo' in file.lower():
                doc_types.add('Call Memo')
            elif 'base' in file.lower() and 'reprogramming' in file.lower():
                doc_types.add('Base Document')
            elif 'transfer' in file.lower():
                doc_types.add('Transfer')
            elif 'ir' in file.lower():
                doc_types.add('Information Request')
            else:
                doc_types.add('Other')
        
        print(f"    Types: {', '.join(sorted(doc_types))}")
    
    # Check if we need to scrape additional URLs
    print(f"\n💡 Recommendations:")
    print("-" * 30)
    
    if missing_years:
        print(f"• Missing {len(missing_years)} years: {missing_years[:5]}{'...' if len(missing_years) > 5 else ''}")
        print("• Check if these years exist under different URL patterns")
        print("• Consider scraping historical archives")
    
    # Check if we should add more URLs to the scraper
    additional_urls = []
    for year in range(1997, 2022):  # Check years before our current coverage
        if year not in years:
            # Try to construct potential URLs
            potential_urls = [
                f"https://comptroller.defense.gov/Portals/45/Documents/execution/reprogramming/fy{year}/",
                f"https://comptroller.defense.gov/Budget-Execution/Reprogramming/fy{year}/",
                f"https://comptroller.defense.gov/Portals/45/Documents/execution/reprogramming/archive/fy{year}/"
            ]
            additional_urls.extend(potential_urls)
    
    if additional_urls:
        print(f"• Consider adding {len(additional_urls)} additional URLs to scraper")
        print("• Focus on years 1997-2006 for complete historical coverage")
    
    # Check if we have a complete set for recent years
    recent_years = [y for y in range(current_year - 3, current_year + 1) if y in years]
    if len(recent_years) >= 3:
        print(f"✅ Recent years coverage looks good: {recent_years}")
    else:
        print(f"⚠️  Recent years coverage incomplete: {recent_years}")
    
    return {
        'total_pdfs': len(pdf_files),
        'years_covered': len(years),
        'missing_years': missing_years,
        'dd1414_count': len(dd1414_files),
        'coverage_percentage': len(years) / len(expected_years) * 100
    }

if __name__ == "__main__":
    results = analyze_scraping_coverage()
    
    print(f"\n📈 Summary:")
    print(f"Total PDFs: {results['total_pdfs']}")
    print(f"Years covered: {results['years_covered']}")
    print(f"Coverage: {results['coverage_percentage']:.1f}%")
    print(f"DD1414 documents: {results['dd1414_count']}")
    print(f"Missing years: {len(results['missing_years'])}")