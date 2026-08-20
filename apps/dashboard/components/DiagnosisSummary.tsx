import type { ReactNode } from "react";
import { formatStatus } from "@/lib/format";
import type { Diagnosis, DiagnosisIssue } from "@/types/investigation";
import { SeverityBadge, StatusBadge } from "@/components/badges";
import { EmptyState } from "@/components/EmptyState";

export function DiagnosisSummary({
  diagnosis,
  result,
}: {
  diagnosis: Diagnosis | null;
  result: string;
}) {
  if (!diagnosis && result) {
    return (
      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Diagnosis</p>
            <h2>Text result</h2>
          </div>
        </div>
        <pre className="text-result">{result}</pre>
      </section>
    );
  }

  if (!diagnosis) {
    return (
      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Diagnosis</p>
            <h2>Findings</h2>
          </div>
        </div>
        <EmptyState
          title="No diagnosis yet"
          message="Structured findings will appear after an investigation completes."
        />
      </section>
    );
  }

  return (
    <section className="diagnosis-stack">
      <div className="panel diagnosis-hero">
        <div>
          <p className="eyebrow">Diagnosis</p>
          <h2>{diagnosis.summary.headline}</h2>
          <p>{diagnosis.narrative || "Structured investigation complete."}</p>
        </div>
        <div className="summary-grid" aria-label="Diagnosis summary">
          <SummaryStat label="Status" value={diagnosis.summary.status} />
          <SummaryStat
            label="Total issues"
            value={String(diagnosis.summary.total_issues)}
          />
          <SummaryStat
            label="Critical"
            value={String(diagnosis.summary.critical)}
            tone="critical"
          />
          <SummaryStat
            label="Warnings"
            value={String(diagnosis.summary.warnings)}
            tone="warning"
          />
          <SummaryStat
            label="Healthy"
            value={String(diagnosis.summary.healthy)}
            tone="healthy"
          />
        </div>
      </div>

      {diagnosis.issues.length > 0 ? (
        <>
          <IssuesTable issues={diagnosis.issues} />
          <div className="issue-card-list">
            {diagnosis.issues.map((issue, index) => (
              <IssueDetails
                key={`${issue.resource}-${issue.resource_type}-${index}`}
                issue={issue}
              />
            ))}
          </div>
        </>
      ) : (
        <div className="panel">
          <EmptyState
            title="No issues detected"
            message="The diagnosis did not return any structured problems."
          />
        </div>
      )}
    </section>
  );
}

function SummaryStat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: DiagnosisIssue["severity"];
}) {
  return (
    <div className={`summary-stat ${tone ? `tone-${tone}` : ""}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function IssuesTable({ issues }: { issues: DiagnosisIssue[] }) {
  return (
    <div className="panel issues-table-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Issues</p>
          <h2>Structured findings</h2>
        </div>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">Resource</th>
              <th scope="col">Type</th>
              <th scope="col">Status</th>
              <th scope="col">Problem</th>
              <th scope="col">Severity</th>
            </tr>
          </thead>
          <tbody>
            {issues.map((issue, index) => (
              <IssueRow
                key={`${issue.resource}-${issue.resource_type}-${index}`}
                issue={issue}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function IssueRow({ issue }: { issue: DiagnosisIssue }) {
  return (
    <tr>
      <td>
        <strong>{issue.resource}</strong>
      </td>
      <td>{issue.resource_type}</td>
      <td>
        <StatusBadge status={formatStatus(issue.status)} />
      </td>
      <td>{issue.problem}</td>
      <td>
        <SeverityBadge severity={issue.severity} />
      </td>
    </tr>
  );
}

function IssueDetails({ issue }: { issue: DiagnosisIssue }) {
  return (
    <article className="panel issue-details">
      <div className="issue-details-header">
        <div>
          <span>{issue.resource_type}</span>
          <h3>{issue.resource}</h3>
        </div>
        <SeverityBadge severity={issue.severity} />
      </div>
      <DetailBlock label="Problem">{issue.problem}</DetailBlock>
      <EvidenceBlock>{issue.evidence}</EvidenceBlock>
      <DetailBlock label="Likely root cause">{issue.likely_cause}</DetailBlock>
      <DetailBlock label="Recommended next step">
        {issue.recommendation}
      </DetailBlock>
    </article>
  );
}

function DetailBlock({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="detail-block">
      <span>{label}</span>
      <p>{children}</p>
    </div>
  );
}

function EvidenceBlock({ children }: { children: ReactNode }) {
  return (
    <div className="detail-block">
      <span>Evidence</span>
      <pre className="evidence-block">{children}</pre>
    </div>
  );
}
