"use client";

const examples = [
  "Find unhealthy Docker containers and explain the likely cause.",
  "Investigate database connectivity issues from the running services.",
];

export function InvestigationForm({
  message,
  loading,
  onMessageChange,
  onSubmit,
}: {
  message: string;
  loading: boolean;
  onMessageChange: (value: string) => void;
  onSubmit: () => void;
}) {
  return (
    <section className="panel investigation-form-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">New investigation</p>
          <h2>What should the agents inspect?</h2>
        </div>
      </div>
      <label className="sr-only" htmlFor="investigation-message">
        Investigation prompt
      </label>
      <textarea
        id="investigation-message"
        value={message}
        onChange={(event) => onMessageChange(event.target.value)}
        placeholder="Example: List any unhealthy Docker containers, explain supporting evidence, and recommend the next read-only step."
        rows={5}
        disabled={loading}
      />
      <div className="form-footer">
        <div className="prompt-suggestions" aria-label="Example prompts">
          {examples.map((example) => (
            <button
              type="button"
              className="suggestion-chip"
              key={example}
              onClick={() => onMessageChange(example)}
              disabled={loading}
            >
              {example}
            </button>
          ))}
        </div>
        <button
          type="button"
          className="primary-button"
          onClick={onSubmit}
          disabled={loading || !message.trim()}
        >
          <span className={loading ? "button-spinner" : "button-icon"} />
          {loading ? "Investigating" : "Start investigation"}
        </button>
      </div>
    </section>
  );
}

