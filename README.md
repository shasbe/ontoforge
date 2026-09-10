# ontoforge

Compile industry data standards into Neo4j property-graph models.

Point it at a published standard — FIBO, HL7 FHIR, GS1, EPCIS, IDMP, IOF, AUTO,
Wikidata — and get a curated Neo4j data model as Workspace JSON, ready to import.

Status: **phase 1 (core) complete**. Web app is phase 2.

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
python -m ontoforge.cli build --out dist --log      # all 8 models
python -m ontoforge.cli build fhir --out dist
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
| `wikidata` | Cross-domain KG | 21 | 45 | spec (hand-modelled) |
| `epcis` | Supply Chain | 20 | 38 | Turtle |

## Source analysis (measured, not estimated)

Run `ontoforge analyze` for the full report. Headline numbers:

| standard | triples | classes | anon% | depth | grounding text |
|---|---|---|---|---|---|
| fibo | 132,414 | 3,021 | 42.0 | 12 | 85% |
| iof | 25,348 | 1,002 | 44.1 | 7 | 95% |
| gs1 | 18,749 | 56 | 0.5 | 3 | 100% |
| idmp | 15,684 | 457 | 11.9 | 7 | 98% |
| auto | 13,474 | 1,171 | 7.8 | 12 | 93% |
| fhir | 8,896 elements | 158 | 0.0 | 0 | 100% |
| epcis | 1,000 | 20 | 14.9 | 1 | 100% |

`anon%` is the share of constraints whose target is an anonymous class
expression. Those must never become graph nodes — it is the single biggest
reason a naive RDF import produces an unusable graph.

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
python tests/test_golden.py
```

The nine models built by hand before this pipeline existed are the
specification. All eight profiles reproduce their golden file **byte-identically**;
any rule change that alters them fails CI.

## Layout

```
packages/core/ontoforge/    ir, adapter, profile, rules, emit, validate, analyze, cli
packages/ingest/            rdf (RDF-XML/Turtle/NT/JSON-LD/OWL), fhir
catalog/profiles/*.yaml     curation -- the reviewed, hand-maintained part
catalog/ir/*.ir.json        prebuilt IR + analysis reports (CI-generated)
targets/<name>/             adapter.yaml + sample.json (+ schema.json)
tests/golden/               the nine hand-built models
```

## Roadmap

- **2** Web app: catalog → canvas (React Flow) → validate → download. Static.
- **3** Target-adapter upload in the UI; regenerate catalog against a new spec.
- **4** Bring-your-own-source + JSON Schema ingester (unlocks Smart Data Models, OCSF, OSDU).
- **5** Reference-data extraction + Cypher DDL in the UI; tabular and XSD ingesters.

## Licensing note

Tool code is ours to license. **Catalog content is derived from third-party
standards with differing terms** — FIBO is MIT, FHIR and IOF are permissive, but
GS1 and IDMP need review before redistributing derived artifacts. Profiles and
`sources.yaml` are unambiguously ours; prebuilt IR for gated standards should be
fetch-on-demand rather than committed.
