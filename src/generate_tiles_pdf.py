#!/usr/bin/env python3
"""
Generate PDFs with tiles, boards, and tokens from a TTS JSON file.

Small items (tokens and small tiles) are packed efficiently on pages.
Large items (boards and large tiles) get one per page.

Scaling convention:
  - 1 TTS scale unit = 1 inch by default
  - Can be adjusted with --scale-factor parameter
"""

import json
from pathlib import Path
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader
import sys


# Standard card dimensions for auto-detection
STANDARD_CARD_HEIGHT_MM = 88.0  # Standard poker card height
STANDARD_CARD_ASPECT_MIN = 0.60  # Minimum aspect ratio for standard cards
STANDARD_CARD_ASPECT_MAX = 0.80  # Maximum aspect ratio for standard cards


def auto_detect_scale_factor(json_file: Path) -> float | None:
    """
    Auto-detect scale factor from cards in the TTS JSON file.

    Looks for DeckCustom objects with standard card aspect ratios and
    derives the scale factor based on standard card dimensions.

    Formula: scale_factor = (STANDARD_CARD_HEIGHT_MM / scaleZ) / 25.4

    Returns:
        Scale factor (TTS units to inches), or None if can't detect
    """
    try:
        with open(json_file) as f:
            data = json.load(f)
    except Exception as e:
        print(f"Warning: Could not read JSON for scale detection: {e}")
        return None

    # Find all DeckCustom objects
    deck_scales = []

    def find_decks(obj, depth=0):
        """Recursively find DeckCustom objects"""
        if not isinstance(obj, dict):
            return

        obj_name = obj.get('Name', '')

        if obj_name in ('DeckCustom', 'Deck'):
            transform = obj.get('Transform', {})
            scale_z = transform.get('scaleZ', 1.0)

            # Check if this looks like a standard card deck
            custom_deck = obj.get('CustomDeck', {})
            for deck_id, deck_info in custom_deck.items():
                num_width = deck_info.get('NumWidth', 1)
                num_height = deck_info.get('NumHeight', 1)

                # Standard cards typically have 1 row (NumHeight=1) or known grid sizes
                # and aspect ratios around 0.71 (63/88)
                if num_height >= 1:
                    deck_scales.append({
                        'scale_z': scale_z,
                        'num_width': num_width,
                        'num_height': num_height,
                        'nickname': obj.get('Nickname', ''),
                    })

        # Recurse into contained objects
        for key in ('ObjectStates', 'ContainedObjects'):
            if key in obj and isinstance(obj[key], list):
                for item in obj[key]:
                    find_decks(item, depth + 1)

    find_decks(data)

    if not deck_scales:
        return None

    # Find decks with typical card scales (0.8 - 1.5 range, avoiding very large/small)
    candidate_scales = [d['scale_z'] for d in deck_scales if 0.5 <= d['scale_z'] <= 2.0]

    if not candidate_scales:
        # Fall back to all scales
        candidate_scales = [d['scale_z'] for d in deck_scales]

    if not candidate_scales:
        return None

    # Use the most common scale value (mode)
    from collections import Counter
    scale_counts = Counter(round(s, 2) for s in candidate_scales)
    most_common_scale = scale_counts.most_common(1)[0][0]

    # Calculate BASE from standard card height
    # BASE = standard_height_mm / scaleZ
    base_mm = STANDARD_CARD_HEIGHT_MM / most_common_scale

    # Convert to scale factor (mm to inches)
    scale_factor = base_mm / 25.4

    return scale_factor


def extract_items(metadata_file: Path) -> tuple:
    """
    Extract tiles, boards, and tokens from metadata.

    Returns: (tiles_list, boards_list, tokens_list)
    """
    with open(metadata_file) as f:
        metadata = json.load(f)

    tiles = metadata.get('tiles', [])
    boards = metadata.get('boards', [])
    tokens = metadata.get('tokens', [])

    return tiles, boards, tokens


