import asyncio
import os

from fastapi import Depends, FastAPI, HTTPException

from .agent_client import AgentServiceClient, AgentServiceError


app = FastAPI(title="Niub Admin Backend", version="0.1.0")


def get_agent_service_client() -> AgentServiceClient:
    return AgentServiceClient(
        base_url=os.getenv(
            "AGENT_SERVICE_URL",
            "http://127.0.0.1:8002",
        ),
        timeout_seconds=float(os.getenv("AGENT_SERVICE_TIMEOUT_SECONDS", "10")),
        summary_timeout_seconds=float(
            os.getenv("AGENT_SERVICE_SUMMARY_TIMEOUT_SECONDS", "1800")
        ),
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "admin-backend"}


@app.get("/api/conversations")
async def list_conversations(
    client: AgentServiceClient = Depends(get_agent_service_client),
) -> object:
    try:
        return await client.list_conversations()
    except AgentServiceError as exc:
        raise HTTPException(
            status_code=502,
            detail="对话服务暂时不可用",
        ) from exc


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    client: AgentServiceClient = Depends(get_agent_service_client),
) -> dict[str, object | None]:
    try:
        conversation, summary = await asyncio.gather(
            client.get_conversation(conversation_id),
            client.get_conversation_summary(conversation_id),
        )
    except AgentServiceError as exc:
        raise HTTPException(
            status_code=502,
            detail="对话服务暂时不可用",
        ) from exc
    if conversation is None:
        raise HTTPException(status_code=404, detail="对话不存在")
    return {
        "conversation": conversation,
        "summary": summary,
    }


@app.post("/api/conversations/{conversation_id}/summary")
async def trigger_conversation_summary(
    conversation_id: str,
    client: AgentServiceClient = Depends(get_agent_service_client),
) -> object:
    try:
        summary = await client.trigger_conversation_summary(conversation_id)
    except AgentServiceError as exc:
        raise HTTPException(
            status_code=502,
            detail="对话总结生成失败",
        ) from exc
    if summary is None:
        raise HTTPException(status_code=404, detail="对话不存在")
    return summary
