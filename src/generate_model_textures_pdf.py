#!/usr/bin/env python3
"""
Generate PDF with 3D model diffuse textures from TTS metadata.

Same-sized textures are packed into grids; unique-sized ones get their own page.
Labels show nickname, pixel dimensions, and copy count.

Usage:
    python generate_model_textures_pdf.py -m model_texture_metadata.json -o model_textures.pdf
"""

import json
import math
import sys
from collections import OrderedDict
from pathlib import Path
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader


def _load_items(models):
    """Load images and return list of (item, img, img_w, img_h) tuples, printing skipped items."""
    loaded = []
    skipped = 0
    for item in models:
        local_image = item.get('local_image', '')
        if not local_image or not Path(local_image).exists():
            nickname = item.get('nickname', '(unnamed)')
            print(f"  Skipping {nickname}: Image not found")
            skipped += 1
            continue
        try:
            img = Image.open(local_image)
        except Exception as e:
            print(f"  Error loading {local_image}: {e}")
            skipped += 1
            continue
        img_w, img_h = img.size
        loaded.append((item, img, img_w, img_h))
    return loaded, skipped


def _draw_label(c, label, margin, available_width, y):
    """Draw a centered label at the given y coordinate."""
    c.setFont("Helvetica", 9)
    text_width = c.stringWidth(label, "Helvetica", 9)
    text_x = margin + (available_width - text_width) / 2
    c.drawString(text_x, y, label)


def _item_label(item, img_w, img_h):
    """Build label string for a texture item."""
    nickname = item.get('nickname', '') or '(unnamed)'
    count = item.get('count', 1)
    count_str = f" (x{count})" if count > 1 else ""
    return f"{nickname}{count_str} - {img_w}x{img_h}px"


def _render_single(c, item, img, img_w, img_h, margin, available_width, available_height, label_space, no_labels):
    """Render a single texture filling its own page. Uses landscape for wide images."""
    use_landscape = img_w > img_h
    if use_landscape:
        page_size = (letter[1], letter[0])
        avail_w, avail_h = available_height, available_width
    else:
        page_size = letter
        avail_w, avail_h = available_width, available_height

    c.setPageSize(page_size)
    draw_height = avail_h - label_space
    scale = min(avail_w / img_w, draw_height / img_h)
    render_w = img_w * scale
    render_h = img_h * scale

    x = margin + (avail_w - render_w) / 2
    y = margin + label_space + (draw_height - render_h) / 2

    img_reader = ImageReader(img)
    c.drawImage(img_reader, x, y, width=render_w, height=render_h, preserveAspectRatio=True, mask='auto')

    if not no_labels:
        label = _item_label(item, img_w, img_h)
        c.setFont("Helvetica", 10)
        text_width = c.stringWidth(label, "Helvetica", 10)
        text_x = margin + (avail_w - text_width) / 2
        text_y = margin + 0.1 * inch
        c.drawString(text_x, text_y, label)

    c.showPage()
    return 1


def _find_best_grid(total_items, img_w, img_h, avail_w, avail_h, spacing, label_height):
    """Find grid (cols, rows, scale) that minimizes pages with min 1-inch cell height."""
    min_cell_h = 72  # 1 inch
    best_cols = 1
    best_rows = 1
    best_scale = 0
    best_pages = total_items

    for cols in range(1, 20):
        max_s_w = (avail_w - (cols - 1) * spacing) / (cols * img_w)
        if max_s_w <= 0:
            break
        for rows in range(1, 30):
            max_s_h = (avail_h - rows * label_height - (rows - 1) * spacing) / (rows * img_h)
            if max_s_h <= 0:
                break
            s = min(max_s_w, max_s_h)
            if img_h * s < min_cell_h:
                continue
            per_page = cols * rows
            if per_page < 2:
                continue
            pages_needed = math.ceil(total_items / per_page)
            if pages_needed < best_pages or (pages_needed == best_pages and s > best_scale):
                best_cols = cols
                best_rows = rows
                best_scale = s
                best_pages = pages_needed

    return best_cols, best_rows, best_scale, best_pages


