# Arcs TTS Scaling Validation Session

**Date**: 2026-02-03
**Objective**: Validate TTS scaling formula using Arcs board game mod with known physical measurements

## Ground Truth Measurements (from User)

### Board Dimensions
- **Main board**: 16.5 × 30.5 inches
- **Player boards**: 115 × 272 mm (4.53 × 10.71 inches)

### Card Dimensions
- **Standard cards**: 63.5 × 88 mm (2.5 × 3.46 inches) - Standard Poker size
- **Tarot cards**: 70 × 120 mm (2.76 × 4.72 inches)
- **Expected counts**: 85 standard cards, 8 tarot cards in base game

## TTS Scaling Formula to Validate

From previous Clank Legacy investigation:

```
For Tiles/Boards/Tokens:
  Physical Width  = 1.300" × Transform.scaleX × (image_width / image_height)
  Physical Height = 1.318" × Transform.scaleZ

For Cards (different BASE):
  Physical Width  = 3.475" × Transform.scaleX × (image_width / image_height)
  Physical Height = 3.500" × Transform.scaleZ
```

## Mods Attempted

### 1. Arcs - Imperial Edition (ID: 3037846252)
**Directory**: `/Users/frankliu/Work/bg/arcs_imperial/`
**Status**: ❌ Incomplete - Dropbox image failures

**Results**:
- Downloaded: 2.00 MB .tts file
- Assets: 93 downloaded, 148 failed (Dropbox URLs blocked by proxy)
- Sprite sheets: 50 found, 1,136 card instances
- Generated PDFs:
  - `complete_deck_faces_with_backs.pdf` - 90 pages, 807 cards
  - `complete_deck_faces_no_backs.pdf` - 37 pages, 329 cards
  - `complete_deck_backs.pdf` - 90 pages, 807 mirrored backs

**Issues**:
- Many sprite sheet loading errors due to missing Dropbox images
- Cards likely rendered as blanks/placeholders for missing sprites
- Total of 1,136 cards processed (807 with unique backs, 329 without)

### 2. Arcs (ID: 2787734760)
**Directory**: `/Users/frankliu/Work/bg/arcs_with_campaign/`
**Status**: ⚠️ Partial - Cards generated, boards pending

**Results**:
- Downloaded: 987.28 KB .tts file
- Assets: Unknown success count, many Dropbox failures
- Generated PDFs:
  - `complete_deck_faces_with_backs.pdf` - 19 KB (48 pages, 424 cards)
  - `complete_deck_faces_no_backs.pdf` - 17 KB
  - `complete_deck_backs.pdf` - 19 KB

**Issues**:
- Similar Dropbox URL blocking issues
- Repeated sprite sheet loading errors: "[Errno 21] Is a directory: '.'"
- Small PDF file sizes suggest minimal content

**Next Steps**:
- Extract tile/board metadata using `tts-extract-tiles`
- Analyze Transform.scale values for main board and player boards
- Calculate physical dimensions using TTS formula
- Compare calculated vs. ground truth measurements

### 3. Arcs Base Game (ID: 3633304735)
**Directory**: `/Users/frankliu/Work/bg/arcs_base/`
**Status**: ❌ No usable data

**Results**:
- Downloaded: 447.11 KB .tts file
- Assets: 1 downloaded, 10 failed (all Dropbox URLs)
- Sprite sheets: 0 found
- No cards generated (0 card instances)

**Issues**:
- Deserialization warning: "Unknown type marker: 0x12 at position 75016"
- No sprite sheets found in JSON
- All images hosted on Dropbox (inaccessible)

## Current Issue: Dropbox Asset Downloads

All three mods use Dropbox URLs for hosting card images, which are blocked by corporate proxy:

```
HTTPSConnectionPool(host='dl.dropboxusercontent.com', port=443): Max retries exceeded
Caused by ProxyError('Unable to connect to proxy', OSError('Tunnel connection failed: 403 Forbidden'))
```

**Assets Successfully Downloaded**: Only Steam CDN URLs work (steamusercontent-a.akamaihd.net)

## Pending Analysis

