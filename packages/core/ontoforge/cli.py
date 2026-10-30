"""ontoforge CLI. The web app is the primary interface, but core stays
scriptable: CI uses this to precompute the catalog, and the field can automate it."""
from __future__ import annotations
import argparse, json, os, sys, glob
from .profile import Profile
from .adapter import Adapter
from .emit import emit, EmitError
from .validate import validate, errors
from .analyze import report, metrics
from .ir import IR

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
def _p(*a): return os.path.join(ROOT, *a)
DEFAULT_TARGET = _p("targets", "neo4j-workspace-4.0.0")


def cmd_list(args):
    rows = []
    for fp in sorted(glob.glob(_p("catalog", "profiles", "*.yaml"))):
        p = Profile.load(fp)
        rows.append((p.standard, p.industry, len(p.nodes), len(p.relationships), p.title))
    w = max(len(r[0]) for r in rows)
    print(f"{'standard'.ljust(w)}  {'industry':30} {'nodes':>6}{'rels':>6}  title")
    for s, ind, n, r, t in rows:
        print(f"{s.ljust(w)}  {ind:30} {n:>6}{r:>6}  {t}")
    print(f"\n{len(rows)} standards in catalog")


def cmd_build(args):
    adapter = Adapter.load(args.target)
    sample_p = os.path.join(args.target, "sample.json")
    sample = json.load(open(sample_p)) if os.path.exists(sample_p) else None
    names = args.standard or [os.path.basename(f)[:-5]
                              for f in sorted(glob.glob(_p("catalog", "profiles", "*.yaml")))]
    os.makedirs(args.out, exist_ok=True)
    failures = 0
    for std in names:
        prof = Profile.load(_p("catalog", "profiles", f"{std}.yaml"))
        try:
            model, log = emit(prof, adapter)
        except EmitError as e:
            print(f"  {std:10} EMIT FAILED: {e}"); failures += 1; continue
        found = validate(model, adapter, sample)
        errs = errors(found)
        fn = os.path.join(args.out, f"{std}-model.json")
        if errs:
            print(f"  {std:10} INVALID ({len(errs)} error(s)) -- not written")
            for e in errs[:6]:
                print(f"      {e}")
            failures += 1
            continue
        with open(fn, "w") as f:
            json.dump(model, f, indent=2)
        if args.log:
            with open(os.path.join(args.out, f"{std}-decisions.log"), "w") as f:
                f.write("\n".join(log) + "\n")
        warns = [x for x in found if x.severity == "warning"]
        nprops = sum(len(n[adapter.node["properties"]["collection"].lstrip("$.")])
                     for n in model[adapter.node["collection"].lstrip("$.")].values())
        print(f"  {std:10} ok  nodes={len(prof.nodes):3} props={nprops:4} "
              f"rels={len(prof.relationships):3}"
              + (f"  ({len(warns)} warning(s))" if warns else ""))
    print(f"\n{len(names)-failures}/{len(names)} models built into {args.out}")
    return 1 if failures else 0


def cmd_validate(args):
    adapter = Adapter.load(args.target)
    sample_p = os.path.join(args.target, "sample.json")
    sample = json.load(open(sample_p)) if os.path.exists(sample_p) else None
    bad = 0
    for fp in args.files:
        found = validate(json.load(open(fp)), adapter, sample)
        errs = errors(found)
        warns = [x for x in found if x.severity == "warning"]
        status = "VALID" if not errs else f"INVALID ({len(errs)} errors)"
        print(f"{os.path.basename(fp):42} {status}" + (f", {len(warns)} warnings" if warns else ""))
        for x in found if args.verbose else errs:
            print(f"    {x}")
        bad += bool(errs)
    return 1 if bad else 0


def cmd_draft_adapter(args):
    sample = json.load(open(args.sample))
    draft = Adapter.draft_from_sample(sample, version=args.version)
    notes = draft.pop("_draft_notes", [])
    try:
        import yaml
        out = yaml.safe_dump(draft, sort_keys=False, width=100)
    except ImportError:
        out = json.dumps(draft, indent=2)
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w") as f:
            f.write("# Auto-drafted from sample -- CONFIRM before use.\n")
            for n in notes:
                f.write(f"# note: {n}\n")
            f.write(out)
        print(f"wrote {args.out}")
    else:
        print(out)
    print("\nheuristic notes (a sample cannot convey semantics -- review these):")
    for n in notes:
        print("  -", n)


