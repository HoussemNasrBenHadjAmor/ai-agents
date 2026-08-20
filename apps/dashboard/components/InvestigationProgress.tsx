import { eventTone, formatDate, formatEvent } from "@/lib/format";
import type { InvestigationEvent } from "@/types/investigation";
import { EmptyState } from "@/components/EmptyState";

export function InvestigationProgress({
  events,
  loading,
}: {
  events: InvestigationEvent[];
  loading: boolean;
}) {
  if (events.length === 0) {
    return (
      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Live progress</p>
            <h2>Agent activity</h2>
          </div>
        </div>
        <EmptyState
          title="No activity yet"
          message="Start an investigation to see orchestrator, agent, and tool events."
        />
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Live progress</p>
          <h2>Agent activity</h2>
        </div>
        {loading && <span className="activity-indicator">Streaming</span>}
      </div>
      <ol className="timeline" aria-label="Investigation progress">
        {events.map((event, index) => (
          <ProgressEvent
            key={`${event.sequence ?? index}-${event.type}-${event.tool ?? ""}`}
            event={event}
            index={index}
            isLast={index === events.length - 1}
          />
        ))}
      </ol>
    </section>
  );
}

function ProgressEvent({
  event,
  index,
  isLast,
}: {
  event: InvestigationEvent;
  index: number;
  isLast: boolean;
}) {
  const tone = eventTone(event.type);

  return (
    <li className={`timeline-item tone-${tone} ${isLast ? "is-last" : ""}`}>
      <div className="timeline-marker" aria-hidden="true">
        {index + 1}
      </div>
      <div className="timeline-content">
        <div className="timeline-title">{formatEvent(event)}</div>
        <div className="timeline-meta">
          {event.agent && <span>{event.agent}</span>}
          {event.tool && <span>{event.tool}</span>}
          {event.created_at && <span>{formatDate(event.created_at)}</span>}
        </div>
        {event.message && event.message !== formatEvent(event) && (
          <p className="timeline-message">{event.message}</p>
        )}
      </div>
    </li>
  );
}

