# Printing Guide: Tokens, Tiles, and Boards from TTS Assets

A complete guide to printing physical game pieces from Tabletop Simulator image assets.

## Overview

The printing tools extract tiles, boards, and tokens from TTS JSON files and generate print-ready PDFs with crop marks and labels. Small items (tokens) are intelligently packed onto pages, while large items (boards) get one per page.

## Quick Start

```bash
# Step 1: Extract metadata from TTS JSON
python src/extract_tiles.py Workshop/your_game.deserialized.json -o tile_metadata.json

# Step 2: Generate PDF
python src/generate_tiles_pdf.py Workshop/your_game.deserialized.json -o output.pdf

# Done! Your PDF is ready to print.
```

## Two-Step Workflow

### Step 1: Extract Metadata

Extract tile, board, and token information from your TTS JSON file:

```bash
python src/extract_tiles.py <json_file> [-o metadata.json]
```

**What it does:**
- Finds all `Custom_Tile`, `Custom_Board`, and `Custom_Token` objects
- Extracts scale, image URL, and properties
- Matches with local downloaded images in `Images/` directory
- Saves metadata for PDF generation

**Example:**
```bash
cd MyGame.deserialized/
python src/extract_tiles.py Workshop/12345_MyGame.json
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
python src/generate_tiles_pdf.py <json_file> [options]
```

**Common Options:**
- `-m, --metadata FILE` - Path to metadata file (default: tile_metadata.json)
- `-o, --output FILE` - Output PDF filename (default: tiles_and_boards.pdf)
- `--scale-factor N` - TTS scale to inches conversion (default: 1.0)
- `--max-size N` - Maximum dimension in inches (default: 10.0)
- `--small-threshold N` - Pack items smaller than N inches (default: 4.0)

## Scaling System

### Understanding TTS Scale

TTS uses **relative scale**, not absolute measurements. The scaling convention:

**Default:** 1 TTS scale unit = 1 inch

**Examples:**
- Token with scale 0.35 → 0.35" × 0.35" (about the size of a penny)
- Player board with scale 6.0 → 6" × 6"
- Game board with scale 200 → 200" × 200" (needs adjustment!)

### Scale Factor

Use `--scale-factor` to adjust the size of all items:

```bash
# Print everything at default size (1 TTS unit = 1 inch)
python src/generate_tiles_pdf.py Workshop/game.json --scale-factor 1.0

# Print everything at half size
python src/generate_tiles_pdf.py Workshop/game.json --scale-factor 0.5

# Print everything at double size
python src/generate_tiles_pdf.py Workshop/game.json --scale-factor 2.0
```

### Maximum Size Constraint

Use `--max-size` to prevent oversized items:

```bash
# Constrain all items to 10 inches maximum
python src/generate_tiles_pdf.py Workshop/game.json --max-size 10.0

# Constrain to 8 inches for easier printing
python src/generate_tiles_pdf.py Workshop/game.json --max-size 8.0
```

**What happens:** Any item larger than max-size will be scaled down proportionally to fit.

## Intelligent Packing

### Small vs Large Items

Items are automatically categorized:

