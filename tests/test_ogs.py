"""Ontology Graph Spec target tests.

The OGS adapter is a second Target Format Adapter: the same nine profiles
compile to a second download format without touching the workspace golden
output. These tests pin that contract:

  - every profile emits and passes all seven validation gates
  - the document is valid against the *official* ONT-31 JSON Schema
    (vendored at targets/neo4j-ontology-graph-spec-1.1.0/schema.json;
    skipped when jsonschema is not installed)
  - required root fields, slug ids, per-node display, KEY constraints
  - the richer Neo4jType enum negotiates DATETIME to ZONED DATETIME instead
    of degrading to STRING (the "better model as the spec grows" promise)
"""
import json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "core"))
from ontoforge.profile import Profile
from ontoforge.adapter import Adapter
from ontoforge.emit import emit
from ontoforge.validate import validate, errors
from ontoforge import rules

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TARGET = os.path.join(ROOT, "targets", "neo4j-ontology-graph-spec-1.1.0")
STANDARDS = ["fibo", "fhir", "idmp", "iof", "auto", "gs1", "epcis", "wikidata", "cdm"]

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL  {msg}")


adapter = Adapter.load(TARGET)
sample = json.load(open(os.path.join(TARGET, "sample.json")))

try:
    from jsonschema import Draft202012Validator
    schema_validator = Draft202012Validator(
        json.load(open(os.path.join(TARGET, "schema.json"))))
except ImportError:
    schema_validator = None
    print("jsonschema not installed -- official-schema check SKIPPED\n")

models = {}
for std in STANDARDS:
    prof = Profile.load(os.path.join(ROOT, "catalog", "profiles", f"{std}.yaml"))
    try:
        model, _ = emit(prof, adapter)
    except Exception as e:
        failures.append(f"{std}: emit raised {e}")
        print(f"  {std:10} FAIL  emit raised {e}")
        continue
    models[std] = (model, prof)
    errs = errors(validate(model, adapter, sample))
    check(not errs, f"{std}: {len(errs)} validation gate error(s): "
                    + "; ".join(str(e) for e in errs[:3]))
    if schema_validator is not None:
        serrs = sorted(schema_validator.iter_errors(model), key=lambda e: list(e.path))
        check(not serrs, f"{std}: official schema: "
                         + "; ".join(f"{list(e.path)}: {e.message[:80]}" for e in serrs[:3]))
    print(f"  {std:10} gates ok" + (", official schema ok" if schema_validator else ""))

# ---- root fields and version provenance
m, prof = models["fhir"]
check(m["schema"] == "https://neo4j.com/docs/ontology-graph-spec/1.1.0/schema.json",
      "root schema URL not pinned to 1.1.0")
check(m["id"] == "fhir" and m["name"] == prof.title, "id/name not derived from profile")
check(m["version"] == "5.0.0", f"fhir version {m['version']!r} != source.version 5.0.0")
check(models["cdm"][0]["version"] == "1.1.0",
      "version should fall back to the adapter version when profile has none")

# ---- ids: kebab-case nodes, slug+counter relationships
m, _ = models["fhir"]
for nid, n in m["nodes"].items():
    check(nid == nid.lower() and " " not in nid, f"node id {nid!r} not kebab-case")
    check(n["labels"]["identifier"] and n["extensions"]["display"]["x"] is not None,
          f"{nid}: label or per-node display missing")
for rid, r in m["relationships"].items():
    check(rid.rsplit("-", 1)[-1].isdigit(), f"relationship id {rid!r} not '<slug>-<i>'")
    check(r["from"]["node"] in m["nodes"] and r["to"]["node"] in m["nodes"],
          f"{rid}: endpoint not a node id")

# ---- node keys become KEY constraints (cdm declares keys)
m, _ = models["cdm"]
trade = next(n for n in m["nodes"].values() if n["labels"]["identifier"] == "Trade")
cons = trade.get("constraints", {})
check(any(c["type"] == "KEY" and "tradeDate" in c["properties"] for c in cons.values()),
      "cdm Trade: profile keys did not become a KEY constraint")
m, _ = models["fhir"]
check(all("constraints" not in n for n in m["nodes"].values()),
      "fhir has no profile keys, nodes should carry no constraints")

# ---- richer type enum: DATETIME survives instead of degrading to STRING
enum = adapter.type_enum()
check(rules.negotiate("DATETIME", enum, [], "x") == "ZONED DATETIME",
      "DATETIME should negotiate to 'ZONED DATETIME' on this target")
m, _ = models["epcis"]
types = {p["type"] for n in m["nodes"].values() for p in n["properties"].values()}
check("ZONED DATETIME" in types,
      "epcis timestamps should be ZONED DATETIME here, not STRING")

# ---- workspace golden output is untouched by the opt-in features
print()
if failures:
    print(f"{len(failures)} failure(s)")
    sys.exit(1)
print("ontology graph spec target: all checks passed")
