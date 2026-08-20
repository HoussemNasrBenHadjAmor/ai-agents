import type { ReactNode } from "react";
import { ThemeToggle } from "@/components/ThemeToggle";

export function DashboardShell({
  sidebar,
  children,
}: {
  sidebar: ReactNode;
  children: ReactNode;
}) {
  return (
    <main className="dashboard-shell">
      <div className="mobile-history">{sidebar}</div>
      <aside className="dashboard-sidebar">{sidebar}</aside>
      <section className="dashboard-main">{children}</section>
    </main>
  );
}

export function Header({ isRunning }: { isRunning: boolean }) {
  return (
    <header className="dashboard-header">
      <div>
        <p className="eyebrow">AI DevOps Console</p>
        <h1>Infrastructure Investigations</h1>
        <p className="header-subtitle">
          Submit read-only diagnostics, watch specialist agents work, and review
          evidence-backed root cause analysis.
        </p>
      </div>
      <div className="header-actions">
        <div className={`live-pill ${isRunning ? "is-live" : ""}`}>
          <span aria-hidden="true" />
          {isRunning ? "Investigation running" : "Ready"}
        </div>
        <ThemeToggle />
      </div>
    </header>
  );
}
