#!/usr/bin/env python3
"""
Generate PDFs with tiles, boards, and tokens from a TTS JSON file.

Uses correct TTS scaling formulas:
  - BASE_WIDTH = 1.300 inches (for tiles/boards/tokens)
  - BASE_HEIGHT = 1.318 inches
  - Physical size = BASE × Transform.scale × aspect_ratio

Supports multi-page printing for large items with 0.25" white borders.
"""

import json
import math
from pathlib import Path
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader
import sys


# TTS BASE units (derived from real-world measurements)
BASE_WIDTH = 1.300  # inches
BASE_HEIGHT = 1.318  # inches


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


def calculate_print_size_tts(scale_x: float, scale_z: float, image_width: int, image_height: int) -> tuple:
    """
    Calculate actual print size using TTS scaling formula.

    Formula:
        width_inches = BASE_WIDTH × scaleX × (image_width / image_height)
        height_inches = BASE_HEIGHT × scaleZ

    Args:
        scale_x: TTS scaleX value
        scale_z: TTS scaleZ value
        image_width: Image width in pixels
        image_height: Image height in pixels

    Returns:
        (width_inches, height_inches)
    """
    aspect_ratio = image_width / image_height if image_height > 0 else 1.0

    width_inches = BASE_WIDTH * scale_x * aspect_ratio
    height_inches = BASE_HEIGHT * scale_z

    return width_inches, height_inches


def split_large_item(item_width_inches, item_height_inches, page_margin=0.25):
    """
    Calculate how to split a large item across multiple pages.

    Args:
        item_width_inches: Item width in inches
        item_height_inches: Item height in inches
        page_margin: Minimum margin in inches (0.25" white border)

    Returns:
        (cols, rows, tile_width, tile_height) or None if fits on one page
    """
    page_width, page_height = letter
    page_width_inches = page_width / inch
    page_height_inches = page_height / inch

    # Usable area per page (with margins)
    usable_width = page_width_inches - (2 * page_margin)
    usable_height = page_height_inches - (2 * page_margin)

    # Check if it fits on one page
    if item_width_inches <= usable_width and item_height_inches <= usable_height:
        return None

    # Calculate number of pages needed
    cols = math.ceil(item_width_inches / usable_width)
    rows = math.ceil(item_height_inches / usable_height)

    # Calculate actual tile size (may be smaller than usable area)
    tile_width = item_width_inches / cols
    tile_height = item_height_inches / rows

    return cols, rows, tile_width, tile_height


