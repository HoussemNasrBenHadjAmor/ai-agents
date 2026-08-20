"use client";

import { useEffect, useState } from "react";

type DiagnosisSummary = {
  status: string;
  total_issues: number;
  critical: number;
  warnings: number;
  healthy: number;
  headline: string;
};

type DiagnosisIssue = {
  resource: string;
  resource_type: string;
  status: string;

  severity: "critical" | "warning" | "info" | "healthy";

  problem: string;
  evidence: string;
  likely_cause: string;
  recommendation: string;
};

type Diagnosis = {
  summary: DiagnosisSummary;
  issues: DiagnosisIssue[];
  narrative: string;
};

type InvestigationEvent = {
  sequence?: number;
  type: string;

  agent?: string | null;

  tool?: string | null;

  message?: string | null;

  result?: string;

  diagnosis?: Diagnosis;

  arguments?: Record<string, unknown>;

  created_at?: string;
};

type InvestigationSummary = {
  id: string;
  message: string;
  status: string;
  headline?: string | null;
  created_at: string;
  completed_at?: string | null;
};

type InvestigationDetail = {
  id: string;
  message: string;
  status: string;

  result?: string | null;

  diagnosis?: Diagnosis | null;

  error?: string | null;

  created_at: string;

  completed_at?: string | null;

  events: InvestigationEvent[];
};

function TableHeader({ children }: { children: React.ReactNode }) {
  return (
    <th
      style={{
        padding: "14px 16px",

        textAlign: "left",

        color: "#a1a1aa",

        fontSize: "12px",

        textTransform: "uppercase",

        letterSpacing: "0.06em",

        background: "#111113",
      }}
    >
      {children}
    </th>
  );
}

function TableCell({ children }: { children: React.ReactNode }) {
  return (
    <td
      style={{
        padding: "16px",

        color: "#d4d4d8",

        fontSize: "14px",

        verticalAlign: "top",
      }}
    >
      {children}
    </td>
  );
}

function Badge({
  text,
  type,
}: {
  text: string;

  type: "critical" | "warning" | "healthy";
}) {
  const styles = {
    critical: {
      background: "#450a0a",

      color: "#fca5a5",

      border: "1px solid #7f1d1d",
    },

    warning: {
      background: "#451a03",

      color: "#fdba74",

      border: "1px solid #9a3412",
    },

    healthy: {
      background: "#052e16",

      color: "#86efac",

      border: "1px solid #166534",
    },
  };

  return (
    <span
      style={{
        ...styles[type],

        padding: "5px 10px",

        borderRadius: "999px",

        fontSize: "12px",

        fontWeight: 600,

        whiteSpace: "nowrap",
      }}
    >
      {text}
    </span>
  );
}

function SeverityBadge({
  severity,
}: {
  severity: "critical" | "warning" | "info" | "healthy";
}) {
  const mapping = {
    critical: {
      label: "● Critical",

      background: "#450a0a",

      color: "#fca5a5",

      border: "#7f1d1d",
    },

    warning: {
      label: "● Warning",

      background: "#451a03",

      color: "#fdba74",

      border: "#9a3412",
    },

    info: {
      label: "● Info",

      background: "#172554",

      color: "#93c5fd",

      border: "#1e40af",
    },

    healthy: {
      label: "● Healthy",

      background: "#052e16",

      color: "#86efac",

      border: "#166534",
    },
  };

  const style = mapping[severity] ?? mapping.info;

  return (
    <span
      style={{
        background: style.background,

        color: style.color,

        border: `1px solid ${style.border}`,

        padding: "5px 10px",

        borderRadius: "999px",

        fontSize: "12px",

        fontWeight: 600,

        whiteSpace: "nowrap",
      }}
    >
      {style.label}
    </span>
  );
}

function InfoRow({
  label,
  value,
  monospace = false,
}: {
  label: string;
  value: string;
  monospace?: boolean;
}) {
  return (
    <div
      style={{
        marginTop: "18px",
      }}
    >
      <div
        style={{
          color: "#71717a",

          fontSize: "11px",

          textTransform: "uppercase",

          letterSpacing: "0.07em",

          marginBottom: "7px",
        }}
      >
        {label}
      </div>

      <div
        style={{
          color: "#d4d4d8",

          lineHeight: 1.6,

          fontFamily: monospace ? "monospace" : "inherit",

          background: monospace ? "#09090b" : "transparent",

          padding: monospace ? "12px" : 0,

          border: monospace ? "1px solid #27272a" : "none",

          borderRadius: monospace ? "7px" : 0,

          wordBreak: "break-word",
        }}
      >
        {value}
      </div>
    </div>
  );
}

