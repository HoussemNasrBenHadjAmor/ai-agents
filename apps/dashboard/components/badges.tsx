import type { DiagnosisIssue } from "@/types/investigation";

type Severity = DiagnosisIssue["severity"];

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span className={`badge severity-${severity}`}>
      <span className="badge-dot" aria-hidden="true" />
      {severity}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  const tone =
    normalized === "completed" || normalized.includes("healthy")
      ? "healthy"
      : normalized === "failed" || normalized.includes("critical")
        ? "critical"
        : normalized === "running" || normalized.includes("started")
          ? "info"
          : "warning";

  return (
    <span className={`badge severity-${tone}`}>
      <span className="badge-dot" aria-hidden="true" />
      {status}
    </span>
  );
}

