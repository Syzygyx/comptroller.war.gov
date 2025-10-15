#!/usr/bin/env python3
"""
LLM CSV Generator
- Takes TXT files and a CSV header template to produce CSV rows via an LLM
- Supports OpenRouter/OpenAI/Anthropic via existing env vars

Usage:
  python3 src/llm_csv_generator.py --txt data/txt --template templates/template.csv --out data/csv_llm
"""

import os
import csv
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

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

OPENROUTER_AVAILABLE = OPENAI_AVAILABLE


def load_headers(template_csv: Path) -> List[str]:
    with open(template_csv, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
    return headers


def build_prompt(headers: List[str], txt: str) -> str:
    cols = ", ".join(headers)
    return (
        "You are extracting structured fields from a U.S. DoD reprogramming/DD1414 text.\n"
        "Return ONLY a CSV with one header row and N data rows.\n"
        f"Headers: {cols}\n"
        "Rules:\n"
        "- Quote all fields with double quotes.\n"
        "- Use '-' when a field is not present.\n"
        "- Monetary amounts should keep signs and commas if present.\n"
        "- Keep PEM codes unmodified.\n\n"
        "Text to extract from (may be OCR):\n"
        f"""{txt[:6000]}"""
    )


def call_llm(provider: str, model: str, prompt: str) -> str:
    provider = provider.lower()
    if provider in ["openai", "openrouter"]:
        if not OPENAI_AVAILABLE:
            raise RuntimeError("openai SDK not installed")
        api_key = os.getenv("OPENROUTER_API_KEY") if provider == "openrouter" else os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("API key missing for provider")
        client = OpenAI(api_key=api_key, base_url=("https://openrouter.ai/api/v1" if provider == "openrouter" else None))
        resp = client.chat.completions.create(
            model=model or ("anthropic/claude-3.5-sonnet" if provider == "openrouter" else "gpt-4o-mini"),
            messages=[
                {"role":"system","content":"You are a precise CSV information extractor."},
                {"role":"user","content":prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        return resp.choices[0].message.content
    elif provider == "anthropic":
        if not ANTHROPIC_AVAILABLE:
            raise RuntimeError("anthropic SDK not installed")
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY missing")
        client = Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=model or "claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0.1,
            system="You are a precise CSV information extractor.",
            messages=[{"role":"user","content":prompt}]
        )
        return resp.content[0].text
    else:
        raise ValueError(f"Unknown provider: {provider}")


def parse_csv_from_text(text: str) -> pd.DataFrame:
    # Strip code fences if model returned markdown
    if "```" in text:
        start = text.find("```")
        end = text.rfind("```")
        if end > start:
            text = text[start+3:end]
            # remove optional language label
            text = text.split('\n', 1)[1] if '\n' in text else text
    from io import StringIO
    return pd.read_csv(StringIO(text))


def main():
    parser = argparse.ArgumentParser(description="Generate CSV from TXT via LLM")
    parser.add_argument("--txt", required=True, help="TXT file or directory")
    parser.add_argument("--template", required=True, help="CSV template with headers")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--provider", default=os.getenv("LLM_PROVIDER", "openrouter"))
    parser.add_argument("--model", default=os.getenv("LLM_MODEL", "anthropic/claude-3.5-sonnet"))

    args = parser.parse_args()

    txt_path = Path(args.txt)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    headers = load_headers(Path(args.template))

    files: List[Path]
    if txt_path.is_dir():
        files = sorted(txt_path.glob("*.txt"))
    else:
        files = [txt_path]

    for fp in files:
        txt = fp.read_text(errors="ignore")
        prompt = build_prompt(headers, txt)
        try:
            raw = call_llm(args.provider, args.model, prompt)
            df = parse_csv_from_text(raw)
        except Exception as e:
            print(f"LLM generation failed for {fp.name}: {e}")
            continue
        # ensure headers
        for h in headers:
            if h not in df.columns:
                df[h] = '-'
        df = df[headers]
        out_csv = out_dir / (fp.stem + "_llm.csv")
        df.to_csv(out_csv, index=False, quoting=csv.QUOTE_ALL)
        print(f"✓ Wrote LLM CSV: {out_csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
