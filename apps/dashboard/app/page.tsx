"use client";

import { useEffect, useMemo, useState } from "react";
import { DashboardShell, Header } from "@/components/DashboardShell";
import { DiagnosisSummary } from "@/components/DiagnosisSummary";
import { ErrorState, LoadingState } from "@/components/EmptyState";
import { InvestigationForm } from "@/components/InvestigationForm";
import { InvestigationHistory } from "@/components/InvestigationHistory";
import { InvestigationMetrics } from "@/components/InvestigationMetrics";
import { InvestigationProgress } from "@/components/InvestigationProgress";
import type {
  Diagnosis,
  InvestigationDetail,
  InvestigationEvent,
  InvestigationMetrics as Metrics,
  InvestigationSummary as Summary,
} from "@/types/investigation";

export default function Home() {
  const [message, setMessage] = useState("");
  const [result, setResult] = useState("");
  const [diagnosis, setDiagnosis] = useState<Diagnosis | null>(null);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [events, setEvents] = useState<InvestigationEvent[]>([]);
  const [history, setHistory] = useState<Summary[]>([]);
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
      setHistory(Array.isArray(data) ? data : []);
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
      setEvents(data.events ?? []);
      setResult(data.result ?? "");
      setDiagnosis(data.diagnosis ?? null);
      setMetrics(data.metrics ?? null);
      setError(data.error ?? "");
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
    setMetrics(null);
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
        body: JSON.stringify({ message }),
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

        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split("\n\n");
        buffer = chunks.pop() ?? "";

        for (const chunk of chunks) {
          if (!chunk.startsWith("data: ")) {
            continue;
          }

          const raw = chunk.slice(6);
          const event: InvestigationEvent & { investigation_id?: string } =
            JSON.parse(raw);

          if (event.type === "investigation_created") {
            if (event.investigation_id) {
              setSelectedInvestigationId(event.investigation_id);
            }
            continue;
          }

          if (event.type === "result") {
            setResult(event.result ?? "");
            setDiagnosis(event.diagnosis ?? null);
            setMetrics(event.metrics ?? null);
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

  const sidebar = useMemo(
    () => (
      <InvestigationHistory
        history={history}
        loading={historyLoading}
        selectedInvestigationId={selectedInvestigationId}
        onSelect={loadInvestigation}
      />
    ),
    [history, historyLoading, selectedInvestigationId],
  );

  const activeAgent = [...events]
    .reverse()
    .find((event) => event.agent && event.type !== "agent_completed")?.agent;

  const completedTools = events.filter(
    (event) => event.type === "tool_completed",
  ).length;

  return (
    <DashboardShell sidebar={sidebar}>
      <Header isRunning={loading} />

      <div className="dashboard-content">
        <InvestigationForm
          message={message}
          loading={loading}
          onMessageChange={setMessage}
          onSubmit={investigate}
        />

        {(selectedPrompt || activeAgent || completedTools > 0) && (
          <section className="status-strip" aria-label="Current investigation">
            <div>
              <span>Question</span>
              <strong>{selectedPrompt || "No investigation selected"}</strong>
            </div>
            <div>
              <span>Active agent</span>
              <strong>{activeAgent ?? (loading ? "Orchestrator" : "Idle")}</strong>
            </div>
            <div>
              <span>Tools completed</span>
              <strong>{completedTools}</strong>
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
    </DashboardShell>
  );
}

