# ontoforge

Compile industry data standards into Neo4j property-graph models.

Point it at a published standard — FIBO, HL7 FHIR, GS1, EPCIS, IDMP, IOF, AUTO,
Wikidata — and get a curated Neo4j data model as Workspace JSON, ready to import.

Status: **phases 1-2 complete** — core pipeline plus a static web app.

```bash
PYTHONPATH=packages/core python -m ontoforge.cli export   # regenerate catalog
cd apps/web && npm install && npm run dev                 # http://localhost:5173
```

## Why it isn't a one-shot converter

FIBO has 3,021 classes; a mechanical conversion produces a 3,021-label model
nobody can use. Across the eight seed models, ~80% of the work was mechanical
(fetch, parse, measure, extract code lists, emit, validate) and ~20% was
judgment (which 30 classes matter, what collapses into a property).

So: the mechanical part is automatic, and the judgment part lives in a
per-standard **profile** you keep in git and review.

## The output format is data, not code

The target JSON shape is a **Target Format Adapter**, not a hardcoded emitter.
Drop in a new spec + sample and every model regenerates — no code change.

```bash
ontoforge draft-adapter path/to/new-sample.json --version 4.2.0 \
    --out targets/neo4j-workspace-4.2.0/adapter.yaml
```

The adapter also declares **capabilities**, which feed back into the
transformation rules — so the same profile compiles to a *better* model as the
spec grows:

| Capability | off (v4.0.0) | on |
|---|---|---|
| `relationship_properties` | `Ownership` stays a node | `-[:OWNS {percentage}]->` |
| `multi_label` | `EPCISEvent.eventType` discriminator | `:EPCISEvent:ObjectEvent` |
| `node_keys` | keys only in Cypher DDL | keys emitted into the model |

