export type Severity = "error" | "warning";

export interface AnalyzeError {
  line: number | null;
  col: number | null;
  msg: string;
  severity: Severity;
}

export interface AnalyzeResp {
  errors: AnalyzeError[];
  globals: string[];
  symtab?: ScopeNode;
}

export type SymEntry =
  | { kind: "var" | "const"; name: string; type: string }
  | {
      kind: "func";
      name: string;
      returnType: string;
      params: { name: string; type: string }[];
    }
  | { kind: "class"; name: string; super?: string | null };

export interface ScopeNode {
  id: string;
  name: string;
  symbols: SymEntry[];
  children: ScopeNode[];
}
