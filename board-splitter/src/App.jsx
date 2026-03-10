import { useState, useRef, useCallback, useEffect } from 'react'
import './App.css'

const MIN_ZOOM = 0.05
const MAX_ZOOM = 2.0
const ZOOM_STEP = 1.15

// How close (in screen px) the mouse must be to an inner edge to show a handle
const EDGE_THRESHOLD_PX = 12
// Handle visual size in screen px
const HANDLE_SIZE_PX = 8

const COLORS = [
  '#ff0000', '#00cc00', '#0066ff', '#ffcc00',
  '#ff00ff', '#00cccc', '#ff8800', '#8800ff',
  '#00ff88', '#ff4444', '#44ff44', '#4444ff',
  '#ffaa00', '#aa00ff', '#00ffaa', '#ff0088',
]

// Detect which inner edge(s) the mouse is near.
// Returns null or { sectionId, edge } where edge is 'left'|'right'|'top'|'bottom'
function detectEdge(boardPos, sections, zoom, boardWidth, boardHeight) {
  const threshold = EDGE_THRESHOLD_PX / zoom // convert screen px to board px
  for (let i = sections.length - 1; i >= 0; i--) {
    const s = sections[i]
    const { x, y, w, h } = s
    const bx = boardPos.x
    const by = boardPos.y
    // Must be inside the rectangle
    if (bx < x || bx > x + w || by < y || by > y + h) continue

    const distLeft = bx - x
    const distRight = (x + w) - bx
    const distTop = by - y
    const distBottom = (y + h) - by

    const min = Math.min(distLeft, distRight, distTop, distBottom)
    if (min > threshold) continue

    let edge = null
    if (min === distLeft) edge = 'left'
    else if (min === distRight) edge = 'right'
    else if (min === distTop) edge = 'top'
    else edge = 'bottom'

    return { sectionId: s.id, edge }
  }
  return null
}

function edgeCursor(edge) {
  if (edge === 'left' || edge === 'right') return 'ew-resize'
  if (edge === 'top' || edge === 'bottom') return 'ns-resize'
  return 'crosshair'
}

