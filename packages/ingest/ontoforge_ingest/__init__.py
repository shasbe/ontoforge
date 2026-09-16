from . import rdf, fhir, rosetta
REGISTRY = {"rdf": rdf.ingest, "fhir": fhir.ingest, "rosetta": rosetta.ingest}
__all__ = ["rdf", "fhir", "rosetta", "REGISTRY"]
