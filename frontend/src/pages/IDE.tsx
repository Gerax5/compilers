import React, { useState } from "react";
import { Toolbar } from "../components/Toolbar";
import { EditorPanel } from "../components/EditorPanel";
import { ResultTabs } from "../components/ResultTabs";
import { analyze } from "../services/api";
import type { AnalyzeError } from "../types/analysis";

const SAMPLE = `// Escribe tu script aquí
class A {}
function f(x:int): int { return x + 1; }
var a:int[] = [1,2,3];
try { print(1); } catch (e) { print(e); }`;

export default function IDE() {
  const [code, setCode] = useState(SAMPLE);
  const [errors, setErrors] = useState<AnalyzeError[]>([]);
  const [globals, setGlobals] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  async function onAnalyze() {
    setLoading(true);
    try {
      const res = await analyze(code);
      setErrors(res.errors || []);
      setGlobals(res.globals || []);
    } catch (e) {
      setErrors([{ line: null, col: null, msg: String(e), severity: "error" }]);
      setGlobals([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        height: "100vh",
        display: "grid",
        gridTemplateColumns: "1fr 420px",
        gridTemplateRows: "56px 1fr",
      }}
    >
      <div style={{ gridColumn: "1 / span 2" }}>
        <Toolbar onAnalyze={onAnalyze} analyzing={loading} />
      </div>
      <div
        style={{
          borderRight: "1px solid #ddd",
          width: "150vh",
          height: "100%",
        }}
      >
        <EditorPanel value={code} onChange={setCode} />
      </div>
      <div>
        <ResultTabs errors={errors} globals={globals} />
      </div>
    </div>
  );
}
