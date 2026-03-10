# TTS Tools - Claude Instructions

## Global Custom Instructions

Before proceeding with any task, check for relevant custom instructions in:

```
~/Documents/Admin/apps/claude/custom-instructions/
```

Key instructions:
- `shell-command-aliases.md` - **CRITICAL:** Always use -f flag with rm, cp, mv commands
- `python-uv-usage.md` - Always use UV for Python package management and script execution
- `stealth-fetch.md` - Web fetching tool for Cloudflare-protected sites

## TTS Tools Overview

This project provides CLI tools for downloading Tabletop Simulator (TTS) Workshop mods and generating printable PDFs of cards, tiles, and boards.

**IMPORTANT:** When the user gives you a Steam Workshop URL or ID (e.g. `https://steamcommunity.com/sharedfiles/filedetails/?id=XXXXXXX`) and asks to download it, generate PDFs, or print the board/cards/tiles — **always use `tts-mod` as the first choice**. It handles everything automatically: creates `~/Projects/bg/<game_name>/`, downloads, deserializes, fetches assets, extracts metadata, and generates all PDFs (cards, tiles, boards). Only fall back to individual tools if the user needs fine-grained control over a specific step.

```bash
# DEFAULT: Use tts-mod for any Workshop URL
/Users/frankliu/Projects/bg/tts-tools/bin/tts-mod "https://steamcommunity.com/sharedfiles/filedetails/?id=XXXXXXX"

# Override directory name
/Users/frankliu/Projects/bg/tts-tools/bin/tts-mod "https://steamcommunity.com/sharedfiles/filedetails/?id=XXXXXXX" -n my_game

# Override full output path
/Users/frankliu/Projects/bg/tts-tools/bin/tts-mod "https://steamcommunity.com/sharedfiles/filedetails/?id=XXXXXXX" -o /path/to/dir
```

## Tool Location

Tools are in `bin/` under this project root. They are **not** on PATH, so always use the full path:

```
/Users/frankliu/Projects/bg/tts-tools/bin/tts-download
/Users/frankliu/Projects/bg/tts-tools/bin/tts-deserialize
/Users/frankliu/Projects/bg/tts-tools/bin/tts-assets
/Users/frankliu/Projects/bg/tts-tools/bin/tts-extract-sprites
/Users/frankliu/Projects/bg/tts-tools/bin/tts-extract-tiles
/Users/frankliu/Projects/bg/tts-tools/bin/tts-generate-pdf
/Users/frankliu/Projects/bg/tts-tools/bin/tts-generate-tiles-pdf
/Users/frankliu/Projects/bg/tts-tools/bin/tts-generate-board-pdf
/Users/frankliu/Projects/bg/tts-tools/bin/tts-extract-models
/Users/frankliu/Projects/bg/tts-tools/bin/tts-extract-bundles
/Users/frankliu/Projects/bg/tts-tools/bin/tts-extract-pdfs
/Users/frankliu/Projects/bg/tts-tools/bin/tts-generate-model-textures-pdf
/Users/frankliu/Projects/bg/tts-tools/bin/tts-pipeline
/Users/frankliu/Projects/bg/tts-tools/bin/tts-mod
/Users/frankliu/Projects/bg/tts-tools/bin/tts-board-splitter
/Users/frankliu/Projects/bg/tts-tools/bin/tts-crop-sections
/Users/frankliu/Projects/bg/tts-tools/bin/tts-inpaint
```

All bin scripts handle `uv` and virtualenv activation internally — just call them directly.

## Complete Workflow

When asked to process a TTS Workshop mod, **use `tts-mod`** — it handles everything in one command.

### Recommended: tts-mod (full pipeline)

`tts-mod` handles the entire workflow — download, deserialize, assets, extract, and generate ALL PDFs (cards, tiles, boards). It auto-creates a `~/Projects/bg/<game_name>/` directory from the mod title:

