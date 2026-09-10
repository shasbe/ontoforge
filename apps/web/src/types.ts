/** Mirrors the shapes emitted by `ontoforge export`. Python is the source of
 *  truth for models and validation; the browser only renders and re-positions. */
export type PropDef = { type: string; name: string };
export type NodeDef = {
  labels: { identifier: string };
  properties: Record<string, PropDef>;
  name: string;
};
export type RelDef = {
  type: string;
  from: { node: string };
  to: { node: string };
  name: string;
};
export type Model = {
  version: string;
  nodes: Record<string, NodeDef>;
  relationships: Record<string, RelDef>;
  display: { nodes: Record<string, { x: number; y: number }> };
};

export type Finding = {
  gate: string;
  severity: "error" | "warning";
  message: string;
  path: string | null;
};
export type Validation = {
  findings: Finding[];
  errors: number;
  warnings: number;
  decisions: string[];
};

export type ProfileNode = {
  source_iri: string | null;
  note: string | null;
  properties: PropDef[];
};
export type ProfileMeta = {
  standard: string;
  title: string;
  industry: string;
  source: Record<string, string>;
  notes: string[];
  keys: Record<string, string[]>;
  nodes: Record<string, ProfileNode>;
};

export type IrStats = {
  triples: number;
  classes: number;
  object_properties: number;
  individuals: number;
  anonymous_share: number;
  anonymous_subclass_share?: number | null;
  max_depth: number;
  grounding_coverage?: number | null;
  top_hubs: [string, number][];
};

export type CatalogEntry = {
  standard: string;
  title: string;
  industry: string;
  source: Record<string, string>;
  nodes: number;
  properties: number;
  relationships: number;
  relationship_types: number;
  self_relationships: string[];
  errors: number;
  warnings: number;
  ir: IrStats | null;
  has_analysis: boolean;
};

export type Catalog = {
  generated_by: string;
  target: {
    name: string;
    version: string;
    type_enum: string[];
    capabilities: Record<string, boolean>;
  };
  standards: CatalogEntry[];
};
