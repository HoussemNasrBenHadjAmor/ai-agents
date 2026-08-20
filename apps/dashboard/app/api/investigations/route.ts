import { NextResponse } from "next/server";

const API_URL = process.env.AGENT_API_URL ?? "http://host.docker.internal:8000";

export async function GET() {
  try {
    const response = await fetch(`${API_URL}/investigations`, {
      cache: "no-store",
    });

    const data = await response.json();

    return NextResponse.json(data, {
      status: response.status,
    });
  } catch {
    return NextResponse.json(
      {
        error: "Unable to load investigation history",
      },
      {
        status: 500,
      },
    );
  }
}
