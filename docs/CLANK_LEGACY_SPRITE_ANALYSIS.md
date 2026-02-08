# Clank Legacy Sprite Sheet Analysis

Analysis of sprite sheets from Clank Legacy: Acquisitions Incorporated TTS mod to determine card dimensions and print quality.

## Overview

**Analyzed Directory:** `/Users/frankliu/Library/CloudStorage/Box-Box/Work/bg/clank_legacy/2083854795_Clank Legacy_ Acquisitions Incorporated.deserialized/`

**Total Findings:**
- 11 deck definitions
- 8 unique sprite sheet images
- 354 total cards
- 327 PNG images in Images/ directory

## Sprite Sheet Dimensions

### Complete Analysis Table

| Deck ID | Grid (W×H) | Cards | Sheet Dimensions (px) | Per-Card Dimensions (px) | Card Ratio |
|---------|------------|-------|----------------------|-------------------------|------------|
| 169 | 10×2 | 13 | 9728 × 1350 | 972.8 × 675.0 | 1.44:1 (landscape) |
| 170 | 6×2 | 10 | 2816 × 1306 | 469.3 × 653.0 | 0.72:1 (portrait) |
| 172 | 10×7 | 65 | 4864 × 4728 | 486.4 × 675.4 | 0.72:1 (portrait) |
| 174 | 10×7 | 69 | 4864 × 4778 | 486.4 × 682.6 | 0.71:1 (portrait) |
| 175 | 10×7 | 52 | 4864 × 4776 | 486.4 × 682.3 | 0.71:1 (portrait) |
| 176 | 10×7 | 60 | 4864 × 4786 | 486.4 × 683.7 | 0.71:1 (portrait) |
| 178 | 10×5 | 21 | 4096 × 2848 | 409.6 × 569.6 | 0.72:1 (portrait) |
| 179 | 10×5 | 21 | 4096 × 2848 | 409.6 × 569.6 | 0.72:1 (portrait) |
| 180 | 10×5 | 21 | 4096 × 2848 | 409.6 × 569.6 | 0.72:1 (portrait) |
| 181 | 10×5 | 21 | 4096 × 2848 | 409.6 × 569.6 | 0.72:1 (portrait) |
| 182 | 1×1 | 1 | 496 × 694 | 496.0 × 694.0 | 0.71:1 (portrait) |

### Notes

**Shared Sprite Sheets:**
- Decks 178, 179, 180, 181 all share the same sprite sheet (4096×2848 px)
- This is a 10×5 grid with 50 positions
- Total of 84 cards across these 4 decks

**Unique Characteristics:**
- Deck 169: Landscape orientation (wider than tall)
- All other decks: Portrait orientation (standard card layout)
- Most cards follow ~0.71:1 ratio (standard playing card proportions)

## DPI Comparison with Standard Card Sizes

### Reference Card Sizes

**Standard Cards:** 63mm × 88mm (2.48" × 3.46")
**Large Cards:** 88mm × 125mm (3.46" × 4.92")

### DPI Calculation Table

| Deck ID | Per-Card (px) | Standard Card DPI | Large Card DPI | Print Quality Rating |
|---------|---------------|-------------------|----------------|---------------------|
| **169** | 972.8 × 675.0 | **392.2 × 195.1** | 278.9 × 138.6 | ⭐⭐⭐⭐⭐ Excellent |
| **170** | 469.3 × 653.0 | **189.2 × 188.7** | 134.4 × 134.1 | ⭐⭐⭐ Good |
| **172** | 486.4 × 675.4 | **196.1 × 195.2** | 139.3 × 138.6 | ⭐⭐⭐⭐ High |
| **174** | 486.4 × 682.6 | **196.1 × 197.3** | 139.3 × 140.1 | ⭐⭐⭐⭐ High |
| **175** | 486.4 × 682.3 | **196.1 × 197.2** | 139.3 × 140.0 | ⭐⭐⭐⭐ High |
| **176** | 486.4 × 683.7 | **196.1 × 197.6** | 139.3 × 140.3 | ⭐⭐⭐⭐ High |
| **178-181** | 409.6 × 569.6 | **165.2 × 164.6** | 117.3 × 116.9 | ⭐⭐ Acceptable |
| **182** | 496.0 × 694.0 | **200.0 × 200.6** | 142.1 × 142.4 | ⭐⭐⭐⭐ High |

