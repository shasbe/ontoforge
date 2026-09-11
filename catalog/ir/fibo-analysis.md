# fibo -- source analysis

- source: `github.com/edmcouncil/fibo`
- version: `119fa8c`  format: xml
- 130,273 triples from 221 file(s)

- classes: **3,021**
- object properties: **946**
- datatype properties: **263**
- individuals: **12,029**
- hierarchy edges: **4,887**
- constraints: **3,969**
- anonymous constraint targets: **336**

- definitions present on **85.5%** of the 4,230 schema entities; definition-or-example on **85.5%** (drives LLM grounding value)
- **8.5%** of constraints target anonymous expressions -- these must not become graph nodes
- **42.1%** of subClassOf axioms point at blank nodes rather than named classes, i.e. most of the apparent 'hierarchy' is really OWL restrictions -- the core reason a naive RDF import fails
- hierarchy depth up to **12**; **662** classes have >1 parent (max 7)

## Combinatorial subclassing warning
371 class names have >=6 CamelCase words (188 have >=8). These are feature combinations encoded as classes and should become properties, not labels.

- `PreferredEnhancedVotingRedeemableExchangeableExtendableAuctionRateIncomeRegisteredShare`
- `PreferredNonVotingRedeemableExchangeableExtendableAuctionRateIncomeRegisteredShare`
- `PreferredRestrictedVotingRedeemableExchangeableExtendableAuctionRateIncomeRegisteredShare`
- `ForeignBranchOfForeignBankManagedByUSOffice`
- `PreferredEnhancedVotingRedeemableExchangeableAuctionRateIncomeRegisteredShare`

## Hub ranking (node-selection candidates, by in-degree)

-   102  `MonetaryAmount`
-    75  `https://www.omg.org/spec/Commons/DatesAndTimes/ExplicitDate`
-    63  `https://www.omg.org/spec/Commons/DatesAndTimes/Date`
-    45  `https://www.omg.org/spec/Commons/DatesAndTimes/DatePeriod`
-    44  `Currency`
-    42  `Security`
-    34  `https://www.omg.org/spec/Commons/RegulatoryAgencies/Jurisdiction`
-    31  `SecuritiesUnderwritingIssuanceProcess`
-    25  `MonetaryPrice`
-    20  `Party`
-    20  `https://www.omg.org/spec/Commons/DatesAndTimes/Duration`
-    20  `RecurrenceInterval`
-    17  `https://www.omg.org/spec/Commons/Locations/Country`
-    17  `LegalPerson`
-    16  `Contract`
-    16  `https://www.omg.org/spec/Commons/DatesAndTimes/DateTime`
-    15  `LegalEntity`
-    15  `LoanSecuredByRealEstate`
-    15  `https://www.omg.org/spec/Commons/PartiesAndSituations/PartyRole`
-    14  `LegallyCompetentNaturalPerson`
-    14  `PercentageMonetaryAmount`
-    14  `https://www.omg.org/spec/Commons/QuantitiesAndUnits/Percentage`
-    13  `Exchange`
-    13  `RegulatoryAgency`
-    12  `Asset`

## Widest parents (collapse candidates)

-   221  `RegisteredSecurity`
-   112  `PreferredShareWithFixedRateDividend`
-    84  `ExchangeablePreferredShare`
-    84  `ExtendablePreferredShare`
-    72  `NonCumulativePreferredShare`
-    56  `CumulativePreferredShare`
-    56  `ParticipatingPreferredShare`
-    56  `NonParticipatingPreferredShare`
-    55  `https://www.omg.org/spec/Commons/Classifiers/Classifier`
-    55  `EnhancedVotingShare`
-    55  `NonVotingShare`
-    55  `RestrictedVotingShare`
-    55  `SingleVotingShare`
-    42  `https://www.omg.org/spec/Commons/DatesAndTimes/hasExplicitDate`
-    37  `https://www.omg.org/spec/Commons/PartiesAndSituations/PartyRole`
-    36  `hasMonetaryAmount`
-    34  `IssuanceProcessActivity`
-    29  `https://www.omg.org/spec/Commons/CodesAndCodeSets/CodeElement`
-    28  `PreferredShareWithAdjustableRateDividend`
-    28  `PreferredShareWithAuctionRateDividend`
