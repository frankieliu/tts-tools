# TTS Tools - Tabletop Simulator Mod Processing Suite

Complete toolkit for downloading, processing, and generating printable PDFs from Tabletop Simulator Workshop mods.

## Overview

This suite provides a unified interface for working with TTS mods, from downloading from Steam Workshop to generating print-ready PDFs of card decks.

### Workflow

```
Steam Workshop URL
    ↓
[tts-download] → .tts file + metadata
    ↓
[tts-deserialize] → .json file
    ↓
[tts-assets] → Images/Models/Assetbundles
    ↓
[tts-extract-sprites] → sprite_metadata.json
    ↓
[tts-generate-pdf] → complete_deck_faces_with_backs.pdf
                   → complete_deck_faces_no_backs.pdf
                   → complete_deck_backs.pdf

Alternative for tiles/boards:
[tts-extract-tiles] → tile_metadata.json
    ↓
[tts-generate-tiles-pdf] → tiles_and_boards.pdf
```

## Installation

### Prerequisites

- Python 3.8+
- `uv` (Python package manager)
- Bash shell

### Setup

1. Add tools to your PATH:
```bash
export PATH="$HOME/Library/CloudStorage/Box-Box/Work/bg/tts-tools/bin:$PATH"
```

Add this to your `~/.bashrc` or `~/.zshrc` for persistence.

2. First run will automatically create required virtual environments.

## Quick Start

### One-Command Pipeline

Generate a complete deck PDF from a Steam Workshop URL:

```bash
tts-pipeline 3162057688
```

Or with a full URL:

```bash
tts-pipeline "https://steamcommunity.com/sharedfiles/filedetails/?id=3162057688"
```

The pipeline will:
1. Download the mod from Steam Workshop
2. Deserialize the .tts file to JSON
3. Download all assets (images, models, etc.)
4. Extract sprite metadata
5. Generate three deck PDFs:
   - Faces with unique backs
   - Faces without unique backs
   - Backs (mirrored for double-sided printing)

Output will be in `<id>_<name>.deserialized/` directory with three PDFs.

### Custom Options

```bash
# Custom output directory
tts-pipeline 3162057688 -o my_mods

# Custom card dimensions
tts-pipeline 3162057688 --card-width 2.75 --card-height 4.0

# Add spacing between cards
tts-pipeline 3162057688 --card-spacing 0.1

# Skip SSL verification (if needed)
tts-pipeline 3162057688 --no-verify
```

## Individual Tools

Each step can also be run independently for more control.

### tts-download

Download TTS mods from Steam Workshop.

```bash
# Download by ID
tts-download 3162057688

# Download by URL
tts-download "https://steamcommunity.com/sharedfiles/filedetails/?id=3162057688"

# Custom output directory
tts-download 3162057688 -o my_downloads
```

**Output:**
- `<id>_<name>.tts` - TTS save file
- `<id>_<name>.json` - Workshop metadata
- `<id>_<name>_preview.jpg` - Preview image

### tts-deserialize

Convert binary .tts files to readable JSON format.

```bash
# Deserialize a .tts file
tts-deserialize downloads/3162057688_Evenfall.tts

# Custom output file
tts-deserialize file.tts -o custom_output.json

# Analysis mode (no output file)
tts-deserialize file.tts --analyze
```

**Output:**
- `<input>.deserialized.json` - Deserialized JSON file

### tts-assets

Download all assets (images, models, asset bundles) from deserialized JSON.

```bash
# Download assets
tts-assets downloads/3162057688_Evenfall.deserialized.json

# Custom output directory
tts-assets file.deserialized.json -o my_output_dir

# Skip SSL verification
tts-assets file.deserialized.json --no-verify
```

**Output:**
- `<output_dir>/Images/` - Card images and textures
- `<output_dir>/Models/` - 3D models
- `<output_dir>/Assetbundles/` - Unity asset bundles
- `<output_dir>/Workshop/` - Copy of JSON file

### tts-extract-sprites

Extract sprite sheet metadata for PDF generation.

```bash
# Extract metadata (run from .deserialized directory)
cd downloads/3162057688_Evenfall.deserialized
tts-extract-sprites Workshop/*.json

# Custom output file
tts-extract-sprites Workshop/mod.json -o metadata.json

# Verbose mode
tts-extract-sprites Workshop/*.json -v
```

