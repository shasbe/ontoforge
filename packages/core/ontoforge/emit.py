"""Profile + Adapter -> target JSON. Deterministic: same inputs, same bytes."""
from __future__ import annotations
from typing import Optional
from .adapter import Adapter, _set
from .profile import Profile
from .ir import IR
from . import rules as R


class EmitError(Exception):
    pass


def emit(profile: Profile, adapter: Adapter, ir: Optional[IR] = None) -> tuple[dict, list[str]]:
    """Returns (model, decision_log)."""
    log: list[str] = []
    enum = adapter.type_enum()
    caps = adapter.capabilities
    log.append(f"target {adapter.target} v{adapter.version}; capabilities: {caps.summary()}")
    log.append(f"accepted property types: {sorted(enum)}")

    nodes = R.apply_type_map(profile.nodes, enum, log)
    rels = list(profile.relationships)
    nodes, rels = R.apply_capabilities(nodes, rels, caps, log)

    out: dict = {}
    _set(out, adapter.version_path, adapter.version)

    node_coll, rel_coll = adapter.node["collection"], adapter.relationship["collection"]
    by_label: dict[str, str] = {}
    nc: dict = {}
    disp: dict = {}
    pc = 0
    cols = int(profile.layout.get("columns", 6))
    dx, dy = int(profile.layout.get("dx", 430)), int(profile.layout.get("dy", 210))

    for i, n in enumerate(nodes):
        nid = adapter.id_for("node", i)
        if n.label in by_label:
            raise EmitError(f"duplicate label {n.label}")
        by_label[n.label] = nid
        entry: dict = {}
        _set(entry, adapter.node["label"], n.label)
        if adapter.node.get("name"):
            _set(entry, adapter.node["name"], n.label)
        props: dict = {}
        seen: set[str] = set()
        if not n.properties:
            raise EmitError(f"{n.label} has no properties")
        for pname, ptype in n.properties:
            if pname in seen:
                raise EmitError(f"{n.label}: duplicate property {pname}")
            seen.add(pname)
            if ptype not in enum:
                raise EmitError(f"{n.label}.{pname}: type {ptype} not accepted by "
                                f"{adapter.target} v{adapter.version}")
            p: dict = {}
            _set(p, adapter.node["properties"]["type"], ptype)
            _set(p, adapter.node["properties"]["name"], pname)
            props[adapter.prop_id(pc)] = p
            pc += 1
        _set(entry, adapter.node["properties"]["collection"], props)
        nc[nid] = entry
        if n.x is not None and n.y is not None:
            disp[nid] = {"x": n.x, "y": n.y}          # curated / user-dragged position
        else:
            col, row = i % cols, i // cols
            disp[nid] = {"x": col * dx - (cols - 1) * dx // 2, "y": row * dy - 200}

    rc: dict = {}
    seen_e: set[tuple[str, str, str]] = set()
    for j, r in enumerate(rels):
        for side, lbl in (("start", r.start), ("end", r.end)):
            if lbl not in by_label:
                raise EmitError(f"relationship {r.type}: unknown {side} label {lbl}")
        key = (r.type, r.start, r.end)
        if key in seen_e:
            raise EmitError(f"duplicate edge {key}")
        seen_e.add(key)
        e: dict = {}
        _set(e, adapter.relationship["type"], r.type)
        if adapter.relationship.get("name"):
            _set(e, adapter.relationship["name"], r.type)
        _set(e, adapter.relationship["from"], by_label[r.start])
        _set(e, adapter.relationship["to"], by_label[r.end])
        rc[adapter.id_for("relationship", j)] = e

    _set(out, node_coll, nc)
    _set(out, rel_coll, rc)
    if adapter.display.get("nodes"):
        _set(out, adapter.display["nodes"], disp)

    selfr = sorted({r.type for r in rels if r.start == r.end})
    log.append(f"emitted {len(nodes)} nodes, {pc} properties, {len(rels)} relationships "
               f"({len({r.type for r in rels})} distinct types)")
    if selfr:
        log.append(f"self-relationships (journey spines / hierarchies): {selfr}")
    return out, log
