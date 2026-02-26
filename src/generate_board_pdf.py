#!/usr/bin/env python3
"""
Generate a multi-page PDF from a board image for physical assembly.

Takes a board image, determines its physical size (via explicit dimensions
or DPI-based calculation), and splits it across multiple letter-sized pages
with margins, crop marks, and registration marks for assembly.
"""

import argparse
import math
import sys
from pathlib import Path

from PIL import Image
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader


def calculate_board_size(img_width_px, img_height_px, width=None, height=None, dpi=125):
    """
    Determine the physical size of the board in inches.

    Priority:
      1. Both --width and --height given: use as-is
      2. Only --width: derive height from aspect ratio
      3. Only --height: derive width from aspect ratio
      4. Neither: derive from image pixels / DPI

    Returns:
        (width_inches, height_inches)
    """
    aspect = img_width_px / img_height_px if img_height_px > 0 else 1.0

    if width is not None and height is not None:
        return width, height
    elif width is not None:
        return width, width / aspect
    elif height is not None:
        return height * aspect, height
    else:
        return img_width_px / dpi, img_height_px / dpi


def split_board(board_width, board_height, page_size, margin, overlap):
    """
    Calculate how to split a board across multiple pages.

    Args:
        board_width: Board width in inches
        board_height: Board height in inches
        page_size: (page_width_pts, page_height_pts) tuple
        margin: Margin in inches
        overlap: Overlap between adjacent pages in inches

    Returns:
        (cols, rows, usable_width, usable_height)
    """
    page_w_in = page_size[0] / inch
    page_h_in = page_size[1] / inch

    usable_w = page_w_in - 2 * margin
    usable_h = page_h_in - 2 * margin

    # With overlap, each page after the first covers (usable - overlap) of new content
    if board_width <= usable_w:
        cols = 1
    else:
        cols = 1 + math.ceil((board_width - usable_w) / (usable_w - overlap))

    if board_height <= usable_h:
        rows = 1
    else:
        rows = 1 + math.ceil((board_height - usable_h) / (usable_h - overlap))

    return cols, rows, usable_w, usable_h


def draw_crop_marks(c, x, y, w_pts, h_pts):
    """Draw crop marks at the four corners of the image area."""
    mark_length = 0.15 * inch
    mark_offset = 0.05 * inch
    c.setLineWidth(0.5)
    c.setStrokeColorRGB(0, 0, 0)

    # Top-left
    c.line(x - mark_offset - mark_length, y + h_pts, x - mark_offset, y + h_pts)
    c.line(x, y + h_pts + mark_offset, x, y + h_pts + mark_offset + mark_length)

    # Top-right
    c.line(x + w_pts + mark_offset, y + h_pts,
           x + w_pts + mark_offset + mark_length, y + h_pts)
    c.line(x + w_pts, y + h_pts + mark_offset,
           x + w_pts, y + h_pts + mark_offset + mark_length)

    # Bottom-left
    c.line(x - mark_offset - mark_length, y, x - mark_offset, y)
    c.line(x, y - mark_offset, x, y - mark_offset - mark_length)

    # Bottom-right
    c.line(x + w_pts + mark_offset, y, x + w_pts + mark_offset + mark_length, y)
    c.line(x + w_pts, y - mark_offset, x + w_pts, y - mark_offset - mark_length)


def draw_registration_marks(c, x, y, w_pts, h_pts, col, row, cols, rows):
    """Draw registration/alignment marks at midpoints of shared edges."""
    mark_length = 0.15 * inch
    mark_offset = 0.05 * inch
    c.setLineWidth(0.5)
    c.setStrokeColorRGB(0, 0, 0)

    mid_x = x + w_pts / 2
    mid_y = y + h_pts / 2

    # Top edge midpoint (shared if there's a row above)
    if row > 0:
        c.line(mid_x - mark_length / 2, y + h_pts + mark_offset,
               mid_x + mark_length / 2, y + h_pts + mark_offset)

    # Bottom edge midpoint (shared if there's a row below)
    if row < rows - 1:
        c.line(mid_x - mark_length / 2, y - mark_offset,
               mid_x + mark_length / 2, y - mark_offset)

    # Left edge midpoint (shared if there's a column to the left)
    if col > 0:
        c.line(x - mark_offset, mid_y - mark_length / 2,
               x - mark_offset, mid_y + mark_length / 2)

    # Right edge midpoint (shared if there's a column to the right)
    if col < cols - 1:
        c.line(x + w_pts + mark_offset, mid_y - mark_length / 2,
               x + w_pts + mark_offset, mid_y + mark_length / 2)


