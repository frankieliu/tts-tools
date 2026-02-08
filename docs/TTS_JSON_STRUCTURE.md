# TTS JSON File Structure and Metadata

## File Locations

### Default Storage Locations by Platform

**Windows:**
```
%USERPROFILE%\Documents\My Games\Tabletop Simulator\
├── Mods\                     # Workshop mods (.json files)
│   ├── Workshop\             # Steam Workshop mods
│   ├── Assetbundles\         # Asset bundle cache
│   ├── Audio\                # Audio file cache
│   ├── Images\               # Image file cache
│   ├── Models\               # 3D model file cache
│   └── PDF\                  # PDF file cache
└── Saves\                    # Saved games (.json files)
    └── SavedObjects\         # Saved objects (.json files)
```

**macOS:**
```
~/Library/Tabletop Simulator/
├── Mods/
│   ├── Workshop/
│   └── [asset folders...]
└── Saves/
    └── SavedObjects/
```

**Linux:**
```
~/.local/share/Tabletop Simulator/
├── Mods/
│   ├── Workshop/
│   └── [asset folders...]
└── Saves/
    └── SavedObjects/

# Alternative (Snap installation):
~/snap/steam/common/.local/share/Tabletop Simulator/
```

### File Naming Convention

- **Mods/Saves:** `[WorkshopID or custom name].json`
  - Example: `123456789.json` (Workshop mod)
  - Example: `MyCustomMod.json` (Custom mod)
- **Saved Objects:** Located in subdirectories within `Saves/SavedObjects/`

## JSON Structure and Metadata

### Top-Level Fields

TTS JSON files contain the following **metadata fields**:

```json
{
  "SaveName": "Cool Adventure Map",
  "Date": "12/23/2025 3:45:30 PM",
  "GameMode": "Tabletop Simulator",
  "Gravity": 0.5,
  "PlayArea": 0.5,
  "Table": "Table_RPG",
  "Sky": "Sky_Museum",
  "Note": "",
  "Rules": "",
  "LuaScript": "-- Game logic here",
  "LuaScriptState": "",
  "XmlUI": "",
  "ObjectStates": [
    // Array of game objects
  ],
  "TabStates": {},
  "VersionNumber": ""
}
```

### Key Metadata Fields

#### 1. SaveName (String)
- **What it is:** The display name of the mod/save
- **Format:** Free text string
- **Example:** `"SaveName": "Epic Dungeon Crawler"`
- **For Saved Objects:** Uses `"Nickname"` field instead of `"SaveName"`
- **Extracted by:** Regex pattern `"SaveName"\s*:\s*"([^"]*)"`

#### 2. Date (String)
- **What it is:** Timestamp when the mod was **last saved in TTS**
- **Format:** `M/d/yyyy h:mm:ss a` (12-hour) or `MM/dd/yyyy HH:mm:ss` (24-hour)
- **Examples:**
  - `"Date": "12/23/2025 3:45:30 PM"`
  - `"Date": "01/15/2025 15:30:00"`
- **Extracted by:** Regex pattern `"Date"\s*:\s*"([^"]*)"`
- **Converted to:** Unix timestamp (seconds since epoch) for storage
- **Important:** This is when the **mod file** was saved, NOT when individual assets were created

#### 3. ObjectStates (Array)
- **What it is:** Array of all game objects in the mod
- **Contains:** Object definitions with asset URLs
- **Each object has:**
  - `Name`: Object type (e.g., "Custom_Model", "Custom_Tile", "Card", "Deck")
  - `Nickname`: Display name
  - `Transform`: Position, rotation, scale
  - **Asset URLs**: References to external files (see below)

### Asset URLs in ObjectStates

**Critical Point:** The JSON does NOT store file metadata (sizes, dates, checksums) for assets. It ONLY stores URLs.

