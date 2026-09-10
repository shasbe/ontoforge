"""Target Format Adapter -- the output format is data, not code.

An adapter binds IR concepts to paths in a target JSON shape. It is drafted
from an uploaded sample (+ optional JSON Schema) and then confirmed, so a new
Neo4j model-spec version is a config drop rather than a code change.

The spec is additive, so unknown fields in a newer sample are preserved as
`extra` passthrough rather than treated as errors.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
import json, os, re

try:
    import yaml
except ImportError:  # keep core importable without pyyaml
    yaml = None


def _dig(obj: Any, path: str) -> Any:
    """Minimal JSONPath-ish: '$.a.b' -> obj['a']['b']."""
    cur = obj
    for part in path.lstrip("$").strip(".").split("."):
        if part == "":
            continue
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _set(obj: dict, path: str, value: Any) -> None:
    parts = [p for p in path.lstrip("$").strip(".").split(".") if p]
    cur = obj
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
    cur[parts[-1]] = value


@dataclass
class Capabilities:
    """Drives transformation rules. All default off; an additive spec turns
    them on, and the same source then compiles to a structurally better model."""
    multi_label: bool = False
    relationship_properties: bool = False
    node_keys: bool = False
    nested_property_types: bool = False

    def summary(self) -> str:
        on = [k for k, v in self.__dict__.items() if v]
        return ", ".join(on) if on else "none"


@dataclass
class Adapter:
    target: str
    version: str
    node: dict
    relationship: dict
    display: dict
    capabilities: Capabilities = field(default_factory=Capabilities)
    version_path: str = "$.version"
    schema: Optional[dict] = None
    label_pattern: str = r"[A-Z][A-Za-z0-9]*"
    rel_type_pattern: str = r"[A-Z][A-Z0-9_]*"
    extra: dict = field(default_factory=dict)

    # ---------- loading
    @staticmethod
    def load(directory: str) -> "Adapter":
        ad_path = os.path.join(directory, "adapter.yaml")
        if yaml is None:
            raise RuntimeError("pyyaml required to load adapter.yaml")
        d = yaml.safe_load(open(ad_path))
        schema = None
        sp = os.path.join(directory, "schema.json")
        if os.path.exists(sp):
            schema = json.load(open(sp))
        caps = Capabilities(**(d.get("capabilities") or {}))
        return Adapter(target=d["target"], version=str(d["version"]),
                       node=d["node"], relationship=d["relationship"],
                       display=d.get("display") or {}, capabilities=caps,
                       version_path=d.get("version_path", "$.version"),
                       schema=schema,
                       label_pattern=d.get("label_pattern", r"[A-Z][A-Za-z0-9]*"),
                       rel_type_pattern=d.get("rel_type_pattern", r"[A-Z][A-Z0-9_]*"),
                       extra=d.get("extra") or {})

    # ---------- the accepted property-type enum
    def type_enum(self) -> set[str]:
        te = self.node.get("properties", {}).get("type_enum")
        if isinstance(te, list):
            return set(te)
        if isinstance(te, dict) and "from_schema" in te and self.schema:
            ref = te["from_schema"].lstrip("#/").split("/")
            cur: Any = self.schema
            for p in ref:
                cur = cur.get(p, {})
            if isinstance(cur, dict) and "enum" in cur:
                return set(cur["enum"])
        raise ValueError("adapter defines no resolvable property type_enum")

    def id_for(self, which: str, i: int) -> str:
        pat = {"node": self.node, "relationship": self.relationship}[which]["id_pattern"]
        return pat.replace("{i}", str(i))

    def prop_id(self, i: int) -> str:
        return self.node["properties"]["id_pattern"].replace("{i}", str(i))

    # ---------- drafting an adapter from a sample (the upload path)
    @staticmethod
    def draft_from_sample(sample: dict, target: str = "neo4j-workspace",
                          version: Optional[str] = None) -> dict:
        """Heuristically infer the adapter for an uploaded sample.

        A sample cannot convey semantics (which field is the *label* vs a
        display *name*), so this returns a draft for human confirmation and
        records what it guessed and why.
        """
        notes: list[str] = []

        def find_collection(pred) -> Optional[str]:
            for k, v in sample.items():
                if isinstance(v, dict) and v and all(isinstance(x, dict) for x in v.values()):
                    if pred(next(iter(v.values()))):
                        return f"$.{k}"
            return None

        rel_coll = find_collection(lambda e: "from" in e and "to" in e)
        node_coll = find_collection(lambda e: "from" not in e and "to" not in e
                                    and any(isinstance(x, dict) for x in e.values()))
        if not node_coll or not rel_coll:
            raise ValueError("could not locate node/relationship collections in sample")

        nodes = _dig(sample, node_coll)
        first_nid, first_node = next(iter(nodes.items()))
        rels = _dig(sample, rel_coll)
        first_rid, first_rel = next(iter(rels.items()))

        def id_pattern(key: str) -> str:
            m = re.match(r"^([A-Za-z]+[:_-]?)\d+$", key)
            return (m.group(1) + "{i}") if m else "{i}"

        # label: prefer a nested single-key dict (labels.identifier); else 'name'
        label_path, name_path = None, None
        for k, v in first_node.items():
            if isinstance(v, dict) and len(v) == 1 and isinstance(next(iter(v.values())), str):
                label_path = f"$.{k}.{next(iter(v.keys()))}"
                notes.append(f"label inferred from nested single-key object '{k}'")
                break
        for k, v in first_node.items():
            if isinstance(v, str):
                name_path = f"$.{k}"
                break
        if label_path is None and name_path:
            label_path = name_path
            notes.append("no nested label object found; using the scalar string field as label")

        # properties sub-collection
        prop_coll = None
        for k, v in first_node.items():
            if isinstance(v, dict) and v and all(isinstance(x, dict) for x in v.values()):
                prop_coll = f"$.{k}"; break
        pname = ptype = None; ptype_vals: set[str] = set()
        pid_pat = "p:{i}"
        if prop_coll:
            props = _dig(first_node, prop_coll)
            pid_pat = id_pattern(next(iter(props.keys())))
            for p in props.values():
                for pk, pv in p.items():
                    if not isinstance(pv, str):
                        continue
                    if pv.isupper():
                        ptype = ptype or f"$.{pk}"; ptype_vals.add(pv)
                    else:
                        pname = pname or f"$.{pk}"
            # collect the enum across the whole sample, not just the first node
            for n in nodes.values():
                for p in (_dig(n, prop_coll) or {}).values():
                    v = _dig(p, ptype) if ptype else None
                    if isinstance(v, str):
                        ptype_vals.add(v)
            notes.append(f"property type enum observed in sample: {sorted(ptype_vals)} "
                         "-- widen this from the JSON Schema if available, the sample "
                         "only proves these are accepted")

        # Collect every scalar field; a format may carry BOTH a type and a
        # separate display name (v4.0.0 does). Taking the first string for both
        # makes the two writes collide, so resolve them independently.
        rel_scalars = [k for k, v in first_rel.items() if isinstance(v, str)]
        rel_type_path = f"$.{rel_scalars[0]}" if rel_scalars else None
        rel_name_path = None
        if "name" in rel_scalars:
            rel_name_path = "$.name"
            if rel_scalars[0] == "name" and len(rel_scalars) > 1:
                rel_type_path = f"$.{rel_scalars[1]}"
        if rel_name_path and rel_name_path != rel_type_path:
            notes.append("relationship carries both a type and a separate 'name' field; "
                         "mapped independently")
        from_key = "from" if "from" in first_rel else None
        inner = next((kk for kk, vv in (first_rel.get("from") or {}).items()
                      if isinstance(vv, str)), "node")

        disp = None
        for k, v in sample.items():
            if k in (node_coll.lstrip("$."), rel_coll.lstrip("$.")):
                continue
            if isinstance(v, dict) and any(isinstance(x, dict) for x in v.values()):
                sub = next((kk for kk, vv in v.items() if isinstance(vv, dict)), None)
                if sub and set(_dig(v, f"$.{sub}").keys()) <= {"x", "y"} | set():
                    disp = {"nodes": f"$.{k}.{sub}"}
        if disp is None and "display" in sample:
            disp = {"nodes": "$.display.nodes"}

        draft = {
            "target": target,
            "version": version or str(sample.get("version", "unknown")),
            "version_path": "$.version",
            "node": {"collection": node_coll, "id_pattern": id_pattern(first_nid),
                     "label": label_path, "name": name_path,
                     "properties": {"collection": prop_coll, "id_pattern": pid_pat,
                                    "name": pname, "type": ptype,
                                    "type_enum": sorted(ptype_vals)}},
            "relationship": {"collection": rel_coll, "id_pattern": id_pattern(first_rid),
                             "type": rel_type_path, "name": rel_name_path,
                             "from": f"$.{from_key}.{inner}", "to": f"$.to.{inner}"},
            "display": disp or {},
            "capabilities": {"multi_label": False, "relationship_properties": False,
                             "node_keys": False, "nested_property_types": False},
            "_draft_notes": notes,
        }
        return draft