def _render_grid(c, items_in_group, img_w, img_h, margin, available_width, available_height, no_labels):
    """Render a group of same-sized textures in a grid, returning pages used.

    Uses landscape pages when the images are landscape-oriented and it yields
    fewer pages (or equal pages at a larger scale).
    """
    spacing = 0.1 * inch
    label_height = 0.25 * inch if not no_labels else 0
    total_items = len(items_in_group)

    # If a single image already fills most of the page, don't grid — give each
    # its own page for maximum clarity.
    if img_w > img_h:
        solo_avail_w, solo_avail_h = available_height, available_width
    else:
        solo_avail_w, solo_avail_h = available_width, available_height
    solo_scale = min(solo_avail_w / img_w, solo_avail_h / img_h)
    fill_ratio = (img_w * solo_scale * img_h * solo_scale) / (solo_avail_w * solo_avail_h)
    # If a single image is large (>4 megapixels) and already fills most of the
    # page, don't grid — give each its own page for maximum clarity.
    megapixels = (img_w * img_h) / 1_000_000
    if megapixels > 4 and fill_ratio > 0.7:
        pages = 0
        for item, img, iw, ih in items_in_group:
            label_space = 0.4 * inch if not no_labels else 0
            pages += _render_single(c, item, img, iw, ih, margin, available_width, available_height, label_space, no_labels)
        return pages

    # Try portrait layout
    p_cols, p_rows, p_scale, p_pages = _find_best_grid(
        total_items, img_w, img_h, available_width, available_height, spacing, label_height)

    # Try landscape layout (swap available dimensions)
    l_cols, l_rows, l_scale, l_pages = _find_best_grid(
        total_items, img_w, img_h, available_height, available_width, spacing, label_height)

    # Pick landscape if it needs fewer pages, or same pages but larger scale
    use_landscape = (img_w > img_h and
                     (l_pages < p_pages or (l_pages == p_pages and l_scale > p_scale)))

    if use_landscape:
        cols, rows, scale = l_cols, l_rows, l_scale
        page_size = (letter[1], letter[0])  # landscape
        avail_w, avail_h = available_height, available_width
    else:
        cols, rows, scale = p_cols, p_rows, p_scale
        page_size = letter
        avail_w, avail_h = available_width, available_height

    # If we couldn't fit at least 2, fall back to 1 per page
    if cols * rows < 2:
        pages = 0
        for item, img, iw, ih in items_in_group:
            label_space = 0.4 * inch if not no_labels else 0
            pages += _render_single(c, item, img, iw, ih, margin, available_width, available_height, label_space, no_labels)
        return pages

    per_page = cols * rows
    cell_w = img_w * scale
    cell_h = img_h * scale + label_height

    # Total grid dimensions
    grid_w = cols * cell_w + (cols - 1) * spacing
    grid_h = rows * cell_h + (rows - 1) * spacing

    # Offset to center grid on page
    x_offset = margin + (avail_w - grid_w) / 2
    y_offset = margin + (avail_h - grid_h) / 2

    num_pages = math.ceil(total_items / per_page)
    pages = 0

    for page_idx in range(num_pages):
        c.setPageSize(page_size)
        start = page_idx * per_page
        page_items = items_in_group[start:start + per_page]

        for idx, (item, img, iw, ih) in enumerate(page_items):
            col = idx % cols
            row = idx // cols
            cell_x = x_offset + col * (cell_w + spacing)
            cell_y = y_offset + grid_h - (row + 1) * cell_h - row * spacing

            img_reader = ImageReader(img)
            c.drawImage(img_reader, cell_x, cell_y + label_height, width=cell_w, height=img_h * scale,
                        preserveAspectRatio=True, mask='auto')

            if not no_labels:
                label = _item_label(item, iw, ih)
                c.setFont("Helvetica", 7)
                max_label_w = cell_w
                if c.stringWidth(label, "Helvetica", 7) > max_label_w:
                    while len(label) > 3 and c.stringWidth(label + "…", "Helvetica", 7) > max_label_w:
                        label = label[:-1]
                    label = label + "…"
                text_w = c.stringWidth(label, "Helvetica", 7)
                c.drawString(cell_x + (cell_w - text_w) / 2, cell_y + 0.05 * inch, label)

        # Page header
        if not no_labels:
            orient = " (landscape)" if use_landscape else ""
            header = f"{img_w}x{img_h}px — {total_items} textures{orient}"
            if num_pages > 1:
                header += f" (page {page_idx + 1}/{num_pages})"
            c.setFont("Helvetica", 9)
            pw, ph = page_size
            text_w = c.stringWidth(header, "Helvetica", 9)
            c.drawString((pw - text_w) / 2, margin + avail_h + 0.15 * inch, header)

        c.showPage()
        pages += 1

    return pages


