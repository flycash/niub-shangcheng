import { NextResponse } from "next/server";

const mallServiceUrl =
  process.env.MALL_SERVICE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8001";

export async function GET() {
  try {
    const response = await fetch(`${mallServiceUrl}/api/products`, {
      cache: "no-store",
    });
    const body: unknown = await response.json();
    return NextResponse.json(body, { status: response.status });
  } catch {
    return NextResponse.json(
      { detail: "商城服务暂时不可用" },
      { status: 502 },
    );
  }
}
