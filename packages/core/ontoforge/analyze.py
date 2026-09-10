"""Metrics over the IR. Produces the numbers that drive node selection and the
combinatorics warnings -- i.e. the draft profile."""
from __future__ import annotations
import collections, re
from .ir import IR, CLASS, OBJ_PROP, DATA_PROP, INDIVIDUAL


def camel_words(n: str) -> list[str]:
    return re.findall(r"[A-Z][a-z0-9]*|[A-Z]+(?![a-z])", n)


def _cov(entities, pred) -> float:
    return round(100 * sum(1 for e in entities if pred(e)) / len(entities), 1) if entities else 0


def metrics(ir: IR) -> dict:
    classes = ir.of_kind(CLASS)
    schema_entities = [e for e in ir.entities.values() if e.kind != INDIVIDUAL]
    children, parents = ir.children(), ir.parents()

    # HUB_RANK -- in-degree over non-anonymous constraint targets
    indeg = collections.Counter()
    outdeg = collections.Counter()
    for c in ir.constraints:
        # Datatype targets ('string', 'boolean', xsd:*) are property value types,
        # not graph hubs -- counting them buries the real entities.
        if c.target and not c.is_anonymous and not c.via_datatype_property:
            indeg[c.target] += 1
        outdeg[c.subject] += 1

    def depth(iri, seen=frozenset()):
        ps = parents.get(iri, set())
        if iri in seen or not ps:
            return 0
        return 1 + max((depth(p, seen | {iri}) for p in ps), default=-1)

    depths = {c.iri: depth(c.iri) for c in classes}
    multi = {k: v for k, v in parents.items() if len(v) > 1}
    long_names = [c.local_name for c in classes if len(camel_words(c.local_name)) >= 6]
    anon = sum(1 for c in ir.constraints if c.is_anonymous)

    return {
        "counts": {"classes": len(classes),
                   "object_properties": len(ir.of_kind(OBJ_PROP)),
                   "datatype_properties": len(ir.of_kind(DATA_PROP)),
                   "individuals": len(ir.of_kind(INDIVIDUAL)),
                   "hierarchy_edges": len(ir.hierarchy),
                   "constraints": len(ir.constraints),
                   "anonymous_constraint_targets": anon},
        "anonymous_share": round(100 * anon / len(ir.constraints), 1) if ir.constraints else 0,
        "max_depth": max(depths.values(), default=0),
        "depth_histogram": dict(sorted(collections.Counter(depths.values()).items())),
        "multiple_inheritance": {"classes": len(multi),
                                 "max_parents": max((len(v) for v in multi.values()), default=0)},
        "combinatorics": {"names_ge_6_words": len(long_names),
                          "names_ge_8_words": len([n for n in long_names
                                                   if len(camel_words(n)) >= 8]),
                          "worst": sorted(long_names, key=lambda n: -len(camel_words(n)))[:5]},
        "top_hubs": [(ir.entities[i].local_name if i in ir.entities else i, n)
                     for i, n in indeg.most_common(25)],
        "widest_parents": [(ir.entities[p].local_name if p in ir.entities else p, len(cs))
                           for p, cs in sorted(children.items(), key=lambda x: -len(x[1]))[:20]],
        # Scoped to SCHEMA entities (classes + properties). Reference-data
        # individuals rarely carry definitions and would dilute the signal --
        # FIBO reads 39% over all 16k entities but 85% over its 4,230 schema ones.
        "definition_coverage": _cov(schema_entities, lambda e: bool(e.definition)),
        "grounding_coverage": _cov(schema_entities,
                                   lambda e: bool(e.definition or e.annotations.get("example"))),
        "schema_entities": len(schema_entities),
        # Share of subClassOf axioms whose object is a blank node -- i.e. how much
        # of the "hierarchy" is really OWL restrictions. This is the number that
        # explains why a naive RDF import produces an unusable graph.
        "anonymous_subclass_share": (
            round(100 * ir.meta.raw_counts.get("subclass_to_anonymous", 0)
                  / ir.meta.raw_counts["subclass_axioms"], 1)
            if ir.meta.raw_counts.get("subclass_axioms") else None),
    }


def report(ir: IR) -> str:
    m = metrics(ir)
    L = [f"# {ir.meta.standard} -- source analysis", "",
         f"- source: `{ir.meta.fetched_from}`",
         f"- version: `{ir.meta.version}`  format: {ir.meta.source_format}",
         f"- {ir.meta.triples:,} triples from {ir.meta.files_parsed} file(s)", ""]
    for k, v in m["counts"].items():
        L.append(f"- {k.replace('_',' ')}: **{v:,}**")
    L += ["", f"- definitions present on **{m['definition_coverage']}%** of the"
              f" {m['schema_entities']:,} schema entities;"
              f" definition-or-example on **{m['grounding_coverage']}%**"
              " (drives LLM grounding value)",
          f"- **{m['anonymous_share']}%** of constraints target anonymous expressions"
          " -- these must not become graph nodes",
          (f"- **{m['anonymous_subclass_share']}%** of subClassOf axioms point at blank"
           " nodes rather than named classes, i.e. most of the apparent 'hierarchy' is"
           " really OWL restrictions -- the core reason a naive RDF import fails"
           if m.get("anonymous_subclass_share") is not None else ""),
          f"- hierarchy depth up to **{m['max_depth']}**;"
          f" **{m['multiple_inheritance']['classes']}** classes have >1 parent"
          f" (max {m['multiple_inheritance']['max_parents']})", ""]
    c = m["combinatorics"]
    if c["names_ge_6_words"]:
        L += [f"## Combinatorial subclassing warning",
              f"{c['names_ge_6_words']} class names have >=6 CamelCase words"
              f" ({c['names_ge_8_words']} have >=8). These are feature combinations"
              " encoded as classes and should become properties, not labels.", ""]
        for n in c["worst"]:
            L.append(f"- `{n}`")
        L.append("")
    L += ["## Hub ranking (node-selection candidates, by in-degree)", ""]
    for n, d in m["top_hubs"]:
        L.append(f"- {d:5}  `{n}`")
    L += ["", "## Widest parents (collapse candidates)", ""]
    for n, d in m["widest_parents"]:
        L.append(f"- {d:5}  `{n}`")
    return "\n".join(L) + "\n"