```bash
TTS_BIN=/Users/frankliu/Projects/bg/tts-tools/bin

# Auto-name directory from mod title (e.g. "Almighty (Official)" → ~/Projects/bg/almighty/)
$TTS_BIN/tts-mod <workshop_id_or_url>

# Override directory name
$TTS_BIN/tts-mod <workshop_id_or_url> -n my_game_name

# Override full output path
$TTS_BIN/tts-mod <workshop_id_or_url> -o /custom/output/dir

# Skip SSL verification if needed
$TTS_BIN/tts-mod <workshop_id_or_url> --no-verify
```

Options:
- `-n, --name NAME` - Override the auto-generated directory name
- `-o, --output-dir DIR` - Override the full output directory path
- `--no-verify` - Skip SSL certificate verification
- `--card-width INCHES` - Card width (default: 2.5)
- `--card-height INCHES` - Card height (default: 3.5)
- `--card-spacing INCHES` - Spacing between cards (default: 0.0)

### Manual step-by-step workflow

Use individual tools only when you need fine-grained control over a specific step.

Use `TTS_BIN` as shorthand below for `/Users/frankliu/Projects/bg/tts-tools/bin`.

### Step 1: Download the mod

```bash
mkdir -p /path/to/output_dir
$TTS_BIN/tts-download <workshop_id_or_url> -o /path/to/output_dir
```

Output: `<id>_<name>.tts`, `<id>_<name>.json`, `<id>_<name>_preview.jpg`

### Step 2: Deserialize

```bash
$TTS_BIN/tts-deserialize "/path/to/output_dir/<id>_<name>.tts"
```

Output: `<id>_<name>.deserialized.json`

### Step 3: Download assets

```bash
$TTS_BIN/tts-assets "/path/to/output_dir/<id>_<name>.deserialized.json"
```

Output: `<id>_<name>.deserialized/` directory with `Images/`, `Models/`, `Workshop/` subdirectories.

### Step 4: Extract metadata and generate PDFs

After step 3, `cd` into the `.deserialized/` directory. Then run **all** extractors to see what the mod contains:

```bash
cd /path/to/output_dir/<id>_<name>.deserialized
$TTS_BIN/tts-extract-tiles Workshop/*.json
$TTS_BIN/tts-extract-sprites Workshop/*.json
$TTS_BIN/tts-extract-models Workshop/*.json
$TTS_BIN/tts-extract-bundles Workshop/*.json
$TTS_BIN/tts-extract-pdfs Workshop/*.json
```

`tts-extract-tiles` prints a summary like: "Found X tile(s), Y board(s), and Z token(s)". `tts-extract-sprites` prints what card decks were found. `tts-extract-models` prints what 3D model textures were found. `tts-extract-bundles` prints what Unity asset bundle textures were found. `tts-extract-pdfs` downloads any Custom_PDF documents (rulebooks, charts) to `PDFs/`. Use this output to decide which PDF generators to run:

#### If cards were found:

```bash
$TTS_BIN/tts-generate-pdf Workshop/*.json
```

Outputs up to 4 PDFs depending on what the mod contains:

- `complete_deck_faces_with_backs.pdf` — Card faces from decks that have **unique** backs (each card has a different back image). Only generated if such decks exist.
- `complete_deck_backs.pdf` — The unique back images, mirrored horizontally for double-sided printing. Pairs with `faces_with_backs.pdf`.
- `complete_deck_faces_no_backs.pdf` — Card faces from decks that have **shared** backs (many cards use the same back image). The name means "faces without accompanying back pages", not that the cards lack backs.
- `complete_deck_shared_backs.pdf` — One copy of each distinct shared back image. Some of these are generic card-back patterns, but others are content-bearing (reference cards, player aids, victory conditions).

**Full-page mode** (one card per page, scaled to fill):

```bash
$TTS_BIN/tts-generate-pdf Workshop/*.json --full-page
```

Useful for reference cards, player aids, or any card you want printed large. Each card gets its own page, scaled to fill letter size with 0.25" margins. Landscape cards auto-rotate to landscape pages.

