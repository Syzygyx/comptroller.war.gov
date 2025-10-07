#!/usr/bin/env python3
"""
CSV Transformer - Converts OCR text to structured CSV
Adapted from StealthOCR's PDF to CSV transformation logic
"""

import re
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

import pandas as pd


class CSVTransformer:
    """Transforms OCR text to structured CSV format"""
    
    # Standard CSV columns (matching StealthOCR format)
    COLUMNS = [
        'appropriation_category',
        'appropriation code',
        'appropriation activity',
        'branch',
        'fiscal_year_start',
        'fiscal_year_end',
        'budget_activity_number',
        'budget_activity_title',
        'pem',
        'budget_title',
        'program_base_congressional',
        'program_base_dod',
        'reprogramming_amount',
        'revised_program_total',
        'explanation',
        'file'
    ]
    
    def __init__(self):
        """Initialize transformer"""
        self.patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for text extraction"""
        return {
            # Branch patterns
            'army_section': re.compile(r'ARMY\s+(?:INCREASE|DECREASE)', re.IGNORECASE),
            'navy_section': re.compile(r'NAVY\s+(?:INCREASE|DECREASE)', re.IGNORECASE),
            'air_force_section': re.compile(r'AIR\s+FORCE\s+(?:INCREASE|DECREASE)', re.IGNORECASE),
            'defense_wide_section': re.compile(r'DEFENSE-WIDE\s+(?:INCREASE|DECREASE)', re.IGNORECASE),
            'marines_section': re.compile(r'MARINE\s+CORPS\s+(?:INCREASE|DECREASE)', re.IGNORECASE),
            'coast_guard_section': re.compile(r'COAST\s+GUARD\s+(?:INCREASE|DECREASE)', re.IGNORECASE),
            
            # Appropriation category patterns
            'operation_maintenance': re.compile(r'Operation\s+and\s+Maintenance', re.IGNORECASE),
            'weapons_procurement': re.compile(r'Weapons?\s+Procurement', re.IGNORECASE),
            'missile_procurement': re.compile(r'Missile\s+Procurement', re.IGNORECASE),
            'procurement': re.compile(r'Procurement(?!,)', re.IGNORECASE),
            'rdte': re.compile(r'RDTE|Research.*Development', re.IGNORECASE),
            
            # Budget activity
            'budget_activity': re.compile(r'Budget\s+Activity\s+(\d+):\s*([^\n]+)', re.IGNORECASE),
            
            # Fiscal year
            'fiscal_year': re.compile(r'(?:FY|Fiscal\s+Year)\s*(\d{2,4})[/-]?(\d{2,4})?', re.IGNORECASE),
            
            # Financial amounts (in thousands)
            'amount': re.compile(r'[+\-]?\$?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', re.IGNORECASE),
            
            # Explanation
            'explanation': re.compile(r'Explanation:\s*([^\n]+(?:\n(?!(?:ARMY|NAVY|AIR FORCE|DEFENSE-WIDE|Budget Activity|Explanation))[^\n]+)*)', re.IGNORECASE),
            
            # PEM code
            'pem': re.compile(r'\b(\d{7}[A-Z])\b'),
            
            # Budget title
            'budget_title': re.compile(r'^\s*([A-Z][A-Za-z\s\-]+(?:\([^)]+\))?)\s*$', re.MULTILINE),
        }
    
    def _extract_branch(self, text: str, position: int) -> Optional[str]:
        """Extract branch name from text near position"""
        # Look backwards for branch section
        text_before = text[max(0, position - 1000):position]
        
        if self.patterns['army_section'].search(text_before):
            return 'Army'
        elif self.patterns['navy_section'].search(text_before):
            return 'Navy'
        elif self.patterns['air_force_section'].search(text_before):
            return 'Air Force'
        elif self.patterns['defense_wide_section'].search(text_before):
            return 'Defense-Wide'
        elif self.patterns['marines_section'].search(text_before):
            return 'Marines'
        elif self.patterns['coast_guard_section'].search(text_before):
            return 'Coast Guard'
        
        return ''
    
    def _extract_appropriation_category(self, text: str, position: int) -> str:
        """Extract appropriation category from text near position"""
        text_nearby = text[max(0, position - 500):position + 500]
        
        if self.patterns['operation_maintenance'].search(text_nearby):
            return 'Operation and Maintenance'
        elif self.patterns['weapons_procurement'].search(text_nearby):
            return 'Weapons Procurement'
        elif self.patterns['missile_procurement'].search(text_nearby):
            return 'Missile Procurement'
        elif self.patterns['procurement'].search(text_nearby):
            return 'Procurement'
        elif self.patterns['rdte'].search(text_nearby):
            return 'RDTE'
        
        return ''
    
    def _extract_fiscal_years(self, text: str) -> tuple:
        """Extract fiscal years from text"""
        match = self.patterns['fiscal_year'].search(text)
        if match:
            year_start = match.group(1)
            year_end = match.group(2) if match.group(2) else year_start
            
            # Convert to 4-digit years
            if len(year_start) == 2:
                year_start = '20' + year_start
            if len(year_end) == 2:
                year_end = '20' + year_end
            
            return (year_start, year_end)
        
        return ('', '')
    
    def _extract_budget_activity(self, text: str, position: int) -> tuple:
        """Extract budget activity number and title"""
        text_nearby = text[max(0, position - 300):position + 300]
        match = self.patterns['budget_activity'].search(text_nearby)
        
        if match:
            return (match.group(1), match.group(2).strip())
        
        return ('', '')
    
    def _extract_amounts(self, text: str) -> List[str]:
        """Extract financial amounts from text"""
        amounts = self.patterns['amount'].findall(text)
        return amounts
    
    def _extract_explanation(self, text: str, position: int) -> str:
        """Extract explanation text"""
        text_after = text[position:position + 2000]
        match = self.patterns['explanation'].search(text_after)
        
        if match:
            explanation = match.group(1).strip()
            # Clean up explanation
            explanation = ' '.join(explanation.split())
            return explanation
        
        return ''
    
    def parse_ocr_text(self, ocr_text: str, source_file: str) -> List[Dict[str, Any]]:
        """
        Parse OCR text and extract appropriation data
        
        Args:
            ocr_text: Raw OCR text from PDF
            source_file: Source filename for reference
            
        Returns:
            List of dictionaries with extracted data
        """
        rows = []
        
        # Split into sections by branch
        sections = []
        branch_pattern = re.compile(
            r'(ARMY|NAVY|AIR\s+FORCE|DEFENSE-WIDE|MARINE\s+CORPS|COAST\s+GUARD)\s+(?:INCREASE|DECREASE)',
            re.IGNORECASE
        )
        
        for match in branch_pattern.finditer(ocr_text):
            sections.append(match.start())
        
        # Add end position
        sections.append(len(ocr_text))
        
        # Process each section
        for i in range(len(sections) - 1):
            section_start = sections[i]
            section_end = sections[i + 1]
            section_text = ocr_text[section_start:section_end]
            
            # Extract branch
            branch = self._extract_branch(ocr_text, section_start)
            
            # Look for appropriation category
            category = self._extract_appropriation_category(section_text, 0)
            
            # Extract fiscal years
            fy_start, fy_end = self._extract_fiscal_years(section_text)
            
            # Extract budget activity
            ba_number, ba_title = self._extract_budget_activity(section_text, 0)
            
            # Extract PEM code
            pem_match = self.patterns['pem'].search(section_text)
            pem = pem_match.group(1) if pem_match else ''
            
            # Extract budget title (look for capitalized lines)
            budget_title_matches = self.patterns['budget_title'].findall(section_text)
            budget_title = budget_title_matches[0] if budget_title_matches else ''
            
            # Extract amounts
            amounts = self._extract_amounts(section_text)
            
            # Extract explanation
            explanation = self._extract_explanation(section_text, 0)
            
            # Create row
            if branch or category or amounts:  # Only add if we found something
                row = {
                    'appropriation_category': category,
                    'appropriation code': '',
                    'appropriation activity': '',
                    'branch': branch,
                    'fiscal_year_start': fy_start,
                    'fiscal_year_end': fy_end,
                    'budget_activity_number': ba_number,
                    'budget_activity_title': ba_title,
                    'pem': pem,
                    'budget_title': budget_title,
                    'program_base_congressional': amounts[0] if len(amounts) > 0 else '-',
                    'program_base_dod': amounts[1] if len(amounts) > 1 else '-',
                    'reprogramming_amount': amounts[2] if len(amounts) > 2 else '-',
                    'revised_program_total': amounts[3] if len(amounts) > 3 else '-',
                    'explanation': explanation if explanation else '-',
                    'file': source_file
                }
                rows.append(row)
        
        return rows
    
    def transform(self, ocr_result: Dict[str, Any], output_path: Optional[str] = None) -> pd.DataFrame:
        """
        Transform OCR result to CSV DataFrame
        
        Args:
            ocr_result: Result from OCRProcessor
            output_path: Optional path to save CSV
            
        Returns:
            pandas DataFrame with structured data
        """
        text = ocr_result.get('text', '')
        source_file = ocr_result.get('file', 'unknown.pdf')
        
        # Parse text
        rows = self.parse_ocr_text(text, source_file)
        
        # Create DataFrame
        df = pd.DataFrame(rows, columns=self.COLUMNS)
        
        # Save if output path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False, quoting=csv.QUOTE_ALL)
            print(f"✓ CSV saved to: {output_path}")
        
        return df
    
    def batch_transform(self, ocr_results: List[Dict[str, Any]], 
                       output_dir: str = 'data/csv') -> List[str]:
        """
        Transform multiple OCR results to CSV
        
        Args:
            ocr_results: List of OCR results
            output_dir: Output directory for CSV files
            
        Returns:
            List of output file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_files = []
        
        for result in ocr_results:
            if 'error' in result:
                print(f"Skipping {result.get('file', 'unknown')} due to error")
                continue
            
            source_file = result.get('file', 'unknown.pdf')
            output_name = Path(source_file).stem + '_extracted.csv'
            output_path = output_dir / output_name
            
            self.transform(result, output_path)
            output_files.append(str(output_path))
        
        return output_files


def main():
    """Main entry point for testing"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Transform OCR text to CSV')
    parser.add_argument('input', help='Input JSON file with OCR results or text file')
    parser.add_argument('--output', help='Output CSV file')
    
    args = parser.parse_args()
    
    transformer = CSVTransformer()
    
    # Load input
    input_path = Path(args.input)
    if input_path.suffix == '.json':
        with open(input_path, 'r') as f:
            ocr_result = json.load(f)
    else:
        # Assume it's a text file
        with open(input_path, 'r') as f:
            ocr_result = {
                'text': f.read(),
                'file': input_path.name
            }
    
    # Transform
    output_path = args.output or str(input_path.with_suffix('.csv'))
    df = transformer.transform(ocr_result, output_path)
    
    print(f"\nExtracted {len(df)} rows")
    print("\nPreview:")
    print(df.to_string())
    
    return 0


if __name__ == '__main__':
    exit(main())
