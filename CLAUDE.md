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
/Users/frankliu/Projects/bg/tts-tools/bin/tts-pipeline
/Users/frankliu/Projects/bg/tts-tools/bin/tts-mod
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

After step 3, `cd` into the `.deserialized/` directory. Then run **both** extractors to see what the mod contains:

```bash
cd /path/to/output_dir/<id>_<name>.deserialized
$TTS_BIN/tts-extract-tiles Workshop/*.json
$TTS_BIN/tts-extract-sprites Workshop/*.json
```

`tts-extract-tiles` prints a summary like: "Found X tile(s), Y board(s), and Z token(s)". `tts-extract-sprites` prints what card decks were found. Use this output to decide which PDF generators to run:

#### If cards were found:

```bash
$TTS_BIN/tts-generate-pdf Workshop/*.json
```

Outputs: `complete_deck_faces_with_backs.pdf`, `complete_deck_faces_no_backs.pdf`, `complete_deck_backs.pdf`

#### If tiles were found (small items packed, large items one per page):

```bash
$TTS_BIN/tts-generate-tiles-pdf Workshop/*.json
```

Output: `tiles_and_boards.pdf`

Scale factor is auto-detected from card decks. Large items with landscape images are automatically rotated to landscape pages. All duplicate items are printed individually by default; use `--group` to group duplicates.

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
| Card decks | `tts-extract-sprites` | `tts-generate-pdf` | 3 deck PDFs |
| Tiles (small) | `tts-extract-tiles` | `tts-generate-tiles-pdf` | `tiles_and_boards.pdf` |
| Boards (large) | `tts-extract-tiles` | `tts-generate-board-pdf` | `board.pdf` |

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
├── complete_deck_faces_with_backs.pdf   # Card faces with unique backs
├── complete_deck_faces_no_backs.pdf     # Card faces without unique backs
├── complete_deck_backs.pdf              # Card backs (mirrored)
├── tiles_and_boards.pdf                 # Small items packed, large items one-per-page
└── board.pdf                            # Large board split across pages
```

## Notes

- Use `--no-verify` flag on download/assets steps if SSL errors occur
- Board game mods are typically stored under `~/Projects/bg/<game_name>/`
- When the user says "print the board" they mean generate the board PDF and open it with `open board.pdf`
