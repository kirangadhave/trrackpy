import { createRender, useModelState } from "@anywidget/react"
import {
  Check,
  History,
  Lock,
  LockOpen,
  Pencil,
  Redo2,
  RotateCcw,
  Undo2,
  X,
} from "lucide-react"
import {
  type CSSProperties,
  type ReactNode,
  useEffect,
  useRef,
  useState,
} from "react"
import { type ComposeContext, showTargetAndStatus } from "./compose"

interface Node {
  id: string
  parent: string | null
  children: string[]
  created_at: string
  label: string
  state: Record<string, unknown>
}

type Nodes = Record<string, Node>

const ROW_H = 28
const LANE_W = 20
const PAD_X = 14
const DOT_R = 5
const CORNER = 6
const LABEL_W = 180
const VIEW_W = 260
const VIEW_H = 360
const MIN_VIEW_W = 160
const RESIZE_HANDLE_W = 6
const RESIZE_HANDLE_H = 36

const TRUNK_COLOR = "#2563eb"
// Branch columns cycle through these so sibling branches stay distinct.
const BRANCH_COLORS = [
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
  "#14b8a6",
  "#f97316",
]

const HOVER_BG = "rgba(37,99,235,0.08)"

const TOOLTIP_LOOK = {
  padding: "3px 7px",
  background: "#111827",
  color: "#fff",
  fontSize: 12,
  borderRadius: 4,
  whiteSpace: "nowrap",
  pointerEvents: "none",
  zIndex: 10,
  boxShadow: "0 1px 3px rgba(0,0,0,0.25)",
} as const

const BUTTON_BASE = {
  display: "inline-flex",
  alignItems: "center",
  padding: 4,
  border: "none",
} as const

interface IconButtonProps {
  label: string
  onClick: () => void
  children: ReactNode
}

function IconButton({ label, onClick, children }: IconButtonProps) {
  return (
    <button
      title={label}
      aria-label={label}
      onClick={onClick}
      style={{
        ...BUTTON_BASE,
        background: "transparent",
        cursor: "pointer",
        color: "#6b7280",
      }}
    >
      {children}
    </button>
  )
}

const colColor = (col: number) =>
  col === 0 ? TRUNK_COLOR : BRANCH_COLORS[(col - 1) % BRANCH_COLORS.length]

interface Placement {
  id: string
  col: number
  depth: number
}

interface Layout {
  places: Placement[]
  byId: Record<string, Placement>
  maxCol: number
  maxDepth: number
}

function computeDepths(nodes: Nodes, rootId: string): Record<string, number> {
  const depth: Record<string, number> = { [rootId]: 0 }
  const queue = [rootId]
  while (queue.length) {
    const id = queue.shift() as string
    for (const child of nodes[id]?.children ?? []) {
      depth[child] = depth[id] + 1
      queue.push(child)
    }
  }
  return depth
}

function trunkSet(
  nodes: Nodes,
  rootId: string,
  currentId: string,
): Set<string> {
  const trunk = new Set<string>()
  let id: string | null = currentId
  while (id != null) {
    trunk.add(id)
    if (id === rootId) break
    id = nodes[id]?.parent ?? null
  }
  return trunk
}

/**
 * Vertical position is the node's depth from the root, so a node's parent always
 * sits exactly one row above it and every edge spans a single row. Horizontal
 * position is a column: the root→current path ("trunk") holds column 0; each
 * fork off a chain opens a fresh column to the right. Columns are never reused,
 * so each branch keeps its own column.
 */
function computeLayout(
  nodes: Nodes,
  rootId: string,
  currentId: string,
): Layout {
  const depth = computeDepths(nodes, rootId)
  const trunk = trunkSet(nodes, rootId, currentId)
  const col: Record<string, number> = {}
  let nextCol = 0

  const assign = (id: string, column: number) => {
    col[id] = column
    const kids = nodes[id]?.children ?? []
    const continuation = trunk.has(id)
      ? kids.find((k) => trunk.has(k))
      : kids[0]
    for (const kid of kids) {
      assign(kid, kid === continuation ? column : ++nextCol)
    }
  }
  if (nodes[rootId]) assign(rootId, 0)

  const places = Object.keys(col).map((id) => ({
    id,
    col: col[id],
    depth: depth[id],
  }))
  const byId: Record<string, Placement> = {}
  for (const place of places) byId[place.id] = place

  return {
    places,
    byId,
    maxCol: Math.max(0, ...Object.values(col)),
    maxDepth: Math.max(0, ...Object.values(depth)),
  }
}

