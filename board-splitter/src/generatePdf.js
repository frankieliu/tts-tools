// Browser-based PDF generation for board sections using pdf-lib.
// Each section is cropped from the board image, split into pages, and downloaded as a PDF.

import { PDFDocument, rgb } from 'pdf-lib'
import { calcPageSplit, PAGE_W, PAGE_H } from './pageSplit.js'

// Convert inches to PDF points (72 points per inch)
const IN_TO_PT = 72

// Crop a rectangle from an image element using an offscreen canvas.
// Returns a canvas element with the cropped region.
function cropFromImage(imageEl, sx, sy, sw, sh) {
  const canvas = document.createElement('canvas')
  canvas.width = sw
  canvas.height = sh
  const ctx = canvas.getContext('2d')
  ctx.drawImage(imageEl, sx, sy, sw, sh, 0, 0, sw, sh)
  return canvas
}

// Get PNG bytes from a canvas region. If the source region extends beyond
// the canvas (due to centering offset), fills excess area with white.
async function getCellPng(sectionCanvas, cellX, cellY, cellW, cellH) {
  const canvas = document.createElement('canvas')
  canvas.width = Math.round(cellW)
  canvas.height = Math.round(cellH)
  const ctx = canvas.getContext('2d')

  // White background for edge pages with partial content
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  // Calculate intersection between the cell rect and the actual section content
  const drawX = Math.max(0, -cellX)
  const drawY = Math.max(0, -cellY)
  const srcX = Math.max(0, cellX)
  const srcY = Math.max(0, cellY)
  const srcW = Math.min(sectionCanvas.width - srcX, cellW - drawX)
  const srcH = Math.min(sectionCanvas.height - srcY, cellH - drawY)

  if (srcW > 0 && srcH > 0) {
    ctx.drawImage(sectionCanvas, srcX, srcY, srcW, srcH, drawX, drawY, srcW, srcH)
  }

  const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'))
  return new Uint8Array(await blob.arrayBuffer())
}

// Generate and download PDFs for all sections.
// imageEl: the <img> element of the board
// sections: array of { name, x, y, w, h }
// dpi: pixels per inch
// margin: page margin in inches
export async function generateSectionPdfs(imageEl, sections, dpi, margin) {
  for (const section of sections) {
    const sectionCanvas = cropFromImage(imageEl, section.x, section.y, section.w, section.h)
    const split = calcPageSplit(section.w, section.h, dpi, margin)
    const { cols, rows, usableW, usableH, orientation, offsetX, offsetY } = split

    // Page dimensions in points
    const pageWPt = (orientation === 'landscape' ? PAGE_H : PAGE_W) * IN_TO_PT
    const pageHPt = (orientation === 'landscape' ? PAGE_W : PAGE_H) * IN_TO_PT
    const marginPt = margin * IN_TO_PT
    const usableWPt = usableW * IN_TO_PT
    const usableHPt = usableH * IN_TO_PT

    // Cell size in section pixels
    const cellWPx = usableW * dpi
    const cellHPx = usableH * dpi

    const totalPages = cols * rows
    const pdfDoc = await PDFDocument.create()

    for (let pageIdx = 0; pageIdx < totalPages; pageIdx++) {
      const col = pageIdx % cols
      const row = Math.floor(pageIdx / cols)

      // Cell origin in section pixels, accounting for centering offset
      const cellX = col * cellWPx - offsetX
      const cellY = row * cellHPx - offsetY

      const pngBytes = await getCellPng(sectionCanvas, cellX, cellY, cellWPx, cellHPx)
      const pngImage = await pdfDoc.embedPng(pngBytes)

      const page = pdfDoc.addPage([pageWPt, pageHPt])

      // Draw image in the usable area (within margins)
      page.drawImage(pngImage, {
        x: marginPt,
        y: pageHPt - marginPt - usableHPt,
        width: usableWPt,
        height: usableHPt,
      })

      // Assembly label
      const label = `Page ${pageIdx + 1}/${totalPages} (Row ${row + 1}, Col ${col + 1})`
      const physW = (Math.min(cellWPx, section.w - (cellX > 0 ? cellX : 0)) / dpi).toFixed(1)
      const physH = (Math.min(cellHPx, section.h - (cellY > 0 ? cellY : 0)) / dpi).toFixed(1)
      const sizeLabel = `${physW}" x ${physH}"`
      page.drawText(`${label}  ${sizeLabel}`, {
        x: marginPt,
        y: marginPt * 0.6,
        size: 7,
        color: rgb(0.5, 0.5, 0.5),
      })
    }

    const pdfBytes = await pdfDoc.save()
    const blob = new Blob([pdfBytes], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    // Sanitize filename
    const safeName = section.name.replace(/[^a-zA-Z0-9_\- ]/g, '').replace(/\s+/g, '_') || 'section'
    a.download = `${safeName}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  }
}
