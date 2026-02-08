# TTS Workflow Analysis

## Current State

### Tools Located in 3 Separate Directories

#### 1. steam_workshop/ - Download & Deserialize
**Location:** `~/Work/bg/steam_workshop/`

**Scripts:**
- `scripts/steam_workshop_downloader.py` - Downloads .tts, .json, preview
  - Input: Steam Workshop URL or ID
  - Output: `downloads/<id>_<name>.tts`, `<id>_<name>.json`, preview image
  - Example: `python scripts/steam_workshop_downloader.py 3162057688`

- `scripts/tts_deserializer.py` - Converts .tts to .deserialized.json
  - Input: .tts file
  - Output: .deserialized.json file
  - Example: `python scripts/tts_deserializer.py downloads/3162057688.tts`

#### 2. tts-mod-download/ - Download Assets
**Location:** `~/Library/CloudStorage/Box-Box/Work/bg/tts-mod-download/`

**Scripts:**
- `download_tts_assets.py` (via `tts-download` wrapper)
  - Input: .deserialized.json file
  - Output: Images/, Models/, Assetbundles/ directories
  - Example: `tts-download ~/Work/bg/steam_workshop/downloads/3162057688.deserialized.json`

#### 3. tts-mods/ - Generate PDFs
**Location:** `~/Library/CloudStorage/Box-Box/Work/bg/tts-mods/`

**Scripts:**
- `extract_sprites.py` - Extracts sprite metadata
  - Input: .deserialized.json
  - Output: sprite_metadata.json
  - Example: `python extract_sprites.py Workshop/*.json -o sprite_metadata.json`

- `generate_deck_from_json.py` - Generates complete deck PDF
  - Input: .deserialized.json, sprite_metadata.json
  - Output: PDF with all cards including duplicates
  - Example: `python generate_deck_from_json.py Workshop/*.json -m sprite_metadata.json -o complete.pdf`

## Current Manual Workflow

```bash
# 1. Download from Steam Workshop
cd ~/Work/bg/steam_workshop
python scripts/steam_workshop_downloader.py "https://steamcommunity.com/sharedfiles/filedetails/?id=3162057688"
# → downloads/3162057688_Evenfall [Scripted].tts
# → downloads/3162057688_Evenfall [Scripted].json

# 2. Deserialize .tts file
python scripts/tts_deserializer.py "downloads/3162057688_Evenfall [Scripted].tts"
# → downloads/3162057688_Evenfall [Scripted].deserialized.json

# 3. Download assets
cd ~/Library/CloudStorage/Box-Box/Work/bg/evenfall
tts-download ~/Work/bg/steam_workshop/downloads/3162057688_Evenfall\ [Scripted].deserialized.json
# → Creates directory: 3162057688_Evenfall [Scripted].deserialized/
# → Downloads to: Images/, Models/, Assetbundles/, Workshop/

# 4. Generate sprite metadata
cd "3162057688_Evenfall [Scripted].deserialized"
python ~/Library/CloudStorage/Box-Box/Work/bg/tts-mods/extract_sprites.py Workshop/*.json -o sprite_metadata.json

# 5. Generate PDF
python ~/Library/CloudStorage/Box-Box/Work/bg/tts-mods/generate_deck_from_json.py Workshop/*.json \
  -m sprite_metadata.json \
  -o complete_deck.pdf
```

## Problems

1. **Fragmented tools** - 3 different directories
2. **Inconsistent interfaces** - Different argument styles
3. **Manual path management** - User must track output locations
4. **Repetitive commands** - 5+ commands for simple workflow
5. **No unified entry point** - Must remember multiple tools

## Proposed Solutions

### Option 1: Unified Pipeline Script

Create a single script that orchestrates the entire workflow:

```bash
tts-pipeline "https://steamcommunity.com/sharedfiles/filedetails/?id=3162057688"
# Automatically:
# 1. Downloads .tts and metadata
# 2. Deserializes to .json
# 3. Downloads all assets
# 4. Generates sprite metadata
# 5. Generates complete deck PDF
# → Output: complete_deck.pdf
```

**Pros:**
- Single command
- Automatic path management
- Beginner-friendly

**Cons:**
- Less flexibility
- Can't run individual steps
- Harder to debug

### Option 2: Central Tools Directory + Pipeline

Create `~/Work/bg/tts-tools/` with:
- All tools in one place
- Consistent CLI interface
- Optional pipeline script

```
tts-tools/
├── tts-download        # Download from Steam
├── tts-deserialize     # Deserialize .tts
├── tts-assets          # Download assets
├── tts-extract-sprites # Extract sprite metadata
├── tts-generate-pdf    # Generate PDF
├── tts-pipeline        # Run all steps (optional)
└── lib/                # Shared Python modules
```

**Usage:**
```bash
# Option A: Individual steps (granular control)
tts-download 3162057688
tts-deserialize downloads/3162057688.tts
tts-assets downloads/3162057688.deserialized.json
cd 3162057688.deserialized/
tts-extract-sprites Workshop/*.json
tts-generate-pdf Workshop/*.json

# Option B: Pipeline (automatic)
tts-pipeline 3162057688
```

**Pros:**
- Flexible (can use individual tools or pipeline)
- Consistent interface
- Easy to debug
- Organized

**Cons:**
- More scripts to maintain

### Option 3: Keep Separate + Add Wrapper

Keep tools in their original locations but add a wrapper script:

```bash
# Keep:
# - ~/Work/bg/steam_workshop/
# - ~/Library/.../tts-mod-download/
# - ~/Library/.../tts-mods/

# Add:
# - ~/bin/tts-workflow (wrapper that calls all tools)
```

**Pros:**
- No reorganization needed
- Tools remain in logical locations

**Cons:**
- Still fragmented
- Hard to discover tools

## Recommendation: Option 2

**Create `~/Library/CloudStorage/Box-Box/Work/bg/tts-tools/` with:**

1. **Wrapper scripts** (symlinks or thin wrappers to actual tools)
2. **Consistent CLI interface** (all use similar argument patterns)
3. **Pipeline script** for common workflow
4. **Shared documentation** in one place

**Benefits:**
- Centralized discoverability
- Flexibility (individual tools + pipeline)
- Consistent user experience
- Easy to maintain (tools stay in original locations)

**Structure:**
```
tts-tools/
├── README.md                    # Main documentation
├── bin/                         # Command-line tools
│   ├── tts-download            # Steam Workshop downloader
│   ├── tts-deserialize         # .tts deserializer
│   ├── tts-assets              # Asset downloader
│   ├── tts-extract-sprites     # Sprite metadata extractor
│   ├── tts-generate-pdf        # PDF generator
│   └── tts-pipeline            # Full pipeline orchestrator
├── lib/                         # Shared Python modules (symlinks)
│   ├── steam_workshop/         → ~/Work/bg/steam_workshop/scripts/
│   ├── asset_download/         → ~/Library/.../tts-mod-download/
│   └── pdf_generation/         → ~/Library/.../tts-mods/
└── docs/                        # Consolidated documentation
    ├── WORKFLOW.md
    ├── CLI_REFERENCE.md
    └── EXAMPLES.md
```

## Implementation Plan

1. Create `tts-tools/` directory
2. Create wrapper scripts in `bin/` with consistent CLI
3. Create `tts-pipeline` orchestrator
4. Add comprehensive documentation
5. Add to PATH for global access
6. Keep original tools in place (no breaking changes)
