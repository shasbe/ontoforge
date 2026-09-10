import type { Catalog, Model, Validation, ProfileMeta } from "./types";

const BASE = `${import.meta.env.BASE_URL}catalog`;

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}/${path}`);
  if (!r.ok) throw new Error(`${path}: ${r.status} ${r.statusText}`);
  return r.json() as Promise<T>;
}

export const loadCatalog = () => get<Catalog>("index.json");
export const loadModel = (std: string) => get<Model>(`${std}/model.json`);
export const loadValidation = (std: string) => get<Validation>(`${std}/validation.json`);
export const loadProfile = (std: string) => get<ProfileMeta>(`${std}/profile.json`);

export async function loadAnalysis(std: string): Promise<string | null> {
  const r = await fetch(`${BASE}/${std}/analysis.md`);
  return r.ok ? r.text() : null;
}

/** Property-type palette. Keys are the canonical tokens; unknown types fall
 *  back to a neutral so a future additive spec still renders sensibly. */
export const TYPE_COLORS: Record<string, string> = {
  STRING: "#60a5fa",
  INTEGER: "#a78bfa",
  FLOAT: "#f472b6",
  BOOLEAN: "#fbbf24",
  DATE: "#34d399",
  DATETIME: "#2dd4bf",
  DURATION: "#fb923c",
  POINT: "#f87171",
};
export const typeColor = (t: string) => TYPE_COLORS[t] ?? "#94a3b8";

export function downloadJson(name: string, data: unknown) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export function downloadText(name: string, text: string, mime = "text/plain") {
  const blob = new Blob([text], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
