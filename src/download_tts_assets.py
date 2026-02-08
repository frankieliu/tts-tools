#!/usr/bin/env python3
"""
Download all assets referenced in a Tabletop Simulator JSON save file.
"""

import json
import re
import shutil
from pathlib import Path
from typing import Dict, Set, List
from urllib.parse import urlparse
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3


# URL field types and their corresponding directories
URL_FIELD_MAPPING = {
    'Images': ['ImageURL', 'FaceURL', 'BackURL', 'DiffuseURL', 'NormalURL', 'SkyURL', 'ImageSecondaryURL'],
    'Models': ['MeshURL', 'ColliderURL'],
    'Assetbundles': ['AssetbundleURL', 'AssetbundleSecondaryURL'],
}

# File extensions for each directory type
EXTENSION_MAPPING = {
    'Images': '.png',
    'Models': '.obj',
    'Assetbundles': '.unity3d',
}


def url_to_filename(url: str, extension: str) -> str:
    """
    Convert a Steam Workshop URL to a local filename.

    Example:
        https://steamusercontent-a.akamaihd.net/ugc/2503519332734782156/C253CB19458EC5FF4BD209D1E63A0F076F336726/
        -> httpssteamusercontentaakamaihdnetugc2503519332734782156C253CB19458EC5FF4BD209D1E63A0F076F336726.png
    """
    # Remove all special characters: ://-
    filename = re.sub(r'[:/\-]', '', url)
    # Remove trailing slashes that might have been converted to empty strings
    filename = filename.rstrip('/')
    # Add appropriate extension
    if not filename.endswith(extension):
        filename += extension
    return filename


def extract_urls_from_json(data: any, url_fields: Set[str]) -> List[str]:
    """
    Recursively extract all URLs from JSON data for specified field names.
    """
    urls = []

    if isinstance(data, dict):
        for key, value in data.items():
            if key in url_fields and isinstance(value, str) and value.startswith('http'):
                urls.append(value)
            else:
                urls.extend(extract_urls_from_json(value, url_fields))
    elif isinstance(data, list):
        for item in data:
            urls.extend(extract_urls_from_json(item, url_fields))

    return urls


def download_file(url: str, output_path: Path, session: requests.Session, verify_ssl: bool = True) -> tuple[str, bool, str]:
    """
    Download a file from URL to output_path.
    Returns (url, success, message)
    """
    try:
        if output_path.exists():
            return (url, True, f"Already exists: {output_path.name}")

        # Convert old Steam URL format to new format (from TTS Mod Vault technique)
        # cloud-3.steamusercontent.com -> steamusercontent-a.akamaihd.net
        download_url = url.replace('cloud-3.steamusercontent.com', 'steamusercontent-a.akamaihd.net')

        # Upgrade HTTP to HTTPS for Steam URLs
        download_url = download_url.replace('http://', 'https://') if download_url.startswith('http://') else download_url

        response = session.get(download_url, timeout=30, stream=True, verify=verify_ssl)
        response.raise_for_status()

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return (url, True, f"Downloaded: {output_path.name}")
    except Exception as e:
        return (url, False, f"Failed {output_path.name}: {str(e)}")


def download_tts_assets(json_path: str, output_dir: str = None, max_workers: int = 10, verify_ssl: bool = True):
    """
    Download all assets referenced in a TTS JSON file.

    Args:
        json_path: Path to the TTS JSON save file
        output_dir: Output directory (defaults to same directory as JSON file)
        max_workers: Maximum number of concurrent downloads
        verify_ssl: Whether to verify SSL certificates (disable for proxy issues)
    """
    # Disable SSL warnings if verification is disabled
    if not verify_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    json_path = Path(json_path)

    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    # Determine output directory
    if output_dir is None:
        output_dir = json_path.parent / json_path.stem
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading JSON file: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Copy JSON file to Workshop directory
    workshop_dir = output_dir / 'Workshop'
    workshop_dir.mkdir(exist_ok=True)
    workshop_json_path = workshop_dir / json_path.name
    shutil.copy2(json_path, workshop_json_path)
    print(f"Copied JSON to: {workshop_json_path}")

    # Extract URLs by category
    downloads = []  # List of (url, output_path) tuples

    for directory, url_fields in URL_FIELD_MAPPING.items():
        print(f"\nExtracting {directory} URLs...")
        url_field_set = set(url_fields)
        urls = extract_urls_from_json(data, url_field_set)
        unique_urls = list(set(urls))  # Remove duplicates

        print(f"  Found {len(urls)} references to {len(unique_urls)} unique URLs")

        # Create directory
        dir_path = output_dir / directory
        dir_path.mkdir(exist_ok=True)

        # Prepare download list
        extension = EXTENSION_MAPPING[directory]
        for url in unique_urls:
            filename = url_to_filename(url, extension)
            output_path = dir_path / filename
            downloads.append((url, output_path))

    # Download files concurrently
    print(f"\nDownloading {len(downloads)} assets with {max_workers} workers...")

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })

    success_count = 0
    fail_count = 0
    skip_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(download_file, url, path, session, verify_ssl): url
            for url, path in downloads
        }

        for i, future in enumerate(as_completed(future_to_url), 1):
            url, success, message = future.result()

            if "Already exists" in message:
                skip_count += 1
            elif success:
                success_count += 1
            else:
                fail_count += 1

            if i % 10 == 0 or not success:
                print(f"  [{i}/{len(downloads)}] {message}")

    # Summary
    print(f"\n{'='*60}")
    print(f"Download complete!")
    print(f"  Output directory: {output_dir}")
    print(f"  Already existed: {skip_count}")
    print(f"  Successfully downloaded: {success_count}")
    print(f"  Failed: {fail_count}")
    print(f"  Total: {len(downloads)}")
    print(f"{'='*60}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Download all assets from a Tabletop Simulator JSON save file'
    )
    parser.add_argument(
        'json_file',
        help='Path to the TTS JSON save file'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output directory (defaults to same directory as JSON file with mod name)'
    )
    parser.add_argument(
        '-w', '--workers',
        type=int,
        default=10,
        help='Number of concurrent download workers (default: 10)'
    )
    parser.add_argument(
        '--no-verify',
        action='store_true',
        help='Disable SSL certificate verification (use with corporate proxies)'
    )

    args = parser.parse_args()

    try:
        download_tts_assets(args.json_file, args.output, args.workers, verify_ssl=not args.no_verify)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
