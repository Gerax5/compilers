import React, { useState } from "react";
import type { AnalyzeError, ScopeNode, Quad } from "../types/analysis";
import { ErrorList } from "./ErrorList";
import { Button } from "./Button";
import { SymtabPane } from "./SymtabPane";
import TacTable from "./TacTable";

type Props = {
  errors: AnalyzeError[];
  globals: string[];
  symtab?: ScopeNode;
  tac?: Quad[];
};

export const ResultTabs: React.FC<Props> = ({
  errors,
  globals,
  symtab,
  tac,
}) => {
  const [tab, setTab] = useState<"errors" | "globals" | "tabla" | "tac">(
    "errors"
  );

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
        <Button
          label={`Symbol Table`}
          onClick={() => setTab("tabla")}
          variant="ghost"
        />
        <Button
          label={`TAC ${tac?.length ?? 0}`}
          variant="ghost"
          onClick={() => setTab("tac")}
        />
      </div>
      <div style={{ overflow: "auto", padding: 8 }}>
        {tab === "errors" && <ErrorList errors={errors} />}
        {tab === "globals" && (
          <pre style={{ whiteSpace: "pre-wrap" }}>
            {(globals || []).join("\n")}
          </pre>
        )}
        {tab === "tabla" && <SymtabPane root={symtab} />}
        {tab === "tac" && <TacTable data={tac} />}
      </div>
    </div>
  );
};
