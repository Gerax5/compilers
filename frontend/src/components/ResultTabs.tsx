import React, { useState } from "react";
import type { AnalyzeError } from "../types/analysis";
import { ErrorList } from "./ErrorList";
import { Button } from "./Button";

type Props = {
  errors: AnalyzeError[];
  globals: string[];
};

export const ResultTabs: React.FC<Props> = ({ errors, globals }) => {
  const [tab, setTab] = useState<"errors" | "globals">("errors");

  return (
    <div
      style={{ height: "100%", display: "grid", gridTemplateRows: "40px 1fr" }}
    >
      <div
        style={{
          display: "flex",
          borderBottom: "1px solid #ddd",
          gap: 8,
          padding: 8,
        }}
      >
        <Button
          label={`Errores ${errors.length}`}
          onClick={() => setTab("errors")}
          variant="ghost"
        />
        <Button
          label={`Simbolos globales ${globals.length}`}
          onClick={() => setTab("globals")}
          variant="ghost"
        />
      </div>
      <div style={{ overflow: "auto", padding: 8 }}>
        {tab === "errors" && <ErrorList errors={errors} />}
        {tab === "globals" && (
          <pre style={{ whiteSpace: "pre-wrap" }}>
            {(globals || []).join("\n")}
          </pre>
        )}
      </div>
    </div>
  );
};
