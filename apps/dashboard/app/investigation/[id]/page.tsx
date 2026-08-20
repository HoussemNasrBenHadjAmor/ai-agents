"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { DashboardShell, Header } from "@/components/DashboardShell";
import { InvestigationDetail } from "@/components/InvestigationDetail";
import { ErrorState, LoadingState } from "@/components/EmptyState";
import type { InvestigationDetail as Detail } from "@/types/investigation";

export default function InvestigationPage() {
  const params = useParams<{ id: string }>();
  const [investigation, setInvestigation] = useState<Detail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadInvestigation() {
      setLoading(true);
      setError("");

      try {
        const response = await fetch(`/api/investigations/${params.id}`, {
          cache: "no-store",
        });

        if (!response.ok) {
          throw new Error(`Investigation request failed: ${response.status}`);
        }

        const data: Detail = await response.json();
        setInvestigation(data);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Unable to load investigation",
        );
      } finally {
        setLoading(false);
      }
    }

    loadInvestigation();
  }, [params.id]);

  return (
    <DashboardShell>
      <Header
        isRunning={investigation?.status === "running"}
        title="Investigation"
        subtitle="Saved investigation details loaded from history."
      />

      {loading && <LoadingState label="Loading investigation" />}
      {error && <ErrorState message={error} />}
      {investigation && (
        <InvestigationDetail
          saved
          prompt={investigation.message}
          status={investigation.status}
          createdAt={investigation.created_at}
          completedAt={investigation.completed_at}
          events={investigation.events ?? []}
          metrics={investigation.metrics ?? null}
          diagnosis={investigation.diagnosis ?? null}
          result={investigation.result ?? ""}
          error={investigation.error}
          loading={false}
        />
      )}
    </DashboardShell>
  );
}
