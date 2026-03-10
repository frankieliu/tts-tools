#!/usr/bin/env python3
"""
Crop a board image into sections and optionally generate multi-page PDFs.

Takes a board image and a JSON file describing rectangular sections
(as exported by tts-board-splitter), crops each section into a separate
PNG, and optionally generates a multi-page PDF for each section using
tts-generate-board-pdf.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image


def crop_sections(image_path, sections, output_dir):
    """
    Crop image into sections and save as numbered PNGs.

    Args:
        image_path: Path to the source image
        sections: List of section dicts with x, y, w/h or right/bottom
        output_dir: Directory to save cropped PNGs

    Returns:
        List of (section_name, output_path) tuples
    """
    img = Image.open(image_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []

    for i, section in enumerate(sections):
        x = section["x"]
        y = section["y"]
        # Support both w/h and right/bottom formats
        if "w" in section and "h" in section:
            right = x + section["w"]
            bottom = y + section["h"]
        elif "right" in section and "bottom" in section:
            right = section["right"]
            bottom = section["bottom"]
        else:
            print(f"Warning: section {i + 1} missing dimensions, skipping", file=sys.stderr)
            continue

        name = section.get("name", f"Section {i + 1}")
        # Sanitize name for filename
        safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in name).strip()
        filename = f"{i + 1:02d}_{safe_name}.png"
        out_path = output_dir / filename

        cropped = img.crop((x, y, right, bottom))
        cropped.save(out_path)
        print(f"  {filename}  ({right - x}x{bottom - y}px)")
        results.append((name, out_path))

    return results


def generate_pdfs(results, dpi=125, overlap=0):
    """
    Generate a multi-page PDF for each cropped section using tts-generate-board-pdf.

    Args:
        results: List of (section_name, png_path) tuples
        dpi: DPI for PDF generation
        overlap: Overlap in inches between pages
    """
    bin_dir = Path(__file__).resolve().parent.parent / "bin"
    board_pdf_cmd = bin_dir / "tts-generate-board-pdf"

    if not board_pdf_cmd.exists():
        print(f"Error: tts-generate-board-pdf not found at {board_pdf_cmd}", file=sys.stderr)
        sys.exit(1)

    for name, png_path in results:
        pdf_path = png_path.with_suffix(".pdf")
        print(f"  Generating PDF for {name}...")

        cmd = [
            str(board_pdf_cmd),
            "-i", str(png_path),
            "--dpi", str(dpi),
            "-o", str(pdf_path),
        ]
        if overlap > 0:
            cmd.extend(["--overlap", str(overlap)])

        subprocess.run(cmd, check=True)
        print(f"    -> {pdf_path.name}")


def main():
    parser = argparse.ArgumentParser(
        description="Crop a board image into sections and optionally generate PDFs."
    )
    parser.add_argument(
        "-i", "--image", required=True,
        help="Path to the board image (PNG/JPG)"
    )
    parser.add_argument(
        "-j", "--json", required=True,
        help="Path to sections JSON (from tts-board-splitter export)"
    )
    parser.add_argument(
        "-o", "--output-dir", default=None,
        help="Output directory for cropped PNGs (default: board_sections/ next to image)"
    )
    parser.add_argument(
        "--pdf", action="store_true",
        help="Also generate multi-page PDFs for each section"
    )
    parser.add_argument(
        "--dpi", type=int, default=125,
        help="DPI for PDF generation (default: 125)"
    )
    parser.add_argument(
        "--overlap", type=float, default=0,
        help="Overlap in inches between PDF pages (default: 0)"
    )
    args = parser.parse_args()

    image_path = Path(args.image)
    json_path = Path(args.json)

    if not image_path.exists():
        print(f"Error: image not found: {image_path}", file=sys.stderr)
        sys.exit(1)
    if not json_path.exists():
        print(f"Error: JSON not found: {json_path}", file=sys.stderr)
        sys.exit(1)

    # Default output dir next to the image
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = image_path.parent / "board_sections"

    with open(json_path) as f:
        sections = json.load(f)

    print(f"Cropping {len(sections)} section(s) from {image_path.name}...")
    results = crop_sections(image_path, sections, output_dir)
    print(f"Saved {len(results)} cropped image(s) to {output_dir}/")

    if args.pdf:
        print(f"\nGenerating PDFs (dpi={args.dpi}, overlap={args.overlap})...")
        generate_pdfs(results, dpi=args.dpi, overlap=args.overlap)
        print("Done.")


if __name__ == "__main__":
    main()
