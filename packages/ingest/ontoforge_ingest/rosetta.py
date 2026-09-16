"""Rosetta DSL ingester (REGnosys) -- used by the FINOS Common Domain Model.

Rosetta is markedly easier to ingest than OWL: there are no anonymous class
expressions, inheritance is single-parent, cardinality is written explicitly,
unions are named `choice` types, and ~92% of attributes carry an inline
description. Most of what the OWL rules have to infer is simply declared here.

What this ingester deliberately does NOT capture: `func` definitions and
`condition` bodies. Those are executable logic -- CDM is machine-executable by
design -- and a property graph holds the data shape, not the calculations. Their
counts are recorded in the IR metadata so the omission is visible.
"""
from __future__ import annotations
import glob, os, re, collections
from ontoforge.ir import (IR, Entity, Hierarchy, Constraint, SourceMeta,
                          CLASS, INDIVIDUAL, DATATYPE)

BASE = "cdm://"

# Rosetta built-in scalar types -> canonical tokens the TYPE_MAP rule understands.
SCALARS = {
    "string": "string", "int": "integer", "number": "decimal", "boolean": "boolean",
    "date": "date", "dateTime": "dateTime", "zonedDateTime": "dateTime",
    "time": "time", "calculation": "string", "productType": "string",
    "eventType": "string",
}

NS     = re.compile(r'^namespace\s+([\w.]+)')
TYPE   = re.compile(r'^type\s+(\w+)\s*(?:extends\s+(\w+))?\s*:')
CHOICE = re.compile(r'^choice\s+(\w+)\s*:')
ENUM   = re.compile(r'^enum\s+(\w+)\s*(?:extends\s+(\w+))?\s*:')
FUNC   = re.compile(r'^func\s+([\w<>]+)\s*:')
OTHER_TOP = re.compile(r'^(reporting\s+rule|rule|body|corpus|segment|eligibility\s+rule|'
                       r'report|synonym\s+source|library|metaType|recordType)\b')
# `typeAlias X: FpMLCodingScheme(domain: "...")` is a coded string, not a
# structure -- treat it as a scalar so attributes referencing it resolve.
TYPEALIAS = re.compile(r'^typeAlias\s+(\w+)\s*:')
# Inline block comments appear between a name and its colon, e.g.
# `enum PeriodExtendedEnum /*extends PeriodEnum*/ :`
BLOCK_COMMENT = re.compile(r'/\*.*?\*/', re.S)
ATTR   = re.compile(r'^\s+(\w+)\s+(\w+)\s*\((\d+)\.\.(\*|\d+)\)')
COND   = re.compile(r'^\s+condition\s*(\w*)\s*:')
ENUMVAL = re.compile(r'^\s+(\w+)\s*(?:displayName\s+"[^"]*")?\s*(?:<"|\[|$)')
CHOICEOPT = re.compile(r'^\s+(\w+)\s*(?:<"|\[|$)')
DESC   = re.compile(r'<"(.*)">', re.S)


def _desc(line: str) -> str | None:
    """Extract an inline <"..."> description. Greedy to the final '">' so
    descriptions containing quotes or brackets survive intact."""
    m = DESC.search(line)
    if not m:
        return None
    return " ".join(m.group(1).split()) or None


def _iri(ns: str, name: str) -> str:
    return f"{BASE}{ns}/{name}" if ns else f"{BASE}{name}"


