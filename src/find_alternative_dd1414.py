#!/usr/bin/env python3
"""
Find Alternative DD1414 Files

This script searches for DD1414 forms that might be named differently,
including variations in form numbers, naming conventions, and abbreviations.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def find_alternative_dd1414():
    """Find potential DD1414 files with different naming patterns"""
    
    print("🔍 Searching for Alternative DD1414 Files")
    print("=" * 50)
    
    # Find all PDF files
    pdf_files = list(Path('data/pdfs').glob('*.pdf'))
    print(f"📁 Total PDFs analyzed: {len(pdf_files)}")
    
    # Define search patterns for potential DD1414 files
    patterns = {
        'dd1414_standard': r'DD_1414',
        'dd1414_variations': r'DD.*1414|1414.*DD',
        'form_numbers': r'141[4-9]|142[0-9]|143[0-9]',
        'reprogramming_keywords': r'reprogram.*action|base.*action|call.*memo',
        'omnibus_calls': r'omnibus.*call|call.*omnibus',
        'budget_forms': r'budget.*form|form.*budget',
        'defense_forms': r'defense.*form|form.*defense',
        'military_forms': r'military.*form|form.*military'
    }
    
    # Search results
    results = defaultdict(list)
    
    for pdf_file in pdf_files:
        filename = pdf_file.name
        
        # Check each pattern
        for pattern_name, pattern in patterns.items():
            if re.search(pattern, filename, re.IGNORECASE):
                results[pattern_name].append(filename)
    
    # Display results
    print(f"\n📋 Search Results by Pattern:")
    print("-" * 40)
    
    for pattern_name, files in results.items():
        print(f"\n🔍 {pattern_name.replace('_', ' ').title()}: {len(files)} files")
        for file in files[:5]:  # Show first 5 files
            print(f"  • {file}")
        if len(files) > 5:
            print(f"  ... and {len(files) - 5} more")
    
    # Analyze potential DD1414 alternatives
    print(f"\n🎯 Potential DD1414 Alternatives:")
    print("-" * 40)
    
    # Look for files that might be DD1414 but with different names
    potential_alternatives = []
    
    for pdf_file in pdf_files:
        filename = pdf_file.name
        
        # Check for reprogramming-related files that might be DD1414
        if any(keyword in filename.lower() for keyword in [
            'reprogram', 'base', 'action', 'call', 'memo', 'omnibus'
        ]) and 'DD_1414' not in filename:
            potential_alternatives.append(filename)
    
    print(f"Found {len(potential_alternatives)} potential alternatives:")
    for file in potential_alternatives[:10]:
        print(f"  • {file}")
    if len(potential_alternatives) > 10:
        print(f"  ... and {len(potential_alternatives) - 10} more")
    
    # Look for form number variations
    print(f"\n📄 Form Number Variations:")
    print("-" * 40)
    
    form_variations = []
    for pdf_file in pdf_files:
        filename = pdf_file.name
        # Look for 1414, 1415, 1416, etc.
        if re.search(r'141[4-9]|142[0-9]', filename):
            form_variations.append(filename)
    
    print(f"Found {len(form_variations)} files with form number variations:")
    for file in form_variations:
        print(f"  • {file}")
    
    # Analyze by year to see if we're missing any years
    print(f"\n📅 Year Analysis:")
    print("-" * 40)
    
    # Get all DD1414 files by year
    dd1414_years = set()
    for file in results['dd1414_standard']:
        year_match = re.search(r'FY_(\d{4})', file)
        if year_match:
            dd1414_years.add(int(year_match.group(1)))
    
    # Get all reprogramming files by year
    reprogramming_years = set()
    for file in results['reprogramming_keywords']:
        year_match = re.search(r'FY_(\d{4})', file)
        if year_match:
            reprogramming_years.add(int(year_match.group(1)))
    
    print(f"DD1414 years: {sorted(dd1414_years)}")
    print(f"Reprogramming years: {sorted(reprogramming_years)}")
    
    # Find years with reprogramming but no DD1414
    missing_years = reprogramming_years - dd1414_years
    if missing_years:
        print(f"Years with reprogramming but no DD1414: {sorted(missing_years)}")
        
        # Find files for these years
        for year in sorted(missing_years):
            year_files = [f for f in results['reprogramming_keywords'] if f'FY_{year}' in f]
            print(f"  FY {year}: {year_files}")
    
    # Summary
    print(f"\n📊 Summary:")
    print("-" * 30)
    print(f"Standard DD1414 files: {len(results['dd1414_standard'])}")
    print(f"DD1414 variations: {len(results['dd1414_variations'])}")
    print(f"Form number variations: {len(form_variations)}")
    print(f"Reprogramming files: {len(results['reprogramming_keywords'])}")
    print(f"Omnibus call files: {len(results['omnibus_calls'])}")
    print(f"Potential alternatives: {len(potential_alternatives)}")
    
    return {
        'dd1414_standard': results['dd1414_standard'],
        'dd1414_variations': results['dd1414_variations'],
        'form_variations': form_variations,
        'potential_alternatives': potential_alternatives,
        'missing_years': missing_years
    }

if __name__ == "__main__":
    results = find_alternative_dd1414()