```json
{
  "ObjectStates": [
    {
      "Name": "Custom_Model",
      "Nickname": "Dragon Miniature",
      "Transform": { /* position data */ },

      // ONLY URLs ARE STORED - NO FILE METADATA
      "MeshURL": "http://cloud-3.steamusercontent.com/ugc/123456/model.obj",
      "DiffuseURL": "http://cloud-3.steamusercontent.com/ugc/123456/texture.png",
      "ColliderURL": "http://cloud-3.steamusercontent.com/ugc/123456/collider.obj"
    },
    {
      "Name": "Custom_Tile",
      "Nickname": "Map Tile",

      // ONLY URLs - NO SIZE, DATE, OR CHECKSUM
      "FaceURL": "http://cloud-3.steamusercontent.com/ugc/987654/face.png",
      "BackURL": "http://cloud-3.steamusercontent.com/ugc/987654/back.png"
    }
  ]
}
```

## What Is NOT Stored in JSON

### ❌ Asset File Metadata

The following information is **NOT stored** in TTS JSON files:

1. **File Sizes** - Asset file sizes are not recorded
2. **File Dates** - Individual asset creation/modification dates are not recorded
3. **Checksums/Hashes** - No CRC, MD5, SHA checksums
4. **File Names** - Only URLs are stored, filenames are derived from URLs
5. **MIME Types** - File types are inferred from URL extensions
6. **Download Status** - Whether assets are cached locally
7. **File Versions** - No version tracking for assets

### Why This Matters

**Implication:** You cannot compare asset files between a mod and a backup just by reading the JSON files.

To determine if assets have changed, you must:
1. Read the URLs from JSON
2. Extract filenames from URLs
3. Check if files exist on disk or in backup
4. Compare file sizes/dates by statting actual files
5. Optionally compute checksums for content comparison

**Example:**

```json
// JSON only contains:
"MeshURL": "http://steamusercontent.com/ugc/123456/dragon.obj"

// To get file metadata, you must:
// 1. Extract filename: "dragon.obj"
// 2. Find file in cache: "Mods/Models/dragon.obj"
// 3. Stat the file:
final stat = await File('Mods/Models/dragon.obj').stat();
final size = stat.size;           // Get size from filesystem
final modified = stat.modified;   // Get date from filesystem

// The JSON itself has NO size or date information for "dragon.obj"
```

## Filesystem Metadata (Not in JSON)

### JSON File Metadata

TTS Mod Vault **does** track metadata about the JSON file itself (not the assets):

```dart
// File metadata from filesystem
final jsonFileStat = await File(jsonPath).stat();

final Mod(
  jsonFilePath: jsonPath,
  saveName: extractedSaveName,
  dateTimeStamp: extractedDateFromJSON,      // From "Date" field IN JSON
  createdAtTimestamp: jsonFileStat.changed,   // From FILE SYSTEM
  // ... other fields
);
```

**Two different timestamps:**
1. `dateTimeStamp` - From `"Date"` field **inside** JSON (when mod was saved in TTS)
2. `createdAtTimestamp` - From **file system** (when JSON file was modified on disk)

These can differ if the JSON file is copied, imported, or downloaded.

## How TTS Mod Vault Extracts Metadata

### Extraction Process

TTS Mod Vault uses **regex patterns** instead of full JSON parsing for performance:

```dart
// Extract SaveName
final saveNameRegex = RegExp(r'"SaveName"\s*:\s*"([^"]*)"');
final match = saveNameRegex.firstMatch(jsonString);
final saveName = match?.group(1);

// Extract Date
final dateRegex = RegExp(r'"Date"\s*:\s*"([^"]*)"');
final match = dateRegex.firstMatch(jsonString);
final dateValue = match?.group(1);

// Extract Asset URLs
final assetKeyRegex = RegExp(r'"MeshURL"\s*:\s*"([^"]*)"');
// ... repeat for all asset key types
```

**Why regex instead of JSON parsing?**
- Large JSON files (50+ MB for complex mods)
- Only need specific fields, not entire structure
- Streaming approach - can stop early once fields found
- Much faster for large files

