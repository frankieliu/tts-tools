# Updated Printing Script with Correct TTS Scaling

## What's New

The updated `generate_tiles_pdf_v2.py` script now uses the **correct TTS scaling formula** derived from real-world measurements:

```python
BASE_WIDTH = 1.300 inches
BASE_HEIGHT = 1.318 inches

Physical Width = BASE_WIDTH × Transform.scaleX × (image_width / image_height)
Physical Height = BASE_HEIGHT × Transform.scaleZ
```

### Key Improvements

1. **Accurate Sizing**: Items print at their true physical size as displayed in TTS
2. **Multi-Page Support**: Large items (>8.5"×11") automatically split across multiple pages
3. **White Borders**: Configurable white border (default 0.25") on multi-page prints
4. **Registration Marks**: Alignment marks for assembling multi-page items

## Usage

### Basic Usage

```bash
# Extract metadata first
python src/extract_tiles.py Workshop/game.json -o tile_metadata.json

# Generate PDF with correct TTS scaling
python src/generate_tiles_pdf_v2.py Workshop/game.json -o output.pdf
```

### Examples

**Example 1: Print all items with correct sizing**
```bash
python src/generate_tiles_pdf_v2.py Workshop/ClankLegacy.json -o clank_all.pdf
```

**Example 2: Print tokens only (small items packed)**
```bash
python src/generate_tiles_pdf_v2.py Workshop/ClankLegacy.json --tokens-only -o tokens.pdf
```

**Example 3: Print boards (will use multi-page for large boards)**
```bash
python src/generate_tiles_pdf_v2.py Workshop/ClankLegacy.json --boards-only -o boards.pdf
```

**Example 4: Custom white border for multi-page items**
```bash
python src/generate_tiles_pdf_v2.py Workshop/ClankLegacy.json --multipage-margin 0.5
```

## Expected Sizes with Correct Scaling

### Clank Legacy Examples

| Object | TTS Scale | Image Size | Calculated Print Size | Pages |
|--------|-----------|------------|----------------------|-------|
| Small token | 0.25 | 184×184 px | 0.33" × 0.33" | 1 (packed) |
| Medium token | 0.42 | 157×157 px | 0.55" × 0.55" | 1 (packed) |
| Large token | 0.61 | 257×256 px | 0.79" × 0.79" | 1 (packed) |
| Major marker | 0.83 | 212×214 px | 1.07" × 1.09" | 1 (packed) |
| Player mat | 5.39 | 2501×2000 px | 8.76" × 7.10" | 1 |
| Main board | 22.0 | 2644×3775 px | 20.0" × 29.0" | 6 (3×2 grid) |
| HQ board | 9.61 | 3899×2450 px | 19.9" × 12.7" | 4 (2×2 grid) |

### Multi-Page Layout

**Main Board (20" × 29" → 6 pages):**
```
With 0.25" margins, usable area per page: 8.0" × 10.5"

Layout (3 columns × 2 rows):
┌─────────┬─────────┬─────────┐
│ Page 1  │ Page 2  │ Page 3  │
│ 6.7×14.5│ 6.7×14.5│ 6.7×14.5│
├─────────┼─────────┼─────────┤
│ Page 4  │ Page 5  │ Page 6  │
│ 6.7×14.5│ 6.7×14.5│ 6.7×14.5│
└─────────┴─────────┴─────────┘

Each tile: 6.67" × 14.5"
Assemble: 20" × 29" total
```

## Command-Line Options

```
Required:
  json_file                TTS JSON file

Optional:
  -m, --metadata FILE      Metadata file (default: tile_metadata.json)
  -o, --output FILE        Output PDF (default: tiles_and_boards.pdf)
  --small-threshold N      Pack items smaller than N inches (default: 4.0)
  --tiles-only             Generate tiles only
  --boards-only            Generate boards only
  --tokens-only            Generate tokens only
  --no-labels              Don't draw text labels
  --no-grouping            Print all duplicates
  --multipage-margin N     White border for multi-page items (default: 0.25")
```

## Multi-Page Features

### Automatic Splitting

Items larger than 8.5" × 11" (with margins) are automatically split:

**Calculation:**
```python
usable_width = 8.5" - (2 × margin)  # 8.0" with 0.25" margins
usable_height = 11" - (2 × margin)  # 10.5" with 0.25" margins

cols = ceil(item_width / usable_width)
rows = ceil(item_height / usable_height)
```

### Registration Marks

Multi-page items include:
- **Corner crop marks**: For cutting each page
- **Midpoint marks**: For aligning pages
- **Assembly info**: "Row X/Y, Col A/B" on each page
- **Total size**: Shows final assembled dimensions

### Assembly Instructions

1. Print all pages for the item
2. Trim each page along the crop marks
3. Align registration marks (midpoint marks match up)
4. Tape or glue pages together from the back
5. Verify final size matches the label

## Comparison: Old vs New Script

| Feature | Old (generate_tiles_pdf.py) | New (generate_tiles_pdf_v2.py) |
|---------|----------------------------|-------------------------------|
| **Scaling** | `scale × scale_factor` (arbitrary) | Correct TTS formula with BASE units |
| **Board Size** | scale 22 → 22" (wrong!) | scale 22 → 20" × 29" (correct!) |
| **Multi-Page** | ❌ Not supported | ✅ Automatic splitting |
| **Margins** | Fixed 0.5" | Configurable per item type |
| **Registration** | Basic crop marks | Full registration system |
| **Accuracy** | Approximate | Verified with real measurements |

### Size Comparison Examples

**Main Board (scale 22.0, aspect 0.70):**
- Old script: 22" × 22" → WRONG
- New script: 20" × 29" → CORRECT

**Token (scale 0.25, aspect 1.0):**
- Old script: 0.25" × 0.25" → Too small
- New script: 0.33" × 0.33" → Correct

**Player Mat (scale 5.39, aspect 1.25):**
- Old script: 5.39" × 5.39" → Wrong aspect
- New script: 8.76" × 7.10" → Correct

## Troubleshooting

### Issue: Pages don't align perfectly

**Solution:**
- Ensure printer is set to "Actual Size" not "Fit to Page"
- Use the same printer for all pages
- Check that paper hasn't shifted in the tray
- Use registration marks for precise alignment

### Issue: Items too large even with multi-page

**Solution:**
- For extremely large items (>40"), consider:
  - Professional large format printing
  - Scaling down (note: will no longer be "true" size)
  - Using as reference only

### Issue: White borders too large/small

**Solution:**
```bash
# Smaller border (0.125")
python src/generate_tiles_pdf_v2.py game.json --multipage-margin 0.125

# Larger border (0.5")
python src/generate_tiles_pdf_v2.py game.json --multipage-margin 0.5
```

## Testing

Test with Clank Legacy to verify:

```bash
# Extract metadata
cd /path/to/clank_legacy/deserialized
python /path/to/src/extract_tiles.py Workshop/*.json

# Generate PDF
python /path/to/src/generate_tiles_pdf_v2.py Workshop/*.json -o clank_correct.pdf

# Check output
# - Main boards should report 20" × 29" (6 pages)
# - Tokens should be 0.33" - 0.79"
# - Player mats should be ~8.76" × 7.10"
```

## Migration Guide

### Switching from Old to New Script

1. **Backup existing PDFs** (if you need to compare)

2. **Use new script**:
```bash
# Old way
python src/generate_tiles_pdf.py game.json --scale-factor 1.0

# New way (no scale-factor needed!)
python src/generate_tiles_pdf_v2.py game.json
```

3. **Expect different sizes**:
   - Items will print at their CORRECT size
   - Some items may now require multiple pages
   - Overall accuracy is much better

4. **Test print one page first** before printing all

### Converting Old Workflow

```bash
# Old workflow
python src/extract_tiles.py game.json
python src/generate_tiles_pdf.py game.json --scale-factor 1.0 --max-size 10

# New workflow (simpler!)
python src/extract_tiles.py game.json
python src/generate_tiles_pdf_v2.py game.json
```

## Future Enhancements

Potential improvements:
- [ ] Support for other page sizes (A4, legal, tabloid)
- [ ] PDF booklet mode for easier printing
- [ ] Automatic overlap between tiles for easier alignment
- [ ] Print preview with size validation
- [ ] Batch processing multiple mods

## Summary

**Key Points:**
- Uses correct TTS scaling formula (BASE = 1.3" × 1.318")
- Automatic multi-page splitting for large items
- Configurable margins and registration marks
- Prints items at their true physical size
- Verified against real Clank Legacy measurements

**When to Use:**
- ✅ When you want accurate physical sizes
- ✅ When printing boards or large components
- ✅ When you have real-world measurements to match
- ✅ For professional or final prints

**When to Use Old Script:**
- Use `--scale-factor` to intentionally scale all items
- Quick prototypes where size doesn't matter
- Forcing everything to fit on one page

---

**Updated:** 2026-02-02
**Script:** `src/generate_tiles_pdf_v2.py`
**Formula:** Physical size = 1.3" × Transform.scale × aspect_ratio
