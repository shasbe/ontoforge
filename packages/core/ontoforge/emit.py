"""Profile + Adapter -> target JSON. Deterministic: same inputs, same bytes."""
from __future__ import annotations
from typing import Optional
from .adapter import Adapter, _set
from .profile import Profile
from .ir import IR
from . import rules as R


class EmitError(Exception):
    pass


def _from_profile(profile: Profile, attr: str):
    """Resolve a dotted profile attribute path, e.g. 'source.version'.
    The first hop is a Profile dataclass field, later hops dict keys."""
    parts = attr.split(".")
    cur = profile.source if parts[0] == "source" else getattr(profile, parts[0], None)
    for part in parts[1:]:
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


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
    version = adapter.version
    if adapter.version_from:
        v = _from_profile(profile, adapter.version_from)
        if v:
            version = str(v)
            log.append(f"model version {version} from profile {adapter.version_from}")
    _set(out, adapter.version_path, version)
    for field, lit in adapter.root.items():
        _set(out, f"$.{field}", lit)
    for field, attr in adapter.root_from_profile.items():
        v = _from_profile(profile, attr)
        if v is None:
            raise EmitError(f"root field {field}: profile has no {attr}")
        _set(out, f"$.{field}", v)

    node_coll, rel_coll = adapter.node["collection"], adapter.relationship["collection"]
    by_label: dict[str, str] = {}
    nc: dict = {}
    disp: dict = {}
    pc = 0
    cols = int(profile.layout.get("columns", 6))
    dx, dy = int(profile.layout.get("dx", 430)), int(profile.layout.get("dy", 210))
    per_node_display = adapter.display.get("per_node")
    cons_spec = adapter.node_constraints if caps.node_keys else None

    for i, n in enumerate(nodes):
        nid = adapter.id_for("node", i, n.label)
        if n.label in by_label:
            raise EmitError(f"duplicate label {n.label}")
        if nid in nc:
            raise EmitError(f"duplicate node id {nid} (label {n.label})")
        by_label[n.label] = nid
        entry: dict = {}
        _set(entry, adapter.node["label"], n.label)
        if adapter.node.get("name"):
            _set(entry, adapter.node["name"], n.label)
        props: dict = {}
        pid_of: dict[str, str] = {}
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
            pid = adapter.prop_id(pc, pname)
            props[pid] = p
            pid_of[pname] = pid
            pc += 1
        _set(entry, adapter.node["properties"]["collection"], props)
        if cons_spec and profile.keys.get(n.label):
            key_props = profile.keys[n.label]
            missing = [kp for kp in key_props if kp not in pid_of]
            if missing:
                raise EmitError(f"{n.label}: key references unknown property {missing}")
            cid = cons_spec["id_pattern"].replace("{i}", "0")
            _set(entry, cons_spec["collection"],
                 {cid: {"type": cons_spec.get("key_type", "KEY"),
                        "properties": [pid_of[kp] for kp in key_props]}})
        nc[nid] = entry
        if n.x is not None and n.y is not None:
            pos = {"x": n.x, "y": n.y}                # curated / user-dragged position
        else:
            col, row = i % cols, i // cols
            pos = {"x": col * dx - (cols - 1) * dx // 2, "y": row * dy - 200}
        if per_node_display:
            _set(entry, per_node_display, pos)
        else:
            disp[nid] = pos

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
        rid = adapter.id_for("relationship", j, r.type)
        if rid in rc:
            raise EmitError(f"duplicate relationship id {rid} (type {r.type})")
        rc[rid] = e

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
