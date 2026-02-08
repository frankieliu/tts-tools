# TTS Scaling System: Complete Analysis Across All Object Types

Comprehensive analysis of how TTS handles scaling for Cards, Tiles, Boards, and Tokens in Clank Legacy.

## Executive Summary

**Key Finding:** TTS uses **different scaling mechanisms** for different object types:

1. **Cards (sprite sheets):** Aspect ratio normalization (no Transform.scale variation)
2. **Tiles/Boards/Tokens:** Transform.scale with aspect ratio from image

Both systems work together to create a unified display where objects appear at appropriate relative sizes.

## Complete Object Inventory - Clank Legacy

### Cards (354 total)

All cards have **Transform.scale = (1.0, 1.0, 1.0)**

| Pixel Dimensions | Aspect Ratio | Count | Decks | Notes |
|------------------|--------------|-------|-------|-------|
| 410×570 px | 0.719 | 84 | 178-181 | Standard portrait |
| 469×653 px | 0.718 | 10 | 170 | Standard portrait |
| 486×675 px | 0.720 | 65 | 172 | Standard portrait |
| 486×682 px | 0.713 | 52 | 175 | Standard portrait |
| 486×683 px | 0.712 | 69 | 174 | Standard portrait |
| 486×684 px | 0.711 | 60 | 176 | Standard portrait |
| 496×694 px | 0.715 | 1 | 182 | Standard portrait |
| **973×675 px** | **1.441** | **13** | **169** | **Landscape (large cards)** |

**Observation:**
- 341 cards have aspect ratio ~0.71-0.72 (standard poker card)
- 13 cards have aspect ratio 1.44 (landscape, likely the 88×125mm large cards)
- ALL have same Transform.scale (1.0, 1.0, 1.0)
- Different pixel counts = different DPI, not different display size

### Tiles (141 total)

Transform.scale varies significantly: **0.59 to 200.00**

| Transform.scale | Image Dimensions | Aspect | Count | Examples |
|----------------|------------------|--------|-------|----------|
| (0.59, 0.59) | 155×160 px | 0.969 | 21 | minor tokens |
| (0.83, 0.83) | 212×214 px | 0.991 | 14 | major tokens |
| (0.90, 0.90) | ~240×220 px | ~1.08 | 20 | relics (varied dimensions) |
| (5.39, 5.39) | 2501×2000 px | 1.250 | 4 | Player mats |
| (6.08, 6.08) | 2000×1500 px | 1.333 | 1 | Play area |
| (7.41, 7.41) | 1648×2175 px | 0.758 | 2 | Charter |
| (9.61, 9.61) | 3899×2450 px | 1.591 | 1 | HQ board |
| (9.89, 9.89) | 3000×3496 px | 0.858 | 16 | Rule book |
| (10.52, 10.52) | 2600-3000×3100-3500 px | ~0.85 | 47 | Book of secrets (pages) |
| (22.00, 22.00) | 2600×3700 px | 0.700 | 2 | Main boards A&B |
| **(200.00, 200.00)** | **8000×8000 px** | **1.000** | **1** | **Background table** |

**Observation:**
- Transform.scale varies by 340x (from 0.59 to 200!)
- Image dimensions also vary significantly
- Aspect ratios range from 0.70 to 10.45 (stickers)

### Tokens (28 total)

Transform.scale ranges: **0.25 to 0.61**

| Transform.scale | Image Dimensions | Aspect | Count | Notes |
|----------------|------------------|--------|-------|-------|
| (0.25, 0.25) | 184×184 px | 1.000 | 2 | Small round tokens |
| (0.27, 0.27) | 187×163 px | 1.147 | 5 | Book tokens |
| (0.40, 0.40) | 155-156×155-159 px | ~1.00 | 6 | Medium tokens |
| (0.42, 0.42) | 156-161×154-159 px | ~1.00 | 10 | Medium tokens |
| (0.61, 0.61) | 250-257×252-256 px | ~1.00 | 6 | Large tokens |

**Observation:**
- All tokens have aspect ratio ~1.0 (square)
- Transform.scale controls physical size
- Higher resolution images (250px) have same scale as lower res (160px)
- Scale varies by 2.4x (0.25 to 0.61)

## The Unified Scaling System

### How TTS Calculates Display Size

**For ALL objects (cards, tiles, boards, tokens):**

```
1. Load image (from URL or extract from sprite sheet)
2. Calculate image aspect ratio: width_px / height_px
3. Apply Transform.scale:
   display_width = BASE_WIDTH * Transform.scaleX * aspect_ratio
   display_height = BASE_HEIGHT * Transform.scaleZ
4. Render at calculated size
```

**The key variables:**
- `BASE_WIDTH` and `BASE_HEIGHT`: TTS internal constants (not in JSON)
- `Transform.scaleX/Z`: Stored in JSON per object
- `aspect_ratio`: Calculated from image pixels

### Cards vs Tiles: The Difference

