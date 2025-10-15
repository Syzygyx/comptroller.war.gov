#!/usr/bin/env python3
"""
Rule-based CSV Parser
- Reads TXT files produced by OCR or text-extraction
- Uses regex and structural cues (similar to CSVTransformer) to output CSV without LLM

Usage:
  python3 src/rule_csv_parser.py --txt data/txt --out data/csv_rule
"""

import re
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pandas as pd

BRANCH_REGEX = re.compile(r"\b(ARMY|NAVY|AIR\s+FORCE|DEFENSE-WIDE|MARINE\s+CORPS|COAST\s+GUARD)\b\s+(INCREASE|DECREASE)", re.IGNORECASE)
CATEGORY_PATTERNS = {
    'Operation and Maintenance': re.compile(r'Operation\s+and\s+Maintenance', re.IGNORECASE),
    'Weapons Procurement': re.compile(r'Weapons?\s+Procurement', re.IGNORECASE),
    'Missile Procurement': re.compile(r'Missile\s+Procurement', re.IGNORECASE),
    'Procurement': re.compile(r'(?<!,)\bProcurement\b', re.IGNORECASE),
    'RDTE': re.compile(r'\bRDTE\b|Research.*Development', re.IGNORECASE),
}
FY_REGEX = re.compile(r'(?:FY|Fiscal\s+Year)\s*(\d{2,4})[\/-]?(\d{2,4})?', re.IGNORECASE)
BA_REGEX = re.compile(r'Budget\s+Activity\s+(\d+):\s*([^\n]+)', re.IGNORECASE)
PEM_REGEX = re.compile(r'\b(\d{7}[A-Z])\b')
AMOUNT_REGEX = re.compile(r'[+\-]?\$?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)')
EXPL_REGEX = re.compile(r'Explanation:\s*([^\n]+(?:\n(?!(?:ARMY|NAVY|AIR FORCE|DEFENSE-WIDE|Budget Activity|Explanation))[^\n]+)*)', re.IGNORECASE)
CAP_LINE = re.compile(r'^\s*([A-Z][A-Za-z\s\-]+(?:\([^)]+\))?)\s*$', re.MULTILINE)

COLUMNS = [
    'appropriation_category','appropriation code','appropriation activity','branch',
    'fiscal_year_start','fiscal_year_end','budget_activity_number','budget_activity_title',
    'pem','budget_title','program_base_congressional','program_base_dod','reprogramming_amount',
    'revised_program_total','explanation','file'
]


def extract_sections(text: str) -> List[Tuple[int, int]]:
    idxs = [m.start() for m in BRANCH_REGEX.finditer(text)]
    if not idxs:
        return [(0, len(text))]
    idxs.append(len(text))
    return [(idxs[i], idxs[i+1]) for i in range(len(idxs)-1)]


def find_branch(text: str, pos: int) -> str:
    before = text[max(0, pos-1000):pos]
    m = BRANCH_REGEX.search(before)
    if not m:
        return ''
    b = m.group(1).upper()
    return {'ARMY':'Army','NAVY':'Navy','AIR FORCE':'Air Force','DEFENSE-WIDE':'Defense-Wide','MARINE CORPS':'Marines','COAST GUARD':'Coast Guard'}[b]


def find_category(snippet: str) -> str:
    for name, rx in CATEGORY_PATTERNS.items():
        if rx.search(snippet):
            return name
    return ''


def find_fys(snippet: str) -> Tuple[str,str]:
    m = FY_REGEX.search(snippet)
    if not m:
        return ('','')
    y1 = m.group(1) or ''
    y2 = m.group(2) or y1
    if len(y1)==2: y1 = '20'+y1
    if len(y2)==2: y2 = '20'+y2
    return (y1,y2)


def find_ba(snippet: str) -> Tuple[str,str]:
    m = BA_REGEX.search(snippet)
    if not m:
        return ('','')
    return (m.group(1), m.group(2).strip())


def find_amounts(snippet: str) -> List[str]:
    return AMOUNT_REGEX.findall(snippet)


def find_expl(snippet: str) -> str:
    m = EXPL_REGEX.search(snippet)
    if not m:
        return ''
    ex = ' '.join(m.group(1).split())
    return ex


def parse_text(ocr_text: str, source_file: str) -> pd.DataFrame:
    rows: List[Dict[str,Any]] = []
    sections = extract_sections(ocr_text)
    for start, end in sections:
        snippet = ocr_text[start:end]
        branch = find_branch(ocr_text, start)
        category = find_category(snippet)
        fy_start, fy_end = find_fys(snippet)
        ba_num, ba_title = find_ba(snippet)
        pem_match = PEM_REGEX.search(snippet)
        pem = pem_match.group(1) if pem_match else ''
        # Title heuristic
        titles = CAP_LINE.findall(snippet)
        budget_title = titles[0] if titles else ''
        amounts = find_amounts(snippet)
        explanation = find_expl(snippet) or '-'
        row = {
            'appropriation_category': category,
            'appropriation code': '',
            'appropriation activity': '',
            'branch': branch,
            'fiscal_year_start': fy_start,
            'fiscal_year_end': fy_end,
            'budget_activity_number': ba_num,
            'budget_activity_title': ba_title,
            'pem': pem,
            'budget_title': budget_title,
            'program_base_congressional': amounts[0] if len(amounts)>0 else '-',
            'program_base_dod': amounts[1] if len(amounts)>1 else '-',
            'reprogramming_amount': amounts[2] if len(amounts)>2 else '-',
            'revised_program_total': amounts[3] if len(amounts)>3 else '-',
            'explanation': explanation,
            'file': source_file,
        }
        # Only add meaningful rows
        if any([branch, category, amounts]):
            rows.append(row)
    df = pd.DataFrame(rows, columns=COLUMNS)
    return df


def main():
    parser = argparse.ArgumentParser(description='Rule-based CSV parser for OCR TXT')
    parser.add_argument('--txt', required=True, help='TXT file or directory')
    parser.add_argument('--out', required=True, help='Output directory for CSV')
    args = parser.parse_args()

    txt_path = Path(args.txt)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    files: List[Path]
    if txt_path.is_dir():
        files = sorted(txt_path.glob('*.txt'))
    else:
        files = [txt_path]

    for fp in files:
        text = fp.read_text(errors='ignore')
        df = parse_text(text, fp.name)
        out_csv = out_dir / (fp.stem + '_rule.csv')
        df.to_csv(out_csv, index=False, quoting=csv.QUOTE_ALL)
        print(f"✓ Wrote rule CSV: {out_csv}")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
