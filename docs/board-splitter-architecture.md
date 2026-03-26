# Board Splitter — Architecture Reference

The board splitter is a React (Vite) app that lets users define rectangular sections on a board image, preview how each section splits across printed pages, and generate PDFs directly in the browser.

## Module Structure

```
board-splitter/src/
├── App.jsx          # Main component: modes, mouse handlers, UI
├── App.css          # All styles (dark theme)
├── pageSplit.js     # Shared page split math (used by overlay + PDF gen)
├── generatePdf.js   # Browser PDF generation via pdf-lib + canvas
├── Ruler.jsx        # Inch rulers (top, bottom, left) + freeze toggle
└── main.jsx         # Entry point
```

## Mode System

Two primary modes controlled by `mode` state (`'draw'` | `'edit'`):

### Draw Mode
- `handleMouseDown` → starts `drawing` state with `{startX, startY, curX, curY}`
- `handleMouseMove` → updates `curX, curY`
- `handleMouseUp` → creates section if w>20 && h>20, adds to `sections` array

### Edit Mode
- **Select**: click on section → `setSelectedId()`
- **Move**: click+drag inside section → `setDragging()` with 5px dead zone (allows double-click)
- **Resize**: hover edge → `edgeCandidates` populated by `detectAllEdges()`, click starts `setResizing()`
- **Rename**: `onDoubleClick` handler (separate from mouseDown) → `setEditingName()` shows input in sidebar
- **Tab cycling**: when multiple edges overlap, Tab increments `edgeCandidateIdx`

### Mode Switching
- Toolbar buttons or D/V keys
- `switchMode()` clears ALL interaction state to prevent cross-mode bugs
- Double-click: Draw→Edit (on anything), Edit→Draw (on empty area)
- `Space+drag` pans in both modes (temporary `spaceHeld` flag)

## Page Split Math (`pageSplit.js`)

Constants: `PAGE_W=8.5"`, `PAGE_H=11"`, `DEFAULT_DPI=125`, `DEFAULT_MARGIN=0.25"`

### `splitBoard(boardW, boardH, pageW, pageH, margin, overlap)`
Port of Python `split_board()`. Returns `{cols, rows, usableW, usableH}`.

```
usableW = pageW - 2*margin
cols = 1 if boardW <= usableW else 1 + ceil((boardW - usableW) / (usableW - overlap))
```

### `calcPageSplit(widthPx, heightPx, dpi, margin)`
Auto-detects portrait vs landscape (uses landscape if board is wider than tall AND it reduces page count).

Returns: `{cols, rows, usableW, usableH, orientation, boardW, boardH, offsetX, offsetY}`

**Centering offsets** — the grid of `cols*usableW × rows*usableH` may be larger than the actual content. Offsets center the content:
```
totalGridWPx = cols * usableW * dpi
offsetX = (totalGridWPx - widthPx) / 2
```

Grid split lines in section pixels:
```
splitLineX[i] = usableW * dpi * (i+1) - offsetX   // for i = 0..cols-2
```

## Edge Detection (`detectAllEdges`)

Returns ALL edges within `EDGE_THRESHOLD_PX / zoom` board-pixels, sorted by distance. Each candidate has `{sectionId, sectionName, edge, dist, color}`.

Checks all 4 edges of each section, requires the cursor to be within the edge's perpendicular extent (e.g., left/right edges require cursor between top and bottom of section).

## Ruler Implementation (`Ruler.jsx`)

Canvas-based rulers drawn with 2D context at the device pixel ratio.

### Tick System
- Subdivisions shown based on `pxPerInch = dpi * zoom`:
  - ≥48px: 1", 1/2", 1/4", 1/8"
  - ≥24px: 1", 1/2", 1/4"
  - ≥12px: 1", 1/2"
  - <12px: 1" only
- Label frequency adapts: every 1" normally, every 2/5/10/20" when zoomed out

### Positioning
- Rulers offset by `RULER_SIZE=24px` to leave room for the corner block
- Pan offset adjusted: `panOffset = pan.x - RULER_SIZE` (horizontal) or `pan.y - RULER_SIZE` (vertical)
- `ResizeObserver` tracks container dimensions

### Freeze Toggle
- `RulerCorner` button toggles `rulerFrozen` state
- When frozen, rulers receive a snapshot of `{x: pan.x, y: pan.y, zoom}` instead of live values
- Visual indicator: red-tinted background and orange border

## PDF Generation (`generatePdf.js`)

Uses `pdf-lib` (pure JS, no server) + offscreen `<canvas>` for image cropping.

### Flow per section:
1. **Crop section** from board `<img>` element via `drawImage` with source rect
2. **Calculate page grid** via `calcPageSplit()`
3. **For each page cell** (col, row):
   - Compute cell origin: `cellX = col * cellWPx - offsetX`
   - `getCellPng()`: creates canvas, fills white, draws intersection of cell rect with section content
   - Embed PNG in PDF page via `pdfDoc.embedPng()`
   - Draw at margin offset, add assembly label text
4. **Download** as `{sanitized_name}.pdf`

### Page sizing
- Points = inches × 72
- Page dimensions respect portrait/landscape from `calcPageSplit()`
- Image drawn at `(marginPt, pageHPt - marginPt - usableHPt)` (PDF y-axis is bottom-up)

## JSON Export Format

```json
{
  "dpi": 125,
  "sections": [
    {
      "index": 1,
      "name": "Section 1",
      "x": 100, "y": 200,
      "w": 500, "h": 400,
      "right": 600, "bottom": 600
    }
  ]
}
```

Import handles both this format and the legacy flat array format (no `dpi` wrapper).

## CSS Architecture

Dark theme (`#1a1a2e` background, `#16213e` panels). Key classes:

- `.mode-toggle` / `.mode-btn` — pill-shaped toggle with `.active` highlight
- `.section-rect` — uses CSS `var(--color)` for per-section coloring, `color-mix()` for translucent fill
- `.edge-handle` — resize grab indicators
- `.edge-label` — disambiguation tooltip for Tab cycling
- `.page-split-line` / `.page-number-label` — grid overlay
- `.generate-btn` — blue-bordered action button
