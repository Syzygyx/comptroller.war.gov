#!/usr/bin/env python3
"""
Analyze Files from Previous Years

This script analyzes what files are available from previous years (before 2007)
to understand what documentation existed before DD1414 forms were introduced.
"""

import os
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def analyze_previous_years():
    """Analyze files from previous years"""
    
    print("🔍 Analyzing Files from Previous Years")
    print("=" * 50)
    
    # Find all PDF files
    pdf_files = list(Path('data/pdfs').glob('*.pdf'))
    print(f"📁 Total PDFs analyzed: {len(pdf_files)}")
    
    # Categorize files by year and type
    files_by_year = defaultdict(list)
    files_by_type = defaultdict(list)
    
    for pdf_file in pdf_files:
        filename = pdf_file.name
        
        # Extract year from filename
        year = None
        
        # Check for FY_YYYY pattern
        fy_match = re.search(r'FY_(\d{4})', filename)
        if fy_match:
            year = int(fy_match.group(1))
        else:
            # Check for YY- pattern (e.g., 99-, 05-)
            yy_match = re.search(r'^(\d{2})-', filename)
            if yy_match:
                yy = int(yy_match.group(1))
                if yy >= 90:  # 1990s
                    year = 1900 + yy
                else:  # 2000s
                    year = 2000 + yy
        
        if year:
            files_by_year[year].append(filename)
            
            # Categorize by type
            if 'DD_1414' in filename:
                files_by_type['dd1414'].append(filename)
            elif 'reprogram' in filename.lower():
                files_by_type['reprogramming'].append(filename)
            elif 'omnibus' in filename.lower():
                files_by_type['omnibus'].append(filename)
            elif 'call' in filename.lower():
                files_by_type['call_memo'].append(filename)
            elif 'transfer' in filename.lower():
                files_by_type['transfer'].append(filename)
            elif 'PA_' in filename:
                files_by_type['prior_approval'].append(filename)
            elif 'IR_' in filename:
                files_by_type['internal_reprogramming'].append(filename)
            elif 'LTR_' in filename:
                files_by_type['letter'].append(filename)
            elif 'MC_' in filename:
                files_by_type['military_construction'].append(filename)
            else:
                files_by_type['other'].append(filename)
    
    # Focus on previous years (before 2007)
    previous_years = {year: files for year, files in files_by_year.items() if year < 2007}
    
    print(f"\n📅 Files from Previous Years (Before 2007):")
    print("-" * 50)
    
    total_previous = 0
    for year in sorted(previous_years.keys()):
        files = previous_years[year]
        total_previous += len(files)
        print(f"\n📆 {year}: {len(files)} files")
        
        # Show first few files
        for file in files[:5]:
            print(f"  • {file}")
        if len(files) > 5:
            print(f"  ... and {len(files) - 5} more")
    
    print(f"\n📊 Total files from previous years: {total_previous}")
    
    # Analyze by document type for previous years
    print(f"\n📋 Document Types in Previous Years:")
    print("-" * 40)
    
    for doc_type, files in files_by_type.items():
        # Filter for previous years
        previous_files = [f for f in files if any(year < 2007 for year in files_by_year.keys() if f in files_by_year[year])]
        if previous_files:
            print(f"\n{doc_type.replace('_', ' ').title()}: {len(previous_files)} files")
            for file in previous_files[:3]:
                print(f"  • {file}")
            if len(previous_files) > 3:
                print(f"  ... and {len(previous_files) - 3} more")
    
    # Look for specific patterns in previous years
    print(f"\n🔍 Specific Patterns in Previous Years:")
    print("-" * 40)
    
    # Check for form numbers
    form_numbers = defaultdict(list)
    for year, files in previous_years.items():
        for file in files:
            # Look for form numbers
            form_match = re.search(r'(\d{4})', file)
            if form_match:
                form_num = form_match.group(1)
                form_numbers[form_num].append(file)
    
    print(f"\nForm Numbers Found:")
    for form_num, files in sorted(form_numbers.items()):
        print(f"  Form {form_num}: {len(files)} files")
        for file in files[:2]:
            print(f"    • {file}")
        if len(files) > 2:
            print(f"    ... and {len(files) - 2} more")
    
    # Check for reprogramming-related files
    print(f"\n🔄 Reprogramming-Related Files in Previous Years:")
    print("-" * 50)
    
    reprogramming_files = []
    for year, files in previous_years.items():
        for file in files:
            if any(keyword in file.lower() for keyword in [
                'reprogram', 'transfer', 'base', 'action', 'call', 'memo'
            ]):
                reprogramming_files.append((year, file))
    
    if reprogramming_files:
        print(f"Found {len(reprogramming_files)} reprogramming-related files:")
        for year, file in reprogramming_files[:10]:
            print(f"  {year}: {file}")
        if len(reprogramming_files) > 10:
            print(f"  ... and {len(reprogramming_files) - 10} more")
    else:
        print("No reprogramming-related files found in previous years")
    
    # Summary by decade
    print(f"\n📈 Summary by Decade:")
    print("-" * 30)
    
    decades = defaultdict(int)
    for year, files in previous_years.items():
        decade = (year // 10) * 10
        decades[decade] += len(files)
    
    for decade in sorted(decades.keys()):
        print(f"{decade}s: {decades[decade]} files")
    
    return {
        'previous_years': previous_years,
        'total_previous': total_previous,
        'form_numbers': form_numbers,
        'reprogramming_files': reprogramming_files,
        'decades': decades
    }

if __name__ == "__main__":
    results = analyze_previous_years()