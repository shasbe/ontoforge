import { useEffect, useMemo, useState } from "react";
import { ReactFlowProvider } from "@xyflow/react";
import GraphCanvas from "./GraphCanvas";
import { Inspector, ValidationPanel, DecisionsPanel, NotesPanel, AnalysisPanel } from "./Panels";
import {
  loadCatalog, loadModel, loadValidation, loadProfile, loadAnalysis, loadOntology,
  downloadJson, downloadText,
} from "./data";
import type { Catalog, CatalogEntry, Model, ProfileMeta, Validation, OntologyDoc } from "./types";

type Tab = "inspector" | "validation" | "decisions" | "analysis" | "notes";

function useHashRoute(): string | null {
  const [std, setStd] = useState<string | null>(
    () => window.location.hash.replace(/^#\/?/, "") || null
  );
  useEffect(() => {
    const on = () => setStd(window.location.hash.replace(/^#\/?/, "") || null);
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  return std;
}

function ThemeToggle() {
  const [light, setLight] = useState(
    () => localStorage.getItem("of-theme") === "light"
  );
  useEffect(() => {
    document.documentElement.dataset.theme = light ? "light" : "dark";
    localStorage.setItem("of-theme", light ? "light" : "dark");
  }, [light]);
  return <button onClick={() => setLight((v) => !v)} title="Toggle theme">
    {light ? "◑" : "◐"}
  </button>;
}

function CatalogView({ catalog }: { catalog: Catalog }) {
  return (
    <div className="wrap">
      <p className="lede">
        Curated Neo4j property-graph models compiled from published industry
        standards. Each is derived from the real source — parsed, measured and
        validated — then hand-curated, because a mechanical conversion of a
        3,000-class ontology produces a model nobody can use. Pick one to
        explore it and download the JSON.
      </p>
      <div className="grid">
        {catalog.standards.map((s) => <StandardCard key={s.standard} s={s} />)}
      </div>
    </div>
  );
}

function StandardCard({ s }: { s: CatalogEntry }) {
  const fmt = s.source.git ? "git" : s.source.http ? "http" : "spec";
  return (
    <button className="card" onClick={() => { window.location.hash = `#/${s.standard}`; }}>
      <div className="ind">{s.industry}</div>
      <h3>{s.title}</h3>
      <div className="chips">
        <span className={`badge ${s.errors ? "err" : "ok"}`}>
          {s.errors ? `${s.errors} errors` : "valid"}
        </span>
        {s.ir && <span className="badge">{s.ir.classes.toLocaleString()} source classes</span>}
        <span className="badge">{fmt}</span>
      </div>
      <div className="stats">
        <div className="stat"><b>{s.nodes}</b><i>nodes</i></div>
        <div className="stat"><b>{s.properties}</b><i>properties</i></div>
        <div className="stat"><b>{s.relationships}</b><i>relationships</i></div>
        <div className="stat"><b>{s.relationship_types}</b><i>rel types</i></div>
      </div>
      {s.self_relationships.length > 0 && (
        <div className="desc">
          spines: <code>{s.self_relationships.join(", ")}</code>
        </div>
      )}
    </button>
  );
}

function ModelView({ catalog, std }: { catalog: Catalog; std: string }) {
  const entry = catalog.standards.find((s) => s.standard === std);
  const [model, setModel] = useState<Model | null>(null);
  const [ontology, setOntology] = useState<OntologyDoc | null>(null);
  const [validation, setValidation] = useState<Validation | null>(null);
  const [profile, setProfile] = useState<ProfileMeta | null>(null);
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("inspector");
  const [selected, setSelected] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [positions, setPositions] = useState<Record<string, { x: number; y: number }> | null>(null);
  const [layoutNonce, setLayoutNonce] = useState(0);
  const [resetNonce, setResetNonce] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setModel(null); setOntology(null); setPositions(null); setSelected(null); setError(null);
    setLayoutNonce(0); setResetNonce(0);   // a new standard starts from its curated layout
    Promise.all([loadModel(std), loadValidation(std), loadProfile(std), loadAnalysis(std),
                 loadOntology(std).catch(() => null)])
      .then(([m, v, p, a, o]) => {
        setModel(m); setValidation(v); setProfile(p); setAnalysis(a); setOntology(o);
      })
      .catch((e) => setError(String(e)));
  }, [std]);

  /** Downloaded JSON carries the user's current layout -- the display block
   *  round-trips, so dragging on the canvas is not throwaway. */
  const exportModel = useMemo(() => {
    if (!model) return null;
    if (!positions) return model;
    return { ...model, display: { ...model.display, nodes: positions } };
  }, [model, positions]);

  /** Same for the Ontology Graph Spec download: its display lives per node
   *  (extensions.display), and its node ids are slugs, so positions are
   *  matched by label via the workspace model. */
  const exportOntology = useMemo(() => {
    if (!ontology || !model) return null;
    if (!positions) return ontology;
    const posByLabel: Record<string, { x: number; y: number }> = {};
    for (const [nid, n] of Object.entries(model.nodes)) {
      posByLabel[n.labels.identifier] = positions[nid] ?? model.display.nodes[nid];
    }
    const nodes = Object.fromEntries(Object.entries(ontology.nodes).map(([id, n]) => {
      const label = n.labels?.identifier;
      const p = label ? posByLabel[label] : undefined;
      if (!p) return [id, n];
      return [id, { ...n, extensions: { ...n.extensions, display: { x: p.x, y: p.y } } }];
    }));
    return { ...ontology, nodes };
  }, [ontology, model, positions]);

  if (error) return <div className="err-box">Failed to load <code>{std}</code>: {error}</div>;
  if (!model || !validation || !profile || !entry)
    return <div className="loading">Loading {std}…</div>;

  return (
    <div className="model">
      <ReactFlowProvider>
        <GraphCanvas
          model={model} query={query} selected={selected}
          onSelect={setSelected} onPositions={setPositions}
          layoutNonce={layoutNonce} resetNonce={resetNonce}
        />
      </ReactFlowProvider>
      <aside className="side">
        <div className="tabs" role="tablist">
          {(["inspector", "validation", "decisions", "analysis", "notes"] as Tab[]).map((t) => (
            <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)}>
              {t === "validation" && validation.errors > 0 ? `validation (${validation.errors})` : t}
            </button>
          ))}
        </div>
        {tab === "inspector" && (
          <Inspector model={model} profile={profile} label={selected} ir={entry.ir} />
        )}
        {tab === "validation" && (
          <ValidationPanel v={validation} target={catalog.target} />
        )}
        {tab === "decisions" && <DecisionsPanel v={validation} />}
        {tab === "analysis" && <AnalysisPanel md={analysis} />}
        {tab === "notes" && <NotesPanel profile={profile} ir={entry.ir} />}
        <div className="toolbar">
          <button className="primary"
                  onClick={() => downloadJson(`${std}-model.json`, exportModel)}
                  title="Includes your current canvas layout in the display block">
            Download JSON
          </button>
          {ontology && (
            <button onClick={() => downloadJson(`${std}-ontology.json`, exportOntology)}
                    title="Neo4j Ontology Graph Spec 1.1.0 -- the same model as a
versioned, SDK-backed ontology document; includes your current layout
as per-node display positions">
              Download Ontology
            </button>
          )}
          <button onClick={() => setLayoutNonce((n) => n + 1)}
                  title="Force-directed relaxation; hubs pull toward the centre">
            Auto-layout
          </button>
          <button onClick={() => setResetNonce((n) => n + 1)}
                  title="Back to the layout as exported">Reset</button>
          {analysis && (
            <button onClick={() => downloadText(`${std}-analysis.md`, analysis, "text/markdown")}>
              Analysis
            </button>
          )}
          <input type="search" placeholder="filter nodes / properties"
                 value={query} onChange={(e) => setQuery(e.target.value)} />
        </div>
      </aside>
    </div>
  );
}

export default function App() {
  const std = useHashRoute();
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { loadCatalog().then(setCatalog).catch((e) => setError(String(e))); }, []);

  const entry = catalog?.standards.find((s) => s.standard === std);
  return (
    <div className="app">
      <header className="top">
        <div className="brand">
          <a href="#/" style={{ color: "inherit", textDecoration: "none" }}>
            onto<span>forge</span>
          </a>
        </div>
        {std && entry && <><span style={{ color: "var(--fg-faint)" }}>/</span>
          <span>{entry.title}</span></>}
        <div className="spacer" />
        {catalog && (
          <span className="badge" title="target format adapter">
            {catalog.target.name} v{catalog.target.version}
          </span>
        )}
        {std && <button onClick={() => { window.location.hash = "#/"; }}>← catalog</button>}
        <ThemeToggle />
      </header>
      {error && <div className="err-box">Failed to load catalog: {error}</div>}
      {!catalog && !error && <div className="loading">Loading catalog…</div>}
      {catalog && (std && entry
        ? <ModelView catalog={catalog} std={std} />
        : <CatalogView catalog={catalog} />)}
    </div>
  );
}
