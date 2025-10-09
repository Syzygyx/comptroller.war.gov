#!/usr/bin/env python3
"""
Budget Parser - Extracts structured budget data from DD 1414 and reprogramming documents
Generates comprehensive CSV output and Sankey flow data
"""

import re
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

import pandas as pd


class BudgetParser:
    """Comprehensive parser for DoD budget documents"""
    
    def __init__(self):
        self.budget_lines = []
    
    def parse_reprogramming_action(self, text: str, filename: str) -> List[Dict[str, Any]]:
        """
        Parse reprogramming action document (IR or PA)
        
        Format example:
        Operation and Maintenance, Army, 05/05 +21
        Budget Activity 1: Operating Forces +21
        Explanation: These funds are transferred...
        """
        lines = []
        
        # Extract fiscal year
        fy_match = re.search(r'(?:FY|Fiscal Year)\s*(\d{2,4})[_\-]?(\d{2,4})?', filename + ' ' + text[:1000])
        if fy_match:
            fy = fy_match.group(1)
            if len(fy) == 2:
                fy = '20' + fy
            fiscal_year = fy
        else:
            fiscal_year = 'Unknown'
        
        # Find all appropriation line items
        # Pattern: Appropriation Title, Branch, FY/FY [+/-]amount
        approp_pattern = re.compile(
            r'(Operation and Maintenance|Procurement|Weapons Procurement|Missile Procurement|'
            r'Other Procurement|Research, Development, Test, and Evaluation|Military Personnel|Reserve Personnel),?\s+'
            r'(Army|Navy|Air Force|Marine Corps|Defense-Wide),?\s+'
            r'(\d{2})/(\d{2})\s+'
            r'([+\-]?\d{1,3}(?:,\d{3})*)',
            re.IGNORECASE
        )
        
        for match in approp_pattern.finditer(text):
            category = match.group(1).strip()
            branch = match.group(2).strip()
            fy_start = '20' + match.group(3)
            fy_end = '20' + match.group(4)
            amount = int(match.group(5).replace(',', '').replace('+', '').replace('-', ''))
            is_increase = '+' in match.group(5) or '-' not in match.group(5)
            
            # Find Budget Activity after this line
            pos = match.end()
            text_after = text[pos:pos+500]
            
            ba_match = re.search(r'Budget\s+Activity\s+(\d+):\s*([^\n]+)', text_after, re.IGNORECASE)
            ba_number = ba_match.group(1) if ba_match else ''
            ba_title = ba_match.group(2).strip() if ba_match else ''
            
            # Find explanation
            expl_match = re.search(r'Explanation:\s*([^\n]+(?:\n(?!(?:Operation|Budget Activity|Explanation))[^\n]+)*)', 
                                  text_after, re.IGNORECASE)
            explanation = expl_match.group(1).strip() if expl_match else ''
            # Clean up explanation
            explanation = ' '.join(explanation.split())
            
            lines.append({
                'fiscal_year_start': fy_start,
                'fiscal_year_end': fy_end,
                'appropriation_category': category,
                'branch': branch,
                'budget_activity_number': ba_number,
                'budget_activity_title': ba_title,
                'reprogramming_amount': amount if is_increase else -amount,
                'direction': 'increase' if is_increase else 'decrease',
                'explanation': explanation[:500],  # Limit length
                'file': filename,
                'type': 'reprogramming_action'
            })
        
        return lines
    
    def parse_dd1414_baseline(self, text: str, filename: str) -> List[Dict[str, Any]]:
        """
        Parse DD 1414 baseline budget document - IMPROVED VERSION
        
        Handles complex table formats with multiple numeric columns
        """
        lines = []
        
        # Extract fiscal year from filename
        fy_match = re.search(r'FY[_\s]*(\d{4})', filename)
        fiscal_year = fy_match.group(1) if fy_match else 'Unknown'
        
        # Current context trackers
        current_branch = None
        current_category = None
        current_budget_activity = None
        current_ba_number = None
        
        text_lines = text.split('\n')
        
        for i, line in enumerate(text_lines):
            line = line.strip()
            if not line or len(line) < 10:
                continue
            
            # Detect appropriation title (top of document)
            # Format: "Appropriation Account Title: Military Personnel, Army, 2023/2023"
            approp_match = re.search(
                r'Appropriation.*?:\s*(Military Personnel|Operation and Maintenance|Procurement|'
                r'Research.*?Development|Research.*?Evaluation),?\s*(Army|Navy|Air Force|Marine|Defense)',
                line, re.IGNORECASE
            )
            if approp_match:
                current_category = approp_match.group(1)
                current_branch = approp_match.group(2)
                # Normalize
                if 'Research' in current_category:
                    current_category = 'Research, Development, Test, and Evaluation'
                if 'Marine' in current_branch:
                    current_branch = 'Marines'
                continue
            
            # Detect Budget Activity headers
            # Format: "Budget Activity 01: Pay and Allowances of Officers"
            ba_match = re.search(r'Budget Activity\s+(\d+):\s*(.+?)(?:\s+\d{1,3},\d{3}|$)', line, re.IGNORECASE)
            if ba_match:
                current_ba_number = ba_match.group(1)
                current_budget_activity = ba_match.group(2).strip()
                continue
            
            # Skip subtotal lines
            if 'Subtotal' in line or 'SUBTOTAL' in line:
                continue
            
            # Extract data lines with amounts
            # Pattern: Line item text followed by 1-4 large numbers
            # Example: "Pay and Allowances    13,599,547 13,599,547"
            # Example: "FY 2023 Appropriated Base 302,538"
            # Example: "Underexecution of strength -15,425"
            
            # Look for lines with dollar amounts (at least 4 digits with commas)
            amounts = re.findall(r'-?\d{1,3}(?:,\d{3})+', line)
            
            if len(amounts) > 0 and current_category and current_branch:
                # Extract the line item text (everything before the first number)
                text_part = re.split(r'\s+-?\d{1,3}(?:,\d{3})+', line)[0].strip()
                
                # Skip if text is too short or looks like a header
                if len(text_part) < 5:
                    continue
                if text_part.upper() == text_part and len(text_part) < 15:  # All caps short = header
                    continue
                
                # Parse amounts
                parsed_amounts = [int(amt.replace(',', '').replace('-', '')) for amt in amounts]
                
                # Use the largest amount (usually the most relevant)
                main_amount = max(parsed_amounts)
                
                # Skip very small amounts (likely page numbers or codes)
                if main_amount < 1000:
                    continue
                
                # Determine if this is a decrease
                is_decrease = any('-' in amt for amt in amounts)
                
                lines.append({
                    'fiscal_year': fiscal_year,
                    'appropriation_category': current_category,
                    'branch': current_branch,
                    'budget_activity_number': current_ba_number or '',
                    'budget_activity_title': current_budget_activity or '',
                    'program_element': text_part[:100],  # Truncate long names
                    'budget_amount': main_amount,
                    'is_decrease': is_decrease,
                    'raw_amounts': amounts[:3],  # Keep first 3 for reference
                    'file': filename,
                    'type': 'baseline'
                })
        
        return lines
    
    def process_all_documents(self, ocr_results: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Process all OCR results and extract budget data
        
        Args:
            ocr_results: List of OCR result dictionaries
            
        Returns:
            DataFrame with all budget data
        """
        all_lines = []
        
        for result in ocr_results:
            if 'error' in result or 'text' not in result:
                continue
            
            text = result['text']
            filename = result.get('file', 'unknown.pdf')
            
            print(f"Parsing {filename}...")
            
            # Determine document type and parse accordingly
            if 'DD_1414' in filename or 'Base_for_Reprogramming' in filename:
                lines = self.parse_dd1414_baseline(text, filename)
                print(f"  Found {len(lines)} baseline budget lines")
            elif '_IR_' in filename or '_PA_' in filename:
                lines = self.parse_reprogramming_action(text, filename)
                print(f"  Found {len(lines)} reprogramming actions")
            else:
                # Try both parsers
                lines_baseline = self.parse_dd1414_baseline(text, filename)
                lines_reprog = self.parse_reprogramming_action(text, filename)
                lines = lines_baseline if len(lines_baseline) > len(lines_reprog) else lines_reprog
                print(f"  Found {len(lines)} budget lines (auto-detected)")
            
            all_lines.extend(lines)
        
        # Convert to DataFrame
        if all_lines:
            df = pd.DataFrame(all_lines)
            print(f"\n✅ Total budget lines extracted: {len(df)}")
            return df
        else:
            print("\n⚠️  No budget data extracted")
            return pd.DataFrame()
    
    def create_sankey_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Create Sankey diagram data from budget DataFrame
        
        Args:
            df: DataFrame with budget data
            
        Returns:
            Dictionary with Sankey flow data
        """
        flows = []
        
        # Create flows for reprogramming actions
        if 'reprogramming_amount' in df.columns:
            reprog_df = df[df['type'] == 'reprogramming_action'].copy()
            
            for _, row in reprog_df.iterrows():
                # Category → Branch flow
                flows.append({
                    'source': row.get('appropriation_category', 'Unknown'),
                    'target': row.get('branch', 'Unknown'),
                    'value': abs(row.get('reprogramming_amount', 0)),
                    'fiscal_year': row.get('fiscal_year_start', 'Unknown'),
                    'type': 'category_to_branch',
                    'direction': row.get('direction', 'increase')
                })
                
                # Branch → Activity flow
                if row.get('budget_activity_title'):
                    flows.append({
                        'source': row.get('branch', 'Unknown'),
                        'target': row.get('budget_activity_title', 'Unknown')[:40],
                        'value': abs(row.get('reprogramming_amount', 0)),
                        'fiscal_year': row.get('fiscal_year_start', 'Unknown'),
                        'type': 'branch_to_activity',
                        'direction': row.get('direction', 'increase')
                    })
        
        # Create flows for baseline budgets
        if 'budget_amount' in df.columns:
            baseline_df = df[df['type'] == 'baseline'].copy()
            
            # Aggregate by category and branch
            aggregated = baseline_df.groupby(['appropriation_category', 'branch', 'fiscal_year'])['budget_amount'].sum().reset_index()
            
            for _, row in aggregated.iterrows():
                if row['budget_amount'] > 50000:  # Filter small amounts
                    flows.append({
                        'source': row['appropriation_category'],
                        'target': row['branch'],
                        'value': int(row['budget_amount']),
                        'fiscal_year': row['fiscal_year'],
                        'type': 'baseline',
                        'direction': 'baseline'
                    })
        
        # Aggregate flows
        flow_dict = defaultdict(lambda: {'value': 0, 'fiscal_years': set(), 'files': set()})
        
        for flow in flows:
            key = (flow['source'], flow['target'], flow['type'])
            flow_dict[key]['value'] += flow['value']
            flow_dict[key]['fiscal_years'].add(flow.get('fiscal_year', 'Unknown'))
            flow_dict[key]['type'] = flow['type']
        
        # Convert to list
        aggregated_flows = []
        for (source, target, flow_type), data in flow_dict.items():
            aggregated_flows.append({
                'source': source,
                'target': target,
                'value': data['value'],
                'fiscal_years': sorted(list(data['fiscal_years'])),
                'type': flow_type
            })
        
        return {
            'flows': aggregated_flows,
            'metadata': {
                'total_flows': len(aggregated_flows),
                'total_value': sum(f['value'] for f in aggregated_flows),
                'fiscal_years': sorted(list(set(
                    fy for f in aggregated_flows for fy in f['fiscal_years']
                )))
            }
        }
    
    def export_budget_csv(self, df: pd.DataFrame, output_file: str):
        """
        Export budget data to CSV
        
        Args:
            df: DataFrame with budget data
            output_file: Output CSV file path
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_path, index=False, quoting=csv.QUOTE_ALL)
        print(f"✓ Saved budget data to: {output_path}")
        print(f"  Rows: {len(df)}")
        
        # Print summary
        if 'appropriation_category' in df.columns:
            print(f"\nBy Category:")
            summary = df.groupby('appropriation_category').size()
            for cat, count in summary.items():
                print(f"  {cat}: {count} lines")
        
        if 'branch' in df.columns:
            print(f"\nBy Branch:")
            summary = df.groupby('branch').size()
            for branch, count in summary.items():
                print(f"  {branch}: {count} lines")


def main():
    """Main entry point"""
    import argparse
    from ocr_processor import OCRProcessor
    
    parser = argparse.ArgumentParser(description='Parse budget documents and create visualizations')
    parser.add_argument('--pdf-dir', default='data/pdfs', help='PDF directory')
    parser.add_argument('--output-csv', default='data/budget_data.csv', help='Output CSV file')
    parser.add_argument('--output-sankey', default='docs/data/budget_flows.json', help='Output Sankey JSON')
    parser.add_argument('--max-files', type=int, help='Maximum files to process')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("Budget Document Parser")
    print("=" * 80)
    
    # Get PDFs
    pdf_dir = Path(args.pdf_dir)
    pdf_files = sorted(pdf_dir.glob('*.pdf'))
    
    if args.max_files:
        pdf_files = pdf_files[:args.max_files]
    
    if not pdf_files:
        print("No PDFs found!")
        return 1
    
    print(f"\nProcessing {len(pdf_files)} PDFs...\n")
    
    # Process with OCR (try text extraction first - faster)
    ocr = OCRProcessor()
    ocr_results = []
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] {pdf_file.name}")
        result = ocr.extract_from_pdf(str(pdf_file), use_ocr=False)  # Try text first
        ocr_results.append(result)
    
    # Parse budget data
    print(f"\n{'=' * 80}")
    print("Parsing Budget Data")
    print(f"{'=' * 80}\n")
    
    budget_parser = BudgetParser()
    df = budget_parser.process_all_documents(ocr_results)
    
    if df.empty:
        print("\n❌ No budget data extracted")
        return 1
    
    # Export CSV
    print(f"\n{'=' * 80}")
    print("Exporting Data")
    print(f"{'=' * 80}\n")
    
    budget_parser.export_budget_csv(df, args.output_csv)
    
    # Create Sankey data
    sankey_data = budget_parser.create_sankey_data(df)
    
    output_path = Path(args.output_sankey)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(sankey_data, f, indent=2)
    
    print(f"\n✓ Saved Sankey data to: {output_path}")
    print(f"  Flows: {sankey_data['metadata']['total_flows']}")
    print(f"  Total value: ${sankey_data['metadata']['total_value'] / 1000000:.2f}B")
    print(f"  Fiscal years: {', '.join(sankey_data['metadata']['fiscal_years'])}")
    
    print(f"\n{'=' * 80}")
    print("✅ Budget Parsing Complete!")
    print(f"{'=' * 80}")
    print(f"\nView results:")
    print(f"  CSV: {args.output_csv}")
    print(f"  Sankey diagram: Open docs/sankey.html in browser")
    
    return 0


if __name__ == '__main__':
    exit(main())
