import { NextRequest, NextResponse } from "next/server";

const agentServiceUrl =
  process.env.AGENT_SERVICE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8002";

export async function POST(request: NextRequest) {
  let message: unknown;
  try {
    const body = (await request.json()) as { message?: unknown };
    message = body.message;
  } catch {
    return NextResponse.json({ detail: "请求格式无效" }, { status: 400 });
  }

  if (typeof message !== "string" || !message.trim()) {
    return NextResponse.json({ detail: "请输入消息" }, { status: 400 });
  }

  try {
    const response = await fetch(`${agentServiceUrl}/api/chat`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ message }),
      cache: "no-store",
    });
    const body: unknown = await response.json();
    return NextResponse.json(body, { status: response.status });
  } catch {
    return NextResponse.json(
      { detail: "Agent 服务暂时不可用" },
      { status: 502 },
    );
  }
}