// Column 0 (the trunk) sits at the right edge of the gutter, next to the
// labels; higher-numbered branch columns fan out to the left.
const colX = (col: number, maxCol: number) => PAD_X + (maxCol - col) * LANE_W
const depthY = (depth: number) => depth * ROW_H + ROW_H / 2

function edgePath(parent: Placement, child: Placement, maxCol: number): string {
  const x1 = colX(parent.col, maxCol)
  const y1 = depthY(parent.depth)
  const x2 = colX(child.col, maxCol)
  const y2 = depthY(child.depth)
  if (x1 === x2) return `M${x1},${y1} L${x2},${y2}`
  const dir = x2 > x1 ? 1 : -1
  return `M${x1},${y1} L${x2 - dir * CORNER},${y1} Q${x2},${y1} ${x2},${
    y1 + CORNER
  } L${x2},${y2}`
}

interface GraphProps {
  nodes: Nodes
  rootId: string
  currentId: string
  onSelect: (id: string) => void
  onRelabel: (id: string, text: string) => void
  width: number
  /** Called with the new width during a resize. Leave out to lock the size. */
  onResize?: (width: number) => void
}

interface ResizeDrag {
  startX: number
  startWidth: number
}

function Graph({
  nodes,
  rootId,
  currentId,
  onSelect,
  onRelabel,
  width,
  onResize,
}: GraphProps) {
  const [hoverId, setHoverId] = useState<string | null>(null)
  const [editId, setEditId] = useState<string | null>(null)
  const [draft, setDraft] = useState("")
  const labelInput = useRef<HTMLInputElement>(null)
  // The browser leaves the focus on the button that started the edit. Without
  // this, the first key press goes to that button and not into the field.
  useEffect(() => {
    labelInput.current?.focus()
    labelInput.current?.select()
  }, [editId])
  const [drag, setDrag] = useState<ResizeDrag | null>(null)
  const [panelHover, setPanelHover] = useState(false)

  const hoverHandlers = (id: string) => ({
    onMouseEnter: () => setHoverId(id),
    onMouseLeave: () => setHoverId(null),
  })
  const startEdit = (id: string) => {
    setDraft(nodes[id].label)
    setEditId(id)
  }
  const commitEdit = () => {
    if (editId) onRelabel(editId, draft)
    setEditId(null)
  }
  const { places, byId, maxCol, maxDepth } = computeLayout(
    nodes,
    rootId,
    currentId,
  )

  const gutterW = colX(0, maxCol) + PAD_X
  const contentW = gutterW + LABEL_W
  const contentH = (maxDepth + 1) * ROW_H
  const trunk = places.filter((place) => place.col === 0)

  return (
    <div
      onMouseEnter={() => setPanelHover(true)}
      onMouseLeave={() => setPanelHover(false)}
      style={{
        boxSizing: "border-box",
        position: "relative",
        width,
        height: VIEW_H,
        overflow: "hidden",
        border: "1px solid #e5e7eb",
        borderRadius: 6,
      }}
    >
      <div style={{ height: "100%", overflow: "auto" }}>
        <div
          style={{
            position: "relative",
            minWidth: contentW,
            height: contentH,
          }}
        >
          <svg
            width={gutterW}
            height={contentH}
            style={{ position: "absolute", top: 0, left: 0 }}
          >
            {places.map((place) => {
              const parentId = nodes[place.id].parent
              if (!parentId || !byId[parentId]) return null
              return (
                <path
                  key={`edge-${place.id}`}
                  d={edgePath(byId[parentId], place, maxCol)}
                  fill="none"
                  stroke={colColor(place.col)}
                  strokeWidth={1.5}
                />
              )
            })}
            {places.map((place) => {
              const isCurrent = place.id === currentId
              const isHover = place.id === hoverId
              const color = colColor(place.col)
              return (
                <circle
                  key={`dot-${place.id}`}
                  cx={colX(place.col, maxCol)}
                  cy={depthY(place.depth)}
                  r={isCurrent || isHover ? DOT_R + 1 : DOT_R}
                  fill={isCurrent ? color : "#fff"}
                  stroke={color}
                  strokeWidth={isCurrent ? 2 : 1.5}
                  cursor="pointer"
                  onClick={() => onSelect(place.id)}
                  {...hoverHandlers(place.id)}
                />
              )
            })}
          </svg>
          {trunk.map((place) => {
            const isCurrent = place.id === currentId
            const isHover = place.id === hoverId
            const isEditing = place.id === editId
            return (
              <div
                key={`label-${place.id}`}
                {...hoverHandlers(place.id)}
                style={{
                  position: "absolute",
                  top: place.depth * ROW_H,
                  left: gutterW,
                  right: 0,
                  height: ROW_H,
                  display: "flex",
                  alignItems: "center",
                  gap: 4,
                  paddingLeft: 6,
                  paddingRight: 4,
                  boxSizing: "border-box",
                  borderRadius: 4,
                  background: isHover && !isEditing ? HOVER_BG : "transparent",
                }}
              >
                {isEditing ? (
                  <>
                    <input
                      ref={labelInput}
                      value={draft}
                      onChange={(event) => setDraft(event.target.value)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter") commitEdit()
                        if (event.key === "Escape") setEditId(null)
                      }}
                      style={{
                        flex: 1,
                        minWidth: 0,
                        fontSize: 13,
                        padding: "2px 4px",
                        border: "1px solid #d1d5db",
                        borderRadius: 4,
                      }}
                    />
                    <IconButton label="Save" onClick={commitEdit}>
                      <Check size={14} />
                    </IconButton>
                    <IconButton label="Cancel" onClick={() => setEditId(null)}>
                      <X size={14} />
                    </IconButton>
                  </>
                ) : (
                  <>
                    <span
                      title={nodes[place.id].label}
                      onClick={() => onSelect(place.id)}
                      style={{
                        flex: 1,
                        minWidth: 0,
                        cursor: "pointer",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        fontWeight: isCurrent ? 600 : 400,
                        color: isCurrent ? "#111827" : "#374151",
                      }}
                    >
                      {nodes[place.id].label}
                    </span>
                    {isHover && (
                      <IconButton
                        label="Edit label"
                        onClick={() => startEdit(place.id)}
                      >
                        <Pencil size={13} />
                      </IconButton>
                    )}
                  </>
                )}
              </div>
            )
          })}
          {hoverId && byId[hoverId] && byId[hoverId].col !== 0 && (
            <div
              style={{
                position: "absolute",
                left: colX(byId[hoverId].col, maxCol) + DOT_R + 8,
                top: depthY(byId[hoverId].depth) - 11,
                maxWidth: LABEL_W,
                overflow: "hidden",
                textOverflow: "ellipsis",
                ...TOOLTIP_LOOK,
              }}
            >
              {nodes[hoverId].label}
            </div>
          )}
        </div>
      </div>
      {/* The graph is at the right edge of the output, so its left edge is the
          one that moves, and the handle is on that edge. */}
      {onResize && (
        <div
          role="separator"
          aria-orientation="vertical"
          aria-label="Resize history"
          title="Drag to resize"
          onPointerDown={(event) => {
            // Capture keeps the drag alive when the pointer leaves the handle.
            event.currentTarget.setPointerCapture(event.pointerId)
            setDrag({ startX: event.clientX, startWidth: width })
          }}
          onPointerMove={(event) => {
            if (!drag) return
            const moved = drag.startX - event.clientX
            onResize(Math.max(MIN_VIEW_W, drag.startWidth + moved))
          }}
          onPointerUp={() => setDrag(null)}
          onPointerCancel={() => setDrag(null)}
          style={{
            position: "absolute",
            left: 2,
            top: "50%",
            transform: "translateY(-50%)",
            width: RESIZE_HANDLE_W,
            height: RESIZE_HANDLE_H,
            borderRadius: RESIZE_HANDLE_W / 2,
            background: "#9ca3af",
            opacity: panelHover || drag ? 1 : 0,
            transition: "opacity 120ms",
            cursor: "ew-resize",
            touchAction: "none",
          }}
        />
      )}
    </div>
  )
}

