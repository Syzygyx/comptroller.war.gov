#!/usr/bin/env python3
"""
LLM Validator - Uses AI to validate and review CSV accuracy
Supports OpenAI and Anthropic
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

import pandas as pd

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

OPENROUTER_AVAILABLE = OPENAI_AVAILABLE  # OpenRouter uses OpenAI SDK


class LLMValidator:
    """Validates CSV data accuracy using LLM"""
    
    def __init__(self, provider: str = 'openai', model: Optional[str] = None):
        """
        Initialize LLM validator
        
        Args:
            provider: 'openai', 'anthropic', or 'openrouter'
            model: Model name (optional, uses defaults)
        """
        self.provider = provider.lower()
        
        if self.provider == 'openai':
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI library not installed. Run: pip install openai")
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            self.client = OpenAI(api_key=api_key)
            self.model = model or 'gpt-4-turbo-preview'
            
        elif self.provider == 'openrouter':
            if not OPENROUTER_AVAILABLE:
                raise ImportError("OpenAI library not installed. Run: pip install openai")
            api_key = os.getenv('OPENROUTER_API_KEY')
            if not api_key:
                raise ValueError("OPENROUTER_API_KEY not set")
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            self.model = model or 'anthropic/claude-3.5-sonnet'
            
        elif self.provider == 'anthropic':
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("Anthropic library not installed. Run: pip install anthropic")
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            self.client = Anthropic(api_key=api_key)
            self.model = model or 'claude-3-opus-20240229'
            
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert in analyzing government appropriation documents and financial data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        return response.choices[0].message.content
    
    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            temperature=0.3,
            system="You are an expert in analyzing government appropriation documents and financial data.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    
    def _call_llm(self, prompt: str) -> str:
        """Call configured LLM"""
        if self.provider in ['openai', 'openrouter']:
            return self._call_openai(prompt)
        else:
            return self._call_anthropic(prompt)
    
    def validate_csv_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate CSV structure and completeness"""
        expected_columns = [
            'appropriation_category', 'appropriation code', 'appropriation activity',
            'branch', 'fiscal_year_start', 'fiscal_year_end', 'budget_activity_number',
            'budget_activity_title', 'pem', 'budget_title', 'program_base_congressional',
            'program_base_dod', 'reprogramming_amount', 'revised_program_total',
            'explanation', 'file'
        ]
        
        issues = []
        warnings = []
        
        # Check columns
        missing_cols = set(expected_columns) - set(df.columns)
        if missing_cols:
            issues.append(f"Missing columns: {', '.join(missing_cols)}")
        
        # Check for empty rows
        empty_rows = df.isnull().all(axis=1).sum()
        if empty_rows > 0:
            warnings.append(f"{empty_rows} completely empty rows")
        
        # Check critical fields
        for col in ['appropriation_category', 'branch', 'fiscal_year_start']:
            empty_count = df[col].isna().sum() if col in df.columns else len(df)
            if empty_count > len(df) * 0.5:
                issues.append(f"More than 50% missing values in '{col}'")
        
        # Check financial fields
        financial_cols = ['program_base_congressional', 'program_base_dod', 
                         'reprogramming_amount', 'revised_program_total']
        for col in financial_cols:
            if col in df.columns:
                # Check if values look like amounts
                non_numeric = df[col].apply(lambda x: str(x) not in ['-', 'nan'] and not str(x).replace(',', '').replace('.', '').replace('+', '').replace('-', '').isdigit()).sum()
                if non_numeric > 0:
                    warnings.append(f"{non_numeric} non-numeric values in '{col}'")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'row_count': len(df),
            'column_count': len(df.columns)
        }
    
    def validate_with_llm(self, df: pd.DataFrame, ocr_text: str) -> Dict[str, Any]:
        """
        Use LLM to validate CSV accuracy against original OCR text
        
        Args:
            df: DataFrame with extracted data
            ocr_text: Original OCR text
            
        Returns:
            Validation results dictionary
        """
        # Prepare CSV preview (first 5 rows)
        csv_preview = df.head(5).to_string()
        
        # Prepare OCR text preview (first 2000 chars)
        ocr_preview = ocr_text[:2000] + "..." if len(ocr_text) > 2000 else ocr_text
        
        prompt = f"""I need you to validate the accuracy of data extraction from a government appropriation document.

ORIGINAL OCR TEXT (excerpt):
{ocr_preview}

EXTRACTED CSV DATA (preview):
{csv_preview}

Please analyze and provide:
1. Accuracy Assessment: Rate the extraction accuracy (0-100%)
2. Identified Issues: List any obvious errors or inconsistencies
3. Missing Information: Note any important data that appears in the OCR text but is missing from the CSV
4. Data Quality: Comment on the completeness and formatting of financial amounts
5. Recommendations: Suggest improvements for extraction

Total rows in CSV: {len(df)}

Provide your response in JSON format with keys: accuracy_score, issues, missing_data, quality_notes, recommendations"""

        try:
            response = self._call_llm(prompt)
            
            # Try to parse JSON response
            try:
                # Extract JSON from response (may be wrapped in markdown)
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    llm_analysis = json.loads(json_str)
                else:
                    llm_analysis = {'raw_response': response}
            except json.JSONDecodeError:
                llm_analysis = {'raw_response': response}
            
            return {
                'success': True,
                'provider': self.provider,
                'model': self.model,
                'analysis': llm_analysis,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def generate_report(self, csv_path: str, ocr_result: Dict[str, Any], 
                       output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive validation report
        
        Args:
            csv_path: Path to CSV file
            ocr_result: Original OCR result dictionary
            output_path: Optional path to save report JSON
            
        Returns:
            Complete validation report
        """
        df = pd.read_csv(csv_path)
        
        print(f"Validating: {csv_path}")
        print(f"  Rows: {len(df)}")
        
        # Structure validation
        print("  Checking structure...")
        structure_validation = self.validate_csv_structure(df)
        
        # LLM validation
        print("  Analyzing with LLM...")
        llm_validation = self.validate_with_llm(df, ocr_result.get('text', ''))
        
        # Compile report
        report = {
            'file': csv_path,
            'timestamp': datetime.now().isoformat(),
            'source_pdf': ocr_result.get('file', 'unknown'),
            'structure_validation': structure_validation,
            'llm_validation': llm_validation,
            'statistics': {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'ocr_character_count': ocr_result.get('character_count', 0),
                'ocr_word_count': ocr_result.get('word_count', 0),
                'ocr_pages': ocr_result.get('pages_processed', 0)
            }
        }
        
        # Calculate overall score
        accuracy_score = llm_validation.get('analysis', {}).get('accuracy_score', 0)
        if isinstance(accuracy_score, str):
            accuracy_score = int(''.join(filter(str.isdigit, accuracy_score))) if any(c.isdigit() for c in accuracy_score) else 0
        
        report['overall_score'] = accuracy_score
        report['passed'] = structure_validation['valid'] and accuracy_score >= 70
        
        # Save report
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"  ✓ Report saved: {output_path}")
        
        # Print summary
        print(f"  Overall Score: {report['overall_score']}%")
        print(f"  Status: {'✓ PASSED' if report['passed'] else '✗ FAILED'}")
        
        return report
    
    def batch_validate(self, csv_files: List[str], ocr_results: List[Dict[str, Any]], 
                      output_dir: str = 'data/validation') -> List[Dict[str, Any]]:
        """
        Validate multiple CSV files
        
        Args:
            csv_files: List of CSV file paths
            ocr_results: List of OCR results
            output_dir: Output directory for reports
            
        Returns:
            List of validation reports
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        reports = []
        
        for csv_file, ocr_result in zip(csv_files, ocr_results):
            report_name = Path(csv_file).stem + '_validation.json'
            report_path = output_dir / report_name
            
            report = self.generate_report(csv_file, ocr_result, report_path)
            reports.append(report)
        
        # Generate summary
        summary = {
            'total_files': len(reports),
            'passed': sum(1 for r in reports if r['passed']),
            'failed': sum(1 for r in reports if not r['passed']),
            'average_score': sum(r['overall_score'] for r in reports) / len(reports) if reports else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        summary_path = output_dir / 'validation_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📊 Validation Summary:")
        print(f"   Total: {summary['total_files']}")
        print(f"   Passed: {summary['passed']}")
        print(f"   Failed: {summary['failed']}")
        print(f"   Average Score: {summary['average_score']:.1f}%")
        
        return reports


def main():
    """Main entry point for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate CSV with LLM')
    parser.add_argument('csv', help='Path to CSV file')
    parser.add_argument('--ocr-json', help='Path to OCR result JSON')
    parser.add_argument('--provider', choices=['openai', 'anthropic'], default='openai')
    parser.add_argument('--output', help='Output report path')
    
    args = parser.parse_args()
    
    # Load OCR result
    if args.ocr_json:
        with open(args.ocr_json, 'r') as f:
            ocr_result = json.load(f)
    else:
        # Create minimal OCR result
        ocr_result = {
            'file': Path(args.csv).stem + '.pdf',
            'text': '',
            'pages_processed': 1
        }
    
    validator = LLMValidator(provider=args.provider)
    report = validator.generate_report(args.csv, ocr_result, args.output)
    
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    exit(main())
