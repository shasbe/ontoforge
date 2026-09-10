# auto -- source analysis

- source: `github.com/edmcouncil/auto`
- version: `main`  format: xml
- 13,474 triples from 8 file(s)

- classes: **1,171**
- object properties: **172**
- datatype properties: **134**
- individuals: **58**
- hierarchy edges: **1,297**
- constraints: **1,030**
- anonymous constraint targets: **80**

- definitions present on **92.7%** of the 1,477 schema entities; definition-or-example on **92.7%** (drives LLM grounding value)
- **7.8%** of constraints target anonymous expressions -- these must not become graph nodes
- **40.9%** of subClassOf axioms point at blank nodes rather than named classes, i.e. most of the apparent 'hierarchy' is really OWL restrictions -- the core reason a naive RDF import fails
- hierarchy depth up to **12**; **92** classes have >1 parent (max 3)

## Combinatorial subclassing warning
21 class names have >=6 CamelCase words (3 have >=8). These are feature combinations encoded as classes and should become properties, not labels.

- `MonitorVehiclePerformanceForDDTPerformanceRelevantSystemFailures`
- `FreewayLowSpeedOptimalRoadMaintenanceFairWeather`
- `InVehicleDynamicDriverTaskFallbackReadyUser`
- `DDTPerformanceRelevantSystemFailure`
- `RemoteDynamicDriverTaskFallbackReadyUser`

## Hub ranking (node-selection candidates, by in-degree)

-   119  `DimensionlessUnit`
-    20  `DiagnosticSystem`
-    17  `QuantitativeValueFloat`
-    17  `PriceSpecification`
-    14  `ChoiceOrComponent`
-    13  `Cabin`
-    13  `MultimediaSystem`
-    12  `QuantitativeValue`
-    11  `TemperatureUnit`
-    10  `Body`
-    10  `PressureOrStressUnit`
-     9  `TimeUnit`
-     9  `GPS`
-     9  `AngleUnit`
-     8  `AutomatedDrivingSystemEquippedVehicle`
-     8  `Seat`
-     8  `Timer`
-     8  `LengthUnit`
-     7  `HumanDriver`
-     7  `TrafficViolation`
-     6  `MotorVehicle`
-     6  `ADAS`
-     6  `Drivetrain`
-     6  `SeatSwitch`
-     6  `SeatPositionActuator`

## Widest parents (collapse candidates)

-   193  `ObservableSignal`
-   120  `VehiclePart`
-    99  `VehicleSensor`
-    89  `ActuableSignal`
-    56  `Actuator`
-    32  `Crash`
-    22  `Process`
-    21  `ValueSpace`
-    20  `Infrastructure`
-    17  `QualitativeValue`
-    15  `ExternalLights`
-    15  `http://www.w3.org/2002/07/owl#topDataProperty`
-    13  `Operation`
-    12  `Trafficway`
-    12  `Role`
-    11  `RoadPart`
-    11  `CollisionCrash`
-    11  `CargoEquipment`
-    11  `http://www.w3.org/2002/07/owl#topObjectProperty`
-    10  `MaterialEntity`
