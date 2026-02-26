# TTS Tools

CLI tools for downloading Tabletop Simulator Workshop mods and generating printable PDFs of cards, tiles, and boards.

## Overview

This toolkit converts TTS Workshop mods into print-ready PDFs. It handles:
- **Card decks** — sprite sheet extraction and 3x3 poker-card PDFs
- **Tiles and tokens** — small items packed onto pages, large items one per page
- **Boards** — large items split across multiple letter-sized pages for assembly

## Tools

All tools are in `bin/` and handle virtualenv/uv internally.

| Tool | Purpose |
|------|---------|
| `tts-download` | Download a TTS Workshop mod by ID or URL |
| `tts-deserialize` | Deserialize a `.tts` mod file to JSON |
| `tts-assets` | Download all images, models, and assets |
| `tts-extract-sprites` | Extract card sprite sheet metadata |
| `tts-extract-tiles` | Extract tile/board/token metadata |
| `tts-generate-pdf` | Generate card deck PDFs (faces, backs) |
| `tts-generate-tiles-pdf` | Generate tiles/tokens PDF |
| `tts-generate-board-pdf` | Generate multi-page board PDF |
| `tts-pipeline` | One-command pipeline (cards only) |

## Quick Start

```bash
# Download and process a mod
mkdir -p ~/bg/my_game
bin/tts-download <workshop_id_or_url> -o ~/bg/my_game
bin/tts-deserialize ~/bg/my_game/<id>_<name>.tts
bin/tts-assets ~/bg/my_game/<id>_<name>.deserialized.json

# Generate PDFs
cd ~/bg/my_game/<id>_<name>.deserialized
bin/tts-extract-sprites Workshop/*.json
bin/tts-extract-tiles Workshop/*.json
bin/tts-generate-pdf Workshop/*.json
bin/tts-generate-tiles-pdf Workshop/*.json
```

## Directory Structure

```
tts-tools/
├── bin/                    # CLI wrapper scripts (entry points)
│   ├── tts-download
│   ├── tts-deserialize
│   ├── tts-assets
│   ├── tts-extract-sprites
│   ├── tts-extract-tiles
│   ├── tts-generate-pdf
│   ├── tts-generate-tiles-pdf
│   ├── tts-generate-board-pdf
│   └── tts-pipeline
├── src/                    # Python source files
│   ├── extract_sprites.py
│   ├── extract_tiles.py
│   ├── generate_deck_from_json.py
│   ├── generate_tiles_pdf.py
│   ├── generate_board_pdf.py
│   └── ...
├── docs/                   # Documentation
└── CLAUDE.md               # Claude Code instructions
```

## Output Structure

After processing a mod:

```
<id>_<name>.deserialized/
├── Images/                              # Downloaded images
├── Models/                              # Downloaded 3D models
├── Workshop/
│   └── <id>_<name>.deserialized.json   # TTS mod JSON
├── sprite_metadata.json                 # Card metadata
├── tile_metadata.json                   # Tile/board metadata
├── complete_deck_faces_with_backs.pdf   # Card faces with unique backs
├── complete_deck_faces_no_backs.pdf     # Card faces without unique backs
├── complete_deck_backs.pdf              # Card backs (mirrored)
├── tiles_and_boards.pdf                 # Tiles/boards one-per-page
└── board.pdf                            # Large board split across pages
```

## Requirements

- Python 3.8+
- [uv](https://astral.sh/uv) for package management (bin scripts handle this internally)

## Documentation

- [SPRITE_SHEETS_EXPLAINED.md](SPRITE_SHEETS_EXPLAINED.md) — How TTS card sprite sheets work
- [TILES_AND_BOARDS.md](TILES_AND_BOARDS.md) — Tile/board extraction and scaling
- [PRINTING_GUIDE.md](PRINTING_GUIDE.md) — Printing tiles, boards, and tokens
- [BOARD_PDF_GUIDE.md](BOARD_PDF_GUIDE.md) — Multi-page board printing
- [COMPOSITE_DECK_KEYS_AND_TILE_LAYOUT.md](COMPOSITE_DECK_KEYS_AND_TILE_LAYOUT.md) — Composite deck key fix and tile layout improvements
- [TTS_JSON_STRUCTURE.md](TTS_JSON_STRUCTURE.md) — Complete TTS JSON reference
