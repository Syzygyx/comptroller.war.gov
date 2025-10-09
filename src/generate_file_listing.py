#!/usr/bin/env python3
"""
Generate file listing for data browser
"""

import os
import json
from pathlib import Path
from datetime import datetime

def generate_file_listing():
    """Generate a comprehensive file listing for the data browser"""
    
    file_listing = {
        "generated": datetime.now().isoformat(),
        "categories": {
            "dd1414": {
                "title": "DD1414 Reprogramming Forms",
                "icon": "📋",
                "description": "Structured data from DD1414 reprogramming action forms",
                "files": []
            },
            "enhanced": {
                "title": "Enhanced Analysis Data", 
                "icon": "🔍",
                "description": "Comprehensive analysis with OCR processing and confidence scoring",
                "files": []
            },
            "extracted": {
                "title": "Extracted CSV Data",
                "icon": "📊", 
                "description": "Individual CSV files extracted from PDF documents",
                "files": []
            },
            "metadata": {
                "title": "Metadata & Configuration",
                "icon": "⚙️",
                "description": "System metadata, configuration files, and processing logs",
                "files": []
            }
        }
    }
    
    # Scan for DD1414 enhanced data
    dd1414_dir = Path("data/dd1414_csv")
    if dd1414_dir.exists():
        for file_path in dd1414_dir.glob("*"):
            if file_path.is_file():
                size = file_path.stat().st_size
                file_info = {
                    "name": file_path.name,
                    "path": f"data/dd1414_csv/{file_path.name}",
                    "size": format_size(size),
                    "type": "enhanced" if "enhanced" in file_path.name else "dd1414",
                    "description": get_file_description(file_path.name),
                    "records": estimate_records(file_path)
                }
                file_listing["categories"]["enhanced"]["files"].append(file_info)
    
    # Scan for extracted CSV files
    csv_dir = Path("data/csv")
    if csv_dir.exists():
        for file_path in csv_dir.glob("*.csv"):
            size = file_path.stat().st_size
            file_info = {
                "name": file_path.stem.replace("_extracted", ""),
                "path": f"data/csv/{file_path.name}",
                "size": format_size(size),
                "type": "dd1414" if "DD_1414" in file_path.name else "extracted",
                "description": get_file_description(file_path.name),
                "records": estimate_records(file_path)
            }
            file_listing["categories"]["extracted"]["files"].append(file_info)
    
    # Scan for metadata files
    metadata_files = [
        "data/metadata.json",
        "data/dd1414_csv/dd1414_summary.json"
    ]
    
    for file_path in metadata_files:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            file_info = {
                "name": Path(file_path).name,
                "path": file_path,
                "size": format_size(size),
                "type": "metadata",
                "description": "System metadata and configuration",
                "records": 1
            }
            file_listing["categories"]["metadata"]["files"].append(file_info)
    
    # Save file listing
    output_path = Path("docs/data/file_listing.json")
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(file_listing, f, indent=2)
    
    print(f"Generated file listing with {sum(len(cat['files']) for cat in file_listing['categories'].values())} files")
    return file_listing

def format_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f}MB"

def get_file_description(filename):
    """Get description based on filename"""
    if "dd1414_enhanced" in filename:
        return "Complete DD1414 analysis with OCR processing and confidence scoring"
    elif "dd1414_fast" in filename:
        return "Fast extraction results for DD1414 documents"
    elif "dd1414_summary" in filename:
        return "Summary statistics and analysis metrics"
    elif "DD_1414" in filename:
        return "DD1414 reprogramming form data"
    elif "extracted" in filename:
        return "Extracted data from PDF document"
    else:
        return "Data file"

def estimate_records(file_path):
    """Estimate number of records in a file"""
    try:
        if file_path.suffix == '.csv':
            with open(file_path, 'r') as f:
                return len(f.readlines()) - 1  # Subtract header
        elif file_path.suffix == '.json':
            with open(file_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return len(data)
                else:
                    return 1
        else:
            return "?"
    except:
        return "?"

if __name__ == "__main__":
    generate_file_listing()