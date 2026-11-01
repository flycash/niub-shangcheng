import type { Metadata } from "next";

import { AgentChat } from "@/components/agent-chat";

export const metadata: Metadata = {
  title: "小牛导购 · 牛掰商城",
  description: "和商城 Agent 开始多轮对话",
};

export default function ChatPage() {
  return <AgentChat />;
}
