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
import math
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


def draw_hex_outline(c, cx, cy, hex_w, hex_h, fill_color=None):
    """
    Draw a flat-top hexagon outline centered at (cx, cy).

    For flat-top orientation:
      - hex_w = width (vertex to vertex, horizontal)
      - hex_h = height (flat side to flat side, vertical)

    Vertices (flat-top, starting from right vertex, clockwise):
      right:       (w/2, 0)
      lower-right: (w/4, -h/2)
      lower-left:  (-w/4, -h/2)
      left:        (-w/2, 0)
      upper-left:  (-w/4, h/2)
      upper-right: (w/4, h/2)

    Args:
        fill_color: Optional (r, g, b) tuple to fill the hex. Values 0.0-1.0.
    """
    hw = hex_w / 2
    hh = hex_h / 2
    qw = hex_w / 4

    vertices = [
        (cx + hw, cy),           # right
        (cx + qw, cy - hh),     # lower-right
        (cx - qw, cy - hh),     # lower-left
        (cx - hw, cy),           # left
        (cx - qw, cy + hh),     # upper-left
        (cx + qw, cy + hh),     # upper-right
    ]

    p = c.beginPath()
    p.moveTo(*vertices[0])
    for vx, vy in vertices[1:]:
        p.lineTo(vx, vy)
    p.close()

    c.setStrokeColorRGB(0.4, 0.4, 0.4)
    c.setLineWidth(0.5)
    if fill_color:
        c.setFillColorRGB(*fill_color)
        c.drawPath(p, stroke=1, fill=1)
    else:
        c.drawPath(p, stroke=1, fill=0)


def pack_hex_grid_items(items, page_width, page_height, margin, hex_gap=0.02 * inch):
    """
    Pack hex-shaped items onto pages in a flat-top honeycomb grid.

    For flat-top hexagons:
      - hex_w = tile width (vertex to vertex, horizontal)
      - hex_h = tile height (flat side to flat side, vertical)
      - Horizontal step between columns: hex_w * 3/4 + gap
      - Vertical step between rows: hex_h + gap
      - Odd columns offset vertically by (hex_h + gap) / 2

    Args:
        items: List of (item_info, width_pts, height_pts, item_image) tuples
            All items should be roughly the same size (uniform hex tiles).
        page_width, page_height: Page dimensions in points
        margin: Margin in points
        hex_gap: Gap between hexes in points

    Returns:
        List of pages, where each page is a list of
        (item_info, width, height, image, cx, cy) tuples
        where cx, cy are the CENTER of the hex cell.
    """
    if not items:
        return []

    # Use the first item's dimensions as the uniform hex size
    _, tile_w, tile_h, _ = items[0]

    hex_w = tile_w
    hex_h = tile_h

    available_width = page_width - (2 * margin)
    available_height = page_height - (2 * margin)

    # Grid spacing for flat-top hex
    col_step = hex_w * 0.75 + hex_gap
    row_step = hex_h + hex_gap

    # Number of columns that fit
    cols = int((available_width - hex_w) / col_step) + 1

    # Number of rows that fit
    # Odd columns are offset down by row_step/2, so they need extra room
    rows = int((available_height - hex_h) / row_step) + 1
    # Check if odd-column offset still fits
    odd_col_last_y = margin + hex_h / 2 + row_step / 2 + (rows - 1) * row_step
    if odd_col_last_y + hex_h / 2 > page_height - margin:
        rows_odd = rows - 1
    else:
        rows_odd = rows

    pages = []
    item_idx = 0

    while item_idx < len(items):
        current_page = []

        for col in range(cols):
            is_odd_col = col % 2 == 1
            num_rows = rows_odd if is_odd_col else rows
            y_offset = row_step / 2 if is_odd_col else 0

            for row in range(num_rows):
                if item_idx >= len(items):
                    break

                cx = margin + hex_w / 2 + col * col_step
                cy = page_height - margin - hex_h / 2 - row * row_step - y_offset

                item_info, w, h, img = items[item_idx]
                current_page.append((item_info, w, h, img, cx, cy))
                item_idx += 1

            if item_idx >= len(items):
                break

        if current_page:
            pages.append(current_page)

    return pages


