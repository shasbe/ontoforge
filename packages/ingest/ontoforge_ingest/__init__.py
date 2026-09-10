from . import rdf, fhir
REGISTRY = {"rdf": rdf.ingest, "fhir": fhir.ingest}
__all__ = ["rdf", "fhir", "REGISTRY"]