def calculate_print_size(scale_x: float, scale_z: float, scale_factor: float = 1.0) -> tuple:
    """
    Calculate print size in inches based on TTS scale.

    Args:
        scale_x: TTS scaleX value
        scale_z: TTS scaleZ value
        scale_factor: Conversion factor (TTS units to inches)

    Returns:
        (width_inches, height_inches)
    """
    width = scale_x * scale_factor
    height = scale_z * scale_factor
    return width, height


def draw_item_with_marks(c, item_image, x, y, width_pts, height_pts, label: str = "", number: int = None, no_labels: bool = False):
    """
    Draw an item on the canvas with crop marks and optional label.

    Args:
        c: ReportLab canvas
        item_image: PIL Image
        x, y: Position (bottom-left corner)
        width_pts, height_pts: Dimensions in points
        label: Label text
        number: Item number for identification
        no_labels: If True, skip drawing labels
    """
    # Draw the image
    img_reader = ImageReader(item_image)
    c.drawImage(img_reader, x, y, width=width_pts, height=height_pts, preserveAspectRatio=True, mask='auto')

    # Draw crop marks
    mark_length = 0.15 * inch
    mark_offset = 0.05 * inch

    c.setLineWidth(0.5)

    # Top-left
    c.line(x - mark_offset - mark_length, y + height_pts, x - mark_offset, y + height_pts)
    c.line(x, y + height_pts + mark_offset, x, y + height_pts + mark_offset + mark_length)

    # Top-right
    c.line(x + width_pts + mark_offset, y + height_pts, x + width_pts + mark_offset + mark_length, y + height_pts)
    c.line(x + width_pts, y + height_pts + mark_offset, x + width_pts, y + height_pts + mark_offset + mark_length)

    # Bottom-left
    c.line(x - mark_offset - mark_length, y, x - mark_offset, y)
    c.line(x, y - mark_offset, x, y - mark_offset - mark_length)

    # Bottom-right
    c.line(x + width_pts + mark_offset, y, x + width_pts + mark_offset + mark_length, y)
    c.line(x + width_pts, y - mark_offset, x + width_pts, y - mark_offset - mark_length)

    # Draw label and number (unless no_labels is True)
    if not no_labels and (label or number is not None):
        c.setFont("Helvetica", 8)
        label_text = f"#{number} - {label}" if number is not None else label
        c.drawString(x, y - 0.3 * inch, label_text[:60])


def pack_small_items(items, page_width, page_height, margin, item_spacing=0.2 * inch):
    """
    Pack small items onto pages using a simple row-based algorithm.

    Args:
        items: List of (item_info, width_pts, height_pts, item_image) tuples
        page_width, page_height: Page dimensions in points
        margin: Margin in points
        item_spacing: Spacing between items in points

    Returns:
        List of pages, where each page is a list of (item_info, width, height, image, x, y) tuples
    """
    available_width = page_width - (2 * margin)
    available_height = page_height - (2 * margin)

    pages = []
    current_page = []
    current_row = []
    current_row_width = 0
    current_row_height = 0
    current_y = margin + available_height  # Start from top

    for item_info, width_pts, height_pts, item_image in items:
        # Check if item fits in current row
        needed_width = width_pts + (item_spacing if current_row else 0)

        if current_row and current_row_width + needed_width > available_width:
            # Row is full, place it and start new row
            # Position items in current row
            x = margin
            y = current_y - current_row_height

            for row_item_info, row_width, row_height, row_image in current_row:
                current_page.append((row_item_info, row_width, row_height, row_image, x, y))
                x += row_width + item_spacing

            current_y = y - item_spacing
            current_row = []
            current_row_width = 0
            current_row_height = 0

        # Check if we need a new page
        if current_y - height_pts < margin:
            # Page is full
            if current_row:
                # Place remaining row items
                x = margin
                y = current_y - current_row_height
                for row_item_info, row_width, row_height, row_image in current_row:
                    current_page.append((row_item_info, row_width, row_height, row_image, x, y))
                    x += row_width + item_spacing

            pages.append(current_page)
            current_page = []
            current_row = []
            current_row_width = 0
            current_row_height = 0
            current_y = margin + available_height

        # Add item to current row
        current_row.append((item_info, width_pts, height_pts, item_image))
        current_row_width += width_pts + (item_spacing if current_row_width > 0 else 0)
        current_row_height = max(current_row_height, height_pts)

    # Place any remaining items
    if current_row:
        x = margin
        y = current_y - current_row_height
        for row_item_info, row_width, row_height, row_image in current_row:
            current_page.append((row_item_info, row_width, row_height, row_image, x, y))
            x += row_width + item_spacing

    if current_page:
        pages.append(current_page)

    return pages


