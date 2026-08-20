"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { DashboardShell, Header } from "@/components/DashboardShell";
import { InvestigationForm } from "@/components/InvestigationForm";
import { InvestigationDetail } from "@/components/InvestigationDetail";
import type {
  Diagnosis,
  InvestigationEvent,
  InvestigationMetrics as Metrics,
} from "@/types/investigation";

export default function Home() {
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [result, setResult] = useState("");
  const [diagnosis, setDiagnosis] = useState<Diagnosis | null>(null);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [events, setEvents] = useState<InvestigationEvent[]>([]);
  const [selectedPrompt, setSelectedPrompt] = useState("");

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
    setSelectedPrompt(message);

    try {
      let createdInvestigationId: string | null = null;

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
              createdInvestigationId = event.investigation_id;
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

      window.dispatchEvent(new Event("investigation-history-refresh"));

      if (createdInvestigationId) {
        router.push(`/investigation/${createdInvestigationId}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Investigation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <DashboardShell>
      <Header
        isRunning={loading}
        title="AI DevOps Agent"
        subtitle="What do you want to investigate?"
      />

      <div className="dashboard-content">
        <InvestigationForm
          message={message}
          loading={loading}
          onMessageChange={setMessage}
          onSubmit={investigate}
        />

        {(selectedPrompt || loading || result || diagnosis || events.length > 0) && (
          <InvestigationDetail
            prompt={selectedPrompt}
            events={events}
            metrics={metrics}
            diagnosis={diagnosis}
            result={result}
            error={error}
            loading={loading}
          />
        )}
      </div>
    </DashboardShell>
  );
}
