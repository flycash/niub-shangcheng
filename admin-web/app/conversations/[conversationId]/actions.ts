"use server";

import { revalidatePath } from "next/cache";

import {
  AdminApiError,
  triggerConversationSummary,
} from "@/lib/admin-api";

export interface TriggerSummaryState {
  status: "idle" | "success" | "error";
  message: string;
}

export async function triggerSummaryAction(
  _previousState: TriggerSummaryState,
  formData: FormData,
): Promise<TriggerSummaryState> {
  const conversationId = formData.get("conversationId");
  if (typeof conversationId !== "string" || !conversationId) {
    return {
      status: "error",
      message: "缺少对话 ID，无法生成总结。",
    };
  }

  try {
    await triggerConversationSummary(conversationId);
    revalidatePath(`/conversations/${conversationId}`);
    revalidatePath("/conversations");
    return {
      status: "success",
      message: "对话总结已生成并更新。",
    };
  } catch (error) {
    return {
      status: "error",
      message:
        error instanceof AdminApiError
          ? error.message
          : "总结生成失败，请稍后重试。",
    };
  }
}