**Cards:**
- Always have Transform.scale = (1.0, 1.0, 1.0)
- Aspect ratio does ALL the work
- 0.72 aspect → portrait card
- 1.44 aspect → landscape card

**Tiles/Boards/Tokens:**
- Transform.scale varies greatly (0.25 to 200!)
- Aspect ratio still matters for proportions
- Scale controls absolute size
- Scale 200 = huge background
- Scale 0.25 = tiny token

## Display Size Calculations

### Example 1: Standard Cards (Different Pixels, Same Size)

**Deck 172 (high res):**
- Image: 486×675 px
- Aspect: 0.720
- Transform.scale: (1.0, 1.0)
- **Display: BASE × 1.0 × 0.720 = 0.720 BASE units wide**

**Deck 179 (lower res):**
- Image: 410×570 px
- Aspect: 0.719
- Transform.scale: (1.0, 1.0)
- **Display: BASE × 1.0 × 0.719 = 0.719 BASE units wide**

**Result:** Nearly identical display size (~0.1% difference)

### Example 2: Landscape Cards

**Deck 169 (large landscape cards):**
- Image: 973×675 px
- Aspect: 1.441
- Transform.scale: (1.0, 1.0)
- **Display: BASE × 1.0 × 1.441 = 1.441 BASE units wide**

**Result:** 2x wider than portrait cards (1.441 / 0.720 = 2.0)

### Example 3: Tokens (Same Aspect, Different Scales)

**Small token:**
- Image: 184×184 px
- Aspect: 1.000
- Transform.scale: (0.25, 0.25)
- **Display: BASE × 0.25 × 1.0 = 0.25 BASE units**

**Large token:**
- Image: 257×256 px
- Aspect: 1.004
- Transform.scale: (0.61, 0.61)
- **Display: BASE × 0.61 × 1.0 = 0.61 BASE units**

**Result:** Large token is 2.4x bigger than small token (0.61 / 0.25)

### Example 4: Game Boards vs Background

**Main board (Board A):**
- Image: 2644×3775 px
- Aspect: 0.700
- Transform.scale: (22.00, 22.00)
- **Display: BASE × 22.0 × 0.700 = 15.4 BASE units wide**

**Background table:**
- Image: 8000×8000 px
- Aspect: 1.000
- Transform.scale: (200.00, 200.00)
- **Display: BASE × 200.0 × 1.0 = 200 BASE units wide**

**Result:** Background is 13x wider than game board (200 / 15.4)

## The Missing Piece: BASE_WIDTH

**TTS has an internal BASE size that normalizes everything:**

```
BASE_WIDTH ≈ 1 TTS unit (arbitrary internal scale)
BASE_HEIGHT ≈ 1 TTS unit
```

**This base unit is NOT exposed in the JSON!**

### Inferring the Base Unit

From the data, we can infer:

**Cards with scale (1.0, 1.0) and aspect 0.72:**
- Display as "standard playing card size" in TTS
- We assume this is 2.5" × 3.5" (63×88mm)

**Therefore:**
```
BASE_WIDTH × 1.0 × 0.72 = 2.5"
BASE_WIDTH = 2.5 / 0.72 = 3.47"

BASE_HEIGHT × 1.0 = 3.5"
BASE_HEIGHT = 3.5"
```

**So roughly: 1 TTS unit ≈ 3.5 inches (for scaleZ)**

### Applying This to Tiles

**Player mat (scale 5.39, aspect 1.25):**
```
Width = 3.47" × 5.39 × 1.25 = 23.4" wide
Height = 3.5" × 5.39 = 18.9" tall
```

**Main board (scale 22.0, aspect 0.70):**
```
Width = 3.47" × 22.0 × 0.70 = 53.4" wide
Height = 3.5" × 22.0 = 77.0" tall
```

**Small token (scale 0.25, aspect 1.0):**
```
Width = 3.47" × 0.25 × 1.0 = 0.87" wide
Height = 3.5" × 0.25 = 0.87" tall
```

## Comparison Table: Relative Sizes in TTS

| Object Type | Example | Transform.scale | Aspect | Relative Width* | Relative Height* |
|-------------|---------|----------------|--------|----------------|------------------|
| Small token | Generic | 0.25 | 1.00 | 0.25 | 0.25 |
| Medium token | Book | 0.42 | 1.00 | 0.42 | 0.42 |
| Large token | Generic | 0.61 | 1.00 | 0.61 | 0.61 |
| Minor tile | Marker | 0.59 | 0.97 | 0.57 | 0.59 |
| Major tile | Marker | 0.83 | 0.99 | 0.82 | 0.83 |
| **Card (portrait)** | **Standard** | **1.00** | **0.72** | **0.72** | **1.00** |
| **Card (landscape)** | **Large** | **1.00** | **1.44** | **1.44** | **1.00** |
| Player mat | Blue/Red | 5.39 | 1.25 | 6.74 | 5.39 |
| HQ board | Game board | 9.61 | 1.59 | 15.3 | 9.61 |
| Rule book | Page | 9.89 | 0.86 | 8.50 | 9.89 |
| Charter | Document | 7.41 | 0.76 | 5.63 | 7.41 |
| Main board | Board A/B | 22.0 | 0.70 | 15.4 | 22.0 |
| Background | Table | 200.0 | 1.00 | 200 | 200 |

