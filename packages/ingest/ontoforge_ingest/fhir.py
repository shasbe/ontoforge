"""HL7 FHIR ingester: StructureDefinition bundles (R4/R5/R6).

FHIR is not an ontology -- resources are JSON schemas whose graph edges are
`Reference.targetProfile` entries. Those become Constraints so the same
HUB_RANK metric works on them.
"""
from __future__ import annotations
import json
from ontoforge.ir import IR, Entity, Constraint, SourceMeta, CLASS, DATA_PROP

PRIM = {"string":"string","code":"string","uri":"string","url":"string","canonical":"string",
        "id":"string","markdown":"string","oid":"string","uuid":"string","xhtml":"string",
        "base64Binary":"string","integer":"integer","integer64":"long","positiveInt":"positiveInteger",
        "unsignedInt":"nonNegativeInteger","decimal":"decimal","boolean":"boolean",
        "date":"date","dateTime":"dateTime","instant":"instant","time":"time"}


def ingest(bundle_path: str, standard: str = "fhir", fetched_from: str = "") -> IR:
    d = json.load(open(bundle_path))
    sds = [e["resource"] for e in d.get("entry", [])
           if e.get("resource", {}).get("resourceType") == "StructureDefinition"]
    versions = {s.get("fhirVersion") for s in sds if s.get("fhirVersion")}
    concrete = [s for s in sds if s.get("kind") == "resource"
                and s.get("derivation") != "constraint" and not s.get("abstract")]
    ir = IR(meta=SourceMeta(standard=standard, version=sorted(versions)[0] if versions else "unknown",
                            fetched_from=fetched_from or bundle_path,
                            source_format="fhir-structuredefinition-json",
                            triples=sum(len(s.get("snapshot", {}).get("element", [])) for s in concrete),
                            files_parsed=1,
                            notes=[f"{len(sds)} StructureDefinitions, "
                                   f"{len(concrete)} concrete resource types"]))
    base = "http://hl7.org/fhir/StructureDefinition/"
    for s in concrete:
        ir.entities[base + s["name"]] = Entity(
            iri=base + s["name"], local_name=s["name"], kind=CLASS,
            label=s.get("title") or s["name"],
            definition=" ".join((s.get("description") or "").split()) or None,
            module=(s.get("meta", {}).get("profile") or [""])[0] or s.get("kind", ""),
            types=["StructureDefinition"])
    for s in concrete:
        subj = base + s["name"]
        for el in s.get("snapshot", {}).get("element", []):
            path = el.get("path", "")
            mn, mx = el.get("min"), el.get("max")
            for t in el.get("type", []):
                code = t.get("code")
                if code == "Reference":
                    for tp in t.get("targetProfile", []):
                        ir.constraints.append(Constraint(
                            subject=subj, predicate=path, target=tp, kind="some",
                            min=mn, max=None if mx == "*" else (int(mx) if mx else None),
                            is_anonymous=False))
                elif code in PRIM:
                    ir.constraints.append(Constraint(
                        subject=subj, predicate=path, target=PRIM[code], kind="domain_range",
                        min=mn, max=None if mx == "*" else (int(mx) if mx else None),
                        is_anonymous=False, via_datatype_property=True))
    return ir
