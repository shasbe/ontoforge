"""Transformation rules. Each one exists because it was needed by hand on at
least one of the eight seed models."""
from __future__ import annotations
from .profile import NodeSpec, RelSpec
from .adapter import Capabilities

# xsd / FHIR / generic -> canonical token. Resolved against the adapter's enum,
# with documented fallbacks when a token is not accepted by the target.
TYPE_MAP = {
    "string": "STRING", "anyURI": "STRING", "normalizedString": "STRING",
    "langString": "STRING", "token": "STRING", "NMTOKEN": "STRING",
    "integer": "INTEGER", "int": "INTEGER", "long": "INTEGER", "short": "INTEGER",
    "positiveInteger": "INTEGER", "nonNegativeInteger": "INTEGER",
    "unsignedInt": "INTEGER", "unsignedLong": "INTEGER",
    "decimal": "FLOAT", "double": "FLOAT", "float": "FLOAT",
    "boolean": "BOOLEAN",
    "date": "DATE", "gYear": "DATE", "gYearMonth": "DATE",
    "dateTime": "DATETIME", "dateTimeStamp": "DATETIME", "instant": "DATETIME",
    "time": "TIME", "duration": "DURATION",
}

# When the target rejects a token, degrade in this order. ISO 8601 strings sort
# lexicographically, so a STRING fallback preserves ordering semantics.
FALLBACK = {
    "DATETIME": ["LOCAL_DATETIME", "ZONED_DATETIME", "DATE_TIME", "STRING"],
    "TIME": ["LOCAL_TIME", "STRING"],
    "DURATION": ["STRING"],
    "POINT": ["STRING"],
    "INTEGER": ["LONG", "FLOAT", "STRING"],
    "FLOAT": ["DOUBLE", "STRING"],
    "DATE": ["STRING"],
    "BOOLEAN": ["STRING"],
}


def map_source_type(source_type: str) -> str:
    """xsd:dateTime -> DATETIME (canonical, before target negotiation)."""
    return TYPE_MAP.get(source_type.split("#")[-1].split(":")[-1], "STRING")


def negotiate(token: str, enum: set[str], log: list[str], where: str) -> str:
    """TYPE_MAP rule: reconcile a canonical token with the target's accepted enum."""
    if token in enum:
        return token
    for alt in FALLBACK.get(token, ["STRING"]):
        if alt in enum:
            log.append(f"TYPE_MAP: {where}: {token} not accepted by target -> {alt}"
                       + (" (store ISO 8601; sorts correctly as text)"
                          if token in ("DATETIME", "TIME") and alt == "STRING" else ""))
            return alt
    raise ValueError(f"{where}: no accepted type for {token}; target enum {sorted(enum)}")


def apply_type_map(nodes: list[NodeSpec], enum: set[str], log: list[str]) -> list[NodeSpec]:
    out, changed = [], 0
    for n in nodes:
        props = []
        for name, t in n.properties:
            nt = negotiate(t, enum, log, f"{n.label}.{name}")
            if nt != t:
                changed += 1
            props.append((name, nt))
        out.append(NodeSpec(label=n.label, properties=props,
                            source_iri=n.source_iri, note=n.note, x=n.x, y=n.y))
    if changed:
        log.append(f"TYPE_MAP: {changed} property type(s) renegotiated for this target")
    return out


def apply_capabilities(nodes: list[NodeSpec], rels: list[RelSpec],
                       caps: Capabilities, log: list[str]):
    """Capability-driven rules. All no-ops on v4.0.0; they activate as the
    additive spec grows, so the same profile compiles to a better model."""
    if caps.relationship_properties:
        log.append("CAPABILITY relationship_properties=on: reification nodes such as "
                   "Ownership could collapse to edges with properties "
                   "(declare via rules.flatten_reification in the profile)")
    if caps.multi_label:
        log.append("CAPABILITY multi_label=on: discriminator properties such as "
                   "EPCISEvent.eventType could become second labels")
    if caps.node_keys:
        log.append("CAPABILITY node_keys=on: profile keys: could be emitted into the "
                   "model instead of only the Cypher DDL")
    return nodes, rels
