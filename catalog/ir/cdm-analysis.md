# cdm -- source analysis

- source: `github.com/finos/common-domain-model`
- version: `FINOS CDM (main)`  format: rosetta-dsl
- 7,193 triples from 145 file(s)

- classes: **1,059**
- object properties: **0**
- datatype properties: **0**
- individuals: **4,226**
- hierarchy edges: **200**
- constraints: **2,767**
- anonymous constraint targets: **0**

- definitions present on **90.1%** of the 1,086 schema entities; definition-or-example on **90.1%** (drives LLM grounding value)
- **0.0%** of constraints target anonymous expressions -- these must not become graph nodes
- **0.0%** of subClassOf axioms point at blank nodes rather than named classes, i.e. most of the apparent 'hierarchy' is really OWL restrictions -- the core reason a naive RDF import fails
- hierarchy depth up to **4**; **32** classes have >1 parent (max 2)

## Combinatorial subclassing warning
31 class names have >=6 CamelCase words (7 have >=8). These are feature combinations encoded as classes and should become properties, not labels.

- `US_CFTC_PR_EligibleCollateralEnum`
- `EU_EMIR_EligibleCollateralEnum`
- `UK_EMIR_EligibleCollateralEnum`
- `FxForceMajeureOrActOfSStateEnum`
- `CSASpecifiedOrAccessConditionEnum`

## Hub ranking (node-selection candidates, by in-degree)

-    56  `CounterpartyRoleEnum`
-    45  `Money`
-    43  `Party`
-    23  `Price`
-    21  `AdjustableOrRelativeDate`
-    19  `LegalEntity`
-    17  `BusinessCenterTime`
-    17  `PriceSchedule`
-    16  `Identifier`
-    14  `RelativeDateOffset`
-    13  `BusinessDayAdjustments`
-    13  `Period`
-    12  `BusinessCenters`
-    12  `EscrowArrangement`
-    11  `PartyRole`
-    10  `TimeZone`
-    10  `Quantity`
-    10  `FloatingRateIndexEnum`
-     9  `Offset`
-     9  `Account`
-     9  `ValuationPostponement`
-     8  `Security`
-     8  `TradeState`
-     8  `Clause`
-     7  `AncillaryRoleEnum`

## Widest parents (collapse candidates)

-    21  `CollateralCriteria`
-     8  `PayoutBase`
-     8  `Payout`
-     6  `AssetBase`
-     6  `IndexBase`
-     5  `Index`
-     4  `CalculationAndTimingBase`
-     4  `CreditSupportObligationsBase`
-     4  `Asset`
-     4  `EligibilityToHoldCollateralCriteria`
-     3  `Schedule`
-     3  `MeasureBase`
-     3  `InstrumentBase`
-     3  `Identifier`
-     3  `TransferBase`
-     3  `MarginCallBase`
-     3  `ContactInformationElection`
-     3  `CreditSupportAgreementElectionsBase`
-     3  `ThresholdMinimumTransferAmountBase`
-     3  `MasterAgreementBase`
