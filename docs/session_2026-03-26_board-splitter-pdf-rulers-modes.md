---
date: 2026-03-26
session_theme: Add browser PDF generation, rulers, and draw/edit modes to board splitter
files_changed:
  - board-splitter/package.json
  - board-splitter/package-lock.json
  - board-splitter/src/App.jsx
  - board-splitter/src/App.css
  - board-splitter/src/pageSplit.js
  - board-splitter/src/generatePdf.js
  - board-splitter/src/Ruler.jsx
reference_docs:
  - docs/board-splitter-architecture.md
scripts_saved: []
scripts_promoted: []
---

# Session: Board Splitter — Browser PDF, Rulers, Draw/Edit Modes

## 1. Installed pdf-lib dependency

Added `pdf-lib` to `board-splitter/package.json` for in-browser PDF generation without a server.

```bash
cd board-splitter && npm install pdf-lib
```

## 2. Extracted page split logic into shared module

Created `board-splitter/src/pageSplit.js` extracting `splitBoard()` and `calcPageSplit()` from `App.jsx`. Added **centering offsets** (`offsetX`, `offsetY`) to `calcPageSplit()` return value so the page grid centers content within the total grid area rather than anchoring to the top-left corner.

Centering formula:
```
totalGridWPx = cols * usableW * dpi
offsetX = (totalGridWPx - sectionWidthPx) / 2
```

Split lines in section pixels:
```
splitLineX[i] = usableW * dpi * (i+1) - offsetX
```

## 3. Created browser PDF generation module

Created `board-splitter/src/generatePdf.js` with `generateSectionPdfs()`. For each section:
1. Crops section from board image using offscreen `<canvas>`
2. Calculates page grid via shared `calcPageSplit()`
3. For each page cell: crops region accounting for centering offset, draws onto cell-sized canvas with white background for edge pages, exports as PNG
4. Creates PDF page via pdf-lib, embeds PNG at margin offset, adds assembly label
5. Downloads each section as `{section_name}.pdf`

## 4. Updated App.jsx grid overlay for centering

Updated the visual overlay (dashed grid lines and page number labels) to use the centering offsets from `calcPageSplit()` instead of the old even-division formula `(i+1)/cols * width`.

Page number labels now compute visible cell bounds accounting for offset and center within the visible portion.

## 5. Added Generate PDFs button

Added a "Generate PDFs" button in the sidebar PDF Settings area. Uses `boardImgRef` on the `<img>` element. Shows "Generating..." state while working. Disabled when no sections exist.

## 6. Added DPI to JSON export/import

`exportJSON` now wraps data as `{ dpi, sections: [...] }`. `importJSON` handles both the new format and the old flat-array format for backwards compatibility. Restores DPI setting on import.

## 7. Added inch rulers

Created `board-splitter/src/Ruler.jsx` with three components:

- **`Ruler`** — Canvas-based ruler at top, bottom, or left edge. Graduated in inches using the current DPI. Tick marks at 1", 1/2", 1/4", 1/8" intervals (smaller ticks auto-hide when zoomed out). Label frequency adapts to zoom level.
- **`RulerCorner`** — Top-left corner block where rulers meet. Acts as a freeze toggle button.
- **Ruler freeze** — Click corner to freeze rulers in place while panning/zooming. Click again to unfreeze and snap back to live tracking. Visual indicator (red tint) when frozen.

Rulers track `pan` and `zoom` in real-time. Uses `ResizeObserver` to track container dimensions.

## 8. Refactored into Draw/Edit modes

Replaced the single interaction mode with two explicit modes:

| Feature | Draw mode (D) | Edit mode (V) |
|---|---|---|
| Click+drag on empty area | Creates new section | Deselects |
| Click on section | Draws over it | Selects it |
| Drag inside section | Draws over it | Moves section |
| Drag edge | — | Resizes section |
| Double-click section | Switch to Edit | Rename |
| Double-click empty | — | Switch to Draw |
| Delete/Backspace | — | Deletes selected |
| Tab near edges | — | Cycles edge candidates |

Key implementation details:
- `switchMode()` helper clears all interaction state (drawing, dragging, resizing, panning, edge candidates) when switching modes
- Toolbar toggle buttons with SVG icons
- `D` / `V` keyboard shortcuts
- `Space+drag` pans in both modes
- Section dragging has 5px dead zone to allow double-click without micro-moving

## 9. Added Tab edge cycling for disambiguation

`detectAllEdges()` replaces the old `detectEdge()` — finds ALL edges within the grab threshold, sorted by distance. State tracks `edgeCandidates` array and `edgeCandidateIdx`.

Press Tab to cycle through candidates. A label appears near the handle: `Section 2 (left edge) [Tab 2/3]`.

## 10. Fixed double-click rename

Initial `e.detail === 2` approach in `handleMouseDown` was unreliable — the edge resize check ran first, and React re-renders between clicks could cause stale closures. Fixed by using a dedicated `onDoubleClick` handler on the canvas-container, which fires reliably after both clicks complete and cancels any in-progress drag/resize.

## 11. Added double-click mode switching

Double-click in Draw mode → switches to Edit (selects section if clicked on one).
Double-click on empty area in Edit mode → switches to Draw.

## 12. Committed and pushed

Committed as `c4c689f` with only board-splitter files. Pushed to `main`.

## 13. Reference docs created

- `docs/board-splitter-architecture.md` — Architecture overview of the board splitter UI: module structure, mode system, page split math, ruler implementation, PDF generation flow
