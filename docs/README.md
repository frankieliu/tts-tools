# Board Game Tools (bg)

A collection of tools for processing board game assets into printable formats.

## Overview

This toolkit provides utilities for converting digital board game assets into physical, printable formats. Whether you're prototyping a game, creating proxies, or printing TTS mods, these tools help you generate print-ready PDFs.

## Tools

### 1. Card Processor (`card-processor/`)

A flexible Python pipeline for processing card sprite sheets into printable PDFs with cutting lines.

**Best for:**
- Prototyping custom card games
- Converting sprite sheets to physical cards
- Creating collages with specific card arrangements
- Batch processing multiple decks

**Key Features:**
- Any m×n sprite sheet layout
- Customizable collages with card assignments
- Auto-centered PDFs with calculated margins
- Multiple page sizes (letter, legal, A4, custom)
- Unified CLI with `zenith` command

[→ Card Processor Documentation](card-processor/README.md)

**Quick Start:**
```bash
cd card-processor
uv sync
zenith run -c config.yaml
```

### 2. TTS Mods PDF Generator (`tts-mods/`)

Automatically generate printable PDFs from Tabletop Simulator (TTS) Workshop JSON files and sprite sheets.

**Best for:**
- Printing TTS Workshop mods as physical cards
- Converting digital TTS games to physical
- Quick PDF generation from TTS saves
- Standard card layouts (3×3 grid)

**Key Features:**
- Auto-extraction of sprite metadata from JSON
- Detects both single cards and deck objects
- Auto-discovery of sprite sheet images
- Standard poker card size (2.5" × 3.5")
- One-command pipeline

[→ TTS Mods Documentation](tts-mods/README.md)

**Quick Start:**
```bash
cd tts-mods
uv venv
uv pip install .
./process_ttsmod.sh YourMod.ttsmod
```

## Which Tool Should I Use?

### Use **Card Processor** if you:
- ✓ Have a sprite sheet and want custom layouts
- ✓ Need fine control over card arrangements
- ✓ Want to combine multiple collages into one PDF
- ✓ Are working with non-TTS sprite sheets
- ✓ Need to process multiple configurations

### Use **TTS Mods** if you:
- ✓ Have TTS Workshop JSON files
- ✓ Want automatic metadata extraction
- ✓ Need quick PDF generation from TTS
- ✓ Want standard 3×3 card layouts
- ✓ Are converting TTS mods to physical

## Installation

### Card Processor
```bash
cd card-processor
uv sync                      # Install dependencies
zenith --help                # Verify installation
```

### TTS Mods
```bash
cd tts-mods
uv venv                         # Create virtual environment
uv pip install .                # Install dependencies
./process_ttsmod.sh --help      # Verify installation
```

## Requirements

- **Python 3.8+** for both tools
- **uv** (recommended) for fast package management
- **Pillow** for image processing
- **reportlab** for PDF generation

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Directory Structure

```
bg/
├── card-processor/       # Generic sprite sheet processor
│   ├── src/             # Pipeline scripts
│   ├── config.yaml      # Configuration
│   └── README.md
├── tts-mods/            # TTS-specific PDF generator
│   ├── extract_sprites.py
│   ├── generate_pdfs.py
│   ├── pipeline.sh
│   └── README.md
├── shared/              # Shared utilities (future)
├── docs/                # Common documentation
├── examples/            # Example projects
├── README.md           # This file
└── QUICK_REFERENCE.md  # Command cheat sheet
```

## Common Workflows

### Workflow 1: TTS Mod → Physical Cards

1. **Export from TTS**
   - Save your TTS game
   - Locate the Workshop JSON file
   - Download sprite sheet images

2. **Organize files**
   ```
   YourMod/
   ├── Workshop/
   │   └── 2083854795.json
   └── Images/
       └── *.png
   ```

3. **Copy tools and run**
   ```bash
   cd bg/tts-mods
   uv venv
   uv pip install .
   ./process_ttsmod.sh /path/to/YourMod.ttsmod -o /path/to/output/
   ```

4. **Print**
   - PDFs in `output/`
   - Standard 3×3 layout
   - Crop marks included

### Workflow 2: Custom Card Game Prototype

