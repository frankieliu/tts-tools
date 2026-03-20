#!/usr/bin/env python3
"""
Extract textures from Unity Asset Bundle (.unity3d) files in TTS mods.

Uses UnityPy to load .unity3d files from the Assetbundles/ directory,
extract Texture2D and Sprite objects, save them as PNGs, and produce
metadata JSON compatible with the model textures PDF generator.

Usage:
    python extract_bundle_textures.py Workshop/mod.deserialized.json
    python extract_bundle_textures.py Workshop/mod.deserialized.json -o bundle_texture_metadata.json
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any

try:
    import UnityPy
except ImportError:
    print("Error: UnityPy is required. Install with: uv pip install UnityPy", file=sys.stderr)
    sys.exit(1)


# Texture name patterns that indicate non-printable PBR/technical maps
SKIP_PATTERNS = [
    '_n', '_normal', '_norm', 'normal',
    '_metallic', 'metallicsmoothness', '_ao',
    '_height', '_roughness', '_specular', '_emission',
    '_mask', '_occlusion',
]


def is_printable_texture(name: str, width: int, height: int, min_size: int = 4) -> bool:
    """Check if a texture is likely printable content (not a PBR map)."""
    if width < min_size or height < min_size:
        return False

    name_lower = name.lower()
    for pattern in SKIP_PATTERNS:
        # Check as suffix or as a word boundary pattern
        if name_lower.endswith(pattern):
            return False
        if f'{pattern}_' in name_lower or f'{pattern} ' in name_lower:
            return False

    return True


def extract_bundle(bundle_path: Path, output_dir: Path, skip_technical: bool = True) -> List[Dict]:
    """Extract textures from a single .unity3d bundle file.

    Args:
        bundle_path: Path to the .unity3d file
        output_dir: Directory to save extracted PNG files
        skip_technical: Skip normal maps, AO maps, etc.

    Returns:
        List of texture metadata dicts
    """
    env = UnityPy.load(str(bundle_path))
    textures = []

    for obj in env.objects:
        if obj.type.name not in ("Texture2D", "Sprite"):
            continue

        try:
            parsed = obj.parse_as_object()
            name = getattr(parsed, "m_Name", f"unknown_{obj.path_id}")

            if obj.type.name == "Texture2D":
                width, height = parsed.m_Width, parsed.m_Height
            else:
                img = parsed.image
                if img is None:
                    continue
                width, height = img.size

            if skip_technical and not is_printable_texture(name, width, height):
                continue

            img = parsed.image
            if img is None:
                continue

            # Sanitize filename
            safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in name)
            out_path = output_dir / f"{safe_name}.png"

            # Handle duplicate names
            counter = 1
            while out_path.exists():
                out_path = output_dir / f"{safe_name}_{counter}.png"
                counter += 1

            img.save(str(out_path))

            textures.append({
                "name": name,
                "nickname": name,
                "type": obj.type.name,
                "width": width,
                "height": height,
                "local_image": str(out_path),
                "bundle_file": str(bundle_path),
                "count": 1,
            })
        except Exception as e:
            print(f"  Warning: Failed to extract {obj.type.name} from {bundle_path.name}: {e}",
                  file=sys.stderr)

    return textures


def find_assetbundles_dir(json_path: Path) -> Path:
    """Find the Assetbundles directory relative to the Workshop JSON."""
    json_dir = json_path.parent
    if json_dir.name == 'Workshop':
        base_dir = json_dir.parent
    else:
        base_dir = json_dir

    return base_dir / 'Assetbundles'


def process_json_file(json_path: Path) -> List[Dict[str, Any]]:
    """Find and extract textures from all asset bundles for a mod."""
    print(f"Processing {json_path}...")

    assetbundles_dir = find_assetbundles_dir(json_path)

    if not assetbundles_dir.exists():
        print(f"  No Assetbundles/ directory found")
        return []

    bundle_files = sorted(assetbundles_dir.glob("*.unity3d"))
    if not bundle_files:
        print(f"  No .unity3d files found in {assetbundles_dir}")
        return []

    print(f"  Found {len(bundle_files)} asset bundle(s)")

    # Create output directory for extracted textures
    output_dir = assetbundles_dir.parent / 'BundleTextures'
    output_dir.mkdir(exist_ok=True)

    all_textures = []
    for bundle_file in bundle_files:
        try:
            textures = extract_bundle(bundle_file, output_dir)
            if textures:
                print(f"  {bundle_file.name[:60]}... → {len(textures)} texture(s)")
            all_textures.extend(textures)
        except Exception as e:
            print(f"  Error loading {bundle_file.name[:60]}...: {e}", file=sys.stderr)

    return all_textures


def main():
    parser = argparse.ArgumentParser(
        description='Extract textures from Unity Asset Bundle (.unity3d) files'
    )
    parser.add_argument(
        'json_files',
        nargs='+',
        type=Path,
        help='TTS JSON file(s) (used to locate the Assetbundles/ directory)'
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        default=Path('bundle_texture_metadata.json'),
        help='Output metadata JSON file (default: bundle_texture_metadata.json)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Include technical textures (normal maps, AO, etc.)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Default output placement
    if args.output == Path('bundle_texture_metadata.json') and args.json_files:
        first_input = Path(args.json_files[0]).resolve()
        if first_input.parent.name == 'Workshop':
            args.output = first_input.parent.parent / 'bundle_texture_metadata.json'
        else:
            args.output = first_input.parent / 'bundle_texture_metadata.json'

    all_textures = []
    for json_file in args.json_files:
        if not json_file.exists():
            print(f"Warning: {json_file} not found, skipping", file=sys.stderr)
            continue

        textures = process_json_file(json_file)
        all_textures.extend(textures)

    # Deduplicate by image content (same name + same dimensions from same bundle)
    seen = {}
    unique_textures = []
    for tex in all_textures:
        key = (tex['name'], tex['width'], tex['height'])
        if key in seen:
            seen[key]['count'] += 1
        else:
            seen[key] = tex
            unique_textures.append(tex)

    print(f"\nFound {len(all_textures)} bundle texture(s) ({len(unique_textures)} unique):")

    if unique_textures:
        for i, tex in enumerate(unique_textures[:10], 1):
            count = tex['count']
            count_str = f" (x{count})" if count > 1 else ""
            print(f"  {i}. {tex['name']}{count_str} ({tex['width']}x{tex['height']})")
        if len(unique_textures) > 10:
            print(f"  ... and {len(unique_textures) - 10} more")

    # Save as metadata JSON compatible with generate_model_textures_pdf
    output_data = {
        'models': unique_textures,
        'summary': {
            'total_instances': len(all_textures),
            'unique_textures': len(unique_textures),
        }
    }

    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\nMetadata saved to {args.output}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
