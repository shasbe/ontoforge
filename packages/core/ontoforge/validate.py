"""Validation gates. Every gate here caught a real defect while hand-building
the seed models, so none of them is speculative.

All gates read the shape from the Adapter, so they keep working when the
target spec grows.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Any
import re, json
from .adapter import Adapter, _dig


@dataclass
class Finding:
    gate: str
    severity: str          # error | warning
    message: str
    path: Optional[str] = None

    def __str__(self) -> str:
        loc = f" [{self.path}]" if self.path else ""
        return f"{self.severity.upper():7} {self.gate:22} {self.message}{loc}"


def _collection(model: dict, path: str) -> dict:
    v = _dig(model, path)
    return v if isinstance(v, dict) else {}


def _shape(d: Any, path: str = "") -> set[str]:
    out: set[str] = set()
    if isinstance(d, dict):
        for k, v in d.items():
            kk = re.sub(r"^([A-Za-z]+[:_-])\d+$", r"\1<id>", k)
            out.add(f"{path}.{kk}")
            out |= _shape(v, f"{path}.{kk}")
    return out


def validate(model: dict, adapter: Adapter, sample: Optional[dict] = None) -> list[Finding]:
    f: list[Finding] = []
    A = adapter

    # ---- gate 1: shape conformance against the reference sample
    if sample is not None:
        ss, ms = _shape(sample), _shape(model)
        for extra in sorted(ms - ss):
            f.append(Finding("shape-conformance", "error",
                             f"key-path not present in target sample: {extra}"))
        for missing in sorted(ss - ms):
            f.append(Finding("shape-conformance", "warning",
                             f"key-path in sample but absent from model: {missing}"))

    # ---- gate 2: property type allowlist
    try:
        enum = A.type_enum()
    except ValueError as e:
        f.append(Finding("type-allowlist", "error", str(e))); enum = set()
    nodes = _collection(model, A.node["collection"])
    rels = _collection(model, A.relationship["collection"])

    # ---- gate 3: id contiguity + uniqueness
    for which, coll in (("node", nodes), ("relationship", rels)):
        want = [A.id_for(which, i) for i in range(len(coll))]
        if list(coll.keys()) != want:
            f.append(Finding("id-contiguity", "error",
                             f"{which} ids are not contiguous/ordered "
                             f"(expected {want[:3]}... got {list(coll.keys())[:3]}...)"))
    pids: list[str] = []

    labels: set[str] = set()
    for nid, n in nodes.items():
        label = _dig(n, A.node["label"])
        if not isinstance(label, str) or not re.fullmatch(A.label_pattern, label or ""):
            f.append(Finding("naming", "error", f"invalid label {label!r}", nid)); continue
        if label in labels:
            f.append(Finding("uniqueness", "error", f"duplicate label {label}", nid))
        labels.add(label)
        if A.node.get("name"):
            nm = _dig(n, A.node["name"])
            if nm != label:
                f.append(Finding("label-name-agreement", "warning",
                                 f"name {nm!r} differs from label {label!r}", nid))
        props = _collection(n, A.node["properties"]["collection"])
        if not props:
            f.append(Finding("empty-node", "error", f"{label} has no properties", nid))
        seen: set[str] = set()
        for pid, p in props.items():
            pids.append(pid)
            pn = _dig(p, A.node["properties"]["name"])
            pt = _dig(p, A.node["properties"]["type"])
            if pn in seen:
                f.append(Finding("uniqueness", "error",
                                 f"{label}: duplicate property {pn}", f"{nid}.{pid}"))
            seen.add(pn)
            if enum and pt not in enum:
                f.append(Finding("type-allowlist", "error",
                                 f"{label}.{pn}: type {pt!r} not accepted "
                                 f"(target accepts {sorted(enum)})", f"{nid}.{pid}"))
    if len(pids) != len(set(pids)):
        dupes = {p for p in pids if pids.count(p) > 1}
        f.append(Finding("uniqueness", "error", f"duplicate property ids: {sorted(dupes)[:5]}"))

    # ---- gate 4: relationships resolve, no duplicate edges
    seen_e: set[tuple] = set()
    for rid, r in rels.items():
        rt = _dig(r, A.relationship["type"])
        if not isinstance(rt, str) or not re.fullmatch(A.rel_type_pattern, rt or ""):
            f.append(Finding("naming", "error", f"invalid relationship type {rt!r}", rid))
        s, t = _dig(r, A.relationship["from"]), _dig(r, A.relationship["to"])
        for side, v in (("from", s), ("to", t)):
            if v not in nodes:
                f.append(Finding("dangling-relationship", "error",
                                 f"{rt}: {side} node {v!r} does not exist", rid))
        key = (rt, s, t)
        if key in seen_e:
            f.append(Finding("uniqueness", "error", f"duplicate edge {key}", rid))
        seen_e.add(key)

    # ---- gate 5: display block completeness
    if A.display.get("nodes"):
        d = _collection(model, A.display["nodes"])
        if set(d.keys()) != set(nodes.keys()):
            miss = sorted(set(nodes) - set(d)); extra = sorted(set(d) - set(nodes))
            f.append(Finding("display-completeness", "error",
                             f"display mismatch (missing {miss[:4]}, extra {extra[:4]})"))

    # ---- gate 6: connectivity
    touched: set[str] = set()
    for r in rels.values():
        touched.add(_dig(r, A.relationship["from"]))
        touched.add(_dig(r, A.relationship["to"]))
    orphans = sorted(_dig(nodes[n], A.node["label"]) for n in set(nodes) - touched)
    if orphans:
        f.append(Finding("connectivity", "warning",
                         f"labels with no relationships: {orphans}"))

    # ---- gate 7: version agreement
    v = _dig(model, A.version_path)
    if str(v) != str(A.version):
        f.append(Finding("version", "error",
                         f"model version {v!r} != adapter version {A.version!r}"))
    return f


def errors(findings: list[Finding]) -> list[Finding]:
    return [x for x in findings if x.severity == "error"]
