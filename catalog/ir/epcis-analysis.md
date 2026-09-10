# epcis -- source analysis

- source: `ref.gs1.org/standards/epcis/2.0.0`
- version: `2.0.0`  format: turtle
- 1,000 triples from 1 file(s)

- classes: **20**
- object properties: **48**
- datatype properties: **26**
- individuals: **0**
- hierarchy edges: **5**
- constraints: **74**
- anonymous constraint targets: **11**

- definitions present on **100.0%** of the 94 schema entities; definition-or-example on **100.0%** (drives LLM grounding value)
- **14.9%** of constraints target anonymous expressions -- these must not become graph nodes
- **0.0%** of subClassOf axioms point at blank nodes rather than named classes, i.e. most of the apparent 'hierarchy' is really OWL restrictions -- the core reason a naive RDF import fails
- hierarchy depth up to **1**; **0** classes have >1 parent (max 0)

## Combinatorial subclassing warning
4 class names have >=6 CamelCase words (0 have >=8). These are feature combinations encoded as classes and should become properties, not labels.

- `EPCISDocumentBody`
- `EPCISDocumentHeader`
- `EPCISEvent`
- `EPCISDocument`

## Hub ranking (node-selection candidates, by in-degree)

-     4  `https://gs1.org/voc/IndividualObject`
-     4  `QuantityElement`
-     3  `https://ref.gs1.org/cbv/Disp`
-     2  `https://gs1.org/voc/Place`
-     2  `EPCISEvent`
-     2  `SourceOrDestination`
-     1  `https://ref.gs1.org/cbv/BizStep`
-     1  `BizTransaction`
-     1  `https://ref.gs1.org/cbv/BTT`
-     1  `https://gs1.org/voc/CertificationDetails`
-     1  `https://gs1.org/voc/SensorDevice`
-     1  `EPCISDocumentBody`
-     1  `EPCISDocumentHeader`
-     1  `ErrorDeclaration`
-     1  `https://gs1.org/voc/SensorAlertType`
-     1  `Transformation`
-     1  `ILMD`
-     1  `MasterData`
-     1  `https://gs1.org/voc/MeasurementType`
-     1  `PersistentDisposition`
-     1  `https://ref.gs1.org/cbv/ER`
-     1  `SensorElement`
-     1  `SensorMetadata`
-     1  `SensorReport`
-     1  `https://ref.gs1.org/cbv/SDT`

## Widest parents (collapse candidates)

-     5  `EPCISEvent`
