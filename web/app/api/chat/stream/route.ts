import { NextRequest, NextResponse } from "next/server";

const agentServiceUrl =
  process.env.AGENT_SERVICE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8002";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  let conversationId: unknown;
  let message: unknown;
  try {
    const body = (await request.json()) as {
      conversation_id?: unknown;
      message?: unknown;
    };
    conversationId = body.conversation_id;
    message = body.message;
  } catch {
    return NextResponse.json({ detail: "请求格式无效" }, { status: 400 });
  }

  if (typeof message !== "string" || !message.trim()) {
    return NextResponse.json({ detail: "请输入消息" }, { status: 400 });
  }
  if (
    conversationId !== undefined &&
    conversationId !== null &&
    typeof conversationId !== "string"
  ) {
    return NextResponse.json({ detail: "对话 ID 无效" }, { status: 400 });
  }

  try {
    const response = await fetch(`${agentServiceUrl}/api/chat/stream`, {
      method: "POST",
      headers: {
        accept: "text/event-stream",
        "content-type": "application/json",
      },
      body: JSON.stringify({
        conversation_id: conversationId || null,
        message,
      }),
      cache: "no-store",
    });

    if (!response.ok || !response.body) {
      const body = (await response.json().catch(() => null)) as {
        detail?: string;
      } | null;
      return NextResponse.json(
        { detail: body?.detail ?? "Agent 流式服务暂时不可用" },
        { status: response.status || 502 },
      );
    }

    return new Response(response.body, {
      status: 200,
      headers: {
        "Cache-Control": "no-cache, no-transform",
        Connection: "keep-alive",
        "Content-Type": "text/event-stream; charset=utf-8",
        "X-Accel-Buffering": "no",
      },
    });
  } catch {
    return NextResponse.json(
      { detail: "Agent 流式服务暂时不可用" },
      { status: 502 },
    );
  }
}
