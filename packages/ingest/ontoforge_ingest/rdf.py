"""RDF family ingester: RDF/XML, Turtle, N-Triples, JSON-LD, OWL, SKOS, OBO-in-RDF.
One ingester covers ~25 of the surveyed standards."""
from __future__ import annotations
import glob, os, collections
from rdflib import Graph, RDF, RDFS, OWL, URIRef, BNode, Literal
from rdflib.namespace import SKOS, DCTERMS
from rdflib import URIRef as _U
from ontoforge.ir import (IR, Entity, Hierarchy, Constraint, SourceMeta,
                          CLASS, OBJ_PROP, DATA_PROP, INDIVIDUAL)

# Definition annotations differ by ontology family. BFO/OBO-derived ontologies
# (IOF) use IAO_0000115 rather than skos:definition.
DEFINITION_PREDICATES = [
    SKOS.definition,
    _U("http://purl.obolibrary.org/obo/IAO_0000115"),
    RDFS.comment,
    DCTERMS.description,
]

EXT_FORMAT = {".rdf": "xml", ".owl": "xml", ".xml": "xml", ".ttl": "turtle",
              ".nt": "nt", ".n3": "n3", ".jsonld": "json-ld", ".trig": "trig"}

RESTRICTION_KINDS = [("some", OWL.someValuesFrom), ("all", OWL.allValuesFrom),
                     ("value", OWL.hasValue), ("min", OWL.minQualifiedCardinality),
                     ("exact", OWL.qualifiedCardinality), ("max", OWL.maxQualifiedCardinality),
                     ("min", OWL.minCardinality), ("exact", OWL.cardinality),
                     ("max", OWL.maxCardinality)]


def local(u) -> str:
    s = str(u)
    return s.split("#")[-1] if "#" in s else s.rstrip("/").split("/")[-1]


def module_of(u) -> str:
    s = str(u)
    for marker in ("/ontology/", "/spec/", "/voc/"):
        if marker in s:
            return s.split(marker, 1)[1].split("/")[0]
    return ""


def expand(paths: list[str], exclude: tuple[str, ...] = ("About", "Metadata", "catalog")) -> list[str]:
    out: list[str] = []
    for p in paths:
        hits = sorted(glob.glob(p, recursive=True)) if any(c in p for c in "*?[") else [p]
        for h in hits:
            if os.path.isfile(h) and os.path.splitext(h)[1].lower() in EXT_FORMAT \
               and not any(x in os.path.basename(h) for x in exclude):
                out.append(h)
    return sorted(set(out))


def ingest(paths: list[str], standard: str, version: str, fetched_from: str,
           exclude: tuple[str, ...] = ("About", "Metadata", "catalog")) -> IR:
    files = expand(paths, exclude)
    if not files:
        raise FileNotFoundError(f"no RDF files matched {paths}")
    g = Graph()
    parsed, notes = 0, []
    fmts = set()
    for fp in files:
        fmt = EXT_FORMAT[os.path.splitext(fp)[1].lower()]
        fmts.add(fmt)
        try:
            g.parse(fp, format=fmt); parsed += 1
        except Exception as e:
            notes.append(f"parse failure {os.path.basename(fp)}: {str(e)[:120]}")

    ir = IR(meta=SourceMeta(standard=standard, version=version, fetched_from=fetched_from,
                            source_format="/".join(sorted(fmts)), triples=len(g),
                            files_parsed=parsed, notes=notes))

    kinds = [(OWL.Class, CLASS), (RDFS.Class, CLASS), (OWL.ObjectProperty, OBJ_PROP),
             (OWL.DatatypeProperty, DATA_PROP), (RDF.Property, OBJ_PROP),
             (OWL.NamedIndividual, INDIVIDUAL)]
    for rdftype, kind in kinds:
        for s in g.subjects(RDF.type, rdftype):
            if not isinstance(s, URIRef):
                continue
            key = str(s)
            if key in ir.entities and ir.entities[key].kind != INDIVIDUAL:
                continue
            lbl = g.value(s, RDFS.label) or g.value(s, SKOS.prefLabel)
            dfn = next((v for v in (g.value(s, p) for p in DEFINITION_PREDICATES)
                        if v is not None), None)
            ann = {}
            ex = g.value(s, SKOS.example)
            if ex is not None:
                ann["example"] = " ".join(str(ex).split())
            db = g.value(s, RDFS.isDefinedBy)
            if db is not None:
                ann["isDefinedBy"] = str(db)
            ir.entities[key] = Entity(
                iri=key, local_name=local(s), kind=kind,
                label=str(lbl) if lbl else None,
                definition=" ".join(str(dfn).split()) if dfn else None,
                module=module_of(s),
                types=sorted({local(o) for o in g.objects(s, RDF.type) if isinstance(o, URIRef)}),
                annotations=ann)

    for pred, hkind in ((RDFS.subClassOf, "subclass"), (RDFS.subPropertyOf, "subproperty")):
        for s, _, o in g.triples((None, pred, None)):
            if isinstance(s, URIRef) and isinstance(o, URIRef):
                ir.hierarchy.append(Hierarchy(child=str(s), parent=str(o), kind=hkind))

    dprops = {e.iri for e in ir.of_kind(DATA_PROP)}
    # restrictions reached via subClassOf blank nodes
    for s, _, r in g.triples((None, RDFS.subClassOf, None)):
        if not isinstance(r, BNode) or (r, RDF.type, OWL.Restriction) not in g:
            continue
        prop = g.value(r, OWL.onProperty)
        for kind, pred in RESTRICTION_KINDS:
            v = g.value(r, pred)
            if v is None:
                continue
            if kind in ("min", "exact", "max"):
                tgt = g.value(r, OWL.onClass) or g.value(r, OWL.onDataRange)
                n = int(v) if isinstance(v, Literal) else None
                ir.constraints.append(Constraint(
                    subject=str(s), predicate=str(prop) if prop else "",
                    target=str(tgt) if isinstance(tgt, URIRef) else None, kind=kind,
                    min=n if kind in ("min", "exact") else None,
                    max=n if kind in ("max", "exact") else None,
                    is_anonymous=not isinstance(tgt, URIRef),
                    via_datatype_property=str(prop) in dprops))
            else:
                ir.constraints.append(Constraint(
                    subject=str(s), predicate=str(prop) if prop else "",
                    target=str(v) if isinstance(v, URIRef) else None, kind=kind,
                    is_anonymous=not isinstance(v, URIRef),
                    via_datatype_property=str(prop) in dprops))
    # declared domain/range (the main signal in schema.org-style vocabularies like GS1)
    for p in list(ir.entities):
        e = ir.entities[p]
        if e.kind not in (OBJ_PROP, DATA_PROP):
            continue
        dom = g.value(URIRef(p), RDFS.domain); rng = g.value(URIRef(p), RDFS.range)
        if dom is not None or rng is not None:
            ir.constraints.append(Constraint(
                subject=str(dom) if isinstance(dom, URIRef) else "",
                predicate=p,
                target=str(rng) if isinstance(rng, URIRef) else None,
                kind="domain_range",
                is_anonymous=not isinstance(rng, URIRef),
                via_datatype_property=e.kind == DATA_PROP))
    return ir
