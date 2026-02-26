#!/usr/bin/env python3
"""
Generate PDF with 3D model diffuse textures from TTS metadata.

Each texture gets one page, scaled to fit letter-size with margins.
Labels show nickname, pixel dimensions, and copy count.

Usage:
    python generate_model_textures_pdf.py -m model_texture_metadata.json -o model_textures.pdf
"""

import json
import sys
from pathlib import Path
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader


def generate_model_textures_pdf(metadata_file: Path, output_file: Path, no_labels: bool = False):
    """
    Generate a PDF with one model texture per page, scaled to fit.

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
    # Reserve space for label below image
    label_space = 0.4 * inch if not no_labels else 0

    c = pdf_canvas.Canvas(str(output_file), pagesize=letter)
    total_pages = 0
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

        # Scale to fit available area (preserving aspect ratio)
        draw_height = available_height - label_space
        scale = min(available_width / img_w, draw_height / img_h)
        render_w = img_w * scale
        render_h = img_h * scale

        # Center on page
        x = margin + (available_width - render_w) / 2
        y = margin + label_space + (draw_height - render_h) / 2

        img_reader = ImageReader(img)
        c.drawImage(img_reader, x, y, width=render_w, height=render_h, preserveAspectRatio=True, mask='auto')

        # Draw label
        if not no_labels:
            nickname = item.get('nickname', '') or '(unnamed)'
            count = item.get('count', 1)
            count_str = f" (x{count})" if count > 1 else ""
            label = f"{nickname}{count_str} - {img_w}x{img_h}px"

            c.setFont("Helvetica", 10)
            # Center the label
            text_width = c.stringWidth(label, "Helvetica", 10)
            text_x = margin + (available_width - text_width) / 2
            text_y = margin + 0.1 * inch
            c.drawString(text_x, text_y, label)

        c.showPage()
        total_pages += 1

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
