#!/usr/bin/env python3
"""
Analyze DD1414 document collection completeness
"""

import os
import re
from collections import defaultdict
from datetime import datetime

def analyze_dd1414_collection():
    """Analyze the completeness of DD1414 document collection"""
    
    print("📊 DD1414 Collection Analysis")
    print("=" * 50)
    
    # Find all DD1414 PDFs
    pdf_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.lower().endswith('.pdf') and 'dd' in file.lower() and '1414' in file.lower():
                pdf_files.append(os.path.join(root, file))
    
    print(f"📁 Total DD1414 PDFs found: {len(pdf_files)}")
    
    # Parse years and document types
    years = defaultdict(list)
    document_types = defaultdict(int)
    
    for pdf_file in pdf_files:
        filename = os.path.basename(pdf_file)
        
        # Extract year
        year_match = re.search(r'FY_(\d{4})', filename)
        if year_match:
            year = int(year_match.group(1))
            years[year].append(filename)
        
        # Extract document type
        if 'Base_for_Reprogramming_Actions' in filename:
            doc_type = 'Base for Reprogramming Actions'
        elif 'Call_Memo' in filename:
            doc_type = 'Call Memo'
        elif 'Service_Call_Memo' in filename:
            doc_type = 'Service Call Memo'
        elif 'Defense_Wide_Call_Memo' in filename:
            doc_type = 'Defense Wide Call Memo'
        elif 'PB_Directors' in filename:
            doc_type = 'PB Directors'
        else:
            doc_type = 'Other'
        
        document_types[doc_type] += 1
    
    # Display year-by-year analysis
    print(f"\n📅 Year-by-Year Analysis:")
    print("-" * 30)
    
    current_year = datetime.now().year
    expected_years = list(range(1997, current_year + 1))
    missing_years = []
    
    for year in sorted(years.keys()):
        docs = years[year]
        print(f"FY {year}: {len(docs)} documents")
        for doc in sorted(docs):
            print(f"  • {doc}")
        
        if year not in expected_years:
            print(f"  ⚠️  Unexpected year (outside 1997-{current_year})")
    
    # Check for missing years
    for year in expected_years:
        if year not in years:
            missing_years.append(year)
    
    if missing_years:
        print(f"\n❌ Missing years: {missing_years}")
    else:
        print(f"\n✅ All expected years present (1997-{current_year})")
    
    # Document type analysis
    print(f"\n📋 Document Type Analysis:")
    print("-" * 30)
    for doc_type, count in sorted(document_types.items()):
        print(f"{doc_type}: {count}")
    
    # Completeness assessment
    print(f"\n🎯 Completeness Assessment:")
    print("-" * 30)
    
    total_expected_years = len(expected_years)
    years_with_docs = len([y for y in expected_years if y in years])
    completeness_percentage = (years_with_docs / total_expected_years) * 100
    
    print(f"Years covered: {years_with_docs}/{total_expected_years} ({completeness_percentage:.1f}%)")
    
    # Check for recent years
    recent_years = [y for y in range(current_year - 2, current_year + 1) if y in years]
    print(f"Recent years (last 3): {len(recent_years)}/3")
    
    # Check for base documents (most important)
    base_docs = [y for y in years.keys() if any('Base_for_Reprogramming_Actions' in doc for doc in years[y])]
    print(f"Years with Base documents: {len(base_docs)}/{total_expected_years}")
    
    # Overall assessment
    print(f"\n📊 Overall Assessment:")
    print("-" * 30)
    
    if completeness_percentage >= 90:
        status = "🟢 EXCELLENT"
        recommendation = "Collection is very complete"
    elif completeness_percentage >= 75:
        status = "🟡 GOOD"
        recommendation = "Collection is mostly complete, some gaps"
    elif completeness_percentage >= 50:
        status = "🟠 FAIR"
        recommendation = "Collection has significant gaps"
    else:
        status = "🔴 POOR"
        recommendation = "Collection is incomplete"
    
    print(f"Status: {status}")
    print(f"Recommendation: {recommendation}")
    
    # Specific recommendations
    print(f"\n💡 Recommendations:")
    print("-" * 30)
    
    if missing_years:
        print(f"• Focus on missing years: {missing_years[:5]}{'...' if len(missing_years) > 5 else ''}")
    
    if len(base_docs) < total_expected_years * 0.8:
        print("• Prioritize Base for Reprogramming Actions documents")
    
    if len(recent_years) < 3:
        print("• Ensure recent years (2022-2024) are complete")
    
    print("• Consider adding Call Memos for years that only have Base documents")
    
    return {
        'total_documents': len(pdf_files),
        'years_covered': years_with_docs,
        'total_expected_years': total_expected_years,
        'completeness_percentage': completeness_percentage,
        'missing_years': missing_years,
        'document_types': dict(document_types)
    }

if __name__ == "__main__":
    results = analyze_dd1414_collection()
    
    print(f"\n📈 Summary:")
    print(f"Total DD1414 documents: {results['total_documents']}")
    print(f"Completeness: {results['completeness_percentage']:.1f}%")
    print(f"Missing years: {len(results['missing_years'])}")