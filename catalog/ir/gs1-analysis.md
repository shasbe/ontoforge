# gs1 -- source analysis

- source: `ref.gs1.org/voc`
- version: `current`  format: turtle
- 18,749 triples from 1 file(s)

- classes: **56**
- object properties: **342**
- datatype properties: **215**
- individuals: **0**
- hierarchy edges: **207**
- constraints: **557**
- anonymous constraint targets: **3**

- definitions present on **100.0%** of entities; definition-or-example on **100.0%** (drives LLM grounding value)
- **0.5%** of constraints target anonymous expressions -- these must not become graph nodes
- hierarchy depth up to **3**; **2** classes have >1 parent (max 2)

## Combinatorial subclassing warning
1 class names have >=6 CamelCase words (0 have >=8). These are feature combinations encoded as classes and should become properties, not labels.

- `MilkButterCreamYogurtCheeseEggsSubstitutes`

## Hub ranking (node-selection candidates, by in-degree)

-    65  `http://www.w3.org/2001/XMLSchema#anyURI`
-    43  `NutritionMeasurementType`
-    32  `QuantitativeValue`
-    26  `Organization`
-    20  `https://ref.gs1.org/voc/NonbinaryLogicCode`
-    13  `Place`
-    10  `http://www.w3.org/2001/XMLSchema#date`
-     7  `Country`
-     7  `Product`
-     6  `ReferencedFileDetails`
-     4  `http://www.w3.org/2001/XMLSchema#string`
-     3  `https://ref.gs1.org/voc/LevelOfContainmentCode`
-     3  `http://www.w3.org/2002/07/owl#Thing`
-     2  `ContactPoint`
-     2  `http://www.w3.org/1999/02/22-rdf-syntax-ns#langString`
-     2  `http://www.w3.org/2001/XMLSchema#dateTime`
-     2  `https://ref.gs1.org/voc/StatusType`
-     2  `https://ref.gs1.org/voc/PreparationTypeCode`
-     2  `WarrantyPromise`
-     2  `https://ref.gs1.org/voc/MeasurementPrecisionCode`
-     2  `PriceSpecification`
-     2  `TextileMaterialDetails`
-     1  `https://ref.gs1.org/voc/PaymentMethod`
-     1  `LocationID_Details`
-     1  `OrganizationID_Details`

## Widest parents (collapse candidates)

-    63  `TypeCode`
-    61  `linkType`
-    40  `http://www.w3.org/2002/07/owl#Thing`
-     5  `FoodBeverageTobaccoProduct`
-     5  `http://schema.org/name`
-     4  `http://schema.org/isSimilarTo`
-     3  `http://schema.org/weight`
-     3  `http://schema.org/eligibleQuantity`
-     3  `http://schema.org/description`
-     2  `WearableProduct`
-     2  `Product`
-     2  `http://schema.org/contactPoint`
-     2  `http://schema.org/brand`
-     1  `QuantitativeValue`
-     1  `http://schema.org/MediaObject`
-     1  `Message`
-     1  `contactPoint`
-     1  `http://schema.org/availableLanguage`
-     1  `http://schema.org/inLanguage`
-     1  `http://schema.org/height`
