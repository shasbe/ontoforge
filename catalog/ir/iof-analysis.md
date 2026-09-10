# iof -- source analysis

- source: `github.com/iofoundry/ontology`
- version: `main`  format: xml
- 25,348 triples from 29 file(s)

- classes: **1,002**
- object properties: **128**
- datatype properties: **3**
- individuals: **1**
- hierarchy edges: **1,098**
- constraints: **737**
- anonymous constraint targets: **325**

- definitions present on **0.4%** of entities; definition-or-example on **95.1%** (drives LLM grounding value)
- **44.1%** of constraints target anonymous expressions -- these must not become graph nodes
- hierarchy depth up to **7**; **3** classes have >1 parent (max 2)

## Combinatorial subclassing warning
11 class names have >=6 CamelCase words (1 have >=8). These are feature combinations encoded as classes and should become properties, not labels.

- `ComplexNGlycolylneuraminicAcidContainingNGlycanMoiety`
- `CorrectiveActionPreventiveActionEffectivenessCheck`
- `CorrectiveActionPreventiveActionPlanSpecification`
- `FailureModeAndEffectsAnalysisSpecification`
- `OneFactorAtATimeDesign`

## Hub ranking (node-selection candidates, by in-degree)

-    56  `http://purl.obolibrary.org/obo/BFO_0000040`
-    19  `http://purl.obolibrary.org/obo/BFO_0000001`
-    10  `Solution`
-    10  `RecipeProcessStage`
-    10  `InformationContentEntity`
-     9  `http://purl.obolibrary.org/obo/BFO_0000015`
-     8  `Agent`
-     8  `PlannedProcess`
-     8  `RecipeProcessOperation`
-     6  `CultureMedium`
-     6  `MaterialProduct`
-     6  `MaterialState`
-     6  `http://purl.obolibrary.org/obo/BFO_0000004`
-     5  `MolecularEntity`
-     4  `CellCulture`
-     4  `ManufacturingProcess`
-     4  `RequirementSpecification`
-     4  `ValueExpression`
-     4  `ObjectiveSpecification`
-     4  `HarmSpecification`
-     4  `RiskEstimate`
-     4  `http://purl.obolibrary.org/obo/OBI_0500000`
-     4  `http://purl.obolibrary.org/obo/BFO_0000002`
-     4  `Supplier`
-     4  `MaintainableMaterialItem`

## Widest parents (collapse candidates)

-    76  `PlannedProcess`
-    43  `http://purl.obolibrary.org/obo/BFO_0000023`
-    42  `InformationContentEntity`
-    30  `http://purl.obolibrary.org/obo/BFO_0000040`
-    27  `PlanSpecification`
-    27  `Capability`
-    26  `http://www.w3.org/2002/07/owl#topObjectProperty`
-    22  `http://purl.obolibrary.org/obo/BFO_0000019`
-    16  `OrganicMolecularEntity`
-    15  `Agent`
-    14  `AgentRole`
-    14  `http://purl.obolibrary.org/obo/BFO_0000027`
-    13  `BusinessProcess`
-    12  `ManufacturingProcess`
-    11  `http://purl.obolibrary.org/obo/BFO_0000015`
-    11  `MolecularEntityRole`
-    10  `EngineeredSystem`
-    10  `ValueExpression`
-     9  `http://purl.obolibrary.org/obo/BFO_0000145`
-     9  `MaterialState`