def pack_hex_strip_items(items, page_width, page_height, margin):
    """
    Pack flat-top hex tiles in rows where pointy edges touch horizontally.

    Layout: each row places hexes so the right vertex of one hex touches the
    left vertex of the next. Odd rows are offset right by half a hex width.
    Vertical row spacing is hex_h * 3/4, so diagonal edges of adjacent rows
    nest together. This maximizes long straight diagonal cuts across the sheet
    and leaves small triangular gaps between three adjacent hexes.

    Geometry (flat-top hex, width W vertex-to-vertex, height H flat-to-flat):
      - Horizontal step in a row: W (vertex tip to vertex tip, touching)
      - Odd row horizontal offset: W / 2
      - Vertical step between rows: H * 3/4

    Args:
        items: List of (item_info, width_pts, height_pts, item_image) tuples
        page_width, page_height: Page dimensions in points
        margin: Margin in points

    Returns:
        List of pages, each a list of (item_info, w, h, image, cx, cy) tuples.
    """
    if not items:
        return []

    _, tile_w, tile_h, _ = items[0]
    hex_w = tile_w
    hex_h = tile_h

    available_width = page_width - (2 * margin)
    available_height = page_height - (2 * margin)

    # Horizontal step: full hex width (pointy tips touching)
    col_step = hex_w
    # Vertical step: full hex height (rows don't nest)
    row_step = hex_h

    # Columns per row (even rows start at margin + hex_w/2)
    cols_even = int((available_width - hex_w) / col_step) + 1
    # Odd rows are offset by hex_w/2, so the last hex may not fit
    cols_odd = cols_even
    odd_last_x = margin + hex_w / 2 + col_step / 2 + (cols_odd - 1) * col_step
    if odd_last_x + hex_w / 2 > page_width - margin:
        cols_odd = cols_odd - 1

    # Rows that fit
    rows = int((available_height - hex_h) / row_step) + 1

    pages = []
    item_idx = 0

    while item_idx < len(items):
        current_page = []

        for row in range(rows):
            is_odd = row % 2 == 1
            num_cols = cols_odd if is_odd else cols_even
            x_offset = col_step / 2 if is_odd else 0

            for col in range(num_cols):
                if item_idx >= len(items):
                    break

                cx = margin + hex_w / 2 + col * col_step + x_offset
                cy = page_height - margin - hex_h / 2 - row * row_step

                item_info, w, h, img = items[item_idx]
                current_page.append((item_info, w, h, img, cx, cy))
                item_idx += 1

            if item_idx >= len(items):
                break

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
    no_grouping: bool = False,
    hex_grid: bool = False,
    hex_strip: bool = False,
    hex_include: list = None
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
        hex_grid: If True, arrange hex tiles in honeycomb grid (default: False)
        hex_strip: If True, arrange hex tiles with pointy edges touching horizontally (default: False)
        hex_include: List of nickname patterns to also include in hex grid with clay red fill
    """
    if not items:
        print(f"No items to generate PDF")
        return

    page_width, page_height = letter
    margin_pts = margin * inch

    # Available area in inches for portrait and landscape orientations
    avail_portrait_w = (page_width / inch) - (2 * margin)    # 7.5" on letter
    avail_portrait_h = (page_height / inch) - (2 * margin)   # 10.0" on letter
    avail_landscape_w = avail_portrait_h                       # 10.0"
    avail_landscape_h = avail_portrait_w                       # 7.5"

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

            # Determine if this large item should use landscape page orientation
            # based on the actual image aspect ratio
            img_w, img_h = item_image.size
            use_landscape = img_w > img_h

            # For large items, use the image's native aspect ratio instead of
            # the TTS square scale (which stretches the image). Then fit to page.
            max_dim = max(width_inches, height_inches)
            if max_dim >= small_item_threshold and img_w != img_h:
                img_aspect = img_w / img_h
                # Recompute dimensions preserving image aspect ratio
                # Use the larger TTS dimension as the reference size
                if img_aspect >= 1.0:
                    # Landscape image: width is the larger dimension
                    width_inches = max_dim
                    height_inches = max_dim / img_aspect
                else:
                    # Portrait image: height is the larger dimension
                    height_inches = max_dim
                    width_inches = max_dim * img_aspect

            # For large items, constrain to the available page area
            max_dim = max(width_inches, height_inches)
            if max_dim >= small_item_threshold:
                if use_landscape:
                    avail_w, avail_h = avail_landscape_w, avail_landscape_h
                else:
                    avail_w, avail_h = avail_portrait_w, avail_portrait_h
                if width_inches > avail_w or height_inches > avail_h:
                    scale_down = min(avail_w / width_inches, avail_h / height_inches)
                    width_inches *= scale_down
                    height_inches *= scale_down
                    width_pts = width_inches * inch
                    height_pts = height_inches * inch

            # Add item number and size to info
            item_with_info = item.copy()
            item_with_info['item_number'] = idx
            item_with_info['print_width'] = width_inches
            item_with_info['print_height'] = height_inches
            item_with_info['use_landscape'] = use_landscape

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

            # Determine if this large item should use landscape page orientation
            img_w, img_h = item_image.size
            use_landscape = img_w > img_h

            # For large items, use the image's native aspect ratio instead of
            # the TTS square scale (which stretches the image). Then fit to page.
            max_dim = max(width_inches, height_inches)
            if max_dim >= small_item_threshold and img_w != img_h:
                img_aspect = img_w / img_h
                if img_aspect >= 1.0:
                    width_inches = max_dim
                    height_inches = max_dim / img_aspect
                else:
                    height_inches = max_dim
                    width_inches = max_dim * img_aspect

            # For large items, constrain to the available page area
            max_dim = max(width_inches, height_inches)
            if max_dim >= small_item_threshold:
                if use_landscape:
                    avail_w, avail_h = avail_landscape_w, avail_landscape_h
                else:
                    avail_w, avail_h = avail_portrait_w, avail_portrait_h
                if width_inches > avail_w or height_inches > avail_h:
                    scale_down = min(avail_w / width_inches, avail_h / height_inches)
                    width_inches *= scale_down
                    height_inches *= scale_down
                    width_pts = width_inches * inch
                    height_pts = height_inches * inch

            # Add item number, size, and quantity to info
            item_with_info = item.copy()
            item_with_info['item_number'] = idx
            item_with_info['print_width'] = width_inches
            item_with_info['print_height'] = height_inches
            item_with_info['quantity'] = quantity
            item_with_info['use_landscape'] = use_landscape

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
        # When hex_grid or hex_strip is enabled, separate hex tiles from non-hex items
        if hex_grid or hex_strip:
            hex_items = []       # (item_info, w, h, img, fill_color) tuples
            non_hex_items = []
            hex_ref_w = None     # reference hex cell width in pts
            hex_ref_h = None     # reference hex cell height in pts
            hex_ref_size = None  # reference image pixel size

            # First pass: find hex tiles (square RGBA images)
            pending_non_hex = []
            for item_tuple in small_items:
                img = item_tuple[3]
                img_w, img_h = img.size
                is_square = abs(img_w - img_h) <= 2  # allow 2px tolerance
                is_rgba = img.mode == 'RGBA'
                if is_square and is_rgba:
                    if hex_ref_w is None:
                        hex_ref_w = item_tuple[1]
                        hex_ref_h = item_tuple[2]
                        hex_ref_size = img.size
                    hex_items.append((*item_tuple, None))  # no fill color
                else:
                    pending_non_hex.append(item_tuple)

            # Second pass: check non-hex items against --hex-include patterns
            # to include them in the hex grid with a colored hex background
            CLAY_RED = (0.55, 0.22, 0.12)  # earthen dark clay red
            include_patterns = [p.lower() for p in (hex_include or [])]
            for item_tuple in pending_non_hex:
                item_info = item_tuple[0]
                nickname = item_info.get('nickname', '').lower()
                if hex_ref_size and include_patterns and any(p in nickname for p in include_patterns):
                    hex_items.append((*item_tuple, CLAY_RED))
                else:
                    non_hex_items.append(item_tuple)

            # Normalize hex tile images: crop to alpha bbox and resize to
            # uniform dimensions so tiles with extra transparent padding
            # fill the grid cell the same as other tiles.
            if hex_items and hex_ref_size:
                normalized = []
                for item_info, w, h, img, fill_color in hex_items:
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    alpha_bbox = img.split()[3].getbbox()
                    if alpha_bbox:
                        img = img.crop(alpha_bbox)
                    # Resize to fit within the hex cell, preserving aspect ratio
                    img_w, img_h = img.size
                    if img_w != hex_ref_size[0] or img_h != hex_ref_size[1]:
                        # Scale to fit within hex ref size preserving aspect
                        scale = min(hex_ref_size[0] / img_w, hex_ref_size[1] / img_h)
                        new_w = int(img_w * scale)
                        new_h = int(img_h * scale)
                        img = img.resize((new_w, new_h), Image.LANCZOS)
                        # Paste centered onto a transparent canvas of ref size
                        canvas_img = Image.new('RGBA', hex_ref_size, (0, 0, 0, 0))
                        paste_x = (hex_ref_size[0] - new_w) // 2
                        paste_y = (hex_ref_size[1] - new_h) // 2
                        canvas_img.paste(img, (paste_x, paste_y), img)
                        img = canvas_img
                    normalized.append((item_info, hex_ref_w, hex_ref_h, img, fill_color))
                hex_items = normalized

            if hex_items:
                if hex_strip:
                    mode_label = "hex strip (pointy edges touching)"
                    # pack_hex_strip_items expects (info, w, h, img) tuples
                    pack_input = [(info, w, h, img) for info, w, h, img, _ in hex_items]
                    hex_pages = pack_hex_strip_items(pack_input, page_width, page_height, margin_pts)
                else:
                    mode_label = "honeycomb grid"
                    pack_input = [(info, w, h, img) for info, w, h, img, _ in hex_items]
                    hex_pages = pack_hex_grid_items(pack_input, page_width, page_height, margin_pts)

                # Build a lookup from id(item_info) to fill_color
                fill_colors = {}
                for item_info, w, h, img, fill_color in hex_items:
                    fill_colors[id(item_info)] = fill_color

                print(f"\nPacking {len(hex_items)} hex tiles in {mode_label}...")

                for page_num, page_items in enumerate(hex_pages, 1):
                    print(f"  Page {page_num}: {len(page_items)} hex tiles")

                    # Draw hex outlines first (behind images)
                    for item_info, width_pts, height_pts, item_image, cx, cy in page_items:
                        fill = fill_colors.get(id(item_info))
                        draw_hex_outline(c, cx, cy, width_pts, height_pts, fill_color=fill)

                    # Draw tile images on top (no preserveAspectRatio so all
                    # tiles fill the same cell size even if alpha bbox varies)
                    for item_info, width_pts, height_pts, item_image, cx, cy in page_items:
                        img_reader = ImageReader(item_image)
                        x = cx - width_pts / 2
                        y = cy - height_pts / 2
                        c.drawImage(img_reader, x, y, width=width_pts, height=height_pts,
                                    mask='auto')

                    c.showPage()
                    total_pages += 1

            # Pack remaining non-hex items with standard rectangular packing
            if non_hex_items:
                print(f"\nPacking {len(non_hex_items)} non-hex small items...")
                packed_pages = pack_small_items(non_hex_items, page_width, page_height, margin_pts)

                for page_num, page_items in enumerate(packed_pages, 1):
                    print(f"  Page {page_num}: {len(page_items)} items")

                    for item_info, width_pts, height_pts, item_image, x, y in page_items:
                        nickname = item_info['nickname'] or '(unnamed)'
                        number = item_info['item_number']
                        size_str = f"{item_info['print_width']:.1f}\" × {item_info['print_height']:.1f}\""

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
        else:
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
            use_landscape = item_info.get('use_landscape', False)

            # Set page orientation
            if use_landscape:
                cur_page_w, cur_page_h = page_height, page_width  # swap for landscape
                c.setPageSize((cur_page_w, cur_page_h))
            else:
                cur_page_w, cur_page_h = page_width, page_height
                c.setPageSize((cur_page_w, cur_page_h))

            # Center on page
            available_width = cur_page_w - (2 * margin_pts)
            available_height = cur_page_h - (2 * margin_pts)

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
    parser.add_argument('--hex-grid', action='store_true',
                        help='Arrange hex tiles in honeycomb grid with hex outlines')
    parser.add_argument('--hex-strip', action='store_true',
                        help='Arrange hex tiles with pointy edges touching horizontally, rows offset by half a tile')
    parser.add_argument('--hex-include', nargs='+', metavar='PATTERN',
                        help='Include tokens matching these nickname patterns in the hex grid (case-insensitive substring match, e.g. --hex-include Moai)')

    args = parser.parse_args()

    json_file = Path(args.json_file).resolve()
    # Default metadata and output paths relative to the .deserialized/ dir (parent of Workshop/)
    target_dir = json_file.parent.parent
    metadata_file = Path(args.metadata)
    if args.metadata == 'tile_metadata.json' and not metadata_file.is_absolute():
        metadata_file = target_dir / metadata_file
    output_file = Path(args.output)
    if args.output == 'tiles_and_boards.pdf' and not output_file.is_absolute():
        output_file = target_dir / output_file

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
        no_grouping=not args.group,
        hex_grid=args.hex_grid,
        hex_strip=args.hex_strip,
        hex_include=args.hex_include
    )

    return 0


if __name__ == '__main__':
    sys.exit(main())
