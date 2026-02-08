"""
Steam Workshop API Client

This module provides functions to retrieve workshop item details from multiple APIs:
- Steam Official Web API (official, most reliable)
- SteamWorkshopDownloader.io Backend API (enriched metadata)
- GGNetwork API (alternative download links)
"""

import requests
import json
from typing import List, Dict, Any, Optional
from enum import Enum


class APIBackend(Enum):
    """Available API backends for fetching workshop data"""
    STEAM_OFFICIAL = "steam-api"
    STEAMWORKSHOP_IO = "steamworkshop"
    GGNETWORK = "ggnetwork"
    AUTO = "auto"  # Try multiple backends with fallback


def get_workshop_items_steam_official(published_file_ids: List[int], verbose: bool = False) -> List[Dict[str, Any]]:
    """
    Retrieve workshop item details from Steam's Official Web API.

    Steam API endpoint: ISteamRemoteStorage/GetPublishedFileDetails
    This is a public API that doesn't require authentication for most items.

    Args:
        published_file_ids: List of workshop item IDs to fetch (max 50 per request)
        verbose: Print debug information

    Returns:
        List of dictionaries containing workshop item metadata

    Example:
        >>> items = get_workshop_items_steam_official([123456789, 987654321])
        >>> for item in items:
        >>>     print(f"{item['title']} - {item.get('file_url', 'N/A')}")
    """

    # Steam's public API endpoint
    url = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"

    # Build the form data - Steam expects this format
    form_data = {
        'itemcount': len(published_file_ids)
    }

    # Add each file ID to the form data
    for idx, file_id in enumerate(published_file_ids):
        form_data[f'publishedfileids[{idx}]'] = file_id

    if verbose:
        print(f"[Steam Official API] Fetching {len(published_file_ids)} item(s)...")

    # Make the POST request
    response = requests.post(url, data=form_data)
    response.raise_for_status()

    # Parse the JSON response
    result = response.json()

    if verbose:
        print("Raw API Response:")
        print(json.dumps(result, indent=2))

    # Steam returns data under 'response' -> 'publishedfiledetails'
    if 'response' in result and 'publishedfiledetails' in result['response']:
        return result['response']['publishedfiledetails']

    return []


def get_workshop_items_steamworkshop_io(published_file_ids: List[int], verbose: bool = False) -> List[Dict[str, Any]]:
    """
    Retrieve workshop item details from SteamWorkshopDownloader.io Backend API.

    This API provides enriched metadata including direct download URLs, subscriptions, views, etc.

    Args:
        published_file_ids: List of workshop item IDs to fetch
        verbose: Print debug information

    Returns:
        List of dictionaries containing workshop item metadata
    """
    url = 'https://steamworkshopdownloader.io/api/details/file'

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    # Format as JSON array
    data = json.dumps(published_file_ids)

    if verbose:
        print(f"[SteamWorkshopDownloader.io] Fetching {len(published_file_ids)} item(s)...")

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()

    result = response.json()

    if verbose:
        print(f"Received data for {len(result)} item(s)")

    return result