### Asset URL Extraction

```dart
// All possible asset keys
final assetKeys = [
  // Asset Bundles
  'AssetbundleURL', 'AssetbundleSecondaryURL',

  // Audio
  'CurrentAudioURL', 'Item1',

  // Images
  'FaceURL', 'BackURL', 'ImageURL', 'ImageSecondaryURL',
  'DiffuseURL', 'NormalURL', 'URL', 'TableURL', 'SkyURL', 'LutURL',

  // Models
  'MeshURL', 'ColliderURL',

  // PDF
  'PDFUrl',
];

// For each key, extract URL
for (final key in assetKeys) {
  final pattern = RegExp('"$key"\\s*:\\s*"([^"]*)"');
  final matches = pattern.allMatches(jsonString);

  for (final match in matches) {
    final url = match.group(1);
    // URL extracted - but NO file metadata
  }
}
```

## Comparing Mods vs Backups

### Challenge: No Asset Metadata in JSON

Since the JSON doesn't contain file sizes or dates for assets, comparison must be done by:

1. **Extracting URLs from both:**
   - Current mod JSON
   - Backup contents (or backup metadata)

2. **Checking file existence:**
   - Current: Check if files exist in TTS cache
   - Backup: Check if files exist in backup archive

3. **Comparing file lists:**
   - Added: URLs in current but not in backup
   - Removed: URLs in backup but not in current
   - Unchanged: URLs in both

4. **Optional: Deep comparison:**
   - Extract actual files from backup
   - Compare file sizes (from filesystem/archive metadata)
   - Compare checksums (requires reading file contents)

### Simple Comparison Strategy

**What TTS Mod Vault Can Compare:**

```dart
// 1. Mod Date (from JSON "Date" field)
if (mod.dateTimeStamp != backup.dateTimeStamp) {
  // Mod has been saved since backup
}

// 2. Asset Count
if (mod.assetCount != backup.totalAssetCount) {
  // Different number of assets
}

// 3. Asset List (from URLs)
final currentUrls = extractUrlsFromJson(mod.jsonPath);
final backupUrls = getBackupFileList(backup.filepath);

final added = currentUrls - backupUrls;
final removed = backupUrls - currentUrls;
```

**What Requires File Access:**

```dart
// File size comparison
final currentSize = File(assetPath).stat().size;
final backupSize = zipFile.size;  // From zip archive metadata

// Content comparison
final currentCrc = computeCrc32(File(assetPath));
final backupCrc = zipFile.crc32;  // From zip archive
```

## Example JSON Structure

### Minimal Mod Example

```json
{
  "SaveName": "Simple Test Mod",
  "Date": "12/23/2025 10:00:00 AM",
  "GameMode": "Tabletop Simulator",
  "ObjectStates": [
    {
      "Name": "Custom_Model",
      "GUID": "abc123",
      "Nickname": "Test Cube",
      "Transform": {
        "posX": 0,
        "posY": 1,
        "posZ": 0,
        "rotX": 0,
        "rotY": 0,
        "rotZ": 0,
        "scaleX": 1,
        "scaleY": 1,
        "scaleZ": 1
      },
      "MeshURL": "http://steamusercontent.com/ugc/123/cube.obj",
      "DiffuseURL": "http://steamusercontent.com/ugc/123/texture.png"
    }
  ]
}
```

**Metadata Available:**
- ✅ Mod name: "Simple Test Mod"
- ✅ Mod save date: "12/23/2025 10:00:00 AM"
- ✅ Asset URLs: 2 URLs found
- ❌ Asset file sizes: NOT in JSON
- ❌ Asset file dates: NOT in JSON
- ❌ Asset checksums: NOT in JSON

## Summary

### What IS in TTS JSON Files

1. **SaveName** - Mod display name
2. **Date** - When mod was last saved in TTS
3. **Asset URLs** - References to external files
4. **Object definitions** - Game object properties
5. **Game settings** - Table, sky, physics, etc.
6. **Scripts** - Lua code and UI definitions

