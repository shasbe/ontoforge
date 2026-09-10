"""Golden-file regression test.

The nine models hand-built before this pipeline existed are the specification.
Any rule or emitter change that alters them fails here unless a golden file is
updated deliberately.
"""
import json, os, sys, glob
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "core"))
from ontoforge.profile import Profile
from ontoforge.adapter import Adapter
from ontoforge.emit import emit
from ontoforge.validate import validate, errors

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TARGET = os.path.join(ROOT, "targets", "neo4j-workspace-4.0.0")
GOLDEN = {  # profile id -> golden filename produced by hand
    "fibo": "fibo-financial-services-model.json",
    "fhir": "fhir-r5-clinical-model.json",
    "idmp": "idmp-medicinal-products-model.json",
    "iof":  "iof-manufacturing-model.json",
    "auto": "auto-automotive-model.json",
    "gs1":  "gs1-trade-item-model.json",
    "epcis": "epcis-traceability-model.json",
    "wikidata": "wikidata-wikibase-model.json",
}


def diff(a, b, path="$"):
    out = []
    if type(a) is not type(b):
        return [f"{path}: type {type(a).__name__} != {type(b).__name__}"]
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a: out.append(f"{path}.{k}: MISSING from produced")
            elif k not in b: out.append(f"{path}.{k}: EXTRA in produced")
            else: out += diff(a[k], b[k], f"{path}.{k}")
    elif a != b:
        out.append(f"{path}: {a!r} != {b!r}")
    return out


def main():
    adapter = Adapter.load(TARGET)
    sample = json.load(open(os.path.join(TARGET, "sample.json")))
    passed = failed = 0
    print(f"golden-file test against {adapter.target} v{adapter.version}\n")
    for std, fn in GOLDEN.items():
        gp = os.path.join(ROOT, "tests", "golden", fn)
        if not os.path.exists(gp):
            print(f"  {std:10} SKIP (no golden file)"); continue
        golden = json.load(open(gp))
        prof = Profile.load(os.path.join(ROOT, "catalog", "profiles", f"{std}.yaml"))
        model, _ = emit(prof, adapter)
        d = diff(model, golden)
        errs = errors(validate(model, adapter, sample))
        if d or errs:
            failed += 1
            print(f"  {std:10} FAIL  ({len(d)} structural diff(s), {len(errs)} validation error(s))")
            for x in (d[:5] + [str(e) for e in errs[:3]]):
                print(f"      {x}")
        else:
            passed += 1
            nb = json.dumps(model, indent=2) == json.dumps(golden, indent=2)
            print(f"  {std:10} PASS  identical to hand-built model"
                  f"{' (byte-identical serialisation)' if nb else ''}")
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
