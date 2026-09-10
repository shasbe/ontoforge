"""Curation profile -- the one hand-maintained artifact per standard.

Across the eight models built by hand, ~80% of the work was mechanical and
~20% was judgment (which 30 of 3,021 classes matter). The profile is where
that judgment lives, in git, reviewable.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import yaml


@dataclass
class NodeSpec:
    label: str
    properties: list[tuple[str, str]]          # (name, TYPE)
    source_iri: Optional[str] = None
    note: Optional[str] = None
    x: Optional[int] = None      # explicit canvas position; grid layout if absent
    y: Optional[int] = None


@dataclass
class RelSpec:
    type: str
    start: str
    end: str
    source_property: Optional[str] = None      # provenance: the source predicate
    note: Optional[str] = None


@dataclass
class Profile:
    standard: str
    title: str
    industry: str
    source: dict = field(default_factory=dict)
    layout: dict = field(default_factory=lambda: {"columns": 6})
    nodes: list[NodeSpec] = field(default_factory=list)
    relationships: list[RelSpec] = field(default_factory=list)
    keys: dict[str, list[str]] = field(default_factory=dict)
    rules: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @staticmethod
    def load(path: str) -> "Profile":
        d = yaml.safe_load(open(path))
        nodes = [NodeSpec(label=n["label"],
                          properties=[(p["name"], p["type"]) for p in n["properties"]],
                          source_iri=n.get("source_iri"), note=n.get("note"),
                          x=n.get("x"), y=n.get("y"))
                 for n in d.get("nodes", [])]
        rels = [RelSpec(type=r["type"], start=r["start"], end=r["end"],
                        source_property=r.get("source_property"), note=r.get("note"))
                for r in d.get("relationships", [])]
        return Profile(standard=d["standard"], title=d["title"], industry=d["industry"],
                       source=d.get("source", {}), layout=d.get("layout", {"columns": 6}),
                       nodes=nodes, relationships=rels, keys=d.get("keys", {}),
                       rules=d.get("rules", {}), notes=d.get("notes", []))

    def save(self, path: str) -> None:
        d = {"standard": self.standard, "title": self.title, "industry": self.industry,
             "source": self.source, "layout": self.layout,
             "nodes": [{"label": n.label, **({"source_iri": n.source_iri} if n.source_iri else {}),
                        **({"note": n.note} if n.note else {}),
                        **({"x": n.x, "y": n.y} if n.x is not None else {}),
                        "properties": [{"name": a, "type": b} for a, b in n.properties]}
                       for n in self.nodes],
             "relationships": [{"type": r.type, "start": r.start, "end": r.end,
                                **({"source_property": r.source_property} if r.source_property else {}),
                                **({"note": r.note} if r.note else {})}
                               for r in self.relationships],
             "keys": self.keys, "rules": self.rules, "notes": self.notes}
        with open(path, "w") as f:
            yaml.safe_dump(d, f, sort_keys=False, width=100, allow_unicode=True)
