"use client";

import Link from "next/link";
import { formatDate, formatDuration } from "@/lib/format";
import type { InvestigationSummary } from "@/types/investigation";
import { EmptyState, LoadingState } from "@/components/EmptyState";
import { StatusBadge } from "@/components/badges";

export function InvestigationHistory({
  history,
  loading,
  selectedInvestigationId,
  onNavigate,
}: {
  history: InvestigationSummary[];
  loading: boolean;
  selectedInvestigationId: string | null;
  onNavigate?: () => void;
}) {
  return (
    <nav className="history-panel" aria-label="Previous investigations">
      <div className="history-header">
        <div>
          <p className="eyebrow">History</p>
          <h2>Previous runs</h2>
        </div>
        <span className="history-count">{history.length}</span>
      </div>

      {loading && <LoadingState label="Loading history" />}

      {!loading && history.length === 0 && (
        <EmptyState
          title="No investigations"
          message="Completed investigations will appear here for quick review."
        />
      )}

      <div className="history-list">
        {history.map((item) => (
          <HistoryItem
            key={item.id}
            item={item}
            selected={item.id === selectedInvestigationId}
            onNavigate={onNavigate}
          />
        ))}
      </div>
    </nav>
  );
}

function HistoryItem({
  item,
  selected,
  onNavigate,
}: {
  item: InvestigationSummary;
  selected: boolean;
  onNavigate?: () => void;
}) {
  const headline = item.headline || item.message;
  const duration = item.metrics?.duration_seconds;
  const durationLabel =
    typeof duration === "number" ? formatDuration(duration) : "No duration yet";

  return (
    <Link
      href={`/investigation/${item.id}`}
      className={`history-item ${selected ? "is-selected" : ""}`}
      onClick={onNavigate}
      aria-current={selected ? "page" : undefined}
    >
      <span className="history-item-topline">
        <StatusBadge status={item.status} />
        <span>{formatDate(item.created_at)}</span>
      </span>
      <span className="history-title">{headline}</span>
      <span className="history-preview">{item.message}</span>
      <span className="history-meta">
        <span>{durationLabel}</span>
        <span>{item.completed_at ? "Finished" : "Open"}</span>
      </span>
    </Link>
  );
}
