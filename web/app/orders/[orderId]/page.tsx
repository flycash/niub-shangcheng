import type { Metadata } from "next";

import { OrderPreview } from "@/components/order-preview";

export const metadata: Metadata = {
  title: "订单预览 · 牛掰商城",
  description: "确认商品并完成订单支付",
};

export default async function OrderPage({
  params,
}: {
  params: Promise<{ orderId: string }>;
}) {
  const { orderId } = await params;
  return <OrderPreview orderId={orderId} />;
}
