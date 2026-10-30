# PLAN — Neo4j Ontology Graph Spec (OGS) as second target format

Goal: add OGS 1.1.0 (https://neo4j.com/docs/ontology-graph-spec/) as a Target
Format Adapter + web download, golden-neutral (workspace output byte-identical).

| step | priority | status | task |
|---|---|---|---|
| 10 | P1 | done | `targets/neo4j-ontology-graph-spec-1.1.0/`: adapter.yaml, schema.json (raw), sample.json |
| 20 | P1 | done | core opt-in extensions: adapter `root`/`root_from_profile`, `{slug}`/`{name}` id patterns, per-node display, node constraints from `profile.keys`, FALLBACK space-form temporals; validate support |
| 30 | P1 | done | CLI `export --also <target>`: emits `<std>/ontology.json`, index.json `formats` |
| 40 | P2 | done | web app: `Download Ontology` button (per-node display baked), types/data |
| 50 | P1 | done | tests: `tests/test_ogs.py` (gates + official JSON Schema via jsonschema when available); golden test unchanged and green |
| 60 | P2 | done | docs: README format section, NOTICE attribution for the vendored schema; regenerate catalog export |

Notes:
- Capabilities on for OGS: multi_label, relationship_properties, node_keys
  (rules are log-only today; node_keys additionally emits KEY constraints,
  which OGS models natively).
- Model `version` per-standard from `profile.source.version` (new adapter
  `version_from`), falling back to the adapter version; gate 7 checks
  non-empty when the version is profile-derived.
