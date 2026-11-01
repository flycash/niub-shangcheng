import json
import logging
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from agents import (
    Agent,
    MaxTurnsExceeded,
    ModelSettings,
    OpenAIChatCompletionsModel,
    RawResponsesStreamEvent,
    RunConfig,
    RunItemStreamEvent,
    Runner,
    function_tool,
    set_tracing_disabled,
)
from openai import AsyncOpenAI
from openai.types.responses import ResponseTextDeltaEvent

from .llm_config import LLMConfig
from .mock_mall import MallGateway
from .models import ConversationMessage, Product, ToolTrace
from .prompt_loader import PromptLoadError, load_agent_prompt

logger = logging.getLogger(__name__)
set_tracing_disabled(True)


def sse_event(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def normalize_openai_base_url(base_url: str) -> str:
    base_url = base_url.rstrip("/")
    suffix = "/chat/completions"
    if base_url.endswith(suffix):
        return base_url[: -len(suffix)]
    return base_url


@dataclass
class ShoppingAgentContext:
    mall: MallGateway
    recommended_products: dict[str, Product] = field(default_factory=dict)
    tool_trace: list[ToolTrace] = field(default_factory=list)

    def remember(self, products: Sequence[Product]) -> None:
        for product in products:
            self.recommended_products[product.id] = product


def product_payload(products: Sequence[Product]) -> str:
    return json.dumps(
        [product.model_dump(mode="json") for product in products],
        ensure_ascii=False,
    )


def create_tools(context: ShoppingAgentContext, config: LLMConfig) -> list[Any]:
    @function_tool(
        name_override="search_products",
        description_override=(
            "搜索商城商品。推荐商品前必须调用。可按关键词、分类和价格筛选，"
            "最多返回 5 件商品。"
        ),
        strict_mode=False,
        timeout=config.tool_timeout_seconds,
        timeout_behavior="raise_exception",
    )
    async def search_products(
        query: str = "",
        category: str | None = None,
        max_price_cents: int | None = None,
        min_price_cents: int | None = None,
        limit: int = 5,
    ) -> str:
        """搜索商城商品。

        Args:
            query: 商品关键词，例如通勤包、礼物、咖啡；泛化推荐时传空字符串。
            category: 商品分类，例如箱包、家居、文创、饮品、个护。
            max_price_cents: 最高价格，单位是分。
            min_price_cents: 最低价格，单位是分。
            limit: 返回数量，范围 1 到 5。
        """
        products = await context.mall.search_products(
            query=query,
            category=category,
            max_price_cents=max_price_cents,
            min_price_cents=min_price_cents,
            limit=limit,
        )
        context.remember(products)
        return product_payload(products)

    @function_tool(
        name_override="get_product",
        description_override=(
            "按商品 ID 查询商城商品详情，用于确认价格、库存和描述。"
        ),
        strict_mode=False,
        timeout=config.tool_timeout_seconds,
        timeout_behavior="raise_exception",
    )
    async def get_product(product_id: str) -> str:
        """查询单个商品详情。

        Args:
            product_id: 商城中稳定且唯一的商品 ID。
        """
        product = await context.mall.get_product(product_id)
        if product is None:
            return json.dumps(
                {"error": f"商品 {product_id} 不存在"},
                ensure_ascii=False,
            )
        context.remember([product])
        return product_payload([product])

    return [search_products, get_product]


def raw_item_value(item: Any, name: str) -> str | None:
    raw_item = getattr(item, "raw_item", None)
    if isinstance(raw_item, dict):
        value = raw_item.get(name)
    else:
        value = getattr(raw_item, name, None)
    return value if isinstance(value, str) else None


async def stream_agent_reply(
    messages: Sequence[ConversationMessage],
    config: LLMConfig,
    mall: MallGateway,
    model_override: Any | None = None,
) -> AsyncIterator[dict[str, Any]]:
    message_id = f"assistant-{uuid4().hex}"
    yield {"type": "start", "message_id": message_id}

    client: AsyncOpenAI | None = None
    context = ShoppingAgentContext(mall=mall)
    content_parts: list[str] = []
    running_tools: dict[str, int] = {}
    try:
        instructions = load_agent_prompt(config)
        if model_override is None:
            client = AsyncOpenAI(
                api_key=config.api_key.get_secret_value(),
                base_url=normalize_openai_base_url(config.base_url),
                timeout=config.timeout_seconds,
                max_retries=1,
            )
            model = OpenAIChatCompletionsModel(
                model=config.model,
                openai_client=client,
                buffer_streamed_tool_calls=True,
            )
        else:
            model = model_override
        agent = Agent[ShoppingAgentContext](
            name="小牛导购",
            instructions=instructions,
            model=model,
            tools=create_tools(context, config),
            model_settings=ModelSettings(
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            ),
        )

        result = Runner.run_streamed(
            agent,
            input=[
                {"role": message.role, "content": message.content}
                for message in messages
            ],
            context=context,
            max_turns=config.max_turns,
            run_config=RunConfig(tracing_disabled=True),
        )

        async for event in result.stream_events():
            if isinstance(event, RawResponsesStreamEvent):
                if isinstance(event.data, ResponseTextDeltaEvent):
                    content_parts.append(event.data.delta)
                    yield {
                        "type": "delta",
                        "message_id": message_id,
                        "content": event.data.delta,
                    }
                continue

            if not isinstance(event, RunItemStreamEvent):
                continue

            if event.name == "tool_called":
                tool_name = event.item.tool_name or "unknown_tool"
                call_id = event.item.call_id
                arguments = raw_item_value(event.item, "arguments") or ""
                trace_index = len(context.tool_trace)
                context.tool_trace.append(
                    ToolTrace(
                        call_id=call_id,
                        tool=tool_name,
                        arguments=arguments,
                        status="started",
                    )
                )
                if call_id:
                    running_tools[call_id] = trace_index
                yield {
                    "type": "tool_started",
                    "message_id": message_id,
                    "call_id": call_id,
                    "tool": tool_name,
                    "arguments": arguments,
                }

            elif event.name == "tool_output":
                tool_name = "tool"
                call_id = event.item.call_id
                trace_index = running_tools.get(call_id or "")
                if trace_index is not None:
                    trace = context.tool_trace[trace_index]
                    tool_name = trace.tool
                    trace.status = "completed"
                    trace.summary = str(event.item.output)[:500]
                yield {
                    "type": "tool_completed",
                    "message_id": message_id,
                    "call_id": call_id,
                    "tool": tool_name,
                }
                if context.recommended_products:
                    yield {
                        "type": "recommendations",
                        "message_id": message_id,
                        "products": [
                            product.model_dump(mode="json")
                            for product in context.recommended_products.values()
                        ],
                    }

        if not content_parts and isinstance(result.final_output, str):
            content_parts.append(result.final_output)
            yield {
                "type": "delta",
                "message_id": message_id,
                "content": result.final_output,
            }

        if context.recommended_products:
            yield {
                "type": "recommendations",
                "message_id": message_id,
                "products": [
                    product.model_dump(mode="json")
                    for product in context.recommended_products.values()
                ],
            }

        yield {
            "type": "done",
            "message_id": message_id,
            "tool_trace": [
                trace.model_dump(mode="json") for trace in context.tool_trace
            ],
        }
    except PromptLoadError as exc:
        yield {
            "type": "error",
            "message_id": message_id,
            "message": f"Agent 提示词加载失败：{exc}",
            "tool_trace": [],
        }
    except MaxTurnsExceeded:
        yield {
            "type": "error",
            "message_id": message_id,
            "message": (
                f"Agent 超过最大工具回合数（{config.max_turns}）。"
                "请换一种问法或提高配置中的 max_turns。"
            ),
            "tool_trace": [
                trace.model_dump(mode="json") for trace in context.tool_trace
            ],
        }
    except Exception:
        logger.exception("Agents SDK run failed")
        yield {
            "type": "error",
            "message_id": message_id,
            "message": (
                "Agent 调用失败，请检查模型服务是否支持 Chat Completions "
                "工具调用，并查看 agent-service 终端日志。"
            ),
            "tool_trace": [
                trace.model_dump(mode="json") for trace in context.tool_trace
            ],
        }
    finally:
        if client is not None:
            await client.close()