def draw_item_tile(c, item_image, tile_col, tile_row, cols, rows,
                   tile_width_inches, tile_height_inches,
                   total_width_inches, total_height_inches,
                   page_margin=0.25, label="", page_num=None):
    """
    Draw one tile of a multi-page item.

    Args:
        c: ReportLab canvas
        item_image: PIL Image (full image)
        tile_col: Column index (0-based)
        tile_row: Row index (0-based)
        cols: Total columns
        rows: Total rows
        tile_width_inches: Width of this tile
        tile_height_inches: Height of this tile
        total_width_inches: Total item width
        total_height_inches: Total item height
        page_margin: Margin in inches
        label: Item label
        page_num: Page number in sequence
    """
    page_width, page_height = letter
    margin_pts = page_margin * inch

    # Calculate which part of the image to extract
    img_width, img_height = item_image.size

    # Source rectangle in pixels
    src_x = int((tile_col / cols) * img_width)
    src_y = int((tile_row / rows) * img_height)
    src_w = int((1.0 / cols) * img_width)
    src_h = int((1.0 / rows) * img_height)

    # Crop the tile
    tile_image = item_image.crop((src_x, src_y, src_x + src_w, src_y + src_h))

    # Position on page (centered)
    tile_width_pts = tile_width_inches * inch
    tile_height_pts = tile_height_inches * inch

    x = margin_pts
    y = page_height - margin_pts - tile_height_pts

    # Draw the tile
    img_reader = ImageReader(tile_image)
    c.drawImage(img_reader, x, y, width=tile_width_pts, height=tile_height_pts,
                preserveAspectRatio=True, mask='auto')

    # Draw crop marks at corners
    mark_length = 0.15 * inch
    mark_offset = 0.05 * inch
    c.setLineWidth(0.5)
    c.setStrokeColorRGB(0, 0, 0)

    # Top-left
    c.line(x - mark_offset - mark_length, y + tile_height_pts, x - mark_offset, y + tile_height_pts)
    c.line(x, y + tile_height_pts + mark_offset, x, y + tile_height_pts + mark_offset + mark_length)

    # Top-right
    c.line(x + tile_width_pts + mark_offset, y + tile_height_pts,
           x + tile_width_pts + mark_offset + mark_length, y + tile_height_pts)
    c.line(x + tile_width_pts, y + tile_height_pts + mark_offset,
           x + tile_width_pts, y + tile_height_pts + mark_offset + mark_length)

    # Bottom-left
    c.line(x - mark_offset - mark_length, y, x - mark_offset, y)
    c.line(x, y - mark_offset, x, y - mark_offset - mark_length)

    # Bottom-right
    c.line(x + tile_width_pts + mark_offset, y, x + tile_width_pts + mark_offset + mark_length, y)
    c.line(x + tile_width_pts, y - mark_offset, x + tile_width_pts, y - mark_offset - mark_length)

    # Draw registration marks at midpoints (for alignment)
    if rows > 1:
        # Top and bottom midpoints
        mid_x = x + tile_width_pts / 2
        c.line(mid_x - mark_length/2, y + tile_height_pts + mark_offset,
               mid_x + mark_length/2, y + tile_height_pts + mark_offset)
        c.line(mid_x - mark_length/2, y - mark_offset,
               mid_x + mark_length/2, y - mark_offset)

    if cols > 1:
        # Left and right midpoints
        mid_y = y + tile_height_pts / 2
        c.line(x - mark_offset, mid_y - mark_length/2,
               x - mark_offset, mid_y + mark_length/2)
        c.line(x + tile_width_pts + mark_offset, mid_y - mark_length/2,
               x + tile_width_pts + mark_offset, mid_y + mark_length/2)

    # Draw label
    c.setFont("Helvetica", 8)
    if page_num is not None:
        label_text = f"{label} - Page {page_num}/{cols*rows} (Row {tile_row+1}/{rows}, Col {tile_col+1}/{cols})"
    else:
        label_text = label

    c.drawString(x, y - 0.3 * inch, label_text[:80])

    # Add assembly info
    if cols > 1 or rows > 1:
        c.setFont("Helvetica", 7)
        c.drawString(x, y - 0.5 * inch,
                    f"Total size: {total_width_inches:.2f}\" × {total_height_inches:.2f}\" - " +
                    f"Align registration marks to assemble")