def cmd_export(args):
    """Emit the static catalog bundle the web app consumes.

    Models and validation results are computed HERE, in Python, so the browser
    never re-implements the rules and cannot drift from them.
    """
    import dataclasses
    adapter = Adapter.load(args.target)
    sample_p = os.path.join(args.target, "sample.json")
    sample = json.load(open(sample_p)) if os.path.exists(sample_p) else None
    # secondary targets: same profiles, additional download formats
    extras = []
    for tdir in args.also or []:
        ea = Adapter.load(tdir)
        es = os.path.join(tdir, "sample.json")
        extras.append((ea, json.load(open(es)) if os.path.exists(es) else None))
    out = args.out
    os.makedirs(out, exist_ok=True)
    index = []
    skip = set(args.exclude or [])
    for fp in sorted(glob.glob(_p("catalog", "profiles", "*.yaml"))):
        std = os.path.basename(fp)[:-5]
        if std in skip:
            print(f"  {std:10} excluded")
            continue
        prof = Profile.load(fp)
        model, log = emit(prof, adapter)
        found = validate(model, adapter, sample)
        errs = [x for x in found if x.severity == "error"]
        d = os.path.join(out, std)
        os.makedirs(d, exist_ok=True)
        json.dump(model, open(os.path.join(d, "model.json"), "w"), indent=2)
        formats = [{"name": adapter.target, "version": adapter.version,
                    "file": "model.json"}]
        for ea, es in extras:
            try:
                em, _ = emit(prof, ea)
                ef = validate(em, ea, es)
                if errors(ef):
                    print(f"  {std:10} {ea.target}: INVALID, format not exported")
                    continue
                fn = f"{ea.target}.json"
                json.dump(em, open(os.path.join(d, fn), "w"), indent=2)
                formats.append({"name": ea.target, "version": ea.version, "file": fn})
            except EmitError as e:
                print(f"  {std:10} {ea.target}: EMIT FAILED: {e}")
        json.dump({"findings": [dataclasses.asdict(x) for x in found],
                   "errors": len(errs),
                   "warnings": len(found) - len(errs),
                   "decisions": log},
                  open(os.path.join(d, "validation.json"), "w"), indent=2)
        # provenance + curation notes, for the inspector panel
        json.dump({"standard": prof.standard, "title": prof.title,
                   "industry": prof.industry, "source": prof.source,
                   "notes": prof.notes, "keys": prof.keys,
                   "nodes": {n.label: {"source_iri": n.source_iri, "note": n.note,
                                       "properties": [{"name": a, "type": b}
                                                      for a, b in n.properties]}
                             for n in prof.nodes}},
                  open(os.path.join(d, "profile.json"), "w"), indent=2)
        ir_stats = None
        irp = _p("catalog", "ir", f"{std}.ir.json")
        if os.path.exists(irp):
            try:
                _ir = IR.load(irp)
                m = metrics(_ir)
                ir_stats = {"triples": _ir.meta.triples,
                            "classes": m["counts"]["classes"],
                            "object_properties": m["counts"]["object_properties"],
                            "individuals": m["counts"]["individuals"],
                            "anonymous_share": m["anonymous_share"],
                            "anonymous_subclass_share": m.get("anonymous_subclass_share"),
                            "max_depth": m["max_depth"],
                            "grounding_coverage": m.get("grounding_coverage"),
                            "top_hubs": m["top_hubs"][:12]}
                ap = _p("catalog", "ir", f"{std}-analysis.md")
                if os.path.exists(ap):
                    open(os.path.join(d, "analysis.md"), "w").write(open(ap).read())
            except Exception as e:                       # analysis is optional
                ir_stats = None
        nprops = sum(len(n[adapter.node["properties"]["collection"].lstrip("$.")])
                     for n in model[adapter.node["collection"].lstrip("$.")].values())
        rels = model[adapter.relationship["collection"].lstrip("$.")]
        index.append({"standard": std, "title": prof.title, "industry": prof.industry,
                      "source": prof.source,
                      "nodes": len(prof.nodes), "properties": nprops,
                      "relationships": len(prof.relationships),
                      "relationship_types": len({r["type"] for r in rels.values()}),
                      "self_relationships": sorted({r["type"] for r in rels.values()
                                                    if r["from"]["node"] == r["to"]["node"]}),
                      "errors": len(errs), "warnings": len(found) - len(errs),
                      "formats": formats,
                      "ir": ir_stats,
                      "has_analysis": os.path.exists(os.path.join(d, "analysis.md"))})
        print(f"  {std:10} model + validation + provenance"
              + ("  + analysis" if ir_stats else ""))
    json.dump({"generated_by": "ontoforge",
               "target": {"name": adapter.target, "version": adapter.version,
                          "type_enum": sorted(adapter.type_enum()),
                          "capabilities": adapter.capabilities.__dict__},
               "standards": index},
              open(os.path.join(out, "index.json"), "w"), indent=2)
    print(f"\nexported {len(index)} standards to {out}")


def cmd_analyze(args):
    ir = IR.load(args.ir)
    txt = report(ir)
    if args.out:
        open(args.out, "w").write(txt); print(f"wrote {args.out}")
    else:
        print(txt)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ontoforge",
        description="Compile industry standards into Neo4j graph data models.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="list catalog standards").set_defaults(fn=cmd_list)

    b = sub.add_parser("build", help="emit model JSON from profiles")
    b.add_argument("standard", nargs="*", help="standard id(s); default all")
    b.add_argument("--target", default=DEFAULT_TARGET)
    b.add_argument("--out", default="dist")
    b.add_argument("--log", action="store_true", help="also write decisions.log")
    b.set_defaults(fn=cmd_build)

    v = sub.add_parser("validate", help="validate model JSON against a target")
    v.add_argument("files", nargs="+")
    v.add_argument("--target", default=DEFAULT_TARGET)
    v.add_argument("-v", "--verbose", action="store_true")
    v.set_defaults(fn=cmd_validate)

    d = sub.add_parser("draft-adapter", help="infer a target adapter from an uploaded sample")
    d.add_argument("sample"); d.add_argument("--version"); d.add_argument("--out")
    d.set_defaults(fn=cmd_draft_adapter)

    x = sub.add_parser("export", help="emit the static catalog bundle for the web app")
    x.add_argument("--target", default=DEFAULT_TARGET)
    x.add_argument("--also", action="append", default=[],
                   help="additional target dir to export per standard as a "
                        "second download format (repeatable)")
    x.add_argument("--out", default="apps/web/public/catalog")
    x.add_argument("--exclude", nargs="*", default=[],
                   help="standard id(s) to omit from the published bundle "
                        "(see NOTICE.md on per-standard licensing)")
    x.set_defaults(fn=cmd_export)

    a = sub.add_parser("analyze", help="metrics report from a prebuilt IR")
    a.add_argument("ir"); a.add_argument("--out")
    a.set_defaults(fn=cmd_analyze)

    args = ap.parse_args(argv)
    return args.fn(args) or 0


if __name__ == "__main__":
    sys.exit(main())
