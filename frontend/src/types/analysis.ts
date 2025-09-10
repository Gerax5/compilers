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
}
