"""
Enhanced Steam Workshop Downloader

This script:
1. Parses Steam Workshop URLs
2. Calls multiple backend APIs with automatic fallback:
   - SteamWorkshopDownloader.io (enriched metadata, direct downloads)
   - Steam Official API (most reliable)
   - GGNetwork API (alternative download links)
3. Downloads workshop files directly from file_url
"""

import requests
import json
import re
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from steam_workshop_api import APIBackend, get_workshop_items


def parse_workshop_url(url_or_id: str) -> Optional[int]:
    """
    Extract workshop item ID from URL or direct ID.

    Args:
        url_or_id: Steam Workshop URL or just the ID

    Returns:
        Workshop item ID as integer, or None if invalid

    Examples:
        >>> parse_workshop_url("https://steamcommunity.com/sharedfiles/filedetails/?id=3253452064")
        3253452064
        >>> parse_workshop_url("3253452064")
        3253452064
    """
    # Try to match ?id=XXXXX pattern
    match = re.search(r'\?id=(\d+)', url_or_id)
    if match:
        return int(match.group(1))

    # Try to match just digits
    match = re.search(r'(\d+)', url_or_id)
    if match:
        return int(match.group(1))

    return None


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1000:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1000
    return f"{size_bytes:.2f} PB"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe filesystem usage.

    Args:
        filename: Original filename

    Returns:
        Safe filename with invalid characters removed
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename


def download_file(url: str, output_path: Path, item_info: Dict[str, Any]) -> bool:
    """
    Download a file from URL with progress indication.

    Args:
        url: Download URL
        output_path: Where to save the file
        item_info: Workshop item metadata

    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"\n📥 Downloading: {item_info.get('title', 'Unknown')}")
        print(f"   From: {url}")
        print(f"   To: {output_path}")

        # Stream the download
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        # Create parent directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Download with progress
        downloaded = 0
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r   Progress: {percent:.1f}% ({format_file_size(downloaded)} / {format_file_size(total_size)})", end='')

        print()  # New line after progress
        print(f"✅ Downloaded successfully!")
        print(f"   Size: {format_file_size(downloaded)}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Download failed: {e}")
        return False


def download_workshop_item(url_or_id: str, output_dir: str = ".",
                          backend: APIBackend = APIBackend.AUTO,
                          verbose: bool = False) -> bool:
    """
    Download a workshop item by URL or ID.

    This is the main function that orchestrates the entire process:
    1. Parse URL/ID
    2. Call backend API (with automatic fallback if backend=AUTO)
    3. Download file if available

    Args:
        url_or_id: Steam Workshop URL or ID
        output_dir: Directory to save downloads
        backend: Which API backend to use (default: AUTO for best success rate)
        verbose: Print detailed API backend information

    Returns:
        True if successful, False otherwise
    """
    # Parse URL/ID
    workshop_id = parse_workshop_url(url_or_id)

    if not workshop_id:
        print(f"❌ Invalid workshop URL or ID: {url_or_id}")
        return False

    print(f"📋 Workshop ID: {workshop_id}")

    try:
        # Call backend API with automatic fallback
        items = get_workshop_items([workshop_id], backend=backend, verbose=verbose)

        if not items:
            print("❌ No data returned from backend")
            return False

        item = items[0]

        # Display item info
        print(f"\n{'='*80}")
        print(f"📦 Workshop Item Details")
        print(f"{'='*80}")
        print(f"Title: {item.get('title', 'N/A')}")
        print(f"ID: {item.get('publishedfileid')}")
        print(f"Game: {item.get('app_name', 'N/A')} (App ID: {item.get('consumer_appid')})")
        print(f"File Size: {format_file_size(int(item.get('file_size', 0)))}")
        print(f"Creator: {item.get('creator', 'N/A')}")
        print(f"Subscriptions: {item.get('subscriptions', 0):,}")
        print(f"Views: {item.get('views', 0):,}")

        # Check for download URL
        file_url = item.get('file_url', '')

        if not file_url or file_url == '':
            print(f"\n⚠️  No direct download URL available")
            print(f"   This item requires SteamCMD to download")
            print(f"   Command: workshop_download_item {item.get('consumer_appid')} {item.get('publishedfileid')}")
            return False

        print(f"\n✅ Direct download URL available!")
        print(f"   URL: {file_url}")

        # Generate filename
        title = item.get('title', f"workshop_{workshop_id}")
        safe_title = sanitize_filename(title)

        # Try to get extension from URL
        parsed_url = urlparse(file_url)
        path_parts = parsed_url.path.split('/')
        original_filename = path_parts[-1] if path_parts else ''

        # Use original filename if it has extension, otherwise use title
        if original_filename and '.' in original_filename:
            filename = f"{workshop_id}_{original_filename}"
        else:
            # Default to .tts if no extension (Tabletop Simulator files)
            filename = f"{workshop_id}_{safe_title}.tts"

        output_path = Path(output_dir) / filename

        # Download the file
        success = download_file(file_url, output_path, item)

        if success:
            print(f"\n🎉 Success! Workshop item downloaded to:")
            print(f"   {output_path.absolute()}")

            # Save metadata
            metadata_path = output_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump(item, f, indent=2)
            print(f"   Metadata saved to: {metadata_path}")

            # Download preview image if available
            preview_url = item.get('preview_url', '')
            if preview_url:
                try:
                    print(f"\n📷 Downloading preview image...")

                    # Extract extension from preview URL
                    parsed_preview = urlparse(preview_url)
                    preview_ext = Path(parsed_preview.path).suffix or '.jpg'

                    # Use same base filename as the main file
                    preview_path = output_path.with_suffix(preview_ext)

                    # Download preview
                    preview_response = requests.get(preview_url, timeout=30)
                    preview_response.raise_for_status()

                    with open(preview_path, 'wb') as f:
                        f.write(preview_response.content)

                    print(f"   Preview saved to: {preview_path.absolute()}")

                except Exception as e:
                    print(f"   ⚠️  Could not download preview: {e}")

        return success

    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def download_multiple_items(urls_or_ids: List[str], output_dir: str = ".",
                           backend: APIBackend = APIBackend.AUTO,
                           verbose: bool = False) -> Dict[str, bool]:
    """
    Download multiple workshop items.

    Args:
        urls_or_ids: List of Steam Workshop URLs or IDs
        output_dir: Directory to save downloads
        backend: Which API backend to use (default: AUTO)
        verbose: Print detailed API backend information

    Returns:
        Dictionary mapping ID to success status
    """
    results = {}

    print(f"📥 Downloading {len(urls_or_ids)} workshop item(s)...")
    print(f"Output directory: {output_dir}")
    print(f"{'='*80}\n")

    for idx, url_or_id in enumerate(urls_or_ids, 1):
        print(f"\n[{idx}/{len(urls_or_ids)}] Processing: {url_or_id}")
        print(f"{'-'*80}")

        workshop_id = parse_workshop_url(url_or_id)
        success = download_workshop_item(url_or_id, output_dir, backend=backend, verbose=verbose)
        results[str(workshop_id)] = success

        print(f"{'-'*80}")

    # Summary
    print(f"\n{'='*80}")
    print(f"📊 Download Summary")
    print(f"{'='*80}")
    print(f"Total: {len(results)}")
    print(f"Success: {sum(results.values())}")
    print(f"Failed: {len(results) - sum(results.values())}")

    return results


# Example usage
if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description='Download Steam Workshop items directly from file URLs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s https://steamcommunity.com/sharedfiles/filedetails/?id=3253452064
  %(prog)s 3253452064
  %(prog)s 3253452064 104691717 --output-dir ./my_downloads
  %(prog)s --multiple 3253452064 104691717 3474332258
        '''
    )

    parser.add_argument(
        'urls_or_ids',
        nargs='*',
        help='Steam Workshop URL(s) or item ID(s) to download'
    )

    parser.add_argument(
        '-o', '--output-dir',
        default='.',
        help='Directory to save downloads (default: current directory)'
    )

    parser.add_argument(
        '-m', '--multiple',
        action='store_true',
        help='Download multiple items and show summary'
    )

    parser.add_argument(
        '-b', '--backend',
        choices=['auto', 'steamworkshop', 'steam-api', 'ggnetwork'],
        default='auto',
        help='API backend to use (default: auto - tries multiple with fallback)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print detailed API backend information'
    )

    args = parser.parse_args()

    # Map backend string to enum
    backend_map = {
        'auto': APIBackend.AUTO,
        'steamworkshop': APIBackend.STEAMWORKSHOP_IO,
        'steam-api': APIBackend.STEAM_OFFICIAL,
        'ggnetwork': APIBackend.GGNETWORK
    }
    backend = backend_map[args.backend]

    print("Steam Workshop Downloader (Enhanced)")
    print("="*80)
    if args.verbose:
        print(f"Backend: {args.backend}")
        print("="*80)

    # Get URL from command line or use default
    if not args.urls_or_ids:
        url = "https://steamcommunity.com/sharedfiles/filedetails/?id=3253452064"
        print(f"No URL provided, using example: {url}")
        print("Use -h or --help for usage information\n")
        args.urls_or_ids = [url]

    # Download items
    if args.multiple or len(args.urls_or_ids) > 1:
        results = download_multiple_items(args.urls_or_ids, args.output_dir,
                                         backend=backend, verbose=args.verbose)
        sys.exit(0 if all(results.values()) else 1)
    else:
        success = download_workshop_item(args.urls_or_ids[0],
                                        output_dir=args.output_dir,
                                        backend=backend,
                                        verbose=args.verbose)

        if success:
            print("\n✅ All done!")
            sys.exit(0)
        else:
            print("\n❌ Download failed")
            sys.exit(1)
