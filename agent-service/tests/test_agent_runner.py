import asyncio
import json
from pathlib import Path

import httpx
from agents.testing import ScriptedModel, assistant_message, function_call
from agents.tool_context import ToolContext
from mall_service.api import app as mall_app

from agent_service.agent_runner import (
    ShoppingAgentContext,
    create_tools,
    normalize_openai_base_url,
    stream_agent_reply,
)
from agent_service.llm_config import LLMConfig
from agent_service.mall_client import MallClient
from agent_service.models import ConversationMessage, PlanState, Product

PROMPT_PATH = (
    Path(__file__).resolve().parents[1] / "prompts" / "shopping_agent.md"
)


def llm_config() -> LLMConfig:
    return LLMConfig(
        base_url="https://api.deepseek.com",
        api_key="test-key",
        model="deepseek-flash",
        max_turns=10,
        prompt_file=str(PROMPT_PATH),
    )


def mall_client() -> MallClient:
    return MallClient(
        base_url="http://mall.test",
        transport=httpx.ASGITransport(app=mall_app),
    )


def plan_arguments(
    *,
    plan_id: str = "plan-recommendation",
    current_step_id: str = "collect",
    summary: str = "准备收集推荐所需信息",
) -> dict:
    return {
        "plan": {
            "plan_id": plan_id,
            "goal": "为用户生成合适的商品推荐",
            "steps": [
                {
                    "step_id": "collect",
                    "title": "收集用户上下文",
                    "objective": "读取画像、浏览、订单和购物车",
                    "kind": "context",
                    "depends_on": [],
                    "metadata": {},
                },
                {
                    "step_id": "retrieve",
                    "title": "获取商品候选",
                    "objective": "获取自然商品和广告候选",
                    "kind": "retrieval",
                    "depends_on": ["collect"],
                    "metadata": {},
                },
                {
                    "step_id": "submit",
                    "title": "提交最终推荐",
                    "objective": "校验并提交最多三个商品",
                    "kind": "decision",
                    "depends_on": ["retrieve"],
                    "metadata": {},
                },
            ],
        },
        "status": "active",
        "current_step_id": current_step_id,
        "step_states": [
            {
                "step_id": "collect",
                "status": "in_progress"
                if current_step_id == "collect"
                else "completed",
                "note": None,
            },
            {
                "step_id": "retrieve",
                "status": "in_progress"
                if current_step_id == "retrieve"
                else "pending",
                "note": None,
            },
            {
                "step_id": "submit",
                "status": "pending",
                "note": None,
            },
        ],
        "summary": summary,
        "next_action": "继续模型认为最合适的下一步",
    }


def tool_by_name(context: ShoppingAgentContext, name: str):
    return next(
        tool
        for tool in create_tools(context, llm_config())
        if tool.name == name
    )


def invoke_tool(context: ShoppingAgentContext, name: str, arguments: dict):
    tool = tool_by_name(context, name)
    tool_context = ToolContext(
        context=context,
        tool_name=tool.name,
        tool_call_id=f"call-{name}",
        tool_arguments=json.dumps(arguments, ensure_ascii=False),
    )
    return asyncio.run(
        tool.on_invoke_tool(
            tool_context,
            json.dumps(arguments, ensure_ascii=False),
        )
    )


class UnavailableMall:
    async def get_browse_history(self, user_id: int, limit: int = 10):
        raise RuntimeError("mall unavailable")


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


def test_context_tools_read_mall_service_data() -> None:
    context = ShoppingAgentContext(mall=mall_client())

    browse = json.loads(invoke_tool(context, "get_browse_history", {}))
    orders = json.loads(invoke_tool(context, "get_order_history", {}))
    cart = json.loads(invoke_tool(context, "get_cart", {}))
    platform_profile = json.loads(
        invoke_tool(context, "get_platform_profile", {})
    )
    agent_profile = json.loads(invoke_tool(context, "get_agent_profile", {}))

    assert browse["items"][0]["product_id"] == "moon-lamp"
    assert orders["items"][0]["order_id"] == "order-1001"
    assert cart["cart"]["items"][0]["product_id"] == "commuter-backpack"
    assert platform_profile["profile"]["confidence"] == 0.76
    assert agent_profile["profile"]["source"] == "agent_memory"