**Output:**
- `sprite_metadata.json` - Sprite sheet metadata

### tts-generate-pdf

Generate complete deck PDF with all cards including duplicates.

```bash
# Generate PDF (run from .deserialized directory)
cd downloads/3162057688_Evenfall.deserialized
tts-generate-pdf Workshop/*.json

# Custom output file
tts-generate-pdf Workshop/mod.json -o my_deck.pdf

# Custom card dimensions
tts-generate-pdf Workshop/*.json --card-width 2.75 --card-height 4.0

# Add spacing between cards
tts-generate-pdf Workshop/*.json --card-spacing 0.1
```

**Output:**
- `complete_deck_faces_with_backs.pdf` - Cards with unique backs
- `complete_deck_faces_no_backs.pdf` - Cards without unique backs
- `complete_deck_backs.pdf` - Unique backs (mirrored)

**Default Settings:**
- Card size: 2.5" × 3.5" (standard poker card)
- Grid: 3×3 (9 cards per page)
- Spacing: 0" (no spacing between cards)
- Includes crop marks for cutting
- Landscape cards automatically rotated 90°

**Printing Workflow:**
1. Print `complete_deck_faces_with_backs.pdf` on cardstock
2. Flip the stack and print `complete_deck_backs.pdf` on reverse
3. Print `complete_deck_faces_no_backs.pdf` single-sided
4. Cut out all cards

### tts-extract-tiles

Extract tile and board metadata from TTS JSON files.

```bash
# Extract tile metadata (run from .deserialized directory)
cd <id>_<name>.deserialized
tts-extract-tiles Workshop/*.json

# Custom output file
tts-extract-tiles Workshop/mod.json -o tile_metadata.json

# Verbose mode
tts-extract-tiles Workshop/*.json -v
```

**Output:**
- `tile_metadata.json` - Tile and board metadata including scales and image paths

### tts-generate-tiles-pdf

Generate printable PDFs of tiles and boards from TTS mods.

```bash
# Generate tiles PDF (run from .deserialized directory)
cd <id>_<name>.deserialized
tts-generate-tiles-pdf Workshop/*.json

# Custom scale factor (1 TTS unit = N inches)
tts-generate-tiles-pdf Workshop/*.json --scale-factor 1.0

# Constrain maximum size
tts-generate-tiles-pdf Workshop/*.json --max-size 10.0

# Generate only tiles or only boards
tts-generate-tiles-pdf Workshop/*.json --tiles-only
tts-generate-tiles-pdf Workshop/*.json --boards-only
```

**Output:**
- `tiles_and_boards.pdf` - One tile/board per page with crop marks and size labels

**Scale Factor Guide:**
- Default: `--scale-factor 1.0` (1 TTS unit = 1 inch)
- For large backgrounds: Use smaller scale or `--max-size` constraint
- See `docs/TILES_AND_BOARDS.md` for detailed scaling guide

## Examples

### Example 1: Quick PDF Generation

```bash
tts-pipeline 3162057688
```

### Example 2: Custom Card Size

```bash
tts-pipeline 3162057688 --card-width 2.75 --card-height 4.0
```

### Example 3: Manual Step-by-Step

```bash
# Download
tts-download 3162057688 -o my_mods

# Deserialize
tts-deserialize my_mods/3162057688_Evenfall.tts

# Download assets
tts-assets my_mods/3162057688_Evenfall.deserialized.json

# Navigate to output directory
cd my_mods/3162057688_Evenfall.deserialized

# Extract sprites
tts-extract-sprites Workshop/*.json

# Generate PDF
tts-generate-pdf Workshop/*.json -o evenfall_deck.pdf
```

### Example 4: Multiple Mods

```bash
# Download and process multiple mods
tts-pipeline 3162057688 -o mods
tts-pipeline 3160692601 -o mods
tts-pipeline 2891391943 -o mods
```

## Features

### Card Deck Generation

**Automatic Card Duplication:**
The PDF generator automatically extracts card counts from the TTS JSON file. No game-specific configuration needed - it works with any TTS mod.