### What is NOT in TTS JSON Files

1. ❌ Asset file sizes
2. ❌ Asset file modification dates
3. ❌ Asset file checksums/hashes
4. ❌ Asset file metadata
5. ❌ Download status
6. ❌ Cache locations
7. ❌ Version information for individual assets

### Key Insight

> **TTS JSON files are essentially "pointers" to external assets, not containers of asset metadata.**
>
> To compare mods and backups, you must:
> 1. Extract URLs from JSON (available)
> 2. Check actual files on disk or in archives (requires filesystem/archive access)
> 3. Compare file metadata from filesystem/archive, not from JSON

This is why TTS Mod Vault stores backup file metadata separately in Hive - the JSON alone doesn't provide enough information to determine what's in a backup without extracting it.

---

## Complete Field Reference

### All Top-Level Fields

Based on analysis of multiple TTS mods, here is a complete list of top-level fields found in deserialized JSON files:

#### Game Metadata
- **SaveName** (String) - Display name of the mod
- **Date** (String) - Last save timestamp  (format: `M/d/yyyy h:mm:ss a`)
- **EpochTime** (Integer) - Unix timestamp of last save
- **GameMode** (String) - Game mode (usually "Tabletop Simulator")
- **GameType** (String) - Type of game (e.g., "RPG", "Board Game")
- **GameComplexity** (String) - Complexity level (e.g., "Light", "Medium", "Heavy")
- **PlayerCounts** (Array[Integer]) - Supported player counts (e.g., `[1, 2, 3, 4]`)
- **PlayingTime** (Integer) - Expected playing time in minutes
- **Tags** (Array[String]) - Searchable tags for the mod
- **VersionNumber** (String) - TTS version number

#### Visual Settings
- **Table** (String) - Table type (e.g., "Table_RPG", "Table_Poker")
- **Sky** (String) - Sky type (e.g., "Sky_Museum", "Sky_Sunset")
- **SkyURL** (String) - Custom sky image URL
- **Grid** (Object) - Grid configuration
  - `Type` (Integer) - Grid type (0 = None, 1 = Square, 2 = Hex)
  - `Lines` (Boolean) - Show grid lines
  - `Color` (Object) - Grid color RGB
  - `Opacity` (Float) - Grid transparency
  - `ThickLines` (Boolean) - Use thick grid lines
  - `Snapping` (Boolean) - Enable grid snapping
  - `Offset` (Boolean) - Offset grid
  - `BothSnapping` (Boolean) - Snap both grid and object
  - `xSize` (Float) - Grid cell width
  - `ySize` (Float) - Grid cell height
  - `PosOffset` (Object) - Grid position offset {x, y, z}
- **Lighting** (Object) - Lighting configuration
  - `LightIntensity` (Float) - Main light intensity
  - `LightColor` (Object) - Light color RGB
  - `AmbientIntensity` (Float) - Ambient light intensity
  - `AmbientType` (Integer) - Ambient light type
  - `AmbientSkyColor` (Object) - Sky ambient color RGB
  - `AmbientEquatorColor` (Object) - Equator ambient color RGB
  - `AmbientGroundColor` (Object) - Ground ambient color RGB
  - `ReflectionIntensity` (Float) - Reflection strength
  - `LutIndex` (Integer) - Color lookup table index
  - `LutURL` (String) - Custom LUT image URL
- **DecalPallet** (Array) - Custom decals available in the mod

#### Physics & Interaction
- **Gravity** (Float) - Gravity strength (default: 0.5)
- **PlayArea** (Float) - Play area size multiplier
- **Hands** (Object) - Player hand configuration
  - `Enable` (Boolean) - Enable player hands
  - `DisableUnused` (Boolean) - Hide unused hand zones
  - `Hiding` (Integer) - Hand hiding mode (0 = Default, 1 = Reverse, 2 = Always)

