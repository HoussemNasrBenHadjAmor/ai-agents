export type DiagnosisSummary = {
  status: string;
  total_issues: number;
  critical: number;
  warnings: number;
  healthy: number;
  headline: string;
};

export type DiagnosisIssue = {
  resource: string;
  resource_type: string;
  status: string;
  severity: "critical" | "warning" | "info" | "healthy";
  problem: string;
  evidence: string;
  likely_cause: string;
  recommendation: string;
};

export type Diagnosis = {
  summary: DiagnosisSummary;
  issues: DiagnosisIssue[];
  narrative: string;
};

export type InvestigationMetrics = {
  duration_seconds: number;
  agents_used: string[];
  tool_calls: number;
  llm_calls: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_cost_usd?: number;
};

export type InvestigationEvent = {
  sequence?: number;
  type: string;
  agent?: string | null;
  tool?: string | null;
  message?: string | null;
  result?: string;
  diagnosis?: Diagnosis;
  metrics?: InvestigationMetrics | null;
  arguments?: Record<string, unknown>;
  created_at?: string;
};

export type InvestigationSummary = {
  id: string;
  message: string;
  status: string;
  headline?: string | null;
  metrics?: InvestigationMetrics | null;
  created_at: string;
  completed_at?: string | null;
};

export type InvestigationDetail = {
  id: string;
  message: string;
  status: string;
  result?: string | null;
  diagnosis?: Diagnosis | null;
  metrics?: InvestigationMetrics | null;
  error?: string | null;
  created_at: string;
  completed_at?: string | null;
  events: InvestigationEvent[];
};