interface RelabelRequest {
  id: string
  text: string
  nonce: number
}

const navButtonStyle = (disabled: boolean, hover: boolean): CSSProperties => ({
  ...BUTTON_BASE,
  borderRadius: 4,
  color: "#374151",
  background: hover && !disabled ? HOVER_BG : "transparent",
  cursor: disabled ? "default" : "pointer",
  opacity: disabled ? 0.3 : 1,
})

type TipAlign = "center" | "end"

// The tooltip is fixed to the viewport, not placed inside the button. A
// tooltip inside the button adds to the scroll height of the notebook's output
// area, which then shows a scroll bar when the controls are one short row.
const navTooltipStyle = (align: TipAlign, anchor: DOMRect): CSSProperties => ({
  position: "fixed",
  top: anchor.bottom + 4,
  ...(align === "center"
    ? { left: anchor.left + anchor.width / 2, transform: "translateX(-50%)" }
    : { right: document.documentElement.clientWidth - anchor.right }),
  ...TOOLTIP_LOOK,
})

interface BarAction {
  tip: string
  icon: ReactNode
  disabled?: boolean
  onClick: () => void
}

type NavButtonProps = Omit<BarAction, "icon"> & {
  tipAlign: TipAlign
  children: ReactNode
}

function NavButton({
  tip,
  tipAlign,
  disabled = false,
  onClick,
  children,
}: NavButtonProps) {
  const [anchor, setAnchor] = useState<DOMRect | null>(null)
  return (
    <div
      style={{ display: "inline-flex" }}
      onMouseEnter={(event) =>
        setAnchor(event.currentTarget.getBoundingClientRect())
      }
      onMouseLeave={() => setAnchor(null)}
    >
      <button
        aria-label={tip}
        disabled={disabled}
        onClick={onClick}
        style={navButtonStyle(disabled, anchor !== null)}
      >
        {children}
      </button>
      {anchor && <div style={navTooltipStyle(tipAlign, anchor)}>{tip}</div>}
    </div>
  )
}