*Relative to BASE unit (standard card height = 1.00)

## Key Insights

### 1. Different pixel counts DON'T mean different display sizes

**Examples:**
- Deck 172: 486 px → displays same as
- Deck 179: 410 px → because aspect ratio is nearly identical

**Pixel count only affects print quality (DPI), not TTS display size.**

### 2. Transform.scale IS the primary size control for tiles/tokens

**Examples:**
- Token at scale 0.25 → tiny
- Token at scale 0.61 → medium
- Player mat at scale 5.39 → large
- Background at scale 200 → enormous

**Even with similar pixel counts, Transform.scale determines display size.**

### 3. Cards use a FIXED Transform.scale convention

**All cards:** Transform.scale = (1.0, 1.0, 1.0)

**Size variation comes from aspect ratio:**
- Portrait (0.72) → standard card
- Landscape (1.44) → 2x wider card

**This is a TTS convention, not a technical requirement.**

### 4. Aspect ratio matters for ALL objects

Even tiles with the same scale display differently based on aspect:

**Board A (scale 22, aspect 0.70):**
- Tall and narrow portrait orientation

**Background (scale 200, aspect 1.00):**
- Square

**HQ board (scale 9.61, aspect 1.59):**
- Wide landscape orientation

### 5. The BASE unit connects everything

**TTS has an internal normalization factor that makes:**
- Cards at scale 1.0 display as playing cards
- Tokens at scale 0.25-0.61 display as tokens
- Boards at scale 20+ display as boards

**This BASE unit is roughly 3.5 inches** (inferred from card sizes).

## Physical Print Sizes

### Converting TTS Scale to Physical Size

Using the inferred BASE unit (3.5" for height):

```
Physical Width (inches) = BASE_WIDTH × Transform.scaleX × (image_width / image_height)
Physical Height (inches) = BASE_HEIGHT × Transform.scaleZ

Where:
  BASE_WIDTH ≈ 3.47 inches
  BASE_HEIGHT ≈ 3.5 inches
```

### Print Size Table

| Object | Transform.scale | Aspect | Physical Size (inches) | Physical Size (mm) |
|--------|----------------|--------|----------------------|-------------------|
| Standard card | 1.0 | 0.72 | 2.5 × 3.5 | 63 × 88 |
| Large card | 1.0 | 1.44 | 5.0 × 3.5 | 127 × 88 |
| Small token | 0.25 | 1.00 | 0.87 × 0.87 | 22 × 22 |
| Medium token | 0.42 | 1.00 | 1.46 × 1.46 | 37 × 37 |
| Large token | 0.61 | 1.00 | 2.12 × 2.12 | 54 × 54 |
| Player mat | 5.39 | 1.25 | 23.4 × 18.9 | 594 × 480 |
| Main board | 22.0 | 0.70 | 53.4 × 77.0 | 1356 × 1956 |

**Note:** The large landscape cards (deck 169) appear to be oversized - they're 5" wide in TTS but likely meant to be printed at standard dimensions. The aspect ratio suggests these should be 88×125mm (3.5"×4.9") when rotated.

## Summary

### The Two Scaling Systems

**System 1: Cards (aspect ratio only)**
- Transform.scale fixed at 1.0
- Aspect ratio determines proportions
- BASE unit determines absolute size
- Result: Standard playing card display

**System 2: Tiles/Boards/Tokens (scale × aspect)**
- Transform.scale varies widely (0.25 to 200)
- Aspect ratio still affects proportions
- Result: Flexible sizing for any game component

### The Unified Formula

**For ALL TTS objects:**
```
display_width = BASE × scaleX × aspect_ratio
display_height = BASE × scaleZ
```

**Where:**
- BASE ≈ 3.5" (inferred from card sizes)
- scaleX/Z from Transform in JSON
- aspect_ratio from image pixels (width/height)

### The Answer

**"How does TTS scale objects with different pixel dimensions?"**

1. **Calculates aspect ratio** from image pixels
2. **Reads Transform.scale** from JSON
3. **Multiplies both** by internal BASE unit
4. **Renders at calculated size**

**Pixel dimensions affect print quality (DPI), not display size in TTS.**

---

**Analysis Date:** 2026-02-02
**Game:** Clank Legacy: Acquisitions Incorporated
**Objects Analyzed:** 354 cards, 141 tiles, 28 tokens, 0 boards (boards classified as tiles in this mod)
**Source:** 2083854795_Clank Legacy_ Acquisitions Incorporated.deserialized.json