def test_unavailable_source_returns_structured_status() -> None:
    context = ShoppingAgentContext(mall=UnavailableMall())

    result = json.loads(invoke_tool(context, "get_browse_history", {}))

    assert result["status"] == "unavailable"
    assert result["items"] == []


def test_new_user_context_is_empty_but_tools_continue() -> None:
    context = ShoppingAgentContext(mall=mall_client(), user_id=999)

    browse = json.loads(invoke_tool(context, "get_browse_history", {}))
    orders = json.loads(invoke_tool(context, "get_order_history", {}))
    cart = json.loads(invoke_tool(context, "get_cart", {}))
    profile = json.loads(invoke_tool(context, "get_platform_profile", {}))

    assert browse == {"status": "ok", "items": []}
    assert orders == {"status": "ok", "items": []}
    assert cart["status"] == "ok"
    assert cart["cart"]["items"] == []
    assert profile == {"status": "ok", "profile": None}


def test_update_plan_preserves_model_decisions_without_auto_advancing() -> None:
    context = ShoppingAgentContext(mall=mall_client())

    first = json.loads(
        invoke_tool(context, "update_plan", plan_arguments())
    )
    assert first["status"] == "saved"
    assert context.plan_state is not None
    assert context.plan_state.current_step_id == "collect"
    assert context.plan_state.revision == 1

    invoke_tool(context, "get_browse_history", {})

    assert context.plan_state is not None
    assert context.plan_state.current_step_id == "collect"
    assert context.plan_state.step_states[0].status == "in_progress"

    revised = plan_arguments(
        current_step_id="retrieve",
        summary="模型判断上下文收集完成，切换到召回步骤",
    )
    invoke_tool(context, "update_plan", revised)

    assert context.plan_state is not None
    assert context.plan_state.current_step_id == "retrieve"
    assert context.plan_state.step_states[0].status == "completed"
    assert context.plan_state.step_states[1].status == "in_progress"
    assert context.plan_state.revision == 2


def test_recommendation_and_ad_tools_register_candidates() -> None:
    context = ShoppingAgentContext(mall=mall_client())

    products = json.loads(
        invoke_tool(
            context,
            "get_product_recommendations",
            {"query": "通勤", "limit": 3},
        )
    )
    ads = json.loads(
        invoke_tool(
            context,
            "get_ad_recommendations",
            {"query": "通勤"},
        )
    )

    assert products
    assert all(
        item["product"]["price_cents"] <= 30000 for item in products
    )
    assert all(
        item["product"]["id"] in context.organic_product_ids
        for item in products
    )
    assert len(ads) <= 1
    assert all(
        item["product"]["id"] in context.ad_product_ids for item in ads
    )


def test_get_product_tool_returns_stock() -> None:
    context = ShoppingAgentContext(mall=mall_client())

    result = json.loads(
        invoke_tool(context, "get_product", {"product_id": "moon-lamp"})
    )

    assert result["item"]["name"] == "月影桌面灯"
    assert result["item"]["stock"] == 12
    assert "moon-lamp" in context.organic_product_ids

    missing = json.loads(
        invoke_tool(context, "get_product", {"product_id": "missing"})
    )
    assert missing["status"] == "not_found"


def test_create_order_tool_creates_pending_order_and_returns_preview() -> None:
    context = ShoppingAgentContext(mall=mall_client(), turn_id="turn-order")
    invoke_tool(
        context,
        "get_product_recommendations",
        {"query": "通勤", "limit": 3},
    )

    created = json.loads(
        invoke_tool(
            context,
            "create_order",
            {"items": [{"product_id": "commuter-backpack", "quantity": 1}]},
        )
    )
    repeated = json.loads(
        invoke_tool(
            context,
            "create_order",
            {"items": [{"product_id": "commuter-backpack", "quantity": 1}]},
        )
    )

    assert created["status"] == "created"
    assert created["order"]["status"] == "pending_payment"
    assert created["order"]["preview_path"].startswith("/orders/order-")
    assert repeated["order"]["order_id"] == created["order"]["order_id"]

    fetched = json.loads(
        invoke_tool(
            context,
            "get_order",
            {"order_id": created["order"]["order_id"]},
        )
    )
    assert fetched["status"] == "ok"
    assert fetched["order"]["items"][0]["name"] == "轻旅通勤双肩包"


