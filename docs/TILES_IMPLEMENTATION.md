# Tile and Board Extraction Implementation

## Date: 2026-01-30

## Summary

Implemented complete tile and board extraction system for TTS mods, enabling users to generate printable PDFs of game tiles, player boards, and other non-card objects.

## Key Finding: TTS Scaling System

**Critical Discovery:** TTS JSON files do NOT contain absolute physical measurements. They only contain relative scale multipliers (`Transform.scaleX` and `Transform.scaleZ`).

**No DPI or Physical Size Information:**
- ❌ No dots-per-inch (DPI)
- ❌ No inches or centimeters
- ❌ No absolute physical dimensions
- ✅ Only relative scale multipliers

**Scaling Reference:**
- Cards at scale 1.0 in Evenfall mod
- We print cards at 2.5" × 3.5"
- This gives conversion: **1 TTS scale unit ≈ 2.5 inches** (approximate)

## Scale Patterns Discovered

| Object Type | Scale Range | Print Size (scale_factor=1.0) |
|-------------|-------------|--------------------------------|
| Standard cards | 1.0 - 1.76 | 1.0" - 1.76" |
| Small tiles/tokens | 0.36 - 2.6 | 0.36" - 2.6" |
| Medium tiles/boards | 1.5 - 6.0 | 1.5" - 6.0" |
| Large backgrounds | 22 - 200 | 22" - 200" (needs scaling) |

## Implementation

### 1. Tile Extraction Tool

**File:** `src/extract_tiles.py`

**Purpose:**
- Parse TTS JSON to find `Custom_Tile` and `Custom_Board` objects
- Extract scale, image URL, nickname, and properties
- Match local downloaded images
- Generate metadata file for PDF generation

**Key Features:**
- Recursive JSON traversal
- Extracts all tile/board properties:
  - `scale_x`, `scale_y`, `scale_z` - Scale multipliers
  - `image_url` - Image URL
  - `image_scalar` - Image scaling factor
  - `thickness`, `stackable`, `stretch` - Physical properties
- Finds local images in `Images/` directory
- Outputs `tile_metadata.json`

**Usage:**
```bash
tts-extract-tiles Workshop/*.json -o tile_metadata.json
```

### 2. Tile PDF Generator

**File:** `src/generate_tiles_pdf.py`

**Purpose:**
- Generate printable PDF from tiles and boards
- Convert TTS scale to physical inches
- Apply size constraints
- Create one-per-page layout with crop marks

**Key Features:**
- Configurable scale factor (default: auto-detect from card decks in the mod)
- Maximum size constraint to prevent oversized prints
- Page-aware constraining (items always fit within page margins)
- Automatic landscape page rotation for wide images
- Image aspect ratio preservation for large items
- Small item packing (multiple per page)
- Crop marks for cutting
- Size labels on each page
- Handles PNG transparency

**Scaling Logic:**
```python
# Convert TTS scale to inches
width_inches = scale_x × scale_factor
height_inches = scale_z × scale_factor

# Apply max_size constraint
if width_inches > max_size or height_inches > max_size:
    scale_down = max_size / max(width_inches, height_inches)
    width_inches *= scale_down
    height_inches *= scale_down

# For large items, use image's native aspect ratio
# (prevents TTS stretch:true from forcing square output)
if image_width > image_height:
    # Landscape: use image aspect ratio
    width_inches = max_dim
    height_inches = max_dim / (image_width / image_height)

# Constrain to available page area
# Portrait: 7.5" × 10", Landscape: 10" × 7.5"
if width_inches > avail_w or height_inches > avail_h:
    scale_down = min(avail_w / width_inches, avail_h / height_inches)
    width_inches *= scale_down
    height_inches *= scale_down
```

**Usage:**
```bash
tts-generate-tiles-pdf Workshop/*.json \
    --scale-factor 1.0 \
    --max-size 10.0 \
    --tiles-only
```

### 3. Wrapper Scripts

**Files:**
- `bin/tts-extract-tiles` - Wrapper for tile extraction
- `bin/tts-generate-tiles-pdf` - Wrapper for PDF generation

**Features:**
- Use `uv run` for Python environment management
- Change to tts-tools directory before execution
- Pass through all command-line arguments

## Testing Results

### Test 1: Evenfall Mod (3160692601)

**Tiles found:** 14
- 2 Catalyst tokens: scale 0.36 → 0.4" × 0.4"
- 4 unnamed tiles: scale 2.14-2.61 → 2.1"-2.6"
- 4 Overview boards: scale 1.48 → 1.5" × 1.5"
- 4 unnamed large tiles: scale 6.02 → 6.0" × 6.0"

**PDF generated:** 19 MB, 14 pages
**Result:** ✓ All tiles printed at reasonable sizes

### Test 2: Eternal Decks (3637615329)

**Tiles found:** 10
- 9 background tiles: scale 200 → scaled down to 7.5" × 7.5"
- 1 medium tile: scale 22 → scaled down to fit

