#!/usr/bin/env python3
"""
Extract Custom_PDF objects from TTS JSON files.

Traverses the TTS JSON to find all Custom_PDF objects, downloads the PDFs
to a PDFs/ directory, and prints a summary.

Usage:
    python extract_pdfs.py Workshop/mod.deserialized.json
"""

import json
import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

import requests


def find_pdfs(data: Any) -> List[Dict]:
    """
    Recursively traverse JSON to find all Custom_PDF objects.

    Returns a list of dicts with 'nickname' and 'pdf_url'.
    """
    pdfs = []

    def traverse(obj):
        if isinstance(obj, dict):
            name = obj.get('Name', '')

            if name == 'Custom_PDF':
                custom_pdf = obj.get('CustomPDF', {})
                pdf_url = custom_pdf.get('PDFUrl', '')

                if pdf_url:
                    pdfs.append({
                        'nickname': obj.get('Nickname', ''),
                        'guid': obj.get('GUID', ''),
                        'pdf_url': pdf_url,
                    })

            for value in obj.values():
                traverse(value)

        elif isinstance(obj, list):
            for item in obj:
                traverse(item)

    traverse(data)
    return pdfs


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use as a filename."""
    # Replace any non-alphanumeric/space/dash/underscore/dot with underscore
    safe = re.sub(r'[^\w\s\-.]', '_', name)
    # Collapse runs of whitespace/underscore
    safe = re.sub(r'[\s_]+', '_', safe)
    # Trim leading/trailing underscores and dots
    safe = safe.strip('_.')
    return safe or 'unnamed'


def download_pdf(url: str, output_path: Path, no_verify: bool = False) -> bool:
    """Download a PDF from a URL to the given path."""
    try:
        resp = requests.get(url, timeout=60, verify=not no_verify)
        resp.raise_for_status()
        output_path.write_bytes(resp.content)
        return True
    except Exception as e:
        print(f"  Warning: Failed to download {url}: {e}", file=sys.stderr)
        return False


def process_json_file(json_path: Path) -> List[Dict]:
    """Process a single JSON file and extract all Custom_PDF objects."""
    print(f"Processing {json_path}...")

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {json_path}: {e}", file=sys.stderr)
        return []

    return find_pdfs(data)


def main():
    parser = argparse.ArgumentParser(
        description='Extract Custom_PDF objects from TTS JSON files'
    )
    parser.add_argument(
        'json_files',
        nargs='+',
        type=Path,
        help='TTS JSON file(s) to process'
    )
    parser.add_argument(
        '--no-verify',
        action='store_true',
        help='Skip SSL certificate verification'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Determine base directory (the .deserialized/ dir)
    first_input = Path(args.json_files[0]).resolve()
    if first_input.parent.name == 'Workshop':
        base_dir = first_input.parent.parent
    else:
        base_dir = first_input.parent

    # Collect all Custom_PDF objects
    all_pdfs = []
    for json_file in args.json_files:
        if not json_file.exists():
            print(f"Warning: {json_file} not found, skipping", file=sys.stderr)
            continue
        all_pdfs.extend(process_json_file(json_file))

    # Deduplicate by URL
    seen_urls = {}
    unique_pdfs = []
    for pdf in all_pdfs:
        url = pdf['pdf_url']
        if url not in seen_urls:
            seen_urls[url] = pdf
            unique_pdfs.append(pdf)

    if not unique_pdfs:
        print(f"\nFound 0 Custom_PDF(s)")
        return 0

    # Create output directory
    pdfs_dir = base_dir / 'PDFs'
    pdfs_dir.mkdir(exist_ok=True)

    # Download each PDF
    used_names = {}
    downloaded = 0
    for pdf in unique_pdfs:
        nickname = pdf['nickname'] or 'unnamed'
        base_name = sanitize_filename(nickname)

        # Deduplicate filenames
        if base_name in used_names:
            used_names[base_name] += 1
            filename = f"{base_name}_{used_names[base_name]}.pdf"
        else:
            used_names[base_name] = 0
            filename = f"{base_name}.pdf"

        output_path = pdfs_dir / filename

        if args.verbose:
            print(f"  Downloading: {nickname} → {filename}")
            print(f"    URL: {pdf['pdf_url'][:80]}")

        if download_pdf(pdf['pdf_url'], output_path, no_verify=args.no_verify):
            downloaded += 1
            pdf['local_path'] = str(output_path)
            size = output_path.stat().st_size
            size_str = f"{size / 1024:.0f}KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f}MB"
            print(f"  {nickname} → {filename} ({size_str})")

    print(f"\nFound {len(unique_pdfs)} Custom_PDF(s), downloaded {downloaded} to {pdfs_dir}/")

    if unique_pdfs:
        for i, pdf in enumerate(unique_pdfs[:20], 1):
            nickname = pdf['nickname'] or '(unnamed)'
            local = pdf.get('local_path', 'FAILED')
            if args.verbose:
                print(f"  {i}. {nickname}: {local}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
