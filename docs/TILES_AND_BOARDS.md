# TTS Tiles and Boards Extraction

## Overview

This document explains how to extract and print tiles and boards from Tabletop Simulator mods.

## TTS Scaling System

### How TTS Represents Size

TTS JSON files contain `Transform.scaleX` and `Transform.scaleZ` values that represent **relative scale multipliers**, not absolute physical measurements.

**Key Finding:** TTS does NOT store:
- DPI (dots per inch)
- Physical dimensions in inches or centimeters
- Absolute size measurements

### Scale Reference Point

From analysis of multiple mods:

**Cards as Reference:**
- Standard playing cards in Evenfall mod have `scale = 1.0`
- We print these at 2.5" × 3.5" (standard poker size)
- This gives us a reference: **1 scale unit ≈ 2.5 inches** (approximate)

**Observed Scale Patterns:**

| Object Type | Typical Scales | Examples |
|-------------|---------------|----------|
| Standard Cards | 1.0 - 1.76 | Playing cards, game cards |
| Small Tiles | 0.36 - 2.6 | Tokens, small markers |
| Medium Tiles | 1.5 - 6.0 | Player boards, reference cards |
| Large Tiles | 22 - 200 | Play mats, table backgrounds |

### Printing Strategy

**For Printable Game Pieces (scale < 10):**
- Use `--scale-factor 1.0` (1 TTS unit = 1 inch)
- This produces reasonable sizes for tiles and player boards
- Example: Scale 6.0 tile → 6" × 6" print

**For Large Backgrounds (scale > 10):**
- Use `--max-size 10.0` to constrain to printable size
- Or use a smaller `--scale-factor` (e.g., 0.1 or 0.05)
- Example: Scale 200 background → 10" × 10" with max-size constraint

## Tools

### 1. Extract Tile Metadata

```bash
tts-extract-tiles <json_file> [-o tile_metadata.json]
```

**What it does:**
- Finds all `Custom_Tile` and `Custom_Board` objects
- Extracts scale, image URL, and properties
- Matches local downloaded images
- Saves metadata for PDF generation

**Example:**
```bash
cd my_mod.deserialized/
tts-extract-tiles Workshop/my_mod.json
```

**Output:**
```json
{
  "tiles": [
    {
      "name": "Custom_Tile",
      "nickname": "Player Board",
      "scale_x": 6.0,
      "scale_z": 6.0,
      "image_url": "https://...",
      "local_image": "Images/xyz.jpg"
    }
  ],
  "boards": [],
  "summary": {
    "total_tiles": 10,
    "total_boards": 0
  }
}
```

### 2. Generate Tiles PDF

```bash
tts-generate-tiles-pdf <json_file> [options]
```

**Options:**
- `-m, --metadata FILE` - Path to tile_metadata.json (default: tile_metadata.json)
- `-o, --output FILE` - Output PDF file (default: tiles_and_boards.pdf)
- `--scale-factor N` - TTS scale to inches conversion (default: auto-detect from cards)
- `--max-size N` - Maximum dimension in inches (default: 10.0)
- `--tiles-only` - Generate only tiles (ignore boards)
- `--boards-only` - Generate only boards (ignore tiles)

**Auto-Detection:**
By default, the tool automatically detects the correct scale factor by analyzing card decks in the mod. It assumes standard poker card dimensions (88mm height) and calculates the appropriate scale factor. You can override this with `--scale-factor` if needed.

**Examples:**

Generate all tiles and boards with default scaling:
```bash
tts-generate-tiles-pdf Workshop/my_mod.json
```

Generate with smaller scale factor for large mods:
```bash
tts-generate-tiles-pdf Workshop/my_mod.json --scale-factor 0.5
```

Generate only tiles, constrain to 8" max:
```bash
tts-generate-tiles-pdf Workshop/my_mod.json --tiles-only --max-size 8.0
```

## Workflow

### Complete Example

```bash
# 1. Download and deserialize mod
cd ~/bg/my_game
tts-pipeline 1234567890

# 2. Navigate to deserialized directory
cd *_*.deserialized/

# 3. Extract tile metadata
tts-extract-tiles Workshop/*.json

# 4. Generate PDF
tts-generate-tiles-pdf Workshop/*.json

# 5. Print
# tiles_and_boards.pdf now contains one tile/board per page
# Each page has crop marks and size label
```

### Output Format

