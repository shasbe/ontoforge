"""Intermediate representation. Every ingester normalises to this, so the
transformation rules and emitters are written once."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional, Any
import json

CLASS = "class"; OBJ_PROP = "object_property"; DATA_PROP = "datatype_property"
INDIVIDUAL = "individual"; DATATYPE = "datatype"


@dataclass
class Entity:
    iri: str
    local_name: str
    kind: str
    label: Optional[str] = None
    definition: Optional[str] = None
    module: Optional[str] = None
    types: list[str] = field(default_factory=list)     # rdf:type local names
    annotations: dict[str, str] = field(default_factory=dict)


@dataclass
class Hierarchy:
    child: str
    parent: str
    kind: str = "subclass"                             # subclass | subproperty


@dataclass
class Constraint:
    """An OWL restriction, FHIR element, or XSD particle -- normalised.

    `is_anonymous` records whether the target was a blank node / inline
    expression. Retaining that is what stops anonymous class expressions being
    emitted as graph nodes (42% of FIBO's subclass axioms point at them)."""
    subject: str
    predicate: str
    target: Optional[str]
    kind: str                                          # some|all|value|min|max|exact|domain_range
    min: Optional[int] = None
    max: Optional[int] = None
    is_anonymous: bool = False
    via_datatype_property: bool = False


@dataclass
class SourceMeta:
    standard: str
    version: str
    fetched_from: str
    source_format: str
    triples: int = 0
    files_parsed: int = 0
    notes: list[str] = field(default_factory=list)


@dataclass
class IR:
    meta: SourceMeta
    entities: dict[str, Entity] = field(default_factory=dict)
    hierarchy: list[Hierarchy] = field(default_factory=list)
    constraints: list[Constraint] = field(default_factory=list)

    # ---- convenience views
    def of_kind(self, kind: str) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == kind]

    def by_local_name(self) -> dict[str, list[Entity]]:
        out: dict[str, list[Entity]] = {}
        for e in self.entities.values():
            out.setdefault(e.local_name, []).append(e)
        return out

    def children(self) -> dict[str, set[str]]:
        out: dict[str, set[str]] = {}
        for h in self.hierarchy:
            out.setdefault(h.parent, set()).add(h.child)
        return out

    def parents(self) -> dict[str, set[str]]:
        out: dict[str, set[str]] = {}
        for h in self.hierarchy:
            out.setdefault(h.child, set()).add(h.parent)
        return out

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump({"meta": asdict(self.meta),
                       "entities": {k: asdict(v) for k, v in self.entities.items()},
                       "hierarchy": [asdict(h) for h in self.hierarchy],
                       "constraints": [asdict(c) for c in self.constraints]}, f)

    @staticmethod
    def load(path: str) -> "IR":
        d = json.load(open(path))
        ir = IR(meta=SourceMeta(**d["meta"]))
        ir.entities = {k: Entity(**v) for k, v in d["entities"].items()}
        ir.hierarchy = [Hierarchy(**h) for h in d["hierarchy"]]
        ir.constraints = [Constraint(**c) for c in d["constraints"]]
        return ir
