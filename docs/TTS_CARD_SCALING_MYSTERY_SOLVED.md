# How TTS Normalizes Card Display Across Different Sprite Sheets

## The Mystery

**Question:** Two sprite sheets have different pixel dimensions per card, but both display at the same size in TTS. How does TTS know how to scale them?

**Example from Clank Legacy:**
- Deck 172: 486×675 pixels per card
- Deck 179: 410×570 pixels per card
- Both have Transform.scale = (1.0, 1.0, 1.0)
- Both display at the same size in TTS

## Investigation Results

### What's in the JSON

**CustomDeck fields (complete list):**
```json
{
  "172": {
    "FaceURL": "http://...",
    "BackURL": "http://...",
    "NumWidth": 10,
    "NumHeight": 7,
    "BackIsHidden": false,
    "UniqueBack": false
  }
}
```

**Card Transform:**
```json
{
  "Transform": {
    "scaleX": 1.0,
    "scaleY": 1.0,
    "scaleZ": 1.0
  }
}
```

### What's NOT in the JSON

❌ No DPI field
❌ No physical dimensions (inches/mm)
❌ No pixel dimensions
❌ No image scale factor
❌ No aspect ratio specification

## The Answer: Aspect Ratio Normalization

**TTS uses the image's aspect ratio to determine physical display size.**

### How It Works

**Deck 172:**
- Sprite sheet: 4864 × 4728 pixels
- Grid: 10 × 7
- Per-card: 486.4 × 675.4 pixels
- **Aspect ratio: 0.720:1**

**Deck 179:**
- Sprite sheet: 4096 × 2848 pixels
- Grid: 10 × 5
- Per-card: 409.6 × 569.6 pixels
- **Aspect ratio: 0.719:1**

**Both have essentially the same aspect ratio (~0.72:1 = standard playing card proportions)**

### TTS Display Algorithm

```
1. Load sprite sheet image
2. Extract card at grid position (CardID % 100)
3. Calculate card aspect ratio: width/height
4. Apply Transform.scale multipliers
5. Display card with calculated aspect ratio at normalized size
```

**Key insight:** TTS doesn't care about absolute pixels, only the **aspect ratio** of the extracted card image.

### Standard Card Aspect Ratios

| Card Size | Dimensions | Aspect Ratio |
|-----------|------------|--------------|
| Poker (Standard) | 63×88mm (2.5"×3.5") | 0.714:1 |
| Bridge | 57×89mm (2.25"×3.5") | 0.640:1 |
| Tarot | 70×120mm (2.75"×4.75") | 0.583:1 |
| Mini Euro | 44×68mm (1.73"×2.68") | 0.647:1 |
| Standard Euro | 59×92mm (2.32"×3.62") | 0.641:1 |

**Clank Legacy cards: 0.72:1 aspect ratio ≈ Poker size**

## Why Different Pixel Counts?

Different sprite sheets can have different resolutions (DPI) but maintain the same aspect ratio:

**Deck 172: Higher DPI**
- 486×675 pixels → 196 DPI @ 63×88mm
- Better print quality

**Deck 179: Lower DPI**
- 410×570 pixels → 165 DPI @ 63×88mm
- Acceptable print quality

**Both display identically in TTS because:**
1. Same aspect ratio (0.72:1)
2. Same Transform.scale (1.0, 1.0, 1.0)
3. TTS normalizes based on aspect ratio, not pixels

## Transform.scale Effect

The Transform.scale DOES affect display size, but proportionally:

```
If Transform.scale = (2.0, 1.0, 2.0):
  Card appears 2x wider and 2x taller in TTS

If Transform.scale = (1.0, 1.0, 1.0):
  Card appears at "standard" size

The "standard" size is determined by aspect ratio
```

## Converting Pixels to Physical Size

Since TTS doesn't provide absolute sizing, we must use conventions:

### Method 1: Standard Card Reference
```
Assume cards are standard poker size (63×88mm)

For 486×675 pixel card:
  DPI = 486 / (63/25.4) = 196 DPI

For 410×570 pixel card:
  DPI = 410 / (63/25.4) = 165 DPI
```

### Method 2: Card Aspect Ratio Matching
```
1. Measure aspect ratio from pixels
2. Match to known card size
3. Calculate DPI

Deck 172: 486/675 = 0.720
  Closest match: Poker (0.714)
  Assume: 63×88mm
  DPI: 196
```

### Method 3: User Measurement
```
1. Print test card at actual sprite resolution
2. Measure physical dimensions
3. Calculate back to intended size
4. Determine DPI
```

## Implications for Printing

### The Problem

**TTS JSON alone cannot tell you the intended physical print size.**

You need external information:
- Game manufacturer specifications
- Community knowledge
- Reference measurements
- Standard card size assumptions

### The Solution

**For Clank Legacy:**
- Aspect ratio 0.72:1 → Standard poker cards
- Assume 63×88mm (2.5"×3.5")
- Calculate DPI from pixel dimensions
- Print at 2.5"×3.5" to match aspect ratio

**Why it works:**
- Maintains correct aspect ratio
- Matches standard card sleeves
- Consistent with board game industry standard

## Technical Details

### How TTS Renders Cards

```
1. CardID decode:
   deck_id = CardID // 100
   position = CardID % 100

2. Load sprite sheet:
   image = load(CustomDeck[deck_id].FaceURL)

3. Extract card rectangle:
   col = position % NumWidth
   row = position // NumWidth
   card_image = crop(image, col, row)

4. Get image aspect ratio:
   aspect = card_image.width / card_image.height

5. Apply Transform.scale:
   display_width = base_width * Transform.scaleX * aspect
   display_height = base_height * Transform.scaleZ

6. Render at calculated size
```

**Note:** `base_width` and `base_height` are TTS internal constants not exposed in JSON.

### Why This System Works

**Advantages:**
- Flexible: Supports any aspect ratio
- Simple: No complex sizing metadata needed
- Automatic: Aspect ratio extracted from image
- Consistent: Same aspect = same display size

**Disadvantages:**
- No absolute sizing information
- Can't determine intended physical print size
- Must rely on conventions and assumptions
- Different DPI possible for same display size

## Comparison: Cards vs Tiles

| Aspect | Cards | Tiles/Boards/Tokens |
|--------|-------|---------------------|
| **Size info in JSON** | Only aspect ratio (from image) | Transform.scale values |
| **Print size** | Convention-based (2.5"×3.5") | scale × scale_factor |
| **Display in TTS** | Normalized by aspect ratio | Directly from Transform.scale |
| **DPI matters?** | No (for TTS display) | No (for TTS display) |
| **Print flexibility** | Fixed aspect ratio | Fully adjustable |

## Summary

### Key Findings

1. **No absolute sizing in JSON** - Only aspect ratio matters
2. **Aspect ratio determines display** - Not pixel dimensions
3. **Transform.scale is relative** - Multiplies the normalized size
4. **Print size is conventional** - Based on aspect ratio matching
5. **DPI only matters for printing** - Not for TTS display

### For Clank Legacy

**Both decks 172 and 179:**
- Aspect ratio: ~0.72:1 (poker card proportions)
- Transform.scale: (1.0, 1.0, 1.0)
- Display at same size in TTS
- Different DPI (196 vs 165)
- Both print at 63×88mm (2.5"×3.5")

**The "magic" is aspect ratio normalization, not hidden metadata!**

### Practical Takeaway

When printing TTS cards:
1. Extract aspect ratio from sprite sheet
2. Match to standard card size
3. Calculate DPI
4. Print at matched physical size
5. Ignore absolute pixel dimensions for sizing (use for quality only)

---

**Date:** 2026-02-02
**Analysis:** Clank Legacy TTS mod
**Files analyzed:** 2083854795_Clank Legacy_ Acquisitions Incorporated.deserialized.json
