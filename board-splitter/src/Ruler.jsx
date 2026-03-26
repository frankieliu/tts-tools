// Ruler component — draws inch-based rulers at viewport edges.
// Ticks: 1" (major, labeled), 1/2", 1/4", 1/8".
// 0" = board origin. Rulers track zoom/pan so measurements stay consistent.

import { useRef, useEffect } from 'react'

export const RULER_SIZE = 24

const BG = '#16213e'
const TICK = '#8899bb'
const TEXT = '#aabbcc'
const BORDER = '#333'

// Tick heights as fraction of ruler thickness
const TICK_H = { 1: 0.8, 0.5: 0.55, 0.25: 0.35, 0.125: 0.2 }

function drawRuler(canvas, length, zoom, panOffset, dpi, isVertical) {
  const dpr = window.devicePixelRatio || 1
  if (isVertical) {
    canvas.width = RULER_SIZE * dpr
    canvas.height = length * dpr
  } else {
    canvas.width = length * dpr
    canvas.height = RULER_SIZE * dpr
  }
  canvas.style.width = isVertical ? `${RULER_SIZE}px` : `${length}px`
  canvas.style.height = isVertical ? `${length}px` : `${RULER_SIZE}px`

  const ctx = canvas.getContext('2d')
  ctx.scale(dpr, dpr)

  // Background
  ctx.fillStyle = BG
  ctx.fillRect(0, 0, isVertical ? RULER_SIZE : length, isVertical ? length : RULER_SIZE)

  // Border along content edge
  ctx.strokeStyle = BORDER
  ctx.lineWidth = 1
  if (isVertical) {
    ctx.beginPath(); ctx.moveTo(RULER_SIZE - 0.5, 0); ctx.lineTo(RULER_SIZE - 0.5, length); ctx.stroke()
  } else {
    ctx.beginPath(); ctx.moveTo(0, RULER_SIZE - 0.5); ctx.lineTo(length, RULER_SIZE - 0.5); ctx.stroke()
  }

  const ppi = dpi * zoom // pixels per inch in viewport space

  // Choose which subdivisions to show based on available space
  const subs = ppi >= 48 ? [1, 0.5, 0.25, 0.125]
    : ppi >= 24 ? [1, 0.5, 0.25]
    : ppi >= 12 ? [1, 0.5]
    : [1]

  // Label frequency — skip labels when they'd overlap
  const labelEvery = ppi < 6 ? 20 : ppi < 12 ? 10 : ppi < 24 ? 5 : ppi < 40 ? 2 : 1

  // Visible range in inches
  const startInch = Math.floor(-panOffset / ppi) - 1
  const endInch = Math.ceil((length - panOffset) / ppi) + 1

  // Smallest subdivision step
  const step = subs[subs.length - 1]

  ctx.fillStyle = TEXT
  ctx.font = '10px -apple-system, BlinkMacSystemFont, sans-serif'

  for (let inchVal = startInch; inchVal <= endInch + 1; inchVal += step) {
    // Round to avoid float drift
    const inch = Math.round(inchVal * 1000) / 1000
    const vPos = inch * ppi + panOffset
    if (vPos < -10 || vPos > length + 10) continue

    // Determine tick level
    let tickFrac
    const absInch = Math.abs(inch)
    if (Math.abs(inch - Math.round(inch)) < 0.001) tickFrac = 1
    else if (Math.abs((absInch * 2) % 1) < 0.01) tickFrac = 0.5
    else if (Math.abs((absInch * 4) % 1) < 0.01) tickFrac = 0.25
    else tickFrac = 0.125

    // Skip if this subdivision isn't active
    if (!subs.includes(tickFrac)) continue

    const h = RULER_SIZE * TICK_H[tickFrac]
    const p = Math.round(vPos) + 0.5

    ctx.strokeStyle = TICK
    ctx.lineWidth = tickFrac === 1 ? 1 : 0.5
    ctx.beginPath()
    if (isVertical) {
      ctx.moveTo(RULER_SIZE, p); ctx.lineTo(RULER_SIZE - h, p)
    } else {
      ctx.moveTo(p, RULER_SIZE); ctx.lineTo(p, RULER_SIZE - h)
    }
    ctx.stroke()

    // Label at whole inches
    if (tickFrac === 1 && inch >= 0 && Math.round(inch) % labelEvery === 0) {
      const label = String(Math.round(inch))
      if (isVertical) {
        ctx.save()
        ctx.translate(10, Math.round(vPos) - 3)
        ctx.rotate(-Math.PI / 2)
        ctx.textAlign = 'left'
        ctx.textBaseline = 'middle'
        ctx.fillText(label, 0, 0)
        ctx.restore()
      } else {
        ctx.textAlign = 'left'
        ctx.textBaseline = 'top'
        ctx.fillText(label, Math.round(vPos) + 3, 2)
      }
    }
  }
}

export function Ruler({ position, zoom, pan, dpi, containerWidth, containerHeight }) {
  const canvasRef = useRef(null)
  const isVertical = position === 'left'
  // Offset by RULER_SIZE to leave room for the corner block
  const length = isVertical ? containerHeight - RULER_SIZE : containerWidth - RULER_SIZE
  const panOffset = (isVertical ? pan.y : pan.x) - RULER_SIZE

  useEffect(() => {
    if (!canvasRef.current || length <= 0) return
    drawRuler(canvasRef.current, length, zoom, panOffset, dpi, isVertical)
  }, [length, zoom, panOffset, dpi, isVertical])

  const style = {
    position: 'absolute',
    pointerEvents: 'none',
    zIndex: 10,
  }
  if (position === 'top') {
    Object.assign(style, { top: 0, left: RULER_SIZE })
  } else if (position === 'bottom') {
    Object.assign(style, { bottom: 0, left: RULER_SIZE })
  } else {
    Object.assign(style, { top: RULER_SIZE, left: 0 })
  }

  return <canvas ref={canvasRef} style={style} />
}

export function RulerCorner({ frozen, onToggleFreeze }) {
  return (
    <div
      onClick={onToggleFreeze}
      title={frozen ? 'Unfreeze rulers' : 'Freeze rulers'}
      style={{
        position: 'absolute', top: 0, left: 0,
        width: RULER_SIZE, height: RULER_SIZE,
        background: frozen ? '#3a2020' : BG,
        borderRight: `1px solid ${frozen ? '#ff6644' : BORDER}`,
        borderBottom: `1px solid ${frozen ? '#ff6644' : BORDER}`,
        zIndex: 11,
        cursor: 'pointer',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 13,
        color: frozen ? '#ff6644' : TICK,
        userSelect: 'none',
        transition: 'background 0.15s, color 0.15s',
      }}
    >
      {frozen ? '\u229E' : '\u229F'}
    </div>
  )
}
