import asyncio
import logging
from collections.abc import AsyncIterator, Sequence

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from .agent_runner import sse_event, stream_agent_reply
from .chat import compose_reply
from .llm_config import LLMConfig, LLMConfigError, load_llm_config
from .mall_client import CatalogUnavailable, MallClient, get_mall_client
from .mall_gateway import MallGateway
from .models import (
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationList,
    ConversationMessage,
    OrderLink,
    PlanState,
    Product,
    StreamChatRequest,
    StoredMessage,
    ToolTrace,
)
from .storage import FIXED_USER_ID, ConversationStore, get_conversation_store

logger = logging.getLogger(__name__)

app = FastAPI(title="Agent Service", version="0.1.0")


def to_conversation_messages(
    messages: Sequence[StoredMessage],
) -> list[ConversationMessage]:
    return [
        ConversationMessage(role=message.role, content=message.content)
        for message in messages
    ]


def latest_plan_state(
    messages: Sequence[StoredMessage],
) -> PlanState | None:
    for message in reversed(messages):
        if message.plan_state is not None:
            return message.plan_state
    return None


def latest_recommendations(
    messages: Sequence[StoredMessage],
) -> list[Product]:
    for message in reversed(messages):
        if message.recommendations:
            return message.recommendations
    return []


def latest_orders(
    messages: Sequence[StoredMessage],
) -> list[OrderLink]:
    for message in reversed(messages):
        if message.orders:
            return message.orders
    return []


async def persisted_agent_stream(
    conversation_id: str,
    conversation_title: str,
    assistant_message_id: str,
    context: Sequence[StoredMessage],
    config: LLMConfig,
    store: ConversationStore,
    mall: MallGateway,
) -> AsyncIterator[str]:
    content_parts: list[str] = []
    recommendations: dict[str, Product] = {}
    tool_trace: list[ToolTrace] = []
    plan_state: PlanState | None = None
    created_orders: dict[str, OrderLink] = {}
    persisted = False

    def message_metadata() -> dict[str, object]:
        metadata: dict[str, object] = {
            "recommendations": [
                product.model_dump(mode="json")
                for product in recommendations.values()
            ],
            "tool_trace": [
                trace.model_dump(mode="json") for trace in tool_trace
            ],
        }
        if plan_state is not None:
            metadata["plan_state"] = plan_state.model_dump(mode="json")
        if created_orders:
            metadata["orders"] = [
                order.model_dump(mode="json")
                for order in created_orders.values()
            ]
        return metadata

    yield sse_event(
        {
            "type": "conversation",
            "conversation_id": conversation_id,
            "title": conversation_title,
        }
    )

    try:
        async for event in stream_agent_reply(
            to_conversation_messages(context),
            config,
            mall,
            previous_plan_state=latest_plan_state(context),
            previous_recommendations=latest_recommendations(context),
            previous_orders=latest_orders(context),
        ):
            event_type = event.get("type")
            raw_event = sse_event(event)

            if event_type == "delta":
                content = event.get("content")
                if isinstance(content, str):
                    content_parts.append(content)
                yield raw_event
                continue

            if event_type == "recommendations":
                for product in event.get("products", []):
                    if isinstance(product, dict):
                        parsed = Product.model_validate(product)
                        recommendations[parsed.id] = parsed
                yield raw_event
                continue

            if event_type == "plan_updated":
                plan_state_payload = event.get("plan_state")
                if isinstance(plan_state_payload, dict):
                    plan_state = PlanState.model_validate(plan_state_payload)
                yield raw_event
                continue

            if event_type == "order_created":
                order_payload = event.get("order")
                if isinstance(order_payload, dict):
                    order = OrderLink.model_validate(order_payload)
                    created_orders[order.order_id] = order
                yield raw_event
                continue

            if event_type == "tool_started":
                call_id = event.get("call_id")
                tool_trace.append(
                    ToolTrace(
                        call_id=call_id if isinstance(call_id, str) else None,
                        tool=str(event.get("tool") or "unknown_tool"),
                        arguments=str(event.get("arguments") or ""),
                    )
                )
                yield raw_event
                continue

            if event_type == "tool_completed":
                call_id = event.get("call_id")
                for trace in reversed(tool_trace):
                    if trace.call_id == call_id:
                        trace.status = "completed"
                        break
                yield raw_event
                continue

            if event_type == "error":
                message = event.get("message")
                error_message = (
                    message
                    if isinstance(message, str)
                    else "模型流返回了未知错误。"
                )
                if isinstance(event.get("tool_trace"), list):
                    tool_trace = [
                        ToolTrace.model_validate(trace)
                        for trace in event["tool_trace"]
                        if isinstance(trace, dict)
                    ]
                plan_state_payload = event.get("plan_state")
                if isinstance(plan_state_payload, dict):
                    plan_state = PlanState.model_validate(plan_state_payload)
                if isinstance(event.get("orders"), list):
                    for order_payload in event["orders"]:
                        if isinstance(order_payload, dict):
                            order = OrderLink.model_validate(order_payload)
                            created_orders[order.order_id] = order
                store.finish_message(
                    assistant_message_id,
                    "".join(content_parts) or error_message,
                    "failed",
                    metadata=message_metadata(),
                )
                persisted = True
                yield raw_event
                return

            if event_type == "done":
                if isinstance(event.get("tool_trace"), list):
                    tool_trace = [
                        ToolTrace.model_validate(trace)
                        for trace in event["tool_trace"]
                        if isinstance(trace, dict)
                    ]
                plan_state_payload = event.get("plan_state")
                if isinstance(plan_state_payload, dict):
                    plan_state = PlanState.model_validate(plan_state_payload)
                if isinstance(event.get("orders"), list):
                    for order_payload in event["orders"]:
                        if isinstance(order_payload, dict):
                            order = OrderLink.model_validate(order_payload)
                            created_orders[order.order_id] = order
                store.finish_message(
                    assistant_message_id,
                    "".join(content_parts),
                    "completed",
                    metadata=message_metadata(),
                )
                persisted = True
                yield raw_event
                return

        error_message = "Agent 流意外结束，没有收到完成标记。"
        store.finish_message(
            assistant_message_id,
            "".join(content_parts) or error_message,
            "failed",
            metadata=message_metadata(),
        )
        persisted = True
        yield sse_event(
            {
                "type": "error",
                "message_id": assistant_message_id,
                "message": error_message,
            }
        )
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("Persisted LLM stream failed")
        error_message = "对话流处理失败，请查看 agent-service 终端日志。"
        store.finish_message(
            assistant_message_id,
            "".join(content_parts) or error_message,
            "failed",
            metadata=message_metadata(),
        )
        persisted = True
        yield sse_event(
            {
                "type": "error",
                "message_id": assistant_message_id,
                "message": error_message,
            }
        )
    finally:
        if not persisted:
            store.finish_message(
                assistant_message_id,
                "".join(content_parts) or "客户端断开，回复未完成。",
                "failed",
                metadata=message_metadata(),
            )


