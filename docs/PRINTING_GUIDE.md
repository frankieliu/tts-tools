# Printing Guide: Tokens, Tiles, and Boards from TTS Assets

A complete guide to printing physical game pieces from Tabletop Simulator image assets.

## Overview

The printing tools extract tiles, boards, and tokens from TTS JSON files and generate print-ready PDFs with crop marks and labels. Small items (tokens) are intelligently packed onto pages, while large items (boards) get one per page with automatic landscape rotation for wide images.

## Quick Start

```bash
# Step 1: Extract metadata from TTS JSON
tts-extract-tiles Workshop/your_game.deserialized.json

# Step 2: Generate PDF
tts-generate-tiles-pdf Workshop/your_game.deserialized.json

# Done! Your PDF is ready to print.
```

## Two-Step Workflow

### Step 1: Extract Metadata

Extract tile, board, and token information from your TTS JSON file:

```bash
tts-extract-tiles <json_file> [-o tile_metadata.json]
```

**What it does:**
- Finds all `Custom_Tile`, `Custom_Board`, and `Custom_Token` objects
- Extracts scale, image URL, and properties
- Matches with local downloaded images in `Images/` directory
- Saves metadata for PDF generation

**Example:**
```bash
cd MyGame.deserialized/
tts-extract-tiles Workshop/12345_MyGame.json
```

**Output:**
```
Found 10 tile(s), 2 board(s), and 40 token(s)

Tiles:
  1. Player Board: scale 6.00
  2. Reference Card: scale 4.00
  ...

Tokens:
  1. Heart: scale 0.35
  2. Star: scale 0.35
  ...

Metadata saved to tile_metadata.json
```

### Step 2: Generate PDF

Generate print-ready PDF from the metadata:

```bash
tts-generate-tiles-pdf <json_file> [options]
```

**Common Options:**
- `-m, --metadata FILE` - Path to metadata file (default: tile_metadata.json)
- `-o, --output FILE` - Output PDF filename (default: tiles_and_boards.pdf)
- `--scale-factor N` - TTS scale to inches conversion (default: auto-detect from cards)
- `--max-size N` - Maximum dimension in inches (default: 10.0)
- `--small-threshold N` - Pack items smaller than N inches (default: 4.0)
- `--group` - Group duplicate items and show quantity labels
- `--no-labels` - Do not draw text labels
- `--tiles-only` - Generate only tiles
- `--boards-only` - Generate only boards
- `--tokens-only` - Generate only tokens

## Scaling System

### Understanding TTS Scale

TTS uses **relative scale**, not absolute measurements. By default, the tool **auto-detects** the correct scale factor by analyzing card decks in the mod (assuming standard 88mm poker card height). You can override this with `--scale-factor`.

**Examples with auto-detection:**
- Token with scale 0.35 at detected factor 3.46 → 1.2" × 1.2"
- Player board with scale 6.0 at detected factor 3.46 → ~7.5" (constrained to page)

### Scale Factor

Use `--scale-factor` to override auto-detection:

```bash
# Explicit scale factor
tts-generate-tiles-pdf Workshop/game.json --scale-factor 1.0

# Print everything at half size
tts-generate-tiles-pdf Workshop/game.json --scale-factor 0.5
```

### Maximum Size Constraint

Use `--max-size` to prevent oversized items:

```bash
# Constrain all items to 8 inches maximum
tts-generate-tiles-pdf Workshop/game.json --max-size 8.0
```

**Note:** Large items are also automatically constrained to the available page area (7.5" x 10" portrait, 10" x 7.5" landscape) regardless of `--max-size`.

## Intelligent Packing

### Small vs Large Items

Items are automatically categorized:

