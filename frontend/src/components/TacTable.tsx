import React from "react";
import type { Quad } from "../types/analysis";

const TacTable = ({ data }: { data?: Quad[] }) => {
  const th = {
    textAlign: "left" as const,
    borderBottom: "1px solid #ddd",
    padding: 6,
  };

  const td = { borderBottom: "1px solid #eee", padding: 6 };
  const tdMono = {
    ...td,
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
  };

  const stringify = (v: unknown) => {
    if (v === null || v === undefined) return "";
    if (typeof v === "string") return v;
    if (typeof v === "boolean") return v ? "1" : "0";
    return String(v);
  };

  if (!data || data.length === 0) return <div>No TAC generated</div>;
  return (
    <div style={{ height: "100%", overflow: "auto" }}>
      <table
        style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}
      >
        <thead>
          <tr>
            <th style={th}>#</th>
            <th style={th}>op</th>
            <th style={th}>arg1</th>
            <th style={th}>arg2</th>
            <th style={th}>result</th>
          </tr>
        </thead>
        <tbody>
          {data.map((q) => (
            <tr key={q.id}>
              <td style={tdMono}>{q.id}</td>
              <td style={td}>{q.op ?? ""}</td>
              <td style={tdMono}>{stringify(q.arg1)}</td>
              <td style={tdMono}>{stringify(q.arg2)}</td>
              <td style={tdMono}>{stringify(q.result)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TacTable;
