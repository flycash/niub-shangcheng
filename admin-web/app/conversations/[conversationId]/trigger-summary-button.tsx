"use client";

import { useActionState } from "react";

import {
  triggerSummaryAction,
  type TriggerSummaryState,
} from "./actions";

const initialState: TriggerSummaryState = {
  status: "idle",
  message: "",
};

export function TriggerSummaryButton({
  conversationId,
  hasSummary,
}: {
  conversationId: string;
  hasSummary: boolean;
}) {
  const [state, formAction, pending] = useActionState(
    triggerSummaryAction,
    initialState,
  );

  return (
    <form className="summary-trigger" action={formAction}>
      <input
        type="hidden"
        name="conversationId"
        value={conversationId}
      />
      <button type="submit" disabled={pending}>
        {pending
          ? "正在生成总结…"
          : hasSummary
            ? "重新生成总结"
            : "立即生成总结"}
      </button>
      {state.message ? (
        <span
          className={`trigger-message trigger-message--${state.status}`}
          role="status"
        >
          {state.message}
        </span>
      ) : null}
    </form>
  );
}