### For Mod: 2787734760 (Arcs with Campaign)

Still need to:

1. **Extract Board/Tile Metadata**:
   ```bash
   cd /Users/frankliu/Work/bg/arcs_with_campaign/2787734760_Arcs.deserialized
   tts-extract-tiles Workshop/*.json -v
   ```

2. **Analyze JSON Structure**:
   - Find main board object (likely named "Arcs" or "Main Board")
   - Find player board objects (4 expected)
   - Extract Transform.scale values
   - Get image dimensions (width × height pixels)

3. **Calculate Physical Dimensions**:
   - Apply formula: `width = 1.300" × scale_x × aspect_ratio`
   - Apply formula: `height = 1.318" × scale_z`
   - Compare to ground truth:
     - Main board should calculate to ~16.5 × 30.5"
     - Player boards should calculate to ~115 × 272 mm

4. **Calculate Error Percentage**:
   ```
   error = |calculated - actual| / actual × 100%
   ```

5. **Document Results**:
   - If error < 2%: Formula validated ✅
   - If error > 5%: Investigate discrepancies, may need different BASE values

## Script Permissions Issue

Encountered permission error with `tts-extract-tiles`:
```bash
# Fix: Make script executable
chmod +x /Users/frankliu/Library/CloudStorage/Box-Box/Work/bg/tts-tools/bin/tts-extract-tiles
```

## Alternative Approaches

If Dropbox blocking continues to be an issue:

1. **Manual JSON Analysis**: Read JSON directly to find board/tile objects
2. **Local Image Access**: If images exist locally, generate PDFs directly
3. **Different Mod Source**: Find Arcs mods that use Steam CDN exclusively
4. **Network Workaround**: Temporarily bypass proxy for Dropbox (if allowed)

## Files and Directories

```
/Users/frankliu/Work/bg/
├── arcs_imperial/                     # Attempt 1 - Imperial Edition
│   ├── 3037846252_Arcs - Imperial Edition.tts
│   ├── 3037846252_Arcs - Imperial Edition.json
│   └── 3037846252_Arcs - Imperial Edition.deserialized/
│       ├── Images/
│       ├── Workshop/
│       ├── sprite_metadata.json
│       └── complete_deck_*.pdf (3 files)
│
├── arcs_with_campaign/                # Attempt 2 - With Campaign (CURRENT)
│   ├── 2787734760_Arcs.tts
│   ├── 2787734760_Arcs.json
│   └── 2787734760_Arcs.deserialized/
│       ├── Images/
│       ├── Workshop/
│       │   └── 2787734760_Arcs.deserialized.json  # <- ANALYZE THIS
│       └── complete_deck_*.pdf (3 files, 17-19KB)
│
└── arcs_base/                         # Attempt 3 - Base Game (FAILED)
    ├── 3633304735_Arcs Base Game.tts
    └── 3633304735_Arcs Base Game.deserialized/
        └── sprite_metadata.json (empty)
```

## Success Criteria

For validation to be considered successful:

- **Primary**: Main board dimensions match within ±2% error
- **Secondary**: Player board dimensions match within ±5% error
- **Tertiary**: Token dimensions show consistent scaling pattern

## Next Session Actions

1. Make `tts-extract-tiles` executable
2. Run tile extraction on mod 2787734760
3. Analyze board Transform.scale values
4. Calculate physical dimensions using TTS formula
5. Compare calculated vs. ground truth measurements
6. Document validation results in new file: `ARCS_VALIDATION_RESULTS.md`

## Questions to Investigate

1. Why do all Arcs mods use Dropbox instead of Steam CDN?
2. Can we find sprite sheets locally despite download failures?
3. Are there alternative Arcs mods with Steam-hosted assets?
4. Does the small PDF size indicate actual missing cards or just low image quality?

## Related Documentation

- `docs/PROJECT_SUMMARY.md` - Previous Clank Legacy investigation
- `docs/TTS_SCALING_SOLVED.md` - Derived BASE units and formula
- `docs/PRINTING_GUIDE_V2.md` - Multi-page printing with correct scaling