### DPI Calculation Method

```
DPI = pixels / physical_inches

For Standard Cards (63×88mm = 2.48"×3.46"):
  DPI_width = card_width_pixels / 2.48
  DPI_height = card_height_pixels / 3.46

For Large Cards (88×125mm = 3.46"×4.92"):
  DPI_width = card_width_pixels / 3.46
  DPI_height = card_height_pixels / 4.92
```

## Detailed DPI Analysis

### Deck 169 - Landscape Cards (Highest Resolution)

**Dimensions:** 972.8 × 675.0 pixels per card

**Analysis:**
- Width DPI (standard): 392.2 DPI - Exceptional quality
- Height DPI (standard): 195.1 DPI - High quality
- These are landscape-oriented cards (wider than tall)
- Excellent for printing at standard size
- Good for printing at large size

**Note:** Asymmetric DPI suggests these cards have a very different aspect ratio from standard playing cards.

### Decks 172, 174, 175, 176 - High Resolution Portrait

**Dimensions:** ~486 × 682 pixels per card

**Standard Card DPI:** ~196 × 197 DPI
- Excellent balance between width and height
- Well above 150 DPI minimum for good print quality
- Perfect for standard card size (63×88mm)
- Acceptable for large card size (88×125mm)

**Large Card DPI:** ~139 × 140 DPI
- Borderline acceptable for professional printing
- Still usable for casual/prototype printing

### Deck 170 - Good Resolution Portrait

**Dimensions:** 469.3 × 653.0 pixels per card

**Standard Card DPI:** 189 × 189 DPI
- Uniform DPI across both dimensions
- Good print quality for standard cards
- Acceptable for large cards with some quality loss

### Decks 178-181 - Acceptable Resolution (Shared Sheet)

**Dimensions:** 409.6 × 569.6 pixels per card

**Standard Card DPI:** 165 × 165 DPI
- Acceptable for standard card size
- Above minimum 150 DPI threshold
- Suitable for casual/prototype printing

**Large Card DPI:** 117 × 117 DPI
- Below ideal quality for large cards
- May appear slightly pixelated at large size
- Use standard size for better quality

### Deck 182 - Single High-Quality Card

**Dimensions:** 496.0 × 694.0 pixels

**Standard Card DPI:** 200 × 201 DPI
- Excellent quality for a single card
- Perfect symmetry in DPI
- Professional print quality

## Print Quality Recommendations

### Quality Tiers

| Quality Tier | DPI Range | Decks | Recommendation |
|--------------|-----------|-------|----------------|
| **Excellent** (300+ DPI) | 300+ | 169 (width only) | Professional printing |
| **High** (190-250 DPI) | 196-201 | 172, 174, 175, 176, 182 | Professional printing for standard cards |
| **Good** (175-189 DPI) | 189 | 170 | Good for standard cards, acceptable for large |
| **Acceptable** (150-174 DPI) | 165 | 178-181 | Suitable for standard cards only |

### By Card Size

**For Standard Cards (63×88mm):**
- ✅ **All decks** meet or exceed 150 DPI minimum
- ⭐ **Best:** Decks 169, 172-176, 182 (195+ DPI)
- ✓ **Good:** Deck 170 (189 DPI)
- ✓ **Acceptable:** Decks 178-181 (165 DPI)

**For Large Cards (88×125mm):**
- ✅ **Recommended:** Decks 169, 172-176, 182 (138-195 DPI)
- ⚠️ **Use with caution:** Deck 170 (134 DPI)
- ❌ **Not recommended:** Decks 178-181 (117 DPI)

## Card Size Identification

Based on the per-card dimensions and DPI analysis:

