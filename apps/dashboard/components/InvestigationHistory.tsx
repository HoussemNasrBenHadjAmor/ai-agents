"use client";

import { formatDate, formatDuration } from "@/lib/format";
import type { InvestigationSummary } from "@/types/investigation";
import { EmptyState, LoadingState } from "@/components/EmptyState";
import { StatusBadge } from "@/components/badges";

export function InvestigationHistory({
  history,
  loading,
  selectedInvestigationId,
  onSelect,
}: {
  history: InvestigationSummary[];
  loading: boolean;
  selectedInvestigationId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="history-panel">
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
            onSelect={() => onSelect(item.id)}
          />
        ))}
      </div>
    </div>
  );
}

function HistoryItem({
  item,
  selected,
  onSelect,
}: {
  item: InvestigationSummary;
  selected: boolean;
  onSelect: () => void;
}) {
  const headline = item.headline || item.message;
  const duration = item.metrics?.duration_seconds;

  return (
    <button
      type="button"
      className={`history-item ${selected ? "is-selected" : ""}`}
      onClick={onSelect}
      aria-current={selected ? "true" : undefined}
    >
      <span className="history-item-topline">
        <StatusBadge status={item.status} />
        <span>{formatDate(item.created_at)}</span>
      </span>
      <span className="history-title">{headline}</span>
      <span className="history-preview">{item.message}</span>
      <span className="history-meta">
        <span>{duration ? formatDuration(duration) : "No duration yet"}</span>
        <span>{item.completed_at ? "Finished" : "Open"}</span>
      </span>
    </button>
  );
}

