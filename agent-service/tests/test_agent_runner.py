import asyncio
import json

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
from agent_service.models import (
    AdInfo,
    ConversationMessage,
    PlanState,
    Product,
    RecommendationBatch,
    RecommendationDemand,
    ScoredProduct,
    SemanticRankingItem,
    SemanticRankingResult,
    SourceEvidence,
)
from agent_service.recommendation_reranker import (
    AgentSemanticReranker,
    semantic_candidates,
)

def llm_config() -> LLMConfig:
    return LLMConfig(
        base_url="https://api.deepseek.com",
        api_key="test-key",
        model="deepseek-flash",
        max_turns=10,
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


class StaticSemanticReranker:
    def __init__(self, result: SemanticRankingResult) -> None:
        self.result = result
        self.environment_context: str | None = None

    async def rerank(
        self,
        *,
        batch: RecommendationBatch,
        user_request: str,
        environment_context: str | None = None,
    ) -> SemanticRankingResult:
        self.environment_context = environment_context
        return self.result


def scored_candidate(
    *,
    product_id: str,
    channel: str,
    score: float,
    ad: AdInfo | None = None,
) -> ScoredProduct:
    product = Product(
        id=product_id,
        name=product_id,
        description="",
        price_cents=1000,
        category="箱包",
        stock=10,
        is_ad=ad is not None,
        ad_label="广告" if ad is not None else None,
    )
    return ScoredProduct(
        product=product,
        channel=channel,
        score=score,
        confidence="high",
        evidence=[
            SourceEvidence(
                source="need",
                signal_score=1,
                weighted_points=45,
                reason="符合当前需求",
            )
        ],
        ad=ad,
    )


def recommendation_batch(
    *,
    organic: list[ScoredProduct],
    ads: list[ScoredProduct],
    ad_only: bool = False,
    cutoff: float | None = None,
) -> RecommendationBatch:
    return RecommendationBatch(
        demand=RecommendationDemand(query="通勤"),
        organic_candidates=organic,
        ad_candidates=ads,
        cutoff_score=cutoff,
        competitive_ads=ads,
        requires_semantic_ranking=bool(ads),
        ad_only=ad_only,
        source_statuses={"cart": "ok_with_data"},
        generated_at="2026-11-03T00:00:00+00:00",
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
    assert len(ads) <= 10
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
        "recommend_products",
        {"query": "通勤", "max_price_cents": 30000},
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


def test_recommend_products_formula_path_selects_top_two() -> None:
    context = ShoppingAgentContext(mall=mall_client(), user_id=999)

    result = json.loads(
        invoke_tool(
            context,
            "recommend_products",
            {"query": "家居"},
        )
    )

    assert result["status"] == "accepted"
    assert context.recommendation_batch is not None
    assert context.recommendation_batch.requires_semantic_ranking is False
    assert len(context.selected_products) == 2
    assert all(
        product.is_ad is False
        for product in context.selected_products.values()
    )


def test_recommend_products_returns_no_match_without_eligible_candidates() -> None:
    context = ShoppingAgentContext(mall=mall_client(), user_id=999)

    result = json.loads(
        invoke_tool(
            context,
            "recommend_products",
            {"query": "宠物用品"},
        )
    )

    assert result["status"] == "no_match"
    assert context.submitted is True
    assert context.selected_products == {}


def test_semantic_reranker_selects_organic_before_ad() -> None:
    context = ShoppingAgentContext(mall=mall_client())
    organic = scored_candidate(
        product_id="commuter-backpack",
        channel="organic",
        score=70,
    )
    ad = scored_candidate(
        product_id="portable-coffee",
        channel="ad",
        score=74,
        ad=AdInfo(ad_id="ad-1001", campaign_id="campaign-autumn-2026"),
    )
    reranker = StaticSemanticReranker(
        SemanticRankingResult(
            items=[
                SemanticRankingItem(
                    product_id="commuter-backpack",
                    channel="organic",
                    reason="更符合通勤用途",
                ),
                SemanticRankingItem(
                    product_id="portable-coffee",
                    channel="ad",
                    reason="补充办公室饮用场景",
                ),
            ],
            summary="自然商品优先，广告作为补充",
        )
    )
    context.semantic_reranker = reranker
    context.recommendation_batch = recommendation_batch(
        organic=[organic],
        ads=[ad],
        cutoff=60,
    )

    accepted = json.loads(
        invoke_tool(
            context,
            "rerank_recommendations",
            {"environment_context": "明早通勤，需要轻便"},
        )
    )

    assert accepted["status"] == "accepted"
    assert len(context.selected_products) == 2
    assert list(context.selected_products) == [
        "commuter-backpack",
        "portable-coffee",
    ]
    assert context.selected_products["portable-coffee"].is_ad is True
    assert context.selected_products["portable-coffee"].ad_label == "广告"
    assert reranker.environment_context == "明早通勤，需要轻便"


def test_semantic_reranker_falls_back_when_ad_is_first() -> None:
    context = ShoppingAgentContext(mall=mall_client())
    organic = scored_candidate(
        product_id="commuter-backpack",
        channel="organic",
        score=70,
    )
    ad = scored_candidate(
        product_id="portable-coffee",
        channel="ad",
        score=74,
        ad=AdInfo(ad_id="ad-1001", campaign_id="campaign-autumn-2026"),
    )
    context.semantic_reranker = StaticSemanticReranker(
        SemanticRankingResult(
            items=[
                SemanticRankingItem(
                    product_id="portable-coffee",
                    channel="ad",
                    reason="分数更高",
                ),
                SemanticRankingItem(
                    product_id="commuter-backpack",
                    channel="organic",
                    reason="符合通勤需求",
                ),
            ]
        )
    )
    context.recommendation_batch = recommendation_batch(
        organic=[organic],
        ads=[ad],
        cutoff=60,
    )

    result = json.loads(
        invoke_tool(
            context,
            "rerank_recommendations",
            {},
        )
    )

    assert result["status"] == "fallback"
    assert "cannot be first" in result["fallback_reason"]
    assert list(context.selected_products) == ["commuter-backpack"]


def test_semantic_reranker_allows_ad_only_when_no_organic_candidate() -> None:
    context = ShoppingAgentContext(mall=mall_client())
    ad = scored_candidate(
        product_id="portable-coffee",
        channel="ad",
        score=74,
        ad=AdInfo(ad_id="ad-1001", campaign_id="campaign-autumn-2026"),
    )
    context.semantic_reranker = StaticSemanticReranker(
        SemanticRankingResult(
            items=[
                SemanticRankingItem(
                    product_id="portable-coffee",
                    channel="ad",
                    reason="当前唯一符合需求的候选",
                )
            ]
        )
    )
    context.recommendation_batch = recommendation_batch(
        organic=[],
        ads=[ad],
        ad_only=True,
    )

    result = json.loads(
        invoke_tool(context, "rerank_recommendations", {})
    )

    assert result["status"] == "accepted"
    assert list(context.selected_products) == ["portable-coffee"]
    assert context.selected_products["portable-coffee"].is_ad is True


def test_semantic_reranker_agent_uses_independent_prompt() -> None:
    organic = scored_candidate(
        product_id="commuter-backpack",
        channel="organic",
        score=70,
    )
    ad = scored_candidate(
        product_id="portable-coffee",
        channel="ad",
        score=74,
        ad=AdInfo(ad_id="ad-1001", campaign_id="campaign-autumn-2026"),
    )
    batch = recommendation_batch(
        organic=[organic],
        ads=[ad],
        cutoff=60,
    )
    model = ScriptedModel(
        [
            [
                assistant_message(
                    json.dumps(
                        {
                            "items": [
                                {
                                    "product_id": "commuter-backpack",
                                    "channel": "organic",
                                    "reason": "首选自然商品",
                                },
                                {
                                    "product_id": "portable-coffee",
                                    "channel": "ad",
                                    "reason": "补充办公室场景",
                                },
                            ],
                            "summary": "自然商品优先",
                        },
                        ensure_ascii=False,
                    )
                )
            ]
        ]
    )
    reranker = AgentSemanticReranker(
        config=llm_config(),
        model=model,
    )

    ranking = asyncio.run(
        reranker.rerank(
            batch=batch,
            user_request="推荐通勤好物",
            environment_context="明早有雨",
        )
    )

    assert [item.product_id for item in ranking.items] == [
        "commuter-backpack",
        "portable-coffee",
    ]
    assert model.first_call is not None
    assert "商品推荐语义终排器" in (
        model.first_call.system_instructions or ""
    )


def test_semantic_candidates_are_one_mixed_score_ordered_pool() -> None:
    organic = scored_candidate(
        product_id="commuter-backpack",
        channel="organic",
        score=70,
    )
    ad = scored_candidate(
        product_id="portable-coffee",
        channel="ad",
        score=76,
        ad=AdInfo(ad_id="ad-1001", campaign_id="campaign-autumn-2026"),
    )
    batch = recommendation_batch(
        organic=[organic],
        ads=[ad],
        cutoff=60,
    )

    candidates = semantic_candidates(batch)

    assert [(item.product.id, item.channel) for item in candidates] == [
        ("portable-coffee", "ad"),
        ("commuter-backpack", "organic"),
    ]


def test_react_loop_loads_sources_and_streams_only_final_selection() -> None:
    model = ScriptedModel(
        [
            [
                function_call(
                    "update_plan",
                    plan_arguments(),
                    call_id="call-plan",
                ),
                function_call(
                    "recommend_products",
                    {"query": "通勤", "max_price_cents": 30000},
                    call_id="call-recommend",
                ),
            ],
            [
                function_call(
                    "rerank_recommendations",
                    {"environment_context": "明早需要通勤"},
                    call_id="call-rerank",
                )
            ],
            [
                assistant_message(
                    json.dumps(
                        {
                            "items": [
                                {
                                    "product_id": "commuter-backpack",
                                    "channel": "organic",
                                    "reason": "通勤容量和电脑夹层更合适",
                                },
                                {
                                    "product_id": "travel-bottle",
                                    "channel": "ad",
                                    "reason": "补充通勤饮水场景",
                                },
                            ],
                            "summary": "自然商品优先，广告补充",
                        },
                        ensure_ascii=False,
                    )
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
        "travel-bottle",
    ]
    assert recommendations[1]["is_ad"] is True
    done = next(event for event in events if event["type"] == "done")
    plan_state = done["plan_state"]
    assert plan_state["current_step_id"] == "collect"
    assert plan_state["step_states"][0]["status"] == "in_progress"
    assert plan_state["revision"] == 1
    assert model.last_call is not None
    assert len(model.last_call.tools) == 14
    assert model.first_call is not None
    assert "小牛导购" in (model.first_call.system_instructions or "")
    assert "独立语义终排" in (
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
