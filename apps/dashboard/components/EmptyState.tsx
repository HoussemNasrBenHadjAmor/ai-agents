export function EmptyState({
  title,
  message,
}: {
  title: string;
  message: string;
}) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon" aria-hidden="true">
        +
      </div>
      <h3>{title}</h3>
      <p>{message}</p>
    </div>
  );
}

export function LoadingState({ label }: { label: string }) {
  return (
    <div className="loading-state" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      {label}
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <section className="error-state" role="alert">
      <strong>Investigation error</strong>
      <p>{message}</p>
    </section>
  );
}

