#!/usr/bin/env python3
"""
Extract 3D model diffuse textures from TTS JSON files.

This script parses TTS JSON files to identify Custom_Model objects and their
diffuse texture URLs for printing.

Usage:
    python extract_model_textures.py Workshop/mod.deserialized.json -o model_texture_metadata.json
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


def find_models(data: Any) -> List[Dict]:
    """
    Recursively traverse JSON to find all Custom_Model objects with diffuse textures.

    Returns a list of model information dicts.
    """
    models = []

    def traverse(obj):
        if isinstance(obj, dict):
            name = obj.get('Name', '')

            if name == 'Custom_Model':
                custom_mesh = obj.get('CustomMesh', {})
                diffuse_url = custom_mesh.get('DiffuseURL', '')

                if diffuse_url:
                    transform = obj.get('Transform', {})

                    model_info = {
                        'name': name,
                        'guid': obj.get('GUID', ''),
                        'nickname': obj.get('Nickname', ''),
                        'description': obj.get('Description', ''),

                        # Transform
                        'scale_x': transform.get('scaleX', 1.0),
                        'scale_y': transform.get('scaleY', 1.0),
                        'scale_z': transform.get('scaleZ', 1.0),

                        # Mesh info
                        'diffuse_url': diffuse_url,
                        'normal_url': custom_mesh.get('NormalURL', ''),
                        'mesh_url': custom_mesh.get('MeshURL', ''),
                    }

                    models.append(model_info)

            # Recursively process all dict values
            for value in obj.values():
                traverse(value)

        elif isinstance(obj, list):
            for item in obj:
                traverse(item)

    traverse(data)
    return models


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

    for ext in ['*.jpg', '*.png', '*.jpeg']:
        for image_file in images_dir.glob(ext):
            if url_id in image_file.name:
                return str(image_file)

    return ''


def process_json_file(json_path: Path) -> List[Dict[str, Any]]:
    """Process a single JSON file and extract all model textures."""
    print(f"Processing {json_path}...")

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {json_path}: {e}", file=sys.stderr)
        return []

    items = find_models(data)

    # Determine base directory for image search
    json_dir = json_path.parent
    if json_dir.name == 'Workshop':
        base_dir = json_dir.parent
    else:
        base_dir = json_dir

    # Enrich with local image paths
    for item in items:
        url_id = extract_filename_from_url(item['diffuse_url'])
        item['image_url_id'] = url_id
        item['local_image'] = find_local_image_file(url_id, base_dir)
        item['source_file'] = str(json_path)

    return items


def main():
    parser = argparse.ArgumentParser(
        description='Extract 3D model diffuse textures from TTS JSON files'
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
        default=Path('model_texture_metadata.json'),
        help='Output JSON file (default: model_texture_metadata.json)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # If output path is the default (relative), place it next to the input file's parent dir
    if args.output == Path('model_texture_metadata.json') and args.json_files:
        first_input = Path(args.json_files[0]).resolve()
        # Input is typically Workshop/*.json; place metadata in the .deserialized/ dir
        args.output = first_input.parent.parent / 'model_texture_metadata.json'

    # Process all JSON files
    all_items = []
    for json_file in args.json_files:
        if not json_file.exists():
            print(f"Warning: {json_file} not found, skipping", file=sys.stderr)
            continue

        items = process_json_file(json_file)
        all_items.extend(items)

    # Deduplicate by diffuse URL
    seen_urls = {}
    unique_items = []
    for item in all_items:
        url = item['diffuse_url']
        if url in seen_urls:
            seen_urls[url]['count'] += 1
        else:
            item['count'] = 1
            seen_urls[url] = item
            unique_items.append(item)

    print(f"\nFound {len(all_items)} model texture(s) ({len(unique_items)} unique):")

    if unique_items:
        for i, item in enumerate(unique_items[:10], 1):
            nickname = item['nickname'] or '(unnamed)'
            count = item['count']
            count_str = f" (x{count})" if count > 1 else ""
            print(f"  {i}. {nickname}{count_str}")
        if len(unique_items) > 10:
            print(f"  ... and {len(unique_items) - 10} more")

    if args.verbose:
        for item in unique_items[:5]:
            print(f"\n{item['nickname'] or '(unnamed)'}:")
            print(f"  Diffuse: {item['diffuse_url'][:80]}")
            print(f"  Local: {item['local_image'] or 'NOT FOUND'}")
            print(f"  Count: {item['count']}")

    # Save results
    output_data = {
        'models': unique_items,
        'summary': {
            'total_instances': len(all_items),
            'unique_textures': len(unique_items),
        }
    }

    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\nMetadata saved to {args.output}")

    # Check for missing images
    missing = [item for item in unique_items if not item['local_image']]
    if missing:
        print(f"\nWarning: {len(missing)} texture(s) missing local images")

    return 0


if __name__ == '__main__':
    sys.exit(main())