The PDF contains:
- **One item per page**
- **Crop marks** for cutting
- **Size label** showing dimensions (e.g., "Player Board (6.0" × 6.0")")
- **Automatic orientation** - landscape for wide items, portrait for tall items
- **Centered** on page with margins

## Scale Factor Guide

### Recommended Settings by Mod Type

**Card Games (Eternal Decks, etc.):**
```bash
# Most tiles are backgrounds (scale 200), use small scale factor
tts-generate-tiles-pdf Workshop/*.json --scale-factor 0.05 --max-size 11.0
# Scale 200 → 10" print
```

**Board Games (Evenfall, etc.):**
```bash
# Tiles are game pieces (scale 0.3 - 6.0), use scale factor 1.0
tts-generate-tiles-pdf Workshop/*.json --scale-factor 1.0 --max-size 10.0
# Scale 6.0 → 6" print
```

**Mixed Content:**
```bash
# Generate tiles and backgrounds separately
tts-generate-tiles-pdf Workshop/*.json --tiles-only --scale-factor 1.0 -o game_tiles.pdf
# Then manually adjust for backgrounds if needed
```

### Trial and Error

Since TTS doesn't provide absolute sizes, you may need to experiment:

1. **Start with scale-factor 1.0**
   ```bash
   tts-generate-tiles-pdf Workshop/*.json --scale-factor 1.0
   ```

2. **Check the output** - are items too large or too small?

3. **Adjust scale-factor:**
   - Items too large? Use 0.5 or 0.1
   - Items too small? Use 2.0 or 3.0

4. **Use max-size as safety** to prevent anything from being too large

## Technical Details

### Scale Calculation

```
print_width_inches = scale_x × scale_factor
print_height_inches = scale_z × scale_factor

if print_width_inches > max_size or print_height_inches > max_size:
    scale_down = max_size / max(print_width_inches, print_height_inches)
    print_width_inches *= scale_down
    print_height_inches *= scale_down
```

### Page Constraints

- Page size: US Letter (8.5" × 11")
- Margin: 0.5" on all sides
- Available area: 7.5" × 10" (portrait) or 10" × 7.5" (landscape)
- Items automatically scaled down to fit if needed

### Image Handling

- Images loaded from `Images/` directory
- Aspect ratio preserved
- PNG transparency supported (alpha channel)
- High-resolution output for printing

### Deriving the Correct Scale Factor

The TTS JSON contains enough information to calculate physical sizes if you know ONE actual component size.

**Formula:**
```
width_mm  = BASE × scaleX × aspect_ratio
height_mm = BASE × scaleZ
```

Where:
- `BASE` = calibration constant in mm (derived from known component)
- `scaleX/Z` = Transform.scaleX and Transform.scaleZ from JSON
- `aspect_ratio` = image_width / image_height (from downloaded image)

**To derive BASE from a known card size:**
```
BASE = known_height_mm / scaleZ
```

**Example (Jisogi mod):**
- Type 3 Standard Cards: 63×88mm at scale 0.92
- BASE = 88mm / 0.92 ≈ 96mm
- Scale factor for inches: 96mm / 25.4 ≈ 3.78

**To use with tts-generate-tiles-pdf:**
```bash
tts-generate-tiles-pdf Workshop/*.json --scale-factor 3.78
```

**Key JSON fields for scaling:**
| Object Type | Scale Source | Aspect Source |
|------------|--------------|---------------|
| DeckCustom | Transform.scaleX/Z | (sheet_width/NumWidth) / (sheet_height/NumHeight) |
| Custom_Tile | Transform.scaleX/Z | image_width / image_height |
| Custom_Token | Transform.scaleX/Z | image_width / image_height |

## Limitations

1. **No absolute size information** - TTS scale is relative only
2. **Trial and error required** - optimal scale_factor varies by mod
3. **Large items** - may need to be printed on multiple pages or at poster size
4. **3D models** - only 2D tiles/boards supported, not Custom_Model objects

## Future Improvements

Potential enhancements:
- Multi-page printing for large items (poster mode)
- Automatic scale detection based on card sizes
- Grid layout (multiple small tiles per page)
- Customizable crop marks and labels
- Support for Custom_Model textures

---

## Summary

- TTS uses **relative scale**, not absolute measurements
- Use **cards as reference** (scale 1.0 ≈ 2.5")
- **Experiment with scale-factor** to get desired print size
- **Use max-size** to prevent oversized items
- Each item prints on **separate page** with crop marks
