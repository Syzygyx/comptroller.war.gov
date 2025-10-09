#!/usr/bin/env python3
"""
Search for early DD1414 documents with alternative naming patterns
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def search_early_dd1414():
    """Search for early DD1414 documents with alternative naming patterns"""
    
    print("🔍 Searching for Early DD1414 Documents")
    print("=" * 50)
    
    # Find all PDFs
    pdf_files = list(Path('data/pdfs').glob('*.pdf'))
    
    # Focus on early years (1997-2006)
    early_years = list(range(1997, 2007))
    
    # Alternative patterns that might be DD1414 forms
    alternative_patterns = [
        # Direct form references
        r'form.*dd',
        r'dd.*form',
        r'1414',
        
        # Reprogramming patterns
        r'reprogram.*action',
        r'base.*action',
        r'reprogram.*memo',
        r'call.*memo',
        
        # Budget/defense patterns
        r'budget.*reprogram',
        r'defense.*reprogram',
        r'omnibus.*reprogram',
        
        # Generic patterns
        r'reprogram.*request',
        r'reprogram.*package',
        r'reprogram.*letter',
        
        # Specific early year patterns
        r'19\d{2}.*reprogram',
        r'20[0-6].*reprogram',
        r'fy.*19\d{2}.*reprogram',
        r'fy.*20[0-6].*reprogram'
    ]
    
    print(f"📁 Searching {len(pdf_files)} PDFs for early DD1414 patterns...")
    
    # Search for each pattern
    pattern_matches = defaultdict(list)
    
    for pattern in alternative_patterns:
        matches = []
        for pdf_file in pdf_files:
            if re.search(pattern, pdf_file.name, re.IGNORECASE):
                # Extract year from filename
                year_match = re.search(r'(\d{4})', pdf_file.name)
                if year_match:
                    year = int(year_match.group(1))
                    if year in early_years:
                        matches.append((pdf_file.name, year))
        
        if matches:
            pattern_matches[pattern] = matches
    
    # Display results
    print(f"\n📋 Potential Early DD1414 Documents Found:")
    print("-" * 50)
    
    total_found = 0
    for pattern, matches in pattern_matches.items():
        print(f"\n🔍 Pattern: '{pattern}'")
        print(f"   Found {len(matches)} matches in early years:")
        
        # Group by year
        by_year = defaultdict(list)
        for filename, year in matches:
            by_year[year].append(filename)
        
        for year in sorted(by_year.keys()):
            print(f"   FY {year}:")
            for filename in by_year[year]:
                print(f"     • {filename}")
                total_found += 1
    
    # Look for documents that might be DD1414 but don't match patterns
    print(f"\n🔍 Manual Review of Early Year Documents:")
    print("-" * 50)
    
    early_docs = []
    for pdf_file in pdf_files:
        year_match = re.search(r'(\d{4})', pdf_file.name)
        if year_match:
            year = int(year_match.group(1))
            if year in early_years:
                early_docs.append((pdf_file.name, year))
    
    # Group by year
    by_year = defaultdict(list)
    for filename, year in early_docs:
        by_year[year].append(filename)
    
    for year in sorted(by_year.keys()):
        docs = by_year[year]
        print(f"\nFY {year}: {len(docs)} documents")
        
        # Look for documents that might be DD1414 related
        potential_dd1414 = []
        for filename in docs:
            # Check for keywords that might indicate DD1414 content
            if any(keyword in filename.lower() for keyword in [
                'reprogram', 'action', 'memo', 'call', 'budget', 'defense',
                'transfer', 'request', 'package', 'letter', 'base'
            ]):
                potential_dd1414.append(filename)
        
        if potential_dd1414:
            print(f"  Potential DD1414 related ({len(potential_dd1414)}):")
            for doc in potential_dd1414:
                print(f"    • {doc}")
        else:
            print(f"  No obvious DD1414 related documents")
    
    # Check if any early documents might be DD1414 forms with different names
    print(f"\n🔍 Checking for Hidden DD1414 Forms:")
    print("-" * 50)
    
    # Look for documents that might contain DD1414 in their content
    # (This would require opening PDFs, which we'll skip for now)
    print("Note: To check if early documents contain DD1414 forms,")
    print("we would need to open and analyze the PDF content.")
    print("This would require OCR processing of the documents.")
    
    # Summary
    print(f"\n📊 Summary:")
    print("-" * 30)
    print(f"Total early year documents: {len(early_docs)}")
    print(f"Pattern matches found: {total_found}")
    print(f"Years with documents: {sorted(by_year.keys())}")
    
    # Conclusions
    print(f"\n📝 Conclusions:")
    print("-" * 30)
    print("1. DD1414 form appears to start in FY 2007")
    print("2. Early years (1997-2006) may not have used DD1414 form")
    print("3. Alternative forms or naming conventions may have been used")
    print("4. Documents from early years may be different types")
    print("5. Need to check PDF content to confirm if DD1414 forms exist")
    
    return {
        'total_early_docs': len(early_docs),
        'pattern_matches': total_found,
        'years_with_docs': len(by_year)
    }

if __name__ == "__main__":
    results = search_early_dd1414()
    
    print(f"\n🎯 Final Results:")
    print(f"Early year documents: {results['total_early_docs']}")
    print(f"Pattern matches: {results['pattern_matches']}")
    print(f"Years covered: {results['years_with_docs']}")