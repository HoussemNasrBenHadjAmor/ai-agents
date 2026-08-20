import type { InvestigationEvent } from "@/types/investigation";

export function formatDate(value?: string | null) {
  if (!value) {
    return "Unknown";
  }

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

export function formatDuration(seconds?: number | null) {
  if (typeof seconds !== "number" || Number.isNaN(seconds)) {
    return "Unknown";
  }

  if (seconds < 60) {
    return `${seconds.toFixed(seconds < 10 ? 1 : 0)}s`;
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);

  return `${minutes}m ${remainingSeconds}s`;
}

export function formatCost(value?: number) {
  if (typeof value !== "number") {
    return "$0.000000";
  }

  return `$${value.toFixed(6)}`;
}

export function formatStatus(status: string) {
  const lower = status.toLowerCase();

  if (lower.includes("restart")) {
    return `Restarting: ${status}`;
  }

  if (lower.includes("healthy")) {
    return status;
  }

  if (lower.includes("exit")) {
    return `Exited: ${status}`;
  }

  if (lower.includes("running")) {
    return status;
  }

  return status;
}

export function formatEvent(event: InvestigationEvent) {
  switch (event.type) {
    case "investigation_started":
      return "Investigation started";
    case "specialist_selected":
      return `${event.agent ?? "Specialist"} selected`;
    case "agent_started":
      return `${event.agent ?? "Agent"} started`;
    case "tool_started":
      return `Running ${event.tool ?? "tool"}`;
    case "tool_completed":
      return `${event.tool ?? "Tool"} completed`;
    case "agent_completed":
      return `${event.agent ?? "Agent"} completed`;
    case "synthesizing":
      return "Synthesizing diagnosis";
    case "investigation_completed":
      return "Investigation completed";
    default:
      return event.message ?? event.type;
  }
}

export function eventTone(type: string) {
  if (type === "tool_started" || type === "agent_started" || type === "synthesizing") {
    return "active";
  }

  if (type === "tool_completed" || type === "agent_completed" || type === "investigation_completed") {
    return "complete";
  }

  if (type === "specialist_selected") {
    return "selected";
  }

  return "neutral";
}