**Double-Sided Printing Support:**
- Separate PDFs for cards with unique backs vs. cards with generic backs
- Backs PDF is horizontally mirrored for proper alignment when double-sided printing
- Clear printing workflow instructions

**Landscape Card Detection:**
- Automatically rotates landscape-oriented cards 90° for proper printing
- Maintains correct aspect ratios

### Tile and Board Extraction

**Physical Size Estimation:**
- Converts TTS scale values to printable dimensions
- Configurable scale factor (default: 1 TTS unit = 1 inch)
- Maximum size constraints to prevent oversized prints
- See `docs/TILES_AND_BOARDS.md` for detailed scaling guide

**Flexible Output:**
- One item per page with crop marks
- Automatic orientation selection (portrait/landscape)
- Size labels on each page
- Separate PDFs for tiles and boards if desired

### Customizable Output

- Adjustable card dimensions
- Configurable spacing
- Custom output locations
- Flexible grid layouts

### Complete Asset Management

- Downloads all images, models, and asset bundles
- Handles URL conversions for Steam CDN
- Creates organized directory structures

### Print-Ready PDFs

- Standard poker card size (2.5" × 3.5") by default for cards
- Scale-based sizing for tiles and boards
- No spacing between cards (perfect for cutting)
- Crop marks for precise cutting
- High-quality output

## Directory Structure

After running the pipeline, you'll have:

```
<id>_<name>.deserialized/
├── Images/                              # Downloaded card/tile images
├── Models/                              # Downloaded 3D models
├── Assetbundles/                        # Downloaded asset bundles
├── Workshop/
│   └── <id>_<name>.deserialized.json   # TTS mod JSON
├── sprite_metadata.json                 # Card sprite metadata
├── tile_metadata.json                   # Tile/board metadata (if extracted)
├── complete_deck_faces_with_backs.pdf   # Cards with unique backs
├── complete_deck_faces_no_backs.pdf     # Cards without unique backs
├── complete_deck_backs.pdf              # Card backs (mirrored)
└── tiles_and_boards.pdf                 # Tiles/boards (if generated)
```

## Troubleshooting

### SSL Certificate Errors

If you encounter SSL errors, use the `--no-verify` flag:

```bash
tts-pipeline 3162057688 --no-verify
```

### Missing Virtual Environment

If you see venv errors, create the environment manually:

```bash
# For download/deserialize tools
cd ~/Work/bg/steam_workshop
uv venv
uv pip install -r requirements.txt

# For asset download
cd ~/Library/CloudStorage/Box-Box/Work/bg/tts-mod-download
uv venv
uv pip install -r requirements.txt

# For PDF generation
cd ~/Library/CloudStorage/Box-Box/Work/bg/tts-mods
uv venv
uv pip install .
```

### Card Count Mismatch

The PDF generator uses the JSON file as the source of truth for card duplication. If you notice incorrect card counts, verify:

1. The JSON file was properly deserialized
2. The sprite metadata was extracted correctly
3. The Images/ directory contains all required sprite sheets

## Technical Details

### Card Duplication

TTS JSON files contain explicit card duplication in `DeckIDs` arrays. Each CardID appears N times = N copies. The generator uses Python's Counter to extract exact counts.

### CardID Format

CardIDs follow the format `DDDPP`:
- DDD: Deck ID (first 2-3 digits)
- PP: Position in sprite sheet

Deck ID is extracted as: `deck_id = card_id // 100`

### Asset URL Conversion

The asset downloader automatically converts Steam CDN URLs:
- From: `cloud-3.steamusercontent.com`
- To: `steamusercontent-a.akamaihd.net`

## Related Documentation

- `docs/TTS_JSON_STRUCTURE.md` - Comprehensive TTS JSON format documentation
- `docs/TILES_AND_BOARDS.md` - Tile/board extraction and scaling guide
- `docs/DOCUMENTATION_UPDATES.md` - Recent documentation changes

## Tool Architecture

All tools use `uv` for Python environment management. Dependencies are defined in `pyproject.toml`:
- `requests` - HTTP downloads
- `pillow` - Image processing
- `reportlab` - PDF generation

Wrapper scripts in `bin/` provide consistent CLI interface across all tools.

## License

These tools are for personal use with Tabletop Simulator mods. Respect mod creators' licenses and terms of use.
