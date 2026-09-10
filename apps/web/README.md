# ontoforge web

Static catalog browser + model canvas. No backend, no login.

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # -> dist/  (deployable to any static host)
```

## How it gets its data

`public/catalog/` is **generated**, not authored. Regenerate after changing any
profile, rule, or target adapter:

```bash
PYTHONPATH=packages/core python -m ontoforge.cli export
```

Models and validation findings are computed in Python by `ontoforge export`, so
the browser never re-implements the rules and cannot drift from them. The app
renders and re-positions; it does not decide.

## What it does

- **Catalog** — every standard with measured source stats and validation status
- **Canvas** (React Flow) — nodes carry their property list with per-type colour;
  border brightness tracks relationship degree, so hubs are visible without
  reading labels; self-relationships get an explicit loop (`⟲`) because those are
  the journey spines and hierarchies
- **Auto-layout** — client-side force relaxation, hubs weighted toward the centre
- **Inspector** — properties, in/out relationships, node key, curation notes
- **Validation** — the seven gates with findings, plus the accepted type enum
- **Decisions** — the rule-firing log, so any node traces to a source axiom
- **Analysis** — the measured source report
- **Download** — model JSON including your current canvas layout in `display`

## Notes

- `display.nodes` round-trips: drag or auto-layout, then download, and the
  layout is preserved.
- Curated layouts (FIBO) are declared per node in the profile and are not
  overwritten unless you explicitly auto-layout that model.
- The property-type palette falls back to a neutral colour for unknown tokens,
  so a future additive spec still renders sensibly.