- **Small items** (< 4" by default): Packed together on pages
- **Large items** (>= 4" by default): One per page, centered

**Adjust threshold:**
```bash
# Pack items smaller than 3 inches together
tts-generate-tiles-pdf Workshop/game.json --small-threshold 3.0
```

### Duplicate Handling

**Default behavior (no grouping):**
- All copies of each item are printed individually
- Useful when you want to cut them all out at once

**Group duplicates:**
```bash
tts-generate-tiles-pdf Workshop/game.json --group
```
- Identical items are grouped, only one copy printed
- Label shows quantity: "Heart (x12)"

## Automatic Landscape Rotation

Large items with landscape images (width > height) are automatically printed on landscape-oriented pages. This maximizes the printed size:

- **Landscape images** → landscape page (up to 10" wide x 7.5" tall)
- **Portrait images** → portrait page (up to 7.5" wide x 10" tall)
- **Image aspect ratio** is preserved from the source image, not the TTS square scale

## Filtering by Type

Generate PDFs for specific item types:

```bash
# Tiles only
tts-generate-tiles-pdf Workshop/game.json --tiles-only -o tiles.pdf

# Boards only
tts-generate-tiles-pdf Workshop/game.json --boards-only -o boards.pdf

# Tokens only
tts-generate-tiles-pdf Workshop/game.json --tokens-only -o tokens.pdf
```

## PDF Features

### What You Get

Each PDF includes:

**For Small Items (Packed Layout):**
- Multiple items per page in rows
- Crop marks around each item
- Labels with: `#1 - Heart (x12) (0.4" x 0.4")`
- 0.2" spacing between items

**For Large Items (One Per Page):**
- Centered on page
- Crop marks at corners
- Label with size and quantity
- Automatic landscape rotation for wide images

### Labels

**Default labels show:**
- Item number: `#1`, `#2`, `#3`...
- Name: `Heart`, `Player Board`, etc.
- Quantity: `(x12)` if using `--group` and duplicates exist
- Physical size: `(0.4" x 0.4")`

**Remove labels:**
```bash
tts-generate-tiles-pdf Workshop/game.json --no-labels
```

## Complete Examples

### Example 1: Standard Board Game
```bash
cd Evenfall.deserialized/

# Extract metadata
tts-extract-tiles Workshop/3160692601_Evenfall.json

# Generate PDF (auto-detects scale factor)
tts-generate-tiles-pdf Workshop/3160692601_Evenfall.json
```

### Example 2: Tokens Only, All Copies
```bash
# Print all token instances individually
tts-generate-tiles-pdf Workshop/game.json --tokens-only -o tokens_all.pdf
```

### Example 3: Grouped with Labels
```bash
# Group duplicates, show quantities
tts-generate-tiles-pdf Workshop/game.json --group -o grouped.pdf
```

### Example 4: No Labels for Clean Printing
```bash
tts-generate-tiles-pdf Workshop/game.json --no-labels -o clean.pdf
```

## Troubleshooting

### Issue: "Image not found"
**Solution:**
- Ensure Images/ directory exists in the same parent directory as Workshop/
- Run `tts-assets` first to download all images
- Verify image filenames contain the URL hash

### Issue: Items too large/small
**Solutions:**
```bash
# Override auto-detected scale factor
tts-generate-tiles-pdf Workshop/game.json --scale-factor 0.5

# Constrain max size
tts-generate-tiles-pdf Workshop/game.json --max-size 8.0
```

### Issue: Need multiple copies
**Default behavior** already prints all copies individually. If you used `--group`, remove it to print all instances.

### Issue: Missing metadata file
**Solution:** Run extract step first:
```bash
tts-extract-tiles Workshop/game.json
tts-generate-tiles-pdf Workshop/game.json
```

## Tips & Best Practices

### For Best Print Quality
- Use high-resolution source images (300+ DPI)
- Test print one page before printing all pages
- Use cardstock for durability (110 lb cover weight recommended)

### For Easy Cutting
- Use the crop marks as cutting guides
- A paper cutter works better than scissors for straight lines
- Cut slightly inside crop marks for cleaner edges

### For Efficient Printing
- Group similar sizes together with filters (`--tokens-only`, `--tiles-only`)
- Use `--no-labels` to save ink if you don't need labels
- Adjust `--small-threshold` to control packing density

## Reference: All Command-Line Options

```
tts-generate-tiles-pdf <json_file> [OPTIONS]

Required:
  json_file                 Path to TTS deserialized JSON file

Options:
  -m, --metadata FILE       Metadata JSON file (default: tile_metadata.json)
  -o, --output FILE         Output PDF file (default: tiles_and_boards.pdf)
  --scale-factor N          TTS units to inches (default: auto-detect from cards)
  --max-size N              Maximum dimension in inches (default: 10.0)
  --small-threshold N       Pack items smaller than N inches (default: 4.0)
  --tiles-only              Generate PDF with tiles only
  --boards-only             Generate PDF with boards only
  --tokens-only             Generate PDF with tokens only
  --no-labels               Do not draw text labels
  --group                   Group duplicate items (default: print all copies)
  --hex-grid                Arrange hex tiles in honeycomb grid with hex outlines
  --hex-strip               Hex tiles with pointy edges touching, rows offset by half
  --hex-include PAT [...]   Include tokens matching nickname patterns in hex grid
  -h, --help                Show help message
```

## Hex Grid Layouts

For mods with hex-shaped tiles (detected as square RGBA images):

### Honeycomb Grid (`--hex-grid`)
Flat-top hexes in a standard honeycomb layout with thin hex outlines drawn between tiles.

```bash
tts-generate-tiles-pdf Workshop/game.json --hex-grid
```

### Hex Strip (`--hex-strip`)
Flat-top hexes with pointy edges touching horizontally, each row offset by half a tile width. This layout maximizes long straight diagonal cut lines across the page.

```bash
tts-generate-tiles-pdf Workshop/game.json --hex-strip
```

### Including Non-Hex Tokens (`--hex-include`)
Pull additional tokens into the hex grid by matching their nickname (case-insensitive substring). Matched tokens are drawn on a colored hex background and scaled to fit the hex cell.

```bash
# Include Moai head tokens in the hex grid
tts-generate-tiles-pdf Workshop/game.json --hex-strip --hex-include Moai

# Include multiple token types
tts-generate-tiles-pdf Workshop/game.json --hex-strip --hex-include Moai Shell
```

Non-matching items continue to use standard rectangular packing on separate pages.

## Summary

**Two-step process:**
1. Extract metadata: `tts-extract-tiles Workshop/*.json`
2. Generate PDF: `tts-generate-tiles-pdf Workshop/*.json`

**Key features:**
- Auto-detected scale factor from card decks
- Automatic packing of small items
- Automatic landscape rotation for wide images
- Page-aware sizing (items always fit within margins)
- Image aspect ratio preservation for large items
- Professional crop marks and labels
- Filter by item type