def generate_board_pdf(image_path, output_path, width=None, height=None, dpi=125,
                       margin=0.5, overlap=0.0, no_labels=False, force_landscape=False):
    """
    Generate a multi-page PDF from a board image.

    Args:
        image_path: Path to board image file
        output_path: Output PDF path
        width: Explicit board width in inches (optional)
        height: Explicit board height in inches (optional)
        dpi: DPI for size derivation (default: 300)
        margin: Page margin in inches (default: 0.5)
        overlap: Overlap between adjacent pages in inches (default: 0)
        no_labels: If True, suppress assembly labels
        force_landscape: Force landscape page orientation
    """
    # Load image
    img = Image.open(image_path)
    img_w_px, img_h_px = img.size
    print(f"Image: {image_path}")
    print(f"  Pixels: {img_w_px} x {img_h_px}")

    # Calculate physical size
    board_w, board_h = calculate_board_size(img_w_px, img_h_px, width, height, dpi)
    print(f"  Physical size: {board_w:.2f}\" x {board_h:.2f}\"")

    # Determine page orientation
    page_size = letter
    orientation = "portrait"

    if force_landscape:
        page_size = landscape(letter)
        orientation = "landscape"
    elif board_w > board_h:
        # Check if landscape reduces page count
        portrait_cols, portrait_rows, _, _ = split_board(board_w, board_h, letter, margin, overlap)
        landscape_cols, landscape_rows, _, _ = split_board(board_w, board_h, landscape(letter), margin, overlap)

        if landscape_cols * landscape_rows < portrait_cols * portrait_rows:
            page_size = landscape(letter)
            orientation = "landscape"

    page_w_pts, page_h_pts = page_size
    print(f"  Page orientation: {orientation}")

    # Calculate page grid
    cols, rows, usable_w, usable_h = split_board(board_w, board_h, page_size, margin, overlap)
    total_pages = cols * rows
    print(f"  Pages: {total_pages} ({cols} cols x {rows} rows)")
    print(f"  Usable area per page: {usable_w:.2f}\" x {usable_h:.2f}\"")

    # Create PDF
    c = pdf_canvas.Canvas(str(output_path), pagesize=page_size)

    margin_pts = margin * inch
    page_num = 0

    for row in range(rows):
        for col in range(cols):
            page_num += 1

            # Calculate which portion of the board this page covers (in inches)
            # With overlap, each successive page starts (usable - overlap) further
            board_x_start = col * (usable_w - overlap)
            board_y_start = row * (usable_h - overlap)

            # The piece width/height in inches (may be smaller for last col/row)
            piece_w = min(usable_w, board_w - board_x_start)
            piece_h = min(usable_h, board_h - board_y_start)

            # Convert board coordinates to pixel coordinates for cropping
            px_per_inch_x = img_w_px / board_w
            px_per_inch_y = img_h_px / board_h

            crop_left = int(board_x_start * px_per_inch_x)
            crop_top = int(board_y_start * px_per_inch_y)
            crop_right = int(min((board_x_start + piece_w) * px_per_inch_x, img_w_px))
            crop_bottom = int(min((board_y_start + piece_h) * px_per_inch_y, img_h_px))

            tile_img = img.crop((crop_left, crop_top, crop_right, crop_bottom))

            # Position on page
            piece_w_pts = piece_w * inch
            piece_h_pts = piece_h * inch
            x = margin_pts
            y = page_h_pts - margin_pts - piece_h_pts

            # Draw the image piece
            img_reader = ImageReader(tile_img)
            c.drawImage(img_reader, x, y, width=piece_w_pts, height=piece_h_pts,
                        preserveAspectRatio=True, mask='auto')

            # Draw crop marks
            draw_crop_marks(c, x, y, piece_w_pts, piece_h_pts)

            # Draw registration marks on shared edges
            draw_registration_marks(c, x, y, piece_w_pts, piece_h_pts, col, row, cols, rows)

            # Draw assembly label
            if not no_labels:
                c.setFont("Helvetica", 8)
                label = (f"Page {page_num}/{total_pages} "
                         f"(Row {row + 1}/{rows}, Col {col + 1}/{cols})")
                c.drawString(x, y - 0.25 * inch, label)

                c.setFont("Helvetica", 7)
                size_info = (f"Assembled size: {board_w:.2f}\" x {board_h:.2f}\" | "
                             f"This piece: {piece_w:.2f}\" x {piece_h:.2f}\"")
                c.drawString(x, y - 0.4 * inch, size_info)

                if overlap > 0:
                    c.drawString(x, y - 0.55 * inch,
                                 f"Overlap: {overlap:.2f}\" on shared edges")

            c.showPage()

    c.save()
    print(f"\nSaved: {output_path} ({total_pages} pages)")


