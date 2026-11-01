import asyncio
import json
from pathlib import Path

from agents.tool_context import ToolContext
from agents.testing import ScriptedModel, assistant_message, function_call

from agent_service.agent_runner import (
    ShoppingAgentContext,
    create_tools,
    normalize_openai_base_url,
    stream_agent_reply,
)
from agent_service.llm_config import LLMConfig
from agent_service.mock_mall import MockMallGateway
from agent_service.models import ConversationMessage

PROMPT_PATH = (
    Path(__file__).resolve().parents[1] / "prompts" / "shopping_agent.md"
)


def test_normalize_openai_base_url() -> None:
    assert (
        normalize_openai_base_url("https://api.deepseek.com")
        == "https://api.deepseek.com"
    )
    assert (
        normalize_openai_base_url(
            "https://api.deepseek.com/v1/chat/completions"
        )
        == "https://api.deepseek.com/v1"
    )


def test_search_tool_returns_products_and_tracks_recommendations() -> None:
    config = LLMConfig(
        base_url="https://api.deepseek.com",
        api_key="test-key",
        model="deepseek-flash",
        system_prompt="test prompt",
    )
    agent_context = ShoppingAgentContext(mall=MockMallGateway())
    search_tool = create_tools(agent_context, config)[0]
    tool_context = ToolContext(
        context=agent_context,
        tool_name=search_tool.name,
        tool_call_id="call-1",
        tool_arguments='{"query":"通勤","max_price_cents":30000}',
    )

    output = asyncio.run(
        search_tool.on_invoke_tool(
            tool_context,
            '{"query":"通勤","max_price_cents":30000,"limit":3}',
        )
    )
    products = json.loads(output)

    assert products
    assert all(product["price_cents"] <= 30000 for product in products)
    assert all(product["id"] in agent_context.recommended_products for product in products)


def test_get_product_tool_returns_stock() -> None:
    config = LLMConfig(
        base_url="https://api.deepseek.com",
        api_key="test-key",
        model="deepseek-flash",
        system_prompt="test prompt",
    )
    agent_context = ShoppingAgentContext(mall=MockMallGateway())
    get_tool = create_tools(agent_context, config)[1]
    tool_context = ToolContext(
        context=agent_context,
        tool_name=get_tool.name,
        tool_call_id="call-2",
        tool_arguments='{"product_id":"moon-lamp"}',
    )

    output = asyncio.run(
        get_tool.on_invoke_tool(
            tool_context,
            '{"product_id":"moon-lamp"}',
        )
    )
    product = json.loads(output)[0]

    assert product["name"] == "月影桌面灯"
    assert product["stock"] == 12


def test_react_loop_calls_mall_tool_and_streams_recommendation() -> None:
    config = LLMConfig(
        base_url="https://api.deepseek.com",
        api_key="test-key",
        model="deepseek-flash",
        max_turns=4,
        prompt_file=str(PROMPT_PATH),
    )
    model = ScriptedModel(
        [
            [
                function_call(
                    "search_products",
                    {"query": "通勤", "max_price_cents": 30000, "limit": 3},
                    call_id="call-search",
                )
            ],
            [assistant_message("我推荐这几件通勤好物。")],
        ]
    )

    async def collect_events() -> list[dict[str, object]]:
        return [
            event
            async for event in stream_agent_reply(
                [ConversationMessage(role="user", content="推荐 300 元内通勤好物")],
                config,
                MockMallGateway(),
                model_override=model,
            )
        ]

    events = asyncio.run(collect_events())

    event_types = [event["type"] for event in events]
    assert "tool_started" in event_types
    assert "tool_completed" in event_types
    assert "recommendations" in event_types
    assert "delta" in event_types
    assert event_types[-1] == "done"
    recommendations = next(
        event["products"]
        for event in events
        if event["type"] == "recommendations"
    )
    assert recommendations
    assert all(product["price_cents"] <= 30000 for product in recommendations)
    assert model.last_call is not None
    assert [tool.name for tool in model.last_call.tools] == [
        "search_products",
        "get_product",
    ]
    assert model.first_call is not None
    assert "小牛导购" in (model.first_call.system_instructions or "")
    assert "最终推荐最多保留 3 件" in (
        model.first_call.system_instructions or ""
    )
