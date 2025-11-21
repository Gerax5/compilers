export type Severity = "error" | "warning";

export interface AnalyzeError {
  line: number | null;
  col: number | null;
  msg: string;
  severity: Severity;
}

export interface Quad {
  id: number;
  op: string | null;
  arg1: string | number | boolean | null;
  arg2: string | number | boolean | null;
  result: string | number | boolean | null;
}

export interface AnalyzeResp {
  errors: AnalyzeError[];
  globals: string[];
  symtab?: ScopeNode;
  tac?: Quad[];
  mips?: string;
}

export type SymEntry =
  | {
      kind: "var" | "const";
      name: string;
      type: string;
      size?: number | null;
      address?: number | string | null;
    }
  | {
      kind: "func";
      name: string;
      returnType: string;
      params: { name: string; type: string }[];
      size?: number | null;
      address?: number | string | null;
    }
  | {
      kind: "class";
      name: string;
      super?: string | null;
      size?: number | null;
      address?: number | string | null;
    };

export interface ScopeNode {
  id: string;
  name: string;
  symbols: SymEntry[];
  children: ScopeNode[];
}
