import { typeColor } from "./data";
import type { Model, ProfileMeta, Validation, IrStats } from "./types";

export function Inspector({ model, profile, label, ir }: {
  model: Model; profile: ProfileMeta; label: string | null; ir: IrStats | null;
}) {
  if (!label) {
    return (
      <div className="panel">
        <h4>Inspector</h4>
        <p className="empty">Select a node on the canvas to see its properties,
          relationships and curation provenance.</p>
        {ir && (
          <>
            <h4>Source hubs (measured in-degree)</h4>
            <p className="note">Node selection was driven by these counts, not intuition.</p>
            <div className="plist">
              {ir.top_hubs.map(([n, d]) => (
                <div className="prow" key={n}>
                  <span className="mono">{n.split("/").pop()}</span>
                  <b>{d}</b>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    );
  }
  const entry = Object.entries(model.nodes).find(([, n]) => n.labels.identifier === label);
  if (!entry) return <div className="panel"><p className="empty">Not found.</p></div>;
  const [nid, node] = entry;
  const pnode = profile.nodes[label];
  const out = Object.values(model.relationships).filter((r) => r.from.node === nid);
  const inc = Object.values(model.relationships).filter((r) => r.to.node === nid);
  const nameOf = (id: string) => model.nodes[id]?.labels.identifier ?? id;
  const keys = profile.keys[label];
  return (
    <div className="panel">
      <h4>{label}</h4>
      <dl className="kv">
        <dt>properties</dt><dd>{Object.keys(node.properties).length}</dd>
        <dt>out / in</dt><dd>{out.length} / {inc.length}</dd>
        {keys && <><dt>node key</dt><dd className="mono">{keys.join(", ")}</dd></>}
        {pnode?.source_iri && <><dt>source</dt><dd className="mono">{pnode.source_iri}</dd></>}
      </dl>
      {pnode?.note && <p className="note">{pnode.note}</p>}

      <h4>Properties</h4>
      <div className="plist">
        {Object.values(node.properties).map((p) => (
          <div className="prow" key={p.name}>
            <span>{p.name}</span>
            <span className="tchip" style={{ background: typeColor(p.type) }}>{p.type}</span>
          </div>
        ))}
      </div>

      {out.length > 0 && (
        <>
          <h4>Outgoing</h4>
          <div className="plist">
            {out.map((r, i) => (
              <div className="prow" key={i}>
                <span className="mono">{r.type}</span>
                <span style={{ color: "var(--fg-dim)" }}>→ {nameOf(r.to.node)}</span>
              </div>
            ))}
          </div>
        </>
      )}
      {inc.length > 0 && (
        <>
          <h4>Incoming</h4>
          <div className="plist">
            {inc.map((r, i) => (
              <div className="prow" key={i}>
                <span style={{ color: "var(--fg-dim)" }}>{nameOf(r.from.node)} →</span>
                <span className="mono">{r.type}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export function ValidationPanel({ v, target }: {
  v: Validation; target: { name: string; version: string; type_enum: string[] };
}) {
  const GATES = ["shape-conformance", "type-allowlist", "id-contiguity",
    "dangling-relationship", "uniqueness", "display-completeness",
    "connectivity", "version"];
  const hit = new Set(v.findings.map((f) => f.gate));
  return (
    <div className="panel">
      <h4>Gates</h4>
      <p className="note">
        Computed in Python by <code>ontoforge export</code> against{" "}
        <b>{target.name} v{target.version}</b> — the browser does not
        re-implement the rules, so it cannot drift from them.
      </p>
      <div className="plist">
        {GATES.map((g) => {
          const fs = v.findings.filter((f) => f.gate === g);
          const err = fs.some((f) => f.severity === "error");
          return (
            <div className="prow" key={g}>
              <span className="mono">{g}</span>
              <span className={`badge ${err ? "err" : hit.has(g) ? "warn" : "ok"}`}>
                {err ? `${fs.length} error` : hit.has(g) ? `${fs.length} warning` : "pass"}
              </span>
            </div>
          );
        })}
      </div>
      <h4>Accepted property types</h4>
      <div className="chips">
        {target.type_enum.map((t) => (
          <span className="tchip" key={t} style={{ background: typeColor(t) }}>{t}</span>
        ))}
      </div>
      {v.findings.length > 0 && (
        <>
          <h4>Findings</h4>
          {v.findings.map((f, i) => (
            <div className={`finding ${f.severity}`} key={i}>
              <div className="g">{f.gate}{f.path ? ` · ${f.path}` : ""}</div>
              {f.message}
            </div>
          ))}
        </>
      )}
    </div>
  );
}

export function DecisionsPanel({ v }: { v: Validation }) {
  return (
    <div className="panel">
      <h4>Decision log</h4>
      <p className="note">Every rule firing, so any node or property traces back
        to a source axiom and a target capability.</p>
      <div className="log">{v.decisions.join("\n")}</div>
    </div>
  );
}

export function NotesPanel({ profile, ir }: { profile: ProfileMeta; ir: IrStats | null }) {
  return (
    <div className="panel">
      <h4>Source</h4>
      <dl className="kv">
        {Object.entries(profile.source).map(([k, val]) => (
          <div style={{ display: "contents" }} key={k}>
            <dt>{k}</dt><dd className="mono">{val}</dd>
          </div>
        ))}
      </dl>
      {ir && (
        <>
          <h4>Measured</h4>
          <dl className="kv">
            <dt>triples</dt><dd>{ir.triples.toLocaleString()}</dd>
            <dt>classes</dt><dd>{ir.classes.toLocaleString()}</dd>
            <dt>object props</dt><dd>{ir.object_properties.toLocaleString()}</dd>
            <dt>individuals</dt><dd>{ir.individuals.toLocaleString()}</dd>
            <dt>max depth</dt><dd>{ir.max_depth}</dd>
            {ir.anonymous_subclass_share != null && (
              <><dt>anon subClassOf</dt><dd>{ir.anonymous_subclass_share}%</dd></>
            )}
            <dt>anon constraint targets</dt><dd>{ir.anonymous_share}%</dd>
            {ir.grounding_coverage != null && (
              <><dt>grounding text</dt><dd>{ir.grounding_coverage}%</dd></>
            )}
          </dl>
        </>
      )}
      <h4>Curation notes</h4>
      {profile.notes.length === 0
        ? <p className="empty">None.</p>
        : profile.notes.map((n, i) => <p className="note" key={i}>{n}</p>)}
    </div>
  );
}

/** Deliberately minimal markdown rendering -- the analysis reports only use
 *  headings, bullets, bold and inline code. */
export function AnalysisPanel({ md }: { md: string | null }) {
  if (!md) return <div className="panel"><p className="empty">
    No source analysis for this standard. Run <code>ontoforge analyze</code>.</p></div>;
  const html = md
    .split("\n")
    .map((l) => {
      const esc = l.replace(/&/g, "&amp;").replace(/</g, "&lt;");
      const inline = esc
        .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
        .replace(/`(.+?)`/g, "<code>$1</code>");
      if (/^# /.test(l)) return `<h1>${inline.slice(2)}</h1>`;
      if (/^## /.test(l)) return `<h2>${inline.slice(3)}</h2>`;
      if (/^- /.test(l)) return `<li>${inline.slice(2)}</li>`;
      if (l.trim() === "") return "";
      return `<p>${inline}</p>`;
    })
    .join("")
    .replace(/(<li>.*?<\/li>)+/g, (m) => `<ul>${m}</ul>`);
  return <div className="panel md" dangerouslySetInnerHTML={{ __html: html }} />;
}