def generate_model_textures_pdf(metadata_file: Path, output_file: Path, no_labels: bool = False):
    """
    Generate a PDF with model textures. Same-sized textures are packed into
    grids; unique-sized textures get one page each.

    Args:
        metadata_file: Path to model_texture_metadata.json
        output_file: Output PDF path
        no_labels: If True, don't draw text labels
    """
    with open(metadata_file) as f:
        metadata = json.load(f)

    models = metadata.get('models', [])
    if not models:
        print("No model textures to generate PDF")
        return 0

    page_width, page_height = letter
    margin = 0.5 * inch
    available_width = page_width - (2 * margin)
    available_height = page_height - (2 * margin)
    label_space = 0.4 * inch if not no_labels else 0

    loaded, skipped = _load_items(models)
    if not loaded:
        print("No valid textures to generate PDF")
        if skipped:
            print(f"  Skipped {skipped} texture(s) with missing images")
        return 0

    # Group by pixel dimensions, preserving encounter order
    groups = OrderedDict()
    for entry in loaded:
        item, img, img_w, img_h = entry
        key = (img_w, img_h)
        groups.setdefault(key, []).append(entry)

    c = pdf_canvas.Canvas(str(output_file), pagesize=letter)
    total_pages = 0

    for (img_w, img_h), items_in_group in groups.items():
        if len(items_in_group) == 1:
            item, img, iw, ih = items_in_group[0]
            total_pages += _render_single(c, item, img, iw, ih, margin, available_width, available_height, label_space, no_labels)
        else:
            total_pages += _render_grid(c, items_in_group, img_w, img_h, margin, available_width, available_height, no_labels)

    if total_pages > 0:
        c.save()
        print(f"\nSaved {output_file.name}: {total_pages} pages")
    else:
        print("No valid textures to generate PDF")

    if skipped:
        print(f"  Skipped {skipped} texture(s) with missing images")

    return 0


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Generate PDF from TTS 3D model textures')
    parser.add_argument(
        '-m', '--metadata',
        type=Path,
        default=Path('model_texture_metadata.json'),
        help='Path to model_texture_metadata.json'
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        default=None,
        help='Output PDF file (default: model_textures.pdf next to metadata)'
    )
    parser.add_argument(
        '--no-labels',
        action='store_true',
        help='Do not draw text labels'
    )

    args = parser.parse_args()

    metadata_file = args.metadata.resolve()

    if not metadata_file.exists():
        print(f"Error: Metadata file not found: {metadata_file}")
        print("Run tts-extract-models first to generate metadata")
        return 1

    if args.output:
        output_file = args.output.resolve()
    else:
        output_file = metadata_file.parent / 'model_textures.pdf'

    print(f"Reading metadata from {metadata_file}")
    print(f"Output: {output_file}")

    return generate_model_textures_pdf(metadata_file, output_file, no_labels=args.no_labels)


if __name__ == '__main__':
    sys.exit(main())
