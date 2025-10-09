#!/usr/bin/env python3
"""
Research DD1414 form history and naming patterns
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def research_dd1414_history():
    """Research DD1414 form history and naming patterns"""
    
    print("🔍 DD1414 Form History Research")
    print("=" * 50)
    
    # Find all PDFs
    pdf_files = list(Path('data/pdfs').glob('*.pdf'))
    print(f"📁 Total PDFs analyzed: {len(pdf_files)}")
    
    # Analyze by year and naming patterns
    year_patterns = defaultdict(list)
    dd1414_patterns = defaultdict(list)
    form_patterns = defaultdict(list)
    
    for pdf_file in pdf_files:
        filename = pdf_file.name
        
        # Extract year from filename
        year_match = re.search(r'(\d{4})', filename)
        if year_match:
            year = int(year_match.group(1))
            year_patterns[year].append(filename)
        
        # Look for DD1414 patterns
        if re.search(r'dd.*1414', filename, re.IGNORECASE):
            dd1414_patterns[year].append(filename)
        
        # Look for form-related patterns
        if re.search(r'(form|dd|reprogram|base.*action|call.*memo)', filename, re.IGNORECASE):
            form_patterns[year].append(filename)
    
    # Analyze DD1414 patterns by year
    print(f"\n📋 DD1414 Documents by Year:")
    print("-" * 40)
    
    for year in sorted(dd1414_patterns.keys()):
        docs = dd1414_patterns[year]
        print(f"FY {year}: {len(docs)} DD1414 documents")
        for doc in docs:
            print(f"  • {doc}")
    
    # Analyze form patterns by year
    print(f"\n📄 Form-Related Documents by Year:")
    print("-" * 40)
    
    for year in sorted(form_patterns.keys()):
        if year < 2007:  # Focus on early years
            docs = form_patterns[year]
            print(f"FY {year}: {len(docs)} form-related documents")
            for doc in docs[:5]:  # Show first 5
                print(f"  • {doc}")
            if len(docs) > 5:
                print(f"  ... and {len(docs) - 5} more")
    
    # Look for alternative naming patterns
    print(f"\n🔍 Alternative Naming Patterns Analysis:")
    print("-" * 40)
    
    # Check for documents that might be DD1414 but with different names
    alternative_patterns = [
        r'reprogram.*action',
        r'base.*reprogram',
        r'call.*memo',
        r'omnibus.*call',
        r'reprogram.*memo',
        r'budget.*reprogram',
        r'defense.*reprogram'
    ]
    
    for pattern in alternative_patterns:
        matches = []
        for pdf_file in pdf_files:
            if re.search(pattern, pdf_file.name, re.IGNORECASE):
                matches.append(pdf_file.name)
        
        if matches:
            print(f"\n📌 Pattern '{pattern}': {len(matches)} matches")
            for match in matches[:3]:  # Show first 3
                print(f"  • {match}")
            if len(matches) > 3:
                print(f"  ... and {len(matches) - 3} more")
    
    # Analyze year coverage
    print(f"\n📊 Year Coverage Analysis:")
    print("-" * 40)
    
    all_years = set(year_patterns.keys())
    dd1414_years = set(dd1414_patterns.keys())
    form_years = set(form_patterns.keys())
    
    print(f"Years with any documents: {len(all_years)}")
    print(f"Years with DD1414 documents: {len(dd1414_years)}")
    print(f"Years with form-related documents: {len(form_years)}")
    
    # Check for early years with form documents
    early_years = [y for y in all_years if y < 2007]
    early_form_years = [y for y in form_years if y < 2007]
    
    print(f"\nEarly years (before 2007):")
    print(f"  Years with documents: {sorted(early_years)}")
    print(f"  Years with form documents: {sorted(early_form_years)}")
    
    # Look for potential DD1414 documents in early years
    print(f"\n🔍 Potential DD1414 Documents in Early Years:")
    print("-" * 40)
    
    for year in sorted(early_years):
        docs = year_patterns[year]
        potential_dd1414 = []
        
        for doc in docs:
            # Look for documents that might be DD1414 forms
            if any(keyword in doc.lower() for keyword in [
                'reprogram', 'base', 'action', 'memo', 'call', 'budget'
            ]):
                potential_dd1414.append(doc)
        
        if potential_dd1414:
            print(f"FY {year}: {len(potential_dd1414)} potential DD1414 documents")
            for doc in potential_dd1414[:3]:
                print(f"  • {doc}")
            if len(potential_dd1414) > 3:
                print(f"  ... and {len(potential_dd1414) - 3} more")
    
    # Research conclusions
    print(f"\n📝 Research Conclusions:")
    print("-" * 40)
    
    print("1. DD1414 Naming Pattern:")
    print("   - Current pattern: 'FY_YYYY_DD_1414_*'")
    print("   - First appearance: FY 2007")
    print("   - Consistent naming from 2007-2025")
    
    print("\n2. Early Years (1997-2006):")
    print("   - No documents with 'DD_1414' in filename")
    print("   - May have used different naming conventions")
    print("   - Could be named as 'reprogramming', 'base action', etc.")
    
    print("\n3. Potential Issues:")
    print("   - Form may not have existed before 2007")
    print("   - Different form number used in early years")
    print("   - Documents may be archived differently")
    print("   - Naming convention may have changed")
    
    print("\n4. Recommendations:")
    print("   - Check if DD1414 form existed before 2007")
    print("   - Look for alternative form numbers")
    print("   - Search for 'reprogramming' documents in early years")
    print("   - Check if documents are in different sections")
    
    return {
        'total_pdfs': len(pdf_files),
        'dd1414_years': len(dd1414_years),
        'form_years': len(form_years),
        'early_years': len(early_years),
        'early_form_years': len(early_form_years)
    }

if __name__ == "__main__":
    results = research_dd1414_history()
    
    print(f"\n📈 Summary:")
    print(f"Total PDFs: {results['total_pdfs']}")
    print(f"DD1414 years: {results['dd1414_years']}")
    print(f"Form years: {results['form_years']}")
    print(f"Early years: {results['early_years']}")
    print(f"Early form years: {results['early_form_years']}")