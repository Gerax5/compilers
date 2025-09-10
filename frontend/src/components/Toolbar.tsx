import React from "react";
import { Button } from "./Button";

type Props = {
  onAnalyze: () => void;
  analyzing?: boolean;
};

export const Toolbar: React.FC<Props> = ({ onAnalyze, analyzing }) => {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "8px 12px",
        borderBottom: "1px solid #ddd",
        height: 56,
      }}
    >
      <div style={{ fontWeight: 700 }}>Compiscript IDE</div>
      <Button
        label={analyzing ? "Analizando…" : "Analizar"}
        onClick={onAnalyze}
        disabled={!!analyzing}
        variant="primary"
      />
    </div>
  );
};
