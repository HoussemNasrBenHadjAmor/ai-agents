"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import { InvestigationHistory } from "@/components/InvestigationHistory";
import { ThemeToggle } from "@/components/ThemeToggle";
import type { InvestigationSummary as Summary } from "@/types/investigation";

export function DashboardShell({
  children,
}: {
  children: ReactNode;
}) {
  const pathname = usePathname();
  const [history, setHistory] = useState<Summary[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const selectedInvestigationId = useMemo(() => {
    const match = pathname.match(/^\/investigation\/([^/]+)/);
    return match?.[1] ?? null;
  }, [pathname]);

  useEffect(() => {
    const stored = window.localStorage.getItem("dashboard-sidebar-collapsed");
    setSidebarCollapsed(stored === "true");
  }, []);

  useEffect(() => {
    window.localStorage.setItem(
      "dashboard-sidebar-collapsed",
      String(sidebarCollapsed),
    );
  }, [sidebarCollapsed]);

  useEffect(() => {
    loadHistory();

    window.addEventListener("investigation-history-refresh", loadHistory);

    return () => {
      window.removeEventListener("investigation-history-refresh", loadHistory);
    };
  }, []);

  useEffect(() => {
    if (!drawerOpen) {
      return;
    }

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setDrawerOpen(false);
      }
    };

    document.body.classList.add("has-open-drawer");
    window.addEventListener("keydown", onKeyDown);

    return () => {
      document.body.classList.remove("has-open-drawer");
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [drawerOpen]);

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

  const renderHistoryNavigation = (closeOnNavigate = false) => (
    <InvestigationHistory
      history={history}
      loading={historyLoading}
      selectedInvestigationId={selectedInvestigationId}
      onNavigate={closeOnNavigate ? () => setDrawerOpen(false) : undefined}
    />
  );

  return (
    <main
      className={`dashboard-shell ${sidebarCollapsed ? "is-sidebar-collapsed" : ""}`}
    >
      <div className="sidebar-rail">
        <button
          type="button"
          className="icon-button"
          onClick={() => setSidebarCollapsed(false)}
          aria-label="Open history sidebar"
          title="Open history sidebar"
        >
          <span className="menu-icon" aria-hidden="true" />
        </button>
      </div>

      <aside className="dashboard-sidebar" aria-label="Investigation history">
        <div className="sidebar-actions">
          <Link className="new-investigation-link" href="/">
            New investigation
          </Link>
          <button
            type="button"
            className="icon-button"
            onClick={() => setSidebarCollapsed(true)}
            aria-label="Collapse history sidebar"
            title="Collapse history sidebar"
          >
            <span className="collapse-icon" aria-hidden="true" />
          </button>
        </div>
        {renderHistoryNavigation()}
      </aside>

      <button
        type="button"
        className="drawer-backdrop"
        onClick={() => setDrawerOpen(false)}
        aria-label="Close history sidebar"
        aria-hidden={!drawerOpen}
        tabIndex={drawerOpen ? 0 : -1}
      />
      <aside
        className={`mobile-drawer ${drawerOpen ? "is-open" : ""}`}
        aria-label="Investigation history"
        aria-hidden={!drawerOpen}
      >
        <div className="sidebar-actions">
          <Link
            className="new-investigation-link"
            href="/"
            onClick={() => setDrawerOpen(false)}
          >
            New investigation
          </Link>
          <button
            type="button"
            className="icon-button"
            onClick={() => setDrawerOpen(false)}
            aria-label="Close history sidebar"
            title="Close history sidebar"
          >
            <span className="close-icon" aria-hidden="true" />
          </button>
        </div>
        {renderHistoryNavigation(true)}
      </aside>

      <section className="dashboard-main">{children}</section>

      <button
        type="button"
        className="mobile-history-button"
        onClick={() => setDrawerOpen(true)}
        aria-label="Open history sidebar"
      >
        <span className="menu-icon" aria-hidden="true" />
        History
      </button>
    </main>
  );
}

export function Header({
  isRunning,
  title = "Infrastructure Investigations",
  subtitle = "Submit read-only diagnostics, watch specialist agents work, and review evidence-backed root cause analysis.",
}: {
  isRunning: boolean;
  title?: string;
  subtitle?: string;
}) {
  return (
    <header className="dashboard-header">
      <div>
        <p className="eyebrow">AI DevOps Console</p>
        <h1>{title}</h1>
        <p className="header-subtitle">{subtitle}</p>
      </div>
      <div className="header-actions">
        <Link className="new-investigation-link header-new-link" href="/">
          New investigation
        </Link>
        <div className={`live-pill ${isRunning ? "is-live" : ""}`}>
          <span aria-hidden="true" />
          {isRunning ? "Investigation running" : "Ready"}
        </div>
        <ThemeToggle />
      </div>
    </header>
  );
}