def ingest(paths: list[str], standard: str = "cdm", version: str = "",
           fetched_from: str = "") -> IR:
    files: list[str] = []
    for p in paths:
        hits = sorted(glob.glob(p, recursive=True)) if any(c in p for c in "*?[") else [p]
        files += [h for h in hits if os.path.isfile(h) and h.endswith(".rosetta")]
    files = sorted(set(files))
    if not files:
        raise FileNotFoundError(f"no .rosetta files matched {paths}")

    ir = IR(meta=SourceMeta(standard=standard, version=version,
                            fetched_from=fetched_from, source_format="rosetta-dsl",
                            files_parsed=len(files)))

    # name -> iri, resolved after the first pass so forward references work
    declared: dict[str, str] = {}
    pending_attrs: list[tuple[str, str, str, int, str, str | None]] = []
    pending_hier: list[tuple[str, str]] = []          # (child name, parent name)
    pending_choice: list[tuple[str, str]] = []        # (choice name, option name)
    conditions = collections.Counter()
    alias_scalars: set[str] = set()
    func_count = 0
    lines_total = 0

    for fp in files:
        ns = ""
        cur = cur_kind = None
        buf: list[str] = []
        raw = open(fp, encoding="utf-8").read().splitlines()
        # stitch descriptions that span lines (only a couple in CDM, but cheap)
        joined: list[str] = []
        acc = None
        for line in raw:
            if acc is not None:
                acc += " " + line.strip()
                if '">' in line:
                    joined.append(acc); acc = None
                continue
            if '<"' in line and '">' not in line:
                acc = line
                continue
            joined.append(line)
        if acc is not None:
            joined.append(acc)

        for line in joined:
            lines_total += 1
            if not line.strip() or line.lstrip().startswith("//"):
                continue
            line = BLOCK_COMMENT.sub(" ", line)
            m = NS.match(line)
            if m:
                ns = m.group(1); continue
            if line.startswith(("import ", "version ")):
                continue
            m = FUNC.match(line)
            if m:
                func_count += 1; cur, cur_kind = None, "func"; continue
            m = TYPEALIAS.match(line)
            if m:
                name = m.group(1)
                iri = f"{BASE}alias/{name}"
                declared[name] = iri
                alias_scalars.add(name)
                ir.entities[iri] = Entity(iri=iri, local_name=name, kind=DATATYPE,
                                          label=name, definition=_desc(line),
                                          module=ns, types=["typeAlias", "string"])
                cur, cur_kind = None, "typeAlias"; continue
            if OTHER_TOP.match(line):
                cur, cur_kind = None, "other"; continue
            m = TYPE.match(line)
            if m:
                name, parent = m.group(1), m.group(2)
                iri = _iri(ns, name); declared[name] = iri
                ir.entities[iri] = Entity(iri=iri, local_name=name, kind=CLASS,
                                          label=name, definition=_desc(line),
                                          module=ns, types=["type"])
                if parent:
                    pending_hier.append((name, parent))
                cur, cur_kind = name, "type"; continue
            m = CHOICE.match(line)
            if m:
                name = m.group(1)
                iri = _iri(ns, name); declared[name] = iri
                ir.entities[iri] = Entity(iri=iri, local_name=name, kind=CLASS,
                                          label=name, definition=_desc(line),
                                          module=ns, types=["choice"])
                cur, cur_kind = name, "choice"; continue
            m = ENUM.match(line)
            if m:
                name, parent = m.group(1), m.group(2)
                iri = _iri(ns, name); declared[name] = iri
                ir.entities[iri] = Entity(iri=iri, local_name=name, kind=CLASS,
                                          label=name, definition=_desc(line),
                                          module=ns, types=["enum"])
                if parent:
                    pending_hier.append((name, parent))
                cur, cur_kind = name, "enum"; continue

            if cur_kind == "type" and cur:
                if COND.match(line):
                    conditions[cur] += 1; continue
                m = ATTR.match(line)
                if m:
                    pending_attrs.append((cur, m.group(1), m.group(2),
                                          int(m.group(3)), m.group(4), _desc(line)))
                continue
            if cur_kind == "choice" and cur:
                m = CHOICEOPT.match(line)
                if m and m.group(1)[0].isupper():
                    pending_choice.append((cur, m.group(1)))
                continue
            if cur_kind == "enum" and cur:
                m = ENUMVAL.match(line)
                if m and not line.lstrip().startswith("condition"):
                    vname = m.group(1)
                    viri = f"{_iri(ns, cur)}#{vname}"
                    ir.entities[viri] = Entity(iri=viri, local_name=vname,
                                               kind=INDIVIDUAL, label=vname,
                                               definition=_desc(line), module=ns,
                                               types=[cur])
                continue

    # ---- scalar datatype entities, so targets resolve and HUB_RANK can skip them
    for s, canonical in SCALARS.items():
        iri = f"{BASE}scalar/{s}"
        ir.entities[iri] = Entity(iri=iri, local_name=s, kind=DATATYPE,
                                  label=s, module="scalar", types=[canonical])

    # ---- resolve inheritance
    for child, parent in pending_hier:
        c, p = declared.get(child), declared.get(parent)
        if c and p:
            ir.hierarchy.append(Hierarchy(child=c, parent=p, kind="subclass"))

    # ---- choice options become subtypes AND an explicit choice constraint.
    # A named union is exactly the DISCRIMINATOR / TAXONOMY_SIDECAR input that
    # the OWL path has to recover from anonymous owl:unionOf expressions.
    for choice, opt in pending_choice:
        ci, oi = declared.get(choice), declared.get(opt)
        if not ci:
            continue
        if oi:
            ir.hierarchy.append(Hierarchy(child=oi, parent=ci, kind="subclass"))
        ir.constraints.append(Constraint(subject=ci, predicate="choiceOf",
                                         target=oi, kind="choice",
                                         is_anonymous=oi is None))

    # ---- attributes -> constraints
    unresolved = collections.Counter()
    for owner, aname, atype, lo, hi, adesc in pending_attrs:
        si = declared.get(owner)
        if not si:
            continue
        is_scalar = atype in SCALARS or atype in alias_scalars
        ti = (f"{BASE}scalar/{atype}" if atype in SCALARS else declared.get(atype))
        if ti is None:
            unresolved[atype] += 1
        hi_n = None if hi == "*" else int(hi)
        kind = "exact" if (lo == hi_n) else ("min" if lo >= 1 else "max" if hi_n else "some")
        ir.constraints.append(Constraint(
            subject=si, predicate=aname, target=ti, kind=kind,
            min=lo or None, max=hi_n,
            is_anonymous=ti is None, via_datatype_property=is_scalar))

    # Not an RDF source, so there are no triples. Record the comparable figure --
    # structural assertions -- so size is reported rather than showing zero.
    ir.meta.triples = (len(pending_attrs) + len(ir.hierarchy) + len(pending_choice)
                       + sum(1 for e in ir.entities.values() if e.kind == INDIVIDUAL))
    ir.meta.notes.append(
        "size is reported as structural assertions (attributes + inheritance + choice "
        "membership + enum values); Rosetta is not an RDF serialisation so there are "
        "no triples to count")
    ir.meta.raw_counts = {
        "files": len(files),
        "namespaces": len({e.module for e in ir.entities.values() if e.module}),
        "types": sum(1 for e in ir.entities.values() if "type" in e.types),
        "choices": sum(1 for e in ir.entities.values() if "choice" in e.types),
        "enums": sum(1 for e in ir.entities.values() if "enum" in e.types),
        "enum_values": sum(1 for e in ir.entities.values() if e.kind == INDIVIDUAL),
        "attributes": len(pending_attrs),
        "conditions": sum(conditions.values()),
        "functions": func_count,
        "type_aliases": len(alias_scalars),
        # Rosetta has no anonymous class expressions; these are here so the
        # anonymity metrics report a real 0 rather than a missing value.
        "subclass_axioms": len(ir.hierarchy),
        "subclass_to_named": len(ir.hierarchy),
        "subclass_to_anonymous": 0,
    }
    seen_names: dict[str, list[str]] = {}
    for e in ir.entities.values():
        if e.kind != INDIVIDUAL:
            seen_names.setdefault(e.local_name, []).append(e.module or "")
    collisions = {n: ms for n, ms in seen_names.items() if len(ms) > 1}
    if collisions:
        ir.meta.notes.append(
            f"{len(collisions)} simple name(s) are declared in more than one namespace "
            f"({', '.join(sorted(collisions)[:4])}); type references are resolved by a "
            "flat name map, so these resolve last-wins rather than via `import` scope")
    if unresolved:
        ir.meta.notes.append(
            f"{sum(unresolved.values())} attribute(s) reference {len(unresolved)} "
            f"type(s) not declared in the parsed set (e.g. "
            f"{', '.join(t for t, _ in unresolved.most_common(4))})")
    ir.meta.notes.append(
        f"{func_count} func definitions and {sum(conditions.values())} conditions were "
        "NOT ingested: they are executable logic, not data shape")
    return ir