The proof is the second target already in the repo: the **Neo4j Ontology
Graph Specification** ([OGS / ONT-31](https://neo4j.com/docs/ontology-graph-spec/))
adapters at `targets/neo4j-ontology-graph-spec-1.1.0` and `-1.0.0`. The same
nine profiles compile to a second download format — a versioned, SDK-backed
ontology document — and because OGS models keys, multi-labels and relationship
properties natively, its capabilities are all on: EPCIS timestamps come out
as `ZONED DATETIME` instead of degrading to `STRING`, and the CDM profile's
keys become real `KEY` constraints. Every emitted document is validated
against the official JSON Schema, vendored in each target dir. Adding a future
spec version is one more target dir; the web download menu picks it up from
`index.json` automatically.

Type negotiation works the same way. Profiles declare semantically honest types;
the adapter reconciles them with what the target accepts:

```
TYPE_MAP: Trade.tradeDateTime: DATETIME not accepted by target -> STRING
          (store ISO 8601; sorts correctly as text)
```

## Usage

```bash
pip install -e packages/core            # + rdflib for ingest
export PYTHONPATH=packages/core:packages/ingest

python -m ontoforge.cli list                        # catalog
python -m ontoforge.cli build --out dist --log      # all 9 models
python -m ontoforge.cli build fhir --out dist
python -m ontoforge.cli build fhir --out dist-ogs \
    --target targets/neo4j-ontology-graph-spec-1.1.0   # as an OGS ontology
python -m ontoforge.cli validate dist/*.json -v
python -m ontoforge.cli analyze catalog/ir/fhir.ir.json
```

## Catalog

| standard | industry | nodes | rels | source format |
|---|---|---|---|---|
| `fibo` | Financial Services | 33 | 86 | OWL / RDF-XML |
| `fhir` | Healthcare | 33 | 101 | FHIR StructureDefinition JSON |
| `iof` | Manufacturing | 31 | 58 | OWL / RDF-XML (BFO) |
| `auto` | Automotive | 30 | 53 | OWL / RDF-XML |
| `idmp` | Pharmaceuticals | 29 | 44 | OWL / RDF-XML |
| `gs1` | Retail / CPG | 28 | 47 | Turtle |
| `cdm` | Financial Services / Capital Markets | 39 | 77 | Rosetta DSL |
| `wikidata` | Cross-domain KG | 21 | 45 | spec (hand-modelled) |
| `epcis` | Supply Chain | 20 | 38 | Turtle |

## Source analysis (measured, not estimated)

Run `ontoforge analyze` for the full report. Headline numbers:

| standard | assertions | classes | anon subClassOf | anon targets | depth | grounding |
|---|---|---|---|---|---|---|
| fibo | 130,273 | 3,021 | 42.1% | 8.5% | 12 | 85.5% |
| iof | 25,348 | 1,002 | 38.6% | 44.1% | 7 | 95.1% |
| gs1 | 18,749 | 56 | 0.0% | 0.5% | 3 | 100.0% |
| idmp | 15,684 | 457 | 62.4% | 11.9% | 7 | 97.9% |
| auto | 13,474 | 1,171 | 40.9% | 7.8% | 12 | 92.7% |
| cdm | 7,193 | 1,059 | 0.0% | 0.0% | 4 | 90.1% |
| fhir | 8,896 | 158 | — | 0.0% | 0 | 100.0% |
| epcis | 1,000 | 20 | 0.0% | 14.9% | 1 | 100.0% |

For RDF sources *assertions* means triples; for Rosetta it means attributes + inheritance + choice membership + enum values, and for FHIR, StructureDefinition elements.

`anon subClassOf` is the share of `rdfs:subClassOf` axioms whose object is a
blank node — i.e. how much of the apparent hierarchy is really OWL restrictions.
This is the single biggest reason a naive RDF import produces an unusable graph.
`anon targets` is the narrower share of extracted constraints pointing at
anonymous unions/intersections. Both are reported because they answer different
questions. **IDMP is the extreme at 62.4%**, ahead of FIBO's 42.1%.

**CDM is the outlier in the other direction**: 0% anonymous constructs, depth 4,
single-parent inheritance, explicit cardinality, and a declared scalar-vs-complex
split. Rosetta DSL states what OWL makes you infer, which makes CDM the cheapest
high-quality model in the catalog. The trade-off is that CDM is machine-*executable* —
its 1,290 functions and 615 conditions are logic a property graph cannot hold.

Grounding coverage is scoped to *schema* entities (classes + properties);
including reference-data individuals would dilute it — FIBO reads 39% over all
16k entities but 85.5% over its 4,230 schema ones.

Two findings worth knowing: **IOF has the highest anonymous share (44%)**
because BFO encodes meaning in `owl:equivalentClass` intersections rather than
prose — it carries almost no `skos:definition` at all, and its grounding text is
144 `skos:example` annotations. **GS1 is the inverse**: only 56 classes but 557
properties, a property-heavy vocabulary rather than a class hierarchy.

## Transformation rules

Each exists because it was needed by hand on at least one seed model.

| rule | evidence |
|---|---|
| `HUB_RANK` | FHIR: Organization 219, Patient 174 — measured in-degree |
| `SUBCLASS_COLLAPSE` | FIBO's 219 `Preferred*Share` classes → boolean flags |
| `TAXONOMY_SIDECAR` | FIBO 12 levels deep, 625 classes with >1 parent |
| `DISCRIMINATOR` | EPCIS's 5 event subclasses → `eventType` |
| `INVERSE_COLLAPSE` | FIBO: 80 explicit `owl:inverseOf` + ~103 conventional |
| `VALUE_OBJECT_FLATTEN` | `MonetaryAmount` → `amount` + `currencyCode` |
| `ROLE_REIFICATION_KEEP` | `PartyInRole`, IOF `AgentRole`, Wikidata `Statement` |
| `IDENTIFIER_RESOLVE` | GS1/FIBO reverse `identifies` + `hasTag` pattern |
| `CODE_LIST_EXTRACT` | FIBO's 12,094 individuals → 12,615 CSV rows |
| `TYPE_MAP` | `DATETIME` rejected by v4.0.0 → ISO 8601 `STRING` |

## Validation gates

Seven gates, all adapter-driven so they survive spec changes. Every one caught a
real defect while building the seed models:

shape conformance · type allowlist · id contiguity/uniqueness ·
dangling & duplicate relationships · display completeness · connectivity ·
version agreement

## Tests

```bash
python tests/test_golden.py     # workspace target
python tests/test_ogs.py        # Ontology Graph Spec target (+ official JSON Schema)
```

The nine models built by hand before this pipeline existed are the
specification. All eight profiles reproduce their golden file **byte-identically**;
any rule change that alters them fails CI. `test_ogs.py` pins the second
target's contract: gates, official-schema validity, root fields, slug ids,
KEY constraints and the richer type negotiation.

## Layout

```
packages/core/ontoforge/    ir, adapter, profile, rules, emit, validate, analyze, cli
packages/ingest/            rdf (RDF-XML/Turtle/NT/JSON-LD/OWL), fhir
catalog/profiles/*.yaml     curation -- the reviewed, hand-maintained part
catalog/ir/*.ir.json        prebuilt IR + analysis reports (CI-generated)
targets/<name>/             adapter.yaml + sample.json (+ schema.json)
tests/golden/               the nine hand-built models
```

## Web app

`apps/web` — static catalog browser and model canvas (React + React Flow, no
backend, no login). Browse the catalog, explore a model on a pan/zoom canvas,
inspect nodes, read the validation gates and decision log, and download the JSON
with your current layout baked into `display`. Every model also downloads as an
**Ontology Graph Spec** document — the `Download Ontology ▾` menu offers each
published spec version (1.0.0, 1.1.0, and future ones as they land), and
picking one downloads it in a single action with the same layout baked into
per-node display positions. See `apps/web/README.md`.

The catalog it serves is precomputed: FIBO is a 137 MB clone and ~2 minutes of
parsing, and FHIR R5 a 44 MB bundle, so neither can happen on a page load. CI
runs `ontoforge export` and the site ships the result as static JSON.

## Roadmap

- **3** Target-adapter upload in the UI; regenerate catalog against a new spec.
- **4** Bring-your-own-source + JSON Schema ingester (unlocks Smart Data Models, OCSF, OSDU).
- **5** Reference-data extraction + Cypher DDL in the UI; tabular and XSD ingesters.

## Hosting

Static site, ~872 KB, no backend and no login — so it hosts for free.
**GitHub Pages** is the recommendation and the workflow is ready in
`.github/workflows/deploy.yml`; `vite.config.ts` uses a relative base, verified
to work from a `/<repo>/` subpath. See `docs/HOSTING.md` for the option
comparison, custom domains, and the Cloudflare Pages alternative.

## Licensing

The tool is Apache-2.0 (`LICENSE`). Catalog content is *derived from*
third-party standards, and terms differ — **FIBO, AUTO and IOF are verified
MIT**; GS1, EPCIS, IDMP and FHIR carry no licence declaration verifiable from
their distributions. `NOTICE.md` records the evidence per standard and how to
publish a narrower catalog with `export --exclude`. Read it before making the
repo public.