def get_workshop_item_ggnetwork(workshop_id: int, verbose: bool = False) -> Optional[Dict[str, Any]]:
    """
    Get download link using GGNetwork API.

    This is a fallback API that can provide download URLs when other methods fail.
    Note: Only supports single item requests.

    Args:
        workshop_id: Workshop item ID
        verbose: Print debug information

    Returns:
        Dictionary with download URL and metadata, or None if failed
    """
    api_url = 'https://api.ggntw.com/steam.request'
    workshop_url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={workshop_id}"

    payload = {'url': workshop_url}

    if verbose:
        print(f"[GGNetwork API] Requesting download for {workshop_id}...")

    try:
        response = requests.post(api_url, json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if 'error' not in data and data.get('url'):
                return data
            return None
        else:
            return None
    except requests.exceptions.Timeout:
        if verbose:
            print("GGNetwork API timeout")
        return None
    except Exception as e:
        if verbose:
            print(f"GGNetwork API error: {e}")
        return None


def get_workshop_items(published_file_ids: List[int],
                       backend: APIBackend = APIBackend.AUTO,
                       verbose: bool = False) -> List[Dict[str, Any]]:
    """
    Retrieve workshop item details using specified backend or auto-fallback.

    This function supports multiple backends with automatic fallback:
    1. SteamWorkshopDownloader.io (enriched metadata, direct downloads)
    2. Steam Official API (most reliable, official)
    3. GGNetwork API (fallback for download URLs)

    Args:
        published_file_ids: List of workshop item IDs to fetch
        backend: Which API backend to use (AUTO for fallback chain)
        verbose: Print debug information about which backend is used

    Returns:
        List of dictionaries containing workshop item metadata

    Example:
        >>> # Auto-select best backend with fallback
        >>> items = get_workshop_items([123456789], backend=APIBackend.AUTO)
        >>>
        >>> # Use specific backend
        >>> items = get_workshop_items([123456789], backend=APIBackend.STEAM_OFFICIAL)
    """

    if backend == APIBackend.STEAMWORKSHOP_IO:
        if verbose:
            print("Using SteamWorkshopDownloader.io backend")
        return get_workshop_items_steamworkshop_io(published_file_ids, verbose)

    elif backend == APIBackend.STEAM_OFFICIAL:
        if verbose:
            print("Using Steam Official API backend")
        return get_workshop_items_steam_official(published_file_ids, verbose)

    elif backend == APIBackend.GGNETWORK:
        if verbose:
            print("Using GGNetwork API backend (single item only)")
        # GGNetwork only supports single items
        if len(published_file_ids) != 1:
            raise ValueError("GGNetwork backend only supports single item requests")
        result = get_workshop_item_ggnetwork(published_file_ids[0], verbose)
        return [result] if result else []

    elif backend == APIBackend.AUTO:
        if verbose:
            print("Using AUTO backend with fallback chain")

        # Try SteamWorkshopDownloader.io first (best metadata + download URLs)
        try:
            if verbose:
                print("Trying SteamWorkshopDownloader.io...")
            items = get_workshop_items_steamworkshop_io(published_file_ids, verbose)
            if items and all(item.get('file_url') for item in items):
                if verbose:
                    print("✓ SteamWorkshopDownloader.io succeeded")
                return items
        except Exception as e:
            if verbose:
                print(f"✗ SteamWorkshopDownloader.io failed: {e}")

        # Fallback to Steam Official API
        try:
            if verbose:
                print("Trying Steam Official API...")
            items = get_workshop_items_steam_official(published_file_ids, verbose)
            if items:
                if verbose:
                    print("✓ Steam Official API succeeded")
                # Check if we have download URLs, if not try to augment with GGNetwork
                for item in items:
                    if not item.get('file_url') and len(published_file_ids) == 1:
                        if verbose:
                            print("No download URL, trying GGNetwork...")
                        gg_data = get_workshop_item_ggnetwork(published_file_ids[0], verbose)
                        if gg_data and gg_data.get('url'):
                            item['file_url'] = gg_data['url']
                            item['file_url_source'] = 'ggnetwork'
                return items
        except Exception as e:
            if verbose:
                print(f"✗ Steam Official API failed: {e}")

        # Last resort: GGNetwork (single item only)
        if len(published_file_ids) == 1:
            try:
                if verbose:
                    print("Trying GGNetwork API as last resort...")
                result = get_workshop_item_ggnetwork(published_file_ids[0], verbose)
                if result:
                    if verbose:
                        print("✓ GGNetwork API succeeded")
                    return [result]
            except Exception as e:
                if verbose:
                    print(f"✗ GGNetwork API failed: {e}")

        # All backends failed
        if verbose:
            print("✗ All backends failed")
        return []

    else:
        raise ValueError(f"Unknown backend: {backend}")


def get_workshop_items_batch(published_file_ids: List[int], batch_size: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieve workshop items in batches (Steam API limits to ~100 items per request).

    Args:
        published_file_ids: List of workshop item IDs to fetch
        batch_size: Number of items per request (default: 50, max recommended: 50)

    Returns:
        Combined list of all workshop item metadata
    """
    all_items = []

    # Process in batches
    for i in range(0, len(published_file_ids), batch_size):
        batch = published_file_ids[i:i + batch_size]
        items = get_workshop_items(batch)
        all_items.extend(items)
        print(f"Fetched batch {i//batch_size + 1}/{(len(published_file_ids) + batch_size - 1)//batch_size}")

    return all_items


def parse_workshop_url(url: str) -> int:
    """
    Extract the workshop item ID from a Steam Workshop URL.

    Args:
        url: Steam Workshop URL (e.g., "http://steamcommunity.com/sharedfiles/filedetails/?id=123456789")

    Returns:
        Workshop item ID as an integer, or None if not found
    """
    import re

    # Match ?id=XXXXX pattern
    match = re.search(r'\?id=(\d+)', url)
    if match:
        return int(match.group(1))

    # Try to match just digits if it's a plain ID
    match = re.search(r'(\d+)', url)
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


# Example usage
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description='Retrieve Steam Workshop item details from Steam API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s 3253452064
  %(prog)s 3253452064 104691717
  %(prog)s --batch 3253452064 104691717 --batch-size 10
        '''
    )

    parser.add_argument(
        'item_ids',
        nargs='*',
        type=int,
        help='Steam Workshop item ID(s) to fetch'
    )

    parser.add_argument(
        '--batch',
        action='store_true',
        help='Use batch mode for multiple items'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Number of items per batch request (default: 50)'
    )

    args = parser.parse_args()

    # Use example IDs if none provided
    if not args.item_ids:
        print("No item IDs provided. Using example ID: 3253452064")
        print("Use -h or --help for usage information\n")
        args.item_ids = [3253452064]

    print(f"Fetching workshop items from Steam API...")

    if args.batch and len(args.item_ids) > 1:
        items = get_workshop_items_batch(args.item_ids, args.batch_size)
    else:
        items = get_workshop_items(args.item_ids)

    for item in items:
        print("\n" + "="*80)
        print(f"Title: {item.get('title', 'N/A')}")
        print(f"ID: {item.get('publishedfileid', 'N/A')}")
        print(f"Result Code: {item.get('result', 'N/A')} (1=success, 9=not found)")
        print(f"App ID: {item.get('consumer_appid', 'N/A')}")
        print(f"File Size: {format_file_size(int(item.get('file_size', 0)))}")
        print(f"Creator: {item.get('creator', 'N/A')}")
        print(f"Time Created: {item.get('time_created', 'N/A')}")
        print(f"Time Updated: {item.get('time_updated', 'N/A')}")
        print(f"Description: {item.get('description', 'N/A')[:200]}...")

        # Check if direct download URL is available
        file_url = item.get('file_url', '')
        if file_url:
            print(f"\n✓ Direct Download URL: {file_url}")
        else:
            print(f"\n✗ No direct download URL (requires SteamCMD)")
            print(f"  Command: workshop_download_item {item.get('consumer_appid')} {item.get('publishedfileid')}")

        # Additional metadata
        print(f"\nPreview: {item.get('preview_url', 'N/A')}")
        print(f"Views: {item.get('views', 'N/A')}")
        print(f"Subscriptions: {item.get('subscriptions', 'N/A')}")
        print(f"Favorited: {item.get('favorited', 'N/A')}")
