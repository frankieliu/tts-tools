#!/usr/bin/env python3
"""
Extract tile and board information from TTS JSON files.

This script parses TTS JSON files to identify Custom_Tile and Custom_Board objects,
their image URLs, scales, and other properties needed for printing.

Usage:
    python extract_tiles.py Workshop/3160692601_Evenfall.deserialized.json -o tile_metadata.json
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any


def extract_filename_from_url(url: str) -> str:
    """Extract the last part of URL (typically the hash) for identification."""
    url = url.rstrip('/')
    return url.split('/')[-1]


def find_tiles_and_boards(data: Any) -> List[Dict]:
    """
    Recursively traverse JSON to find all Custom_Tile, Custom_Board, and Custom_Token objects.

    Returns a list of tile/board/token information dicts.
    """
    tiles_and_boards = []

    def traverse(obj):
        if isinstance(obj, dict):
            name = obj.get('Name', '')

            # Check if this is a Custom_Tile, Custom_Board, or Custom_Token
            if name in ('Custom_Tile', 'Custom_Board', 'Custom_Token'):
                # Extract relevant information
                transform = obj.get('Transform', {})
                custom_image = obj.get('CustomImage', {})

                tile_info = {
                    'name': name,
                    'guid': obj.get('GUID', ''),
                    'nickname': obj.get('Nickname', ''),
                    'description': obj.get('Description', ''),

                    # Transform
                    'scale_x': transform.get('scaleX', 1.0),
                    'scale_y': transform.get('scaleY', 1.0),
                    'scale_z': transform.get('scaleZ', 1.0),

                    # Image
                    'image_url': custom_image.get('ImageURL', ''),
                    'image_scalar': custom_image.get('ImageScalar', 1.0),
                    'width_scale': custom_image.get('WidthScale', 0.0),

                    # Custom Tile properties
                    'thickness': custom_image.get('CustomTile', {}).get('Thickness', 0.1),
                    'stackable': custom_image.get('CustomTile', {}).get('Stackable', False),
                    'stretch': custom_image.get('CustomTile', {}).get('Stretch', True),
                }

                tiles_and_boards.append(tile_info)

            # Recursively process all dict values
            for value in obj.values():
                traverse(value)

        elif isinstance(obj, list):
            # Recursively process all list items
            for item in obj:
                traverse(item)

    traverse(data)
    return tiles_and_boards


def find_local_image_file(url_id: str, base_dir: Path = None) -> str:
    """
    Find the local image file matching the URL identifier.

    Looks in Images/ directory for files containing the URL ID.
    """
    if base_dir is None:
        base_dir = Path('.')

    images_dir = base_dir / 'Images'
    if not images_dir.exists():
        return ''

    # Search for files containing this URL ID
    for ext in ['*.jpg', '*.png', '*.jpeg']:
        for image_file in images_dir.glob(ext):
            if url_id in image_file.name:
                return str(image_file)

    return ''


def process_json_file(json_path: Path) -> List[Dict[str, Any]]:
    """Process a single JSON file and extract all tiles and boards."""
    print(f"Processing {json_path}...")

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {json_path}: {e}", file=sys.stderr)
        return []

    # Find all tiles and boards
    items = find_tiles_and_boards(data)

    # Determine base directory for image search
    json_dir = json_path.parent
    if json_dir.name == 'Workshop':
        base_dir = json_dir.parent
    else:
        base_dir = json_dir

    # Enrich with local image paths
    for item in items:
        if item['image_url']:
            url_id = extract_filename_from_url(item['image_url'])
            item['image_url_id'] = url_id
            item['local_image'] = find_local_image_file(url_id, base_dir)
            item['source_file'] = str(json_path)

    return items


def main():
    parser = argparse.ArgumentParser(
        description='Extract tile and board information from TTS JSON files'
    )
    parser.add_argument(
        'json_files',
        nargs='+',
        type=Path,
        help='TTS JSON file(s) to process'
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        default=Path('tile_metadata.json'),
        help='Output JSON file (default: tile_metadata.json)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Process all JSON files
    all_items = []
    for json_file in args.json_files:
        if not json_file.exists():
            print(f"Warning: {json_file} not found, skipping", file=sys.stderr)
            continue

        items = process_json_file(json_file)
        all_items.extend(items)

    # Display summary
    tiles = [item for item in all_items if item['name'] == 'Custom_Tile']
    boards = [item for item in all_items if item['name'] == 'Custom_Board']
    tokens = [item for item in all_items if item['name'] == 'Custom_Token']

    print(f"\nFound {len(tiles)} tile(s), {len(boards)} board(s), and {len(tokens)} token(s):")

    if tiles:
        print(f"\nTiles:")
        for i, tile in enumerate(tiles[:10], 1):
            nickname = tile['nickname'] or '(unnamed)'
            scale = tile['scale_x']
            print(f"  {i}. {nickname}: scale {scale:.2f}")
        if len(tiles) > 10:
            print(f"  ... and {len(tiles) - 10} more")

    if boards:
        print(f"\nBoards:")
        for i, board in enumerate(boards[:10], 1):
            nickname = board['nickname'] or '(unnamed)'
            scale = board['scale_x']
            print(f"  {i}. {nickname}: scale {scale:.2f}")
        if len(boards) > 10:
            print(f"  ... and {len(boards) - 10} more")

    if tokens:
        print(f"\nTokens:")
        for i, token in enumerate(tokens[:10], 1):
            nickname = token['nickname'] or '(unnamed)'
            scale = token['scale_x']
            print(f"  {i}. {nickname}: scale {scale:.2f}")
        if len(tokens) > 10:
            print(f"  ... and {len(tokens) - 10} more")

    if args.verbose:
        for item in all_items[:5]:
            print(f"\n{item['name']} - {item['nickname']}:")
            print(f"  Scale: {item['scale_x']:.2f} x {item['scale_z']:.2f}")
            print(f"  Image: {item['local_image'] or 'NOT FOUND'}")

    # Save results
    output_data = {
        'tiles': tiles,
        'boards': boards,
        'tokens': tokens,
        'summary': {
            'total_tiles': len(tiles),
            'total_boards': len(boards),
            'total_tokens': len(tokens),
        }
    }

    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\nMetadata saved to {args.output}")

    # Check for missing images
    missing = [item for item in all_items if not item['local_image']]
    if missing:
        print(f"\nWarning: {len(missing)} item(s) missing local images")

    return 0


if __name__ == '__main__':
    sys.exit(main())
