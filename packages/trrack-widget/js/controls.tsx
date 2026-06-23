import { createRender, useModelState } from "@anywidget/react"
import { Check, Pencil, Redo2, Undo2, X } from "lucide-react"
import { useRef, useState } from "react"

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
const VIEW_W = 320
const VIEW_H = 360

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

const iconButtonStyle = {
  display: "inline-flex",
  alignItems: "center",
  padding: 4,
  background: "transparent",
  border: "none",
  cursor: "pointer",
  color: "#6b7280",
} as const

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
}

function Graph({ nodes, rootId, currentId, onSelect, onRelabel }: GraphProps) {
  const [hoverId, setHoverId] = useState<string | null>(null)
  const [editId, setEditId] = useState<string | null>(null)
  const [draft, setDraft] = useState("")

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
      style={{
        width: VIEW_W,
        height: VIEW_H,
        overflow: "auto",
        border: "1px solid #e5e7eb",
        borderRadius: 6,
      }}
    >
      <div style={{ position: "relative", width: contentW, height: contentH }}>
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
                onMouseEnter={() => setHoverId(place.id)}
                onMouseLeave={() => setHoverId(null)}
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
              onMouseEnter={() => setHoverId(place.id)}
              onMouseLeave={() => setHoverId(null)}
              style={{
                position: "absolute",
                top: place.depth * ROW_H,
                left: gutterW,
                width: LABEL_W,
                height: ROW_H,
                display: "flex",
                alignItems: "center",
                gap: 4,
                paddingLeft: 6,
                paddingRight: 4,
                boxSizing: "border-box",
                borderRadius: 4,
                background:
                  isHover && !isEditing
                    ? "rgba(37,99,235,0.08)"
                    : "transparent",
              }}
            >
              {isEditing ? (
                <>
                  <input
                    autoFocus
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
                  <button
                    title="Save"
                    aria-label="Save"
                    onClick={commitEdit}
                    style={iconButtonStyle}
                  >
                    <Check size={14} />
                  </button>
                  <button
                    title="Cancel"
                    aria-label="Cancel"
                    onClick={() => setEditId(null)}
                    style={iconButtonStyle}
                  >
                    <X size={14} />
                  </button>
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
                    <button
                      title="Edit label"
                      aria-label="Edit label"
                      onClick={() => startEdit(place.id)}
                      style={iconButtonStyle}
                    >
                      <Pencil size={13} />
                    </button>
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
              padding: "3px 7px",
              background: "#111827",
              color: "#fff",
              fontSize: 12,
              borderRadius: 4,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
              pointerEvents: "none",
              zIndex: 10,
              boxShadow: "0 1px 3px rgba(0,0,0,0.25)",
            }}
          >
            {nodes[hoverId].label}
          </div>
        )}
      </div>
    </div>
  )
}

interface RelabelRequest {
  id: string
  text: string
  nonce: number
}

function Controls() {
  const [nodes] = useModelState<Nodes>("nodes")
  const [currentId, setCurrentId] = useModelState<string>("current_id")
  const [, setRelabel] = useModelState<RelabelRequest>("_relabel")
  const nonce = useRef(0)
  const rootId = Object.keys(nodes).find((id) => nodes[id].parent === null)
  const current = nodes[currentId]

  const onRelabel = (id: string, text: string) => {
    nonce.current += 1
    setRelabel({ id, text, nonce: nonce.current })
  }

  const iconButton = {
    display: "inline-flex",
    alignItems: "center",
    padding: 4,
  } as const

  return (
    <div style={{ fontFamily: "system-ui", fontSize: 13 }}>
      <div style={{ display: "flex", gap: 6, marginBottom: 6 }}>
        <button
          title="Undo"
          aria-label="Undo"
          disabled={!current?.parent}
          onClick={() => current?.parent && setCurrentId(current.parent)}
          style={iconButton}
        >
          <Undo2 size={16} />
        </button>
        <button
          title="Redo"
          aria-label="Redo"
          disabled={!current?.children.length}
          onClick={() =>
            current?.children.length &&
            setCurrentId(current.children[current.children.length - 1])
          }
          style={iconButton}
        >
          <Redo2 size={16} />
        </button>
      </div>
      {rootId && (
        <Graph
          nodes={nodes}
          rootId={rootId}
          currentId={currentId}
          onSelect={setCurrentId}
          onRelabel={onRelabel}
        />
      )}
    </div>
  )
}

export default { render: createRender(Controls) }
