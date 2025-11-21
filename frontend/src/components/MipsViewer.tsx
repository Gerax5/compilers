import React from "react";
import { Button } from "./Button";

type MipsViewerProps = {
  mips?: string;
};

export const MipsViewer: React.FC<MipsViewerProps> = ({ mips }) => {
  const handleDownload = () => {
    if (!mips) return;

    const blob = new Blob([mips], {
      type: "text/plain;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "codegen.s";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ marginBottom: 8, textAlign: "right" }}>
        <Button label="Descargar .s" variant="primary" onClick={handleDownload} />
      </div>
      <pre
        style={{
          flex: 1,
          whiteSpace: "pre",
          background: "#111",
          color: "#0f0",
          padding: 8,
          borderRadius: 4,
          overflow: "auto",
          fontSize: 12,
        }}
      >
        {mips || "// No hay código MIPS generado aún."}
      </pre>
    </div>
  );
};

export default MipsViewer;
