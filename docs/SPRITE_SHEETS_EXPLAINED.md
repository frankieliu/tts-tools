# TTS Sprite Sheets: Complete Guide

Understanding how Tabletop Simulator uses sprite sheets to store and reference individual cards.

## Overview

Unlike tiles, boards, and tokens which use direct image URLs, **cards in TTS use sprite sheets** - a single large image containing multiple cards arranged in a grid. TTS uses a positioning system to identify which card to extract from the sprite sheet.

## Key Concept: No Per-Card Transforms

**Important:** Individual cards in sprite sheets do **NOT** have scale transforms that affect print size or extraction. Instead, TTS uses:

- **Grid position** to identify which card to extract
- **Fixed print size** (2.5" × 3.5" poker card standard)
- **Grid dimensions** to calculate pixel coordinates

## The CustomDeck Structure

Each sprite sheet is defined in a `CustomDeck` object within the TTS JSON:

```json
{
  "CustomDeck": {
    "25": {
      "FaceURL": "https://steamusercontent.com/ugc/123/faces.png",
      "BackURL": "https://steamusercontent.com/ugc/123/backs.png",
      "NumWidth": 10,
      "NumHeight": 7,
      "BackIsHidden": false,
      "UniqueBack": true,
      "Type": 0
    }
  }
}
```

### CustomDeck Fields

| Field | Type | Description |
|-------|------|-------------|
| Deck ID | String | Key for this deck (e.g., "25") |
| `FaceURL` | String | URL to sprite sheet with card faces |
| `BackURL` | String | URL to card backs (single image or sprite sheet) |
| `NumWidth` | Integer | Number of cards horizontally in grid |
| `NumHeight` | Integer | Number of cards vertically in grid |
| `BackIsHidden` | Boolean | Whether backs are hidden by default |
| `UniqueBack` | Boolean | If true, BackURL is a sprite sheet with unique backs |
| `Type` | Integer | Card shape: 0=Standard, 1=Square, 2=Hex |

**Grid size:** `NumWidth × NumHeight = Total positions available`

**Example:** `10 × 7 = 70` positions (0 through 69)

## CardID: The Positioning System

Every card in TTS has a `CardID` that encodes both the deck it belongs to and its position in the sprite sheet grid.

### CardID Format: DDDPP

```
CardID = DDDPP
  DDD = Deck ID (first 1-3 digits)
  PP = Position in sprite sheet (last 2 digits, 0-based)
```

### Decoding CardID

**Example: CardID = 2537**

```python
deck_id = card_id // 100        # 2537 // 100 = 25
grid_position = card_id % 100   # 2537 % 100 = 37
```

**Result:**
- References CustomDeck "25"
- Position 37 in that sprite sheet

### More Examples

| CardID | Deck ID | Grid Position | Notes |
|--------|---------|---------------|-------|
| 801 | 8 | 1 | Deck 8, position 1 |
| 2500 | 25 | 0 | Deck 25, first card (position 0) |
| 2537 | 25 | 37 | Deck 25, position 37 |
| 2569 | 25 | 69 | Deck 25, last card in 10×7 grid |
| 10015 | 100 | 15 | Deck 100, position 15 |

## Grid Position to Row/Column

Once you have the grid position, calculate the row and column using the grid dimensions:

```python
col = position % grid_width
row = position // grid_width
```

### Example: Position 37 in 10×7 Grid

```python
NumWidth = 10   # Cards per row
NumHeight = 7   # Number of rows

position = 37
col = 37 % 10  # = 7 (8th column, 0-indexed)
row = 37 // 10 # = 3 (4th row, 0-indexed)
```

### Visual Grid Layout

```
Grid: 10 cards wide × 7 cards tall (positions 0-69)

Position:  0    1    2    3    4    5    6    7    8    9
Row 0:   [00] [01] [02] [03] [04] [05] [06] [07] [08] [09]
Row 1:   [10] [11] [12] [13] [14] [15] [16] [17] [18] [19]
Row 2:   [20] [21] [22] [23] [24] [25] [26] [27] [28] [29]
Row 3:   [30] [31] [32] [33] [34] [35] [36] [37]★<-- [39]
Row 4:   [40] [41] [42] [43] [44] [45] [46] [47] [48] [49]
Row 5:   [50] [51] [52] [53] [54] [55] [56] [57] [58] [59]
Row 6:   [60] [61] [62] [63] [64] [65] [66] [67] [68] [69]

Position 37 ★ is at Row 3, Column 7
```

