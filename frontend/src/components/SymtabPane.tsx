import React, { useMemo, useState } from "react";
import type { ScopeNode, SymEntry } from "../types/analysis";

function Tree({
  node,
  selected,
  onSelect,
  level = 0,
}: {
  node: ScopeNode;
  selected?: string;
  onSelect: (id: string) => void;
  level?: number;
}) {
  const isSel = selected === node.id;
  return (
    <div>
      <div
        onClick={() => onSelect(node.id)}
        style={{
          padding: "4px 6px",
          marginLeft: level * 10,
          cursor: "pointer",
          borderRadius: 6,
          background: isSel ? "#eef6ff" : "transparent",
          border: isSel ? "1px solid #93c5fd" : "1px solid transparent",
          color: isSel ? "black" : "white",
        }}
      >
        {node.name}{" "}
        <span style={{ color: "#777" }}>({node.symbols.length})</span>
      </div>
      {(node.children || []).map((c) => (
        <Tree
          key={c.id}
          node={c}
          selected={selected}
          onSelect={onSelect}
          level={level + 1}
        />
      ))}
    </div>
  );
}

function SymbolsTable({ entries }: { entries: SymEntry[] }) {
  if (!entries?.length) return <div>Sin símbolos en este scope</div>;
  return (
    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
      <thead>
        <tr>
          <th
            style={{
              textAlign: "left",
              borderBottom: "1px solid #ddd",
              padding: 6,
            }}
          >
            Kind
          </th>
          <th
            style={{
              textAlign: "left",
              borderBottom: "1px solid #ddd",
              padding: 6,
            }}
          >
            Nombre
          </th>
          <th
            style={{
              textAlign: "left",
              borderBottom: "1px solid #ddd",
              padding: 6,
            }}
          >
            Tipo / Firma
          </th>
        </tr>
      </thead>
      <tbody>
        {entries.map((e, i) => {
          let typeOrSig = "";
          if (e.kind === "func") {
            const params = e.params
              .map((p) => `${p.name}: ${p.type}`)
              .join(", ");
            typeOrSig = `(${params}) => ${e.returnType}`;
          } else if (e.kind === "class") {
            typeOrSig = e.super ? `extends ${e.super}` : "";
          } else {
            typeOrSig = e.type;
          }
          return (
            <tr key={i}>
              <td style={{ borderBottom: "1px solid #eee", padding: 6 }}>
                {e.kind}
              </td>
              <td style={{ borderBottom: "1px solid #eee", padding: 6 }}>
                {e.name}
              </td>
              <td
                style={{
                  borderBottom: "1px solid #eee",
                  padding: 6,
                  fontFamily: "monospace",
                }}
              >
                {typeOrSig}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

export default function SymtabPane({ root }: { root?: ScopeNode }) {
  const [selected, setSelected] = useState<string | undefined>(root?.id);
  const map = useMemo(() => {
    const m = new Map<string, ScopeNode>();
    const dfs = (n?: ScopeNode) => {
      if (!n) return;
      m.set(n.id, n);
      (n.children || []).forEach(dfs);
    };
    dfs(root);
    return m;
  }, [root]);

  const current = selected ? map.get(selected) : root;

  if (!root) return <div>No se recibió tabla de símbolos</div>;

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "280px 1fr",
        height: "100%",
      }}
    >
      <div
        style={{ borderRight: "1px solid #ddd", padding: 8, overflow: "auto" }}
      >
        <div style={{ fontWeight: 600, marginBottom: 8 }}>Scopes</div>
        <Tree node={root} selected={selected} onSelect={setSelected} />
      </div>
      <div style={{ padding: 8, overflow: "auto" }}>
        <div style={{ fontWeight: 600, marginBottom: 8 }}>
          {current?.name || "Scope"} – {current?.symbols.length || 0} símbolo(s)
        </div>
        <SymbolsTable entries={current?.symbols || []} />
      </div>
    </div>
  );
}