function formatStatus(status: string) {
  const lower = status.toLowerCase();

  if (lower.includes("restart")) {
    return `↻ ${status}`;
  }

  if (lower.includes("healthy")) {
    return `● ${status}`;
  }

  if (lower.includes("exit")) {
    return `■ ${status}`;
  }

  if (lower.includes("running")) {
    return `▶ ${status}`;
  }

  return status;
}

export default function Home() {
  const [message, setMessage] = useState("");

  const [result, setResult] = useState("");

  const [diagnosis, setDiagnosis] = useState<Diagnosis | null>(null);

  const [error, setError] = useState("");

  const [loading, setLoading] = useState(false);

  const [events, setEvents] = useState<InvestigationEvent[]>([]);

  const [history, setHistory] = useState<InvestigationSummary[]>([]);

  const [historyLoading, setHistoryLoading] = useState(false);

  const [selectedInvestigationId, setSelectedInvestigationId] = useState<
    string | null
  >(null);

  const [selectedPrompt, setSelectedPrompt] = useState("");

  useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    setHistoryLoading(true);

    try {
      const response = await fetch("/api/investigations", {
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error(`History request failed: ${response.status}`);
      }

      const data = await response.json();

      setHistory(data);
    } catch (err) {
      console.error("Failed to load history:", err);
    } finally {
      setHistoryLoading(false);
    }
  }

  async function loadInvestigation(investigationId: string) {
    setLoading(true);

    setError("");

    try {
      const response = await fetch(`/api/investigations/${investigationId}`, {
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error(`Investigation request failed: ${response.status}`);
      }

      const data: InvestigationDetail = await response.json();

      setSelectedInvestigationId(data.id);

      setSelectedPrompt(data.message);

      setMessage(data.message);

      setEvents(data.events);

      setResult(data.result ?? "");

      setDiagnosis(data.diagnosis ?? null);

      if (data.error) {
        setError(data.error);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to load investigation",
      );
    } finally {
      setLoading(false);
    }
  }

  async function investigate() {
    if (!message.trim()) {
      return;
    }

    setLoading(true);

    setResult("");

    setDiagnosis(null);

    setError("");

    setEvents([]);

    setSelectedInvestigationId(null);

    setSelectedPrompt(message);

    try {
      const response = await fetch("/api/investigate", {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify({
          message,
        }),
      });

      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }

      if (!response.body) {
        throw new Error("Streaming response unavailable");
      }

      const reader = response.body.getReader();

      const decoder = new TextDecoder();

      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();

        if (done) {
          break;
        }

        buffer += decoder.decode(value, {
          stream: true,
        });

        const chunks = buffer.split("\n\n");

        buffer = chunks.pop() ?? "";

        for (const chunk of chunks) {
          if (!chunk.startsWith("data: ")) {
            continue;
          }

          const raw = chunk.slice(6);

          const event: InvestigationEvent & {
            investigation_id?: string;
          } = JSON.parse(raw);

          if (event.type === "investigation_created") {
            if (event.investigation_id) {
              setSelectedInvestigationId(event.investigation_id);
            }

            continue;
          }

          if (event.type === "result") {
            setResult(event.result ?? "");

            if (event.diagnosis) {
              setDiagnosis(event.diagnosis);
            }

            continue;
          }

          if (event.type === "error") {
            setError(event.message ?? "Investigation failed");

            continue;
          }

          if (event.type !== "done") {
            setEvents((current) => [...current, event]);
          }
        }
      }

      await loadHistory();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Investigation failed");
    } finally {
      setLoading(false);
    }
  }

  function formatDate(value: string) {
    try {
      return new Intl.DateTimeFormat(undefined, {
        month: "short",

        day: "numeric",

        hour: "numeric",

        minute: "2-digit",
      }).format(new Date(value));
    } catch {
      return value;
    }
  }

  function formatEvent(event: InvestigationEvent) {
    switch (event.type) {
      case "investigation_started":
        return "Investigation started";

      case "specialist_selected":
        return `${event.agent ?? "Specialist"} Agent selected`;

      case "agent_started":
        return `${event.agent ?? "Agent"} Agent started`;

      case "tool_started":
        return `Running ${event.tool ?? "tool"}`;

      case "tool_completed":
        return `${event.tool ?? "Tool"} completed`;

      case "agent_completed":
        return `${event.agent ?? "Agent"} Agent completed`;

      case "synthesizing":
        return "Building final diagnosis";

      case "investigation_completed":
        return "Investigation completed";

      default:
        return event.message ?? event.type;
    }
  }

  function eventSymbol(event: InvestigationEvent) {
    if (
      event.type === "tool_started" ||
      event.type === "agent_started" ||
      event.type === "synthesizing"
    ) {
      return "→";
    }

    if (event.type === "investigation_started") {
      return "●";
    }

    return "✓";
  }

  return (
    <main
      style={{
        minHeight: "100vh",

        background: "#09090b",

        color: "#f4f4f5",
      }}
    >
      <div
        style={{
          display: "grid",

          gridTemplateColumns: "300px minmax(0, 1fr)",

          minHeight: "100vh",
        }}
      >
        {/* HISTORY */}

        <aside
          style={{
            borderRight: "1px solid #27272a",

            padding: "24px 16px",

            background: "#111113",

            overflowY: "auto",
          }}
        >
          <h2
            style={{
              marginTop: 0,

              marginBottom: "4px",

              fontSize: "20px",
            }}
          >
            History
          </h2>

          <p
            style={{
              color: "#71717a",

              fontSize: "13px",

              marginTop: 0,

              marginBottom: "24px",
            }}
          >
            Previous investigations
          </p>

          {historyLoading && (
            <div
              style={{
                color: "#a1a1aa",

                fontSize: "14px",
              }}
            >
              Loading history...
            </div>
          )}

          {!historyLoading && history.length === 0 && (
            <div
              style={{
                color: "#71717a",

                fontSize: "14px",
              }}
            >
              No investigations yet.
            </div>
          )}

          <div
            style={{
              display: "flex",

              flexDirection: "column",

              gap: "10px",
            }}
          >
            {history.map((item) => {
              const selected = item.id === selectedInvestigationId;

              return (
                <button
                  key={item.id}
                  onClick={() => loadInvestigation(item.id)}
                  style={{
                    width: "100%",

                    textAlign: "left",

                    padding: "12px",

                    borderRadius: "8px",

                    border: selected
                      ? "1px solid #52525b"
                      : "1px solid #27272a",

                    background: selected ? "#27272a" : "#18181b",

                    color: "#f4f4f5",

                    cursor: "pointer",
                  }}
                >
                  <div
                    style={{
                      fontSize: "13px",

                      fontWeight: 600,

                      overflow: "hidden",

                      textOverflow: "ellipsis",

                      whiteSpace: "nowrap",
                    }}
                  >
                    {item.headline ?? item.message}
                  </div>

                  <div
                    style={{
                      marginTop: "5px",

                      color: "#71717a",

                      fontSize: "11px",

                      overflow: "hidden",

                      textOverflow: "ellipsis",

                      whiteSpace: "nowrap",
                    }}
                  >
                    {item.message}
                  </div>

                  <div
                    style={{
                      marginTop: "8px",

                      display: "flex",

                      justifyContent: "space-between",

                      gap: "8px",

                      fontSize: "11px",

                      color: "#a1a1aa",
                    }}
                  >
                    <span>
                      {item.status === "completed"
                        ? "✓ Completed"
                        : item.status === "failed"
                          ? "✕ Failed"
                          : "● Running"}
                    </span>

                    <span>{formatDate(item.created_at)}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </aside>

        {/* MAIN */}

        <section
          style={{
            width: "100%",

            maxWidth: "1100px",

            margin: "0 auto",

            padding: "48px 32px",
          }}
        >
          <header>
            <h1
              style={{
                margin: 0,

                fontSize: "34px",
              }}
            >
              AI DevOps Agent
            </h1>

            <p
              style={{
                color: "#a1a1aa",

                marginTop: "8px",
              }}
            >
              Read-only infrastructure investigation
            </p>
          </header>

          {/* INPUT */}

          <section
            style={{
              marginTop: "32px",
            }}
          >
            <textarea
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder={"Example: List any unhealthy Docker containers."}
              rows={5}
              style={{
                width: "100%",

                padding: "16px",

                background: "#18181b",

                color: "#f4f4f5",

                border: "1px solid #3f3f46",

                borderRadius: "10px",

                resize: "vertical",

                outline: "none",
              }}
            />

            <button
              onClick={investigate}
              disabled={loading}
              style={{
                marginTop: "14px",

                padding: "11px 22px",

                border: 0,

                borderRadius: "8px",

                cursor: loading ? "wait" : "pointer",

                fontWeight: 600,

                opacity: loading ? 0.6 : 1,
              }}
            >
              {loading ? "Investigating..." : "Investigate"}
            </button>
          </section>

          {/* PROMPT */}

          {selectedPrompt && (
            <section
              style={{
                marginTop: "32px",

                padding: "18px",

                background: "#111113",

                border: "1px solid #27272a",

                borderRadius: "10px",
              }}
            >
              <div
                style={{
                  color: "#71717a",

                  fontSize: "12px",

                  textTransform: "uppercase",

                  letterSpacing: "0.08em",

                  marginBottom: "8px",
                }}
              >
                Investigation
              </div>

              <div>{selectedPrompt}</div>
            </section>
          )}

          {/* ERROR */}

          {error && (
            <section
              style={{
                marginTop: "28px",

                padding: "18px",

                border: "1px solid #7f1d1d",

                background: "#450a0a",

                borderRadius: "10px",
              }}
            >
              {error}
            </section>
          )}

          {/* PROGRESS */}

          {events.length > 0 && (
            <section
              style={{
                marginTop: "32px",

                padding: "24px",

                background: "#18181b",

                border: "1px solid #27272a",

                borderRadius: "10px",
              }}
            >
              <h2
                style={{
                  marginTop: 0,
                }}
              >
                Investigation Progress
              </h2>

              <div>
                {events.map((event, index) => (
                  <div
                    key={event.sequence ?? index}
                    style={{
                      display: "grid",

                      gridTemplateColumns: "32px 1fr",

                      padding: "12px 0",

                      borderBottom:
                        index === events.length - 1
                          ? "none"
                          : "1px solid #27272a",
                    }}
                  >
                    <div
                      style={{
                        color: "#a1a1aa",
                      }}
                    >
                      {eventSymbol(event)}
                    </div>

                    <div>
                      <div
                        style={{
                          fontSize: "14px",
                        }}
                      >
                        {formatEvent(event)}
                      </div>

                      {event.created_at && (
                        <div
                          style={{
                            marginTop: "4px",

                            color: "#71717a",

                            fontSize: "11px",
                          }}
                        >
                          {formatDate(event.created_at)}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* STRUCTURED DIAGNOSIS */}

          {diagnosis && (
            <section
              style={{
                marginTop: "32px",
              }}
            >
              {/* SUMMARY */}

              <div
                style={{
                  padding: "24px",

                  background: "#18181b",

                  border: "1px solid #27272a",

                  borderRadius: "12px",
                }}
              >
                <div
                  style={{
                    display: "flex",

                    justifyContent: "space-between",

                    alignItems: "center",

                    gap: "20px",

                    flexWrap: "wrap",
                  }}
                >
                  <div>
                    <div
                      style={{
                        color: "#71717a",

                        fontSize: "12px",

                        textTransform: "uppercase",

                        letterSpacing: "0.08em",
                      }}
                    >
                      Diagnosis
                    </div>

                    <h2
                      style={{
                        margin: "8px 0 4px",
                      }}
                    >
                      {diagnosis.summary.headline}
                    </h2>

                    <div
                      style={{
                        color: "#a1a1aa",

                        fontSize: "13px",
                      }}
                    >
                      {diagnosis.summary.total_issues} issue
                      {diagnosis.summary.total_issues === 1 ? "" : "s"} detected
                    </div>
                  </div>

                  <div
                    style={{
                      display: "flex",

                      gap: "10px",

                      flexWrap: "wrap",
                    }}
                  >
                    {diagnosis.summary.critical > 0 && (
                      <Badge
                        text={`${diagnosis.summary.critical} Critical`}
                        type="critical"
                      />
                    )}

                    {diagnosis.summary.warnings > 0 && (
                      <Badge
                        text={`${diagnosis.summary.warnings} Warning`}
                        type="warning"
                      />
                    )}

                    {diagnosis.summary.healthy > 0 && (
                      <Badge
                        text={`${diagnosis.summary.healthy} Healthy`}
                        type="healthy"
                      />
                    )}
                  </div>
                </div>
              </div>

              {/* TABLE */}

              {diagnosis.issues.length > 0 && (
                <div
                  style={{
                    marginTop: "18px",

                    overflowX: "auto",

                    background: "#18181b",

                    border: "1px solid #27272a",

                    borderRadius: "12px",
                  }}
                >
                  <table
                    style={{
                      width: "100%",

                      borderCollapse: "collapse",

                      minWidth: "850px",
                    }}
                  >
                    <thead>
                      <tr>
                        <TableHeader>Resource</TableHeader>

                        <TableHeader>Type</TableHeader>

                        <TableHeader>Status</TableHeader>

                        <TableHeader>Problem</TableHeader>

                        <TableHeader>Severity</TableHeader>
                      </tr>
                    </thead>

                    <tbody>
                      {diagnosis.issues.map((issue, index) => (
                        <tr
                          key={`${issue.resource}-${index}`}
                          style={{
                            borderTop: "1px solid #27272a",
                          }}
                        >
                          <TableCell>
                            <strong>{issue.resource}</strong>
                          </TableCell>

                          <TableCell>{issue.resource_type}</TableCell>

                          <TableCell>{formatStatus(issue.status)}</TableCell>

                          <TableCell>{issue.problem}</TableCell>

                          <TableCell>
                            <SeverityBadge severity={issue.severity} />
                          </TableCell>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* DETAILS */}

              <div
                style={{
                  marginTop: "20px",

                  display: "grid",

                  gap: "16px",
                }}
              >
                {diagnosis.issues.map((issue, index) => (
                  <div
                    key={`details-${index}`}
                    style={{
                      padding: "22px",

                      background: "#18181b",

                      border: "1px solid #27272a",

                      borderRadius: "12px",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",

                        alignItems: "center",

                        justifyContent: "space-between",

                        gap: "12px",

                        flexWrap: "wrap",
                      }}
                    >
                      <div>
                        <div
                          style={{
                            color: "#71717a",

                            fontSize: "11px",

                            textTransform: "uppercase",

                            marginBottom: "5px",
                          }}
                        >
                          {issue.resource_type}
                        </div>

                        <h3
                          style={{
                            margin: 0,
                          }}
                        >
                          {issue.resource}
                        </h3>
                      </div>

                      <SeverityBadge severity={issue.severity} />
                    </div>

                    <InfoRow label="Problem" value={issue.problem} />

                    <InfoRow
                      label="Evidence"
                      value={issue.evidence}
                      monospace
                    />

                    <InfoRow label="Likely Cause" value={issue.likely_cause} />

                    <InfoRow
                      label="Recommended Next Step"
                      value={issue.recommendation}
                    />
                  </div>
                ))}
              </div>

              {/* NARRATIVE */}

              {diagnosis.narrative && (
                <div
                  style={{
                    marginTop: "20px",

                    padding: "24px",

                    background: "#111113",

                    border: "1px solid #27272a",

                    borderRadius: "12px",
                  }}
                >
                  <h3
                    style={{
                      marginTop: 0,
                    }}
                  >
                    Analysis
                  </h3>

                  <div
                    style={{
                      color: "#d4d4d8",

                      lineHeight: 1.7,

                      whiteSpace: "pre-wrap",
                    }}
                  >
                    {diagnosis.narrative}
                  </div>
                </div>
              )}
            </section>
          )}

          {/* OLD HISTORY FALLBACK */}

          {!diagnosis && result && (
            <section
              style={{
                marginTop: "32px",

                padding: "24px",

                background: "#18181b",

                border: "1px solid #27272a",

                borderRadius: "10px",
              }}
            >
              <h2
                style={{
                  marginTop: 0,
                }}
              >
                Diagnosis
              </h2>

              <pre
                style={{
                  margin: 0,

                  whiteSpace: "pre-wrap",

                  lineHeight: 1.65,

                  color: "#d4d4d8",

                  fontFamily: "inherit",

                  fontSize: "14px",
                }}
              >
                {result}
              </pre>
            </section>
          )}
        </section>
      </div>
    </main>
  );
}
