import Link from "next/link";
import { notFound } from "next/navigation";

import { AdminApiError, getConversation } from "@/lib/admin-api";
import { formatFullDate, formatMoney } from "@/lib/format";
import type {
  ProductFeedback,
  RecommendedProductSummary,
} from "@/lib/types";
import { TriggerSummaryButton } from "./trigger-summary-button";

export const dynamic = "force-dynamic";

const feedbackLabels: Record<ProductFeedback["overall"], string> = {
  positive: "正面",
  negative: "负面",
  neutral: "中性",
  mixed: "褒贬不一",
  unclear: "不明确",
};

function ProductCard({
  item,
}: {
  item: RecommendedProductSummary;
}) {
  return (
    <article className="product-summary-card">
      <div className="product-summary-card__heading">
        <div>
          <span className="product-category">{item.product.category}</span>
          <h4>{item.product.name}</h4>
        </div>
        <div className="product-price">
          {formatMoney(item.product.price_cents)}
          {item.product.is_ad ? <span>广告</span> : null}
        </div>
      </div>
      <p className="product-description">{item.product.description}</p>
      {item.key_information.length > 0 ? (
        <dl className="key-information">
          {item.key_information.map((information, index) => (
            <div key={`${information.name}-${index}`}>
              <dt>{information.name}</dt>
              <dd>{information.value}</dd>
            </div>
          ))}
        </dl>
      ) : null}
      {item.reason ? (
        <div className="reason-block">
          <span>最终推荐理由</span>
          <p>{item.reason}</p>
          {item.environmental_fit ? (
            <small>场景匹配：{item.environmental_fit}</small>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}

export default async function ConversationDetailPage({
  params,
}: {
  params: Promise<{ conversationId: string }>;
}) {
  const { conversationId } = await params;
  let result;
  try {
    result = await getConversation(conversationId);
  } catch (error) {
    const message =
      error instanceof AdminApiError
        ? error.message
        : "无法连接管理后端。";
    return (
      <section className="empty-state">
        <p className="eyebrow">CONVERSATION UNAVAILABLE</p>
        <h1>暂时无法加载对话</h1>
        <p>{message}</p>
        <Link className="primary-button" href="/conversations">
          返回对话列表
        </Link>
      </section>
    );
  }
  if (result === null) {
    notFound();
  }

  const { conversation, summary } = result;
  const summaryIsCurrent =
    summary !== null && summary.source_updated_at === conversation.updated_at;
  const productNames = new Map<string, string>();
  summary?.recommendation_rounds?.forEach((round) => {
    round.products.forEach((item) => {
      productNames.set(item.product.id, item.product.name);
    });
  });

  return (
    <div className="detail-page">
      <div className="detail-breadcrumb">
        <Link href="/conversations">对话管理</Link>
        <span>/</span>
        <strong>{conversation.title}</strong>
      </div>

      <section className="detail-hero">
        <div>
          <p className="eyebrow">CONVERSATION DETAIL</p>
          <h1>{conversation.title}</h1>
          <p className="mono-id">{conversation.id}</p>
        </div>
        <dl className="detail-metadata">
          <div>
            <dt>消息数量</dt>
            <dd>{conversation.message_count}</dd>
          </div>
          <div>
            <dt>创建时间</dt>
            <dd>{formatFullDate(conversation.created_at)}</dd>
          </div>
          <div>
            <dt>最近更新</dt>
            <dd>{formatFullDate(conversation.updated_at)}</dd>
          </div>
        </dl>
      </section>

      <section className="summary-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">GENERATED DIGEST</p>
            <h2>对话总结</h2>
          </div>
          <div className="summary-heading-actions">
            {summary ? (
              <div className="summary-heading-meta">
                {!summaryIsCurrent ? (
                  <span className="summary-stale">等待重新生成</span>
                ) : null}
                <span className="summary-time">
                  生成于 {formatFullDate(summary.generated_at)}
                </span>
              </div>
            ) : null}
            <TriggerSummaryButton
              conversationId={conversation.id}
              hasSummary={summary !== null}
            />
          </div>
        </div>

        {summary ? (
          <>
            <p className="summary-lead">{summary.summary}</p>
            {!summaryIsCurrent ? (
              <div className="summary-stale-notice">
                这份总结生成后对话又发生了更新，最新内容将在下个定时周期重新总结。
              </div>
            ) : null}

            <div className="summary-columns">
              <div className="summary-block">
                <h3>用户目标</h3>
                {summary.user_goals?.length ? (
                  <ul className="plain-list">
                    {summary.user_goals.map((goal, index) => (
                      <li key={`${goal}-${index}`}>{goal}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">未提取到明确目标</p>
                )}
              </div>
              <div className="summary-block">
                <h3>明确约束</h3>
                {summary.explicit_constraints?.length ? (
                  <div className="tag-list">
                    {summary.explicit_constraints.map((constraint, index) => (
                      <span key={`${constraint}-${index}`}>{constraint}</span>
                    ))}
                  </div>
                ) : (
                  <p className="muted">未提取到明确约束</p>
                )}
              </div>
            </div>

            <div className="summary-section">
              <div className="section-title-row">
                <h3>推荐商品与理由</h3>
                <span>
                  {summary.recommendation_rounds?.reduce(
                    (total, round) => total + round.products.length,
                    0,
                  ) ?? 0}{" "}
                  件
                </span>
              </div>
              {summary.recommendation_rounds?.length ? (
                <div className="recommendation-rounds">
                  {summary.recommendation_rounds.map((round, roundIndex) => (
                    <div
                      className="recommendation-round"
                      key={round.assistant_message_id}
                    >
                      <div className="round-heading">
                        <span>推荐轮次 {roundIndex + 1}</span>
                        <p>{round.user_request}</p>
                      </div>
                      {round.ranking_summary ? (
                        <p className="ranking-summary">
                          终排摘要：{round.ranking_summary}
                        </p>
                      ) : null}
                      <div className="product-card-grid">
                        {round.products.map((item) => (
                          <ProductCard
                            item={item}
                            key={item.product.id}
                          />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="muted">本对话没有记录到最终推荐商品。</p>
              )}
            </div>

            <div className="summary-columns summary-columns--wide">
              <div className="summary-block">
                <h3>商品反馈</h3>
                {summary.product_feedback?.length ? (
                  <div className="feedback-list">
                    {summary.product_feedback.map((feedback, index) => (
                      <article
                        className="feedback-card"
                        key={`${feedback.product_id}-${index}`}
                      >
                        <div>
                          <strong>
                            {productNames.get(feedback.product_id) ??
                              feedback.product_id}
                          </strong>
                          <span
                            className={`polarity polarity--${feedback.overall}`}
                          >
                            {feedbackLabels[feedback.overall]}
                          </span>
                        </div>
                        {feedback.aspects.length ? (
                          <p>
                            {feedback.aspects
                              .map(
                                (aspect) =>
                                  `${aspect.name}${
                                    aspect.value ? `：${aspect.value}` : ""
                                  }`,
                              )
                              .join(" · ")}
                          </p>
                        ) : null}
                        {feedback.evidence.map((evidence) => (
                          <blockquote key={`${evidence.message_id}-${evidence.quote}`}>
                            “{evidence.quote}”
                          </blockquote>
                        ))}
                      </article>
                    ))}
                  </div>
                ) : (
                  <p className="muted">用户尚未对推荐商品作出明确评价。</p>
                )}
              </div>

              <div className="summary-block">
                <h3>一般偏好</h3>
                {summary.general_preferences?.length ? (
                  <div className="preference-list">
                    {summary.general_preferences.map((preference, index) => (
                      <article
                        className="preference-card"
                        key={`${preference.dimension}-${index}`}
                      >
                        <div>
                          <span>{preference.dimension}</span>
                          <strong>{preference.value}</strong>
                          <em>
                            {preference.polarity === "prefer"
                              ? "偏好"
                              : "排斥"}
                          </em>
                        </div>
                        {preference.evidence[0] ? (
                          <blockquote>
                            “{preference.evidence[0].quote}”
                          </blockquote>
                        ) : null}
                      </article>
                    ))}
                  </div>
                ) : (
                  <p className="muted">本对话没有提取到一般偏好。</p>
                )}
              </div>
            </div>

            {summary.unresolved_items?.length ? (
              <div className="unresolved-block">
                <h3>待处理事项</h3>
                <ul className="plain-list">
                  {summary.unresolved_items.map((item, index) => (
                    <li key={`${item}-${index}`}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </>
        ) : (
          <div className="summary-missing">
            <strong>总结尚未生成</strong>
            <p>
              对话超过一小时未更新后，定时任务会在下一周期生成总结。当前仍可查看
              下方完整对话。
            </p>
          </div>
        )}
      </section>

      <section className="panel message-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">CONVERSATION TRANSCRIPT</p>
            <h2>完整对话</h2>
          </div>
          <span className="count-badge">
            {conversation.messages.length} 条消息
          </span>
        </div>
        <div className="message-list">
          {conversation.messages.map((message, index) => (
            <article
              className={`message message--${message.role}`}
              key={message.id}
            >
              <div className="message-rail">
                <span>{String(index + 1).padStart(2, "0")}</span>
                <i />
              </div>
              <div className="message-body">
                <div className="message-heading">
                  <strong>
                    {message.role === "user" ? "用户" : "小牛导购"}
                  </strong>
                  <span
                    className={`message-status message-status--${message.status}`}
                  >
                    {message.status}
                  </span>
                  <time>{formatFullDate(message.created_at)}</time>
                </div>
                <p className="message-content">{message.content}</p>
                {message.recommendations?.length ? (
                  <div className="inline-products">
                    {message.recommendations.map((product) => (
                      <div
                        className="inline-product"
                        key={product.id}
                      >
                        <div>
                          <strong>{product.name}</strong>
                          <span>{product.category}</span>
                        </div>
                        <b>{formatMoney(product.price_cents)}</b>
                      </div>
                    ))}
                  </div>
                ) : null}
                {message.orders?.length ? (
                  <p className="order-note">
                    创建订单：
                    {message.orders
                      .map((order) => order.order_id)
                      .join("、")}
                  </p>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
