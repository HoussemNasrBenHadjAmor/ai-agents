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
  duration_seconds?: number | null;
  agents_used?: string[] | null;
  tool_calls?: number | null;
  llm_calls?: number | null;
  input_tokens?: number | null;
  input_cache_hit_tokens?: number | null;
  input_cache_miss_tokens?: number | null;
  cache_hit_ratio_percent?: number | null;
  output_tokens?: number | null;
  reasoning_tokens?: number | null;
  total_tokens?: number | null;
  peak_llm_calls?: number | null;
  off_peak_llm_calls?: number | null;
  pricing_period?: "peak" | "off_peak" | "mixed" | "unknown" | string | null;
  peak_cache_hit_tokens?: number | null;
  peak_cache_miss_tokens?: number | null;
  peak_output_tokens?: number | null;
  off_peak_cache_hit_tokens?: number | null;
  off_peak_cache_miss_tokens?: number | null;
  off_peak_output_tokens?: number | null;
  estimated_cost_usd?: number;
  pricing_currency?: string | null;
  pricing_model?: string | null;
  pricing_rates_per_1m?: {
    off_peak?: PricingRateSet | null;
    peak?: PricingRateSet | null;
    [period: string]: PricingRateSet | null | undefined;
  } | null;
};

export type PricingRateSet = {
  cache_hit?: number | null;
  cache_miss?: number | null;
  output?: number | null;
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
