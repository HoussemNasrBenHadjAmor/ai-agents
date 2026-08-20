"use client";

import { useState } from "react";

type InvestigationEvent = {
  type: string;
  agent?: string;
  tool?: string;
  message?: string;
  result?: string;
  arguments?: Record<string, unknown>;
};

export default function Home() {
  const [message, setMessage] = useState("");
  const [result, setResult] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [events, setEvents] = useState<InvestigationEvent[]>([]);

  async function investigate() {
    if (!message.trim()) {
      return;
    }

    setLoading(true);
    setResult("");
    setError("");
    setEvents([]);

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

          const event: InvestigationEvent = JSON.parse(raw);

          if (event.type === "result") {
            setResult(event.result ?? "");

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
    } catch (error) {
      setError(error instanceof Error ? error.message : "Investigation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main
      style={{
        maxWidth: "900px",
        margin: "0 auto",
        padding: "60px 24px",
      }}
    >
      <h1 style={{ fontSize: "36px", marginBottom: "8px" }}>AI DevOps Agent</h1>

      <p
        style={{
          color: "#a1a1aa",
          marginBottom: "40px",
        }}
      >
        Read-only infrastructure investigation
      </p>

      <textarea
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        placeholder="Example: Why is my worker failing?"
        rows={6}
        style={{
          width: "100%",
          padding: "16px",
          background: "#18181b",
          color: "#f4f4f5",
          border: "1px solid #3f3f46",
          borderRadius: "8px",
          resize: "vertical",
        }}
      />

      <button
        onClick={investigate}
        disabled={loading}
        style={{
          marginTop: "16px",
          padding: "12px 22px",
          border: 0,
          borderRadius: "8px",
          cursor: loading ? "wait" : "pointer",
          fontWeight: 600,
        }}
      >
        {loading ? "Investigating..." : "Ask Agent"}
      </button>

      {error && (
        <div
          style={{
            marginTop: "30px",
            padding: "18px",
            border: "1px solid #7f1d1d",
            background: "#450a0a",
            borderRadius: "8px",
          }}
        >
          {error}
        </div>
      )}

      {events.length > 0 && (
        <section
          style={{
            marginTop: "40px",
            padding: "24px",
            background: "#18181b",
            border: "1px solid #27272a",
            borderRadius: "10px",
          }}
        >
          <h2>Investigation Progress</h2>

          <div
            style={{
              marginTop: "20px",
              display: "flex",
              flexDirection: "column",
              gap: "12px",
            }}
          >
            {events.map((event, index) => (
              <div
                key={index}
                style={{
                  paddingBottom: "10px",
                  borderBottom: "1px solid #27272a",
                }}
              >
                {event.type === "investigation_started" &&
                  "▶ Investigation started"}

                {event.type === "specialist_selected" &&
                  `✓ ${event.agent} Agent selected`}

                {event.type === "agent_started" &&
                  `→ ${event.agent} Agent started`}

                {event.type === "tool_started" && `→ Running ${event.tool}`}

                {event.type === "tool_completed" && `✓ ${event.tool} completed`}

                {event.type === "agent_completed" &&
                  `✓ ${event.agent} Agent completed`}

                {event.type === "synthesizing" && "→ Combining findings"}

                {event.type === "investigation_completed" &&
                  "✓ Investigation completed"}
              </div>
            ))}
          </div>
        </section>
      )}

      {result && (
        <section
          style={{
            marginTop: "40px",
            padding: "24px",
            background: "#18181b",
            border: "1px solid #27272a",
            borderRadius: "10px",
          }}
        >
          <h2>Investigation Result</h2>

          <pre
            style={{
              whiteSpace: "pre-wrap",
              lineHeight: 1.6,
              color: "#d4d4d8",
              fontFamily: "inherit",
            }}
          >
            {result}
          </pre>
        </section>
      )}
    </main>
  );
}