def test_create_order_rejects_product_outside_known_recommendations() -> None:
    context = ShoppingAgentContext(mall=mall_client(), turn_id="turn-order")

    result = json.loads(
        invoke_tool(
            context,
            "create_order",
            {"items": [{"product_id": "commuter-backpack", "quantity": 1}]},
        )
    )

    assert result["status"] == "rejected"


def test_submit_recommendations_enforces_limits_and_ad_source() -> None:
    context = ShoppingAgentContext(mall=mall_client())
    product_result = json.loads(
        invoke_tool(
            context,
            "get_product_recommendations",
            {"query": "通勤", "limit": 3},
        )
    )
    ad_result = json.loads(
        invoke_tool(context, "get_ad_recommendations", {"query": "通勤"})
    )

    organic_id = product_result[0]["product"]["id"]
    ad_id = ad_result[0]["product"]["id"]
    accepted = json.loads(
        invoke_tool(
            context,
            "submit_recommendations",
            {
                "items": [
                    {
                        "product_id": organic_id,
                        "source": "organic",
                        "reason": "符合通勤需求",
                    },
                    {
                        "product_id": ad_id,
                        "source": "ad",
                        "reason": "广告候选也符合通勤需求",
                    },
                ]
            },
        )
    )
    too_many = json.loads(
        invoke_tool(
            context,
            "submit_recommendations",
            {
                "items": [
                    {
                        "product_id": organic_id,
                        "source": "organic",
                        "reason": "理由一",
                    },
                    {
                        "product_id": organic_id,
                        "source": "organic",
                        "reason": "理由二",
                    },
                    {
                        "product_id": organic_id,
                        "source": "organic",
                        "reason": "理由三",
                    },
                    {
                        "product_id": organic_id,
                        "source": "organic",
                        "reason": "理由四",
                    },
                ]
            },
        )
    )

    assert accepted["status"] == "accepted"
    assert len(context.selected_products) == 2
    assert context.selected_products[ad_id].is_ad is True
    assert context.selected_products[ad_id].ad_label == "广告"
    assert too_many["status"] == "rejected"

    no_match = json.loads(
        invoke_tool(
            context,
            "submit_recommendations",
            {
                "items": [],
                "no_match_reason": "当前商城没有合适商品",
            },
        )
    )
    assert no_match["status"] == "accepted"
    assert context.selected_products == {}


