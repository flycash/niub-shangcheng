import { NextResponse } from "next/server";

const agentServiceUrl =
  process.env.AGENT_SERVICE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8002";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const response = await fetch(`${agentServiceUrl}/api/conversations`, {
      cache: "no-store",
    });
    const body: unknown = await response.json();
    return NextResponse.json(body, { status: response.status });
  } catch {
    return NextResponse.json(
      { detail: "历史对话服务暂时不可用" },
      { status: 502 },
    );
  }
}
