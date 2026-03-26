import { useState, useRef, useCallback, useEffect } from 'react'
import './App.css'
import { calcPageSplit, DEFAULT_DPI, DEFAULT_MARGIN } from './pageSplit.js'
import { generateSectionPdfs } from './generatePdf.js'
import { Ruler, RulerCorner, RULER_SIZE } from './Ruler.jsx'

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

// Detect ALL edges within threshold, sorted by distance (nearest first).
// Returns array of { sectionId, sectionName, edge, dist }
function detectAllEdges(boardPos, sections, zoom) {
  const threshold = EDGE_THRESHOLD_PX / zoom
  const candidates = []
  for (const s of sections) {
    const { x, y, w, h } = s
    const bx = boardPos.x
    const by = boardPos.y
    if (bx < x - threshold || bx > x + w + threshold ||
        by < y - threshold || by > y + h + threshold) continue

    const edges = [
      { edge: 'left', dist: Math.abs(bx - x), inY: by >= y && by <= y + h },
      { edge: 'right', dist: Math.abs(bx - (x + w)), inY: by >= y && by <= y + h },
      { edge: 'top', dist: Math.abs(by - y), inX: bx >= x && bx <= x + w },
      { edge: 'bottom', dist: Math.abs(by - (y + h)), inX: bx >= x && bx <= x + w },
    ]
    for (const e of edges) {
      const inRange = (e.edge === 'left' || e.edge === 'right') ? e.inY : e.inX
      if (e.dist <= threshold && inRange) {
        candidates.push({
          sectionId: s.id,
          sectionName: s.name,
          edge: e.edge,
          dist: e.dist,
          color: s.color,
        })
      }
    }
  }
  candidates.sort((a, b) => a.dist - b.dist)
  return candidates
}

function edgeCursor(edge) {
  if (edge === 'left' || edge === 'right') return 'ew-resize'
  if (edge === 'top' || edge === 'bottom') return 'ns-resize'
  return 'default'
}

function hitTestSection(pos, sections) {
  return [...sections].reverse().find(s =>
    pos.x >= s.x && pos.x <= s.x + s.w && pos.y >= s.y && pos.y <= s.y + s.h
  )
}

// Letter page size in inches
const PAGE_W = 8.5
const PAGE_H = 11.0

