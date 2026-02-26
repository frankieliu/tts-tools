# TTS Tools Workflow

## Quick Start: tts-mod (recommended)

One command to go from a Steam Workshop URL to printable PDFs:

```bash
TTS_BIN=/Users/frankliu/Projects/bg/tts-tools/bin

# Auto-creates ~/Projects/bg/<game_name>/ from the mod title
$TTS_BIN/tts-mod "https://steamcommunity.com/sharedfiles/filedetails/?id=XXXXXXX"

# Override directory name
$TTS_BIN/tts-mod 2846396687 -n life_amazonia

# Override full output path
$TTS_BIN/tts-mod 2846396687 -o /tmp/my_mod
```

This handles everything: queries Steam for the title, creates the directory, downloads the mod, deserializes, fetches assets, extracts metadata, and generates all applicable PDFs (cards, tiles, boards).

Options:
- `-n, --name NAME` — override the auto-generated directory name
- `-o, --output-dir DIR` — override the full output path
- `--no-verify` — skip SSL certificate verification
- `--card-width`, `--card-height`, `--card-spacing` — card sizing overrides

## Manual Step-by-Step

Use individual tools when you need fine-grained control.

### Prerequisites

Download and prepare the mod (steps 1-3), then generate PDFs (step 4).

### From Scratch

```bash
TTS_BIN=/Users/frankliu/Projects/bg/tts-tools/bin

# Step 1: Download the mod
mkdir -p ~/bg/my_game
$TTS_BIN/tts-download <workshop_id_or_url> -o ~/bg/my_game

# Step 2: Deserialize
$TTS_BIN/tts-deserialize ~/bg/my_game/<id>_<name>.tts

# Step 3: Download assets
$TTS_BIN/tts-assets ~/bg/my_game/<id>_<name>.deserialized.json

# Step 4: Extract metadata and generate PDFs (see below)
cd ~/bg/my_game/<id>_<name>.deserialized
```

## Generating PDFs (from a deserialized mod)

```bash
cd /path/to/<id>_<name>.deserialized
TTS_BIN=/Users/frankliu/Projects/bg/tts-tools/bin
```

### 1. Extract metadata (run both)

```bash
$TTS_BIN/tts-extract-sprites Workshop/*.json    # → sprite_metadata.json
$TTS_BIN/tts-extract-tiles Workshop/*.json      # → tile_metadata.json
```

### 2. Generate PDFs based on what was found

**Cards** (if `tts-extract-sprites` found decks):

```bash
$TTS_BIN/tts-generate-pdf Workshop/*.json
```

Outputs:
- `complete_deck_faces_with_backs.pdf`
- `complete_deck_faces_no_backs.pdf`
- `complete_deck_backs.pdf`

**Tiles & tokens** (if `tts-extract-tiles` found tiles/tokens):

```bash
$TTS_BIN/tts-generate-tiles-pdf Workshop/*.json
```

Output: `tiles_and_boards.pdf` — small items packed onto pages, large items one per page with automatic landscape rotation.

Options:
- `--group` — group duplicate items (default: print all copies)
- `--tiles-only` / `--tokens-only` / `--boards-only` — filter by type
- `--no-labels` — omit text labels
- `--scale-factor N` — override auto-detected scale factor

**Boards** (if `tts-extract-tiles` found `Custom_Board` objects):

```bash
$TTS_BIN/tts-generate-board-pdf -m tile_metadata.json
```

Output: `board.pdf` — large board split across multiple letter pages for assembly.

Options:
- `--dpi N` — control physical size (default: 125). Lower DPI = larger print.
- `--width INCHES` / `--height INCHES` — set explicit physical dimensions
- `--overlap INCHES` — overlap between adjacent pages for assembly
- `--no-labels` — omit assembly labels

## Quick Reference

| Mod contains | Extract tool | PDF tool | Output |
|---|---|---|---|
| Card decks | `tts-extract-sprites` | `tts-generate-pdf` | 3 deck PDFs |
| Tiles/tokens | `tts-extract-tiles` | `tts-generate-tiles-pdf` | `tiles_and_boards.pdf` |
| Boards (large) | `tts-extract-tiles` | `tts-generate-board-pdf` | `board.pdf` |

Most board game mods have a mix — run all applicable generators.