def generate_tiles_pdf(
    items: list,
    output_file: Path,
    scale_factor: float = 1.0,
    max_size: float = 10.0,
    small_item_threshold: float = 4.0,
    margin: float = 0.5,
    no_labels: bool = False,
    no_grouping: bool = False
):
    """
    Generate a PDF with tiles, boards, and tokens.

    Small items are packed onto pages. Large items get one per page.
    Duplicate items can be grouped and counted, or printed individually.

    Args:
        items: List of tile/board/token info dicts
        output_file: Output PDF path
        scale_factor: TTS scale to inches conversion (default: 1.0)
        max_size: Maximum dimension in inches (default: 10.0)
        small_item_threshold: Items smaller than this are packed (default: 4.0)
        margin: Page margin in inches (default: 0.5)
        no_labels: If True, don't draw text labels (default: False)
        no_grouping: If True, print all duplicates (default: False)
    """
    if not items:
        print(f"No items to generate PDF")
        return

    page_width, page_height = letter
    margin_pts = margin * inch

    # Separate small and large items
    small_items = []
    large_items = []

    if no_grouping:
        # Don't group - process all items individually
        print(f"\nProcessing {len(items)} items (all instances, no grouping)...")

        for idx, item in enumerate(items, 1):
            local_image = item.get('local_image', '')
            if not local_image or not Path(local_image).exists():
                nickname = item.get('nickname', '(unnamed)')
                print(f"  Skipping #{idx} {nickname}: Image not found")
                continue

            # Calculate print size
            scale_x = item['scale_x']
            scale_z = item['scale_z']
            width_inches, height_inches = calculate_print_size(scale_x, scale_z, scale_factor)

            # Constrain to max_size
            if width_inches > max_size or height_inches > max_size:
                scale_down = max_size / max(width_inches, height_inches)
                width_inches *= scale_down
                height_inches *= scale_down

            width_pts = width_inches * inch
            height_pts = height_inches * inch

            # Load image
            try:
                item_image = Image.open(local_image)
            except Exception as e:
                print(f"  Error loading #{idx}: {e}")
                continue

            # Add item number and size to info
            item_with_info = item.copy()
            item_with_info['item_number'] = idx
            item_with_info['print_width'] = width_inches
            item_with_info['print_height'] = height_inches

            # Categorize by size
            max_dim = max(width_inches, height_inches)
            if max_dim < small_item_threshold:
                small_items.append((item_with_info, width_pts, height_pts, item_image))
            else:
                large_items.append((item_with_info, width_pts, height_pts, item_image))

    else:
        # Group identical items (same nickname + image + scale)
        from collections import defaultdict
        item_groups = defaultdict(list)

        for item in items:
            # Create a key for grouping
            key = (item['nickname'], item.get('image_url', ''), item['scale_x'], item['scale_z'])
            item_groups[key].append(item)

        print(f"\nProcessing {len(items)} items ({len(item_groups)} unique)...")

        for idx, ((nickname, image_url, scale_x, scale_z), group_items) in enumerate(item_groups.items(), 1):
            # Use first item from group as representative
            item = group_items[0]
            quantity = len(group_items)

            local_image = item.get('local_image', '')
            if not local_image or not Path(local_image).exists():
                print(f"  Skipping #{idx} {nickname or '(unnamed)'}: Image not found")
                continue

            # Calculate print size
            width_inches, height_inches = calculate_print_size(scale_x, scale_z, scale_factor)

            # Constrain to max_size
            if width_inches > max_size or height_inches > max_size:
                scale_down = max_size / max(width_inches, height_inches)
                width_inches *= scale_down
                height_inches *= scale_down

            width_pts = width_inches * inch
            height_pts = height_inches * inch

            # Load image
            try:
                item_image = Image.open(local_image)
            except Exception as e:
                print(f"  Error loading #{idx}: {e}")
                continue

            # Add item number, size, and quantity to info
            item_with_info = item.copy()
            item_with_info['item_number'] = idx
            item_with_info['print_width'] = width_inches
            item_with_info['print_height'] = height_inches
            item_with_info['quantity'] = quantity

            # Categorize by size
            max_dim = max(width_inches, height_inches)
            if max_dim < small_item_threshold:
                small_items.append((item_with_info, width_pts, height_pts, item_image))
            else:
                large_items.append((item_with_info, width_pts, height_pts, item_image))

    print(f"\n  Small items (< {small_item_threshold}\"): {len(small_items)}")
    print(f"  Large items (>= {small_item_threshold}\"): {len(large_items)}")

    if not small_items and not large_items:
        print("No valid items to generate PDF")
        return

    # Create PDF
    c = pdf_canvas.Canvas(str(output_file), pagesize=letter)
    total_pages = 0

    # Pack and draw small items
    if small_items:
        print(f"\nPacking {len(small_items)} small items...")
        packed_pages = pack_small_items(small_items, page_width, page_height, margin_pts)

        for page_num, page_items in enumerate(packed_pages, 1):
            print(f"  Page {page_num}: {len(page_items)} items")

            for item_info, width_pts, height_pts, item_image, x, y in page_items:
                nickname = item_info['nickname'] or '(unnamed)'
                number = item_info['item_number']
                size_str = f"{item_info['print_width']:.1f}\" × {item_info['print_height']:.1f}\""

                # Build label (only if not no_labels)
                if not no_grouping and 'quantity' in item_info:
                    quantity = item_info['quantity']
                    if quantity > 1:
                        label = f"{nickname} (×{quantity}) ({size_str})"
                    else:
                        label = f"{nickname} ({size_str})"
                else:
                    label = f"{nickname} ({size_str})"

                draw_item_with_marks(c, item_image, x, y, width_pts, height_pts, label, number, no_labels)

            c.showPage()
            total_pages += 1

    # Draw large items (one per page)
    if large_items:
        print(f"\nDrawing {len(large_items)} large items...")

        for item_info, width_pts, height_pts, item_image in large_items:
            # Center on page
            available_width = page_width - (2 * margin_pts)
            available_height = page_height - (2 * margin_pts)

            x = margin_pts + (available_width - width_pts) / 2
            y = margin_pts + (available_height - height_pts) / 2

            nickname = item_info['nickname'] or '(unnamed)'
            number = item_info['item_number']
            size_str = f"{item_info['print_width']:.1f}\" × {item_info['print_height']:.1f}\""

            # Build label (only if not no_labels)
            if not no_grouping and 'quantity' in item_info:
                quantity = item_info['quantity']
                if quantity > 1:
                    label = f"{nickname} (×{quantity}) ({size_str})"
                    print(f"  #{number} {nickname} (×{quantity}): {size_str}")
                else:
                    label = f"{nickname} ({size_str})"
                    print(f"  #{number} {nickname}: {size_str}")
            else:
                label = f"{nickname} ({size_str})"
                print(f"  #{number} {nickname}: {size_str}")

            draw_item_with_marks(c, item_image, x, y, width_pts, height_pts, label, number, no_labels)

            c.showPage()
            total_pages += 1

    c.save()

    if no_grouping:
        print(f"\n✓ Saved {output_file.name}: {total_pages} pages, {len(items)} items")
    else:
        total_unique = len(small_items) + len(large_items)
        total_instances = sum(item[0].get('quantity', 1) for item in small_items) + sum(item[0].get('quantity', 1) for item in large_items)

        print(f"\n✓ Saved {output_file.name}: {total_pages} pages")
        print(f"  {total_unique} unique items ({total_instances} total instances)")

        # Show quantity summary
        high_quantity = [(item[0], item[0].get('quantity', 1)) for item in small_items + large_items if item[0].get('quantity', 1) > 1]
        if high_quantity:
            print(f"\n  Items with multiple copies:")
            for item, qty in sorted(high_quantity, key=lambda x: x[1], reverse=True)[:10]:
                name = item['nickname'] or '(unnamed)'
                print(f"    {name}: ×{qty}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Generate PDF from TTS tiles, boards, and tokens')
    parser.add_argument('json_file', help='Path to TTS deserialized JSON file')
    parser.add_argument('-m', '--metadata', default='tile_metadata.json',
                        help='Path to tile_metadata.json (default: tile_metadata.json)')
    parser.add_argument('-o', '--output', default='tiles_and_boards.pdf',
                        help='Output PDF file (default: tiles_and_boards.pdf)')
    parser.add_argument('--scale-factor', type=float, default=None,
                        help='TTS scale units to inches conversion (default: auto-detect from cards)')
    parser.add_argument('--max-size', type=float, default=10.0,
                        help='Maximum dimension for any item in inches (default: 10.0)')
    parser.add_argument('--small-threshold', type=float, default=4.0,
                        help='Items smaller than this are packed together (default: 4.0 inches)')
    parser.add_argument('--tiles-only', action='store_true',
                        help='Generate PDF with tiles only')
    parser.add_argument('--boards-only', action='store_true',
                        help='Generate PDF with boards only')
    parser.add_argument('--tokens-only', action='store_true',
                        help='Generate PDF with tokens only')
    parser.add_argument('--no-labels', action='store_true',
                        help='Do not draw text labels on items')
    parser.add_argument('--group', action='store_true',
                        help='Group duplicate items (default: print all copies)')

    args = parser.parse_args()

    json_file = Path(args.json_file)
    metadata_file = Path(args.metadata)
    output_file = Path(args.output)

    if not metadata_file.exists():
        print(f"Error: Metadata file not found: {metadata_file}")
        print("Run tts-extract-tiles first to generate metadata")
        return 1

    # Determine scale factor
    if args.scale_factor is not None:
        scale_factor = args.scale_factor
        print(f"Using specified scale factor: {scale_factor:.2f}")
    else:
        # Auto-detect from cards in the JSON
        detected = auto_detect_scale_factor(json_file)
        if detected:
            scale_factor = detected
            print(f"Auto-detected scale factor: {scale_factor:.2f} (from card dimensions)")
        else:
            scale_factor = 1.0
            print(f"Could not auto-detect scale factor, using default: {scale_factor:.2f}")

    # Extract items
    tiles, boards, tokens = extract_items(metadata_file)

    print(f"Found {len(tiles)} tiles, {len(boards)} boards, and {len(tokens)} tokens")

    # Determine what to generate
    if args.tiles_only:
        items = tiles
        output_file = output_file.parent / 'tiles.pdf'
    elif args.boards_only:
        items = boards
        output_file = output_file.parent / 'boards.pdf'
    elif args.tokens_only:
        items = tokens
        output_file = output_file.parent / 'tokens.pdf'
    else:
        items = tiles + boards + tokens

    if not items:
        print("No items to generate")
        return 0

    # Generate PDF
    generate_tiles_pdf(
        items,
        output_file,
        scale_factor=scale_factor,
        max_size=args.max_size,
        small_item_threshold=args.small_threshold,
        no_labels=args.no_labels,
        no_grouping=not args.group
    )

    return 0


if __name__ == '__main__':
    sys.exit(main())