async def configuration_error_stream(
    conversation_id: str,
    conversation_title: str,
    assistant_message_id: str,
    message: str,
) -> AsyncIterator[str]:
    yield sse_event(
        {
            "type": "conversation",
            "conversation_id": conversation_id,
            "title": conversation_title,
        }
    )
    yield sse_event(
        {"type": "start", "message_id": assistant_message_id}
    )
    yield sse_event(
        {
            "type": "error",
            "message_id": assistant_message_id,
            "message": message,
        }
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "agent-service"}


@app.get("/api/conversations", response_model=ConversationList)
def list_conversations(
    store: ConversationStore = Depends(get_conversation_store),
) -> ConversationList:
    return ConversationList(items=store.list_conversations(FIXED_USER_ID))


@app.get(
    "/api/conversations/{conversation_id}",
    response_model=ConversationDetail,
)
def get_conversation(
    conversation_id: str,
    store: ConversationStore = Depends(get_conversation_store),
) -> ConversationDetail:
    conversation = store.get_conversation(FIXED_USER_ID, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="对话不存在")
    return conversation


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    mall_client: MallClient = Depends(get_mall_client),
) -> ChatResponse:
    try:
        catalog = await mall_client.list_products()
        products = catalog.items
    except CatalogUnavailable:
        products = []

    return ChatResponse(
        reply=compose_reply(request.message, products),
        products=list(products[:3]),
    )


@app.post("/api/chat/stream")
async def stream_chat(
    request: StreamChatRequest,
    store: ConversationStore = Depends(get_conversation_store),
    mall: MallGateway = Depends(get_mall_client),
) -> StreamingResponse:
    if request.conversation_id:
        conversation = store.get_conversation(
            FIXED_USER_ID,
            request.conversation_id,
        )
        if conversation is None:
            raise HTTPException(status_code=404, detail="对话不存在")
        conversation_id = conversation.id
        title = conversation.title
    else:
        conversation_id = store.create_conversation(
            FIXED_USER_ID,
            request.message,
        )
        conversation = store.get_conversation(FIXED_USER_ID, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=500, detail="创建对话失败")
        title = conversation.title

    store.add_message(
        conversation_id,
        "user",
        request.message,
        "completed",
    )
    context = store.model_context(conversation_id)
    assistant_message_id = store.add_message(
        conversation_id,
        "assistant",
        "",
        "streaming",
    )

    try:
        config = load_llm_config()
    except LLMConfigError as exc:
        message = str(exc)
        store.finish_message(assistant_message_id, message, "failed")
        stream = configuration_error_stream(
            conversation_id,
            title,
            assistant_message_id,
            message,
        )
    else:
        stream = persisted_agent_stream(
            conversation_id,
            title,
            assistant_message_id,
            context,
            config,
            store,
            mall,
        )

    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
