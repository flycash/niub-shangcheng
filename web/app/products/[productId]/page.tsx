import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import styles from "./product-detail.module.css";

const mallServiceUrl =
  process.env.MALL_SERVICE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8001";

type Product = {
  id: string;
  name: string;
  description: string;
  price_cents: number;
  category: string;
  badge: string | null;
  stock: number | null;
  tags: string[];
};

export const dynamic = "force-dynamic";

async function getProduct(productId: string): Promise<Product | null> {
  const response = await fetch(
    `${mallServiceUrl}/api/products/${encodeURIComponent(productId)}`,
    { cache: "no-store" },
  );
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error("商品服务暂时不可用");
  }
  return (await response.json()) as Product;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ productId: string }>;
}): Promise<Metadata> {
  const { productId } = await params;
  const product = await getProduct(productId);
  return {
    title: product
      ? `${product.name} · 牛掰商城`
      : "商品不存在 · 牛掰商城",
  };
}

export default async function ProductDetailPage({
  params,
}: {
  params: Promise<{ productId: string }>;
}) {
  const { productId } = await params;
  const product = await getProduct(productId);
  if (!product) {
    notFound();
  }

  return (
    <main className={styles.page}>
      <div className={styles.shell}>
        <Link className={styles.back} href="/chat">
          ← 返回对话
        </Link>
        <section className={styles.product}>
          <div className={styles.visual} aria-hidden="true">
            <span>{product.name.slice(0, 1)}</span>
            <small>{product.category}</small>
          </div>
          <div className={styles.content}>
            <div className={styles.topline}>
              <span>{product.category}</span>
              {product.badge ? <b>{product.badge}</b> : null}
            </div>
            <h1>{product.name}</h1>
            <p className={styles.description}>{product.description}</p>
            <strong className={styles.price}>
              ¥{(product.price_cents / 100).toFixed(2)}
            </strong>
            <p className={styles.stock}>
              {product.stock && product.stock > 0
                ? `库存 ${product.stock}`
                : "暂时缺货"}
            </p>
            <div className={styles.tags}>
              {product.tags.map((tag) => (
                <span key={tag}>{tag}</span>
              ))}
            </div>
            <button className={styles.action} type="button">
              加入购物袋
              <span>＋</span>
            </button>
          </div>
        </section>
      </div>
    </main>
  );
}
