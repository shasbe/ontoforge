# Attribution and licensing

`ontoforge` (this tool) is licensed under Apache-2.0 — see `LICENSE`.

The **catalog content** is different: each model is *derived from* a third-party
industry standard. The models are structural summaries — label names, property
names, relationship names and curation decisions — not copies of the source
ontologies. Even so, attribution matters and terms differ per standard.

## Verified from the source distributions

| Standard | Licence | Copyright holder | How verified |
|---|---|---|---|
| **FIBO** | MIT | Enterprise Data Management Council (2020) | `LICENSE` in `edmcouncil/fibo` |
| **AUTO** | MIT | edmcouncil (2020) | `LICENSE` in `edmcouncil/auto` |
| **IOF** | MIT | Industrial Ontologies Foundry (2022) | `LICENSE` in `iofoundry/ontology` |

FIBO modules additionally carry
`cmns-av:copyright "Copyright (c) 2013-2025 Object Management Group, Inc."`,
reflecting its dual EDM Council / OMG stewardship.

## Not verified — review before relying on redistribution

| Standard | Steward | Status |
|---|---|---|
| **GS1 Web Vocabulary** | GS1 | No licence triple found in `gs1Voc.ttl`. GS1 publishes under its own terms. |
| **GS1 EPCIS 2.0** | GS1 | No `dcterms:license` in the ontology file. |
| **ISO IDMP** | EDM Association / Pistoia Alliance | No `LICENSE` in the published tree; the Pistoia spec site gates the files, which is itself a signal. Underlying ISO standards are separately licensed. |
| **HL7 FHIR** | HL7 International | Not checked from the distribution. HL7 makes the specification freely available under its own terms. |

**Wikidata / Wikibase** is a special case: that model was written from the
publicly documented Wikibase data model rather than parsed from a file, so it is
original expression in this repo. Wikidata's own content is CC0.

## If you need to ship a narrower catalog

Exclude any standard from the published bundle:

```bash
PYTHONPATH=packages/core python -m ontoforge.cli export --exclude gs1 epcis idmp fhir
```

The profile and `sources.yaml` entry stay in the repo (those are this project's
own work); only the derived model, validation and analysis artifacts are omitted.

## Trademarks

FIBO is a trademark of EDM Council, Inc. GS1, GTIN, GLN and EPCIS are trademarks
of GS1 AISBL. HL7 and FHIR are trademarks of Health Level Seven International.
Used here for identification only; no endorsement implied.