**PDF generated:** Size TBD, 10 pages
**Result:** ✓ Max-size constraint working correctly

## Documentation Created

### 1. TILES_AND_BOARDS.md

Comprehensive guide covering:
- TTS scaling system explanation
- Scale reference points
- Tool usage instructions
- Scale factor guide by mod type
- Complete workflow examples
- Technical details
- Troubleshooting tips

### 2. README.md Updates

Added to main README:
- Tile/board workflow diagram
- Tool descriptions for tts-extract-tiles and tts-generate-tiles-pdf
- Updated features section
- Updated directory structure
- References to new documentation

### 3. DOCUMENTATION_UPDATES.md

Already exists from previous work, documents the comprehensive TTS JSON structure analysis.

## Usage Recommendations

### For Game Pieces (Tiles, Player Boards)

```bash
# Default works well for most tiles
tts-generate-tiles-pdf Workshop/*.json --scale-factor 1.0 --max-size 10.0
```

### For Large Backgrounds

```bash
# Use smaller scale factor or rely on max-size
tts-generate-tiles-pdf Workshop/*.json --scale-factor 0.05 --max-size 11.0
```

### Separate Tiles and Boards

```bash
# Generate tiles only
tts-generate-tiles-pdf Workshop/*.json --tiles-only -o game_tiles.pdf

# Generate boards only
tts-generate-tiles-pdf Workshop/*.json --boards-only -o game_boards.pdf
```

## Limitations

1. **No Absolute Size Information:**
   - TTS only provides relative scale
   - Auto-detection from card decks usually provides the correct scale factor
   - Different mods may require manual `--scale-factor` override

2. **Page Size:**
   - Limited to US Letter (8.5" x 11")
   - Large items are constrained to available page area
   - For items that need to span multiple pages, use `tts-generate-board-pdf`

3. **2D Only:**
   - Only handles Custom_Tile and Custom_Board
   - Cannot extract textures from Custom_Model objects

## Files Added/Modified

**Added:**
- `src/extract_tiles.py` - Tile extraction script
- `src/generate_tiles_pdf.py` - Tile PDF generator
- `bin/tts-extract-tiles` - Wrapper script
- `bin/tts-generate-tiles-pdf` - Wrapper script
- `docs/TILES_AND_BOARDS.md` - Comprehensive guide

**Modified:**
- `README.md` - Added tile/board tools documentation
- All scripts made executable

## Integration with Existing Tools

The tile extraction tools follow the same patterns as card extraction:

1. **Metadata Extraction:** `tts-extract-tiles` (parallel to `tts-extract-sprites`)
2. **PDF Generation:** `tts-generate-tiles-pdf` (parallel to `tts-generate-pdf`)
3. **Workflow:** Extract → Generate (same as cards)

**Not integrated into pipeline yet:**
- `tts-pipeline` currently only handles cards
- Future: could add `--include-tiles` flag to pipeline

## Implemented Features (since initial release)

The following features have been added since the initial implementation:

1. **Small Item Packing:** Multiple small items packed onto shared pages (items < 4" threshold)
2. **Automatic Scale Detection:** Scale factor auto-detected from card decks in the mod
3. **Multi-Page Board Printing:** `tts-generate-board-pdf` splits large items across multiple pages
4. **Landscape Page Rotation:** Large items with landscape images printed on landscape pages
5. **Image Aspect Ratio Preservation:** Large items use native image aspect ratio instead of TTS square scale
6. **Page-Aware Constraining:** Items constrained to available page area, not just a fixed max_size
7. **No-Grouping Default:** All duplicate items printed individually by default; `--group` flag to group

## Future Enhancements

### Medium Priority
1. **Custom Page Sizes:** Support for different paper sizes (A4, legal, tabloid)
2. **Pipeline Integration:** Add tiles to `tts-pipeline`
3. **Batch Processing:** Process multiple mods at once

### Low Priority
4. **Custom_Model Support:** Extract textures from 3D models
5. **Interactive Sizing:** Preview before generating PDF
6. **Print Optimization:** Minimize paper waste

## Success Metrics

✅ **Tile extraction working:** Successfully extracts all tiles from multiple mods
✅ **PDF generation working:** Creates printable PDFs with crop marks
✅ **Scale factor system:** Configurable and documented
✅ **Max-size constraint:** Prevents oversized items
✅ **Documentation complete:** Comprehensive guide with examples
✅ **Testing successful:** Tested on Evenfall and Eternal Decks

## Conclusion

Successfully implemented complete tile and board extraction system for TTS mods. The key challenge was understanding that TTS uses relative scaling without absolute physical measurements. The solution uses a configurable scale factor with reasonable defaults (1 TTS unit = 1 inch) and a max-size safety constraint.

Users can now extract and print game tiles, player boards, and other non-card objects from any TTS mod. The system is flexible enough to handle tiles ranging from tiny tokens (0.36 scale) to massive play mats (200 scale) through appropriate scaling parameters.
