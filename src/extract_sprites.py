#!/usr/bin/env python3
"""
Extract sprite sheet information from Tabletop Simulator JSON files.

This script parses TTS JSON files to identify sprite sheets (card images),
their grid dimensions, and which positions are used for cards vs card backs.

Usage:
    python extract_sprites.py Workshop/2083854795.json -o sprite_metadata.json
    python extract_sprites.py Workshop/*.json -o sprite_metadata.json
"""

import json
import argparse
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Any
import re


def extract_filename_from_url(url: str) -> str:
    """Extract the last part of URL (typically the hash) for identification."""
    # Remove trailing slash and get last component
    url = url.rstrip('/')
    return url.split('/')[-1]


def find_sprite_sheets(data: Any, sprite_info: Dict = None) -> Dict:
    """
    Recursively traverse JSON to find all CustomDeck entries and associated cards.

    Returns a dict mapping deck_id -> sprite sheet information
    """
    if sprite_info is None:
        sprite_info = defaultdict(lambda: {
            'face_url': '',
            'back_url': '',
            'num_width': 0,
            'num_height': 0,
            'unique_back': False,
            'card_positions': set(),
            'card_nicknames': {},
            'deck_id': '',
        })

    if isinstance(data, dict):
        # Check if this is a card object with CardID and CustomDeck
        if 'CardID' in data and 'CustomDeck' in data:
            card_id = data['CardID']
            nickname = data.get('Nickname', '')

            # Process each CustomDeck reference
            for deck_id_str, deck_info in data['CustomDeck'].items():
                face_url = deck_info.get('FaceURL', '')

                # Calculate grid position from CardID
                # CardID format: DDDPP where DDD is deck ID, PP is position
                grid_position = card_id % 100

                # Store deck information
                if not sprite_info[deck_id_str]['face_url']:
                    sprite_info[deck_id_str].update({
                        'face_url': face_url,
                        'back_url': deck_info.get('BackURL', ''),
                        'num_width': deck_info.get('NumWidth', 0),
                        'num_height': deck_info.get('NumHeight', 0),
                        'unique_back': deck_info.get('UniqueBack', False),
                        'deck_id': deck_id_str,
                    })

                # Record this card position
                sprite_info[deck_id_str]['card_positions'].add(grid_position)
                sprite_info[deck_id_str]['card_nicknames'][grid_position] = nickname

        # Check if this is a deck object with DeckIDs array and CustomDeck
        elif 'DeckIDs' in data and 'CustomDeck' in data:
            deck_ids = data['DeckIDs']

            # Process each CustomDeck reference
            for deck_id_str, deck_info in data['CustomDeck'].items():
                face_url = deck_info.get('FaceURL', '')

                # Store deck information
                if not sprite_info[deck_id_str]['face_url']:
                    sprite_info[deck_id_str].update({
                        'face_url': face_url,
                        'back_url': deck_info.get('BackURL', ''),
                        'num_width': deck_info.get('NumWidth', 0),
                        'num_height': deck_info.get('NumHeight', 0),
                        'unique_back': deck_info.get('UniqueBack', False),
                        'deck_id': deck_id_str,
                    })

                # Process all card IDs in the deck
                for card_id in deck_ids:
                    # Calculate grid position from CardID
                    # CardID format: DDDPP where DDD is deck ID, PP is position
                    grid_position = card_id % 100

                    # Check if this card belongs to this deck
                    card_deck_id = str(card_id // 100)
                    if card_deck_id == deck_id_str:
                        # Record this card position
                        sprite_info[deck_id_str]['card_positions'].add(grid_position)
                        # Try to find nickname from ContainedObjects if available
                        if 'ContainedObjects' in data:
                            for obj in data['ContainedObjects']:
                                if obj.get('CardID') == card_id:
                                    nickname = obj.get('Nickname', '')
                                    sprite_info[deck_id_str]['card_nicknames'][grid_position] = nickname
                                    break

        # Recursively process all dict values
        for value in data.values():
            find_sprite_sheets(value, sprite_info)

    elif isinstance(data, list):
        # Recursively process all list items
        for item in data:
            find_sprite_sheets(item, sprite_info)

    return sprite_info


def analyze_sprite_sheet(deck_id: str, info: Dict, base_dir: Path = None) -> Dict:
    """
    Analyze a sprite sheet to determine card layout and usage.

    Args:
        deck_id: Deck identifier
        info: Sprite sheet information
        base_dir: Base directory for finding local images

    Returns a structured dict with all relevant information.
    """
    positions = sorted(info['card_positions'])
    num_width = info['num_width']
    num_height = info['num_height']
    total_positions = num_width * num_height

    # Determine card back position (usually the last position: total_positions - 1)
    # It's the position NOT in the card_positions list
    all_positions = set(range(total_positions))
    unused_positions = sorted(all_positions - info['card_positions'])

    # Common pattern: card back is at the last position
    likely_back_position = total_positions - 1 if (total_positions - 1) in unused_positions else None

    # Extract URL identifier
    face_url_id = extract_filename_from_url(info['face_url'])

    # Try to find matching image file
    image_file = find_local_image_file(face_url_id, base_dir)

    # Handle unique backs - find the back sprite sheet image
    unique_back = info.get('unique_back', False)
    back_image_file = ''
    back_url_id = ''
    if unique_back and info['back_url']:
        back_url_id = extract_filename_from_url(info['back_url'])
        back_image_file = find_local_image_file(back_url_id, base_dir)

    result = {
        'deck_id': deck_id,
        'face_url': info['face_url'],
        'face_url_id': face_url_id,
        'back_url': info['back_url'],
        'unique_back': unique_back,
        'back_url_id': back_url_id,
        'local_back_image': back_image_file,
        'local_image': image_file,
        'grid_width': num_width,
        'grid_height': num_height,
        'total_positions': total_positions,
        'num_cards': len(positions),
        'used_positions': positions,
        'unused_positions': unused_positions,
        'likely_back_position': likely_back_position,
        'card_nicknames': {str(k): v for k, v in info['card_nicknames'].items()},
    }

    return result


def find_local_image_file(url_id: str, base_dir: Path = None) -> str:
    """
    Find the local image file matching the URL identifier.

    Looks in Images/ directory for files containing the URL ID.

    Args:
        url_id: URL identifier to search for
        base_dir: Base directory to search from (looks for base_dir/Images/)
    """
    if base_dir is None:
        base_dir = Path('.')

    images_dir = base_dir / 'Images'
    if not images_dir.exists():
        return ''

    # Search for files containing this URL ID
    for image_file in images_dir.glob('*.jpg'):
        if url_id in image_file.name:
            return str(image_file)

    for image_file in images_dir.glob('*.png'):
        if url_id in image_file.name:
            return str(image_file)

    return ''


def process_json_file(json_path: Path) -> Dict[str, Any]:
    """Process a single JSON file and extract all sprite sheets."""
    print(f"Processing {json_path}...")

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {json_path}: {e}", file=sys.stderr)
        return {}

    # Find all sprite sheets
    sprite_info = find_sprite_sheets(data)

    # Determine base directory for image search
    # If JSON is in Workshop/ subdirectory, use parent; otherwise use JSON's directory
    json_dir = json_path.parent
    if json_dir.name == 'Workshop':
        base_dir = json_dir.parent
    else:
        base_dir = json_dir

    # Analyze each sprite sheet
    results = {}
    for deck_id, info in sprite_info.items():
        if info['face_url']:  # Only process if we found a face URL
            analyzed = analyze_sprite_sheet(deck_id, info, base_dir)
            results[deck_id] = analyzed

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Extract sprite sheet information from TTS JSON files'
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
        default=Path('sprite_metadata.json'),
        help='Output JSON file (default: sprite_metadata.json)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Process all JSON files
    all_sprites = {}
    for json_file in args.json_files:
        if not json_file.exists():
            print(f"Warning: {json_file} not found, skipping", file=sys.stderr)
            continue

        sprites = process_json_file(json_file)

        # Merge results (use deck_id as key to avoid duplicates)
        for deck_id, sprite_data in sprites.items():
            sprite_data['source_file'] = str(json_file)
            all_sprites[deck_id] = sprite_data

    # Display summary
    print(f"\nFound {len(all_sprites)} sprite sheet(s):")
    for deck_id, sprite in all_sprites.items():
        print(f"  Deck {deck_id}: {sprite['grid_width']}×{sprite['grid_height']} grid, "
              f"{sprite['num_cards']} cards, URL ID: ...{sprite['face_url_id']}")
        if args.verbose:
            print(f"    Positions: {sprite['used_positions'][:5]}...{sprite['used_positions'][-3:]}")
            print(f"    Local image: {sprite['local_image'] or 'NOT FOUND'}")

    # Save results
    output_data = {
        'sprite_sheets': all_sprites,
        'summary': {
            'total_sheets': len(all_sprites),
            'total_cards': sum(s['num_cards'] for s in all_sprites.values()),
        }
    }

    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\nMetadata saved to {args.output}")

    # Check for missing images
    missing = [s for s in all_sprites.values() if not s['local_image']]
    if missing:
        print(f"\nWarning: {len(missing)} sprite sheet(s) missing local images:")
        for sprite in missing:
            print(f"  Deck {sprite['deck_id']}: {sprite['face_url_id']}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