def draw_item_with_marks(c, item_image, x, y, width_pts, height_pts,
                        label: str = "", number: int = None, no_labels: bool = False):
    """
    Draw an item on the canvas with crop marks and optional label.
    (For items that fit on one page)
    """
    # Draw the image
    img_reader = ImageReader(item_image)
    c.drawImage(img_reader, x, y, width=width_pts, height=height_pts,
                preserveAspectRatio=True, mask='auto')

    # Draw crop marks
    mark_length = 0.15 * inch
    mark_offset = 0.05 * inch

    c.setLineWidth(0.5)
    c.setStrokeColorRGB(0, 0, 0)

    # Top-left
    c.line(x - mark_offset - mark_length, y + height_pts, x - mark_offset, y + height_pts)
    c.line(x, y + height_pts + mark_offset, x, y + height_pts + mark_offset + mark_length)

    # Top-right
    c.line(x + width_pts + mark_offset, y + height_pts,
           x + width_pts + mark_offset + mark_length, y + height_pts)
    c.line(x + width_pts, y + height_pts + mark_offset,
           x + width_pts, y + height_pts + mark_offset + mark_length)

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
    small_item_threshold: float = 4.0,
    margin: float = 0.5,
    no_labels: bool = False,
    no_grouping: bool = False,
    multipage_margin: float = 0.25
):
    """
    Generate a PDF with tiles, boards, and tokens using correct TTS scaling.

    Small items are packed onto pages. Large items get one per page or split across
    multiple pages if they exceed letter size.

    Args:
        items: List of tile/board/token info dicts
        output_file: Output PDF path
        small_item_threshold: Items smaller than this are packed (default: 4.0 inches)
        margin: Page margin for packed items in inches (default: 0.5)
        no_labels: If True, don't draw text labels (default: False)
        no_grouping: If True, print all duplicates (default: False)
        multipage_margin: Margin for multi-page items (default: 0.25 inches)
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
        print(f"\nProcessing {len(items)} items (all instances, no grouping)...")

        for idx, item in enumerate(items, 1):
            local_image = item.get('local_image', '')
            if not local_image or not Path(local_image).exists():
                nickname = item.get('nickname', '(unnamed)')
                print(f"  Skipping #{idx} {nickname}: Image not found")
                continue

            # Calculate TRUE print size using TTS formula
            scale_x = item['scale_x']
            scale_z = item['scale_z']

            # Load image to get dimensions
            try:
                img = Image.open(local_image)
                img_width, img_height = img.size
            except Exception as e:
                print(f"  Error loading #{idx}: {e}")
                continue

            # Use TTS scaling formula
            width_inches, height_inches = calculate_print_size_tts(
                scale_x, scale_z, img_width, img_height
            )

            width_pts = width_inches * inch
            height_pts = height_inches * inch

            # Add item info
            item_with_info = item.copy()
            item_with_info['item_number'] = idx
            item_with_info['print_width'] = width_inches
            item_with_info['print_height'] = height_inches

            # Categorize by size
            max_dim = max(width_inches, height_inches)
            if max_dim < small_item_threshold:
                small_items.append((item_with_info, width_pts, height_pts, img))
            else:
                large_items.append((item_with_info, width_pts, height_pts, img))

    else:
        # Group identical items
        from collections import defaultdict
        item_groups = defaultdict(list)

        for item in items:
            key = (item['nickname'], item.get('image_url', ''), item['scale_x'], item['scale_z'])
            item_groups[key].append(item)

        print(f"\nProcessing {len(items)} items ({len(item_groups)} unique)...")

        for idx, ((nickname, image_url, scale_x, scale_z), group_items) in enumerate(item_groups.items(), 1):
            item = group_items[0]
            quantity = len(group_items)

            local_image = item.get('local_image', '')
            if not local_image or not Path(local_image).exists():
                print(f"  Skipping #{idx} {nickname or '(unnamed)'}: Image not found")
                continue

            # Load image
            try:
                img = Image.open(local_image)
                img_width, img_height = img.size
            except Exception as e:
                print(f"  Error loading #{idx}: {e}")
                continue

            # Calculate TRUE print size using TTS formula
            width_inches, height_inches = calculate_print_size_tts(
                scale_x, scale_z, img_width, img_height
            )

            width_pts = width_inches * inch
            height_pts = height_inches * inch

            # Add item info
            item_with_info = item.copy()
            item_with_info['item_number'] = idx
            item_with_info['print_width'] = width_inches
            item_with_info['print_height'] = height_inches
            item_with_info['quantity'] = quantity

            # Categorize by size
            max_dim = max(width_inches, height_inches)
            if max_dim < small_item_threshold:
                small_items.append((item_with_info, width_pts, height_pts, img))
            else:
                large_items.append((item_with_info, width_pts, height_pts, img))

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
                size_str = f"{item_info['print_width']:.2f}\" × {item_info['print_height']:.2f}\""

                # Build label
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

    # Draw large items (one per page or split across pages)
    if large_items:
        print(f"\nDrawing {len(large_items)} large items...")

        for item_info, width_pts, height_pts, item_image in large_items:
            width_inches = item_info['print_width']
            height_inches = item_info['print_height']
            nickname = item_info['nickname'] or '(unnamed)'
            number = item_info['item_number']
            size_str = f"{width_inches:.2f}\" × {height_inches:.2f}\""

            # Build label
            if not no_grouping and 'quantity' in item_info:
                quantity = item_info['quantity']
                if quantity > 1:
                    label = f"#{number} {nickname} (×{quantity}) ({size_str})"
                else:
                    label = f"#{number} {nickname} ({size_str})"
            else:
                label = f"#{number} {nickname} ({size_str})"

            # Check if it needs to be split
            split_info = split_large_item(width_inches, height_inches, multipage_margin)

            if split_info is None:
                # Fits on one page - center it
                print(f"  #{number} {nickname}: {size_str} (1 page)")

                available_width = page_width - (2 * margin_pts)
                available_height = page_height - (2 * margin_pts)

                x = margin_pts + (available_width - width_pts) / 2
                y = margin_pts + (available_height - height_pts) / 2

                draw_item_with_marks(c, item_image, x, y, width_pts, height_pts, label, number, no_labels)
                c.showPage()
                total_pages += 1
            else:
                # Split across multiple pages
                cols, rows, tile_width, tile_height = split_info
                num_tiles = cols * rows
                print(f"  #{number} {nickname}: {size_str} ({num_tiles} pages: {cols}×{rows} grid)")

                tile_num = 1
                for row in range(rows):
                    for col in range(cols):
                        draw_item_tile(
                            c, item_image,
                            col, row, cols, rows,
                            tile_width, tile_height,
                            width_inches, height_inches,
                            multipage_margin,
                            label, tile_num
                        )
                        c.showPage()
                        total_pages += 1
                        tile_num += 1

    c.save()

    if no_grouping:
        print(f"\n✓ Saved {output_file.name}: {total_pages} pages, {len(items)} items")
    else:
        total_unique = len(small_items) + len(large_items)
        total_instances = sum(item[0].get('quantity', 1) for item in small_items) + \
                         sum(item[0].get('quantity', 1) for item in large_items)

        print(f"\n✓ Saved {output_file.name}: {total_pages} pages")
        print(f"  {total_unique} unique items ({total_instances} total instances)")

        # Show quantity summary
        high_quantity = [(item[0], item[0].get('quantity', 1)) for item in small_items + large_items
                        if item[0].get('quantity', 1) > 1]
        if high_quantity:
            print(f"\n  Items with multiple copies:")
            for item, qty in sorted(high_quantity, key=lambda x: x[1], reverse=True)[:10]:
                name = item['nickname'] or '(unnamed)'
                print(f"    {name}: ×{qty}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate PDF from TTS tiles, boards, and tokens with correct TTS scaling'
    )
    parser.add_argument('json_file', help='Path to TTS deserialized JSON file')
    parser.add_argument('-m', '--metadata', default='tile_metadata.json',
                        help='Path to tile_metadata.json (default: tile_metadata.json)')
    parser.add_argument('-o', '--output', default='tiles_and_boards.pdf',
                        help='Output PDF file (default: tiles_and_boards.pdf)')
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
    parser.add_argument('--no-grouping', action='store_true',
                        help='Print all duplicate items (do not group)')
    parser.add_argument('--multipage-margin', type=float, default=0.25,
                        help='White border margin for multi-page items (default: 0.25 inches)')

    args = parser.parse_args()

    json_file = Path(args.json_file)
    metadata_file = Path(args.metadata)
    output_file = Path(args.output)

    if not metadata_file.exists():
        print(f"Error: Metadata file not found: {metadata_file}")
        print("Run extract_tiles.py first to generate metadata")
        return 1

    # Extract items
    tiles, boards, tokens = extract_items(metadata_file)

    print(f"Found {len(tiles)} tiles, {len(boards)} boards, and {len(tokens)} tokens")
    print(f"Using TTS scaling: BASE = {BASE_WIDTH:.3f}\" × {BASE_HEIGHT:.3f}\"")

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
        small_item_threshold=args.small_threshold,
        no_labels=args.no_labels,
        no_grouping=args.no_grouping,
        multipage_margin=args.multipage_margin
    )

    return 0


if __name__ == '__main__':
    sys.exit(main())
