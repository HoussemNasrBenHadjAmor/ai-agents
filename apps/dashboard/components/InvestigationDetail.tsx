import Link from "next/link";
import { formatDate, formatDuration } from "@/lib/format";
import { DiagnosisSummary } from "@/components/DiagnosisSummary";
import { ErrorState, LoadingState } from "@/components/EmptyState";
import { InvestigationMetrics } from "@/components/InvestigationMetrics";
import { InvestigationProgress } from "@/components/InvestigationProgress";
import { StatusBadge } from "@/components/badges";
import type {
  Diagnosis,
  InvestigationEvent,
  InvestigationMetrics as Metrics,
} from "@/types/investigation";

export function InvestigationDetail({
  prompt,
  status,
  createdAt,
  completedAt,
  events,
  metrics,
  diagnosis,
  result,
  error,
  loading,
  saved = false,
}: {
  prompt: string;
  status?: string | null;
  createdAt?: string | null;
  completedAt?: string | null;
  events: InvestigationEvent[];
  metrics: Metrics | null;
  diagnosis: Diagnosis | null;
  result: string;
  error?: string | null;
  loading: boolean;
  saved?: boolean;
}) {
  const activeAgent = [...events]
    .reverse()
    .find((event) => event.agent && event.type !== "agent_completed")?.agent;

  const completedTools = events.filter(
    (event) => event.type === "tool_completed",
  ).length;

  return (
    <div className="dashboard-content">
      {(saved || prompt || activeAgent || completedTools > 0) && (
        <section className="investigation-detail-header">
          <div className="detail-title-row">
            <div>
              <p className="eyebrow">
                {saved ? "Saved investigation" : "Current investigation"}
              </p>
              <h2>{saved ? "Investigation" : "Live run"}</h2>
            </div>
            <div className="detail-actions">
              {status && <StatusBadge status={status} />}
              {saved && (
                <Link className="new-investigation-link" href="/">
                  New investigation
                </Link>
              )}
            </div>
          </div>
          <div className="detail-meta-grid">
            <DetailMeta label="Prompt" value={prompt || "No prompt recorded"} />
            {(saved || createdAt) && (
              <DetailMeta label="Created" value={formatDate(createdAt)} />
            )}
            {(saved || completedAt) && (
              <DetailMeta
                label="Completed"
                value={completedAt ? formatDate(completedAt) : "Not completed"}
              />
            )}
            <DetailMeta
              label="Active agent"
              value={activeAgent ?? (loading ? "Orchestrator" : "Idle")}
            />
            <DetailMeta label="Tools completed" value={String(completedTools)} />
            {metrics && (
              <DetailMeta
                label="Duration"
                value={formatDuration(metrics.duration_seconds)}
              />
            )}
          </div>
        </section>
      )}

      {error && <ErrorState message={error} />}
      {loading && events.length === 0 && (
        <LoadingState label="Opening investigation stream" />
      )}

      <DiagnosisSummary diagnosis={diagnosis} result={result} />
      <InvestigationProgress events={events} loading={loading} />
      <InvestigationMetrics metrics={metrics} />
    </div>
  );
}

function DetailMeta({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