#### Scripting & UI
- **LuaScript** (String) - Global Lua script code
- **LuaScriptState** (String) - Persisted Lua state data (JSON string)
- **XmlUI** (String) - XML UI definition
- **CustomUIAssets** (Array) - Custom UI asset URLs
- **ComponentTags** (Object) - Component tagging system
  - `labels` (Array) - Label definitions

#### Game Mechanics
- **Turns** (Object) - Turn order configuration
  - `Enable` (Boolean) - Enable turn system
  - `Type` (Integer) - Turn type
  - `TurnOrder` (Array) - Player turn order
  - `Reverse` (Boolean) - Reverse turn direction
  - `SkipEmpty` (Boolean) - Skip players with no objects
  - `DisableInteractions` (Boolean) - Disable interactions when not your turn
  - `PassTurns` (Boolean) - Allow passing turns
  - `TurnColor` (String) - Current player color

- **SnapPoints** (Array) - Predefined snap points on the table
- **TabStates** (Object) - Notebook tab states
- **MusicPlayer** (Object) - Music player state
  - `RepeatSong` (Boolean) - Loop current song
  - `PlaylistEntry` (Integer) - Current playlist index
  - `CurrentAudioURL` (String) - Currently playing audio URL
  - `CurrentAudioTitle` (String) - Current song title

#### Content
- **ObjectStates** (Array) - All game objects (see Object Fields below)
- **Note** (String) - Game notes (visible to all players)
- **Rules** (String) - Game rules text

### CustomDeck Fields

When cards are present, they reference CustomDeck definitions with these fields:

- **FaceURL** (String) - URL to card face sprite sheet
- **BackURL** (String) - URL to card back image or sprite sheet
- **NumWidth** (Integer) - Number of cards horizontally in sprite sheet
- **NumHeight** (Integer) - Number of cards vertically in sprite sheet
- **BackIsHidden** (Boolean) - Whether back is hidden by default
- **UniqueBack** (Boolean) - Whether each card has a unique back (BackURL is a sprite sheet)
- **Type** (Integer) - Card type (0 = Standard, 1 = Square, 2 = Hex)

**Example:**
```json
{
  "CustomDeck": {
    "25": {
      "FaceURL": "https://steamusercontent.com/ugc/.../faces.png",
      "BackURL": "https://steamusercontent.com/ugc/.../backs.png",
      "NumWidth": 8,
      "NumHeight": 3,
      "BackIsHidden": false,
      "UniqueBack": true,
      "Type": 0
    }
  }
}
```

### Card Object Fields

Objects with `"Name": "Card"` or `"Name": "CardCustom"` have these fields:

#### Identity
- **GUID** (String) - Unique object identifier
- **Name** (String) - Object type ("Card", "CardCustom")
- **Nickname** (String) - Display name
- **Description** (String) - Object description
- **GMNotes** (String) - GM-only notes

#### Card-Specific
- **CardID** (Integer) - Card identifier (format: DDDPP where DDD = deck ID, PP = position in sprite sheet)
- **CustomDeck** (Object) - Reference to CustomDeck definition(s)
- **SidewaysCard** (Boolean) - Whether card is oriented sideways
- **Value** (Integer) - Card numeric value (for traditional decks)

#### Transform & Placement
- **Transform** (Object) - Position, rotation, scale
  - `posX`, `posY`, `posZ` (Float) - Position coordinates
  - `rotX`, `rotY`, `rotZ` (Float) - Rotation angles
  - `scaleX`, `scaleY`, `scaleZ` (Float) - Scale multipliers
- **AltLookAngle** (Object) - Alternate viewing angle {x, y, z}