function Controls() {
  const [nodes] = useModelState<Nodes>("nodes")
  const [currentId, setCurrentId] = useModelState<string>("current_id")
  const [, setRelabel] = useModelState<RelabelRequest>("_relabel")
  const [showButtons] = useModelState<boolean>("buttons")
  const [showGraph, setShowGraph] = useModelState<boolean>("graph")
  // The width is kept here so the graph has the same size after a hide.
  const [graphWidth, setGraphWidth] = useState(VIEW_W)
  const [sizeLocked, setSizeLocked] = useState(false)
  const nonce = useRef(0)
  const rootId = Object.keys(nodes).find((id) => nodes[id].parent === null)
  const current = nodes[currentId]

  const onRelabel = (id: string, text: string) => {
    nonce.current += 1
    setRelabel({ id, text, nonce: nonce.current })
  }

  const atRoot = !current?.parent
  const atLeaf = !current?.children.length
  const redoChildId = current?.children[current.children.length - 1]
  const rootLabel = rootId ? nodes[rootId]?.label : undefined
  const resetDisabled = !rootId || currentId === rootId

  const undoTip =
    !atRoot && current?.parent
      ? `Undo to “${nodes[current.parent]?.label}”`
      : "Nothing to undo"
  const redoTip = redoChildId
    ? `Redo to “${nodes[redoChildId]?.label}”`
    : "Nothing to redo"
  const resetTip = resetDisabled
    ? "Already at initial state"
    : `Reset to “${rootLabel}”`

  const navigation: BarAction[] = [
    {
      tip: undoTip,
      icon: <Undo2 size={16} />,
      disabled: atRoot,
      onClick: () => current?.parent && setCurrentId(current.parent),
    },
    {
      tip: redoTip,
      icon: <Redo2 size={16} />,
      disabled: atLeaf,
      onClick: () => redoChildId && setCurrentId(redoChildId),
    },
  ]
  const lock: BarAction = {
    tip: sizeLocked ? "Unlock size" : "Lock size",
    icon: sizeLocked ? <Lock size={16} /> : <LockOpen size={16} />,
    onClick: () => setSizeLocked(!sizeLocked),
  }
  const view: BarAction[] = [
    {
      tip: resetTip,
      icon: <RotateCcw size={16} />,
      disabled: resetDisabled,
      onClick: () => rootId && setCurrentId(rootId),
    },
    ...(showGraph ? [lock] : []),
    {
      tip: showGraph ? "Hide history" : "Show history",
      icon: <History size={16} />,
      onClick: () => setShowGraph(!showGraph),
    },
  ]
  const buttons = (actions: BarAction[], tipAlign: TipAlign) =>
    actions.map(({ icon, ...action }) => (
      <NavButton key={action.tip} tipAlign={tipAlign} {...action}>
        {icon}
      </NavButton>
    ))

  return (
    <div
      style={{
        fontFamily: "system-ui",
        fontSize: 13,
        display: "flex",
        flexDirection: "column",
        gap: 6,
      }}
    >
      {showButtons && (
        <div style={{ display: "flex", gap: showGraph ? 6 : 2 }}>
          {/* With the graph shown, the bar has the width of the graph, and
              the spacer pushes the view buttons to its right end. A button at
              the right edge of the output needs an end-aligned tooltip,
              because a centered one would cross that edge. */}
          {buttons(navigation, showGraph ? "center" : "end")}
          <div style={{ flex: 1 }} />
          {buttons(view, "end")}
        </div>
      )}
      {showGraph && rootId && (
        <Graph
          nodes={nodes}
          rootId={rootId}
          currentId={currentId}
          onSelect={setCurrentId}
          onRelabel={onRelabel}
          width={graphWidth}
          onResize={sizeLocked ? undefined : setGraphWidth}
        />
      )}
    </div>
  )
}

