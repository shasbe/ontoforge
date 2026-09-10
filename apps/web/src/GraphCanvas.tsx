import { useMemo, useCallback, useEffect, useRef } from "react";
import {
  ReactFlow, Background, Controls, MiniMap, Handle, Position,
  useNodesState, useEdgesState, useReactFlow, MarkerType,
  type Node, type Edge, type NodeProps, type EdgeProps,
} from "@xyflow/react";
import { typeColor } from "./data";
import { forceLayout } from "./layout";
import type { Model } from "./types";

const MAX_PROPS_SHOWN = 7;

type NodeData = {
  label: string;
  props: { name: string; type: string }[];
  degree: number;
  hasSelfLoop: boolean;
  dim: boolean;
};

function ModelNode({ data, selected }: NodeProps<Node<NodeData>>) {
  const d = data;
  const shown = d.props.slice(0, MAX_PROPS_SHOWN);
  const rest = d.props.length - shown.length;
  // Hub intensity: node border brightens with degree, so the structural
  // backbone is visible without reading a single label.
  const intensity = Math.min(1, d.degree / 14);
  return (
    <div
      className={`rf-node${selected ? " sel" : ""}${d.dim ? " dim" : ""}`}
      style={{
        borderColor: selected
          ? undefined
          : `color-mix(in srgb, var(--accent) ${Math.round(intensity * 70)}%, var(--line))`,
      }}
    >
      <Handle type="target" position={Position.Top} />
      <div className="hd">
        <span>
          {d.hasSelfLoop && <span title="self-relationship (journey spine / hierarchy)">⟲ </span>}
          {d.label}
        </span>
        <span className="deg" title="relationship degree">{d.degree}</span>
      </div>
      <div className="pp">
        {shown.map((p) => (
          <div key={p.name}>
            <i className="dot" style={{ background: typeColor(p.type) }} />
            <span className="nm" title={`${p.name}: ${p.type}`}>{p.name}</span>
          </div>
        ))}
      </div>
      {rest > 0 && <div className="more">+{rest} more</div>}
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

/** React Flow does not draw same-source/target edges usefully, so self
 *  relationships get an explicit loop. These are the journey spines
 *  (NEXT, SUCCEEDS) and hierarchies (PART_OF, BROADER_THAN) -- worth seeing. */
function SelfLoopEdge({ sourceX, sourceY, data, style }: EdgeProps) {
  const r = 26;
  const path = `M ${sourceX - 7} ${sourceY} C ${sourceX - r * 2} ${sourceY - r * 1.7},
                ${sourceX + r * 2} ${sourceY - r * 1.7}, ${sourceX + 7} ${sourceY}`;
  return (
    <>
      <path d={path} fill="none" stroke={(style?.stroke as string) ?? "#4f8ef7"}
            strokeWidth={1.4} markerEnd="url(#rf-arrow-self)" />
      <text x={sourceX} y={sourceY - r * 1.5} textAnchor="middle"
            className="react-flow__edge-text">{String(data?.label ?? "")}</text>
    </>
  );
}

const nodeTypes = { model: ModelNode };
const edgeTypes = { selfLoop: SelfLoopEdge };

export default function GraphCanvas({
  model, query, selected, onSelect, onPositions, layoutNonce, resetNonce,
}: {
  model: Model;
  query: string;
  selected: string | null;
  onSelect: (label: string | null) => void;
  onPositions: (pos: Record<string, { x: number; y: number }>) => void;
  layoutNonce: number;
  resetNonce: number;
}) {
  const { initialNodes, initialEdges } = useMemo(() => {
    const degree: Record<string, number> = {};
    const selfLoop = new Set<string>();
    for (const r of Object.values(model.relationships)) {
      degree[r.from.node] = (degree[r.from.node] ?? 0) + 1;
      degree[r.to.node] = (degree[r.to.node] ?? 0) + 1;
      if (r.from.node === r.to.node) selfLoop.add(r.from.node);
    }
    const nodes: Node<NodeData>[] = Object.entries(model.nodes).map(([id, n]) => ({
      id,
      type: "model",
      position: model.display.nodes[id] ?? { x: 0, y: 0 },
      data: {
        label: n.labels.identifier,
        props: Object.values(n.properties).map((p) => ({ name: p.name, type: p.type })),
        degree: degree[id] ?? 0,
        hasSelfLoop: selfLoop.has(id),
        dim: false,
      },
    }));
    const edges: Edge[] = Object.entries(model.relationships).map(([id, r]) => {
      const isSelf = r.from.node === r.to.node;
      return {
        id,
        source: r.from.node,
        target: r.to.node,
        label: isSelf ? undefined : r.type,
        data: isSelf ? { label: r.type } : undefined,
        type: isSelf ? "selfLoop" : "default",
        style: { stroke: isSelf ? "#22d3a6" : "#3c4a63", strokeWidth: isSelf ? 1.6 : 1 },
        markerEnd: isSelf ? undefined : { type: MarkerType.ArrowClosed, color: "#3c4a63" },
      };
    });
    return { initialNodes: nodes, initialEdges: edges };
  }, [model]);

  const { fitView } = useReactFlow();
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => { setNodes(initialNodes); }, [initialNodes, setNodes]);

  // Remount React Flow per model so its own mount-time fitView applies -- it
  // waits for node measurement internally, which an imperative post-swap
  // fitView does not.
  const fitKey = useMemo(() => Object.keys(model.nodes).join("|"), [model]);

  // search dimming + selection are derived, not stored twice
  useEffect(() => {
    const q = query.trim().toLowerCase();
    setNodes((ns) =>
      ns.map((n) => {
        const d = n.data as NodeData;
        const hit =
          !q ||
          d.label.toLowerCase().includes(q) ||
          d.props.some((p) => p.name.toLowerCase().includes(q));
        return d.dim === !hit && n.selected === (n.id === selected)
          ? n
          : { ...n, selected: n.id === selected, data: { ...d, dim: !hit } };
      })
    );
  }, [query, selected, setNodes]);

  // auto-layout / reset, triggered by nonce bumps from the toolbar
  const lastLayout = useRef(0);
  useEffect(() => {
    if (layoutNonce === lastLayout.current) return;   // model changed, not the button
    lastLayout.current = layoutNonce;
    if (layoutNonce === 0) return;
    const ids = Object.keys(model.nodes);
    const edges: [string, string][] = Object.values(model.relationships)
      .map((r) => [r.from.node, r.to.node] as [string, string]);
    const seed = Object.fromEntries(
      ids.map((id) => [id, model.display.nodes[id] ?? { x: 0, y: 0 }])
    );
    const pos = forceLayout(ids, edges, seed);
    setNodes((ns) => ns.map((n) => ({ ...n, position: pos[n.id] ?? n.position })));
    onPositions(pos);
    fitView({ duration: 400, padding: 0.12 });
  }, [layoutNonce, model, setNodes, onPositions, fitView]);

  const lastReset = useRef(0);
  useEffect(() => {
    if (resetNonce === lastReset.current) return;
    lastReset.current = resetNonce;
    if (resetNonce === 0) return;
    const pos = Object.fromEntries(
      Object.keys(model.nodes).map((id) => [id, model.display.nodes[id] ?? { x: 0, y: 0 }])
    );
    setNodes((ns) => ns.map((n) => ({ ...n, position: pos[n.id] ?? n.position })));
    onPositions(pos);
    fitView({ duration: 400, padding: 0.12 });
  }, [resetNonce, model, setNodes, onPositions, fitView]);

  const handleNodeDragStop = useCallback(() => {
    setNodes((ns) => {
      onPositions(
        Object.fromEntries(
          ns.map((n) => [n.id, { x: Math.round(n.position.x), y: Math.round(n.position.y) }])
        )
      );
      return ns;
    });
  }, [setNodes, onPositions]);

  return (
    <div className="canvas">
      <svg style={{ position: "absolute", width: 0, height: 0 }}>
        <defs>
          <marker id="rf-arrow-self" viewBox="0 0 10 10" refX="8" refY="5"
                  markerWidth="5" markerHeight="5" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#22d3a6" />
          </marker>
        </defs>
      </svg>
      <ReactFlow
        key={fitKey}
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeDragStop={handleNodeDragStop}
        onNodeClick={(_, n) => onSelect((n.data as NodeData).label)}
        onPaneClick={() => onSelect(null)}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{ padding: 0.14 }}
        minZoom={0.05}
        maxZoom={1.75}
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={22} size={1} color="#2a3448" />
        <Controls showInteractive={false} />
        <MiniMap pannable zoomable nodeColor="#2f3d55" maskColor="rgba(15,20,32,.7)"
                 style={{ background: "#161d2c", border: "1px solid #2a3448" }} />
      </ReactFlow>
      <div className="legend">
        {["STRING", "INTEGER", "FLOAT", "BOOLEAN", "DATE"].map((t) => (
          <span key={t}><i style={{ background: typeColor(t) }} />{t}</span>
        ))}
        <span><i style={{ background: "#22d3a6" }} />⟲ self-rel</span>
      </div>
    </div>
  );
}
