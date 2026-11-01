"use client";

import { FormEvent, useEffect, useState } from "react";

type Product = {
  id: string;
  name: string;
  description: string;
  price_cents: number;
  category: string;
  badge: string | null;
};

type Message = {
  role: "user" | "agent";
  content: string;
};

const money = new Intl.NumberFormat("zh-CN", {
  style: "currency",
  currency: "CNY",
});

const productMarks = ["01", "02", "03"];

export function Storefront() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "agent",
      content: "你好，我是小牛。想找点好喝的、好用的，还是送给朋友？",
    },
  ]);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    const controller = new AbortController();

    fetch("/api/products", { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error("商品加载失败");
        }
        return (await response.json()) as { items: Product[] };
      })
      .then((data) => setProducts(data.items))
      .catch((error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          setLoadError("商城服务暂未连接");
        }
      })
      .finally(() => setLoading(false));

    return () => controller.abort();
  }, []);

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = message.trim();
    if (!text || sending) {
      return;
    }

    setMessages((current) => [...current, { role: "user", content: text }]);
    setMessage("");
    setSending(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = (await response.json()) as {
        reply?: string;
        detail?: string;
      };

      if (!response.ok || !data.reply) {
        throw new Error(data.detail ?? "导购暂时没有回应");
      }
      setMessages((current) => [
        ...current,
        { role: "agent", content: data.reply as string },
      ]);
    } catch (error) {
      const detail = error instanceof Error ? error.message : "导购暂时没有回应";
      setMessages((current) => [
        ...current,
        { role: "agent", content: detail },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <main>
      <nav className="nav-shell">
        <a className="brand" href="#">
          牛掰<span>商店</span>
        </a>
        <div className="nav-links">
          <a href="#goods">今日好物</a>
          <a href="/chat">问问小牛</a>
        </div>
        <button className="bag-button" type="button" aria-label="购物袋">
          购物袋 <span>0</span>
        </button>
      </nav>

      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">NICE THINGS, EVERY DAY</p>
          <h1>
            给普通日子，
            <br />
            加一点<span>新意思。</span>
          </h1>
          <p className="hero-description">
            从一口清凉到一盏暖光，认真挑选那些让生活变好的小东西。
          </p>
          <a className="primary-link" href="#goods">
            逛逛今日好物
          </a>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="sun" />
          <div className="object object-one">牛</div>
          <div className="object object-two" />
          <p>
            GOOD STUFF
            <br />
            FOR SLOW DAYS
          </p>
        </div>
      </section>

      <section className="goods-section" id="goods">
        <div className="section-heading">
          <div>
            <p className="eyebrow">FRESHLY PICKED</p>
            <h2>今日好物</h2>
          </div>
          <p>每一件都经过认真挑选</p>
        </div>

        {loadError ? <p className="status-card">{loadError}</p> : null}
        {loading ? <p className="status-card">正在搬来好物…</p> : null}

        {!loading && !loadError ? (
          <div className="product-grid">
            {products.map((product, index) => (
              <article className="product-card" key={product.id}>
                <div className={`product-visual visual-${index + 1}`}>
                  {product.badge ? (
                    <span className="product-badge">{product.badge}</span>
                  ) : null}
                  <span className="product-number">
                    {productMarks[index] ?? "00"}
                  </span>
                  <span className="product-shape" aria-hidden="true">
                    {product.name.slice(0, 1)}
                  </span>
                </div>
                <div className="product-meta">
                  <p>{product.category}</p>
                  <h3>{product.name}</h3>
                  <span>{money.format(product.price_cents / 100)}</span>
                </div>
                <p className="product-description">{product.description}</p>
                <button className="product-action" type="button">
                  加入购物袋
                  <span>＋</span>
                </button>
              </article>
            ))}
          </div>
        ) : null}
      </section>

      <section className="guide-section" id="guide">
        <div className="guide-intro">
          <p className="eyebrow">PERSONAL SHOPPER</p>
          <h2>
            不知道怎么选？
            <br />
            问问<span>小牛。</span>
          </h2>
          <p>
            Agent 会读取商城当前商品，帮你快速缩小选择范围。
            当前为可运行的基础导购，后续可接入真实模型。
          </p>
          <div className="agent-status">
            <span />
            Agent 服务在线
          </div>
          <a className="chat-entry" href="/chat">
            打开完整对话页 <span>↗</span>
          </a>
        </div>

        <div className="chat-panel">
          <div className="chat-heading">
            <div className="avatar">牛</div>
            <div>
              <strong>小牛导购</strong>
              <p>通常立刻回复</p>
            </div>
          </div>
          <div className="messages" aria-live="polite">
            {messages.map((item, index) => (
              <p
                className={`message ${item.role}`}
                key={`${item.role}-${index}`}
              >
                {item.content}
              </p>
            ))}
            {sending ? <p className="message agent">正在看看商城…</p> : null}
          </div>
          <form className="chat-form" onSubmit={sendMessage}>
            <label className="sr-only" htmlFor="agent-message">
              输入消息
            </label>
            <input
              id="agent-message"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="例如：推荐一件居家好物"
              maxLength={2000}
            />
            <button type="submit" disabled={sending || !message.trim()}>
              发送
            </button>
          </form>
        </div>
      </section>

      <footer>
        <span>牛掰商店</span>
        <p>把普通日子，过得有点意思。</p>
      </footer>
    </main>
  );
}
