import type { AnalyzeResp } from "../types/analysis";

const API =
  (import.meta as ImportMeta).env?.VITE_API_URL ||
  (import.meta as ImportMeta).env?.VITE_API ||
  "http://localhost:8000";

export async function analyze(code: string): Promise<AnalyzeResp> {
  const r = await fetch(`${API}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}
