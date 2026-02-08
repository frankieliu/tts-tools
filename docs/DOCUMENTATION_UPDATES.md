# TTS JSON Structure Documentation Updates

## Summary

Updated `TTS_JSON_STRUCTURE.md` with comprehensive field documentation discovered through analysis of multiple TTS mods.

## What Was Added

### 1. Complete Top-Level Fields (30+ fields documented)

#### New Game Metadata Fields:
- `EpochTime` - Unix timestamp
- `GameType` - Type of game (RPG, Board Game, etc.)
- `GameComplexity` - Complexity level
- `PlayerCounts` - Supported player counts
- `PlayingTime` - Expected duration in minutes
- `Tags` - Searchable tags

#### New Visual Settings:
- `SkyURL` - Custom sky image
- `Grid` - Complete grid configuration object with 12 sub-fields
- `Lighting` - Complete lighting configuration with 10 sub-fields
- `DecalPallet` - Custom decals

#### New Physics & Interaction:
- `Hands` - Complete hand configuration object

#### New Scripting & UI:
- `CustomUIAssets` - Custom UI resources
- `ComponentTags` - Component tagging system

#### New Game Mechanics:
- `Turns` - Complete turn system with 8 sub-fields
- `SnapPoints` - Predefined snap points
- `MusicPlayer` - Music player state with 4 sub-fields

### 2. CustomDeck Fields (Complete)

Previously only implied, now fully documented:
- `FaceURL`
- `BackURL`
- `NumWidth`
- `NumHeight`
- `BackIsHidden`
- `UniqueBack` - **Critical for double-sided printing**
- `Type`

### 3. Card/CardCustom Object Fields (35+ fields)

Organized into categories:
- **Identity** (5 fields): GUID, Name, Nickname, Description, GMNotes
- **Card-Specific** (4 fields): CardID, CustomDeck, SidewaysCard, Value
- **Transform & Placement** (2 objects): Transform, AltLookAngle
- **Behavior & State** (13 fields): Locked, Grid, Snap, Autoraise, etc.
- **Visual** (2 fields): ColorDiffuse, LayoutGroupSortIndex
- **Scripting** (3 fields): LuaScript, LuaScriptState, XmlUI
- **Containers** (1 field): ContainedObjects

### 4. Deck Object Fields

- All Card fields plus:
- `DeckIDs` - Array of all CardIDs in deck
- `ContainedObjects` - Array of all card objects

### 5. Important Concepts Documented

#### CardID Format
- Explained DDDPP format (Deck ID + Position)
- Example calculation showing how to extract position from CardID

#### UniqueBack for Printing
- Explained critical importance for double-sided printing
- How BackURL sprite sheet works with same grid dimensions as FaceURL

### 6. Common Object Types Reference

Documented 16 common object types:
- Cards & Decks (3 types)
- Tiles & Boards (2 types)
- 3D Objects (2 types)
- Containers (3 types)
- Dice (5 types)
- Special (3 types)

## Analysis Process

Fields were discovered by:
1. Analyzing 3+ different TTS mods across multiple genres
2. Recursive JSON traversal to find all fields at all depths
3. Categorizing fields by purpose and location
4. Cross-referencing with actual usage in real mods

## File Statistics

- **Original:** 395 lines
- **Updated:** 661 lines
- **Added:** 266 lines of new documentation
- **New Sections:** 7 major sections added

## Files Analyzed

- Eternal Decks (3637615329) - Card game with unique backs
- Stardew Valley The Board Game (3639937524) - Complex board game
- Ada's Dream (3642212076) - Scripted game

## Impact

This comprehensive documentation now covers:
- ✅ All common top-level fields
- ✅ Complete CustomDeck structure (critical for card printing)
- ✅ All object fields found in real mods
- ✅ Important concepts like CardID format and UniqueBack
- ✅ Common object type reference

The documentation is now suitable for:
- Building TTS mod parsers
- Generating printable PDFs from TTS mods
- Understanding TTS save file structure
- Extracting assets and metadata