#### If tiles were found (small items packed, large items one per page):

```bash
$TTS_BIN/tts-generate-tiles-pdf Workshop/*.json
```

Output: `tiles_and_boards.pdf`

Scale factor is auto-detected from card decks. Large items with landscape images are automatically rotated to landscape pages. All duplicate items are printed individually by default; use `--group` to group duplicates.

**Hex grid layouts** for mods with hex tiles:

```bash
# Honeycomb grid (flat-top hexes with hex outlines)
$TTS_BIN/tts-generate-tiles-pdf Workshop/*.json --hex-grid

# Hex strip (pointy edges touching horizontally, rows offset by half a tile,
# maximizes straight-line cuts)
$TTS_BIN/tts-generate-tiles-pdf Workshop/*.json --hex-strip

# Include non-hex tokens in the hex grid by nickname pattern
# (matched tokens get a colored hex background)
$TTS_BIN/tts-generate-tiles-pdf Workshop/*.json --hex-strip --hex-include Moai Shell
```

Hex tile detection: square RGBA images are auto-detected as hex tiles. The `--hex-include` flag pulls additional tokens into the hex grid by case-insensitive nickname substring match, drawing them on a clay-red hex background. Non-matching items use standard rectangular packing.

#### If boards were found (large items, split across pages):

```bash
$TTS_BIN/tts-generate-board-pdf -m tile_metadata.json
```

Output: `board.pdf` — board image split across multiple letter-sized pages for assembly.

Options:
- `--dpi N` - Control physical size (default: 125). Lower DPI = larger print.
- `--width INCHES` / `--height INCHES` - Set explicit physical dimensions instead of DPI
- `--overlap INCHES` - Overlap between adjacent pages for easier assembly
- `--no-labels` - Omit assembly labels

#### If 3D models were found (diffuse textures):

```bash
$TTS_BIN/tts-generate-model-textures-pdf -m model_texture_metadata.json
```

Output: `model_textures.pdf` — one texture per page, scaled to fit letter size.

#### If the mod has a mix of components

Run all applicable generators. Most board game mods have cards + tiles + boards.

### One-command pipeline (cards only, legacy)

For card-only mods, the older pipeline handles steps 1-4 automatically:

```bash
$TTS_BIN/tts-pipeline <workshop_id_or_url> -o /path/to/output_dir
```

This does NOT generate tiles or board PDFs — only card deck PDFs. Prefer `tts-mod` instead.

## Quick Reference

| Mod contains | Extract tool | PDF tool | Output |
|---|---|---|---|
| Card decks | `tts-extract-sprites` | `tts-generate-pdf` | Up to 4 deck PDFs (see below) |
| Tiles (small) | `tts-extract-tiles` | `tts-generate-tiles-pdf` | `tiles_and_boards.pdf` |
| Boards (large) | `tts-extract-tiles` | `tts-generate-board-pdf` | `board.pdf` |
| 3D Models | `tts-extract-models` | `tts-generate-model-textures-pdf` | `model_textures.pdf` |
| Asset Bundles | `tts-extract-bundles` | `tts-generate-model-textures-pdf` | `bundle_textures.pdf` |
| Custom PDFs | `tts-extract-pdfs` | (downloads directly) | `PDFs/*.pdf` |
| Board sections | `tts-board-splitter` | `tts-crop-sections` | `board_sections/*.png` + PDFs |
| Image cleanup | — | `tts-inpaint` | `inpainted/*.png` |

## Output Directory Structure

