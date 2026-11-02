import { NextResponse } from "next/server";

const mallServiceUrl =
  process.env.MALL_SERVICE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8001";
const demoUserId = process.env.DEMO_USER_ID ?? "1";

export const dynamic = "force-dynamic";

export async function GET(
  _request: Request,
  context: { params: Promise<{ orderId: string }> },
) {
  const { orderId } = await context.params;
  try {
    const response = await fetch(
      `${mallServiceUrl}/api/users/${demoUserId}/orders/${encodeURIComponent(orderId)}`,
      { cache: "no-store" },
    );
    const body: unknown = await response.json();
    return NextResponse.json(body, { status: response.status });
  } catch {
    return NextResponse.json(
      { detail: "订单服务暂时不可用" },
      { status: 502 },
    );
  }
}