1. **Create sprite sheet**
   - Arrange cards in grid
   - Save as `cards.png`

2. **Configure**
   ```yaml
   # config.yaml
   sprite_sheet:
     rows: 9
     cols: 12
     total_cards: 108

   card:
     width_inches: 2.5
     height_inches: 3.5
     dpi: 300
   ```

3. **Run pipeline**
   ```bash
   cd card-processor
   zenith run -c config.yaml
   ```

4. **Print and cut**
   - Combined PDF with all pages
   - Custom collage layouts
   - Cutting lines included

### Workflow 3: Multiple Card Decks

1. **Create configurations**
   ```
   card-processor/
   ├── config_heroes.yaml
   ├── config_monsters.yaml
   └── config_items.yaml
   ```

2. **Run each deck**
   ```bash
   zenith run -c config_heroes.yaml
   zenith run -c config_monsters.yaml
   zenith run -c config_items.yaml
   ```

3. **Separate outputs**
   - Each deck gets its own PDF
   - Easy to manage multiple decks
   - Same tool, different configs

## Example Projects

See `examples/` directory for:
- Sample configurations
- Example sprite sheets
- Complete project templates
- Reference implementations

## Documentation

- [Card Processor Guide](card-processor/README.md) - Detailed configuration
- [TTS Mods Guide](tts-mods/README.md) - TTS-specific instructions
- [Quick Reference](QUICK_REFERENCE.md) - Common commands
- [Examples](examples/) - Sample projects

## Use Cases

### Board Game Prototyping
- Test game mechanics with printed prototypes
- Iterate quickly on card designs
- Professional-looking playtest materials

### TTS Mod Printing
- Convert digital TTS games to physical
- Create backup decks
- Play offline with friends

### Card Proxies
- Create proxies for existing games
- Test expansions before buying
- Replace damaged cards

### Print-on-Demand Prep
- Generate print-ready PDFs
- Proper sizing and margins
- Professional crop marks

### Custom Game Production
- Prepare files for printing services
- Batch process multiple decks
- Consistent quality output

## Tips & Best Practices

### For Best Print Quality
- Use 300+ DPI for cards
- Ensure sprite sheets are high resolution
- Test print one page before printing all

### For Easy Cutting
- Enable crop marks
- Add 0.1" spacing between cards
- Use a paper cutter for straight lines

### For Multiple Decks
- Use separate config files
- Name outputs clearly
- Keep source files organized

### For TTS Mods
- Download highest quality images
- Check grid dimensions in JSON
- Verify all sprite sheets downloaded

## Troubleshooting

### Common Issues

**"ModuleNotFoundError"**
```bash
uv venv
uv pip install .
```

**"Sprite image not found"**
- Check Images/ directory exists
- Verify image filenames match URLs
- Run with `--verbose` or `-v` flag

**Cards are blurry**
- Increase DPI in config
- Use higher resolution sprite sheets
- Check source image quality

**Wrong grid dimensions**
- Verify `rows × cols = total_cards`
- Check TTS JSON for NumWidth/NumHeight
- Count cards manually if needed

**PDF too large/small**
- Adjust card dimensions
- Change page size
- Modify spacing and margins

See tool-specific READMEs for detailed troubleshooting.

## Contributing

We welcome contributions!

- Report bugs or issues
- Suggest new features
- Submit pull requests
- Improve documentation
- Share example projects

## Related Projects

- [Zenith](../zenith/) - Zenith board game resources and assets
- [Clank Mods](../clank/Mods/) - Example TTS mod project
- [A Wild Venture Mods](../aWildVenture/Mods/) - Another example project

## License

MIT License - feel free to use and modify for your projects.

## Support

For help:
1. Check the [Quick Reference](QUICK_REFERENCE.md)
2. Read tool-specific documentation
3. Review example projects
4. Check troubleshooting sections

## Version

**Current Version:** 1.0.0
**Last Updated:** 2026-01-28
**Python Support:** 3.8+

---

**Quick Links:**
- [Card Processor →](card-processor/)
- [TTS Mods →](tts-mods/)
- [Quick Reference →](QUICK_REFERENCE.md)
- [Examples →](examples/)
