import React from "react";
import type { AnalyzeError } from "../types/analysis";

export const ErrorList: React.FC<{ errors: AnalyzeError[] }> = ({ errors }) => {
  if (!errors?.length) return <div>✅ Sin errores</div>;
  return (
    <div style={{ display: "grid", gap: 8 }}>
      {errors.map((e, i) => (
        <div
          key={i}
          style={{
            borderLeft: "4px solid #e11",
            paddingLeft: 8,
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
          }}
        >
          {e.line != null ? `[${e.line}:${e.col}] ` : ""}
          {e.msg}
        </div>
      ))}
    </div>
  );
};