**Reading order:** Left-to-right, top-to-bottom (row-major order)

## Extracting a Card from Sprite Sheet

Once you know the row and column, calculate pixel coordinates to crop the card image.

### Extraction Algorithm

**From generate_deck_from_json.py:54-97**

```python
def extract_card_from_sprite_sheet(
    sprite_image: Image.Image,
    grid_width: int,        # NumWidth from CustomDeck
    grid_height: int,       # NumHeight from CustomDeck
    position: int           # Calculated from CardID % 100
) -> Image.Image:
    """Extract a single card from a sprite sheet."""

    # Get sprite sheet dimensions in pixels
    sprite_width, sprite_height = sprite_image.size
    # Example: 4096 × 2867 pixels

    # Calculate individual card dimensions in pixels
    card_pixel_width = sprite_width // grid_width
    card_pixel_height = sprite_height // grid_height
    # Example: 4096 / 10 = 409.6px wide
    #          2867 / 7  = 409.6px tall

    # Calculate card position in grid
    col = position % grid_width      # 37 % 10 = 7
    row = position // grid_width     # 37 // 10 = 3

    # Calculate pixel coordinates for cropping
    left = col * card_pixel_width    # 7 × 409.6 = 2867px
    top = row * card_pixel_height    # 3 × 409.6 = 1229px
    right = left + card_pixel_width  # 2867 + 409.6 = 3277px
    bottom = top + card_pixel_height # 1229 + 409.6 = 1639px

    # Extract the card by cropping
    card = sprite_image.crop((left, top, right, bottom))

    return card  # Returns 409×409 pixel image of this card
```

### Step-by-Step Example

**Given:**
- Sprite sheet: 4096 × 2867 pixels
- Grid: 10 × 7 cards
- CardID: 2537 (position 37)

**Steps:**

1. **Calculate card size:**
   - Width: 4096 ÷ 10 = 409.6 px per card
   - Height: 2867 ÷ 7 = 409.6 px per card

2. **Find row and column:**
   - Column: 37 % 10 = 7
   - Row: 37 ÷ 10 = 3

3. **Calculate crop box:**
   - Left: 7 × 409.6 = 2867 px
   - Top: 3 × 409.6 = 1229 px
   - Right: 2867 + 409.6 = 3277 px
   - Bottom: 1229 + 409.6 = 1639 px

4. **Crop image:**
   - Extract rectangle (2867, 1229, 3277, 1639)
   - Result: 409 × 409 px card image

5. **Print at standard size:**
   - Scale to 2.5" × 3.5" at 300 DPI
   - Final size: 750 × 1050 pixels

## Complete JSON Example

Here's a full example showing how a card references a sprite sheet:

```json
{
  "ObjectStates": [
    {
      "Name": "Card",
      "GUID": "abc123",
      "CardID": 2537,
      "Nickname": "Ace of Spades",
      "Description": "The highest card",

      "Transform": {
        "posX": 0,
        "posY": 1,
        "posZ": 0,
        "rotX": 0,
        "rotY": 180,        // Face down
        "rotZ": 0,
        "scaleX": 1,        // TTS display scale only!
        "scaleY": 1,        // Does NOT affect print size
        "scaleZ": 1
      },

      "CustomDeck": {
        "25": {
          "FaceURL": "https://steamusercontent.com/ugc/123/faces.png",
          "BackURL": "https://steamusercontent.com/ugc/123/backs.png",
          "NumWidth": 10,
          "NumHeight": 7,
          "BackIsHidden": false,
          "UniqueBack": true,
          "Type": 0
        }
      },

      "SidewaysCard": false,
      "Hands": true,
      "Locked": false
    }
  ]
}
```

**Processing this card:**

1. **CardID 2537** → Deck "25", Position 37
2. **Load FaceURL** → Download sprite sheet image
3. **Calculate position** → Row 3, Column 7
4. **Extract pixels** → Crop (2867, 1229, 3277, 1639)
5. **Print** → Scale to 2.5" × 3.5"

## Transform.scale on Cards