- **Small items** (< 4" by default): Packed together on pages
- **Large items** (≥ 4" by default): One per page, centered

**Adjust threshold:**
```bash
# Pack items smaller than 3 inches together
python src/generate_tiles_pdf.py Workshop/game.json --small-threshold 3.0

# Pack items smaller than 6 inches together
python src/generate_tiles_pdf.py Workshop/game.json --small-threshold 6.0
```

### Duplicate Handling

**Default behavior (grouping):**
- Identical items are automatically grouped
- Only one copy is printed
- Label shows quantity: "Heart (×12)"

**Print all duplicates:**
```bash
python src/generate_tiles_pdf.py Workshop/game.json --no-grouping
```

This prints every instance individually (useful if you want to cut them all out at once).

## Filtering by Type

Generate PDFs for specific item types:

### Tiles Only
```bash
python src/generate_tiles_pdf.py Workshop/game.json --tiles-only -o tiles.pdf
```

### Boards Only
```bash
python src/generate_tiles_pdf.py Workshop/game.json --boards-only -o boards.pdf
```

### Tokens Only
```bash
python src/generate_tiles_pdf.py Workshop/game.json --tokens-only -o tokens.pdf
```

## PDF Features

### What You Get

Each PDF includes:

**For Small Items (Packed Layout):**
- Multiple items per page in rows
- Crop marks around each item
- Labels with: `#1 - Heart (×12) (0.4" × 0.4")`
- 0.2" spacing between items

**For Large Items (One Per Page):**
- Centered on page
- Crop marks at corners
- Label with size and quantity
- Automatic orientation (landscape/portrait)

### Labels

**Default labels show:**
- Item number: `#1`, `#2`, `#3`...
- Name: `Heart`, `Player Board`, etc.
- Quantity: `(×12)` if duplicates exist
- Physical size: `(0.4" × 0.4")`

**Remove labels:**
```bash
python src/generate_tiles_pdf.py Workshop/game.json --no-labels
```

Useful if you just want clean images without text.

## Complete Examples

### Example 1: Standard Board Game
```bash
# Game with player boards, tiles, and tokens
cd Evenfall.deserialized/

# Extract metadata
python src/extract_tiles.py Workshop/3160692601_Evenfall.json

# Generate PDF with default settings
python src/generate_tiles_pdf.py Workshop/3160692601_Evenfall.json -o evenfall.pdf
```

**Expected output:**
- Tokens (scale 0.35): 0.35" × 0.35", packed on 1-2 pages
- Player boards (scale 6.0): 6" × 6", one per page
- Reference cards (scale 4.0): 4" × 4", one per page

### Example 2: Card Game with Large Backgrounds
```bash
# Game with huge background tiles (scale 200)
cd EternalDecks.deserialized/

python src/extract_tiles.py Workshop/2083854795.json

# Scale down large backgrounds
python src/generate_tiles_pdf.py Workshop/2083854795.json \
    --scale-factor 0.05 \
    --max-size 11.0 \
    -o eternal_decks.pdf
```

**Result:** Scale 200 backgrounds → 10" × 10" (fits on letter paper)

### Example 3: Tokens Only, Multiple Copies
```bash
# Extract just the tokens, print all duplicates
python src/generate_tiles_pdf.py Workshop/game.json \
    --tokens-only \
    --no-grouping \
    -o tokens_all.pdf
```

**Use case:** You want to cut out all 40 tokens at once, not just 18 unique ones.

### Example 4: Small Tiles Packed, Custom Size
```bash
# Pack all tiles smaller than 5 inches
python src/generate_tiles_pdf.py Workshop/game.json \
    --tiles-only \
    --small-threshold 5.0 \
    --scale-factor 0.8 \
    -o small_tiles.pdf
```

### Example 5: No Labels for Clean Printing
```bash
# Generate PDF without any text labels
python src/generate_tiles_pdf.py Workshop/game.json \
    --no-labels \
    -o clean_pieces.pdf
```

## Common Workflows

### Workflow A: Print Everything
```bash
# 1. Extract metadata
python src/extract_tiles.py Workshop/game.json

# 2. Generate complete PDF
python src/generate_tiles_pdf.py Workshop/game.json -o complete.pdf

# 3. Print complete.pdf
# Small items are packed, large items are one per page
```

### Workflow B: Separate PDFs by Type
```bash
# Extract once
python src/extract_tiles.py Workshop/game.json

# Generate separate PDFs for each type
python src/generate_tiles_pdf.py Workshop/game.json --tokens-only -o tokens.pdf
python src/generate_tiles_pdf.py Workshop/game.json --tiles-only -o tiles.pdf
python src/generate_tiles_pdf.py Workshop/game.json --boards-only -o boards.pdf
```

### Workflow C: Custom Scaling Per Type
```bash
python src/extract_tiles.py Workshop/game.json

# Tokens at 1.5x size
python src/generate_tiles_pdf.py Workshop/game.json \
    --tokens-only \
    --scale-factor 1.5 \
    -o tokens_large.pdf

# Boards at 0.5x size
python src/generate_tiles_pdf.py Workshop/game.json \
    --boards-only \
    --scale-factor 0.5 \
    -o boards_small.pdf
```

## Troubleshooting

### Issue: "Image not found"
**Problem:** Script can't find downloaded images

**Solution:**
- Ensure Images/ directory exists in the same parent directory as Workshop/
- Check that images were downloaded (use TTS asset downloader first)
- Verify image filenames contain the URL hash

### Issue: Items too large/small
**Problem:** Printed size doesn't match expectations

**Solutions:**
```bash
# If too large, reduce scale factor
python src/generate_tiles_pdf.py Workshop/game.json --scale-factor 0.5

# If too small, increase scale factor
python src/generate_tiles_pdf.py Workshop/game.json --scale-factor 2.0

# Use max-size as safety
python src/generate_tiles_pdf.py Workshop/game.json --max-size 8.0
```

### Issue: Too many pages
**Problem:** Getting 40 pages for 40 tokens

**Solution:** Tokens should pack automatically. Check:
```bash
# Ensure small-threshold is high enough (default: 4.0)
python src/generate_tiles_pdf.py Workshop/game.json --small-threshold 4.0

# Check if your tokens are actually small (< 4")
# If tokens have scale 0.35, they should be 0.35" and pack automatically
```

### Issue: Need multiple copies
**Problem:** Only printing 1 copy of each token, but need 12 Hearts

**Solutions:**

**Option 1:** Print PDF multiple times and cut out the needed quantities
- PDF shows "Heart (×12)" - print and cut 12 copies

**Option 2:** Use --no-grouping to print all instances
```bash
python src/generate_tiles_pdf.py Workshop/game.json --no-grouping
```
- Prints all 12 Hearts individually (more pages, but cut them all at once)

### Issue: Missing metadata file
**Problem:** `Error: Metadata file not found`

**Solution:** Run extract step first:
```bash
python src/extract_tiles.py Workshop/game.json -o tile_metadata.json
python src/generate_tiles_pdf.py Workshop/game.json -m tile_metadata.json
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
- Group similar sizes together with filters (--tokens-only, --tiles-only)
- Use --no-labels to save ink if you don't need labels
- Adjust --small-threshold to control packing density

### For Professional Results
- Laminate tokens for durability
- Mount boards on foam core for stiffness
- Use a corner rounder punch for rounded corners

## Reference: All Command-Line Options

```bash
python src/generate_tiles_pdf.py <json_file> [OPTIONS]

Required:
  json_file                 Path to TTS deserialized JSON file

Options:
  -m, --metadata FILE       Metadata JSON file (default: tile_metadata.json)
  -o, --output FILE         Output PDF file (default: tiles_and_boards.pdf)
  --scale-factor N          TTS units to inches (default: 1.0)
  --max-size N             Maximum dimension in inches (default: 10.0)
  --small-threshold N      Pack items smaller than N inches (default: 4.0)
  --tiles-only             Generate PDF with tiles only
  --boards-only            Generate PDF with boards only
  --tokens-only            Generate PDF with tokens only
  --no-labels              Do not draw text labels
  --no-grouping            Print all duplicate items individually
  -h, --help               Show help message
```

## Scale Reference Guide

| Item Type | Typical TTS Scale | Default Print Size | Recommended Settings |
|-----------|-------------------|-------------------|---------------------|
| Tokens | 0.35 - 0.5 | 0.35" - 0.5" | Default (1.0) |
| Cards | 1.0 - 1.76 | 1.0" - 1.76" | Default (1.0) |
| Small Tiles | 1.5 - 4.0 | 1.5" - 4.0" | Default (1.0) |
| Player Boards | 4.0 - 8.0 | 4" - 8" | Default (1.0) |
| Game Boards | 10 - 30 | 10" - 30" | scale-factor 0.5 or max-size 10.0 |
| Backgrounds | 100 - 200 | 100" - 200" | scale-factor 0.05, max-size 11.0 |

## Summary

**Two-step process:**
1. Extract metadata: `python src/extract_tiles.py`
2. Generate PDF: `python src/generate_tiles_pdf.py`

**Key features:**
- Automatic packing of small items
- Duplicate detection and grouping
- Customizable scaling and sizing
- Professional crop marks and labels
- Filter by item type

**Common use cases:**
- Print all game pieces: Use defaults
- Print tokens only: Use `--tokens-only`
- Adjust size: Use `--scale-factor` or `--max-size`
- Print all duplicates: Use `--no-grouping`
- Clean printing: Use `--no-labels`

Happy printing! 🎲
