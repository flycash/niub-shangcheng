"use client";

import Link from "next/link";
import {
  FormEvent,
  KeyboardEvent,
  useEffect,
  useRef,
  useState,
} from "react";

import styles from "./agent-chat.module.css";

type Role = "user" | "assistant";

type Message = {
  id: string;
  role: Role;
  content: string;
  streaming?: boolean;
  failed?: boolean;
  products?: Product[];
  toolTrace?: ToolTrace[];
};

type Product = {
  id: string;
  name: string;
  description: string;
  price_cents: number;
  category: string;
  badge: string | null;
  stock: number | null;
  tags: string[];
  image_url: string | null;
};

type ToolTrace = {
  call_id: string | null;
  tool: string;
  arguments: string;
  status: "started" | "completed" | "failed";
  summary: string | null;
};

type ConversationSummary = {
  id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
};

type ConversationDetail = ConversationSummary & {
  messages: Array<{
    id: string;
    role: Role;
    content: string;
    status: "streaming" | "completed" | "failed";
    created_at: string;
    recommendations: Product[];
    tool_trace: ToolTrace[];
  }>;
};

type StreamEvent = {
  type:
    | "conversation"
    | "start"
    | "delta"
    | "tool_started"
    | "tool_completed"
    | "recommendations"
    | "done"
    | "error";
  conversation_id?: string;
  title?: string;
  message_id?: string;
  content?: string;
  message?: string;
  call_id?: string | null;
  tool?: string;
  arguments?: string;
  products?: Product[];
  tool_trace?: ToolTrace[];
};

const starters = [
  "推荐一件居家好物",
  "帮我挑个通勤礼物",
  "今天有什么新品？",
];

function createId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function createWelcomeMessage(): Message {
  return {
    id: createId("welcome"),
    role: "assistant",
    content: "你好，我是小牛。今天想找点什么？",
  };
}

function toMessages(conversation: ConversationDetail): Message[] {
  return conversation.messages.map((message) => ({
    id: message.id,
    role: message.role,
    content:
      message.content ||
      (message.status === "failed" ? "这次回复没有生成内容。" : ""),
    streaming: message.status === "streaming",
    failed: message.status === "failed",
    products: message.recommendations,
    toolTrace: message.tool_trace,
  }));
}

const priceFormatter = new Intl.NumberFormat("zh-CN", {
  style: "currency",
  currency: "CNY",
});

function formatHistoryTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("zh-CN", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

async function consumeEventStream(
  response: Response,
  onEvent: (event: StreamEvent) => void,
) {
  if (!response.body) {
    throw new Error("浏览器没有收到流式响应");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });

      const frames = buffer.split(/\r?\n\r?\n/);
      buffer = frames.pop() ?? "";

      for (const frame of frames) {
        const data = frame
          .split(/\r?\n/)
          .filter((line) => line.startsWith("data:"))
          .map((line) => line.slice(5).trimStart())
          .join("\n");

        if (data) {
          onEvent(JSON.parse(data) as StreamEvent);
        }
      }

      if (done) {
        break;
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export function AgentChat() {
  const [messages, setMessages] = useState<Message[]>([
    createWelcomeMessage(),
  ]);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [conversationLoading, setConversationLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [error, setError] = useState("");
  const endRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  useEffect(() => {
    const controller = new AbortController();

    async function loadInitialHistory() {
      try {
        const response = await fetch("/api/conversations", {
          signal: controller.signal,
          cache: "no-store",
        });
        const body = (await response.json()) as {
          items?: ConversationSummary[];
          detail?: string;
        };
        if (!response.ok) {
          throw new Error(body.detail ?? "历史对话加载失败");
        }

        const items = body.items ?? [];
        setConversations(items);
        if (items[0]) {
          await openConversation(items[0].id, controller.signal);
        }
      } catch (loadError) {
        if (
          !(loadError instanceof DOMException && loadError.name === "AbortError")
        ) {
          setHistoryError(
            loadError instanceof Error
              ? loadError.message
              : "历史对话加载失败",
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setHistoryLoading(false);
        }
      }
    }

    void loadInitialHistory();
    return () => controller.abort();
  }, []);

  async function openConversation(
    id: string,
    signal?: AbortSignal,
  ) {
    if (sending) {
      return;
    }

    setConversationLoading(true);
    setError("");
    try {
      const response = await fetch(`/api/conversations/${encodeURIComponent(id)}`, {
        signal,
        cache: "no-store",
      });
      const body = (await response.json()) as ConversationDetail & {
        detail?: string;
      };
      if (!response.ok) {
        throw new Error(body.detail ?? "对话加载失败");
      }

      setConversationId(body.id);
      setMessages(toMessages(body));
      setDraft("");
    } catch (loadError) {
      if (!(loadError instanceof DOMException && loadError.name === "AbortError")) {
        setError(
          loadError instanceof Error ? loadError.message : "对话加载失败",
        );
      }
    } finally {
      setConversationLoading(false);
    }
  }

  async function refreshHistory() {
    try {
      const response = await fetch("/api/conversations", {
        cache: "no-store",
      });
      const body = (await response.json()) as {
        items?: ConversationSummary[];
        detail?: string;
      };
      if (!response.ok) {
        throw new Error(body.detail ?? "历史对话刷新失败");
      }
      setConversations(body.items ?? []);
      setHistoryError("");
    } catch (loadError) {
      setHistoryError(
        loadError instanceof Error ? loadError.message : "历史对话刷新失败",
      );
    }
  }

  function resetConversation() {
    if (sending) {
      return;
    }
    setMessages([createWelcomeMessage()]);
    setConversationId(null);
    setDraft("");
    setError("");
    setConversationLoading(false);
    textareaRef.current?.focus();
  }

  function chooseStarter(prompt: string) {
    setDraft(prompt);
    textareaRef.current?.focus();
  }

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = draft.trim();
    if (!content || sending || conversationLoading) {
      return;
    }

    const userMessage: Message = {
      id: createId("user"),
      role: "user",
      content,
    };
    const assistantId = createId("assistant");
    const assistantPlaceholder: Message = {
      id: assistantId,
      role: "assistant",
      content: "",
      streaming: true,
    };

    setMessages((current) => [
      ...current,
      userMessage,
      assistantPlaceholder,
    ]);
    setDraft("");
    setSending(true);
    setError("");

    try {
      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: {
          accept: "text/event-stream",
          "content-type": "application/json",
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          message: content,
        }),
      });

      if (!response.ok) {
        const body = (await response.json().catch(() => null)) as {
          detail?: string;
        } | null;
        throw new Error(body?.detail ?? "Agent 暂时没有回应");
      }

      await consumeEventStream(response, (streamEvent) => {
        if (streamEvent.type === "conversation") {
          setConversationId(streamEvent.conversation_id ?? null);
        }

        if (streamEvent.type === "error") {
          if (streamEvent.tool_trace) {
            setMessages((current) =>
              current.map((item) =>
                item.id === assistantId
                  ? { ...item, toolTrace: streamEvent.tool_trace }
                  : item,
              ),
            );
          }
          throw new Error(streamEvent.message ?? "大模型调用失败");
        }

        if (streamEvent.type === "tool_started" && streamEvent.tool) {
          setMessages((current) =>
            current.map((item) =>
              item.id === assistantId
                ? {
                    ...item,
                    toolTrace: [
                      ...(item.toolTrace ?? []),
                      {
                        call_id: streamEvent.call_id ?? null,
                        tool: streamEvent.tool as string,
                        arguments: streamEvent.arguments ?? "",
                        status: "started",
                        summary: null,
                      },
                    ],
                  }
                : item,
            ),
          );
        }

        if (streamEvent.type === "tool_completed") {
          setMessages((current) =>
            current.map((item) =>
              item.id === assistantId
                ? {
                    ...item,
                    toolTrace: (item.toolTrace ?? []).map((trace) =>
                      trace.call_id === streamEvent.call_id
                        ? { ...trace, status: "completed" as const }
                        : trace,
                    ),
                  }
                : item,
            ),
          );
        }

        if (streamEvent.type === "recommendations" && streamEvent.products) {
          setMessages((current) =>
            current.map((item) =>
              item.id === assistantId
                ? { ...item, products: streamEvent.products }
                : item,
            ),
          );
        }

        if (streamEvent.type === "delta" && streamEvent.content) {
          setMessages((current) =>
            current.map((item) =>
              item.id === assistantId
                ? {
                    ...item,
                    content: `${item.content}${streamEvent.content}`,
                  }
                : item,
            ),
          );
        }

        if (streamEvent.type === "done") {
          setMessages((current) =>
            current.map((item) =>
              item.id === assistantId
                ? {
                    ...item,
                    streaming: false,
                    toolTrace: streamEvent.tool_trace ?? item.toolTrace,
                  }
                : item,
            ),
          );
        }
      });
    } catch (streamError) {
      const messageText =
        streamError instanceof Error ? streamError.message : "对话连接已中断";
      setError(messageText);
      setMessages((current) =>
        current.map((item) =>
          item.id === assistantId
            ? {
                ...item,
                content: item.content || messageText,
                streaming: false,
                failed: true,
              }
            : item,
        ),
      );
    } finally {
      setSending(false);
      await refreshHistory();
      textareaRef.current?.focus();
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (
      event.key === "Enter" &&
      !event.shiftKey &&
      !event.nativeEvent.isComposing
    ) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  const activeConversation = conversations.find(
    (item) => item.id === conversationId,
  );

  return (
    <main className={styles.page}>
      <header className={styles.topbar}>
        <Link className={styles.brand} href="/">
          牛掰<span>商店</span>
        </Link>
        <div className={styles.topbarActions}>
          <span className={styles.connection}>
            <i />
            SQLITE PERSISTENCE
          </span>
          <Link className={styles.backLink} href="/">
            返回商城
          </Link>
        </div>
      </header>

      <div className={styles.workspace}>
        <aside className={styles.sidebar}>
          <div className={styles.sidebarHeading}>
            <p className={styles.kicker}>YOUR PERSONAL SHOPPER</p>
            <h1>
              和小牛
              <br />
              聊一聊。
            </h1>
          </div>

          <section className={styles.history}>
            <div className={styles.historyHeading}>
              <p>历史对话</p>
              <span>{conversations.length}</span>
            </div>

            {historyLoading ? (
              <p className={styles.historyEmpty}>正在读取历史…</p>
            ) : null}
            {historyError ? (
              <p className={styles.historyError}>{historyError}</p>
            ) : null}
            {!historyLoading && !historyError && conversations.length === 0 ? (
              <p className={styles.historyEmpty}>还没有保存过对话</p>
            ) : null}

            <div className={styles.historyList}>
              {conversations.map((conversation) => (
                <button
                  className={`${styles.historyItem} ${
                    conversation.id === conversationId
                      ? styles.historyItemActive
                      : ""
                  }`}
                  type="button"
                  key={conversation.id}
                  onClick={() => void openConversation(conversation.id)}
                  disabled={sending || conversationLoading}
                >
                  <strong>{conversation.title}</strong>
                  <span>
                    {formatHistoryTime(conversation.updated_at)}
                    <b>{conversation.message_count} 条</b>
                  </span>
                </button>
              ))}
            </div>
          </section>

          <div className={styles.starters}>
            <p>可以这样开始</p>
            {starters.map((starter) => (
              <button
                type="button"
                key={starter}
                onClick={() => chooseStarter(starter)}
                disabled={sending || conversationLoading}
              >
                {starter}
                <span>↗</span>
              </button>
            ))}
          </div>
        </aside>

        <section className={styles.chatArea}>
          <header className={styles.chatHeader}>
            <div className={styles.agentIdentity}>
              <div className={styles.avatar}>牛</div>
              <div>
                <strong>{activeConversation?.title ?? "新对话"}</strong>
                <p>
                  {sending
                    ? "正在组织回复…"
                    : conversationLoading
                      ? "正在读取历史…"
                      : "在线 · 大模型流式回复"}
                </p>
              </div>
            </div>
            <button
              className={styles.newChat}
              type="button"
              onClick={resetConversation}
              disabled={sending || conversationLoading}
            >
              ＋ 新对话
            </button>
          </header>

          <div
            className={styles.messages}
            role="log"
            aria-live="polite"
            aria-label="Agent 对话记录"
          >
            <div className={styles.dayDivider}>
              <span>{activeConversation ? "已保存的对话" : "今天"}</span>
            </div>

            {messages.map((item) => (
              <article
                className={`${styles.messageRow} ${
                  item.role === "user" ? styles.userRow : styles.agentRow
                }`}
                key={item.id}
              >
                {item.role === "assistant" ? (
                  <div className={styles.smallAvatar}>牛</div>
                ) : null}
                <div className={styles.messageBody}>
                  <p className={styles.messageLabel}>
                    {item.role === "assistant"
                      ? item.failed
                        ? "小牛 · 未完成"
                        : "小牛"
                      : "你"}
                  </p>
                  {item.toolTrace?.length ? (
                    <div className={styles.toolTrace} aria-label="Agent 工具调用">
                      {item.toolTrace.map((trace, traceIndex) => (
                        <span
                          className={
                            trace.status === "completed"
                              ? styles.toolCompleted
                              : styles.toolRunning
                          }
                          key={`${trace.call_id ?? trace.tool}-${traceIndex}`}
                        >
                          {trace.status === "completed" ? "✓" : "···"}
                          {trace.tool === "search_products"
                            ? " 搜索商品"
                            : trace.tool === "get_product"
                              ? " 查询详情"
                              : ` ${trace.tool}`}
                        </span>
                      ))}
                    </div>
                  ) : null}
                  <div
                    className={`${styles.bubble} ${
                      item.role === "user"
                        ? styles.userBubble
                        : item.failed
                          ? styles.failedBubble
                          : styles.agentBubble
                    }`}
                  >
                    {item.content ? (
                      item.content
                    ) : (
                      <span className={styles.typing} aria-label="正在输入">
                        <i />
                        <i />
                        <i />
                      </span>
                    )}
                    {item.streaming && item.content ? (
                      <span className={styles.cursor} aria-hidden="true" />
                    ) : null}
                  </div>
                  {item.products?.length ? (
                    <div className={styles.recommendations}>
                      {item.products.slice(0, 3).map((product) => (
                        <article className={styles.productCard} key={product.id}>
                          <div className={styles.productTopline}>
                            <span>{product.category}</span>
                            {product.badge ? <b>{product.badge}</b> : null}
                          </div>
                          <h3>{product.name}</h3>
                          <p>{product.description}</p>
                          <div className={styles.productFooter}>
                            <strong>
                              {priceFormatter.format(product.price_cents / 100)}
                            </strong>
                            <span
                              className={
                                product.stock && product.stock > 0
                                  ? styles.inStock
                                  : styles.outOfStock
                              }
                            >
                              {product.stock && product.stock > 0
                                ? `库存 ${product.stock}`
                                : "暂时缺货"}
                            </span>
                          </div>
                          <div className={styles.productTags}>
                            {product.tags.slice(0, 3).map((tag) => (
                              <span key={tag}>{tag}</span>
                            ))}
                          </div>
                        </article>
                      ))}
                    </div>
                  ) : null}
                </div>
                {item.role === "user" ? (
                  <div className={styles.userAvatar}>你</div>
                ) : null}
              </article>
            ))}
            <div ref={endRef} />
          </div>

          <div className={styles.composerArea}>
            {error ? (
              <p className={styles.error} role="alert">
                {error}
              </p>
            ) : null}
            <form className={styles.composer} onSubmit={sendMessage}>
              <textarea
                ref={textareaRef}
                rows={2}
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="问问小牛，今天想找点什么…"
                maxLength={10000}
                disabled={sending || conversationLoading}
                aria-label="输入消息"
              />
              <button
                type="submit"
                disabled={sending || conversationLoading || !draft.trim()}
              >
                <span>{sending ? "回复中" : "发送"}</span>
                <b>↑</b>
              </button>
            </form>
            <div className={styles.composerHint}>
              <span>Enter 发送 · Shift + Enter 换行</span>
              <span>对话自动保存到 SQLite</span>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
