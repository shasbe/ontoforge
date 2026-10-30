"""Ontology Graph Spec target tests.

The OGS adapters are second Target Format Adapters: the same nine profiles
compile to additional download formats without touching the workspace golden
output. Both published spec versions are shipped as targets; the published
1.0.0 and 1.1.0 schemas are structurally identical (they differ only in $id),
so the models differ only in the pinned schema URL and version. These tests
pin that contract:

  - every profile emits and passes all seven validation gates, per version
  - the document is valid against the *official* ONT-31 JSON Schema vendored
    in each target dir (skipped when jsonschema is not installed)
  - required root fields, slug ids, per-node display, KEY constraints
  - the richer Neo4jType enum negotiates DATETIME to ZONED DATETIME instead
    of degrading to STRING (the "better model as the spec grows" promise)
  - the two versions' documents differ only in schema and version
"""
import json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "core"))
from ontoforge.profile import Profile
from ontoforge.adapter import Adapter
from ontoforge.emit import emit
from ontoforge.validate import validate, errors
from ontoforge import rules

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TARGETS = ["neo4j-ontology-graph-spec-1.1.0", "neo4j-ontology-graph-spec-1.0.0"]
STANDARDS = ["fibo", "fhir", "idmp", "iof", "auto", "gs1", "epcis", "wikidata", "cdm"]

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL  {msg}")


profiles = {std: Profile.load(os.path.join(ROOT, "catalog", "profiles", f"{std}.yaml"))
            for std in STANDARDS}
models: dict[str, dict[str, dict]] = {}      # version -> standard -> model

try:
    from jsonschema import Draft202012Validator
    validators = {t: Draft202012Validator(
        json.load(open(os.path.join(ROOT, "targets", t, "schema.json"))))
        for t in TARGETS}
except ImportError:
    validators = {}
    print("jsonschema not installed -- official-schema check SKIPPED\n")

for tname in TARGETS:
    tdir = os.path.join(ROOT, "targets", tname)
    adapter = Adapter.load(tdir)
    sample = json.load(open(os.path.join(tdir, "sample.json")))
    models[tname] = {}
    print(f"target {tname}")
    for std in STANDARDS:
        prof = profiles[std]
        try:
            model, _ = emit(prof, adapter)
        except Exception as e:
            failures.append(f"{tname}/{std}: emit raised {e}")
            print(f"  {std:10} FAIL  emit raised {e}")
            continue
        models[tname][std] = model
        errs = errors(validate(model, adapter, sample))
        check(not errs, f"{tname}/{std}: {len(errs)} validation gate error(s): "
                        + "; ".join(str(e) for e in errs[:3]))
        if tname in validators:
            serrs = sorted(validators[tname].iter_errors(model), key=lambda e: list(e.path))
            check(not serrs, f"{tname}/{std}: official schema: "
                             + "; ".join(f"{list(e.path)}: {e.message[:80]}" for e in serrs[:3]))
        print(f"  {std:10} gates ok" + (", official schema ok" if tname in validators else ""))
    print()

# ---- the two published versions differ only in schema and version fields
for std in STANDARDS:
    a, b = models["neo4j-ontology-graph-spec-1.1.0"][std], \
           models["neo4j-ontology-graph-spec-1.0.0"][std]
    da, db = dict(a), dict(b)
    for k in ("schema", "version"):
        check(k in da and k in db, f"{std}: missing root field {k}")
        da.pop(k, None); db.pop(k, None)
    check(da == db, f"{std}: 1.0.0 and 1.1.0 documents differ beyond schema/version")

adapter = Adapter.load(os.path.join(ROOT, "targets", "neo4j-ontology-graph-spec-1.1.0"))

# ---- root fields and version provenance
M11 = models["neo4j-ontology-graph-spec-1.1.0"]
M10 = models["neo4j-ontology-graph-spec-1.0.0"]
m = M11["fhir"]
check(m["schema"] == "https://neo4j.com/docs/ontology-graph-spec/1.1.0/schema.json",
      "root schema URL not pinned to 1.1.0")
check(M10["fhir"]["schema"] == "https://neo4j.com/docs/ontology-graph-spec/1.0.0/schema.json",
      "1.0.0 target did not pin its own schema URL")
check(m["id"] == "fhir" and m["name"] == profiles["fhir"].title,
      "id/name not derived from profile")
check(m["version"] == "5.0.0", f"fhir version {m['version']!r} != source.version 5.0.0")
check(M11["cdm"]["version"] == "1.1.0",
      "version should fall back to the adapter version when profile has none")

# ---- ids: kebab-case nodes, slug+counter relationships
m = M11["fhir"]
for nid, n in m["nodes"].items():
    check(nid == nid.lower() and " " not in nid, f"node id {nid!r} not kebab-case")
    check(n["labels"]["identifier"] and n["extensions"]["display"]["x"] is not None,
          f"{nid}: label or per-node display missing")
for rid, r in m["relationships"].items():
    check(rid.rsplit("-", 1)[-1].isdigit(), f"relationship id {rid!r} not '<slug>-<i>'")
    check(r["from"]["node"] in m["nodes"] and r["to"]["node"] in m["nodes"],
          f"{rid}: endpoint not a node id")

# ---- node keys become KEY constraints (cdm declares keys)
m = M11["cdm"]
trade = next(n for n in m["nodes"].values() if n["labels"]["identifier"] == "Trade")
cons = trade.get("constraints", {})
check(any(c["type"] == "KEY" and "tradeDate" in c["properties"] for c in cons.values()),
      "cdm Trade: profile keys did not become a KEY constraint")
m = M11["fhir"]
check(all("constraints" not in n for n in m["nodes"].values()),
      "fhir has no profile keys, nodes should carry no constraints")

# ---- richer type enum: DATETIME survives instead of degrading to STRING
enum = adapter.type_enum()
check(rules.negotiate("DATETIME", enum, [], "x") == "ZONED DATETIME",
      "DATETIME should negotiate to 'ZONED DATETIME' on this target")
m = M11["epcis"]
types = {p["type"] for n in m["nodes"].values() for p in n["properties"].values()}
check("ZONED DATETIME" in types,
      "epcis timestamps should be ZONED DATETIME here, not STRING")

# ---- workspace golden output is untouched by the opt-in features
print()
if failures:
    print(f"{len(failures)} failure(s)")
    sys.exit(1)
print("ontology graph spec target: all checks passed")