#### Behavior & State
- **Locked** (Boolean) - Whether object is locked in place
- **Grid** (Boolean) - Whether object snaps to grid
- **Snap** (Boolean) - Whether object snaps to snap points
- **Autoraise** (Boolean) - Auto-raise when picked up
- **Sticky** (Boolean) - Stick to other objects
- **Tooltip** (Boolean) - Show tooltip on hover
- **GridProjection** (Boolean) - Project grid onto object
- **HideWhenFaceDown** (Boolean) - Hide face when card is face down
- **Hands** (Boolean) - Can be held in player hands
- **DragSelectable** (Boolean) - Can be drag-selected
- **IgnoreFoW** (Boolean) - Ignore fog of war
- **MeasureMovement** (Boolean) - Measure movement with ruler

#### Visual
- **ColorDiffuse** (Object) - Tint color {r, g, b}
- **LayoutGroupSortIndex** (Integer) - Sort order in groups
- **AttachedSnapPoints** (Array) - Snap points attached to this object

#### Scripting
- **LuaScript** (String) - Object-specific Lua script
- **LuaScriptState** (String) - Object-specific Lua state
- **XmlUI** (String) - Object-specific XML UI

#### Containers (for Card inside Deck)
- **ContainedObjects** (Array) - Objects contained within (if this is a container)

### Deck Object Fields

Objects with `"Name": "Deck"` contain multiple cards:

All fields from Card Object (above), plus:

- **DeckIDs** (Array[Integer]) - Array of CardIDs for all cards in the deck
- **ContainedObjects** (Array[Object]) - Array of all card objects in the deck

**Example:**
```json
{
  "Name": "Deck",
  "GUID": "abc123",
  "Nickname": "Player Deck",
  "DeckIDs": [2500, 2501, 2502, 2503],
  "CustomDeck": {
    "25": {
      "FaceURL": "https://...",
      "BackURL": "https://...",
      "NumWidth": 10,
      "NumHeight": 7
    }
  },
  "ContainedObjects": [
    {
      "Name": "Card",
      "CardID": 2500,
      "Nickname": "Ace of Spades"
    },
    // ... more cards
  ]
}
```

### Important Card/Deck Concepts

#### CardID Format: DDDPP

- **DDD** = Deck ID (e.g., 25 for CustomDeck "25")
- **PP** = Position in sprite sheet (0-based, row-major order)

**Example:** CardID `2537` means:
- Deck ID: 25
- Position: 37 in the sprite sheet
- If sprite sheet is 10×7 (70 positions), position 37 is:
  - Row: 37 ÷ 10 = 3 (4th row, 0-indexed)
  - Column: 37 % 10 = 7 (8th column, 0-indexed)

#### UniqueBack for Double-Sided Printing

When `"UniqueBack": true`:
- `BackURL` points to a sprite sheet (not a single image)
- Each card has a unique back at the same position as its face
- Both `FaceURL` and `BackURL` use the same grid dimensions (`NumWidth` × `NumHeight`)
- Critical for generating double-sided printable PDFs

### Common Object Types

#### Cards & Decks
- `Card` - Single card from standard TTS deck
- `CardCustom` - Custom card with URLs
- `Deck` - Multiple cards stacked together

#### Tiles & Boards
- `Custom_Tile` - Flat custom image (tiles, tokens)
- `Custom_Board` - Larger board piece

#### 3D Objects
- `Custom_Model` - Custom 3D model with mesh
- `Custom_Assetbundle` - Unity asset bundle

#### Containers
- `Bag` - Generic bag container
- `Custom_Model_Bag` - Custom 3D bag
- `Infinite_Bag` - Infinite token source

#### Dice
- `Custom_Dice` - Custom dice with images
- `Die_6`, `Die_8`, `Die_12`, `Die_20` - Standard dice

#### Special
- `ScriptingTrigger` - Invisible scripting zone
- `HandTrigger` - Player hand zone
- `Custom_PDF` - PDF viewer object

---

## Field Discovery Notes

This documentation was expanded by analyzing multiple TTS mods:
- Eternal Decks (3637615329)
- Stardew Valley The Board Game (3639937524)
- Ada's Dream (3642212076)

Fields were extracted by recursive JSON traversal across different mod types to ensure comprehensive coverage of the TTS JSON structure.

