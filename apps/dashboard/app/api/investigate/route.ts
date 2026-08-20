import { NextRequest } from "next/server";

const API_URL = process.env.AGENT_API_URL ?? "http://host.docker.internal:8000";

export async function POST(request: NextRequest) {
  const body = await request.text();

  try {
    const response = await fetch(`${API_URL}/investigate/stream`, {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body,

      cache: "no-store",
    });

    if (!response.body) {
      return new Response(
        JSON.stringify({
          error: "No response stream",
        }),
        {
          status: 500,
          headers: {
            "Content-Type": "application/json",
          },
        },
      );
    }

    return new Response(response.body, {
      status: response.status,

      headers: {
        "Content-Type": "text/event-stream",

        "Cache-Control": "no-cache",

        Connection: "keep-alive",

        "X-Accel-Buffering": "no",
      },
    });
  } catch (error) {
    return new Response(
      JSON.stringify({
        error: "Unable to contact Agent API",
      }),
      {
        status: 500,
        headers: {
          "Content-Type": "application/json",
        },
      },
    );
  }
}
