import Link from "next/link";

import { AdminApiError, listConversations } from "@/lib/admin-api";
import { formatDate } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function ConversationsPage() {
  let conversations;
  try {
    conversations = await listConversations();
  } catch (error) {
    const message =
      error instanceof AdminApiError
        ? error.message
        : "无法连接管理后端，请确认服务已经启动。";
    return (
      <section className="empty-state">
        <p className="eyebrow">SERVICE UNAVAILABLE</p>
        <h1>对话服务暂时不可用</h1>
        <p>{message}</p>
        <code>ADMIN_BACKEND_URL=http://127.0.0.1:8003</code>
      </section>
    );
  }

  const totalMessages = conversations.items.reduce(
    (total, conversation) => total + conversation.message_count,
    0,
  );

  return (
    <div className="page-stack">
      <section className="page-heading">
        <div>
          <p className="eyebrow">CONVERSATION OPERATIONS</p>
          <h1>对话管理</h1>
          <p className="page-description">
            查看商城 Agent 的历史会话、完整消息和定时生成的对话总结。
          </p>
        </div>
        <div className="metric-grid">
          <div className="metric-card">
            <span>对话总数</span>
            <strong>{conversations.items.length}</strong>
          </div>
          <div className="metric-card">
            <span>消息总数</span>
            <strong>{totalMessages}</strong>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>全部对话</h2>
            <p>按最近更新时间倒序排列</p>
          </div>
          <span className="count-badge">
            {conversations.items.length} 条记录
          </span>
        </div>

        {conversations.items.length === 0 ? (
          <div className="empty-row">暂时还没有对话记录。</div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>对话</th>
                  <th>消息数</th>
                  <th>创建时间</th>
                  <th>最近更新</th>
                  <th aria-label="操作" />
                </tr>
              </thead>
              <tbody>
                {conversations.items.map((conversation) => (
                  <tr key={conversation.id}>
                    <td>
                      <Link
                        className="conversation-title"
                        href={`/conversations/${conversation.id}`}
                      >
                        {conversation.title}
                      </Link>
                      <span className="mono-id">{conversation.id}</span>
                    </td>
                    <td>{conversation.message_count}</td>
                    <td>{formatDate(conversation.created_at)}</td>
                    <td>{formatDate(conversation.updated_at)}</td>
                    <td className="action-cell">
                      <Link
                        className="text-link"
                        href={`/conversations/${conversation.id}`}
                      >
                        查看详情
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
