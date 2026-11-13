import type {
  ConversationAdminDetail,
  ConversationListPayload,
} from "@/lib/types";

const adminBackendUrl =
  process.env.ADMIN_BACKEND_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8003";

export class AdminApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "AdminApiError";
  }
}

async function adminFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${adminBackendUrl}${path}`, {
    cache: "no-store",
    ...init,
  });
  const payload = (await response.json().catch(() => null)) as
    | { detail?: unknown }
    | T
    | null;
  if (!response.ok) {
    const detail =
      payload &&
      typeof payload === "object" &&
      "detail" in payload &&
      typeof payload.detail === "string"
        ? payload.detail
        : "管理服务返回了未知错误";
    throw new AdminApiError(detail, response.status);
  }
  return payload as T;
}

export async function listConversations(): Promise<ConversationListPayload> {
  return adminFetch<ConversationListPayload>("/api/conversations");
}

export async function getConversation(
  conversationId: string,
): Promise<ConversationAdminDetail | null> {
  try {
    return await adminFetch<ConversationAdminDetail>(
      `/api/conversations/${encodeURIComponent(conversationId)}`,
    );
  } catch (error) {
    if (error instanceof AdminApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function triggerConversationSummary(
  conversationId: string,
): Promise<void> {
  await adminFetch(
    `/api/conversations/${encodeURIComponent(conversationId)}/summary`,
    { method: "POST" },
  );
}