### Standard Cards (63×88mm)
**Most cards in the set** - Decks 170, 172-176, 178-181, 182
- Per-card pixels: 409-496 width, 569-694 height
- Portrait orientation
- Standard playing card proportions (0.71:1 ratio)

### Landscape Cards
**Deck 169 only** - 13 cards
- Per-card pixels: 972.8 × 675.0
- Landscape orientation (1.44:1 ratio)
- Likely special game boards or reference cards

### Large Cards (88×125mm)
Based on the user's mention of 14 large cards, these could be:
- **Deck 169:** 13 cards (close to 14)
- Very high resolution in width dimension
- Landscape format suggests oversized/special cards

## Technical Details

### Image File Information

**Location:** `Images/` directory in deserialized folder
**Format:** PNG
**Total Files:** 327 images
**Sprite Sheets:** 8 unique files
**Deck Definitions:** 11 CustomDeck entries

### Metadata File

**Location:** `sprite_metadata.json`
**Contents:**
- CustomDeck definitions with FaceURL, BackURL
- Grid dimensions (NumWidth × NumHeight)
- Card positions used in each deck
- Local image paths

### Per-Card Calculation

```python
# For each sprite sheet:
card_width_px = sprite_width_px / NumWidth
card_height_px = sprite_height_px / NumHeight

# Example - Deck 172 (4864×4728, 10×7 grid):
card_width = 4864 / 10 = 486.4 px
card_height = 4728 / 7 = 675.4 px
```

## Summary Statistics

### Overall Quality
- **Average DPI (Standard):** ~195 DPI
- **Average DPI (Large):** ~139 DPI
- **Minimum DPI:** 165 DPI (standard cards)
- **Maximum DPI:** 392 DPI (deck 169 width)

### Resolution Distribution
- **High res (190+ DPI):** 6 decks (172-176, 182)
- **Good res (175-189 DPI):** 1 deck (170)
- **Acceptable res (150-174 DPI):** 4 decks (178-181)

### Card Count by Quality
- **High quality cards:** 247 cards (69.8%)
- **Good quality cards:** 10 cards (2.8%)
- **Acceptable quality cards:** 84 cards (23.7%)
- **Special cards:** 13 cards (3.7%)

## Recommendations

### For Professional Printing

**Best Results:**
1. Print Decks 172-176, 182 at **standard size (63×88mm)**
2. Print Deck 169 at **large size (88×125mm)** or custom size
3. Consider printing Decks 178-181 at standard size for acceptable quality

**Quality Settings:**
- Use 300+ DPI printer settings
- High-quality cardstock
- Color correction for accurate reproduction

### For Prototype/Casual Printing

**All decks acceptable** when printed at standard size (63×88mm):
- Decks 178-181 will have slightly lower quality but usable
- Use home inkjet or color laser printer
- Standard cardstock or photo paper

### For Large Format Printing

**Recommended:**
- Deck 169: Excellent for large format
- Decks 172-176, 182: Acceptable quality at 88×125mm

**Not Recommended:**
- Decks 178-181: Below optimal DPI for large format
- Deck 170: Borderline quality for large format

## Conclusion

The Clank Legacy sprite sheets show **high overall quality** with most cards (69.8%) exceeding 190 DPI for standard card printing. The shared sprite sheet for decks 178-181 provides acceptable quality at standard size, while the landscape cards in deck 169 offer exceptional resolution for oversized printing.

**Key Findings:**
1. Most cards are optimized for 63×88mm (standard) printing
2. Deck 169's landscape cards are likely the 14 large cards mentioned
3. Average ~195 DPI provides professional print quality
4. All cards meet minimum 150 DPI threshold for acceptable printing

---

**Analysis Date:** 2026-02-02
**Source Files:**
- `/Users/frankliu/Library/CloudStorage/Box-Box/Work/bg/clank_legacy/2083854795_Clank Legacy_ Acquisitions Incorporated.deserialized/sprite_metadata.json`
- Images directory with 327 PNG files