const renderApp = createRender(Controls)

type RenderContext = Parameters<typeof renderApp>[0] & ComposeContext

export default {
  render(ctx: RenderContext) {
    const row = document.createElement("div")
    // A target that is too wide to sit next to the controls keeps its width,
    // and the controls wrap to the next line.
    row.style.cssText =
      "display:flex;flex-wrap:wrap;gap:16px;align-items:flex-start"
    // The target stays in the light DOM so it keeps the host's own styles.
    const slot = document.createElement("div")
    slot.style.cssText = "flex:1 1 auto;min-width:0"
    // A widget can replace the whole style of the element it renders into.
    // It gets its own element, so the slot keeps the styles of the row.
    const target = document.createElement("div")
    slot.append(target)
    const controlsHost = document.createElement("div")
    // The controls stay at the right edge after a wrap too, so the left edge
    // of the graph is always the one that a resize moves.
    controlsHost.style.cssText = "margin-left:auto"
    const status = document.createElement("div")
    row.append(slot, controlsHost)
    ctx.el.replaceChildren(row, status)
    const stopStatus = showTargetAndStatus(ctx, target, status)

    // The controls mount in their own shadow root so they are style-isolated
    // from the host in every environment. Jupyter renders widgets into light
    // DOM, where host CSS (resets, themes) would otherwise reach our elements.
    // CSS custom properties still inherit across the boundary, so host theming
    // continues to apply.
    const mount = document.createElement("div")
    controlsHost.attachShadow({ mode: "open" }).append(mount)
    const cleanupControls = renderApp({ ...ctx, el: mount })

    return async () => {
      stopStatus()
      const cleanup = await cleanupControls
      if (typeof cleanup === "function") await cleanup()
    }
  },
}