def load_boards_from_metadata(metadata_path):
    """
    Load Custom_Board entries from a tile_metadata.json file.

    Returns:
        List of board dicts with keys: local_image, nickname, guid, etc.
    """
    import json

    with open(metadata_path) as f:
        metadata = json.load(f)

    boards = metadata.get('boards', [])
    if not boards:
        print(f"No Custom_Board objects found in {metadata_path}")
    return boards


def main():
    parser = argparse.ArgumentParser(
        description='Generate a multi-page PDF from a board image for physical assembly'
    )
    parser.add_argument('image_file', nargs='?', default=None,
                        help='Path to board image (PNG/JPG)')

    # Metadata mode
    parser.add_argument('-m', '--metadata', default=None,
                        help='Path to tile_metadata.json (auto-detect boards)')

    # Sizing options
    sizing = parser.add_argument_group('sizing (pick one approach)')
    sizing.add_argument('--width', type=float, default=None,
                        help='Physical width in inches')
    sizing.add_argument('--height', type=float, default=None,
                        help='Physical height in inches')
    sizing.add_argument('--dpi', type=int, default=125,
                        help='Derive size from image pixels (default: 125)')

    # Output options
    parser.add_argument('-o', '--output', default=None,
                        help='Output PDF file (default: board.pdf)')
    parser.add_argument('--margin', type=float, default=0.5,
                        help='Page margin in inches (default: 0.5)')
    parser.add_argument('--overlap', type=float, default=0.0,
                        help='Overlap between adjacent pages in inches (default: 0)')
    parser.add_argument('--no-labels', action='store_true',
                        help="Don't draw assembly text labels")
    parser.add_argument('--landscape', action='store_true',
                        help='Force landscape page orientation')

    args = parser.parse_args()

    # Metadata mode: auto-detect boards from tile_metadata.json
    if args.metadata:
        metadata_path = Path(args.metadata)
        if not metadata_path.exists():
            print(f"Error: Metadata file not found: {metadata_path}")
            return 1

        boards = load_boards_from_metadata(metadata_path)
        if not boards:
            return 1

        print(f"Found {len(boards)} board(s) in {metadata_path}")

        for i, board in enumerate(boards):
            nickname = board.get('nickname', '') or f"board_{i + 1}"
            local_image = board.get('local_image', '')

            if not local_image or not Path(local_image).exists():
                print(f"\nSkipping '{nickname}': image not found ({local_image})")
                continue

            # Determine output filename
            if args.output and len(boards) == 1:
                output_path = Path(args.output)
            elif args.output and len(boards) > 1:
                base = Path(args.output)
                output_path = base.parent / f"{base.stem}_{i + 1}{base.suffix}"
            else:
                safe_name = nickname.replace(' ', '_').replace('/', '_') or f"board_{i + 1}"
                output_path = Path(f"{safe_name}.pdf")

            print(f"\n--- Board {i + 1}/{len(boards)}: {nickname or '(unnamed)'} ---")

            generate_board_pdf(
                image_path=Path(local_image),
                output_path=output_path,
                width=args.width,
                height=args.height,
                dpi=args.dpi,
                margin=args.margin,
                overlap=args.overlap,
                no_labels=args.no_labels,
                force_landscape=args.landscape,
            )

        return 0

    # Direct image mode
    if not args.image_file:
        parser.error("either image_file or --metadata is required")

    image_path = Path(args.image_file)
    if not image_path.exists():
        print(f"Error: Image file not found: {image_path}")
        return 1

    output_path = Path(args.output or 'board.pdf')

    generate_board_pdf(
        image_path=image_path,
        output_path=output_path,
        width=args.width,
        height=args.height,
        dpi=args.dpi,
        margin=args.margin,
        overlap=args.overlap,
        no_labels=args.no_labels,
        force_landscape=args.landscape,
    )

    return 0


if __name__ == '__main__':
    sys.exit(main())
