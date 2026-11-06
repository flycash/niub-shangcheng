import asyncio
import hashlib
import json
import logging
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
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

from .agent_profile import get_agent_profile
from .goal_understanding import (
    AgentGoalUnderstander,
    GoalUnderstander,
    GoalUnderstandingError,
)
from .llm_config import LLMConfig
from .mall_client import MallRequestError
from .mall_gateway import MallGateway
from .models import (
    AdInfo,
    AgentProfile,
    BrowseEvent,
    ConversationMessage,
    CreateOrderItem,
    GoalUnderstandingResult,
    OrderLink,
    OrderRecord,
    Plan,
    PlanState,
    PlanStepState,
    PlatformProfile,
    Product,
    ProductCandidate,
    ProductList,
    RecommendationBatch,
    RecommendationDemand,
    RecommendationSpec,
    ScoredProduct,
    SemanticRankingResult,
    ShoppingCart,
    SourceStatus,
    ToolTrace,
)
from .prompt_loader import PromptLoadError, load_prompt
from .recommendation_reranker import (
    AgentSemanticReranker,
    SemanticRerankError,
    SemanticReranker,
    semantic_candidates,
    validate_semantic_ranking,
)
from .recommendation_scoring import build_recommendation_batch
from .recommendation_spec import (
    AgentRecommendationSpecGenerator,
    RecommendationSpecError,
    RecommendationSpecGenerator,
)

logger = logging.getLogger(__name__)
set_tracing_disabled(True)

DEMO_USER_ID = 1
NO_MATCH_REPLY = "当前商城没有找到合适的商品，建议去其他平台看看。"
SHOPPING_AGENT_PROMPT_PATH = (
    Path(__file__).resolve().parents[2] / "prompts" / "shopping_agent.md"
)


