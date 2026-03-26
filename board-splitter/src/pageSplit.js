// Shared page split calculations for board section splitting.
// Used by both the visual overlay (App.jsx) and PDF generator (generatePdf.js).

// Letter page size in inches
export const PAGE_W = 8.5
export const PAGE_H = 11.0
export const DEFAULT_DPI = 125
export const DEFAULT_MARGIN = 0.25

// Port of split_board from generate_board_pdf.py
export function splitBoard(boardWidthIn, boardHeightIn, pageW, pageH, margin, overlap = 0) {
  const usableW = pageW - 2 * margin
  const usableH = pageH - 2 * margin

  let cols, rows
  if (boardWidthIn <= usableW) {
    cols = 1
  } else {
    cols = 1 + Math.ceil((boardWidthIn - usableW) / (usableW - overlap))
  }
  if (boardHeightIn <= usableH) {
    rows = 1
  } else {
    rows = 1 + Math.ceil((boardHeightIn - usableH) / (usableH - overlap))
  }
  return { cols, rows, usableW, usableH }
}

// Calculate page split for a section, auto-detecting orientation.
// Returns cols, rows, usableW, usableH, orientation, boardW, boardH,
// and centering offsets (offsetX, offsetY) in section pixels.
export function calcPageSplit(widthPx, heightPx, dpi, margin) {
  const boardW = widthPx / dpi
  const boardH = heightPx / dpi

  // Portrait
  const portrait = splitBoard(boardW, boardH, PAGE_W, PAGE_H, margin)
  // Landscape
  const landscape = splitBoard(boardW, boardH, PAGE_H, PAGE_W, margin)

  const portraitPages = portrait.cols * portrait.rows
  const landscapePages = landscape.cols * landscape.rows

  // Use landscape if board is wider than tall AND it reduces page count
  let result
  if (boardW > boardH && landscapePages < portraitPages) {
    result = { ...landscape, orientation: 'landscape', boardW, boardH }
  } else {
    result = { ...portrait, orientation: 'portrait', boardW, boardH }
  }

  // Calculate centering offsets in section pixels.
  // The grid covers cols*usableW x rows*usableH inches, which may exceed
  // the actual board dimensions. Center the board content within that grid.
  const totalGridWPx = result.cols * result.usableW * dpi
  const totalGridHPx = result.rows * result.usableH * dpi
  result.offsetX = (totalGridWPx - widthPx) / 2
  result.offsetY = (totalGridHPx - heightPx) / 2

  return result
}
