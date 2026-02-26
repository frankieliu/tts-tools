# Composite Deck Keys and Tile Layout Improvements

## Date: 2026-02-24

## Summary

Two sets of changes: (1) fixed a bug where the same deck ID mapping to multiple sprite sheets caused incorrect card extraction, and (2) improved tile PDF layout with proper page fitting and automatic landscape rotation.

---

## Change 1: Composite Deck Keys for Sprite Sheets

### Problem

In TTS, a single deck ID (e.g. `17`) can appear in multiple card objects, each with a **different** `CustomDeck` entry pointing to a different FaceURL, grid size, etc. For example, deck 17 in the Earthborne Rangers mod maps to 5 different sprite sheet images:

| Deck ID | Grid | FaceURL hash (truncated) |
|---------|------|--------------------------|
| 17 | 4x4 | `0D55CFFC...` |
| 17 | 1x1 | `EF14BCDB...` |
| 17 | 5x5 | `818FC395...` |
| 17 | 8x5 | `3FD6DE33...` |
| 17 | 1x1 | `EE00AF11...` |

Previously, `extract_sprites.py` keyed sprite sheets by `deck_id` alone and only stored the **first** FaceURL encountered, discarding the rest. This caused cards to be extracted from the wrong sprite sheet, producing incorrect cards.

### Solution

**`src/extract_sprites.py` — `find_sprite_sheets()`:**

Changed the dict key from `deck_id_str` to a composite key `f"{deck_id_str}:{face_url_id}"`, where `face_url_id` is the hash extracted from the FaceURL. Each unique (deck_id, FaceURL) combination now gets its own entry with correct grid dimensions and card positions.

Example keys in `sprite_metadata.json`:
```
Before: "17"
After:  "17:0D55CFFCC54BB1209F693A0C74566BF9226ED52C"
        "17:EF14BCDB5553B675BDF86E0EED13A50063D9306E"
        "17:818FC395FAB1047DAC21F93BFE82B63BD59B5DC9"
        ...
```

**`src/generate_deck_from_json.py` — `extract_card_ids_from_json()`:**

Changed return type from a flat list of CardIDs to a list of `(card_id, face_url_id)` tuples. For each card, the FaceURL is captured from the card's own `CustomDeck` entry.

**`src/generate_deck_from_json.py` — `generate_deck_pdf()`:**

Updated sprite sheet lookup to construct the composite key `f"{deck_id_str}:{face_url_id}"`. Added two fallback strategies:
1. Search all sprite sheets by `face_url_id` alone (handles TTS quirk where `CustomDeck` key doesn't match `CardID // 100`)
2. Fall back to plain `deck_id_str` for backward compatibility with old metadata files

### TTS Quirk: Mismatched CustomDeck Keys

Discovered that TTS sometimes uses a `CustomDeck` key that doesn't match the deck ID derived from `CardID // 100`. For example, CardID 3127 has `deck_id = 31` (from `3127 // 100`), but its `CustomDeck` entry is keyed as `"26"`. The fallback search by `face_url_id` handles this case.

### Files Modified

- `src/extract_sprites.py` — composite key in `find_sprite_sheets()`
- `src/generate_deck_from_json.py` — added `extract_filename_from_url()`, updated `extract_card_ids_from_json()` return type, updated `generate_deck_pdf()` lookup logic

---

## Change 2: Tile PDF Page Fitting and Landscape Rotation

### Problem

Large tiles were constrained to a fixed `max_size` of 10.0 inches, but the usable width on a letter page is only 7.5 inches (8.5" minus 0.5" margins on each side). This caused tiles to overflow the page boundaries.

Additionally, all tiles were printed on portrait pages regardless of the image's actual aspect ratio, and TTS `stretch: true` forced landscape images into square print dimensions.

### Solution

**`src/generate_tiles_pdf.py` — `generate_tiles_pdf()`:**

Three improvements:

1. **Page-aware constraining:** In addition to the existing `max_size` constraint, large items are further constrained to the actual available area of their target page orientation (portrait: 7.5" x 10.0", landscape: 10.0" x 7.5").

2. **Image aspect ratio preservation:** For large items, the image's native aspect ratio is used to determine print dimensions instead of the TTS square scale values. This prevents landscape images from being printed as squares.

3. **Automatic landscape rotation:** Large items with landscape images (width > height) are printed on landscape-oriented pages, giving them up to 10" of width. Portrait images stay on portrait pages with up to 10" of height.

### Results (Earthborne Rangers)

| Tile | Image Dims | Print Size | Page |
|------|-----------|------------|------|
| 4x unnamed tiles | 7275x4275 | 10.0" x 5.9" | Landscape |
| 1x unnamed tile | 7560x4560 | 10.0" x 6.0" | Landscape |
| Campaign Tracker | 3508x2481 | 10.0" x 7.1" | Landscape |
| Valley Map | 2415x3401 | 7.1" x 10.0" | Portrait |

### Files Modified

- `src/generate_tiles_pdf.py` — page-aware constraining, aspect ratio preservation, landscape page rotation for large items