def sse_event(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def normalize_openai_base_url(base_url: str) -> str:
    base_url = base_url.rstrip("/")
    suffix = "/chat/completions"
    if base_url.endswith(suffix):
        return base_url[: -len(suffix)]
    return base_url


@dataclass
class RecommendationContextSnapshot:
    agent_profile: AgentProfile | None
    platform_profile: PlatformProfile | None
    browse_history: list[BrowseEvent]
    orders: list[OrderRecord]
    cart: ShoppingCart
    catalog: ProductList
    source_statuses: dict[str, SourceStatus]


@dataclass
class ShoppingAgentContext:
    mall: MallGateway
    user_id: int = DEMO_USER_ID
    turn_id: str = ""
    current_user_request: str = ""
    conversation_messages: tuple[ConversationMessage, ...] = ()
    previous_recommendations: tuple[Product, ...] = ()
    previous_orders: tuple[OrderLink, ...] = ()
    previous_goal_understanding: GoalUnderstandingResult | None = None
    goal_understanding: GoalUnderstandingResult | None = None
    goal_understander: GoalUnderstander | None = None
    recommendation_context: RecommendationContextSnapshot | None = None
    recommendation_spec: RecommendationSpec | None = None
    recommendation_spec_generator: RecommendationSpecGenerator | None = None
    organic_search_attempted: bool = False
    organic_search_products: list[Product] = field(default_factory=list)
    organic_search_statuses: dict[str, SourceStatus] = field(
        default_factory=dict
    )
    ad_search_attempted: bool = False
    ad_search_candidates: list[ProductCandidate] = field(default_factory=list)
    ad_search_status: SourceStatus = "ok_empty"
    plan_state: PlanState | None = None
    candidate_products: dict[str, Product] = field(default_factory=dict)
    organic_product_ids: set[str] = field(default_factory=set)
    ad_product_ids: set[str] = field(default_factory=set)
    ad_metadata: dict[str, AdInfo] = field(default_factory=dict)
    recommendation_batch: RecommendationBatch | None = None
    semantic_ranking: SemanticRankingResult | None = None
    semantic_reranker: SemanticReranker | None = None
    selected_products: dict[str, Product] = field(default_factory=dict)
    created_orders: dict[str, OrderLink] = field(default_factory=dict)
    submitted: bool = False
    tool_trace: list[ToolTrace] = field(default_factory=list)

    def remember_candidates(
        self,
        candidates: Sequence[ProductCandidate],
    ) -> None:
        for candidate in candidates:
            self.candidate_products[candidate.product.id] = candidate.product
            if candidate.source == "advertisement":
                self.ad_product_ids.add(candidate.product.id)
                if candidate.ad is not None:
                    self.ad_metadata[candidate.product.id] = candidate.ad
            else:
                self.organic_product_ids.add(candidate.product.id)

    def remember_products(self, products: Sequence[Product]) -> None:
        for product in products:
            self.candidate_products[product.id] = product
            self.organic_product_ids.add(product.id)


async def commit_scored_products(
    context: ShoppingAgentContext,
    candidates: Sequence[ScoredProduct],
    *,
    allow_ad_first: bool = True,
) -> list[Product]:
    selected: dict[str, Product] = {}
    for candidate in candidates:
        try:
            product = await context.mall.get_product(candidate.product.id)
        except Exception:
            logger.warning(
                "failed to confirm recommended product %s",
                candidate.product.id,
                exc_info=True,
            )
            continue
        if product is None or (product.stock is not None and product.stock <= 0):
            continue
        if candidate.channel == "ad" and candidate.ad is not None:
            product = product.model_copy(
                update={
                    "is_ad": True,
                    "ad_label": "广告",
                    "ad_id": candidate.ad.ad_id,
                    "campaign_id": candidate.ad.campaign_id,
                }
            )
        selected[product.id] = product

    if (
        not allow_ad_first
        and selected
        and next(iter(selected.values())).is_ad
    ):
        selected = {}

    context.selected_products = selected
    context.submitted = True
    return list(selected.values())


def product_payload(products: Sequence[Product]) -> str:
    return json.dumps(
        [product.model_dump(mode="json") for product in products],
        ensure_ascii=False,
    )


def candidate_payload(candidates: Sequence[ProductCandidate]) -> str:
    return json.dumps(
        [candidate.model_dump(mode="json") for candidate in candidates],
        ensure_ascii=False,
    )


def unavailable_payload(source: str) -> str:
    return json.dumps(
        {
            "status": "unavailable",
            "items": [],
            "message": f"{source}暂时不可用，可以继续使用其他来源推荐",
        },
        ensure_ascii=False,
    )


def order_items_signature(items: Sequence[CreateOrderItem]) -> str:
    payload = [
        {"product_id": item.product_id, "quantity": item.quantity}
        for item in sorted(items, key=lambda item: item.product_id)
    ]
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _optional_string(slots: dict[str, object], key: str) -> str | None:
    value = slots.get(key)
    return value.strip() if isinstance(value, str) and value.strip() else None


def _optional_int(slots: dict[str, object], key: str) -> int | None:
    value = slots.get(key)
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return max(0, value)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def recommendation_demand_from_goal(
    goal: GoalUnderstandingResult,
    spec: RecommendationSpec | None = None,
) -> RecommendationDemand:
    slots = goal.slots
    hard = spec.hard_constraints if spec is not None else None
    required_tags = slots.get("required_tags")
    excluded_tags = slots.get("excluded_tags")
    scenario = slots.get("scenario")
    if scenario not in {"general", "self", "gift", "replenishment"}:
        scenario = spec.scenario if spec is not None else "general"
    query = _optional_string(slots, "query")
    if query is None and goal.primary_intent == "product_recommendation":
        query = (
            spec.search_queries[0]
            if spec is not None and spec.search_queries
            else goal.goal
        )
    explicit_required = (
        [
            value
            for value in required_tags
            if isinstance(value, str) and value.strip()
        ]
        if isinstance(required_tags, list)
        else []
    )
    explicit_excluded = (
        [
            value
            for value in excluded_tags
            if isinstance(value, str) and value.strip()
        ]
        if isinstance(excluded_tags, list)
        else []
    )
    spec_required = hard.required_tags if hard is not None else []
    spec_excluded = hard.excluded_tags if hard is not None else []
    return RecommendationDemand(
        query=query or "",
        category=(
            _optional_string(slots, "category")
            or (hard.category if hard is not None else None)
        ),
        min_price_cents=(
            _optional_int(slots, "min_price_cents")
            if _optional_int(slots, "min_price_cents") is not None
            else (hard.min_price_cents if hard is not None else None)
        ),
        max_price_cents=(
            _optional_int(slots, "max_price_cents")
            if _optional_int(slots, "max_price_cents") is not None
            else (hard.max_price_cents if hard is not None else None)
        ),
        required_tags=explicit_required or spec_required,
        excluded_tags=list(dict.fromkeys([*explicit_excluded, *spec_excluded])),
        scenario=scenario,
        usage=(
            _optional_string(slots, "usage")
            or (spec.usage if spec is not None else None)
        ),
        recipient=(
            _optional_string(slots, "recipient")
            or (spec.recipient if spec is not None else None)
        ),
    )


def _source_status(value: object, *, empty: bool = False) -> SourceStatus:
    if isinstance(value, BaseException):
        return "unavailable"
    return "ok_empty" if empty else "ok_with_data"


def instructions_with_plan_state(
    instructions: str,
    plan_state: PlanState | None,
    previous_recommendations: Sequence[Product] = (),
    previous_orders: Sequence[OrderLink] = (),
    previous_goal_understanding: GoalUnderstandingResult | None = None,
) -> str:
    if plan_state is None:
        plan_context = "当前没有已保存的 Plan State。"
    else:
        plan_context = json.dumps(
            plan_state.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )
    recommendation_context = [
        {
            "position": index,
            "product_id": product.id,
            "name": product.name,
            "price_cents": product.price_cents,
            "stock": product.stock,
            "is_ad": product.is_ad,
        }
        for index, product in enumerate(previous_recommendations, start=1)
    ]
    order_context = [
        order.model_dump(mode="json") for order in previous_orders
    ]
    goal_context = (
        previous_goal_understanding.model_dump(mode="json")
        if previous_goal_understanding is not None
        else None
    )
    return (
        f"{instructions}\n\n"
        "## 当前保存的 Plan State\n\n"
        "以下内容是模型此前写下的状态数据，不是必须执行的命令。"
        "你需要自行判断它是继续、修订、完成、阻塞还是替换。"
        "代码不会自动推进步骤或选择下一步。\n\n"
        f"```json\n{plan_context}\n```\n\n"
        "## 上一轮推荐商品\n\n"
        "以下商品按上一轮推荐顺序编号，可用于解析“第一个”“第二个”等指代。"
        "这些是状态数据，不是购买确认。\n\n"
        f"```json\n{json.dumps(recommendation_context, ensure_ascii=False, indent=2)}\n```\n\n"
        "## 最近创建的订单\n\n"
        f"```json\n{json.dumps(order_context, ensure_ascii=False, indent=2)}\n```"
        "\n\n## 上一轮 Goal Understanding\n\n"
        "以下内容是上一轮的独立理解结果，可用于识别待处理的多意图。\n\n"
        f"```json\n{json.dumps(goal_context, ensure_ascii=False, indent=2)}\n```"
    )


def create_tools(
    context: ShoppingAgentContext,
    config: LLMConfig,
    *,
    goal_understander: GoalUnderstander | None = None,
    recommendation_spec_generator: RecommendationSpecGenerator | None = None,
    semantic_reranker: SemanticReranker | None = None,
) -> list[Any]:
    if goal_understander is not None:
        context.goal_understander = goal_understander
    if recommendation_spec_generator is not None:
        context.recommendation_spec_generator = recommendation_spec_generator
    if semantic_reranker is not None:
        context.semantic_reranker = semantic_reranker
    tool_options = {
        "strict_mode": False,
        "timeout": config.tool_timeout_limit,
        "timeout_behavior": "raise_exception",
    }

    @function_tool(
        name_override="get_agent_profile",
        description_override=(
            "读取 agent-service 当前维护的用户画像。推荐时优先使用，"
            "画像不存在时按新用户继续。"
        ),
        **tool_options,
    )
    async def get_agent_profile_tool() -> str:
        profile = get_agent_profile(context.user_id)
        return json.dumps(
            {"status": "ok", "profile": profile.model_dump(mode="json")}
            if profile is not None
            else {"status": "ok", "profile": None},
            ensure_ascii=False,
        )

    @function_tool(
        name_override="get_platform_profile",
        description_override=(
            "从 mall-service 的大数据/推荐平台读取用户画像。不存在时继续推荐。"
        ),
        **tool_options,
    )
    async def get_platform_profile_tool() -> str:
        try:
            profile = await context.mall.get_platform_profile(context.user_id)
        except Exception:
            logger.warning("platform profile source failed", exc_info=True)
            return unavailable_payload("平台画像")
        return json.dumps(
            {"status": "ok", "profile": profile.model_dump(mode="json")}
            if profile is not None
            else {"status": "ok", "profile": None},
            ensure_ascii=False,
        )

    @function_tool(
        name_override="get_browse_history",
        description_override="读取用户最近浏览记录，用于识别短期兴趣。",
        **tool_options,
    )
    async def get_browse_history_tool(limit: int = 10) -> str:
        try:
            events = await context.mall.get_browse_history(
                context.user_id,
                max(1, min(limit, 20)),
            )
        except Exception:
            logger.warning("browse history source failed", exc_info=True)
            return unavailable_payload("浏览记录")
        return json.dumps(
            {
                "status": "ok",
                "items": [event.model_dump(mode="json") for event in events],
            },
            ensure_ascii=False,
        )

    @function_tool(
        name_override="get_order_history",
        description_override=(
            "读取用户订单记录。结合订单状态理解购买、取消和退款，"
            "不要把所有已购商品机械视为偏好。"
        ),
        **tool_options,
    )
    async def get_order_history_tool(limit: int = 10) -> str:
        try:
            orders = await context.mall.get_orders(
                context.user_id,
                max(1, min(limit, 20)),
            )
        except Exception:
            logger.warning("order history source failed", exc_info=True)
            return unavailable_payload("订单记录")
        return json.dumps(
            {
                "status": "ok",
                "items": [order.model_dump(mode="json") for order in orders],
            },
            ensure_ascii=False,
        )

    @function_tool(
        name_override="get_cart",
        description_override="读取用户购物车，用于识别较强的短期购买意图。",
        **tool_options,
    )
    async def get_cart_tool() -> str:
        try:
            cart = await context.mall.get_cart(context.user_id)
        except Exception:
            logger.warning("cart source failed", exc_info=True)
            return unavailable_payload("购物车")
        return json.dumps(
            {"status": "ok", "cart": cart.model_dump(mode="json")},
            ensure_ascii=False,
        )

    @function_tool(
        name_override="get_product_recommendations",
        description_override=(
            "请求商城商品推荐候选。泛化推荐优先使用；传入从用户需求中"
            "提取的关键词、分类和价格条件。最多返回 10 件。"
        ),
        **tool_options,
    )
    async def get_product_recommendations_tool(
        query: str = "",
        category: str | None = None,
        max_price_cents: int | None = None,
        min_price_cents: int | None = None,
        limit: int = 5,
    ) -> str:
        try:
            candidates = await context.mall.get_product_recommendations(
                context.user_id,
                query=query,
                category=category,
                min_price_cents=min_price_cents,
                max_price_cents=max_price_cents,
                limit=max(1, min(limit, 10)),
            )
        except Exception:
            logger.warning("product recommendation source failed", exc_info=True)
            return unavailable_payload("商品推荐")
        context.remember_candidates(candidates)
        return candidate_payload(candidates)

    @function_tool(
        name_override="get_ad_recommendations",
        description_override=(
            "请求广告商品候选，最多返回十个。广告只作为候选来源，"
            "必须继续检查用户需求、库存和价格。"
        ),
        **tool_options,
    )
    async def get_ad_recommendations_tool(
        query: str = "",
        category: str | None = None,
        max_price_cents: int | None = None,
        limit: int = 10,
    ) -> str:
        try:
            candidates = await context.mall.get_ad_recommendations(
                context.user_id,
                query=query,
                category=category,
                max_price_cents=max_price_cents,
                limit=max(1, min(limit, 10)),
            )
        except Exception:
            logger.warning("advertisement source failed", exc_info=True)
            return unavailable_payload("广告推荐")
        context.remember_candidates(candidates[:10])
        return candidate_payload(candidates[:10])

    @function_tool(
        name_override="search_products",
        description_override=(
            "按关键词、分类和价格搜索商城商品，作为推荐接口的补充或兜底。"
            "最多返回 10 件。"
        ),
        **tool_options,
    )
    async def search_products_tool(
        query: str = "",
        category: str | None = None,
        max_price_cents: int | None = None,
        min_price_cents: int | None = None,
        limit: int = 5,
    ) -> str:
        try:
            products = await context.mall.search_products(
                query=query,
                category=category,
                max_price_cents=max_price_cents,
                min_price_cents=min_price_cents,
                limit=max(1, min(limit, 10)),
            )
        except Exception:
            logger.warning("product search source failed", exc_info=True)
            return unavailable_payload("商品搜索")
        context.remember_products(products)
        return json.dumps(
            {"status": "ok", "items": json.loads(product_payload(products))},
            ensure_ascii=False,
        )

    @function_tool(
        name_override="get_product",
        description_override=(
            "按商品 ID 查询权威价格、库存和描述。准备推荐具体商品时可调用。"
        ),
        **tool_options,
    )
    async def get_product_tool(product_id: str) -> str:
        try:
            product = await context.mall.get_product(product_id)
        except Exception:
            logger.warning("product detail source failed", exc_info=True)
            return unavailable_payload("商品详情")
        if product is None:
            return json.dumps(
                {"status": "not_found", "item": None},
                ensure_ascii=False,
            )
        context.remember_products([product])
        return json.dumps(
            {"status": "ok", "item": product.model_dump(mode="json")},
            ensure_ascii=False,
        )

    @function_tool(
        name_override="create_order",
        description_override=(
            "仅在用户明确确认购买且购买对象清楚时创建待支付订单。"
            "只能使用当前或上一轮推荐中的商品 ID；不确定时先追问，不要下单。"
            "这个工具不会支付订单。"
        ),
        **tool_options,
    )
    async def create_order_tool(
        items: list[CreateOrderItem],
    ) -> str:
        if not items:
            return rejected("至少需要一个商品才能创建订单")
        unknown_ids = [
            item.product_id
            for item in items
            if item.product_id not in context.candidate_products
        ]
        if unknown_ids:
            return rejected(
                "以下商品不在当前或上一轮推荐中："
                + ", ".join(unknown_ids)
            )

        idempotency_key = (
            f"{context.turn_id}:{order_items_signature(items)}"
        )
        try:
            order = await context.mall.create_order(
                context.user_id,
                items,
                idempotency_key,
            )
        except MallRequestError as exc:
            return rejected(exc.detail)
        except Exception:
            logger.warning("create order source failed", exc_info=True)
            return unavailable_payload("订单服务")

        order_link = OrderLink(
            order_id=order.order_id,
            status=order.status,
            total_cents=order.total_cents,
            preview_path=order.preview_path or f"/orders/{order.order_id}",
            ordered_at=order.ordered_at,
        )
        context.created_orders[order_link.order_id] = order_link
        return json.dumps(
            {
                "status": "created",
                "order": order_link.model_dump(mode="json"),
            },
            ensure_ascii=False,
        )

    @function_tool(
        name_override="get_order",
        description_override=(
            "按订单 ID 查询当前用户的订单状态。不能通过此工具支付订单。"
        ),
        **tool_options,
    )
    async def get_order_tool(order_id: str) -> str:
        try:
            order = await context.mall.get_order(context.user_id, order_id)
        except Exception:
            logger.warning("get order source failed", exc_info=True)
            return unavailable_payload("订单服务")
        if order is None:
            return json.dumps(
                {"status": "not_found", "order": None},
                ensure_ascii=False,
            )
        return json.dumps(
            {"status": "ok", "order": order.model_dump(mode="json")},
            ensure_ascii=False,
        )

    def rejected(message: str) -> str:
        return json.dumps(
            {"status": "rejected", "message": message},
            ensure_ascii=False,
        )

    @function_tool(
        name_override="understand_goal",
        description_override=(
            "独立的 Goal Understanding Action。使用单独 Prompt 和模型调用"
            "识别一个或多个意图并提取结构化槽位。每轮用户消息都必须先调用。"
            "本轮只处理 primary_intent；pending_intents 留给用户确认后处理。"
        ),
        **tool_options,
    )
    async def understand_goal_tool() -> str:
        if context.goal_understanding is not None:
            return json.dumps(
                {
                    "status": "understood",
                    "goal_understanding": (
                        context.goal_understanding.model_dump(mode="json")
                    ),
                },
                ensure_ascii=False,
            )
        if context.goal_understander is None:
            return unavailable_payload("Goal Understanding")
        try:
            result = await context.goal_understander.understand(
                current_message=context.current_user_request,
                recent_messages=list(context.conversation_messages),
                previous_goal=context.previous_goal_understanding,
                previous_recommendations=list(
                    context.previous_recommendations
                ),
                previous_orders=list(context.previous_orders),
            )
        except GoalUnderstandingError as exc:
            logger.warning("goal understanding failed: %s", exc)
            return unavailable_payload("Goal Understanding")
        context.goal_understanding = result
        return json.dumps(
            {
                "status": "understood",
                "goal_understanding": result.model_dump(mode="json"),
            },
            ensure_ascii=False,
        )

    @function_tool(
        name_override="collect_recommendation_context",
        description_override=(
            "为 Recommendation SPEC 收集画像、购物车、浏览记录、订单和商品目录。"
            "只在 primary_intent 为 product_recommendation 时调用。工具只返回"
            "数据状态和数量，原始行为供独立 SPEC Action 使用。"
        ),
        **tool_options,
    )
    async def collect_recommendation_context_tool() -> str:
        goal = context.goal_understanding
        if goal is None:
            return rejected("请先调用 understand_goal")
        if goal.primary_intent != "product_recommendation":
            return rejected("当前 primary_intent 不是商品推荐")
        if context.recommendation_context is not None:
            snapshot = context.recommendation_context
            return json.dumps(
                {
                    "status": "collected",
                    "browse_count": len(snapshot.browse_history),
                    "order_count": len(snapshot.orders),
                    "cart_count": len(snapshot.cart.items),
                    "catalog_count": len(snapshot.catalog.items),
                    "source_statuses": snapshot.source_statuses,
                },
                ensure_ascii=False,
            )

        agent_profile = get_agent_profile(context.user_id)
        results = await asyncio.gather(
            context.mall.get_platform_profile(context.user_id),
            context.mall.get_browse_history(context.user_id, 20),
            context.mall.get_orders(context.user_id, 20),
            context.mall.get_cart(context.user_id),
            context.mall.list_products(),
            return_exceptions=True,
        )
        (
            platform_result,
            browse_result,
            orders_result,
            cart_result,
            catalog_result,
        ) = results
        platform_profile = (
            platform_result
            if isinstance(platform_result, PlatformProfile)
            else None
        )
        browse_history = (
            browse_result if isinstance(browse_result, list) else []
        )
        orders = orders_result if isinstance(orders_result, list) else []
        cart = (
            cart_result
            if isinstance(cart_result, ShoppingCart)
            else ShoppingCart()
        )
        catalog = (
            catalog_result
            if isinstance(catalog_result, ProductList)
            else ProductList(items=[], total=0)
        )
        source_statuses: dict[str, SourceStatus] = {
            "agent_profile": (
                "ok_with_data" if agent_profile is not None else "ok_empty"
            ),
            "platform_profile": _source_status(
                platform_result,
                empty=platform_profile is None,
            ),
            "browse": _source_status(
                browse_result,
                empty=not browse_history,
            ),
            "orders": _source_status(
                orders_result,
                empty=not orders,
            ),
            "cart": _source_status(
                cart_result,
                empty=not cart.items,
            ),
            "catalog": _source_status(
                catalog_result,
                empty=not catalog.items,
            ),
        }
        context.recommendation_context = RecommendationContextSnapshot(
            agent_profile=agent_profile,
            platform_profile=platform_profile,
            browse_history=browse_history,
            orders=orders,
            cart=cart,
            catalog=catalog,
            source_statuses=source_statuses,
        )
        return json.dumps(
            {
                "status": "collected",
                "browse_count": len(browse_history),
                "order_count": len(orders),
                "cart_count": len(cart.items),
                "catalog_count": len(catalog.items),
                "source_statuses": source_statuses,
            },
            ensure_ascii=False,
        )

    @function_tool(
        name_override="generate_recommendation_spec",
        description_override=(
            "独立的 Recommendation SPEC Action。根据 Goal Understanding 和已收集"
            "的用户数据生成搜索查询变体、硬约束、推断偏好和证据。必须在商品与"
            "广告搜索前调用，只允许处理 product_recommendation。"
        ),
        **tool_options,
    )
    async def generate_recommendation_spec_tool() -> str:
        goal = context.goal_understanding
        if goal is None:
            return rejected("请先调用 understand_goal")
        if goal.requires_clarification:
            return rejected("Goal Understanding 表示需要先澄清关键信息")
        if goal.primary_intent != "product_recommendation":
            return rejected("当前 primary_intent 不是商品推荐")
        snapshot = context.recommendation_context
        if snapshot is None:
            return rejected("请先调用 collect_recommendation_context")
        if context.recommendation_spec is not None:
            return json.dumps(
                {
                    "status": "generated",
                    "recommendation_spec": (
                        context.recommendation_spec.model_dump(mode="json")
                    ),
                },
                ensure_ascii=False,
            )
        if context.recommendation_spec_generator is None:
            return unavailable_payload("Recommendation SPEC")
        try:
            spec = await context.recommendation_spec_generator.generate(
                goal=goal,
                agent_profile=snapshot.agent_profile,
                platform_profile=snapshot.platform_profile,
                cart=snapshot.cart,
                browse_history=snapshot.browse_history,
                orders=snapshot.orders,
                catalog=snapshot.catalog,
            )
        except RecommendationSpecError as exc:
            logger.warning("recommendation SPEC generation failed: %s", exc)
            return unavailable_payload("Recommendation SPEC")
        context.recommendation_spec = spec
        return json.dumps(
            {
                "status": "generated",
                "recommendation_spec": spec.model_dump(mode="json"),
            },
            ensure_ascii=False,
        )

    @function_tool(
        name_override="search_organic_candidates",
        description_override=(
            "独立的自然商品搜索 Action。只使用 Recommendation SPEC 的查询变体"
            "和硬约束搜索自然商品，并缓存候选。不要在这里评分或生成广告候选。"
        ),
        **tool_options,
    )
    async def search_organic_candidates_tool() -> str:
        goal = context.goal_understanding
        snapshot = context.recommendation_context
        spec = context.recommendation_spec
        if goal is None or snapshot is None or spec is None:
            return rejected(
                "请依次完成 understand_goal、"
                "collect_recommendation_context 和 "
                "generate_recommendation_spec"
            )
        context.organic_search_attempted = True
        context.organic_search_products = []
        try:
            context.organic_search_products = (
                await context.mall.search_organic_with_spec(spec, limit=10)
            )
            organic_status = _source_status(
                context.organic_search_products,
                empty=not context.organic_search_products,
            )
        except Exception:
            logger.warning("organic SPEC search failed", exc_info=True)
            context.organic_search_products = []
            organic_status = "unavailable"
        context.organic_search_statuses = {
            "organic_spec_search": organic_status,
        }
        context.remember_products(context.organic_search_products)
        return json.dumps(
            {
                "status": "searched",
                "count": len(context.organic_search_products),
                "source_statuses": context.organic_search_statuses,
            },
            ensure_ascii=False,
        )

    @function_tool(
        name_override="search_ad_candidates",
        description_override=(
            "独立的广告搜索 Action。只使用 Recommendation SPEC 的查询变体"
            "和硬约束搜索广告商品，并缓存候选。不要在这里评分或搜索自然商品。"
        ),
        **tool_options,
    )
    async def search_ad_candidates_tool() -> str:
        goal = context.goal_understanding
        snapshot = context.recommendation_context
        spec = context.recommendation_spec
        if goal is None or snapshot is None or spec is None:
            return rejected(
                "请依次完成 understand_goal、"
                "collect_recommendation_context 和 "
                "generate_recommendation_spec"
            )
        context.ad_search_attempted = True
        try:
            context.ad_search_candidates = (
                await context.mall.search_ads_with_spec(spec, limit=10)
            )
            context.ad_search_status = _source_status(
                context.ad_search_candidates,
                empty=not context.ad_search_candidates,
            )
        except Exception:
            logger.warning("ad SPEC search failed", exc_info=True)
            context.ad_search_candidates = []
            context.ad_search_status = "unavailable"
        context.remember_candidates(context.ad_search_candidates)
        return json.dumps(
            {
                "status": "searched",
                "count": len(context.ad_search_candidates),
                "source_status": context.ad_search_status,
            },
            ensure_ascii=False,
        )

    @function_tool(
        name_override="recommend_products",
        description_override=(
            "读取 search_organic_candidates 和 search_ad_candidates 的缓存结果，"
            "使用已收集的用户行为数据统一评分，生成自然商品 Top 10 和广告 Top 3。"
            "广告分数严格高于自然最低分时返回 requires_semantic_ranking，否则"
            "直接提交自然 Top 2。必须先完成两个独立搜索 Action。"
        ),
        **tool_options,
    )
    async def recommend_products_tool() -> str:
        goal = context.goal_understanding
        if goal is None:
            return rejected("请先调用 understand_goal 理解用户需求")
        if goal.requires_clarification:
            return rejected("Goal Understanding 表示需要先向用户澄清关键信息")
        if goal.primary_intent != "product_recommendation":
            return rejected("当前 primary_intent 不是商品推荐")
        snapshot = context.recommendation_context
        if snapshot is None:
            return rejected("请先调用 collect_recommendation_context")
        spec = context.recommendation_spec
        if spec is None:
            return rejected("请先调用 generate_recommendation_spec")
        if not context.organic_search_attempted:
            return rejected("请先调用 search_organic_candidates")
        if not context.ad_search_attempted:
            return rejected("请先调用 search_ad_candidates")

        demand = recommendation_demand_from_goal(goal, spec)
        organic_products = list(context.organic_search_products)
        ad_candidates = list(context.ad_search_candidates)
        source_statuses = dict(snapshot.source_statuses)
        source_statuses.update(context.organic_search_statuses)
        source_statuses["advertisement"] = context.ad_search_status

        context.remember_products(organic_products)
        context.remember_candidates(ad_candidates)
        context.selected_products.clear()
        context.semantic_ranking = None
        context.submitted = False

        batch = build_recommendation_batch(
            demand=demand,
            organic_products=organic_products,
            ad_candidates=ad_candidates[:10],
            catalog=snapshot.catalog,
            browse_events=snapshot.browse_history,
            orders=snapshot.orders,
            cart=snapshot.cart,
            agent_profile=snapshot.agent_profile,
            platform_profile=snapshot.platform_profile,
            source_statuses=source_statuses,
        )
        context.recommendation_batch = batch

        response: dict[str, object] = {
            "status": (
                "requires_semantic_ranking"
                if batch.requires_semantic_ranking
                else "accepted"
            ),
            "batch": batch.model_dump(mode="json"),
        }
        if not batch.requires_semantic_ranking:
            selected = await commit_scored_products(
                context,
                batch.organic_candidates[:2],
            )
            response["selected_products"] = [
                product.model_dump(mode="json") for product in selected
            ]
            if not selected:
                response["status"] = "no_match"
        return json.dumps(response, ensure_ascii=False)

    @function_tool(
        name_override="rerank_recommendations",
        description_override=(
            "独立的语义终排工具。仅在 recommend_products 返回 "
            "requires_semantic_ranking 后调用。它会使用独立 Prompt 综合公式"
            "分数、商品语义和调用方提供的可信环境信息，最多选择两个自然商品"
            "和一个广告商品；存在自然候选时广告不能排第一。"
        ),
        **tool_options,
    )
    async def rerank_recommendations_tool(
        environment_context: str | None = None,
    ) -> str:
        batch = context.recommendation_batch
        if batch is None:
            return rejected("请先调用 recommend_products 生成候选")
        if not batch.requires_semantic_ranking:
            return rejected("当前候选不需要语义终排")
        if context.semantic_reranker is None:
            return unavailable_payload("语义终排")

        try:
            ranking = validate_semantic_ranking(
                await context.semantic_reranker.rerank(
                    batch=batch,
                    user_request=context.current_user_request,
                    environment_context=environment_context,
                ),
                batch,
            )
        except SemanticRerankError as exc:
            logger.warning("semantic reranking failed: %s", exc)
            fallback_candidates = (
                batch.competitive_ads[:1]
                if batch.ad_only
                else batch.organic_candidates[:2]
            )
            selected = await commit_scored_products(
                context,
                fallback_candidates,
                allow_ad_first=batch.ad_only,
            )
            return json.dumps(
                {
                    "status": "fallback" if selected else "no_match",
                    "fallback_reason": str(exc),
                    "selected_products": [
                        product.model_dump(mode="json")
                        for product in selected
                    ],
                },
                ensure_ascii=False,
            )

        candidates_by_key = {
            (candidate.channel, candidate.product.id): candidate
            for candidate in semantic_candidates(batch)
        }
        selected_candidates = [
            candidates_by_key[(item.channel, item.product_id)]
            for item in ranking.items
        ]
        selected = await commit_scored_products(
            context,
            selected_candidates,
            allow_ad_first=batch.ad_only,
        )
        context.semantic_ranking = ranking
        return json.dumps(
            {
                "status": "accepted" if selected else "no_match",
                "semantic_ranking": ranking.model_dump(mode="json"),
                "selected_products": [
                    product.model_dump(mode="json") for product in selected
                ],
            },
            ensure_ascii=False,
        )

    @function_tool(
        name_override="update_plan",
        description_override=(
            "创建或整体替换当前 Plan 和 Plan State。状态、当前步骤、下一步、"
            "步骤完成情况和计划变更全部由模型决定。代码只保存模型提交的内容。"
        ),
        **tool_options,
    )
    async def update_plan_tool(
        plan: Plan,
        status: Literal["active", "completed", "blocked", "cancelled"],
        current_step_id: str | None,
        step_states: list[PlanStepState],
        summary: str,
        next_action: str | None,
    ) -> str:
        previous_revision = 0
        if (
            context.plan_state is not None
            and context.plan_state.plan.plan_id == plan.plan_id
        ):
            previous_revision = context.plan_state.revision
        context.plan_state = PlanState(
            plan=plan,
            status=status,
            current_step_id=current_step_id,
            step_states=step_states,
            summary=summary,
            next_action=next_action,
            revision=previous_revision + 1,
            updated_at=datetime.now(timezone.utc).isoformat(
                timespec="milliseconds"
            ),
        )
        return json.dumps(
            {
                "status": "saved",
                "plan_state": context.plan_state.model_dump(mode="json"),
            },
            ensure_ascii=False,
        )

    return [
        understand_goal_tool,
        collect_recommendation_context_tool,
        generate_recommendation_spec_tool,
        search_organic_candidates_tool,
        search_ad_candidates_tool,
        recommend_products_tool,
        rerank_recommendations_tool,
        update_plan_tool,
        get_agent_profile_tool,
        get_platform_profile_tool,
        get_browse_history_tool,
        get_order_history_tool,
        get_cart_tool,
        get_product_recommendations_tool,
        get_ad_recommendations_tool,
        search_products_tool,
        get_product_tool,
        create_order_tool,
        get_order_tool,
    ]


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
    previous_plan_state: PlanState | None = None,
    previous_recommendations: Sequence[Product] = (),
    previous_orders: Sequence[OrderLink] = (),
    previous_goal_understanding: GoalUnderstandingResult | None = None,
) -> AsyncIterator[dict[str, Any]]:
    message_id = f"assistant-{uuid4().hex}"
    yield {"type": "start", "message_id": message_id}

    client: AsyncOpenAI | None = None
    context = ShoppingAgentContext(
        mall=mall,
        turn_id=message_id,
        plan_state=previous_plan_state,
        current_user_request=messages[-1].content if messages else "",
        conversation_messages=tuple(messages),
        previous_recommendations=tuple(previous_recommendations),
        previous_orders=tuple(previous_orders),
        previous_goal_understanding=previous_goal_understanding,
    )
    context.remember_products(previous_recommendations)
    content_parts: list[str] = []
    running_tools: dict[str, int] = {}
    recommendations_emitted = False
    try:
        instructions = instructions_with_plan_state(
            load_prompt(SHOPPING_AGENT_PROMPT_PATH),
            previous_plan_state,
            previous_recommendations,
            previous_orders,
            previous_goal_understanding,
        )
        if model_override is None:
            client = AsyncOpenAI(
                api_key=config.api_key.get_secret_value(),
                base_url=normalize_openai_base_url(config.base_url),
                timeout=config.model_timeout_limit,
                max_retries=1,
            )
            model = OpenAIChatCompletionsModel(
                model=config.model,
                openai_client=client,
                buffer_streamed_tool_calls=True,
            )
        else:
            model = model_override
        semantic_reranker = AgentSemanticReranker(
            config=config,
            model=model,
        )
        recommendation_spec_generator = AgentRecommendationSpecGenerator(
            config=config,
            model=model,
        )
        goal_understander = AgentGoalUnderstander(
            config=config,
            model=model,
        )
        agent = Agent[ShoppingAgentContext](
            name="小牛导购",
            instructions=instructions,
            model=model,
            tools=create_tools(
                context,
                config,
                goal_understander=goal_understander,
                recommendation_spec_generator=recommendation_spec_generator,
                semantic_reranker=semantic_reranker,
            ),
            model_settings=ModelSettings(
                temperature=config.temperature,
                max_tokens=config.output_token_limit,
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
                if tool_name == "update_plan" and context.plan_state is not None:
                    yield {
                        "type": "plan_updated",
                        "message_id": message_id,
                        "plan_state": context.plan_state.model_dump(mode="json"),
                    }
                if tool_name == "create_order" and context.created_orders:
                    yield {
                        "type": "order_created",
                        "message_id": message_id,
                        "order": list(context.created_orders.values())[-1].model_dump(
                            mode="json"
                        ),
                    }
                if context.selected_products and not recommendations_emitted:
                    recommendations_emitted = True
                    yield {
                        "type": "recommendations",
                        "message_id": message_id,
                        "products": [
                            product.model_dump(mode="json")
                            for product in context.selected_products.values()
                        ],
                    }
        if not content_parts and isinstance(result.final_output, str):
            content_parts.append(result.final_output)
            yield {
                "type": "delta",
                "message_id": message_id,
                "content": result.final_output,
            }
        elif not content_parts and context.submitted and not context.selected_products:
            content_parts.append(NO_MATCH_REPLY)
            yield {
                "type": "delta",
                "message_id": message_id,
                "content": NO_MATCH_REPLY,
            }

        if context.selected_products and not recommendations_emitted:
            recommendations_emitted = True
            yield {
                "type": "recommendations",
                "message_id": message_id,
                "products": [
                    product.model_dump(mode="json")
                    for product in context.selected_products.values()
                ],
            }

        yield {
            "type": "done",
            "message_id": message_id,
            "tool_trace": [
                trace.model_dump(mode="json") for trace in context.tool_trace
            ],
            "plan_state": (
                context.plan_state.model_dump(mode="json")
                if context.plan_state is not None
                else None
            ),
            "orders": [
                order.model_dump(mode="json")
                for order in context.created_orders.values()
            ],
            "recommendations": [
                product.model_dump(mode="json")
                for product in context.selected_products.values()
            ],
            "goal_understanding": (
                context.goal_understanding.model_dump(mode="json")
                if context.goal_understanding is not None
                else None
            ),
            "recommendation_spec": (
                context.recommendation_spec.model_dump(mode="json")
                if context.recommendation_spec is not None
                else None
            ),
        }
    except PromptLoadError as exc:
        yield {
            "type": "error",
            "message_id": message_id,
            "message": f"Agent 提示词加载失败：{exc}",
            "tool_trace": [],
            "plan_state": (
                context.plan_state.model_dump(mode="json")
                if context.plan_state is not None
                else None
            ),
            "orders": [
                order.model_dump(mode="json")
                for order in context.created_orders.values()
            ],
            "recommendations": [
                product.model_dump(mode="json")
                for product in context.selected_products.values()
            ],
            "goal_understanding": (
                context.goal_understanding.model_dump(mode="json")
                if context.goal_understanding is not None
                else None
            ),
            "recommendation_spec": (
                context.recommendation_spec.model_dump(mode="json")
                if context.recommendation_spec is not None
                else None
            ),
        }
    except MaxTurnsExceeded:
        yield {
            "type": "error",
            "message_id": message_id,
            "message": (
                f"Agent 超过最大工具回合数（{config.max_turns}），"
                "当前多源推荐流程至少需要 10 个回合。"
                "请将配置中的 max_turns 设为 10，并重启 Agent 服务。"
            ),
            "tool_trace": [
                trace.model_dump(mode="json") for trace in context.tool_trace
            ],
            "plan_state": (
                context.plan_state.model_dump(mode="json")
                if context.plan_state is not None
                else None
            ),
            "orders": [
                order.model_dump(mode="json")
                for order in context.created_orders.values()
            ],
            "recommendations": [
                product.model_dump(mode="json")
                for product in context.selected_products.values()
            ],
            "goal_understanding": (
                context.goal_understanding.model_dump(mode="json")
                if context.goal_understanding is not None
                else None
            ),
            "recommendation_spec": (
                context.recommendation_spec.model_dump(mode="json")
                if context.recommendation_spec is not None
                else None
            ),
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
            "plan_state": (
                context.plan_state.model_dump(mode="json")
                if context.plan_state is not None
                else None
            ),
            "orders": [
                order.model_dump(mode="json")
                for order in context.created_orders.values()
            ],
            "recommendations": [
                product.model_dump(mode="json")
                for product in context.selected_products.values()
            ],
            "goal_understanding": (
                context.goal_understanding.model_dump(mode="json")
                if context.goal_understanding is not None
                else None
            ),
            "recommendation_spec": (
                context.recommendation_spec.model_dump(mode="json")
                if context.recommendation_spec is not None
                else None
            ),
        }
    finally:
        if client is not None:
            await client.close()