```
<id>_<name>.deserialized/
├── Images/                              # Downloaded images
├── Models/                              # Downloaded 3D models
├── Assetbundles/                        # Downloaded asset bundles
├── Workshop/
│   └── <id>_<name>.deserialized.json   # TTS mod JSON
├── sprite_metadata.json                 # Card metadata (from tts-extract-sprites, uses composite keys)
├── tile_metadata.json                   # Tile/board metadata (from tts-extract-tiles)
├── model_texture_metadata.json          # 3D model texture metadata (from tts-extract-models)
├── bundle_texture_metadata.json         # Asset bundle texture metadata (from tts-extract-bundles)
├── BundleTextures/                      # Extracted bundle textures as PNGs
├── PDFs/                                # Downloaded Custom_PDF documents (rulebooks, charts)
├── complete_deck_faces_with_backs.pdf   # Faces of cards with unique (per-card) backs
├── complete_deck_faces_no_backs.pdf     # Faces of cards with shared backs (back not inline)
├── complete_deck_backs.pdf              # Unique backs, mirrored for double-sided printing
├── complete_deck_shared_backs.pdf       # One copy of each distinct shared back image
├── tiles_and_boards.pdf                 # Small items packed, large items one-per-page
├── board.pdf                            # Large board split across pages
└── model_textures.pdf                   # 3D model diffuse textures, one per page
└── bundle_textures.pdf                  # Asset bundle textures (from .unity3d files)
```

## Splitting a Board into Sections

For very large boards that need to be split into logical sections (e.g., separate map regions), use this 3-step workflow:

### Step 1: Define sections visually

```bash
$TTS_BIN/tts-board-splitter board_image.png
```

Opens a React web app in the browser. Draw rectangles on the board, name them, resize edges, then click "Export JSON" to download `board_sections.json`. Requires Node.js.

### Step 2: Crop sections and generate PDFs

```bash
$TTS_BIN/tts-crop-sections -i board_image.png -j board_sections.json --pdf --dpi 125
```

Crops each section into a separate PNG and generates a multi-page PDF for each. Without `--pdf`, only saves the cropped PNGs.

### Step 3: Clean up artifacts (optional)

```bash
$TTS_BIN/tts-inpaint board_sections/01_Section_1.png
```

Launches IOPaint to interactively mask and inpaint artifacts (text overlays, grid lines, etc.). Requires `uv tool install iopaint`.

## Known Gaps

The following TTS object types are **not** handled by the toolchain:

### ~~Shared card backs not printed~~ (FIXED)

Shared card backs are now resolved in `extract_sprites.py` and printed in `complete_deck_shared_backs.pdf` (one copy per distinct back image). This covers reference cards, player aids, and other content-bearing backs that were previously dropped.

### ~~Custom_PDF objects~~ (FIXED)

`Custom_PDF` objects now have their PDFs downloaded by `tts-extract-pdfs`. The tool traverses the TTS JSON, finds all `Custom_PDF` objects with `CustomPDF.PDFUrl` fields, and downloads them to a `PDFs/` directory with sanitized filenames derived from the object's `Nickname`. No metadata JSON is needed — the PDFs are the final output.

### ~~Custom_Assetbundle objects~~ (FIXED)

`Custom_Assetbundle` objects now have their textures extracted using UnityPy. `tts-extract-bundles` loads `.unity3d` files from `Assetbundles/`, extracts Texture2D and Sprite objects (filtering out normal maps, AO maps, and other PBR technical textures), saves them as PNGs in `BundleTextures/`, and produces `bundle_texture_metadata.json`. The existing `tts-generate-model-textures-pdf` generates `bundle_textures.pdf` from this metadata.

### Built-in TTS pieces

`BlockSquare`, `PlayerPawn`, `Die_6_Rounded`, `Checker_red`, `Chinese_Checkers_Piece` — generic TTS pieces with no custom images. Not printable. `Custom_Dice` (3 across mods) could have custom face textures but is very rare.

### Notecards

`Notecard` objects contain text content but are not image-based. Not printable in the same way as other components.

## Notes

- Use `--no-verify` flag on download/assets steps if SSL errors occur
- Board game mods are typically stored under `~/Projects/bg/<game_name>/`
- When the user says "print the board" they mean generate the board PDF and open it with `open board.pdf`
- `tts-board-splitter` requires Node.js (npm) — it runs a Vite+React dev server
- `tts-inpaint` requires IOPaint: install with `uv tool install iopaint`