The `Transform.scaleX/Y/Z` fields on card objects affect how the card appears **in the TTS game**, not the print size or sprite extraction.

### What Transform Does

```json
{
  "Name": "Card",
  "CardID": 801,
  "Transform": {
    "scaleX": 2.0,    // Makes card appear 2x bigger in TTS
    "scaleY": 1.0,
    "scaleZ": 2.0     // Makes card appear 2x taller in TTS
  }
}
```

**In TTS:** This card appears as a giant 2x sized card on the table

**When printed:** Still prints at standard 2.5" × 3.5" size

**The card printing tools ignore Transform.scale** and use a fixed poker card size convention.

## Cards vs Tiles: Key Differences

| Aspect | Cards (Sprite Sheets) | Tiles/Boards/Tokens |
|--------|----------------------|---------------------|
| **Image source** | Single sprite sheet | Individual image URL per item |
| **Identification** | CardID + Grid position | Direct image URL |
| **Extraction** | Requires grid math and cropping | Direct image use |
| **Transform.scale** | Affects TTS display only | Defines print size via formula |
| **Print size** | Fixed 2.5" × 3.5" poker card | `scale × scale_factor` |
| **Grid system** | Yes (NumWidth × NumHeight) | No grid system |
| **Multiple instances** | Same CardID can appear many times | Each token tracked separately |

### Why This Matters

**For cards:** You cannot change print size with `--scale-factor` because card tools use hardcoded 2.5" × 3.5" dimensions.

**For tiles/tokens:** You can adjust print size with `--scale-factor` because they use the `scale × scale_factor` formula.

## UniqueBack System

When `UniqueBack: true`, both face and back sprite sheets use the **same grid layout**.

### Standard Back (UniqueBack: false)

```json
{
  "FaceURL": "https://.../faces.png",     // 10×7 grid of card faces
  "BackURL": "https://.../single_back.png", // Single image
  "UniqueBack": false
}
```

**All cards use the same back image.**

### Unique Backs (UniqueBack: true)

```json
{
  "FaceURL": "https://.../faces.png",  // 10×7 grid of card faces
  "BackURL": "https://.../backs.png",  // 10×7 grid of card backs
  "UniqueBack": true
}
```

**Each card has a unique back at the same position.**

### Visual Example

```
FaceURL sprite sheet (10×7):          BackURL sprite sheet (10×7):
┌────┬────┬────┬────┐                ┌────┬────┬────┬────┐
│ F0 │ F1 │ F2 │ F3 │ ...            │ B0 │ B1 │ B2 │ B3 │ ...
├────┼────┼────┼────┤                ├────┼────┼────┼────┤
│F10 │F11 │F12 │F13 │ ...            │B10 │B11 │B12 │B13 │ ...
├────┼────┼────┼────┤                ├────┼────┼────┼────┤
│F20 │F21 │F22 │F23 │ ...            │B20 │B21 │B22 │B23 │ ...
└────┴────┴────┴────┘                └────┴────┴────┴────┘

CardID 2537 (position 37):
- Face: Extract position 37 from FaceURL → Card face image
- Back: Extract position 37 from BackURL → Matching back image
```

**This allows double-sided printing** where each card has its own unique artwork on both sides.

### Printing Double-Sided Cards

For double-sided printing with unique backs:

1. **Generate face PDF:** Extract all face images at their positions
2. **Generate back PDF:** Extract all back images at their positions
3. **Mirror backs:** Flip back PDF horizontally for proper alignment
4. **Print:** Print faces, flip paper, print backs

The tools handle the mirroring automatically so backs align correctly when printed on the reverse side.

## Deck Objects

A `Deck` object contains multiple cards stacked together:

```json
{
  "Name": "Deck",
  "GUID": "deck123",
  "Nickname": "Player Deck",

  "DeckIDs": [2500, 2501, 2502, 2503, 2537],

  "CustomDeck": {
    "25": {
      "FaceURL": "https://.../faces.png",
      "BackURL": "https://.../backs.png",
      "NumWidth": 10,
      "NumHeight": 7
    }
  },

  "ContainedObjects": [
    {
      "Name": "Card",
      "CardID": 2500,
      "Nickname": "Card 1"
    },
    {
      "Name": "Card",
      "CardID": 2501,
      "Nickname": "Card 2"
    },
    {
      "Name": "Card",
      "CardID": 2502,
      "Nickname": "Card 3"
    },
    {
      "Name": "Card",
      "CardID": 2503,
      "Nickname": "Card 4"
    },
    {
      "Name": "Card",
      "CardID": 2537,
      "Nickname": "Ace of Spades"
    }
  ]
}
```