function App() {
  // Board dimensions detected from image
  const [boardSize, setBoardSize] = useState(null) // { width, height }

  const [sections, setSections] = useState([])
  const [drawing, setDrawing] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [editingName, setEditingName] = useState(null)

  // Zoom & pan state
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [panning, setPanning] = useState(null)
  const [mode, setMode] = useState('draw') // 'draw' or 'pan'

  // Edge resize state
  const [hoveredEdge, setHoveredEdge] = useState(null) // { sectionId, edge }
  const [resizing, setResizing] = useState(null) // { sectionId, edge, startPos, origSection }

  const canvasRef = useRef(null)
  const containerRef = useRef(null)

  const BOARD_WIDTH = boardSize?.width ?? 0
  const BOARD_HEIGHT = boardSize?.height ?? 0

  // Handle image load — detect dimensions and fit to view
  const handleImageLoad = useCallback((e) => {
    const { naturalWidth, naturalHeight } = e.target
    setBoardSize({ width: naturalWidth, height: naturalHeight })
    if (containerRef.current) {
      const cw = containerRef.current.clientWidth
      const ch = containerRef.current.clientHeight
      const fitZoom = Math.min(cw / naturalWidth, ch / naturalHeight)
      setZoom(fitZoom)
      setPan({ x: (cw - naturalWidth * fitZoom) / 2, y: (ch - naturalHeight * fitZoom) / 2 })
    }
  }, [])

  const toBoard = useCallback((clientX, clientY) => {
    const rect = containerRef.current.getBoundingClientRect()
    return {
      x: Math.round(Math.max(0, Math.min(BOARD_WIDTH, (clientX - rect.left - pan.x) / zoom))),
      y: Math.round(Math.max(0, Math.min(BOARD_HEIGHT, (clientY - rect.top - pan.y) / zoom))),
    }
  }, [zoom, pan, BOARD_WIDTH, BOARD_HEIGHT])

  // Ctrl/Cmd+scroll: zoom, otherwise scroll to pan (both axes)
  const handleWheel = useCallback((e) => {
    e.preventDefault()

    if (e.ctrlKey || e.metaKey) {
      // Zoom toward cursor
      const rect = containerRef.current.getBoundingClientRect()
      const mouseX = e.clientX - rect.left
      const mouseY = e.clientY - rect.top
      const boardX = (mouseX - pan.x) / zoom
      const boardY = (mouseY - pan.y) / zoom
      const direction = e.deltaY < 0 ? 1 : -1
      const newZoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, zoom * (direction > 0 ? ZOOM_STEP : 1 / ZOOM_STEP)))
      setPan({ x: mouseX - boardX * newZoom, y: mouseY - boardY * newZoom })
      setZoom(newZoom)
    } else {
      // Pan using both axes (handles trackpad, shift+scroll, etc.)
      setPan(p => ({ x: p.x - e.deltaX, y: p.y - e.deltaY }))
    }
  }, [zoom, pan])

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    el.addEventListener('wheel', handleWheel, { passive: false })
    return () => el.removeEventListener('wheel', handleWheel)
  }, [handleWheel])

  const handleMouseDown = useCallback((e) => {
    if (e.button !== 0) return

    // Pan mode
    if (mode === 'pan') {
      setPanning({ startX: e.clientX, startY: e.clientY, startPanX: pan.x, startPanY: pan.y })
      return
    }

    const pos = toBoard(e.clientX, e.clientY)

    // If hovering an edge handle, start resizing
    if (hoveredEdge) {
      const section = sections.find(s => s.id === hoveredEdge.sectionId)
      if (section) {
        setResizing({
          sectionId: section.id,
          edge: hoveredEdge.edge,
          startPos: pos,
          origSection: { ...section },
        })
        return
      }
    }

    // Double-click to select
    const clicked = [...sections].reverse().find(s =>
      pos.x >= s.x && pos.x <= s.x + s.w && pos.y >= s.y && pos.y <= s.y + s.h
    )
    if (clicked && e.detail === 2) {
      setSelectedId(clicked.id)
      return
    }

    setSelectedId(null)
    setDrawing({ startX: pos.x, startY: pos.y, curX: pos.x, curY: pos.y })
  }, [toBoard, sections, mode, pan, hoveredEdge])

  const handleMouseMove = useCallback((e) => {
    // Panning
    if (panning) {
      setPan({ x: panning.startPanX + (e.clientX - panning.startX), y: panning.startPanY + (e.clientY - panning.startY) })
      return
    }

    const pos = toBoard(e.clientX, e.clientY)

    // Resizing
    if (resizing) {
      const { edge, origSection: os } = resizing
      const MIN_SIZE = 30
      setSections(prev => prev.map(s => {
        if (s.id !== resizing.sectionId) return s
        let { x, y, w, h } = os
        if (edge === 'left') {
          const newX = Math.min(pos.x, x + w - MIN_SIZE)
          w = (x + w) - newX
          x = newX
        } else if (edge === 'right') {
          w = Math.max(MIN_SIZE, pos.x - x)
        } else if (edge === 'top') {
          const newY = Math.min(pos.y, y + h - MIN_SIZE)
          h = (y + h) - newY
          y = newY
        } else if (edge === 'bottom') {
          h = Math.max(MIN_SIZE, pos.y - y)
        }
        return { ...s, x, y, w, h }
      }))
      return
    }

    // Drawing
    if (drawing) {
      setDrawing(prev => ({ ...prev, curX: pos.x, curY: pos.y }))
      return
    }

    // Hover detection for edge handles (only in draw mode, not panning)
    if (mode === 'draw') {
      const detected = detectEdge(pos, sections, zoom, BOARD_WIDTH, BOARD_HEIGHT)
      setHoveredEdge(detected)
    }
  }, [drawing, panning, resizing, toBoard, sections, zoom, mode, BOARD_WIDTH, BOARD_HEIGHT])

  const handleMouseUp = useCallback(() => {
    if (panning) { setPanning(null); return }
    if (resizing) { setResizing(null); return }
    if (!drawing) return

    const x = Math.min(drawing.startX, drawing.curX)
    const y = Math.min(drawing.startY, drawing.curY)
    const w = Math.abs(drawing.curX - drawing.startX)
    const h = Math.abs(drawing.curY - drawing.startY)
    if (w > 20 && h > 20) {
      const id = Date.now()
      setSections(prev => [...prev, {
        id, x, y, w, h,
        name: `Section ${prev.length + 1}`,
        color: COLORS[prev.length % COLORS.length],
      }])
      setSelectedId(id)
    }
    setDrawing(null)
  }, [drawing, panning, resizing])

  // Space key toggles pan mode
  useEffect(() => {
    const down = (e) => {
      if (e.code === 'Space' && !editingName) { e.preventDefault(); setMode('pan') }
    }
    const up = (e) => {
      if (e.code === 'Space') { setMode('draw'); setPanning(null) }
    }
    window.addEventListener('keydown', down)
    window.addEventListener('keyup', up)
    return () => { window.removeEventListener('keydown', down); window.removeEventListener('keyup', up) }
  }, [editingName])

  const deleteSection = useCallback((id) => {
    setSections(prev => prev.filter(s => s.id !== id))
    if (selectedId === id) setSelectedId(null)
  }, [selectedId])

  const updateSection = useCallback((id, updates) => {
    setSections(prev => prev.map(s => s.id === id ? { ...s, ...updates } : s))
  }, [])

  const fitToView = useCallback(() => {
    if (!containerRef.current || !boardSize) return
    const cw = containerRef.current.clientWidth
    const ch = containerRef.current.clientHeight
    const fitZoom = Math.min(cw / BOARD_WIDTH, ch / BOARD_HEIGHT)
    setZoom(fitZoom)
    setPan({ x: (cw - BOARD_WIDTH * fitZoom) / 2, y: (ch - BOARD_HEIGHT * fitZoom) / 2 })
  }, [BOARD_WIDTH, BOARD_HEIGHT, boardSize])

  const exportJSON = useCallback(() => {
    const data = sections.map(({ name, x, y, w, h }, i) => ({
      index: i + 1, name, x, y, w, h, right: x + w, bottom: y + h,
    }))
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'board_sections.json'; a.click()
    URL.revokeObjectURL(url)
  }, [sections])

  const importJSON = useCallback(() => {
    const input = document.createElement('input'); input.type = 'file'; input.accept = '.json'
    input.onchange = (e) => {
      const file = e.target.files[0]; if (!file) return
      const reader = new FileReader()
      reader.onload = (ev) => {
        try {
          const data = JSON.parse(ev.target.result)
          setSections(data.map((s, i) => ({
            id: Date.now() + i, x: s.x, y: s.y,
            w: s.w || (s.right - s.x), h: s.h || (s.bottom - s.y),
            name: s.name || `Section ${i + 1}`, color: COLORS[i % COLORS.length],
          })))
        } catch { alert('Invalid JSON file') }
      }
      reader.readAsText(file)
    }
    input.click()
  }, [])

  // Delete / Escape keys
  useEffect(() => {
    const handler = (e) => {
      if ((e.key === 'Delete' || e.key === 'Backspace') && selectedId && !editingName) {
        e.preventDefault(); deleteSection(selectedId)
      }
      if (e.key === 'Escape') { setSelectedId(null); setDrawing(null) }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [selectedId, editingName, deleteSection])

  const drawingRect = drawing ? {
    x: Math.min(drawing.startX, drawing.curX),
    y: Math.min(drawing.startY, drawing.curY),
    w: Math.abs(drawing.curX - drawing.startX),
    h: Math.abs(drawing.curY - drawing.startY),
  } : null

  // Compute cursor style
  let cursor = 'crosshair'
  if (mode === 'pan' || panning) cursor = panning ? 'grabbing' : 'grab'
  else if (resizing) cursor = edgeCursor(resizing.edge)
  else if (hoveredEdge) cursor = edgeCursor(hoveredEdge.edge)

  // Build handle positions for rendering
  const handleSize = HANDLE_SIZE_PX / zoom
  const handles = []
  if (hoveredEdge && !resizing && !drawing) {
    const s = sections.find(sec => sec.id === hoveredEdge.sectionId)
    if (s) {
      const { edge } = hoveredEdge
      const midX = s.x + s.w / 2
      const midY = s.y + s.h / 2
      if (edge === 'left') {
        handles.push({ x: s.x - handleSize / 2, y: midY - handleSize * 2, w: handleSize, h: handleSize * 4, edge, color: s.color })
      } else if (edge === 'right') {
        handles.push({ x: s.x + s.w - handleSize / 2, y: midY - handleSize * 2, w: handleSize, h: handleSize * 4, edge, color: s.color })
      } else if (edge === 'top') {
        handles.push({ x: midX - handleSize * 2, y: s.y - handleSize / 2, w: handleSize * 4, h: handleSize, edge, color: s.color })
      } else if (edge === 'bottom') {
        handles.push({ x: midX - handleSize * 2, y: s.y + s.h - handleSize / 2, w: handleSize * 4, h: handleSize, edge, color: s.color })
      }
    }
  }

  // Loading state
  if (!boardSize) {
    return (
      <div className="app">
        <div className="loading">
          <img
            src="/board.png"
            alt=""
            style={{ display: 'none' }}
            onLoad={handleImageLoad}
            onError={() => setBoardSize({ width: 0, height: 0, error: true })}
          />
          {boardSize?.error ? (
            <p>No board image found. Place an image at <code>public/board.png</code> or use <code>tts-board-splitter</code>.</p>
          ) : (
            <p>Loading board image...</p>
          )}
        </div>
      </div>
    )
  }

  if (boardSize.error) {
    return (
      <div className="app">
        <div className="loading">
          <p>No board image found. Place an image at <code>public/board.png</code> or use <code>tts-board-splitter &lt;image&gt;</code>.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      <div className="toolbar">
        <h2>Board Section Splitter</h2>
        <span className="info">
          {BOARD_WIDTH}×{BOARD_HEIGHT}px &nbsp;|&nbsp;
          {sections.length} section(s) &nbsp;|&nbsp;
          Drag: draw &nbsp;|&nbsp; Space+drag: pan &nbsp;|&nbsp;
          Scroll: pan &nbsp;|&nbsp; {navigator.platform.includes('Mac') ? '\u2318' : 'Ctrl'}+scroll: zoom &nbsp;|&nbsp;
          Edge handles: resize &nbsp;|&nbsp; Dbl-click: select &nbsp;|&nbsp; Del: remove
        </span>
        <div className="toolbar-buttons">
          <button onClick={fitToView} title="Fit to view">Fit</button>
          <button onClick={() => setZoom(z => Math.min(MAX_ZOOM, z * ZOOM_STEP))}>+</button>
          <button onClick={() => setZoom(z => Math.max(MIN_ZOOM, z / ZOOM_STEP))}>&minus;</button>
          <span className="zoom-label">{Math.round(zoom * 1000) / 10}%</span>
          <span className="separator" />
          <button onClick={exportJSON} disabled={sections.length === 0}>Export JSON</button>
          <button onClick={importJSON}>Import JSON</button>
          <button className="danger" onClick={() => { setSections([]); setSelectedId(null) }} disabled={sections.length === 0}>Clear All</button>
        </div>
      </div>

      <div className="main">
        <div
          className="canvas-container"
          ref={containerRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          style={{ cursor }}
        >
          <div
            ref={canvasRef}
            className="canvas"
            style={{
              width: BOARD_WIDTH,
              height: BOARD_HEIGHT,
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              transformOrigin: '0 0',
            }}
          >
            <img
              src="/board.png"
              alt="Board"
              style={{ width: BOARD_WIDTH, height: BOARD_HEIGHT, display: 'block' }}
              draggable={false}
            />
            {/* Section rectangles */}
            {sections.map((s) => (
              <div
                key={s.id}
                className={`section-rect ${selectedId === s.id ? 'selected' : ''}`}
                style={{
                  left: s.x, top: s.y, width: s.w, height: s.h,
                  '--color': s.color,
                  borderWidth: Math.max(2, 3 / zoom),
                }}
                onDoubleClick={(e) => { e.stopPropagation(); setSelectedId(s.id) }}
              >
                <span
                  className="section-label"
                  style={{
                    backgroundColor: s.color,
                    fontSize: Math.max(12, 16 / zoom),
                    padding: `${Math.max(1, 2 / zoom)}px ${Math.max(3, 6 / zoom)}px`,
                  }}
                >
                  {s.name}
                </span>
              </div>
            ))}
            {/* Edge resize handles */}
            {handles.map((h, i) => (
              <div
                key={`handle-${i}`}
                className="edge-handle"
                style={{
                  left: h.x, top: h.y, width: h.w, height: h.h,
                  backgroundColor: h.color,
                }}
              />
            ))}
            {/* Drawing preview */}
            {drawingRect && drawingRect.w > 20 && drawingRect.h > 20 && (
              <div
                className="section-rect drawing"
                style={{
                  left: drawingRect.x, top: drawingRect.y,
                  width: drawingRect.w, height: drawingRect.h,
                  borderWidth: Math.max(2, 3 / zoom),
                }}
              >
                <span className="drawing-size" style={{ fontSize: Math.max(12, 14 / zoom) }}>
                  {drawingRect.w} &times; {drawingRect.h}
                </span>
              </div>
            )}
          </div>
        </div>

        <div className="sidebar">
          <h3>Sections</h3>
          <div className="section-list">
            {sections.map((s) => (
              <div
                key={s.id}
                className={`section-item ${selectedId === s.id ? 'selected' : ''}`}
                onClick={() => setSelectedId(s.id)}
              >
                <div className="section-header">
                  <span className="section-color" style={{ backgroundColor: s.color }} />
                  {editingName === s.id ? (
                    <input
                      className="name-input"
                      value={s.name}
                      onChange={(e) => updateSection(s.id, { name: e.target.value })}
                      onBlur={() => setEditingName(null)}
                      onKeyDown={(e) => { if (e.key === 'Enter') setEditingName(null) }}
                      autoFocus
                    />
                  ) : (
                    <span className="section-name" onDoubleClick={() => setEditingName(s.id)}>
                      {s.name}
                    </span>
                  )}
                  <button className="delete-btn" onClick={(e) => { e.stopPropagation(); deleteSection(s.id) }}>&times;</button>
                </div>
                <div className="section-coords">
                  ({s.x}, {s.y}) &rarr; ({s.x + s.w}, {s.y + s.h}) &nbsp; {s.w}&times;{s.h}px
                </div>
                {selectedId === s.id && (
                  <div className="section-edit">
                    <label>x <input type="number" value={s.x} onChange={e => updateSection(s.id, { x: +e.target.value })} /></label>
                    <label>y <input type="number" value={s.y} onChange={e => updateSection(s.id, { y: +e.target.value })} /></label>
                    <label>w <input type="number" value={s.w} onChange={e => updateSection(s.id, { w: +e.target.value })} /></label>
                    <label>h <input type="number" value={s.h} onChange={e => updateSection(s.id, { h: +e.target.value })} /></label>
                  </div>
                )}
              </div>
            ))}
          </div>
          {sections.length === 0 && (
            <p className="hint">Click and drag on the board to create sections.<br/>Hold Space + drag to pan. Scroll to pan both axes.<br/>{navigator.platform.includes('Mac') ? '\u2318' : 'Ctrl'}+scroll to zoom.<br/>Hover inner edges to resize.</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
