"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import styles from "./order-preview.module.css";

type OrderStatus =
  | "pending_payment"
  | "paid"
  | "completed"
  | "cancelled"
  | "refunded";

type OrderItem = {
  product_id: string;
  name: string;
  image_url: string | null;
  quantity: number;
  unit_price_cents: number;
  subtotal_cents: number;
};

type Order = {
  order_id: string;
  user_id: number;
  status: OrderStatus;
  ordered_at: string;
  address: {
    recipient: string;
    phone_masked: string;
    region: string;
    detail: string;
  } | null;
  subtotal_cents: number;
  shipping_fee_cents: number;
  total_cents: number;
  items: OrderItem[];
  preview_path: string | null;
  paid_at: string | null;
};

const statusLabels: Record<OrderStatus, string> = {
  pending_payment: "待支付",
  paid: "已支付",
  completed: "已完成",
  cancelled: "已取消",
  refunded: "已退款",
};

const priceFormatter = new Intl.NumberFormat("zh-CN", {
  style: "currency",
  currency: "CNY",
});

function formatTime(value: string | null) {
  if (!value) {
    return "—";
  }
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function OrderPreview({ orderId }: { orderId: string }) {
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadOrder() {
      try {
        const response = await fetch(`/api/orders/${encodeURIComponent(orderId)}`, {
          cache: "no-store",
        });
        const body = (await response.json()) as Order | { detail?: string };
        if (!response.ok) {
          throw new Error(
            "detail" in body && body.detail
              ? body.detail
              : "订单读取失败",
          );
        }
        if (!cancelled) {
          setOrder(body as Order);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error ? loadError.message : "订单读取失败",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadOrder();
    return () => {
      cancelled = true;
    };
  }, [orderId]);

  async function payOrder() {
    if (!order || order.status !== "pending_payment") {
      return;
    }
    setPaying(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/orders/${encodeURIComponent(order.order_id)}/pay`,
        { method: "POST" },
      );
      const body = (await response.json()) as Order | { detail?: string };
      if (!response.ok) {
        throw new Error(
          "detail" in body && body.detail ? body.detail : "支付失败",
        );
      }
      setOrder(body as Order);
    } catch (payError) {
      setError(
        payError instanceof Error ? payError.message : "支付失败，请稍后重试",
      );
    } finally {
      setPaying(false);
    }
  }

  return (
    <main className={styles.page}>
      <header className={styles.topbar}>
        <Link className={styles.brand} href="/">
          牛掰<span>商店</span>
        </Link>
        <Link className={styles.backLink} href="/chat">
          返回导购对话
        </Link>
      </header>

      <section className={styles.sheet}>
        {loading ? (
          <p className={styles.stateText}>正在读取订单…</p>
        ) : error && !order ? (
          <div className={styles.errorState}>
            <h1>无法打开订单</h1>
            <p>{error}</p>
            <Link href="/chat">返回对话</Link>
          </div>
        ) : order ? (
          <>
            <header className={styles.heading}>
              <div>
                <p>ORDER PREVIEW</p>
                <h1>确认订单</h1>
                <span>订单号 {order.order_id}</span>
              </div>
              <b
                className={
                  order.status === "pending_payment"
                    ? styles.pending
                    : styles.paid
                }
              >
                {statusLabels[order.status]}
              </b>
            </header>

            {order.status === "paid" ? (
              <div className={styles.paidNotice} role="status">
                <strong>支付成功</strong>
                <span>订单已于 {formatTime(order.paid_at)} 完成支付。</span>
              </div>
            ) : null}

            <div className={styles.contentGrid}>
              <section className={styles.items}>
                <h2>商品明细</h2>
                {order.items.map((item) => (
                  <article className={styles.item} key={item.product_id}>
                    <div className={styles.itemMark}>
                      {item.name.slice(0, 1)}
                    </div>
                    <div>
                      <strong>{item.name}</strong>
                      <span>
                        {priceFormatter.format(item.unit_price_cents / 100)} ×{" "}
                        {item.quantity}
                      </span>
                    </div>
                    <b>
                      {priceFormatter.format(item.subtotal_cents / 100)}
                    </b>
                  </article>
                ))}
              </section>

              <aside className={styles.summary}>
                <h2>收货信息</h2>
                {order.address ? (
                  <div className={styles.address}>
                    <strong>
                      {order.address.recipient} · {order.address.phone_masked}
                    </strong>
                    <span>
                      {order.address.region} {order.address.detail}
                    </span>
                  </div>
                ) : (
                  <p>暂无收货地址</p>
                )}

                <dl>
                  <div>
                    <dt>商品金额</dt>
                    <dd>
                      {priceFormatter.format(order.subtotal_cents / 100)}
                    </dd>
                  </div>
                  <div>
                    <dt>运费</dt>
                    <dd>
                      {priceFormatter.format(order.shipping_fee_cents / 100)}
                    </dd>
                  </div>
                  <div className={styles.total}>
                    <dt>应付总额</dt>
                    <dd>
                      {priceFormatter.format(order.total_cents / 100)}
                    </dd>
                  </div>
                </dl>

                {error ? (
                  <p className={styles.error} role="alert">
                    {error}
                  </p>
                ) : null}

                <button
                  className={styles.payButton}
                  type="button"
                  disabled={order.status !== "pending_payment" || paying}
                  onClick={() => void payOrder()}
                >
                  {order.status === "paid"
                    ? "订单已支付"
                    : order.status !== "pending_payment"
                      ? statusLabels[order.status]
                    : paying
                      ? "正在支付…"
                      : "模拟支付"}
                </button>
                <p className={styles.hint}>
                  当前为 Mock 支付，不会产生真实扣款。
                </p>
              </aside>
            </div>
          </>
        ) : null}
      </section>
    </main>
  );
}
