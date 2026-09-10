# idmp -- source analysis

- source: `spec.edmcouncil.org/idmp`
- version: `v1.4.0`  format: xml
- 15,684 triples from 6 file(s)

- classes: **457**
- object properties: **231**
- datatype properties: **91**
- individuals: **206**
- hierarchy edges: **888**
- constraints: **1,248**
- anonymous constraint targets: **148**

- definitions present on **98.0%** of entities; definition-or-example on **98.1%** (drives LLM grounding value)
- **11.9%** of constraints target anonymous expressions -- these must not become graph nodes
- hierarchy depth up to **7**; **147** classes have >1 parent (max 3)

## Combinatorial subclassing warning
15 class names have >=6 CamelCase words (2 have >=8). These are feature combinations encoded as classes and should become properties, not labels.

- `IUPACInternationalChemicalIdentifierKey`
- `IUPACInternationalChemicalIdentifier`
- `ActiveIngredientActiveMoietyBasisOfStrength`
- `ActiveIngredientEntireSubstanceBasisOfStrength`
- `ActiveIngredientReferenceSubstanceBasisOfStrength`

## Hub ranking (node-selection candidates, by in-degree)

-    25  `SubstanceName`
-    25  `MedicinalProduct`
-    19  `ReferenceSource`
-    18  `Substance`
-    15  `https://www.omg.org/spec/Commons/DatesAndTimes/ExplicitDate`
-    13  `https://www.omg.org/spec/Commons/QuantitiesAndUnits/ScalarQuantityValue`
-    12  `Amount`
-    12  `Manufacturer`
-     9  `Moiety`
-     8  `PolymerSubstance`
-     8  `Strength`
-     8  `PhysicalCharacteristic`
-     8  `MarketingAuthorization`
-     8  `MarketingStatusReason`
-     8  `ShelfLife`
-     8  `CodeElement`
-     7  `InvestigationalMedicinalProduct`
-     6  `Material`
-     6  `MolecularWeight`
-     6  `SubstanceClassifier`
-     6  `MedicinesRegulatoryAgency`
-     6  `MedicalCondition`
-     5  `MolecularStructure`
-     5  `GeneElement`
-     5  `Organism`

## Widest parents (collapse candidates)

-    97  `ISO21090-ConceptDescriptor`
-    96  `https://www.omg.org/spec/Commons/Classifiers/Classifier`
-    33  `https://www.omg.org/spec/Commons/Classifiers/isClassifiedBy`
-    24  `hasTextValue`
-    21  `Specification`
-    17  `CodeElement`
-    15  `https://www.omg.org/spec/Commons/ContextualDesignators/ContextualName`
-    15  `https://www.omg.org/spec/MVF/MultipleVocabularyFacility/hasTextualName`
-    14  `https://www.omg.org/spec/Commons/Identifiers/Identifier`
-    14  `https://www.omg.org/spec/Commons/RegistrationAuthorities/RegisteredIdentifier`
-    14  `https://www.omg.org/spec/Commons/Collections/Constituent`
-    13  `https://www.omg.org/spec/Commons/RegistrationAuthorities/isRelatedTo`
-    12  `PhysicalCharacteristic`
-    12  `https://www.omg.org/spec/Commons/Documents/specifies`
-    11  `hasIntegerValue`
-    11  `https://www.omg.org/spec/Commons/Designators/isDescribedBy`
-    11  `https://www.omg.org/spec/Commons/Documents/refersTo`
-    10  `hasPhysicalCharacteristic`
-     9  `Substance`
-     9  `InactiveIngredient`
