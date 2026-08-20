import {
  NextRequest,
  NextResponse,
} from "next/server";


const API_URL =
  process.env.AGENT_API_URL ??
  "http://host.docker.internal:8000";


export async function GET(
  request: NextRequest,
  context: {
    params: Promise<{
      id: string;
    }>;
  }
) {

  const { id } =
    await context.params;

  try {

    const response = await fetch(
      `${API_URL}/investigations/${id}`,
      {
        cache: "no-store",
      }
    );

    const data =
      await response.json();

    return NextResponse.json(
      data,
      {
        status: response.status,
      }
    );

  } catch {

    return NextResponse.json(
      {
        error:
          "Unable to load investigation",
      },
      {
        status: 500,
      }
    );
  }
}
