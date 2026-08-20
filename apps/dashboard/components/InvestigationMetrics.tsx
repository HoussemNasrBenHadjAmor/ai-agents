import { formatCost, formatDuration } from "@/lib/format";
import type { InvestigationMetrics as Metrics } from "@/types/investigation";

export function InvestigationMetrics({ metrics }: { metrics: Metrics | null }) {
  if (!metrics) {
    return null;
  }

  const metricItems = [
    { label: "Duration", value: formatDuration(metrics.duration_seconds) },
    {
      label: "Agents used",
      value: metrics.agents_used.length ? metrics.agents_used.join(", ") : "None",
    },
    { label: "Tool calls", value: String(metrics.tool_calls) },
    { label: "LLM calls", value: String(metrics.llm_calls) },
    { label: "Input tokens", value: metrics.input_tokens.toLocaleString() },
    { label: "Output tokens", value: metrics.output_tokens.toLocaleString() },
    { label: "Total tokens", value: metrics.total_tokens.toLocaleString() },
    { label: "Estimated cost", value: formatCost(metrics.estimated_cost_usd) },
  ];

  return (
    <section className="panel metrics-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Usage</p>
          <h2>Investigation metrics</h2>
        </div>
      </div>
      <div className="metrics-grid">
        {metricItems.map((item) => (
          <MetricCard key={item.label} label={item.label} value={item.value} />
        ))}
      </div>
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

