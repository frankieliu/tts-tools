# Board PDF Generator Guide

Generate a multi-page printable PDF from a board image, split across letter-sized pages with crop marks and registration marks for physical assembly.

## End-to-End Workflow (from TTS Workshop File)

The full pipeline to go from a TTS workshop `.json` file to a printed board PDF:

```bash
# 1. Extract tiles, boards, and tokens from the TTS JSON
#    This produces tile_metadata.json with image URLs, scales, and local paths
tts-extract-tiles Workshop/*.json

# 2. Generate the board PDF from the extracted metadata
#    The -m flag reads Custom_Board entries and finds their images automatically
tts-generate-board-pdf -m tile_metadata.json --dpi 100 -o board.pdf
```

Step 1 (`tts-extract-tiles`) parses the TTS JSON, identifies all `Custom_Tile`, `Custom_Board`, and `Custom_Token` objects, downloads their images to `Images/`, and writes `tile_metadata.json`.

Step 2 (`tts-generate-board-pdf -m`) reads the board entries from that metadata, locates their downloaded images, and generates the multi-page PDF.

**Why boards need a separate script:** The standard TTS tile scaling formula (`BASE × scale × aspect`) works for `Custom_Tile` and `Custom_Token` but gives incorrect sizes for `Custom_Board` objects (e.g., 2"×1.8" for a full game board). Board sizing must be specified via explicit dimensions or DPI instead.

**Choosing DPI:** The board image pixel dimensions divided by DPI gives the physical size. Lower DPI = larger board. For a 3000×2633 image: 300 DPI → 10"×8.8", 150 DPI → 20"×17.6", 100 DPI → 30"×26.3". You may need to experiment to find the right physical size for your game.

## Quick Start

```bash
# From metadata (recommended — auto-detects board images)
tts-generate-board-pdf -m tile_metadata.json --dpi 150

# Using explicit dimensions (if you know the board size)
tts-generate-board-pdf board.png --width 11 --height 9.8 -o board.pdf

# Using DPI-based sizing (derives size from image pixels)
tts-generate-board-pdf board.png --dpi 150 -o board.pdf

# Default: 300 DPI if no sizing specified
tts-generate-board-pdf board.png
```

## Sizing Options

### Explicit Dimensions (`--width` / `--height`)

Specify the desired physical size directly in inches:

```bash
# Both dimensions
tts-generate-board-pdf board.png --width 20 --height 16

# Width only (height derived from aspect ratio)
tts-generate-board-pdf board.png --width 20

# Height only (width derived from aspect ratio)
tts-generate-board-pdf board.png --height 16
```

### DPI-Based (`--dpi`)

Derive physical size from the image's pixel dimensions:

```
physical_width  = image_width_px  / DPI
physical_height = image_height_px / DPI
```

For example, a 3000x2400 image at 150 DPI produces a 20" x 16" board.

```bash
tts-generate-board-pdf board.png --dpi 150
```

Default DPI is 300 if neither `--width`, `--height`, nor `--dpi` is specified.

## How Page Splitting Works

The board is split into a grid of pages, each containing a portion of the image:

```
Board (20" x 16")  →  Split across 3x2 = 6 pages (letter, 0.5" margin)

┌─────────┬─────────┬─────────┐
│ Page 1  │ Page 2  │ Page 3  │
│ R1,C1   │ R1,C2   │ R1,C3   │
│         │         │         │
├─────────┼─────────┼─────────┤
│ Page 4  │ Page 5  │ Page 6  │
│ R2,C1   │ R2,C2   │ R2,C3   │
│         │         │         │
└─────────┴─────────┴─────────┘

Each page has:
  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ┐   ← crop marks at corners
  │ ┌───────────────┐ │
  │ │               │ │   ← board image piece
  │ │               │ │
  │ └───────────────┘ │
  │  Page 2/6 (R1,C2) │   ← assembly label
  └ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```

- **Usable area** = page size minus 2× margin on each side
  - Letter portrait: 7.5" x 10" (with 0.5" margins)
  - Letter landscape: 10" x 7.5" (with 0.5" margins)
- **Grid**: `cols = ceil(board_width / usable_width)`, same for rows

## Assembly Instructions

1. Print all pages at 100% scale (no "fit to page")
2. Cut along the crop marks at each corner
3. Align registration marks on shared edges between adjacent pages
4. Tape or glue pages together, using overlap if specified
5. Each page is labeled with its grid position (e.g., "Row 1/2, Col 2/3")

## Options Reference

| Option | Default | Description |
|--------|---------|-------------|
| `-m, --metadata FILE` | — | Read boards from tile_metadata.json |
| `--width INCHES` | — | Physical board width |
| `--height INCHES` | — | Physical board height |
| `--dpi N` | 300 | Derive size from pixels |
| `-o, --output FILE` | board.pdf | Output PDF path |
| `--margin INCHES` | 0.5 | Page margin |
| `--overlap INCHES` | 0 | Overlap between adjacent pages |
| `--no-labels` | off | Suppress assembly text labels |
| `--landscape` | auto | Force landscape orientation |

### Overlap

Use `--overlap` to add shared content between adjacent pages, making alignment easier:

```bash
tts-generate-board-pdf board.png --width 20 --overlap 0.25
```

With overlap, adjacent pages share 0.25" of image content along their shared edge, giving you a visual guide for alignment.

### Landscape Auto-Detection

By default, if the board is wider than tall and landscape orientation would reduce the total page count, landscape is used automatically. Use `--landscape` to force it.

## Custom_Board Metadata Properties

The `extract_tiles.py` script captures three board-specific properties from TTS:

| Property | Description | Useful for sizing? |
|----------|-------------|-------------------|
| `WidthScale` | Always equals the image aspect ratio (width/height) | No — redundant with image dimensions |
| `ImageScalar` | Typically 1.0 | No — no effect at default value |
| `Thickness` | 3D thickness of the board in TTS (e.g., 0.1) | No — irrelevant to print |

These properties are stored in `tile_metadata.json` but **do not help determine the physical board size**. The standard TTS tile formula (`BASE_WIDTH × scaleX × aspect`) also fails for boards — it gives ~2"×1.8" for what should be a full game board. Board physical size must be determined via DPI or explicit dimensions.

## Calibrating Board Size with Track Tiles

Track tiles computed via the TTS tile formula are **1.37" × 1.44"** (34.8mm × 36.6mm). These should fit within the smaller hexes on the game board.

To calibrate:
1. Print one page of the board at your chosen DPI
2. Measure the hex size on the printed page
3. Check that a 1.37" × 1.44" tile fits inside the smaller hexes
4. Adjust DPI up (smaller board) or down (larger board) as needed

**Hex geometry reference** (pointy-top hexagon fitting a 1.37" × 1.44" tile):
- Side length: ~0.72" (18.3mm)
- Width (flat to flat): ~1.25"
- Height (point to point): ~1.44"

## Examples

```bash
# Steam Power board at known dimensions
tts-generate-board-pdf Images/board.png --width 11 --height 9.8 -o steam_board.pdf

# Large board with overlap for easier assembly
tts-generate-board-pdf Images/board.png --width 24 --height 18 --overlap 0.5

# Minimal margins to maximize image area per page
tts-generate-board-pdf Images/board.png --dpi 200 --margin 0.25

# No labels for cleaner output
tts-generate-board-pdf Images/board.png --width 15 --no-labels
```