def test_react_loop_loads_sources_and_streams_only_final_selection() -> None:
    model = ScriptedModel(
        [
            [
                function_call(
                    "update_plan",
                    plan_arguments(),
                    call_id="call-plan",
                ),
                function_call("get_agent_profile", {}, call_id="call-agent"),
                function_call("get_platform_profile", {}, call_id="call-platform"),
                function_call("get_browse_history", {}, call_id="call-browse"),
                function_call("get_order_history", {}, call_id="call-orders"),
                function_call("get_cart", {}, call_id="call-cart"),
                function_call(
                    "get_product_recommendations",
                    {"query": "通勤", "max_price_cents": 30000, "limit": 3},
                    call_id="call-products",
                ),
                function_call(
                    "get_ad_recommendations",
                    {"query": "通勤", "max_price_cents": 30000},
                    call_id="call-ads",
                ),
            ],
            [
                function_call(
                    "submit_recommendations",
                    {
                        "items": [
                            {
                                "product_id": "commuter-backpack",
                                "source": "organic",
                                "reason": "通勤实用且符合预算",
                            },
                            {
                                "product_id": "portable-coffee",
                                "source": "ad",
                                "reason": "轻便，也可作为通勤礼物",
                            },
                        ]
                    },
                    call_id="call-submit",
                )
            ],
            [assistant_message("我综合你的记录，推荐这两件商品。")],
        ]
    )

    async def collect_events() -> list[dict[str, object]]:
        return [
            event
            async for event in stream_agent_reply(
                [ConversationMessage(role="user", content="推荐通勤好物")],
                llm_config(),
                mall_client(),
                model_override=model,
            )
        ]

    events = asyncio.run(collect_events())

    event_types = [event["type"] for event in events]
    assert "tool_started" in event_types
    assert "tool_completed" in event_types
    assert "plan_updated" in event_types
    assert "recommendations" in event_types
    assert "delta" in event_types
    assert event_types[-1] == "done"
    recommendations = next(
        event["products"]
        for event in events
        if event["type"] == "recommendations"
    )
    assert [product["id"] for product in recommendations] == [
        "commuter-backpack",
        "portable-coffee",
    ]
    assert recommendations[1]["is_ad"] is True
    assert recommendations[1]["ad_label"] == "广告"
    plan_state = next(
        event["plan_state"]
        for event in events
        if event["type"] == "done"
    )
    assert plan_state["current_step_id"] == "collect"
    assert plan_state["step_states"][0]["status"] == "in_progress"
    assert plan_state["revision"] == 1
    assert model.last_call is not None
    assert len(model.last_call.tools) == 13
    assert model.first_call is not None
    assert "小牛导购" in (model.first_call.system_instructions or "")
    assert "最终推荐最多三个" in (
        model.first_call.system_instructions or ""
    )


def test_previous_plan_state_is_exposed_to_model_without_forcing_action() -> None:
    previous_plan_state = PlanState.model_validate(
        {
            **plan_arguments(
                plan_id="plan-previous",
                current_step_id="retrieve",
                summary="上一轮已经完成上下文收集",
            ),
            "revision": 3,
            "updated_at": "2026-11-02T12:00:00+00:00",
        }
    )
    model = ScriptedModel([[assistant_message("我会接着处理。")]])

    async def collect_events() -> list[dict[str, object]]:
        return [
            event
            async for event in stream_agent_reply(
                [ConversationMessage(role="user", content="继续")],
                llm_config(),
                mall_client(),
                model_override=model,
                previous_plan_state=previous_plan_state,
            )
        ]

    events = asyncio.run(collect_events())
    done = next(event for event in events if event["type"] == "done")

    assert model.first_call is not None
    instructions = model.first_call.system_instructions or ""
    assert "plan-previous" in instructions
    assert "上一轮已经完成上下文收集" in instructions
    assert "代码不会自动推进步骤" in instructions
    assert done["plan_state"]["revision"] == 3
    assert done["plan_state"]["current_step_id"] == "retrieve"


def test_purchase_turn_uses_previous_recommendation_and_emits_order() -> None:
    previous_product = Product(
        id="canvas-tote",
        name="日常帆布托特包",
        description="厚实帆布与宽肩带。",
        price_cents=6900,
        category="箱包",
        stock=36,
    )
    model = ScriptedModel(
        [
            [
                function_call(
                    "create_order",
                    {"items": [{"product_id": "canvas-tote", "quantity": 1}]},
                    call_id="call-create-order",
                )
            ],
            [assistant_message("订单已创建，请前往订单预览页支付。")],
        ]
    )

    async def collect_events() -> list[dict[str, object]]:
        return [
            event
            async for event in stream_agent_reply(
                [ConversationMessage(role="user", content="第一个我确定买")],
                llm_config(),
                mall_client(),
                model_override=model,
                previous_recommendations=[previous_product],
            )
        ]

    events = asyncio.run(collect_events())

    order_event = next(
        event for event in events if event["type"] == "order_created"
    )
    assert order_event["order"]["status"] == "pending_payment"
    done = next(event for event in events if event["type"] == "done")
    assert done["orders"][0]["order_id"] == order_event["order"]["order_id"]
    assert model.first_call is not None
    instructions = model.first_call.system_instructions or ""
    assert "日常帆布托特包" in instructions
    assert '"position": 1' in instructions