**Key fields:**
- `DeckIDs`: Array of all CardIDs in the deck (determines quantity)
- `ContainedObjects`: Full card objects with nicknames and properties
- `CustomDeck`: Shared sprite sheet definition

**Processing decks:**
- Extract all CardIDs from `DeckIDs` array
- Each CardID represents one card instance
- Duplicate CardIDs = multiple copies of that card

## Counting Card Instances

**From generate_deck_from_json.py:20-51:**

```python
def extract_card_ids_from_json(json_file: Path) -> list:
    """
    Extract all card instances from TTS JSON.
    Returns list of CardIDs (with duplicates).
    """
    card_ids = []

    def traverse(obj):
        if isinstance(obj, dict):
            # Deck with multiple cards
            if 'DeckIDs' in obj:
                card_ids.extend(obj['DeckIDs'])

            # Single card
            elif 'CardID' in obj and 'CustomDeck' in obj:
                card_ids.append(obj['CardID'])

            # Recurse
            for value in obj.values():
                traverse(value)

        elif isinstance(obj, list):
            for item in obj:
                traverse(item)

    traverse(data)
    return card_ids
```

**Example output:**
```python
card_ids = [2500, 2501, 2501, 2501, 2502, 2537]
#                    ↑     ↑     ↑
#                    Three copies of card 2501
```

**Counting duplicates:**
```python
from collections import Counter

card_counts = Counter(card_ids)
# Result: {2500: 1, 2501: 3, 2502: 1, 2537: 1}
```

This tells you how many copies of each card to print.

## Code Reference

### Extraction Functions

**Located in:** `src/extract_sprites.py`

**Key functions:**
- `find_sprite_sheets()` - Recursively find all CustomDeck definitions (lines 29-123)
- `extract_filename_from_url()` - Get image filename from URL (line 22)
- `find_local_image_file()` - Find downloaded sprite sheet (lines 186-212)

**Located in:** `src/generate_deck_from_json.py`

**Key functions:**
- `extract_card_ids_from_json()` - Get all card instances (lines 20-51)
- `extract_card_from_sprite_sheet()` - Crop card from sprite (lines 54-97)
- `draw_card_with_marks()` - Draw card with crop marks (lines 100+)

## Summary

### How Sprite Sheets Work

1. **CustomDeck defines grid:** NumWidth × NumHeight layout
2. **CardID encodes position:** DDDPP format (deck + position)
3. **Grid math calculates row/col:** Using modulo and division
4. **Pixel coordinates extracted:** Based on card size and position
5. **Image cropped:** Extract rectangle from sprite sheet
6. **Printed at fixed size:** 2.5" × 3.5" poker card standard

### Key Points

- **No per-card transforms** affect extraction or print size
- **CardID is the key** to finding cards in sprite sheets
- **Grid position** uses row-major order (left-to-right, top-to-bottom)
- **Transform.scale** affects TTS display, not printing
- **UniqueBack** enables double-sided printing with unique backs
- **Card print size is fixed** at 2.5" × 3.5" (not affected by `--scale-factor`)

### Workflow

```bash
# 1. Extract sprite sheet metadata
python src/extract_sprites.py Workshop/game.json -o sprite_metadata.json

# 2. Generate card PDFs (uses 2.5" × 3.5" fixed size)
python src/generate_deck_from_json.py Workshop/game.json -o cards.pdf

# Result: Print-ready PDF with all cards at poker size
```

---

**Related Documentation:**
- [PRINTING_GUIDE.md](PRINTING_GUIDE.md) - For tiles, boards, and tokens
- [TTS_JSON_STRUCTURE.md](TTS_JSON_STRUCTURE.md) - Complete JSON reference
- [TILES_AND_BOARDS.md](TILES_AND_BOARDS.md) - Scale system for tiles

**File paths referenced:**
- `/src/extract_sprites.py` - Sprite sheet metadata extraction
- `/src/generate_deck_from_json.py` - Card PDF generation