function App() {
  // Board dimensions detected from image
  const [boardSize, setBoardSize] = useState(null)

  const [sections, setSections] = useState([])
  const [drawing, setDrawing] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [editingName, setEditingName] = useState(null)

  // Zoom & pan state
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [panning, setPanning] = useState(null)

  // Mode: 'draw' or 'edit'. Space temporarily enables panning in either mode.
  const [mode, setMode] = useState('draw')
  const [spaceHeld, setSpaceHeld] = useState(false)

  // Edge resize state
  const [edgeCandidates, setEdgeCandidates] = useState([]) // all edges near cursor
  const [edgeCandidateIdx, setEdgeCandidateIdx] = useState(0) // which one is active
  const [resizing, setResizing] = useState(null)

  // Section dragging state (Edit mode)
  const [dragging, setDragging] = useState(null) // { sectionId, startPos, origSection }

  // Clear all interaction state when switching modes
  const switchMode = useCallback((newMode) => {
    setMode(newMode)
    setDrawing(null)
    setDragging(null)
    setResizing(null)
    setPanning(null)
    setEdgeCandidates([])
    setEdgeCandidateIdx(0)
  }, [])

  // PDF split preview state
  const [dpi, setDpi] = useState(DEFAULT_DPI)
  const [showPageSplits, setShowPageSplits] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [containerSize, setContainerSize] = useState({ w: 0, h: 0 })
  const [rulerFrozen, setRulerFrozen] = useState(false)
  const [frozenPan, setFrozenPan] = useState(null)

  const canvasRef = useRef(null)
  const containerRef = useRef(null)
  const boardImgRef = useRef(null)

  const BOARD_WIDTH = boardSize?.width ?? 0
  const BOARD_HEIGHT = boardSize?.height ?? 0

  // The currently active edge candidate
  const activeEdge = edgeCandidates.length > 0 ? edgeCandidates[edgeCandidateIdx % edgeCandidates.length] : null

  // Track container dimensions for rulers
  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const ro = new ResizeObserver(([entry]) => {
      setContainerSize({ w: entry.contentRect.width, h: entry.contentRect.height })
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [boardSize])

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

  // Ctrl/Cmd+scroll: zoom, otherwise scroll to pan
  const handleWheel = useCallback((e) => {
    e.preventDefault()
    if (e.ctrlKey || e.metaKey) {
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
      setPan(p => ({ x: p.x - e.deltaX, y: p.y - e.deltaY }))
    }
  }, [zoom, pan])

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    el.addEventListener('wheel', handleWheel, { passive: false })
    return () => el.removeEventListener('wheel', handleWheel)
  }, [handleWheel])

  // --- Mouse handlers ---

  const handleMouseDown = useCallback((e) => {
    if (e.button !== 0) return

    // Space+click = pan in any mode
    if (spaceHeld) {
      setPanning({ startX: e.clientX, startY: e.clientY, startPanX: pan.x, startPanY: pan.y })
      return
    }

    const pos = toBoard(e.clientX, e.clientY)

    if (mode === 'draw') {
      // Draw mode: always start drawing a new section
      setSelectedId(null)
      setDrawing({ startX: pos.x, startY: pos.y, curX: pos.x, curY: pos.y })
      return
    }

    // --- Edit mode ---

    // If hovering an edge handle, start resizing
    if (activeEdge) {
      const section = sections.find(s => s.id === activeEdge.sectionId)
      if (section) {
        setResizing({
          sectionId: section.id,
          edge: activeEdge.edge,
          startPos: pos,
          origSection: { ...section },
        })
        return
      }
    }

    // Click on a section — select and start potential drag
    const clicked = hitTestSection(pos, sections)
    if (clicked) {
      setSelectedId(clicked.id)
      setDragging({
        sectionId: clicked.id,
        startPos: pos,
        origSection: { ...clicked },
        started: false,
      })
      return
    }

    // Click on empty area: deselect
    setSelectedId(null)
  }, [toBoard, sections, mode, pan, spaceHeld, activeEdge])

  const handleMouseMove = useCallback((e) => {
    // Panning
    if (panning) {
      setPan({ x: panning.startPanX + (e.clientX - panning.startX), y: panning.startPanY + (e.clientY - panning.startY) })
      return
    }

    const pos = toBoard(e.clientX, e.clientY)

    // Resizing (edit mode)
    if (resizing) {
      const { edge, origSection: os } = resizing
      const MIN_SIZE = 30
      setSections(prev => prev.map(s => {
        if (s.id !== resizing.sectionId) return s
        let { x, y, w, h } = os
        if (edge === 'left') {
          const newX = Math.min(pos.x, x + w - MIN_SIZE)
          w = (x + w) - newX; x = newX
        } else if (edge === 'right') {
          w = Math.max(MIN_SIZE, pos.x - x)
        } else if (edge === 'top') {
          const newY = Math.min(pos.y, y + h - MIN_SIZE)
          h = (y + h) - newY; y = newY
        } else if (edge === 'bottom') {
          h = Math.max(MIN_SIZE, pos.y - y)
        }
        return { ...s, x, y, w, h }
      }))
      return
    }

    // Dragging section (edit mode) — require minimum distance to start
    if (dragging) {
      const dx = pos.x - dragging.startPos.x
      const dy = pos.y - dragging.startPos.y
      const dist = Math.abs(dx) + Math.abs(dy)
      if (!dragging.started && dist < 5) return // dead zone to allow double-click
      if (!dragging.started) {
        setDragging(prev => ({ ...prev, started: true }))
      }
      const os = dragging.origSection
      setSections(prev => prev.map(s => {
        if (s.id !== dragging.sectionId) return s
        return {
          ...s,
          x: Math.max(0, Math.min(BOARD_WIDTH - os.w, os.x + dx)),
          y: Math.max(0, Math.min(BOARD_HEIGHT - os.h, os.y + dy)),
        }
      }))
      return
    }

    // Drawing (draw mode)
    if (drawing) {
      setDrawing(prev => ({ ...prev, curX: pos.x, curY: pos.y }))
      return
    }

    // Hover detection for edge handles (edit mode only, not while space panning)
    if (mode === 'edit' && !spaceHeld) {
      const candidates = detectAllEdges(pos, sections, zoom)
      setEdgeCandidates(candidates)
      // Reset index when candidates change (unless Tab is being used)
      if (candidates.length === 0) setEdgeCandidateIdx(0)
    } else {
      setEdgeCandidates([])
    }
  }, [drawing, panning, resizing, dragging, toBoard, sections, zoom, mode, spaceHeld, BOARD_WIDTH, BOARD_HEIGHT])

  const handleMouseUp = useCallback(() => {
    if (panning) { setPanning(null); return }
    if (resizing) { setResizing(null); return }
    if (dragging) { setDragging(null); return }
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
  }, [drawing, panning, resizing, dragging])

  const handleDoubleClick = useCallback((e) => {
    const pos = toBoard(e.clientX, e.clientY)
    const clicked = hitTestSection(pos, sections)

    if (mode === 'draw') {
      // Double-click in draw mode → switch to edit
      switchMode('edit')
      if (clicked) setSelectedId(clicked.id)
      return
    }

    // Edit mode
    if (clicked) {
      // Double-click on section → rename
      setDragging(null)
      setResizing(null)
      setSelectedId(clicked.id)
      setEditingName(clicked.id)
    } else {
      // Double-click on empty area → switch to draw
      switchMode('draw')
    }
  }, [mode, toBoard, sections, switchMode])

  // Keyboard shortcuts: Space for pan, D/V for mode, Tab for edge cycling, Delete
  useEffect(() => {
    const down = (e) => {
      if (editingName) return // don't intercept while editing a name

      if (e.code === 'Space') {
        e.preventDefault()
        setSpaceHeld(true)
      } else if (e.key === 'd' || e.key === 'D') {
        switchMode('draw')
      } else if (e.key === 'v' || e.key === 'V') {
        switchMode('edit')
      } else if (e.key === 'Tab' && edgeCandidates.length > 1) {
        e.preventDefault()
        setEdgeCandidateIdx(prev => (prev + 1) % edgeCandidates.length)
      } else if ((e.key === 'Delete' || e.key === 'Backspace') && selectedId) {
        e.preventDefault()
        setSections(prev => prev.filter(s => s.id !== selectedId))
        setSelectedId(null)
      } else if (e.key === 'Escape') {
        setSelectedId(null)
        setDrawing(null)
        setEditingName(null)
      }
    }
    const up = (e) => {
      if (e.code === 'Space') {
        setSpaceHeld(false)
        setPanning(null)
      }
    }
    window.addEventListener('keydown', down)
    window.addEventListener('keyup', up)
    return () => { window.removeEventListener('keydown', down); window.removeEventListener('keyup', up) }
  }, [editingName, selectedId, edgeCandidates.length, switchMode])

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
    const data = {
      dpi,
      sections: sections.map(({ name, x, y, w, h }, i) => ({
        index: i + 1, name, x, y, w, h, right: x + w, bottom: y + h,
      })),
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'board_sections.json'; a.click()
    URL.revokeObjectURL(url)
  }, [sections, dpi])

  const importJSON = useCallback(() => {
    const input = document.createElement('input'); input.type = 'file'; input.accept = '.json'
    input.onchange = (e) => {
      const file = e.target.files[0]; if (!file) return
      const reader = new FileReader()
      reader.onload = (ev) => {
        try {
          const raw = JSON.parse(ev.target.result)
          const arr = Array.isArray(raw) ? raw : raw.sections
          if (raw.dpi) setDpi(raw.dpi)
          setSections(arr.map((s, i) => ({
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

  const handleGeneratePdfs = useCallback(async () => {
    if (!boardImgRef.current || sections.length === 0) return
    setGenerating(true)
    try {
      await generateSectionPdfs(boardImgRef.current, sections, dpi, DEFAULT_MARGIN)
    } catch (err) {
      console.error('PDF generation failed:', err)
      alert('PDF generation failed: ' + err.message)
    } finally {
      setGenerating(false)
    }
  }, [sections, dpi])

  // --- Computed values for rendering ---

  const drawingRect = drawing ? {
    x: Math.min(drawing.startX, drawing.curX),
    y: Math.min(drawing.startY, drawing.curY),
    w: Math.abs(drawing.curX - drawing.startX),
    h: Math.abs(drawing.curY - drawing.startY),
  } : null

  // Cursor
  let cursor = mode === 'draw' ? 'crosshair' : 'default'
  if (spaceHeld || panning) cursor = panning ? 'grabbing' : 'grab'
  else if (resizing) cursor = edgeCursor(resizing.edge)
  else if (dragging) cursor = 'move'
  else if (mode === 'edit' && activeEdge) cursor = edgeCursor(activeEdge.edge)
  else if (mode === 'edit') {
    // Show move cursor when hovering a section in edit mode
    // (We'd need the current mouse pos for this — approximate with last known)
  }

  // Build handle positions for the active edge
  const handleSize = HANDLE_SIZE_PX / zoom
  const handles = []
  if (mode === 'edit' && activeEdge && !resizing && !drawing && !dragging) {
    const s = sections.find(sec => sec.id === activeEdge.sectionId)
    if (s) {
      const { edge } = activeEdge
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

  // Edge label for Tab cycling disambiguation
  const edgeLabel = (mode === 'edit' && edgeCandidates.length > 1 && activeEdge)
    ? `${activeEdge.sectionName} (${activeEdge.edge} edge) [Tab ${(edgeCandidateIdx % edgeCandidates.length) + 1}/${edgeCandidates.length}]`
    : null

  // Mode-specific help text
  const helpText = mode === 'draw'
    ? 'Click+drag: draw section | Space+drag: pan | D/V: switch mode'
    : 'Click: select | Drag: move | Edges: resize | Tab: cycle edges | Dbl-click: rename | Del: remove | D/V: switch mode'

  // --- Loading states ---

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
        <div className="mode-toggle">
          <button
            className={`mode-btn ${mode === 'draw' ? 'active' : ''}`}
            onClick={() => switchMode('draw')}
            title="Draw mode (D)"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M2 14 L12 4 L14 2 L12 4 L2 14Z" />
              <path d="M2 14 L1 15" />
              <rect x="3" y="3" width="10" height="10" rx="1" strokeDasharray="2 2" />
            </svg>
            Draw
          </button>
          <button
            className={`mode-btn ${mode === 'edit' ? 'active' : ''}`}
            onClick={() => switchMode('edit')}
            title="Edit mode (V)"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M4 1 L1 6 L4 6 L4 15" />
              <path d="M4 1 L7 6 L4 6" />
            </svg>
            Edit
          </button>
        </div>
        <span className="info">
          {BOARD_WIDTH}&times;{BOARD_HEIGHT}px &nbsp;|&nbsp;
          {sections.length} section(s) &nbsp;|&nbsp;
          {helpText}
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
          onDoubleClick={handleDoubleClick}
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
              ref={boardImgRef}
              src="/board.png"
              alt="Board"
              style={{ width: BOARD_WIDTH, height: BOARD_HEIGHT, display: 'block' }}
              draggable={false}
            />
            {/* Section rectangles */}
            {sections.map((s) => {
              const split = calcPageSplit(s.w, s.h, dpi, DEFAULT_MARGIN)
              return (
              <div
                key={s.id}
                className={`section-rect ${selectedId === s.id ? 'selected' : ''}`}
                style={{
                  left: s.x, top: s.y, width: s.w, height: s.h,
                  '--color': s.color,
                  borderWidth: Math.max(2, 3 / zoom),
                }}
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
                {/* Page split grid overlay */}
                {showPageSplits && split.cols > 0 && split.rows > 0 && (
                  <>
                    {/* Vertical split lines (centered) */}
                    {Array.from({ length: split.cols - 1 }, (_, i) => {
                      const xPos = split.usableW * dpi * (i + 1) - split.offsetX
                      return (
                        <div
                          key={`v${i}`}
                          className="page-split-line page-split-vertical"
                          style={{
                            left: xPos,
                            top: 0,
                            height: s.h,
                            borderLeftWidth: Math.max(1, 2 / zoom),
                            borderLeftColor: s.color,
                          }}
                        />
                      )
                    })}
                    {/* Horizontal split lines (centered) */}
                    {Array.from({ length: split.rows - 1 }, (_, i) => {
                      const yPos = split.usableH * dpi * (i + 1) - split.offsetY
                      return (
                        <div
                          key={`h${i}`}
                          className="page-split-line page-split-horizontal"
                          style={{
                            top: yPos,
                            left: 0,
                            width: s.w,
                            borderTopWidth: Math.max(1, 2 / zoom),
                            borderTopColor: s.color,
                          }}
                        />
                      )
                    })}
                    {/* Page number labels (centered) */}
                    {Array.from({ length: split.cols * split.rows }, (_, i) => {
                      const col = i % split.cols
                      const row = Math.floor(i / split.cols)
                      const cellWPx = split.usableW * dpi
                      const cellHPx = split.usableH * dpi
                      const cellLeft = Math.max(0, col * cellWPx - split.offsetX)
                      const cellRight = Math.min(s.w, (col + 1) * cellWPx - split.offsetX)
                      const cellTop = Math.max(0, row * cellHPx - split.offsetY)
                      const cellBottom = Math.min(s.h, (row + 1) * cellHPx - split.offsetY)
                      const visW = cellRight - cellLeft
                      const visH = cellBottom - cellTop
                      const labelSize = Math.max(10, Math.min(20, Math.min(visW, visH) * 0.3))
                      return (
                        <span
                          key={`p${i}`}
                          className="page-number-label"
                          style={{
                            left: cellLeft + visW / 2,
                            top: cellTop + visH / 2,
                            fontSize: labelSize,
                            backgroundColor: s.color,
                          }}
                        >
                          {i + 1}
                        </span>
                      )
                    })}
                  </>
                )}
              </div>
            )})}

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

            {/* Edge disambiguation label */}
            {edgeLabel && activeEdge && (() => {
              const s = sections.find(sec => sec.id === activeEdge.sectionId)
              if (!s) return null
              let lx, ly
              if (activeEdge.edge === 'left') { lx = s.x; ly = s.y + s.h / 2 }
              else if (activeEdge.edge === 'right') { lx = s.x + s.w; ly = s.y + s.h / 2 }
              else if (activeEdge.edge === 'top') { lx = s.x + s.w / 2; ly = s.y }
              else { lx = s.x + s.w / 2; ly = s.y + s.h }
              return (
                <span
                  className="edge-label"
                  style={{
                    left: lx, top: ly,
                    fontSize: Math.max(10, 12 / zoom),
                    backgroundColor: activeEdge.color,
                  }}
                >
                  {edgeLabel}
                </span>
              )
            })()}

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
          {/* Rulers */}
          {(() => {
            const rPan = rulerFrozen && frozenPan ? frozenPan : pan
            const rZoom = rulerFrozen && frozenPan ? frozenPan.zoom : zoom
            return (
              <>
                <RulerCorner frozen={rulerFrozen} onToggleFreeze={() => {
                  if (rulerFrozen) {
                    setRulerFrozen(false)
                    setFrozenPan(null)
                  } else {
                    setRulerFrozen(true)
                    setFrozenPan({ x: pan.x, y: pan.y, zoom })
                  }
                }} />
                <Ruler position="top" zoom={rZoom} pan={rPan} dpi={dpi} containerWidth={containerSize.w} containerHeight={containerSize.h} />
                <Ruler position="bottom" zoom={rZoom} pan={rPan} dpi={dpi} containerWidth={containerSize.w} containerHeight={containerSize.h} />
                <Ruler position="left" zoom={rZoom} pan={rPan} dpi={dpi} containerWidth={containerSize.w} containerHeight={containerSize.h} />
              </>
            )
          })()}
        </div>

        <div className="sidebar">
          <div className="pdf-settings">
            <h3>PDF Settings</h3>
            <div className="pdf-setting-row">
              <label>DPI</label>
              <input
                type="range"
                min={50}
                max={300}
                step={5}
                value={dpi}
                onChange={(e) => setDpi(+e.target.value)}
              />
              <input
                type="number"
                className="dpi-input"
                min={50}
                max={300}
                value={dpi}
                onChange={(e) => {
                  const v = +e.target.value
                  if (v >= 50 && v <= 300) setDpi(v)
                }}
              />
            </div>
            <div className="pdf-setting-row">
              <label>Margin</label>
              <span className="pdf-setting-value">0.25&quot;</span>
            </div>
            <div className="pdf-setting-row">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={showPageSplits}
                  onChange={(e) => setShowPageSplits(e.target.checked)}
                />
                Show page splits
              </label>
            </div>
            <div className="pdf-setting-row">
              <button
                className="generate-btn"
                onClick={handleGeneratePdfs}
                disabled={sections.length === 0 || generating}
              >
                {generating ? 'Generating...' : 'Generate PDFs'}
              </button>
            </div>
          </div>
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
                {(() => {
                  const split = calcPageSplit(s.w, s.h, dpi, DEFAULT_MARGIN)
                  return (
                    <div className="section-pages">
                      {split.boardW.toFixed(1)}&quot; &times; {split.boardH.toFixed(1)}&quot;
                      &nbsp;|&nbsp; {split.cols}&times;{split.rows} = {split.cols * split.rows} page{split.cols * split.rows !== 1 ? 's' : ''}
                      {split.orientation === 'landscape' ? ' (L)' : ''}
                    </div>
                  )
                })()}
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
            <p className="hint">Press D to draw sections, V to edit them.<br/>Space+drag to pan. Scroll to pan both axes.<br/>{navigator.platform.includes('Mac') ? '\u2318' : 'Ctrl'}+scroll to zoom.</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
