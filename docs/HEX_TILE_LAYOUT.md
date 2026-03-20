# Hex Tile Layout Guide

## Overview

Many board games use hexagonal tiles — voting tokens, terrain pieces, resource markers. The `tts-generate-tiles-pdf` tool supports two hex layout modes for printing these as tightly-packed hex grids with outlines, ready for cutting.

**Preferred mode: `--hex-strip`** — used for most hex tile printing.

## Hex Strip Layout (`--hex-strip`)

Flat-top hexagons arranged in horizontal rows. Each row is offset horizontally by half a hex width, so hexes nestle together with 6 neighbors each. Small triangular gaps appear between three adjacent hexes.

```
    ___     ___     ___     ___
   /   \   /   \   /   \   /   \      ← Row 0
  / A   \ / B   \ / C   \ / D   \
  \     / \     / \     / \     /
   \___/   \___/   \___/   \___/
      /   \   /   \   /   \
     / E   \ / F   \ / G   \          ← Row 1 (offset right by ½ hex)
     \     / \     / \     /
      \___/   \___/   \___/
   /   \   /   \   /   \   /   \
  / H   \ / I   \ / J   \ / K   \     ← Row 2
  \     / \     / \     / \     /
   \___/   \___/   \___/   \___/
```

### Geometry

- **Hex orientation**: Flat-top (long diagonal horizontal)
- **Horizontal step**: Full hex width (pointy tips touching)
- **Row offset**: Odd rows shifted right by half a hex width
- **Vertical step**: Full hex height (rows don't overlap)
- **Gaps**: Small equilateral triangles between three adjacent hexes

### Styling

- **Page background**: Creamy yellow (`RGB 0.98, 0.95, 0.85`) — matches typical rulebook backgrounds
- **Hex outlines**: Warm brown (`RGB 0.55, 0.45, 0.30`), 1pt line width
- **Image clipping**: Circular clip mask (radius = 45% of hex cell size), centered on each hex cell
- **Transparency**: Alpha channel preserved — images with transparent backgrounds show the creamy page beneath

### Usage

```bash
# Basic hex strip (most common)
tts-generate-tiles-pdf Workshop/*.json --hex-strip

# Tiles only (exclude tokens/boards from separate pages)
tts-generate-tiles-pdf Workshop/*.json --hex-strip --tiles-only
```

## Honeycomb Grid Layout (`--hex-grid`)

Alternative layout where hexes are arranged in columns. Odd columns are offset vertically by half a hex height. Same styling as hex strip.

```bash
tts-generate-tiles-pdf Workshop/*.json --hex-grid
```

Use this when vertical column alignment is preferred over horizontal row alignment.

## Auto-Detection

The tool automatically detects which items should go on the hex grid:

1. **Square-ish images**: `abs(width - height) <= 5` pixels
2. **RGBA mode**: Image has an alpha channel (transparency)

Items matching both criteria are placed on the hex grid. All others go into standard rectangular packing on separate pages.

### Common hex tile types in TTS

| TTS Object | Typical Image | Detected as hex? |
|---|---|---|
| Round voting tokens | ~165×165 RGBA | Yes |
| Circular resource markers | ~200×200 RGBA | Yes |
| Hex terrain tiles | ~300×300 RGBA | Yes |
| Rectangular standees | ~180×320 RGBA | No (not square) |
| Board images | ~1500×2100 RGB | No (not RGBA) |

## Including Non-Hex Items in the Grid

Use `--hex-include` to pull additional tokens into the hex grid by nickname pattern matching:

```bash
# Include tokens whose nickname contains "Moai" or "Shell"
tts-generate-tiles-pdf Workshop/*.json --hex-strip --hex-include Moai Shell
```

Matched tokens are drawn on a **clay-red hex background** (`RGB 0.55, 0.22, 0.12`) to visually distinguish them from auto-detected hex tiles. The matching is case-insensitive substring.

## Handling TTS Infinite Bags

TTS `Infinite_Bag` containers store a single template item that players can pull unlimited copies from. For printing, you need to specify how many copies to create.

### Problem

A mod has 14 rank-I tokens loose on the table + 1 rank-I template in an Infinite_Bag. The physical game has 60 rank-I tokens total.

### Solution

Use `--infinite-count N` on `tts-extract-tiles` to multiply items from Infinite_Bags:

```bash
# Step 1: Extract with 46 copies from infinite bag (14 loose + 46 = 60)
tts-extract-tiles Workshop/*.json --infinite-count 46

# Step 2: Generate hex grid
tts-generate-tiles-pdf Workshop/*.json --hex-strip --tiles-only
```

The `--infinite-count` value is: `(desired_total - loose_count)`.

### Identifying Infinite Bag contents

Check the TTS JSON for `Infinite_Bag` objects to see what template items they contain and how many loose copies exist elsewhere. The extract tool's output summary shows total counts after multiplication.

## Complete Example: Zoo Vadis

Zoo Vadis has round voting tokens with Roman numerals (I through V):

| Rank | Count | In TTS JSON |
|------|-------|-------------|
| I | 60 | 14 loose + 1 in Infinite_Bag |
| II (4 flavors) | 15 | 15 in Bag |
| III | 12 | 12 in Bag |
| IV | 9 | 9 in Bag |
| V | 6 | 6 in Bag |
| **Total** | **102** | |

```bash
cd ~/Projects/bg/Zoo\ Vadis/<mod>.deserialized/

# Extract with 46 infinite bag copies (14 + 46 = 60 rank-I tokens)
tts-extract-tiles Workshop/*.json --infinite-count 46

# Generate hex strip PDF for tiles only
tts-generate-tiles-pdf Workshop/*.json --hex-strip --tiles-only
```

Result: 103 tiles on hex grid (102 voting tokens + 1 start marker), creamy yellow background, circular clipping, warm brown hex outlines.

## Tips

- **`--tiles-only`**: Use this with hex modes to keep rectangular tokens (standees, figures) on separate pages with standard packing
- **No `--group`**: By default all copies print individually — essential for hex tiles where you need every instance
- **Scale factor**: Auto-detected from card decks. If no cards exist in the mod, use `--scale-factor` manually
- **Large items**: Items exceeding the small-item threshold (default 4") are excluded from the hex grid and placed one-per-page
