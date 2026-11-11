# Codex conversation

## User

我们将推荐流程修改一下：1. 先收集用户的需求，详细需求，你可以根据 spec 来设计一下，看看要收集什么东西；2. 每次收集用户的需求的时候，只收集一项需求，比如说价格区间；3. 允许用户跳过收集需求的步骤，比如用户说“你别管那么多，直接推荐”这种情况就要直接跳过。你先梳理一下项目，输出你对我这个需求的理解。

## Assistant

我先梳理现有推荐流程、相关 spec 和会话状态设计，确认当前入口、需求字段与跳转逻辑；这一轮只做分析，不改代码。

## Activity

    $ pwd && rg --files -g 'AGENTS.md' -g '!node_modules' -g '!dist' -g '!build'
    /Users/mindeng/workspace/niub-shangcheng
    ✗ (1) • 0ms

## Activity

    $ rg --files -g '!node_modules' -g '!dist' -g '!build' | sed -n '1,240p'
    codex-session-11.8.md
    RECOMMENDATION_E2E_TEST.md
    codex-session-2026.11.1.md
    mall-service/src/mall_service/main.py
    mall-service/src/mall_service/search.py
    mall-service/src/mall_service/api.py
    mall-service/src/mall_service/mock_data.py
    mall-service/src/mall_service/orders.py
    mall-service/src/mall_service/__init__.py
    mall-service/src/mall_service/recommendations.py
    mall-service/src/mall_service/models.py
    mall-service/src/mall_service/catalog.py
    mall-service/.env.example
    mall-service/tests/test_mall_api.py
    mall-service/pyproject.toml
    codex-session-11.2.md
    codex-session-11.3.md
    README.md
    TODO.md
    codex-session-11.5.md
    pyproject.toml
    agent-service/src/agent_service/prompt_loader.py
    agent-service/src/agent_service/recommendation_scoring.py
    agent-service/src/agent_service/recommendation_spec.py
    agent-service/src/agent_service/llm_config.py
    agent-service/src/agent_service/main.py
    agent-service/src/agent_service/mall_client.py
    agent-service/src/agent_service/storage.py
    agent-service/src/agent_service/mall_gateway.py
    agent-service/src/agent_service/goal_understanding.py
    agent-service/src/agent_service/chat.py
    agent-service/src/agent_service/api.py
    agent-service/src/agent_service/observability/middleware.py
    agent-service/src/agent_service/observability/serialization.py
    agent-service/src/agent_service/observability/http.py
    agent-service/src/agent_service/observability/context.py
    agent-service/src/agent_service/observability/agents.py
    agent-service/src/agent_service/observability/spans.py
    agent-service/src/agent_service/observability/telemetry.py
    agent-service/src/agent_service/observability/__init__.py
    agent-service/src/agent_service/observability/log_exporters.py
    agent-service/src/agent_service/observability/database.py
    agent-service/src/agent_service/observability/config.py
    agent-service/src/agent_service/observability/metrics.py
    agent-service/src/agent_service/observability/logging.py
    agent-service/src/agent_service/__init__.py
    agent-service/src/agent_service/agent_runner.py
    agent-service/src/agent_service/recommendation_reranker.py
    agent-service/src/agent_service/models.py
    agent-service/src/agent_service/agent_profile.py
    agent-service/.env.example
    agent-service/prompts/recommendation_reranker.md
    agent-service/prompts/recommendation_spec.md
    agent-service/prompts/goal_understanding.md
    agent-service/prompts/shopping_agent.md
    agent-service/tests/test_mall_contract.py
    agent-service/tests/test_prompt_loader.py
    agent-service/tests/test_chat.py
    agent-service/tests/test_storage.py
    agent-service/tests/test_agent_runner.py
    agent-service/tests/test_observability.py
    agent-service/tests/test_recommendation_scoring.py
    agent-service/tests/conftest.py
    agent-service/tests/test_agent_api.py
    agent-service/tests/test_llm_config.py
    agent-service/pyproject.toml
    agent-service/config/llm.example.yaml
    web/next.config.ts
    web/.env.example
    web/tsconfig.json
    web/package.json
    web/components/agent-chat.tsx
    web/components/order-preview.tsx
    web/components/agent-chat.module.css
    web/components/order-preview.module.css
    web/components/storefront.tsx
    web/next-env.d.ts
    web/app/globals.css
    web/app/page.tsx
    web/app/layout.tsx
    uv.lock
    web/pnpm-lock.yaml
    web/app/orders/[orderId]/page.tsx
    web/app/chat/page.tsx
    web/app/products/[productId]/page.tsx
    web/app/products/[productId]/product-detail.module.css
    web/app/api/products/route.ts
    web/app/api/chat/route.ts
    web/app/api/chat/stream/route.ts
    web/app/api/orders/[orderId]/route.ts
    web/app/api/conversations/route.ts
    web/app/api/conversations/[conversationId]/route.ts
    web/app/api/orders/[orderId]/pay/route.ts
    ✓ • 0ms

## Activity

    $ git status --short --branch
    ## main
    ✓ • 0ms

## Assistant

当前仓库是双服务结构：`agent-service` 负责会话、意图与推荐编排，`mall-service` 提供商品检索/推荐能力。接下来我重点核对 recommendation spec、系统提示词、会话状态机和现有测试，判断“逐项收集、可跳过”分别应落在哪一层。

## Activity

    $ sed -n '1,260p' agent-service/src/agent_service/recommendation_spec.py && sed -n '1,260p' agent-service/prompts/recommendation_spec.md
    import json
    import re
    from pathlib import Path
    from typing import Any, Protocol
    
    from agents import Agent, ModelSettings
    from pydantic import ValidationError
    
    from .llm_config import LLMConfig
    from .models import (
        AgentProfile,
        BrowseEvent,
        GoalUnderstandingResult,
        OrderRecord,
        PlatformProfile,
        ProductList,
        RecommendationSpec,
        RecommendationSpecHardConstraints,
        ShoppingCart,
    )
    from .prompt_loader import PromptLoadError, load_prompt
    from .observability.agents import run_observed_action
    
    
    RECOMMENDATION_SPEC_PROMPT_PATH = (
        Path(__file__).resolve().parents[2]
        / "prompts"
        / "recommendation_spec.md"
    )
    
    
    class RecommendationSpecError(Exception):
        """Raised when recommendation SPEC generation fails."""
    
    
    class RecommendationSpecGenerator(Protocol):
        async def generate(
            self,
            *,
            goal: GoalUnderstandingResult,
            agent_profile: AgentProfile | None,
            platform_profile: PlatformProfile | None,
            cart: ShoppingCart,
            browse_history: list[BrowseEvent],
            orders: list[OrderRecord],
            catalog: ProductList,
        ) -> RecommendationSpec: ...
    
    
    def _json_payload(text: str) -> dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end < start:
            raise RecommendationSpecError(
                "recommendation SPEC did not return a JSON object"
            )
        try:
            payload = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise RecommendationSpecError(
                "recommendation SPEC returned invalid JSON"
            ) from exc
        if not isinstance(payload, dict):
            raise RecommendationSpecError(
                "recommendation SPEC JSON must be an object"
            )
        return payload
    
    
    def _string_list(value: object) -> list[str] | None:
        if not isinstance(value, list):
            return None
        return [
            item.strip()
            for item in value
            if isinstance(item, str) and item.strip()
        ]
    
    
    def _non_negative_int(value: object) -> int | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, int) and value >= 0:
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return None
    
    
    def _apply_explicit_goal_constraints(
        spec: RecommendationSpec,
        goal: GoalUnderstandingResult,
    ) -> RecommendationSpec:
        slots = goal.slots
        hard = spec.hard_constraints
        category = slots.get("category")
        min_price = _non_negative_int(slots.get("min_price_cents"))
        max_price = _non_negative_int(slots.get("max_price_cents"))
        required_tags = _string_list(slots.get("required_tags"))
        excluded_tags = _string_list(slots.get("excluded_tags"))
        normalized_hard = RecommendationSpecHardConstraints(
            category=category if isinstance(category, str) and category else hard.category,
            min_price_cents=(
                min_price if min_price is not None else hard.min_price_cents
            ),
            max_price_cents=(
                max_price if max_price is not None else hard.max_price_cents
            ),
            required_tags=(
                required_tags
                if required_tags is not None
                else hard.required_tags
            ),
            excluded_tags=(
                excluded_tags
                if excluded_tags is not None
                else hard.excluded_tags
            ),
        )
        scenario = slots.get("scenario")
        if scenario not in {"general", "self", "gift", "replenishment"}:
            scenario = spec.scenario
        usage = slots.get("usage")
        recipient = slots.get("recipient")
        queries = list(dict.fromkeys(
            query.strip()
            for query in spec.search_queries
            if query.strip()
        ))[:6]
        if not queries:
            queries = [goal.goal]
        return spec.model_copy(
            update={
                "hard_constraints": normalized_hard,
                "search_queries": queries,
                "scenario": scenario,
                "usage": (
                    usage
                    if isinstance(usage, str) and usage
                    else spec.usage
                ),
                "recipient": (
                    recipient
                    if isinstance(recipient, str) and recipient
                    else spec.recipient
                ),
            }
        )
    
    
    class AgentRecommendationSpecGenerator:
        def __init__(self, *, config: LLMConfig, model: Any) -> None:
            self.config = config
            self.model = model
    
        async def generate(
            self,
            *,
            goal: GoalUnderstandingResult,
            agent_profile: AgentProfile | None,
            platform_profile: PlatformProfile | None,
            cart: ShoppingCart,
            browse_history: list[BrowseEvent],
            orders: list[OrderRecord],
            catalog: ProductList,
        ) -> RecommendationSpec:
            try:
                instructions = load_prompt(RECOMMENDATION_SPEC_PROMPT_PATH)
            except PromptLoadError as exc:
                raise RecommendationSpecError(str(exc)) from exc
    
            agent = Agent[Any](
                name="recommendation-spec-generator",
                instructions=instructions,
                model=self.model,
                model_settings=ModelSettings(
                    temperature=self.config.temperature,
                    max_tokens=self.config.output_token_limit,
                ),
            )
            payload = {
                "goal": goal.model_dump(mode="json"),
                "agent_profile": (
                    agent_profile.model_dump(mode="json")
                    if agent_profile is not None
                    else None
                ),
                "platform_profile": (
                    platform_profile.model_dump(mode="json")
                    if platform_profile is not None
                    else None
                ),
                "cart": cart.model_dump(mode="json"),
                "browse_history": [
                    event.model_dump(mode="json")
                    for event in browse_history
                ],
                "orders": [
                    order.model_dump(mode="json")
                    for order in orders
                ],
                "catalog": [
                    {
                        "id": product.id,
                        "name": product.name,
                        "category": product.category,
                        "tags": product.tags,
                        "price_cents": product.price_cents,
                    }
                    for product in catalog.items
                ],
            }
            try:
                result = await run_observed_action(
                    agent,
                    action_name="recommendation_spec",
                    model=str(self.config.model),
                    input=json.dumps(
                        payload,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                    max_turns=1,
                )
            except Exception as exc:
                raise RecommendationSpecError(
                    "recommendation SPEC model call failed: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
    
            if not isinstance(result.final_output, str):
                raise RecommendationSpecError(
                    "recommendation SPEC returned non-text output"
                )
            try:
                spec = RecommendationSpec.model_validate(
                    _json_payload(result.final_output)
                )
            except ValidationError as exc:
                raise RecommendationSpecError(
                    "recommendation SPEC returned invalid data"
                ) from exc
            return _apply_explicit_goal_constraints(spec, goal)
    # Recommendation SPEC Generator
    
    你是商城推荐系统中的独立 Recommendation SPEC Generator。你根据 Goal
    Understanding、用户画像、购物车、浏览记录、订单记录和商品目录，生成一份用于商品
    搜索与广告搜索的推荐规格。
    
    你不负责最终推荐、商品排序、评分或调用搜索服务。
    
    ## 输入
    
    - `goal`：Goal Understanding 结果。
    - `agent_profile`：Agent 维护的长期偏好。
    - `platform_profile`：平台画像。
    - `cart`：购物车及加购时间。
    - `browse_history`：浏览行为、停留时长和时间。
    - `orders`：订单状态和商品。
    - `catalog`：商品 ID、名称、分类和标签，用于理解商品引用。
    
    ## 生成原则
    
    1. 用户当前明确需求永远是最高优先级。
    2. 购物车表示较强短期意图。
    3. 浏览记录和停留时长表示近期兴趣，但不等同于购买需求。
    4. 订单记录表示历史偏好或复购需求，不应机械推荐刚买过且无需补货的商品。
    5. 平台画像和 Agent 画像用于补充长期偏好和冷启动。
    6. 当前显式需求与历史推测冲突时，必须服从显式需求。
    7. 不要把弱推断写成硬约束。
    
    ## 硬约束
    
    `hard_constraints` 只能包含用户明确给出的条件：
    
    - 品类；
    - 最低和最高价格；
    - 必须满足的标签；
    - 明确排除的标签。
    
    历史浏览、订单和画像推测出的偏好应放入 `preferred_categories`、
    `preferred_tags`、`weak_categories` 或 `negative_tags`，不能擅自变成硬约束。
    
    ## 搜索词
    
    生成 1～6 个适合商城关键词搜索的查询变体：
    
    - 保留用户原词；
    - 可以加入同义词、用途和常见商品表达；
    - 查询之间应有实际召回价值，不要机械堆叠；
    - 不得引入没有依据的品牌、价格、库存、销量或促销信息。
    
    ## 证据
    
    `source_evidence` 记录影响本次 SPEC 的主要观察：
    
    - 来源，例如 `goal`、`cart`、`browse`、`order`、`agent_profile`、
      `platform_profile`；
    - 简洁观察；
    - 影响强度：`high`、`medium`、`low`。
    
    不要编造用户没有发生过的行为。
    
    ## 输出
    
    只输出 JSON，不要输出 Markdown 或解释：
    
    ```json
    {
      "goal_summary": "推荐预算 300 元以内、适合通勤并携带电脑的商品",
      "hard_constraints": {
        "category": null,
        "min_price_cents": null,
        "max_price_cents": 30000,
        "required_tags": [],
        "excluded_tags": []
      },
      "preferred_categories": ["箱包"],
      "preferred_tags": ["通勤", "电脑包", "轻便"],
      "weak_categories": ["家居"],
      "negative_tags": [],
      "search_queries": [
        "通勤双肩包",
        "通勤电脑包",
        "轻便通勤包"
      ],
      "scenario": "self",
      "usage": "通勤并携带电脑",
      "recipient": null,
      "source_evidence": [
        {
          "source": "cart",
          "observation": "购物车中有通勤双肩包",
          "influence": "high"
        }
      ],
      "confidence": 0.9,
      "missing_information": []
    }
    ```
    ✓ • 0ms

## Activity

    $ sed -n '1,320p' agent-service/src/agent_service/agent_runner.py && sed -n '1,320p' agent-service/src/agent_service/chat.py
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
    from .observability.agents import (
        AgentTraceSession,
        ObservabilityRunHooks,
        instrument_tools,
    )
    from .observability.serialization import redact_payload
    from .observability.telemetry import get_observability_runtime
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
    recommendation_spec_logger = logging.getLogger(
        "agent_service.observability.tool"
    )
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
    from collections.abc import Sequence
    
    from .models import Product
    
    
    def compose_reply(message: str, products: Sequence[Product]) -> str:
        """Generate a deterministic reply until a model-backed implementation is added."""
        if not products:
            return "商城目录暂时没有可推荐的商品，请稍后再试。"
    
        names = "、".join(product.name for product in products[:3])
        lowered = message.lower()
        if any(greeting in lowered for greeting in ("你好", "hello", "hi")):
            return f"你好，我是商城导购。今天可以先看看 {names}。"
    
        return f"我查看了商城目录，{names} 都值得看看。你更偏好饮品、家居还是文创？"
    ✓ • 0ms

## Activity

    $ sed -n '1,300p' agent-service/prompts/shopping_agent.md && sed -n '1,260p' agent-service/prompts/goal_understanding.md && sed -n '1,260p' agent-service/src/agent_service/goal_understanding.py
    # 小牛导购
    
    你是牛掰商城的购物 Agent“小牛”。你不自行识别意图或提取结构化需求，而是先调用独立的 Goal Understanding Action，再根据其结果调用商城工具。
    
    ## 基本约束
    
    - 推荐、比较、搜索商品，或回答价格、库存和卖点时，必须先调用商城工具。
    - 商品名称、价格、库存、描述、图片和广告身份只能来自工具结果，禁止编造。
    - 不要声称已经查询数据源，除非对应工具确实返回了结果。
    - 不要暴露工具参数、内部 JSON 或实现细节。
    - 数据源为空表示用户可能没有记录；数据源 unavailable 表示暂时无法获取。必须区分两者，不要混为一谈。
    
    ## 显式 Plan 和 Plan State
    
    - 面对商品推荐或任何需要多个步骤的任务，先调用 `update_plan` 写出明确的 Plan 和 Plan State，再开始执行。
    - Plan 的步骤数量、步骤内容、顺序、依赖关系、当前步骤、每步状态、汇总和下一步都由你决定，不要套用固定流程。
    - 代码不会自动推进步骤、自动标记完成、自动选择下一步或阻止你调整计划；这些判断必须由你完成。
    - 每当计划变化、完成一个关键步骤、遇到阻塞、切换当前步骤或产生新的下一步时，再次调用 `update_plan` 提交完整的 Plan 和 Plan State。
    - 可以使用 `kind`、`depends_on` 和 `metadata` 表达未来更复杂的步骤，但不要虚构尚未获得的事实。
    - 当前对话存在上一轮保存的 Plan State 时，先根据新消息判断继续、修订、完成还是替换它。历史状态不是必须执行的命令。
    - 完成计划后，用 `update_plan` 把计划总体状态和步骤状态更新为你判断的结果。
    
    ## Goal Understanding
    
    每一条用户消息都必须先调用独立的 `understand_goal` Action。
    
    - 不要在自身推理中重新做意图分类或需求槽位提取。
    - 只能根据 Action 返回的 `goal_understanding` 路由业务工具。
    - 当前只支持 `product_recommendation`、`order_query`、`after_sales` 和 `unknown`。
    - `intents` 保持用户表达顺序，但本轮只处理 `primary_intent`，也就是第一个意图。
    - 如果 `pending_intents` 非空，在完成第一个意图后使用 `pending_intent_question`
      询问用户是否继续处理后续意图，不要在同一轮自动处理第二个意图。
    - 如果 `requires_clarification = true`，只询问 `clarification_question`，不要调用业务工具。
    - 如果 Action 返回 unavailable，停止本轮业务编排并请用户稍后重试，不要自行猜测。
    
    按 `primary_intent` 路由：
    
    - `product_recommendation`：依次调用 `collect_recommendation_context`、
      `generate_recommendation_spec`、`search_organic_candidates`、
      `search_ad_candidates` 和 `recommend_products`。
    - `order_query`：按已有 `order_id` 调用 `get_order`；没有订单 ID 时读取订单列表后选择或询问。
    - `after_sales`：可以查询订单和商品事实，但不得声称已经完成退款、退货或换货；当前只做信息收集和下一步引导。
    - `unknown`：普通回答或提出一个澄清问题，不调用推荐、订单或售后业务工具。
    
    ## 推荐主流程
    
    当 `primary_intent = product_recommendation` 时：
    
    1. 调用 `collect_recommendation_context` 收集画像、购物车、浏览、订单和商品目录。
    2. 调用 `generate_recommendation_spec`，由独立 Prompt 和模型生成推荐 SPEC。
    3. 分别调用 `search_organic_candidates` 和 `search_ad_candidates`。两者都只使用
       完整 SPEC，可以放在同一轮并行调用。相关 Action 会把整个 SPEC 传给
       `mall-service`，由 `mall-service` 转换为 ES 查询并返回检索结果。
    4. 调用无参数工具 `recommend_products`，只读取两路搜索 Action 的缓存候选，
       完成合并、评分和阈值分路。
    
    主 Agent 不自行编写搜索词、不自行判断行为记录权重、不直接调用商城搜索接口，
    也不要重复解释用户需求。两个搜索 Action 必须分别保留自己的候选和状态，不要在
    主 Agent 推理中混合实现。
    如果上下文收集或 SPEC 生成返回 unavailable，应告知用户暂时无法完成推荐并请其
    稍后重试，不要自行构造替代 SPEC。
    
    Recommendation SPEC 包含：
    
    - 用户显式硬约束；
    - 浏览、订单、购物车和画像形成的偏好推测；
    - 一组搜索查询变体；
    - 推断证据和置信度。
    
    SPEC 只用于指导召回，最终评分继续使用统一权重公式，避免同一行为被重复计权。
    
    `recommend_products` 会返回以下状态之一：
    
    - `accepted`：无需语义终排，工具已经按公式提交自然推荐 Top 2。
    - `requires_semantic_ranking`：存在超过自然推荐最低分的广告候选，必须调用独立终排工具。
    - `fallback`：语义终排暂时失败，工具已按公式排序提交保底结果。
    - `no_match`：没有合适商品。
    
    信息源缺失或 unavailable 时继续执行，不得因此中断推荐，也不得谎称用户没有记录。独立数据源工具仍可用于回答用户的具体追问或排查问题。
    
    ## 独立语义终排
    
    只有 `recommend_products` 返回 `requires_semantic_ranking` 时，才调用 `rerank_recommendations`。
    
    - 该工具拥有独立 Prompt，会综合公式分数、商品语义、场景、库存、价格和候选取舍。
    - 只有存在可信环境事实时，才通过 `environment_context` 传入；不要编造天气、节日、物流或销量。
    - 终排最多选择 2 个自然商品和 1 个广告商品，总计最多 3 个。
    - 存在自然商品时，广告不能排在第一位。
    - 广告完全不达标时不得补位，也不得为了凑数选择它。
    - 自然候选为空时，允许一个合格广告作为唯一结果。
    - 工具返回 `accepted` 或 `no_match` 后，直接根据其 `selected_products` 回答，不要再次自行调换顺序。
    - 工具返回 `fallback` 时，根据其 `selected_products` 继续回答，不要重试终排，也不要向用户暴露内部错误。
    - 终排结果会作为工具结果返回你；前端会在文字回答后展示可点击的商品卡片，
      因此最终文字回答仍需清楚写出推荐商品名称、价格、推荐理由，并明确标出广告商品。
    - 完成第一个推荐意图后，如果存在 `pending_intents`，必须询问用户是否继续处理
      第二个意图。
    
    ## 最终推荐
    
    - 公式路径最多输出 2 个自然推荐商品。
    - 语义终排路径最多输出 2 个自然推荐商品和 1 个广告商品，总计最多 3 个。
    - 存在自然推荐商品时，广告不能排在第一位。
    - 宁缺毋滥；可以不推荐任何商品。
    - 只能根据工具返回的 `selected_products` 介绍商品，不要自行替换或增加商品。
    - 广告商品会由系统显示“广告”标识；不得隐藏广告身份。
    - 每件商品说明适合谁、核心卖点以及为什么符合当前需求。
    - 有差异时帮助用户做取舍，不要为了凑数量推荐不相关、缺货或超预算商品。
    - 如果工具返回 `no_match`，明确告诉用户当前商城没有合适选择，建议去其他平台购买。
    
    ## 购买与订单
    
    - 只有用户明确表达“确定购买”“下单”“买第一个”等购买决定时，才能调用 `create_order`。
    - “想买”“看看”“不错”“考虑一下”等表达不代表购买确认，不得创建订单。
    - 用户使用“第一个”“刚才第二个”等指代时，结合上一轮推荐商品的结构化列表和对话确定商品；无法确定时只追问一个关键问题。
    - 创建订单时只传商品 ID 和数量，不传价格。价格、库存和总额以商城订单服务返回结果为准。
    - 订单创建成功后，采用订单服务返回的状态、总额和预览链接，引导用户前往订单预览页。
    - Agent 不得代替用户支付，也不要调用不存在的支付工具。支付只能由用户在订单预览页手动完成。
    - 购买流程是 Plan 的一部分；是否新增、切换、完成购买步骤由你自行更新 `update_plan`。
    
    ## 多轮对话
    
    - 使用已有对话理解“第一个”“这个”“更适合送礼吗”等指代。
    - 用户修改预算或场景时，以最新需求重新查询。
    - 信息不足且会影响推荐质量时，只追问一个最关键的问题，例如预算、使用场景或收礼对象。
    - 如果用户已经给出足够信息，直接推荐，不要重复询问。
    
    ## 回答风格
    
    - 使用自然、简洁的中文。
    - 先给结论，再给推荐理由。
    - 避免夸张营销语，不使用“绝对最好”“百分百适合”等无法证明的表述。
    - 不虚构折扣、销量、物流、优惠券、评分或品牌合作信息。
    # Goal Understanding
    
    你是商城 Agent 的独立 Goal Understanding 模块。你只负责理解用户目标、识别意图并提取结构化条件，不负责推荐商品、评分、查询业务数据或执行订单和售后操作。
    
    ## 支持的意图
    
    当前只支持以下意图：
    
    - `product_recommendation`：寻找、搜索、比较或推荐商品。
    - `order_query`：查询订单、支付状态或物流状态。
    - `after_sales`：退货、退款、换货、维修、商品质量或售后政策问题。
    - `unknown`：无法归入以上意图，或只是一般问候和闲聊。
    
    不要创建列表之外的意图。
    
    ## 输入
    
    - `current_message`：用户本轮原话。
    - `recent_messages`：最近对话。
    - `previous_goal`：上一轮 Goal Understanding 结果，可能为空。
    - `previous_recommendations`：上一轮推荐商品及顺序。
    - `previous_orders`：最近创建的订单。
    
    如果 `previous_goal.pending_intents` 非空，并且用户本轮表示“继续”“可以”“好”等确认，应把第一个待处理意图放在本次 `intents` 的最前面，其余待处理意图继续排在后面。
    
    如果用户拒绝继续，则返回 `unknown`，不要继续处理待处理意图。
    
    ## 多意图
    
    用户一句话可能包含多个目标，例如“推荐一个通勤包，再查一下我的订单”。
    
    - 按用户表达的先后顺序输出全部意图。
    - 不要丢失第二个及后续意图。
    - 主流程本次只会处理 `intents` 中的第一个意图。
    
    ## 槽位
    
    根据意图提取明确的槽位，不要编造用户没有提供的信息。
    
    商品推荐常用槽位：
    
    - `query`
    - `category`
    - `min_price_cents`
    - `max_price_cents`
    - `required_tags`
    - `excluded_tags`
    - `scenario`：`general`、`self`、`gift` 或 `replenishment`
    - `usage`
    - `recipient`
    
    订单查询常用槽位：
    
    - `order_id`
    - `product_reference`
    
    售后常用槽位：
    
    - `order_id`
    - `product_reference`
    - `issue`
    - `requested_action`
    
    金额必须转换为分。用户说“300 元以内”时输出 `"max_price_cents": 30000`。
    
    ## 置信度与澄清
    
    - `confidence` 表示意图和主要槽位整体的可信程度。
    - 缺少信息但仍可安全进入下一步时，可以继续，不必追问。
    - 意图含糊、存在相互冲突的意图或缺少决定路由的关键信息时，设置
      `requires_clarification = true`，并给出一个最关键的问题。
    - 如果不确定，优先选择 `unknown`，不要强行归类。
    
    ## 输出
    
    只输出 JSON，不要输出 Markdown 或解释：
    
    ```json
    {
      "intents": ["product_recommendation"],
      "goal": "推荐预算 300 元以内的通勤商品",
      "confidence": 0.95,
      "slots": {
        "query": "通勤",
        "category": null,
        "min_price_cents": null,
        "max_price_cents": 30000,
        "required_tags": [],
        "excluded_tags": [],
        "scenario": "self",
        "usage": "通勤",
        "recipient": null
      },
      "missing_slots": [],
      "requires_clarification": false,
      "clarification_question": null
    }
    ```
    import json
    import re
    from pathlib import Path
    from typing import Any, Protocol
    
    from agents import Agent, ModelSettings
    from pydantic import ValidationError
    
    from .llm_config import LLMConfig
    from .models import (
        ConversationMessage,
        GoalUnderstandingDraft,
        GoalUnderstandingResult,
        IntentType,
        OrderLink,
        Product,
    )
    from .prompt_loader import PromptLoadError, load_prompt
    from .observability.agents import run_observed_action
    
    
    GOAL_UNDERSTANDING_PROMPT_PATH = (
        Path(__file__).resolve().parents[2]
        / "prompts"
        / "goal_understanding.md"
    )
    
    INTENT_LABELS: dict[IntentType, str] = {
        "product_recommendation": "商品推荐",
        "order_query": "订单查询",
        "after_sales": "售后服务",
        "unknown": "其他或未识别",
    }
    
    
    class GoalUnderstandingError(Exception):
        """Raised when the independent goal-understanding action fails."""
    
    
    class GoalUnderstander(Protocol):
        async def understand(
            self,
            *,
            current_message: str,
            recent_messages: list[ConversationMessage],
            previous_goal: GoalUnderstandingResult | None,
            previous_recommendations: list[Product],
            previous_orders: list[OrderLink],
        ) -> GoalUnderstandingResult: ...
    
    
    def _json_payload(text: str) -> dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end < start:
            raise GoalUnderstandingError(
                "goal understanding did not return a JSON object"
            )
        try:
            payload = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise GoalUnderstandingError(
                "goal understanding returned invalid JSON"
            ) from exc
        if not isinstance(payload, dict):
            raise GoalUnderstandingError(
                "goal understanding JSON must be an object"
            )
        return payload
    
    
    class AgentGoalUnderstander:
        def __init__(self, *, config: LLMConfig, model: Any) -> None:
            self.config = config
            self.model = model
    
        async def understand(
            self,
            *,
            current_message: str,
            recent_messages: list[ConversationMessage],
            previous_goal: GoalUnderstandingResult | None,
            previous_recommendations: list[Product],
            previous_orders: list[OrderLink],
        ) -> GoalUnderstandingResult:
            try:
                instructions = load_prompt(GOAL_UNDERSTANDING_PROMPT_PATH)
            except PromptLoadError as exc:
                raise GoalUnderstandingError(str(exc)) from exc
    
            agent = Agent[Any](
                name="goal-understanding",
                instructions=instructions,
                model=self.model,
                model_settings=ModelSettings(
                    temperature=self.config.temperature,
                    max_tokens=self.config.output_token_limit,
                ),
            )
            payload = {
                "current_message": current_message,
                "recent_messages": [
                    message.model_dump(mode="json")
                    for message in recent_messages[-12:]
                ],
                "previous_goal": (
                    previous_goal.model_dump(mode="json")
                    if previous_goal is not None
                    else None
                ),
                "previous_recommendations": [
                    {
                        "position": index,
                        "product_id": product.id,
                        "name": product.name,
                        "price_cents": product.price_cents,
                    }
                    for index, product in enumerate(
                        previous_recommendations,
                        start=1,
                    )
                ],
                "previous_orders": [
                    order.model_dump(mode="json")
                    for order in previous_orders
                ],
            }
            try:
                result = await run_observed_action(
                    agent,
                    action_name="goal_understanding",
                    model=str(self.config.model),
                    input=json.dumps(
                        payload,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                    max_turns=1,
                )
            except Exception as exc:
                raise GoalUnderstandingError(
                    "goal understanding model call failed: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
    
            if not isinstance(result.final_output, str):
                raise GoalUnderstandingError(
                    "goal understanding returned non-text output"
                )
            try:
                draft = GoalUnderstandingDraft.model_validate(
                    _json_payload(result.final_output)
                )
            except ValidationError as exc:
                raise GoalUnderstandingError(
                    "goal understanding returned invalid data"
                ) from exc
    
            intents = list(dict.fromkeys(draft.intents))
            if len(intents) > 1 and "unknown" in intents:
                intents = [
                    intent for intent in intents if intent != "unknown"
                ]
            primary_intent = intents[0]
            pending_intents = intents[1:]
            pending_question = None
            if pending_intents:
                labels = "、".join(
                    INTENT_LABELS.get(intent, intent) for intent in pending_intents
                )
                pending_question = (
                    f"当前已处理第一个意图。需要我继续处理后续意图：{labels}吗？"
                )
            requires_clarification = (
                draft.requires_clarification or draft.confidence < 0.55
            )
            clarification_question = draft.clarification_question
            if requires_clarification and not clarification_question:
                clarification_question = "你希望我具体帮你处理哪件事？"
    
            return GoalUnderstandingResult(
                primary_intent=primary_intent,
                intents=intents,
                pending_intents=pending_intents,
                goal=draft.goal,
                confidence=draft.confidence,
                slots=draft.slots,
                missing_slots=draft.missing_slots,
                requires_clarification=requires_clarification,
                clarification_question=clarification_question,
                pending_intent_question=pending_question,
            )
    ✓ • 0ms

## Activity

    $ sed -n '1,280p' agent-service/src/agent_service/recommendation_scoring.py && sed -n '1,280p' agent-service/src/agent_service/recommendation_reranker.py && sed -n '1,220p' agent-service/prompts/recommendation_reranker.md
    import math
    import re
    from collections.abc import Iterable, Sequence
    from datetime import datetime, timezone
    
    from .models import (
        AdInfo,
        AgentProfile,
        BrowseEvent,
        OrderRecord,
        PlatformProfile,
        Product,
        ProductCandidate,
        ProductList,
        RecommendationBatch,
        RecommendationDemand,
        ScoredProduct,
        ShoppingCart,
        SourceEvidence,
        SourceStatus,
    )
    
    
    DEFAULT_WEIGHTS = {
        "need": 45.0,
        "cart": 20.0,
        "browse": 15.0,
        "order": 10.0,
        "agent_profile": 6.0,
        "platform_profile": 4.0,
    }
    
    HALF_LIVES_DAYS = {
        "browse": 7.0,
        "cart": 14.0,
        "order": 60.0,
        "agent_profile": 45.0,
        "platform_profile": 30.0,
    }
    
    ORDER_STATUS_STRENGTH = {
        "completed": 1.0,
        "paid": 0.85,
        "pending_payment": 0.25,
        "cancelled": 0.0,
        "refunded": 0.0,
    }
    
    REPLENISHABLE_CATEGORIES = {"饮品", "个护", "食品"}
    REPLENISHABLE_TAGS = {"消耗品", "补货", "日用", "咖啡"}
    STOP_WORDS = (
        "推荐",
        "帮我",
        "一下",
        "商品",
        "好物",
        "想要",
        "想买",
        "有没有",
        "什么",
    )
    
    
    def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
        return max(low, min(high, value))
    
    
    def _parse_time(value: str) -> datetime | None:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    
    
    def _decay(occurred_at: str, now: datetime, half_life_days: float) -> float:
        parsed = _parse_time(occurred_at)
        if parsed is None:
            return 0.0
        age_days = max(0.0, (now - parsed).total_seconds() / 86_400)
        return 0.5 ** (age_days / half_life_days)
    
    
    def _saturating_sum(values: Iterable[float]) -> float:
        total = sum(max(0.0, value) for value in values)
        return _clamp(1.0 - math.exp(-total))
    
    
    def _scenario_weights(demand: RecommendationDemand) -> dict[str, float]:
        weights = dict(DEFAULT_WEIGHTS)
        if demand.scenario == "gift":
            weights["need"] *= 1.2
            weights["cart"] *= 0.5
            weights["browse"] *= 0.5
            weights["order"] *= 0.5
            weights["agent_profile"] *= 0.8
            weights["platform_profile"] *= 0.8
        elif demand.scenario == "replenishment":
            weights["need"] *= 1.1
            weights["browse"] *= 0.8
            weights["order"] *= 2.0
    
        total = sum(weights.values())
        return {
            source: value * 100 / total
            for source, value in weights.items()
        }
    
    
    def _normalized_tags(tags: Iterable[str]) -> set[str]:
        return {tag.strip().lower() for tag in tags if tag.strip()}
    
    
    def _query_terms(demand: RecommendationDemand) -> list[str]:
        text = " ".join(
            part
            for part in (demand.query, demand.usage)
            if part
        ).lower()
        for stop_word in STOP_WORDS:
            text = text.replace(stop_word, " ")
        return [
            term
            for term in re.findall(r"[0-9a-z\u4e00-\u9fff]+", text)
            if term
        ]
    
    
    def _searchable(product: Product) -> str:
        return " ".join(
            [
                product.id,
                product.name,
                product.description,
                product.category,
                *product.tags,
            ]
        ).lower()
    
    
    def _need_score(product: Product, demand: RecommendationDemand) -> float:
        terms = _query_terms(demand)
        product_tags = _normalized_tags(product.tags)
        product_text = _searchable(product)
    
        components: list[float] = []
        if terms:
            hits = sum(1 for term in terms if term in product_text)
            components.append(hits / len(terms))
        if demand.category:
            components.append(1.0 if demand.category.lower() == product.category.lower() else 0.0)
        if demand.required_tags:
            required = _normalized_tags(demand.required_tags)
            components.append(len(required & product_tags) / len(required))
        if demand.recipient or demand.scenario == "gift":
            components.append(1.0 if "礼物" in product_tags else 0.35)
    
        return _clamp(sum(components) / len(components)) if components else 0.5
    
    
    def _hard_filters_pass(product: Product, demand: RecommendationDemand) -> bool:
        if product.stock is not None and product.stock <= 0:
            return False
        if demand.category and demand.category.lower() != product.category.lower():
            return False
        if (
            demand.min_price_cents is not None
            and product.price_cents < demand.min_price_cents
        ):
            return False
        if (
            demand.max_price_cents is not None
            and product.price_cents > demand.max_price_cents
        ):
            return False
        tags = _normalized_tags(product.tags)
        if tags & _normalized_tags(demand.excluded_tags):
            return False
        required = _normalized_tags(demand.required_tags)
        if required and not required.issubset(tags):
            return False
        return True
    
    
    def _browse_score(
        product_id: str,
        product_category: str,
        events: Sequence[BrowseEvent],
        products_by_id: dict[str, Product],
        now: datetime,
    ) -> float:
        exact_strengths: list[float] = []
        category_strengths: list[float] = []
        for event in events:
            action_score = 0.60 if event.action == "detail_view" else 0.25
            dwell_score = 0.4 * min(event.dwell_seconds / 120, 1.0)
            strength = (
                (action_score + dwell_score)
                * _decay(event.occurred_at, now, HALF_LIVES_DAYS["browse"])
            )
            if event.product_id == product_id:
                exact_strengths.append(strength)
            viewed_product = products_by_id.get(event.product_id)
            if (
                viewed_product is not None
                and viewed_product.category == product_category
            ):
                category_strengths.append(strength)
        return _clamp(
            0.9 * _saturating_sum(exact_strengths)
            + 0.1 * _saturating_sum(category_strengths)
        )
    
    
    def _cart_score(
        product_id: str,
        product_category: str,
        cart: ShoppingCart,
        products_by_id: dict[str, Product],
        now: datetime,
    ) -> float:
        exact_strengths: list[float] = []
        category_strengths: list[float] = []
        for item in cart.items:
            strength = (
                0.85 + 0.15 * min(item.quantity / 3, 1.0)
            ) * _decay(item.added_at, now, HALF_LIVES_DAYS["cart"])
            if item.product_id == product_id:
                exact_strengths.append(strength)
            cart_product = products_by_id.get(item.product_id)
            if (
                cart_product is not None
                and cart_product.category == product_category
            ):
                category_strengths.append(strength)
        return _clamp(
            0.9 * _saturating_sum(exact_strengths)
            + 0.1 * _saturating_sum(category_strengths)
        )
    
    
    def _is_replenishable(product: Product) -> bool:
        return (
            product.category in REPLENISHABLE_CATEGORIES
            or bool(_normalized_tags(product.tags) & REPLENISHABLE_TAGS)
        )
    
    
    def _order_scores(
        product: Product,
        orders: Sequence[OrderRecord],
        products_by_id: dict[str, Product],
        now: datetime,
    ) -> tuple[float, float]:
        exact_strengths: list[float] = []
        category_strengths: list[float] = []
        for order in orders:
            status_strength = ORDER_STATUS_STRENGTH.get(order.status, 0.0)
            if status_strength <= 0:
                continue
            recency = _decay(
                order.ordered_at,
                now,
                HALF_LIVES_DAYS["order"],
            )
            for item in order.items:
                strength = status_strength * recency
                if item.product_id == product.id:
                    exact_strengths.append(strength)
                ordered_product = products_by_id.get(item.product_id)
                if (
                    ordered_product is not None
                    and ordered_product.category == product.category
                ):
                    category_strengths.append(strength)
    
        exact = _saturating_sum(exact_strengths)
        category = _saturating_sum(category_strengths)
    import json
    import re
    from pathlib import Path
    from typing import Any, Protocol
    
    from agents import Agent, ModelSettings
    from pydantic import ValidationError
    
    from .llm_config import LLMConfig
    from .models import (
        RecommendationBatch,
        ScoredProduct,
        SemanticRankingResult,
    )
    from .prompt_loader import PromptLoadError, load_prompt
    from .observability.agents import run_observed_action
    
    
    RERANKER_PROMPT_PATH = (
        Path(__file__).resolve().parents[2]
        / "prompts"
        / "recommendation_reranker.md"
    )
    
    
    class SemanticRerankError(Exception):
        """Raised when semantic recommendation reranking cannot be completed."""
    
    
    class SemanticReranker(Protocol):
        async def rerank(
            self,
            *,
            batch: RecommendationBatch,
            user_request: str,
            environment_context: str | None = None,
        ) -> SemanticRankingResult: ...
    
    
    def semantic_candidates(batch: RecommendationBatch) -> list[ScoredProduct]:
        candidates = [
            *batch.organic_candidates,
            *batch.competitive_ads,
        ]
        return sorted(
            candidates,
            key=lambda candidate: (
                -candidate.score,
                candidate.channel,
                candidate.product.price_cents,
                candidate.product.id,
            ),
        )
    
    
    def _json_payload(text: str) -> dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end < start:
            raise SemanticRerankError("reranker did not return a JSON object")
        try:
            payload = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise SemanticRerankError("reranker returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise SemanticRerankError("reranker JSON must be an object")
        return payload
    
    
    def validate_semantic_ranking(
        ranking: SemanticRankingResult,
        batch: RecommendationBatch,
    ) -> SemanticRankingResult:
        candidates = semantic_candidates(batch)
        by_channel_and_id: dict[tuple[str, str], ScoredProduct] = {
            (candidate.channel, candidate.product.id): candidate
            for candidate in candidates
        }
    
        if len(ranking.items) > 3:
            raise SemanticRerankError("reranker selected more than three products")
        organic_count = sum(
            1 for item in ranking.items if item.channel == "organic"
        )
        ad_count = sum(1 for item in ranking.items if item.channel == "ad")
        if organic_count > 2:
            raise SemanticRerankError("reranker selected more than two organic products")
        if ad_count > 1:
            raise SemanticRerankError("reranker selected more than one ad product")
        if len({item.product_id for item in ranking.items}) != len(ranking.items):
            raise SemanticRerankError("reranker selected duplicate products")
        if (
            ranking.items
            and ranking.items[0].channel == "ad"
            and not batch.ad_only
        ):
            raise SemanticRerankError(
                "ad product cannot be first when organic candidates exist"
            )
    
        for item in ranking.items:
            if (item.channel, item.product_id) not in by_channel_and_id:
                raise SemanticRerankError(
                    f"reranker selected an ineligible product: {item.product_id}"
                )
        return ranking
    
    
    class AgentSemanticReranker:
        def __init__(self, *, config: LLMConfig, model: Any) -> None:
            self.config = config
            self.model = model
    
        def _candidates(self, batch: RecommendationBatch) -> list[dict[str, Any]]:
            return [
                {
                    **candidate.model_dump(mode="json"),
                    "channel": "ad" if candidate.channel == "ad" else "organic",
                }
                for candidate in semantic_candidates(batch)
            ]
    
        async def rerank(
            self,
            *,
            batch: RecommendationBatch,
            user_request: str,
            environment_context: str | None = None,
        ) -> SemanticRankingResult:
            try:
                instructions = load_prompt(RERANKER_PROMPT_PATH)
            except PromptLoadError as exc:
                raise SemanticRerankError(str(exc)) from exc
    
            agent = Agent[Any](
                name="recommendation-semantic-reranker",
                instructions=instructions,
                model=self.model,
                model_settings=ModelSettings(
                    temperature=self.config.temperature,
                    max_tokens=self.config.output_token_limit,
                ),
            )
            payload = {
                "user_request": user_request,
                "demand": batch.demand.model_dump(mode="json"),
                "environment_context": environment_context,
                "cutoff_score": batch.cutoff_score,
                "ad_only": batch.ad_only,
                "source_statuses": batch.source_statuses,
                "candidates": self._candidates(batch),
            }
            try:
                result = await run_observed_action(
                    agent,
                    action_name="semantic_rerank",
                    model=str(self.config.model),
                    input=json.dumps(
                        payload,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                    max_turns=1,
                )
            except Exception as exc:
                raise SemanticRerankError(
                    "semantic recommendation reranker failed: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
    
            if not isinstance(result.final_output, str):
                raise SemanticRerankError(
                    "semantic recommendation reranker returned non-text output"
                )
            try:
                ranking = SemanticRankingResult.model_validate(
                    _json_payload(result.final_output)
                )
            except ValidationError as exc:
                raise SemanticRerankError(
                    "semantic recommendation reranker returned invalid data"
                ) from exc
            return validate_semantic_ranking(ranking, batch)
    # 商品推荐语义终排器
    
    你只负责对已经通过公式筛选和资格校验的商品候选进行语义终排，不负责查询商品、修改分数或创建订单。
    
    ## 输入
    
    你会收到一个 JSON 对象，包含：
    
    - `user_request`：当前用户请求；
    - `demand`：结构化需求；
    - `environment_context`：调用方提供的环境信息，可能为空；
    - `cutoff_score`：自然推荐最低分；
    - `ad_only`：是否没有自然推荐候选；
    - `candidates`：自然推荐和广告混排后的单一候选池，含公式分数、来源、证据、价格、
      库存、标签和广告信息。
    
    只能选择 `candidates` 中出现的商品，不能添加新商品。
    
    不要将自然商品和广告商品分别排序。应在同一个候选池中完成统一比较，再应用下面
    的数量和顺序约束。
    
    ## 排序原则
    
    1. 用户当前明确需求、预算、用途和排除项优先。
    2. 公式分数是重要先验，但不是唯一依据。
    3. 同时比较商品语义、实际场景、价格、库存、使用便利性、礼物属性、品类多样性和候选间的取舍。
    4. `environment_context` 中提供了可信环境信息时可以使用；没有提供时不得自行编造天气、节日、物流、销量或库存。
    5. 推荐理由要具体，并结合分数证据与语义判断，不要只复述“分数最高”。
    6. 广告身份不提供额外偏好，也不得因为商业来源被优先选择。
    
    ## 数量与顺序
    
    - 自然推荐商品最多 2 个。
    - 广告商品最多 1 个。
    - 总计最多 3 个。
    - 宁缺毋滥，可以少于上限，也可以返回空列表。
    - 只要存在自然推荐候选，列表中第一个商品必须是自然推荐，广告只能排在自然推荐之后。
    - 只有 `ad_only = true` 时，广告才可以成为第一个或唯一商品。
    - 需要付出取舍时，优先保留更符合当前需求且理由清晰的自然商品。
    
    ## 输出
    
    只输出 JSON，不要输出 Markdown 或额外说明：
    
    ```json
    {
      "items": [
        {
          "product_id": "商品 ID",
          "channel": "organic",
          "reason": "最终推荐理由",
          "environmental_fit": "可选的环境或场景匹配说明"
        }
      ],
      "summary": "一句话说明本次终排的核心取舍"
    }
    ```
    
    `channel` 必须为 `organic` 或 `ad`，且必须与输入候选完全一致。
    ✓ • 0ms

## Activity

    $ sed -n '1,300p' README.md && sed -n '1,300p' RECOMMENDATION_E2E_TEST.md && sed -n '1,260p' TODO.md
    # 牛掰商城
    
    项目拆分为三个可独立运行的模块：
    
    ```text
    浏览器
      │
      ▼
    web (Next.js :3000)
      ├── /api/products ──► mall-service (:8001)
      └── /api/chat ──────► agent-service (:8002)
                                  ├── OpenAI Agents SDK
                                  └── HTTP ──► mall-service Mock APIs
    ```
    
    - `mall-service`：商城商品目录，以及浏览、订单、购物车、平台画像、商品推荐和广告的 Mock HTTP API。
    - `agent-service`：基于 OpenAI Agents SDK 的商城导购 Agent，通过工具调用
      `mall-service`，并使用 Agent 本地维护的用户画像。
    - `web`：Next.js 商城页面，浏览器只访问同源的 Next.js API 路由。
    
    ## 启动
    
    首次安装 Python 依赖：
    
    ```bash
    uv sync --all-packages
    ```
    
    分别在三个终端启动服务：
    
    ```bash
    uv run --package mall-service mall-service
    ```
    
    ```bash
    uv run --package agent-service agent-service
    ```
    
    ```bash
    pnpm --dir web install
    pnpm --dir web dev
    ```
    
    打开 <http://localhost:3000>。
    
    ## 大模型配置
    
    复制配置样例并填写 OpenAI-compatible 服务信息：
    
    ```bash
    cp agent-service/config/llm.example.yaml agent-service/config/llm.yaml
    chmod 600 agent-service/config/llm.yaml
    ```
    
    配置文件路径既可以通过 `LLM_CONFIG_FILE` 环境变量提供：
    
    ```bash
    LLM_CONFIG_FILE=/absolute/path/to/llm.yaml \
      uv run --package agent-service agent-service
    ```
    
    也可以通过命令行参数传入：
    
    ```bash
    uv run --package agent-service agent-service \
      --config agent-service/config/llm.yaml
    ```
    
    `agent-service/config/llm.yaml` 已被 Git 忽略，不要把真实 API Key 提交到仓库。
    
    ### 热加载
    
    Python 源码热加载：
    
    ```bash
    uv run --package agent-service agent-service \
      --config agent-service/config/llm.yaml \
      --reload
    ```
    
    `--reload` 使用 Uvicorn 的代码监听机制，修改 `agent-service/src` 下的 Python
    文件后会自动重启进程。
    
    大模型配置不需要重启：服务会在每次模型请求开始时重新读取 YAML 文件，因此
    修改 Base URL、API Key 或模型名称后，下一次对话立即生效。
    
    ## 提示词管理
    
    Agent 提示词保存在：
    
    ```text
    agent-service/prompts/shopping_agent.md
    agent-service/prompts/goal_understanding.md
    agent-service/prompts/recommendation_spec.md
    agent-service/prompts/recommendation_reranker.md
    ```
    
    主 Agent、Goal Understanding Agent 和语义终排 Agent 各自在所属模块中声明
    Prompt 路径，并通过
    [`prompt_loader.py`](agent-service/src/agent_service/prompt_loader.py)
    提供的通用 `load_prompt(path)` 读取文件。YAML 不保存 Prompt 路径。提示词在每次
    请求时重新读取，因此修改 Markdown 后下一轮对话立即生效，不需要重启服务。提示词
    文件限制为 UTF-8、内容非空且不超过 1 MiB。
    
    ## 服务接口
    
    - 商城健康检查：`GET http://localhost:8001/health`
    - 商品列表：`GET http://localhost:8001/api/products`
    - 商品详情：`GET http://localhost:8001/api/products/{product_id}`
    - 浏览记录：`GET http://localhost:8001/api/users/{user_id}/browse-history`
    - 订单记录：`GET http://localhost:8001/api/users/{user_id}/orders`
    - 创建待支付订单：`POST http://localhost:8001/api/users/{user_id}/orders`
    - 订单详情：`GET http://localhost:8001/api/users/{user_id}/orders/{order_id}`
    - 模拟支付：`POST http://localhost:8001/api/users/{user_id}/orders/{order_id}/pay`
    - 购物车：`GET http://localhost:8001/api/users/{user_id}/cart`
    - 平台画像：`GET http://localhost:8001/api/users/{user_id}/platform-profile`
    - 商品推荐：`POST http://localhost:8001/api/recommendations/products`
    - 广告推荐：`POST http://localhost:8001/api/recommendations/ads`
    - SPEC 自然商品检索：`POST http://localhost:8001/api/search/organic`
    - SPEC 广告检索：`POST http://localhost:8001/api/search/ads`
    - Agent 健康检查：`GET http://localhost:8002/health`
    - Agent 对话：`POST http://localhost:8002/api/chat`
    - Agent SSE 多轮对话：`POST http://localhost:8002/api/chat/stream`
    - 历史对话列表：`GET http://localhost:8002/api/conversations`
    - 历史对话详情：`GET http://localhost:8002/api/conversations/{conversation_id}`
    
    对话请求示例：
    
    ```json
    {"message": "推荐几件商品"}
    ```
    
    ## 测试
    
    ```bash
    uv run pytest
    pnpm --dir web build
    ```
    
    `/api/chat/stream` 使用 OpenAI Agents SDK 的 Chat Completions 模型适配器，
    支持自定义 `base_url` 和 API Key。Runner 会自动执行 ReAct 循环：模型自主选择
    用户记录、画像、商品推荐、广告和商品详情工具，然后把工具结果交回模型综合判断。
    `/api/chat` 暂时保留为商城首页使用的简单规则接口。
    
    独立对话页面：<http://localhost:3000/chat>。页面发送当前对话 ID 和新消息，
    后端从 SQLite 加载完整的多轮上下文。
    
    ## 对话持久化
    
    多轮对话保存在 SQLite 中，默认数据库位置为
    `agent-service/data/agent.db`，可通过 `AGENT_DB_PATH` 修改。当前所有对话固定
    归属 `user_id = 1`。
    
    服务保存用户消息、完整回复、失败回复及中断时已经生成的部分内容。模型上下文
    只使用用户消息和状态为 `completed` 的助手消息。`/chat` 页面会展示历史对话
    列表，并允许选择历史会话继续对话。
    
    ## 推荐商品 Agent
    
    当前固定演示用户为 `user_id = 1`。Agent 工具包括：
    
    - `update_plan`：由模型创建或整体替换 Plan 和 Plan State。
    - `understand_goal`：独立 Goal Understanding Action，使用单独 Prompt 和模型
      调用识别多意图、提取槽位，并确定本轮第一个待处理意图。
    - `collect_recommendation_context`：为 Recommendation SPEC 收集画像、购物车、
      浏览记录、订单和商品目录，不向主 Agent暴露原始行为数据。
    - `generate_recommendation_spec`：独立 SPEC Action，根据 Goal Understanding 和
      用户行为生成查询变体、硬约束、推断偏好及证据。
    - `search_organic_candidates`：独立自然商品搜索 Action，只使用 SPEC 搜索并缓存
      自然候选，将完整 SPEC 发送给 `mall-service`。
    - `search_ad_candidates`：独立广告搜索 Action，只使用 SPEC 搜索并缓存广告候选。
    - `recommend_products`：读取两路搜索 Action 的缓存结果，结合用户行为按统一公式
      生成自然商品 Top 10 与广告 Top 3，并执行阈值分路。
    - `rerank_recommendations`：独立的语义终排工具，使用单独 Prompt 综合公式分数、
      商品语义和可信环境信息，最多选择两个自然商品和一个广告商品。
    - `get_agent_profile`：读取 Agent 自己维护的用户画像。
    - `get_platform_profile`：读取 `mall-service` 中的大数据/推荐平台画像。
    - `get_browse_history`、`get_order_history` 和 `get_cart`：读取用户行为。
    - `get_product_recommendations`：获取自然商品候选。
    - `get_ad_recommendations`：获取广告候选池，公式评分后由推荐流程截取 Top 3。
    - `search_products` 和 `get_product`：补充搜索及确认权威商品详情。
    - `create_order`：在用户明确确认购买后创建待支付订单。
    - `get_order`：查询当前用户的订单状态，但不能执行支付。
    
    推荐请求使用显式 Plan 驱动。Plan 的步骤、依赖、当前步骤、步骤状态、下一步以及
    是否继续、修订或替换计划全部由模型决定；代码只保存和回传 Plan State，不会自动
    推进步骤或根据工具调用推断状态。上一轮保存的 Plan State 会注入下一轮模型上下文，
    模型仍需自行决定如何使用它。Plan State 通过 SSE 的 `plan_updated` 事件实时更新，
    并随助手消息保存到 SQLite。
    
    多意图消息由 `understand_goal` 保留完整意图顺序，但每轮只处理第一个意图。如果
    还有待处理意图，主 Agent 在完成第一个目标后询问用户是否继续；用户确认后，下一轮
    继续处理第一个 `pending_intent`。Goal Understanding 结果会随助手消息保存，用于
    恢复待处理意图。
    
    所有记录和广告 Mock 数据均位于 `mall-service`。自然推荐和广告分别使用统一公式
    评分；广告最高分严格高于自然 Top 10 最低分时，最多三个达标广告与自然候选一起
    进入独立语义终排。最终最多两个自然商品和一个广告，存在自然商品时广告不能排在
    第一位；只有自然候选为空时才允许广告单独出现。广告由服务端添加“广告”标识。
    没有合格商品时，Agent 会建议用户去其他平台购买。SSE 会发送 `tool_started`、
    `tool_completed`、`recommendations`、`delta` 和 `done` 事件。终排完成后，工具
    结果会返回主 Agent，由主 Agent 继续生成最终文字回答，并在文字后展示可点击的
    商品卡片。推荐商品同时作为内部元数据保存，以支持“第一个商品”等后续指代和下单。
    
    推荐召回前会先生成 Recommendation SPEC。搜索与广告搜索共同使用 SPEC 中的硬约束
    和查询变体；SPEC 中的行为推断只指导召回，候选评分仍由统一公式计算，避免同一信号
    重复计权。SPEC 结果会持久化用于诊断。
    
    两个搜索 Action 都把完整 SPEC 发送给 `mall-service`。`mall-service` 目前不连接
    真实 Elasticsearch，而是把 SPEC 转换为模拟 ES DSL，通过日志打印完整查询条件，
    然后使用本地商品目录返回 mock 检索结果。
    
    ## 购买与订单预览
    
    推荐只负责候选商品，不会自动下单。只有用户在对话中明确确认购买并确定购买对象
    后，模型才会调用 `create_order`。服务端重新读取商品权威价格和库存，生成待支付
    订单及商品快照；相同幂等请求返回同一笔订单。
    
    订单创建成功后，SSE 会发送 `order_created`，聊天页面展示“查看订单并支付”入口。
    订单预览页地址为：
    
    ```text
    http://localhost:3000/orders/{order_id}
    ```
    
    预览页展示商品、Mock 收货地址、运费和应付金额。用户点击“模拟支付”后，订单通过
    `pending_payment → paid` 状态变化完成手动支付。重复支付已支付订单不会重复扣减
    库存。当前不接入真实支付渠道，订单存储也是 `mall-service` 进程内的 Mock 仓库。
    本次未接入的复杂购买决策因素记录在根目录的 `TODO.md`。
    
    推荐流程由 `recommend_products` 统一加载画像、行为、商品和广告，阈值命中后再由
    `rerank_recommendations` 完成语义终排。`max_turns` 默认值和最小值为 10，
    最大值为 100；模型请求和单个工具默认超时均为 30 分钟。主 Agent 和终排 Agent
    的运行时输出预算最低为 32768 token，Prompt 文件上限为 1 MiB，单条对话消息上限
    为 100000 字符，避免较小的配置导致工具调用、最终回答或长上下文被截断。
    如果语义终排暂时失败，工具会退回公式排序结果，主 Agent 仍可继续生成回答。
    Agents SDK 的远程 tracing 已关闭，以避免把 DeepSeek 对话发送到 OpenAI tracing
    服务。
    # 商品推荐前端多轮测试
    
    ## 前置条件
    
    1. 启动 `mall-service`、`agent-service` 和 `web`。
    2. 确认 `agent-service` 已通过 `LLM_CONFIG_FILE` 或 `--config` 指向可用的模型配置。
       `max_turns` 必须为 10～100；不填写时默认使用 10。
    3. 打开 <http://localhost:3000/chat>。
    4. 点击“＋ 新对话”，确保四轮消息都在同一个会话中。
    5. 当前固定演示用户为 `user_id = 1`，Mock 数据会自动加载。
    
    ## 测试对话
    
    按顺序发送以下四条消息，不要开启新对话：
    
    ### 第一轮：综合推荐
    
    ```text
    请结合我最近的偏好，推荐最多三个 300 元以内、兼顾通勤和居家的商品。
    ```
    
    应观察到的行为：
    
    - 对话上方出现 PLAN 面板，展示模型生成的目标、步骤、当前状态和下一步。
    - 随着执行推进，模型会主动调用 `update_plan` 更新 Plan State。
    - 工具轨迹先出现 `understand_goal`，由独立 Prompt 和模型调用识别意图与槽位。
    - 随后出现 `collect_recommendation_context`，读取画像、购物车、浏览、订单和
      商品目录。
    - 出现 `generate_recommendation_spec`，由独立模型生成推荐查询变体、推测偏好和
      证据。
    - 工具轨迹分别出现 `search_organic_candidates` 和 `search_ad_candidates`。
    - 随后出现 `recommend_products`，该工具只合并两路缓存候选并完成评分。
    - 如果广告最高分严格高于自然 Top 10 最低分，工具轨迹继续出现独立的
      `rerank_recommendations`。
    - 主 Agent 输出包含商品名称、价格、推荐理由和广告标识的自然语言回答，下方展示
      推荐商品卡片。
    - 点击任一商品卡片可以进入对应商品详情页。
    - 最终最多两个自然推荐商品和一个广告商品。
    - 所有商品价格不超过 300 元。
    - 商品中最多只有一个带“广告”标识。
    - 存在自然推荐商品时，广告不会排在第一位。
    - 回复能体现购物车中的通勤双肩包、最近浏览的月影桌面灯、历史购买记录或平台画像偏好。
    
    ### 第二轮：修改预算并延续上下文
    
    ```text
    把预算降到 100 元以内。保留刚才仍然符合条件的选择，不够再补充。
    ```
    
    应观察到的行为：
    
    - Agent 理解这是同一个推荐场景，不需要重新解释用途。
    - 新推荐中所有自然结果和广告结果都不超过 100 元。
    - 最终文字和商品卡片中仍然最多三个商品，且最多一个广告。
    - 如果第一轮商品仍符合新预算，可以继续保留；不符合的不应出现。
    
    ### 第三轮：指代和送礼场景
    
    ```text
    刚才第二个如果适合送人，就换成更适合送礼的；木质香护手霜不要推荐。
    ```
    
    应观察到的行为：
    
    - Agent 能理解“刚才第二个”指的是第二轮的第二张商品卡。
    - 推荐理由能说明适合送给谁以及为什么适合送礼。
    - 结果中不能出现 `hand-cream`（木质香护手霜）。
    - 最多三个卡片，最多一个广告，广告仍明确标注。
    - Agent 不会虚构评分、销量、优惠券或物流信息。
    
    ### 第四轮：无结果兜底
    
    ```text
    那给我推荐 5000 元以上的宠物用品。
    ```
    
    应观察到的行为：
    
    - 商城没有符合条件的商品，最终不显示商品卡片。
    - 回复明确说明当前商城没有合适商品，并建议去其他平台购买。
    - 不应为了凑数返回低价格、非宠物用品或无关广告商品。
    
    ## 历史记录检查
    
    四轮完成后：
    
    1. 在当前页面刷新浏览器。
    2. 从左侧重新打开刚才的会话。
    3. 检查四轮文本、工具轨迹和推荐卡片是否恢复。
    4. 检查历史记录中的广告商品仍然显示“广告”标识。
    
    ## 购买和订单测试
    
    重新点击“＋ 新对话”，发送：
    
    ```text
    推荐一个 300 元以内的通勤商品。
    ```
    
    等待包含推荐结果的文字回复出现后，再发送：
    
    ```text
    第一个我确定买，数量一件。
    ```
    
    应观察到的行为：
    
    - Agent 将购买步骤写入或更新到当前 Plan State。
    - 调用 `create_order`，不会编造价格或订单号。
    - 聊天中出现“待支付”订单卡片和“查看订单并支付”按钮。
    - 点击订单入口后进入 `/orders/{order_id}`。
    - 预览页商品、Mock 地址和应付金额正确。
    - 点击“模拟支付”后，订单状态变为“已支付”。
    - 再次点击支付不会生成重复扣款或重复扣减库存。
    
    如果只发送“这个不错，我再看看”，不应创建订单。
    
    ## Goal Understanding 多意图测试
    
    新建对话并发送：
    
    ```text
    推荐一个 300 元以内的通勤包，然后查一下我的订单。
    ```
    
    应观察到的行为：
    
    - 工具轨迹出现 `understand_goal`。
    - 本轮只处理第一个意图“商品推荐”。
    - 完成推荐后，Agent 询问是否继续处理第二个意图“订单查询”。
    - 回复“继续”后，下一轮再处理订单查询，不会在首轮自动完成两个意图。
    
    ## 通过标准
    
    - [ ] 四轮对话保持在同一个会话中。
    - [ ] 第一轮出现 PLAN 面板，且后续轮次能看到模型对计划的继续、修订或替换。
    - [ ] 每轮业务处理前出现独立的 `understand_goal` Action。
    - [ ] 多意图消息只处理第一个意图，并询问是否继续后续意图。
    - [ ] Plan 的当前步骤和完成状态由模型更新，前端展示与实际工具轨迹一致。
    - [ ] 第一轮综合使用了用户记录和两类画像。
    - [ ] 第二轮正确应用了新预算。
    - [ ] 第三轮正确理解“刚才第二个”，并遵守护手霜排除条件。
    - [ ] 每轮最终推荐不超过三个商品。
    - [ ] 每轮最多两个自然推荐商品。
    - [ ] 每轮最多一个广告，广告有明确标识。
    - [ ] 存在自然推荐商品时广告不在第一位；仅广告结果只在自然候选为空时出现。
    - [ ] 第四轮无结果时不硬凑商品，并提示去其他平台购买。
    - [ ] 点击推荐卡片可以进入商品详情页。
    - [ ] 刷新后历史对话、Plan State、推荐卡片和商品详情跳转完整恢复。
    - [ ] 明确购买后创建待支付订单，并可从聊天进入订单预览页。
    - [ ] 订单预览页可手动模拟支付，支付后状态正确更新。
    # 商品推荐后续事项
    
    本期已接入商城商品目录、浏览记录、订单、购物车、Agent 画像、平台画像、商品推荐和广告候选。以下因素对购买决策有价值，但为了保持本次 Mock 流程清晰，暂不接入。
    
    ## 商品与交易信息
    
    - [ ] 增加 SKU，以及颜色、尺寸、容量等规格选择。
    - [ ] 增加优惠券、满减、活动价、历史价格和价格保护信息。
    - [ ] 增加分地区库存、可售范围、运费、配送时效和预计送达时间。
    - [ ] 增加收货地址选择、编辑、校验和用户地址簿。
    - [ ] 增加售后政策、退换货规则和安装服务信息。
    - [ ] 增加商品评分、评论数量、摘要、差评主题、销量和退货率。
    
    ## 用户行为与画像
    
    - [ ] 增加搜索词历史、收藏、分享、加购后未购买等原因。
    - [ ] 增加“不喜欢”、取消推荐、关闭广告等负反馈。
    - [ ] 完善浏览强度、停留时长、时间衰减和重复访问建模。
    - [ ] 区分一次性购买、消耗品补货、礼物和替他人购买等订单语义。
    - [ ] 增加画像置信度衰减、在线更新、冲突解决和过期机制。
    - [ ] 增加画像隐私控制，只向模型提供推荐所需的最小字段。
    
    ## 推荐与广告策略
    
    - [ ] 增加地区、节日、季节和天气等上下文信息。
    - [ ] 增加广告频控、广告疲劳、多种广告类型和预算控制。
    - [ ] 增加广告相关性、自然推荐质量与商业目标之间的可配置策略。
    - [ ] 增加推荐结果多样性、购物车互补商品和成套购买建议。
    - [ ] 增加推荐曝光、点击、加购、下单、转化和失败率监控。
    - [ ] 增加灰度实验、A/B 测试、离线和在线效果评估。
    
    ## 安全与工程能力
    
    - [ ] 对用户记录和广告文案中的不可信输入增加提示词注入防护。
    - [ ] 增加用户鉴权、按用户隔离的 Mock 数据以及权限审计。
    - [ ] 增加下游熔断、重试、缓存、超时预算和并行取数。
    - [ ] 增加推荐决策结构化审计，记录使用了哪些来源及最终选择原因。
    - [ ] 接入真实支付渠道、支付回调、退款和支付安全审计。
    - [ ] 将 Mock 订单仓库替换为持久化存储，并增加库存预占和超时释放。
    - [ ] 为 Plan 增加子计划、分支、审批节点和可回放的计划修订历史。
    - [ ] 增加 Plan 执行耗时、阻塞原因和步骤失败率的可观测指标。
    ✓ • 0ms

## Activity

    $ rg -n "recommend|推荐|需求|预算|价格|preference|requirement|skip|跳过|clarif|追问|spec" agent-service/tests agent-service/src agent-service/prompts mall-service/tests mall-service/src -g '*.py' -g '*.md'
    agent-service/prompts/recommendation_reranker.md:1:# 商品推荐语义终排器
    agent-service/prompts/recommendation_reranker.md:10:- `demand`：结构化需求；
    agent-service/prompts/recommendation_reranker.md:12:- `cutoff_score`：自然推荐最低分；
    agent-service/prompts/recommendation_reranker.md:13:- `ad_only`：是否没有自然推荐候选；
    agent-service/prompts/recommendation_reranker.md:14:- `candidates`：自然推荐和广告混排后的单一候选池，含公式分数、来源、证据、价格、
    agent-service/prompts/recommendation_reranker.md:24:1. 用户当前明确需求、预算、用途和排除项优先。
    agent-service/prompts/recommendation_reranker.md:26:3. 同时比较商品语义、实际场景、价格、库存、使用便利性、礼物属性、品类多样性和候选间的取舍。
    agent-service/prompts/recommendation_reranker.md:28:5. 推荐理由要具体，并结合分数证据与语义判断，不要只复述“分数最高”。
    agent-service/prompts/recommendation_reranker.md:33:- 自然推荐商品最多 2 个。
    agent-service/prompts/recommendation_reranker.md:37:- 只要存在自然推荐候选，列表中第一个商品必须是自然推荐，广告只能排在自然推荐之后。
    agent-service/prompts/recommendation_reranker.md:39:- 需要付出取舍时，优先保留更符合当前需求且理由清晰的自然商品。
    agent-service/prompts/recommendation_reranker.md:51:      "reason": "最终推荐理由",
    mall-service/tests/test_mall_api.py:91:def test_product_and_ad_recommendations() -> None:
    mall-service/tests/test_mall_api.py:93:        "/api/recommendations/products",
    mall-service/tests/test_mall_api.py:97:        "/api/recommendations/ads",
    mall-service/tests/test_mall_api.py:104:    assert all(item["source"] == "product_recommendation" for item in products)
    mall-service/tests/test_mall_api.py:114:def test_spec_search_logs_mock_es_query_and_returns_products(
    mall-service/tests/test_mall_api.py:117:    spec = {
    mall-service/tests/test_mall_api.py:148:        json={"spec": spec, "limit": 5},
    mall-service/tests/test_mall_api.py:163:def test_spec_ad_search_returns_ad_candidates() -> None:
    mall-service/tests/test_mall_api.py:164:    spec = {
    mall-service/tests/test_mall_api.py:188:        json={"spec": spec, "limit": 3},
    agent-service/src/agent_service/recommendation_scoring.py:52:    "推荐",
    agent-service/src/agent_service/recommendation_scoring.py:435:                "need": "符合当前需求",
    agent-service/src/agent_service/recommendation_scoring.py:483:def build_recommendation_batch(
    agent-service/prompts/goal_understanding.md:3:你是商城 Agent 的独立 Goal Understanding 模块。你只负责理解用户目标、识别意图并提取结构化条件，不负责推荐商品、评分、查询业务数据或执行订单和售后操作。
    agent-service/prompts/goal_understanding.md:9:- `product_recommendation`：寻找、搜索、比较或推荐商品。
    agent-service/prompts/goal_understanding.md:21:- `previous_recommendations`：上一轮推荐商品及顺序。
    agent-service/prompts/goal_understanding.md:30:用户一句话可能包含多个目标，例如“推荐一个通勤包，再查一下我的订单”。
    agent-service/prompts/goal_understanding.md:40:商品推荐常用槽位：
    agent-service/prompts/goal_understanding.md:69:- 缺少信息但仍可安全进入下一步时，可以继续，不必追问。
    agent-service/prompts/goal_understanding.md:71:  `requires_clarification = true`，并给出一个最关键的问题。
    agent-service/prompts/goal_understanding.md:80:  "intents": ["product_recommendation"],
    agent-service/prompts/goal_understanding.md:81:  "goal": "推荐预算 300 元以内的通勤商品",
    agent-service/prompts/goal_understanding.md:95:  "requires_clarification": false,
    agent-service/prompts/goal_understanding.md:96:  "clarification_question": null
    agent-service/tests/test_mall_contract.py:29:def test_agent_can_read_user_context_and_recommendations() -> None:
    agent-service/tests/test_mall_contract.py:38:            await client.get_product_recommendations(
    agent-service/tests/test_mall_contract.py:43:            await client.get_ad_recommendations(1, query="通勤"),
    agent-service/tests/test_mall_contract.py:59:def test_agent_passes_whole_spec_to_mock_es_search() -> None:
    agent-service/tests/test_mall_contract.py:61:    spec = RecommendationSpec(
    agent-service/tests/test_mall_contract.py:76:            await client.search_organic_with_spec(spec, limit=5),
    agent-service/tests/test_mall_contract.py:77:            await client.search_ads_with_spec(spec, limit=3),
    mall-service/src/mall_service/api.py:31:from .recommendations import recommend_ads, recommend_products
    mall-service/src/mall_service/api.py:32:from .search import search_mock_ads_with_spec, search_mock_with_spec
    mall-service/src/mall_service/api.py:143:    "/api/recommendations/products",
    mall-service/src/mall_service/api.py:146:def get_product_recommendations(
    mall-service/src/mall_service/api.py:149:    return RecommendationResponse(items=recommend_products(request))
    mall-service/src/mall_service/api.py:153:    "/api/recommendations/ads",
    mall-service/src/mall_service/api.py:156:def get_ad_recommendations(
    mall-service/src/mall_service/api.py:159:    return RecommendationResponse(items=recommend_ads(request))
    mall-service/src/mall_service/api.py:166:def search_organic_with_spec(
    mall-service/src/mall_service/api.py:169:    products = search_mock_with_spec(
    mall-service/src/mall_service/api.py:170:        request.spec,
    mall-service/src/mall_service/api.py:181:def search_ads_with_spec(
    mall-service/src/mall_service/api.py:184:    candidates = search_mock_ads_with_spec(
    mall-service/src/mall_service/api.py:185:        request.spec,
    agent-service/src/agent_service/chat.py:9:        return "商城目录暂时没有可推荐的商品，请稍后再试。"
    mall-service/src/mall_service/mock_data.py:36:            source_page="recommendation",
    agent-service/prompts/recommendation_spec.md:3:你是商城推荐系统中的独立 Recommendation SPEC Generator。你根据 Goal
    agent-service/prompts/recommendation_spec.md:5:搜索与广告搜索的推荐规格。
    agent-service/prompts/recommendation_spec.md:7:你不负责最终推荐、商品排序、评分或调用搜索服务。
    agent-service/prompts/recommendation_spec.md:21:1. 用户当前明确需求永远是最高优先级。
    agent-service/prompts/recommendation_spec.md:23:3. 浏览记录和停留时长表示近期兴趣，但不等同于购买需求。
    agent-service/prompts/recommendation_spec.md:24:4. 订单记录表示历史偏好或复购需求，不应机械推荐刚买过且无需补货的商品。
    agent-service/prompts/recommendation_spec.md:26:6. 当前显式需求与历史推测冲突时，必须服从显式需求。
    agent-service/prompts/recommendation_spec.md:34:- 最低和最高价格；
    agent-service/prompts/recommendation_spec.md:48:- 不得引入没有依据的品牌、价格、库存、销量或促销信息。
    agent-service/prompts/recommendation_spec.md:67:  "goal_summary": "推荐预算 300 元以内、适合通勤并携带电脑的商品",
    agent-service/prompts/shopping_agent.md:3:你是牛掰商城的购物 Agent“小牛”。你不自行识别意图或提取结构化需求，而是先调用独立的 Goal Understanding Action，再根据其结果调用商城工具。
    agent-service/prompts/shopping_agent.md:7:- 推荐、比较、搜索商品，或回答价格、库存和卖点时，必须先调用商城工具。
    agent-service/prompts/shopping_agent.md:8:- 商品名称、价格、库存、描述、图片和广告身份只能来自工具结果，禁止编造。
    agent-service/prompts/shopping_agent.md:15:- 面对商品推荐或任何需要多个步骤的任务，先调用 `update_plan` 写出明确的 Plan 和 Plan State，再开始执行。
    agent-service/prompts/shopping_agent.md:27:- 不要在自身推理中重新做意图分类或需求槽位提取。
    agent-service/prompts/shopping_agent.md:29:- 当前只支持 `product_recommendation`、`order_query`、`after_sales` 和 `unknown`。
    agent-service/prompts/shopping_agent.md:33:- 如果 `requires_clarification = true`，只询问 `clarification_question`，不要调用业务工具。
    agent-service/prompts/shopping_agent.md:38:- `product_recommendation`：依次调用 `collect_recommendation_context`、
    agent-service/prompts/shopping_agent.md:39:  `generate_recommendation_spec`、`search_organic_candidates`、
    agent-service/prompts/shopping_agent.md:40:  `search_ad_candidates` 和 `recommend_products`。
    agent-service/prompts/shopping_agent.md:43:- `unknown`：普通回答或提出一个澄清问题，不调用推荐、订单或售后业务工具。
    agent-service/prompts/shopping_agent.md:45:## 推荐主流程
    agent-service/prompts/shopping_agent.md:47:当 `primary_intent = product_recommendation` 时：
    agent-service/prompts/shopping_agent.md:49:1. 调用 `collect_recommendation_context` 收集画像、购物车、浏览、订单和商品目录。
    agent-service/prompts/shopping_agent.md:50:2. 调用 `generate_recommendation_spec`，由独立 Prompt 和模型生成推荐 SPEC。
    agent-service/prompts/shopping_agent.md:54:4. 调用无参数工具 `recommend_products`，只读取两路搜索 Action 的缓存候选，
    agent-service/prompts/shopping_agent.md:58:也不要重复解释用户需求。两个搜索 Action 必须分别保留自己的候选和状态，不要在
    agent-service/prompts/shopping_agent.md:60:如果上下文收集或 SPEC 生成返回 unavailable，应告知用户暂时无法完成推荐并请其
    agent-service/prompts/shopping_agent.md:72:`recommend_products` 会返回以下状态之一：
    agent-service/prompts/shopping_agent.md:74:- `accepted`：无需语义终排，工具已经按公式提交自然推荐 Top 2。
    agent-service/prompts/shopping_agent.md:75:- `requires_semantic_ranking`：存在超过自然推荐最低分的广告候选，必须调用独立终排工具。
    agent-service/prompts/shopping_agent.md:79:信息源缺失或 unavailable 时继续执行，不得因此中断推荐，也不得谎称用户没有记录。独立数据源工具仍可用于回答用户的具体追问或排查问题。
    agent-service/prompts/shopping_agent.md:83:只有 `recommend_products` 返回 `requires_semantic_ranking` 时，才调用 `rerank_recommendations`。
    agent-service/prompts/shopping_agent.md:85:- 该工具拥有独立 Prompt，会综合公式分数、商品语义、场景、库存、价格和候选取舍。
    agent-service/prompts/shopping_agent.md:94:  因此最终文字回答仍需清楚写出推荐商品名称、价格、推荐理由，并明确标出广告商品。
    agent-service/prompts/shopping_agent.md:95:- 完成第一个推荐意图后，如果存在 `pending_intents`，必须询问用户是否继续处理
    agent-service/prompts/shopping_agent.md:98:## 最终推荐
    agent-service/prompts/shopping_agent.md:100:- 公式路径最多输出 2 个自然推荐商品。
    agent-service/prompts/shopping_agent.md:101:- 语义终排路径最多输出 2 个自然推荐商品和 1 个广告商品，总计最多 3 个。
    agent-service/prompts/shopping_agent.md:102:- 存在自然推荐商品时，广告不能排在第一位。
    agent-service/prompts/shopping_agent.md:103:- 宁缺毋滥；可以不推荐任何商品。
    agent-service/prompts/shopping_agent.md:106:- 每件商品说明适合谁、核心卖点以及为什么符合当前需求。
    agent-service/prompts/shopping_agent.md:107:- 有差异时帮助用户做取舍，不要为了凑数量推荐不相关、缺货或超预算商品。
    agent-service/prompts/shopping_agent.md:114:- 用户使用“第一个”“刚才第二个”等指代时，结合上一轮推荐商品的结构化列表和对话确定商品；无法确定时只追问一个关键问题。
    agent-service/prompts/shopping_agent.md:115:- 创建订单时只传商品 ID 和数量，不传价格。价格、库存和总额以商城订单服务返回结果为准。
    agent-service/prompts/shopping_agent.md:123:- 用户修改预算或场景时，以最新需求重新查询。
    agent-service/prompts/shopping_agent.md:124:- 信息不足且会影响推荐质量时，只追问一个最关键的问题，例如预算、使用场景或收礼对象。
    agent-service/prompts/shopping_agent.md:125:- 如果用户已经给出足够信息，直接推荐，不要重复询问。
    agent-service/prompts/shopping_agent.md:130:- 先给结论，再给推荐理由。
    agent-service/src/agent_service/recommendation_spec.py:28:    / "recommendation_spec.md"
    agent-service/src/agent_service/recommendation_spec.py:33:    """Raised when recommendation SPEC generation fails."""
    agent-service/src/agent_service/recommendation_spec.py:59:            "recommendation SPEC did not return a JSON object"
    agent-service/src/agent_service/recommendation_spec.py:65:            "recommendation SPEC returned invalid JSON"
    agent-service/src/agent_service/recommendation_spec.py:69:            "recommendation SPEC JSON must be an object"
    agent-service/src/agent_service/recommendation_spec.py:95:    spec: RecommendationSpec,
    agent-service/src/agent_service/recommendation_spec.py:99:    hard = spec.hard_constraints
    agent-service/src/agent_service/recommendation_spec.py:126:        scenario = spec.scenario
    agent-service/src/agent_service/recommendation_spec.py:131:        for query in spec.search_queries
    agent-service/src/agent_service/recommendation_spec.py:136:    return spec.model_copy(
    agent-service/src/agent_service/recommendation_spec.py:144:                else spec.usage
    agent-service/src/agent_service/recommendation_spec.py:149:                else spec.recipient
    agent-service/src/agent_service/recommendation_spec.py:177:            name="recommendation-spec-generator",
    agent-service/src/agent_service/recommendation_spec.py:220:                action_name="recommendation_spec",
    agent-service/src/agent_service/recommendation_spec.py:231:                "recommendation SPEC model call failed: "
    agent-service/src/agent_service/recommendation_spec.py:237:                "recommendation SPEC returned non-text output"
    agent-service/src/agent_service/recommendation_spec.py:240:            spec = RecommendationSpec.model_validate(
    agent-service/src/agent_service/recommendation_spec.py:245:                "recommendation SPEC returned invalid data"
    agent-service/src/agent_service/recommendation_spec.py:247:        return _apply_explicit_goal_constraints(spec, goal)
    agent-service/src/agent_service/agent_runner.py:69:from .recommendation_reranker import (
    agent-service/src/agent_service/agent_runner.py:76:from .recommendation_scoring import build_recommendation_batch
    agent-service/src/agent_service/agent_runner.py:77:from .recommendation_spec import (
    agent-service/src/agent_service/agent_runner.py:84:recommendation_spec_logger = logging.getLogger(
    agent-service/src/agent_service/agent_runner.py:126:    previous_recommendations: tuple[Product, ...] = ()
    agent-service/src/agent_service/agent_runner.py:131:    recommendation_context: RecommendationContextSnapshot | None = None
    agent-service/src/agent_service/agent_runner.py:132:    recommendation_spec: RecommendationSpec | None = None
    agent-service/src/agent_service/agent_runner.py:133:    recommendation_spec_generator: RecommendationSpecGenerator | None = None
    agent-service/src/agent_service/agent_runner.py:147:    recommendation_batch: RecommendationBatch | None = None
    agent-service/src/agent_service/agent_runner.py:186:                "failed to confirm recommended product %s",
    agent-service/src/agent_service/agent_runner.py:235:            "message": f"{source}暂时不可用，可以继续使用其他来源推荐",
    agent-service/src/agent_service/agent_runner.py:267:def recommendation_demand_from_goal(
    agent-service/src/agent_service/agent_runner.py:269:    spec: RecommendationSpec | None = None,
    agent-service/src/agent_service/agent_runner.py:272:    hard = spec.hard_constraints if spec is not None else None
    agent-service/src/agent_service/agent_runner.py:277:        scenario = spec.scenario if spec is not None else "general"
    agent-service/src/agent_service/agent_runner.py:279:    if query is None and goal.primary_intent == "product_recommendation":
    agent-service/src/agent_service/agent_runner.py:281:            spec.search_queries[0]
    agent-service/src/agent_service/agent_runner.py:282:            if spec is not None and spec.search_queries
    agent-service/src/agent_service/agent_runner.py:303:    spec_required = hard.required_tags if hard is not None else []
    agent-service/src/agent_service/agent_runner.py:304:    spec_excluded = hard.excluded_tags if hard is not None else []
    agent-service/src/agent_service/agent_runner.py:321:        required_tags=explicit_required or spec_required,
    agent-service/src/agent_service/agent_runner.py:322:        excluded_tags=list(dict.fromkeys([*explicit_excluded, *spec_excluded])),
    agent-service/src/agent_service/agent_runner.py:326:            or (spec.usage if spec is not None else None)
    agent-service/src/agent_service/agent_runner.py:330:            or (spec.recipient if spec is not None else None)
    agent-service/src/agent_service/agent_runner.py:344:    previous_recommendations: Sequence[Product] = (),
    agent-service/src/agent_service/agent_runner.py:356:    recommendation_context = [
    agent-service/src/agent_service/agent_runner.py:365:        for index, product in enumerate(previous_recommendations, start=1)
    agent-service/src/agent_service/agent_runner.py:382:        "## 上一轮推荐商品\n\n"
    agent-service/src/agent_service/agent_runner.py:383:        "以下商品按上一轮推荐顺序编号，可用于解析“第一个”“第二个”等指代。"
    agent-service/src/agent_service/agent_runner.py:385:        f"```json\n{json.dumps(recommendation_context, ensure_ascii=False, indent=2)}\n```\n\n"
    agent-service/src/agent_service/agent_runner.py:399:    recommendation_spec_generator: RecommendationSpecGenerator | None = None,
    agent-service/src/agent_service/agent_runner.py:404:    if recommendation_spec_generator is not None:
    agent-service/src/agent_service/agent_runner.py:405:        context.recommendation_spec_generator = recommendation_spec_generator
    agent-service/src/agent_service/agent_runner.py:417:            "读取 agent-service 当前维护的用户画像。推荐时优先使用，"
    agent-service/src/agent_service/agent_runner.py:434:            "从 mall-service 的大数据/推荐平台读取用户画像。不存在时继续推荐。"
    agent-service/src/agent_service/agent_runner.py:515:        name_override="get_product_recommendations",
    agent-service/src/agent_service/agent_runner.py:517:            "请求商城商品推荐候选。泛化推荐优先使用；传入从用户需求中"
    agent-service/src/agent_service/agent_runner.py:518:            "提取的关键词、分类和价格条件。最多返回 10 件。"
    agent-service/src/agent_service/agent_runner.py:522:    async def get_product_recommendations_tool(
    agent-service/src/agent_service/agent_runner.py:530:            candidates = await context.mall.get_product_recommendations(
    agent-service/src/agent_service/agent_runner.py:539:            logger.warning("product recommendation source failed", exc_info=True)
    agent-service/src/agent_service/agent_runner.py:540:            return unavailable_payload("商品推荐")
    agent-service/src/agent_service/agent_runner.py:545:        name_override="get_ad_recommendations",
    agent-service/src/agent_service/agent_runner.py:548:            "必须继续检查用户需求、库存和价格。"
    agent-service/src/agent_service/agent_runner.py:552:    async def get_ad_recommendations_tool(
    agent-service/src/agent_service/agent_runner.py:559:            candidates = await context.mall.get_ad_recommendations(
    agent-service/src/agent_service/agent_runner.py:568:            return unavailable_payload("广告推荐")
    agent-service/src/agent_service/agent_runner.py:575:            "按关键词、分类和价格搜索商城商品，作为推荐接口的补充或兜底。"
    agent-service/src/agent_service/agent_runner.py:607:            "按商品 ID 查询权威价格、库存和描述。准备推荐具体商品时可调用。"
    agent-service/src/agent_service/agent_runner.py:632:            "只能使用当前或上一轮推荐中的商品 ID；不确定时先追问，不要下单。"
    agent-service/src/agent_service/agent_runner.py:649:                "以下商品不在当前或上一轮推荐中："
    agent-service/src/agent_service/agent_runner.py:740:                previous_recommendations=list(
    agent-service/src/agent_service/agent_runner.py:741:                    context.previous_recommendations
    agent-service/src/agent_service/agent_runner.py:758:        name_override="collect_recommendation_context",
    agent-service/src/agent_service/agent_runner.py:761:            "只在 primary_intent 为 product_recommendation 时调用。工具只返回"
    agent-service/src/agent_service/agent_runner.py:766:    async def collect_recommendation_context_tool() -> str:
    agent-service/src/agent_service/agent_runner.py:770:        if goal.primary_intent != "product_recommendation":
    agent-service/src/agent_service/agent_runner.py:771:            return rejected("当前 primary_intent 不是商品推荐")
    agent-service/src/agent_service/agent_runner.py:772:        if context.recommendation_context is not None:
    agent-service/src/agent_service/agent_runner.py:773:            snapshot = context.recommendation_context
    agent-service/src/agent_service/agent_runner.py:846:        context.recommendation_context = RecommendationContextSnapshot(
    agent-service/src/agent_service/agent_runner.py:868:        name_override="generate_recommendation_spec",
    agent-service/src/agent_service/agent_runner.py:872:            "广告搜索前调用，只允许处理 product_recommendation。"
    agent-service/src/agent_service/agent_runner.py:876:    async def generate_recommendation_spec_tool() -> str:
    agent-service/src/agent_service/agent_runner.py:880:        if goal.requires_clarification:
    agent-service/src/agent_service/agent_runner.py:882:        if goal.primary_intent != "product_recommendation":
    agent-service/src/agent_service/agent_runner.py:883:            return rejected("当前 primary_intent 不是商品推荐")
    agent-service/src/agent_service/agent_runner.py:884:        snapshot = context.recommendation_context
    agent-service/src/agent_service/agent_runner.py:886:            return rejected("请先调用 collect_recommendation_context")
    agent-service/src/agent_service/agent_runner.py:887:        if context.recommendation_spec is not None:
    agent-service/src/agent_service/agent_runner.py:891:                    "recommendation_spec": (
    agent-service/src/agent_service/agent_runner.py:892:                        context.recommendation_spec.model_dump(mode="json")
    agent-service/src/agent_service/agent_runner.py:897:        if context.recommendation_spec_generator is None:
    agent-service/src/agent_service/agent_runner.py:900:            spec = await context.recommendation_spec_generator.generate(
    agent-service/src/agent_service/agent_runner.py:910:            logger.warning("recommendation SPEC generation failed: %s", exc)
    agent-service/src/agent_service/agent_runner.py:912:        context.recommendation_spec = spec
    agent-service/src/agent_service/agent_runner.py:916:        spec_payload = redact_payload(
    agent-service/src/agent_service/agent_runner.py:917:            spec.model_dump(mode="json"),
    agent-service/src/agent_service/agent_runner.py:921:        recommendation_spec_logger.debug(
    agent-service/src/agent_service/agent_runner.py:924:                "event": "agent.recommendation_spec.generated",
    agent-service/src/agent_service/agent_runner.py:925:                "agent.recommendation_spec": spec_payload,
    agent-service/src/agent_service/agent_runner.py:926:                "agent.recommendation_spec.search_query_count": len(
    agent-service/src/agent_service/agent_runner.py:927:                    spec.search_queries
    agent-service/src/agent_service/agent_runner.py:929:                "agent.recommendation_spec.confidence": spec.confidence,
    agent-service/src/agent_service/agent_runner.py:935:                "recommendation_spec": spec.model_dump(mode="json"),
    agent-service/src/agent_service/agent_runner.py:950:        snapshot = context.recommendation_context
    agent-service/src/agent_service/agent_runner.py:951:        spec = context.recommendation_spec
    agent-service/src/agent_service/agent_runner.py:952:        if goal is None or snapshot is None or spec is None:
    agent-service/src/agent_service/agent_runner.py:955:                "collect_recommendation_context 和 "
    agent-service/src/agent_service/agent_runner.py:956:                "generate_recommendation_spec"
    agent-service/src/agent_service/agent_runner.py:962:                await context.mall.search_organic_with_spec(spec, limit=10)
    agent-service/src/agent_service/agent_runner.py:973:            "organic_spec_search": organic_status,
    agent-service/src/agent_service/agent_runner.py:995:        snapshot = context.recommendation_context
    agent-service/src/agent_service/agent_runner.py:996:        spec = context.recommendation_spec
    agent-service/src/agent_service/agent_runner.py:997:        if goal is None or snapshot is None or spec is None:
    agent-service/src/agent_service/agent_runner.py:1000:                "collect_recommendation_context 和 "
    agent-service/src/agent_service/agent_runner.py:1001:                "generate_recommendation_spec"
    agent-service/src/agent_service/agent_runner.py:1006:                await context.mall.search_ads_with_spec(spec, limit=10)
    agent-service/src/agent_service/agent_runner.py:1027:        name_override="recommend_products",
    agent-service/src/agent_service/agent_runner.py:1036:    async def recommend_products_tool() -> str:
    agent-service/src/agent_service/agent_runner.py:1039:            return rejected("请先调用 understand_goal 理解用户需求")
    agent-service/src/agent_service/agent_runner.py:1040:        if goal.requires_clarification:
    agent-service/src/agent_service/agent_runner.py:1042:        if goal.primary_intent != "product_recommendation":
    agent-service/src/agent_service/agent_runner.py:1043:            return rejected("当前 primary_intent 不是商品推荐")
    agent-service/src/agent_service/agent_runner.py:1044:        snapshot = context.recommendation_context
    agent-service/src/agent_service/agent_runner.py:1046:            return rejected("请先调用 collect_recommendation_context")
    agent-service/src/agent_service/agent_runner.py:1047:        spec = context.recommendation_spec
    agent-service/src/agent_service/agent_runner.py:1048:        if spec is None:
    agent-service/src/agent_service/agent_runner.py:1049:            return rejected("请先调用 generate_recommendation_spec")
    agent-service/src/agent_service/agent_runner.py:1055:        demand = recommendation_demand_from_goal(goal, spec)
    agent-service/src/agent_service/agent_runner.py:1068:        batch = build_recommendation_batch(
    agent-service/src/agent_service/agent_runner.py:1080:        context.recommendation_batch = batch
    agent-service/src/agent_service/agent_runner.py:1103:        name_override="rerank_recommendations",
    agent-service/src/agent_service/agent_runner.py:1105:            "独立的语义终排工具。仅在 recommend_products 返回 "
    agent-service/src/agent_service/agent_runner.py:1112:    async def rerank_recommendations_tool(
    agent-service/src/agent_service/agent_runner.py:1115:        batch = context.recommendation_batch
    agent-service/src/agent_service/agent_runner.py:1117:            return rejected("请先调用 recommend_products 生成候选")
    agent-service/src/agent_service/agent_runner.py:1212:                timespec="milliseconds"
    agent-service/src/agent_service/agent_runner.py:1225:        collect_recommendation_context_tool,
    agent-service/src/agent_service/agent_runner.py:1226:        generate_recommendation_spec_tool,
    agent-service/src/agent_service/agent_runner.py:1229:        recommend_products_tool,
    agent-service/src/agent_service/agent_runner.py:1230:        rerank_recommendations_tool,
    agent-service/src/agent_service/agent_runner.py:1237:        get_product_recommendations_tool,
    agent-service/src/agent_service/agent_runner.py:1238:        get_ad_recommendations_tool,
    agent-service/src/agent_service/agent_runner.py:1265:    previous_recommendations: Sequence[Product] = (),
    agent-service/src/agent_service/agent_runner.py:1287:        previous_recommendations=tuple(previous_recommendations),
    agent-service/src/agent_service/agent_runner.py:1291:    context.remember_products(previous_recommendations)
    agent-service/src/agent_service/agent_runner.py:1294:    recommendations_emitted = False
    agent-service/src/agent_service/agent_runner.py:1299:            previous_recommendations,
    agent-service/src/agent_service/agent_runner.py:1321:        recommendation_spec_generator = AgentRecommendationSpecGenerator(
    agent-service/src/agent_service/agent_runner.py:1337:                recommendation_spec_generator=recommendation_spec_generator,
    agent-service/src/agent_service/agent_runner.py:1435:                        and not recommendations_emitted
    agent-service/src/agent_service/agent_runner.py:1437:                        recommendations_emitted = True
    agent-service/src/agent_service/agent_runner.py:1439:                            "type": "recommendations",
    agent-service/src/agent_service/agent_runner.py:1463:        if context.selected_products and not recommendations_emitted:
    agent-service/src/agent_service/agent_runner.py:1464:            recommendations_emitted = True
    agent-service/src/agent_service/agent_runner.py:1466:                "type": "recommendations",
    agent-service/src/agent_service/agent_runner.py:1490:            "recommendations": [
    agent-service/src/agent_service/agent_runner.py:1499:            "recommendation_spec": (
    agent-service/src/agent_service/agent_runner.py:1500:                context.recommendation_spec.model_dump(mode="json")
    agent-service/src/agent_service/agent_runner.py:1501:                if context.recommendation_spec is not None
    agent-service/src/agent_service/agent_runner.py:1521:            "recommendations": [
    agent-service/src/agent_service/agent_runner.py:1530:            "recommendation_spec": (
    agent-service/src/agent_service/agent_runner.py:1531:                context.recommendation_spec.model_dump(mode="json")
    agent-service/src/agent_service/agent_runner.py:1532:                if context.recommendation_spec is not None
    agent-service/src/agent_service/agent_runner.py:1543:                "当前多源推荐流程至少需要 10 个回合。"
    agent-service/src/agent_service/agent_runner.py:1558:            "recommendations": [
    agent-service/src/agent_service/agent_runner.py:1567:            "recommendation_spec": (
    agent-service/src/agent_service/agent_runner.py:1568:                context.recommendation_spec.model_dump(mode="json")
    agent-service/src/agent_service/agent_runner.py:1569:                if context.recommendation_spec is not None
    agent-service/src/agent_service/agent_runner.py:1598:            "recommendations": [
    agent-service/src/agent_service/agent_runner.py:1607:            "recommendation_spec": (
    agent-service/src/agent_service/agent_runner.py:1608:                context.recommendation_spec.model_dump(mode="json")
    agent-service/src/agent_service/agent_runner.py:1609:                if context.recommendation_spec is not None
    mall-service/src/mall_service/recommendations.py:26:def _recommend_scores(user_id: int) -> dict[str, tuple[float, list[str]]]:
    mall-service/src/mall_service/recommendations.py:68:def recommend_products(
    mall-service/src/mall_service/recommendations.py:78:    scores = _recommend_scores(request.user_id)
    mall-service/src/mall_service/recommendations.py:82:            source="product_recommendation",
    mall-service/src/mall_service/recommendations.py:92:def recommend_ads(request: AdRecommendationRequest) -> list[ProductCandidate]:
    agent-service/src/agent_service/storage.py:27:    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    agent-service/src/agent_service/storage.py:293:        recommendations = [
    agent-service/src/agent_service/storage.py:295:            for product in metadata.get("recommendations", [])
    agent-service/src/agent_service/storage.py:317:        recommendation_spec: RecommendationSpec | None = None
    agent-service/src/agent_service/storage.py:318:        if isinstance(metadata.get("recommendation_spec"), dict):
    agent-service/src/agent_service/storage.py:320:                recommendation_spec = RecommendationSpec.model_validate(
    agent-service/src/agent_service/storage.py:321:                    metadata["recommendation_spec"]
    agent-service/src/agent_service/storage.py:324:                recommendation_spec = None
    agent-service/src/agent_service/storage.py:336:            recommendations=recommendations,
    agent-service/src/agent_service/storage.py:340:            recommendation_spec=recommendation_spec,
    mall-service/src/mall_service/orders.py:100:            ordered_at=now.isoformat(timespec="milliseconds"),
    mall-service/src/mall_service/orders.py:108:                timespec="milliseconds"
    mall-service/src/mall_service/orders.py:152:                "paid_at": _now().isoformat(timespec="milliseconds"),
    agent-service/src/agent_service/recommendation_reranker.py:22:    / "recommendation_reranker.md"
    agent-service/src/agent_service/recommendation_reranker.py:27:    """Raised when semantic recommendation reranking cannot be completed."""
    agent-service/src/agent_service/recommendation_reranker.py:140:            name="recommendation-semantic-reranker",
    agent-service/src/agent_service/recommendation_reranker.py:171:                "semantic recommendation reranker failed: "
    agent-service/src/agent_service/recommendation_reranker.py:177:                "semantic recommendation reranker returned non-text output"
    agent-service/src/agent_service/recommendation_reranker.py:185:                "semantic recommendation reranker returned invalid data"
    agent-service/src/agent_service/models.py:121:    source: Literal["recommendation_platform"]
    agent-service/src/agent_service/models.py:139:    source: Literal["product_recommendation", "advertisement"]
    agent-service/src/agent_service/models.py:171:    requires_clarification: bool = False
    agent-service/src/agent_service/models.py:172:    clarification_question: str | None = Field(default=None, max_length=1_000)
    agent-service/src/agent_service/models.py:183:    requires_clarification: bool = False
    agent-service/src/agent_service/models.py:184:    clarification_question: str | None = Field(default=None, max_length=1_000)
    agent-service/src/agent_service/models.py:283:    "skipped",
    agent-service/src/agent_service/models.py:376:    recommendations: list[Product] = Field(default_factory=list)
    agent-service/src/agent_service/models.py:380:    recommendation_spec: RecommendationSpec | None = None
    mall-service/src/mall_service/search.py:18:    spec: RecommendationSearchSpec,
    mall-service/src/mall_service/search.py:23:    hard = spec.hard_constraints
    mall-service/src/mall_service/search.py:27:    preference_should: list[dict[str, Any]] = []
    mall-service/src/mall_service/search.py:45:    if spec.negative_tags:
    mall-service/src/mall_service/search.py:46:        must_not.append({"terms": {"tags.keyword": spec.negative_tags}})
    mall-service/src/mall_service/search.py:50:        for query in [*spec.search_queries, spec.usage, spec.recipient]
    mall-service/src/mall_service/search.py:67:    for category in spec.preferred_categories:
    mall-service/src/mall_service/search.py:68:        preference_should.append(
    mall-service/src/mall_service/search.py:78:    for tag in spec.preferred_tags:
    mall-service/src/mall_service/search.py:79:        preference_should.append(
    mall-service/src/mall_service/search.py:103:    if preference_should:
    mall-service/src/mall_service/search.py:104:        bool_query["should"] = preference_should
    mall-service/src/mall_service/search.py:123:    spec: RecommendationSearchSpec,
    mall-service/src/mall_service/search.py:129:        "mock_es_query channel=%s spec=%s query=%s",
    mall-service/src/mall_service/search.py:131:        json.dumps(spec.model_dump(mode="json"), ensure_ascii=False),
    mall-service/src/mall_service/search.py:148:def _mock_score(product: Product, spec: RecommendationSearchSpec) -> float:
    mall-service/src/mall_service/search.py:152:        for query in [*spec.search_queries, spec.usage, spec.recipient]
    mall-service/src/mall_service/search.py:156:    if product.category in spec.preferred_categories:
    mall-service/src/mall_service/search.py:158:    score += sum(1 for tag in spec.preferred_tags if tag in product.tags)
    mall-service/src/mall_service/search.py:164:    spec: RecommendationSearchSpec,
    mall-service/src/mall_service/search.py:166:    hard = spec.hard_constraints
    mall-service/src/mall_service/search.py:186:    if product_tags & set(spec.negative_tags):
    mall-service/src/mall_service/search.py:192:    spec: RecommendationSearchSpec,
    mall-service/src/mall_service/search.py:197:        (product, _mock_score(product, spec))
    mall-service/src/mall_service/search.py:199:        if _hard_filter_pass(product, spec)
    mall-service/src/mall_service/search.py:203:        for query in [*spec.search_queries, spec.usage, spec.recipient]
    mall-service/src/mall_service/search.py:221:def search_mock_with_spec(
    mall-service/src/mall_service/search.py:222:    spec: RecommendationSearchSpec,
    mall-service/src/mall_service/search.py:227:    es_query = build_es_query(spec, channel=channel, limit=limit)
    mall-service/src/mall_service/search.py:228:    log_mock_es_query(spec, channel=channel, es_query=es_query)
    mall-service/src/mall_service/search.py:229:    return mock_search_products(spec, limit=limit)
    mall-service/src/mall_service/search.py:232:def search_mock_ads_with_spec(
    mall-service/src/mall_service/search.py:233:    spec: RecommendationSearchSpec,
    mall-service/src/mall_service/search.py:237:    products = search_mock_with_spec(
    mall-service/src/mall_service/search.py:238:        spec,
    mall-service/src/mall_service/search.py:250:                campaign_id="campaign-mock-spec",
    agent-service/src/agent_service/api.py:55:def latest_recommendations(
    agent-service/src/agent_service/api.py:59:        if message.recommendations:
    agent-service/src/agent_service/api.py:60:            return message.recommendations
    agent-service/src/agent_service/api.py:93:    recommendations: dict[str, Product] = {}
    agent-service/src/agent_service/api.py:97:    recommendation_spec: RecommendationSpec | None = None
    agent-service/src/agent_service/api.py:109:            "recommendations": [
    agent-service/src/agent_service/api.py:111:                for product in recommendations.values()
    agent-service/src/agent_service/api.py:123:        if recommendation_spec is not None:
    agent-service/src/agent_service/api.py:124:            metadata["recommendation_spec"] = recommendation_spec.model_dump(
    agent-service/src/agent_service/api.py:149:            previous_recommendations=latest_recommendations(context),
    agent-service/src/agent_service/api.py:163:            if event_type == "recommendations":
    agent-service/src/agent_service/api.py:167:                        recommendations[parsed.id] = parsed
    agent-service/src/agent_service/api.py:228:                if isinstance(event.get("recommendations"), list):
    agent-service/src/agent_service/api.py:229:                    for product_payload in event["recommendations"]:
    agent-service/src/agent_service/api.py:232:                            recommendations[product.id] = product
    agent-service/src/agent_service/api.py:238:                spec_payload = event.get("recommendation_spec")
    agent-service/src/agent_service/api.py:239:                if isinstance(spec_payload, dict):
    agent-service/src/agent_service/api.py:240:                    recommendation_spec = RecommendationSpec.model_validate(
    agent-service/src/agent_service/api.py:241:                        spec_payload
    agent-service/src/agent_service/api.py:269:                if isinstance(event.get("recommendations"), list):
    agent-service/src/agent_service/api.py:270:                    for product_payload in event["recommendations"]:
    agent-service/src/agent_service/api.py:273:                            recommendations[product.id] = product
    agent-service/src/agent_service/api.py:279:                spec_payload = event.get("recommendation_spec")
    agent-service/src/agent_service/api.py:280:                if isinstance(spec_payload, dict):
    agent-service/src/agent_service/api.py:281:                    recommendation_spec = RecommendationSpec.model_validate(
    agent-service/src/agent_service/api.py:282:                        spec_payload
    agent-service/src/agent_service/goal_understanding.py:29:    "product_recommendation": "商品推荐",
    agent-service/src/agent_service/goal_understanding.py:47:        previous_recommendations: list[Product],
    agent-service/src/agent_service/goal_understanding.py:87:        previous_recommendations: list[Product],
    agent-service/src/agent_service/goal_understanding.py:115:            "previous_recommendations": [
    agent-service/src/agent_service/goal_understanding.py:123:                    previous_recommendations,
    agent-service/src/agent_service/goal_understanding.py:178:        requires_clarification = (
    agent-service/src/agent_service/goal_understanding.py:179:            draft.requires_clarification or draft.confidence < 0.55
    agent-service/src/agent_service/goal_understanding.py:181:        clarification_question = draft.clarification_question
    agent-service/src/agent_service/goal_understanding.py:182:        if requires_clarification and not clarification_question:
    agent-service/src/agent_service/goal_understanding.py:183:            clarification_question = "你希望我具体帮你处理哪件事？"
    agent-service/src/agent_service/goal_understanding.py:193:            requires_clarification=requires_clarification,
    agent-service/src/agent_service/goal_understanding.py:194:            clarification_question=clarification_question,
    mall-service/src/mall_service/models.py:108:    source: Literal["recommendation_platform"] = "recommendation_platform"
    mall-service/src/mall_service/models.py:131:    source: Literal["product_recommendation", "advertisement"]
    mall-service/src/mall_service/models.py:199:    spec: RecommendationSearchSpec
    agent-service/src/agent_service/mall_client.py:148:    async def search_organic_with_spec(
    agent-service/src/agent_service/mall_client.py:150:        spec: RecommendationSpec,
    agent-service/src/agent_service/mall_client.py:157:                "spec": spec.model_dump(mode="json"),
    agent-service/src/agent_service/mall_client.py:212:    async def get_product_recommendations(
    agent-service/src/agent_service/mall_client.py:223:            "/api/recommendations/products",
    agent-service/src/agent_service/mall_client.py:235:    async def get_ad_recommendations(
    agent-service/src/agent_service/mall_client.py:245:            "/api/recommendations/ads",
    agent-service/src/agent_service/mall_client.py:256:    async def search_ads_with_spec(
    agent-service/src/agent_service/mall_client.py:258:        spec: RecommendationSpec,
    agent-service/src/agent_service/mall_client.py:265:                "spec": spec.model_dump(mode="json"),
    agent-service/src/agent_service/mall_gateway.py:28:    async def search_organic_with_spec(
    agent-service/src/agent_service/mall_gateway.py:30:        spec: RecommendationSpec,
    agent-service/src/agent_service/mall_gateway.py:55:    async def get_product_recommendations(
    agent-service/src/agent_service/mall_gateway.py:65:    async def get_ad_recommendations(
    agent-service/src/agent_service/mall_gateway.py:74:    async def search_ads_with_spec(
    agent-service/src/agent_service/mall_gateway.py:76:        spec: RecommendationSpec,
    agent-service/tests/test_recommendation_scoring.py:16:from agent_service.recommendation_scoring import build_recommendation_batch
    agent-service/tests/test_recommendation_scoring.py:59:    return build_recommendation_batch(
    agent-service/tests/test_recommendation_scoring.py:192:        source="recommendation_platform",
    agent-service/tests/test_recommendation_scoring.py:199:    with_profile = build_recommendation_batch(
    agent-service/tests/test_recommendation_scoring.py:262:    batch = build_recommendation_batch(
    agent-service/tests/test_recommendation_scoring.py:289:    batch = build_recommendation_batch(
    agent-service/tests/test_chat.py:16:    assert "抹茶气泡水" in compose_reply("推荐一下", products)
    agent-service/tests/test_chat.py:20:    assert "暂时" in compose_reply("推荐一下", [])
    agent-service/src/agent_service/observability/log_exporters.py:27:    ).isoformat(timespec="milliseconds")
    agent-service/src/agent_service/observability/logging.py:78:            ).isoformat(timespec="milliseconds"),
    mall-service/src/mall_service/catalog.py:11:        badge="通勤推荐",
    mall-service/src/mall_service/catalog.py:113:    "推荐",
    agent-service/tests/test_storage.py:88:    assert conversation.messages[0].recommendations == []
    agent-service/tests/test_agent_api.py:62:                "title": "提交推荐",
    agent-service/tests/test_agent_api.py:63:                "objective": "生成最终推荐",
    agent-service/tests/test_agent_api.py:77:    "next_action": "提交最终推荐",
    agent-service/tests/test_agent_api.py:107:    "primary_intent": "product_recommendation",
    agent-service/tests/test_agent_api.py:108:    "intents": ["product_recommendation", "order_query"],
    agent-service/tests/test_agent_api.py:110:    "goal": "推荐商品并查询订单",
    agent-service/tests/test_agent_api.py:114:    "requires_clarification": False,
    agent-service/tests/test_agent_api.py:115:    "clarification_question": None,
    agent-service/tests/test_agent_api.py:120:    "goal_summary": "推荐通勤商品",
    agent-service/tests/test_agent_api.py:147:    previous_recommendations=None,
    agent-service/tests/test_agent_api.py:176:        "type": "recommendations",
    agent-service/tests/test_agent_api.py:199:        "recommendations": [RECOMMENDED_PRODUCT],
    agent-service/tests/test_agent_api.py:201:        "recommendation_spec": RECOMMENDATION_SPEC,
    agent-service/tests/test_agent_api.py:216:        response = client.post("/api/chat", json={"message": "推荐一件商品"})
    agent-service/tests/test_agent_api.py:254:    assert '"type": "recommendations"' in response.text
    agent-service/tests/test_agent_api.py:271:    assert detail.messages[1].recommendations[0].id == "tote"
    agent-service/tests/test_agent_api.py:272:    assert detail.messages[1].recommendations[0].is_ad is True
    agent-service/tests/test_agent_api.py:273:    assert detail.messages[1].recommendations[0].ad_label == "广告"
    agent-service/tests/test_agent_api.py:278:    assert detail.messages[1].recommendation_spec is not None
    agent-service/tests/test_agent_api.py:279:    assert detail.messages[1].recommendation_spec.search_queries == [
    agent-service/tests/test_agent_api.py:337:        previous_recommendations=None,
    agent-service/tests/test_agent_api.py:378:    conversation_id = store.create_conversation(1, "继续推荐")
    agent-service/tests/test_agent_api.py:379:    store.add_message(conversation_id, "user", "先推荐商品", "completed")
    agent-service/tests/test_agent_api.py:387:            "recommendations": [
    agent-service/tests/test_agent_api.py:407:        previous_recommendations=None,
    agent-service/tests/test_agent_api.py:412:        captured["previous_recommendations"] = previous_recommendations
    agent-service/tests/test_agent_api.py:440:    assert captured["previous_recommendations"][0].id == "tote"
    agent-service/tests/test_agent_api.py:450:    store.add_message(conversation_id, "assistant", "推荐托特包", "completed")
    agent-service/tests/test_agent_api.py:459:    assert detail_response.json()["messages"][1]["content"] == "推荐托特包"
    agent-service/tests/test_agent_runner.py:36:from agent_service.recommendation_reranker import (
    agent-service/tests/test_agent_runner.py:40:from agent_service.recommendation_spec import AgentRecommendationSpecGenerator
    agent-service/tests/test_agent_runner.py:61:    plan_id: str = "plan-recommendation",
    agent-service/tests/test_agent_runner.py:63:    summary: str = "准备收集推荐所需信息",
    agent-service/tests/test_agent_runner.py:68:            "goal": "为用户生成合适的商品推荐",
    agent-service/tests/test_agent_runner.py:88:                    "title": "提交最终推荐",
    agent-service/tests/test_agent_runner.py:148:def prepare_recommendation_context(
    agent-service/tests/test_agent_runner.py:151:    spec: RecommendationSpec | None = None,
    agent-service/tests/test_agent_runner.py:153:    invoke_tool(context, "collect_recommendation_context", {})
    agent-service/tests/test_agent_runner.py:154:    context.recommendation_spec = spec or recommendation_spec()
    agent-service/tests/test_agent_runner.py:191:        previous_recommendations: list[Product],
    agent-service/tests/test_agent_runner.py:221:    ordered_intents = intents or ["product_recommendation"]
    agent-service/tests/test_agent_runner.py:226:        goal=f"推荐与 {query} 相关的商品",
    agent-service/tests/test_agent_runner.py:241:def recommendation_spec(
    agent-service/tests/test_agent_runner.py:246:        goal_summary="推荐预算 300 元以内的通勤商品",
    agent-service/tests/test_agent_runner.py:287:                reason="符合当前需求",
    agent-service/tests/test_agent_runner.py:294:def recommendation_batch(
    agent-service/tests/test_agent_runner.py:399:def test_recommendation_and_ad_tools_register_candidates() -> None:
    agent-service/tests/test_agent_runner.py:405:            "get_product_recommendations",
    agent-service/tests/test_agent_runner.py:412:            "get_ad_recommendations",
    agent-service/tests/test_agent_runner.py:451:    prepare_recommendation_context(context)
    agent-service/tests/test_agent_runner.py:454:        "recommend_products",
    agent-service/tests/test_agent_runner.py:489:def test_create_order_rejects_product_outside_known_recommendations() -> None:
    agent-service/tests/test_agent_runner.py:506:        current_user_request="推荐一个通勤包，然后查一下我的订单",
    agent-service/tests/test_agent_runner.py:510:            intents=["product_recommendation", "order_query"],
    agent-service/tests/test_agent_runner.py:520:        "product_recommendation"
    agent-service/tests/test_agent_runner.py:534:                                "product_recommendation",
    agent-service/tests/test_agent_runner.py:537:                            "goal": "推荐通勤包并查询订单",
    agent-service/tests/test_agent_runner.py:541:                            "requires_clarification": False,
    agent-service/tests/test_agent_runner.py:542:                            "clarification_question": None,
    agent-service/tests/test_agent_runner.py:557:            current_message="推荐一个通勤包，然后查订单",
    agent-service/tests/test_agent_runner.py:561:                    content="推荐一个通勤包，然后查订单",
    agent-service/tests/test_agent_runner.py:565:            previous_recommendations=[],
    agent-service/tests/test_agent_runner.py:570:    assert result.primary_intent == "product_recommendation"
    agent-service/tests/test_agent_runner.py:578:def test_collect_context_and_generate_recommendation_spec_are_separate_actions(
    agent-service/tests/test_agent_runner.py:583:    context.recommendation_spec_generator = StaticRecommendationSpecGenerator(
    agent-service/tests/test_agent_runner.py:584:        recommendation_spec()
    agent-service/tests/test_agent_runner.py:588:        invoke_tool(context, "collect_recommendation_context", {})
    agent-service/tests/test_agent_runner.py:595:            invoke_tool(context, "generate_recommendation_spec", {})
    agent-service/tests/test_agent_runner.py:601:    assert context.recommendation_spec is not None
    agent-service/tests/test_agent_runner.py:602:    assert context.recommendation_spec.search_queries == ["通勤", "办公室"]
    agent-service/tests/test_agent_runner.py:603:    spec_log = next(
    agent-service/tests/test_agent_runner.py:607:        == "agent.recommendation_spec.generated"
    agent-service/tests/test_agent_runner.py:609:    assert getattr(spec_log, "agent.recommendation_spec")[
    agent-service/tests/test_agent_runner.py:613:        getattr(spec_log, "agent.recommendation_spec.search_query_count")
    agent-service/tests/test_agent_runner.py:621:    invoke_tool(context, "collect_recommendation_context", {})
    agent-service/tests/test_agent_runner.py:622:    context.recommendation_spec = recommendation_spec()
    agent-service/tests/test_agent_runner.py:641:def test_recommendation_spec_agent_uses_own_prompt_and_explicit_constraints() -> None:
    agent-service/tests/test_agent_runner.py:644:    invoke_tool(context, "collect_recommendation_context", {})
    agent-service/tests/test_agent_runner.py:645:    snapshot = context.recommendation_context
    agent-service/tests/test_agent_runner.py:690:    spec = asyncio.run(
    agent-service/tests/test_agent_runner.py:702:    assert spec.hard_constraints.max_price_cents == 30000
    agent-service/tests/test_agent_runner.py:703:    assert spec.search_queries == ["通勤包", "轻便通勤包"]
    agent-service/tests/test_agent_runner.py:710:def test_recommend_products_formula_path_selects_top_two() -> None:
    agent-service/tests/test_agent_runner.py:713:    prepare_recommendation_context(
    agent-service/tests/test_agent_runner.py:715:        spec=recommendation_spec(queries=["家居", "居家"]),
    agent-service/tests/test_agent_runner.py:723:            "recommend_products",
    agent-service/tests/test_agent_runner.py:729:    assert context.recommendation_batch is not None
    agent-service/tests/test_agent_runner.py:730:    assert context.recommendation_batch.requires_semantic_ranking is False
    agent-service/tests/test_agent_runner.py:738:def test_recommend_products_returns_no_match_without_eligible_candidates() -> None:
    agent-service/tests/test_agent_runner.py:741:    no_match_spec = recommendation_spec(queries=["宠物用品"]).model_copy(
    agent-service/tests/test_agent_runner.py:748:    prepare_recommendation_context(
    agent-service/tests/test_agent_runner.py:750:        spec=no_match_spec,
    agent-service/tests/test_agent_runner.py:756:            "recommend_products",
    agent-service/tests/test_agent_runner.py:797:    context.recommendation_batch = recommendation_batch(
    agent-service/tests/test_agent_runner.py:806:            "rerank_recommendations",
    agent-service/tests/test_agent_runner.py:846:                    reason="符合通勤需求",
    agent-service/tests/test_agent_runner.py:851:    context.recommendation_batch = recommendation_batch(
    agent-service/tests/test_agent_runner.py:860:            "rerank_recommendations",
    agent-service/tests/test_agent_runner.py:884:                    reason="当前唯一符合需求的候选",
    agent-service/tests/test_agent_runner.py:889:    context.recommendation_batch = recommendation_batch(
    agent-service/tests/test_agent_runner.py:896:        invoke_tool(context, "rerank_recommendations", {})
    agent-service/tests/test_agent_runner.py:916:    batch = recommendation_batch(
    agent-service/tests/test_agent_runner.py:955:            user_request="推荐通勤好物",
    agent-service/tests/test_agent_runner.py:965:    assert "商品推荐语义终排器" in (
    agent-service/tests/test_agent_runner.py:982:    batch = recommendation_batch(
    agent-service/tests/test_agent_runner.py:1015:                            "intents": ["product_recommendation"],
    agent-service/tests/test_agent_runner.py:1016:                            "goal": "推荐预算 300 元以内的通勤商品",
    agent-service/tests/test_agent_runner.py:1024:                            "requires_clarification": False,
    agent-service/tests/test_agent_runner.py:1025:                            "clarification_question": None,
    agent-service/tests/test_agent_runner.py:1033:                    "collect_recommendation_context",
    agent-service/tests/test_agent_runner.py:1040:                    "generate_recommendation_spec",
    agent-service/tests/test_agent_runner.py:1042:                    call_id="call-spec",
    agent-service/tests/test_agent_runner.py:1049:                            "goal_summary": "推荐 300 元以内通勤商品",
    agent-service/tests/test_agent_runner.py:1093:                    "recommend_products",
    agent-service/tests/test_agent_runner.py:1095:                    call_id="call-recommend",
    agent-service/tests/test_agent_runner.py:1100:                    "rerank_recommendations",
    agent-service/tests/test_agent_runner.py:1127:            [assistant_message("我综合你的记录，推荐这两件商品。")],
    agent-service/tests/test_agent_runner.py:1135:                [ConversationMessage(role="user", content="推荐通勤好物")],
    agent-service/tests/test_agent_runner.py:1148:    assert "recommendations" in event_types
    agent-service/tests/test_agent_runner.py:1151:    recommendations = next(
    agent-service/tests/test_agent_runner.py:1154:        if event["type"] == "recommendations"
    agent-service/tests/test_agent_runner.py:1156:    assert [product["id"] for product in recommendations] == [
    agent-service/tests/test_agent_runner.py:1160:    assert recommendations[1]["is_ad"] is True
    agent-service/tests/test_agent_runner.py:1216:def test_purchase_turn_uses_previous_recommendation_and_emits_order() -> None:
    agent-service/tests/test_agent_runner.py:1246:                previous_recommendations=[previous_product],
    agent-service/tests/test_agent_runner.py:1286:                [ConversationMessage(role="user", content="推荐通勤商品")],
    agent-service/tests/test_llm_config.py:45:def test_load_llm_config_rejects_too_few_recommendation_turns(
    agent-service/tests/test_llm_config.py:64:def test_load_llm_config_accepts_high_recommendation_turn_limit(
    ✓ • 0ms

## Activity

    $ rg -n "class (GoalUnderstanding|RecommendationSpec|RecommendationDemand|ShoppingCart|BrowseEvent|OrderRecord|Product)|missing_information|missing_slots|clarification" agent-service/src/agent_service/models.py && sed -n '1,360p' agent-service/src/agent_service/models.py
    6:class Product(BaseModel):
    22:class ProductList(BaseModel):
    27:class BrowseEvent(BaseModel):
    52:class OrderRecord(BaseModel):
    98:class ShoppingCart(BaseModel):
    137:class ProductCandidate(BaseModel):
    145:class RecommendationDemand(BaseModel):
    165:class GoalUnderstandingDraft(BaseModel):
    170:    missing_slots: list[str] = Field(default_factory=list)
    171:    requires_clarification: bool = False
    172:    clarification_question: str | None = Field(default=None, max_length=1_000)
    175:class GoalUnderstandingResult(BaseModel):
    182:    missing_slots: list[str] = Field(default_factory=list)
    183:    requires_clarification: bool = False
    184:    clarification_question: str | None = Field(default=None, max_length=1_000)
    188:class RecommendationSpecHardConstraints(BaseModel):
    196:class RecommendationSpecEvidence(BaseModel):
    202:class RecommendationSpec(BaseModel):
    224:    missing_information: list[str] = Field(default_factory=list)
    from typing import Literal
    
    from pydantic import BaseModel, Field, field_validator
    
    
    class Product(BaseModel):
        id: str
        name: str
        description: str
        price_cents: int
        category: str
        badge: str | None = None
        stock: int | None = None
        tags: list[str] = Field(default_factory=list)
        image_url: str | None = None
        is_ad: bool = False
        ad_label: str | None = None
        ad_id: str | None = None
        campaign_id: str | None = None
    
    
    class ProductList(BaseModel):
        items: list[Product]
        total: int
    
    
    class BrowseEvent(BaseModel):
        event_id: str
        product_id: str
        action: Literal["view", "detail_view"]
        occurred_at: str
        dwell_seconds: int = Field(ge=0)
        source_page: str
    
    
    class OrderItem(BaseModel):
        product_id: str
        name: str
        image_url: str | None = None
        quantity: int = Field(gt=0)
        unit_price_cents: int = Field(ge=0)
        subtotal_cents: int = Field(ge=0)
    
    
    class ShippingAddress(BaseModel):
        recipient: str
        phone_masked: str
        region: str
        detail: str
    
    
    class OrderRecord(BaseModel):
        order_id: str
        user_id: int = 1
        status: Literal[
            "pending_payment",
            "paid",
            "completed",
            "cancelled",
            "refunded",
        ]
        ordered_at: str
        address: ShippingAddress | None = None
        subtotal_cents: int = Field(ge=0)
        shipping_fee_cents: int = Field(default=0, ge=0)
        total_cents: int = Field(ge=0)
        items: list[OrderItem]
        preview_path: str | None = None
        paid_at: str | None = None
        expires_at: str | None = None
    
    
    class CreateOrderItem(BaseModel):
        product_id: str = Field(min_length=1, max_length=100)
        quantity: int = Field(default=1, ge=1, le=99)
    
    
    class OrderLink(BaseModel):
        order_id: str
        status: Literal[
            "pending_payment",
            "paid",
            "completed",
            "cancelled",
            "refunded",
        ]
        total_cents: int
        preview_path: str
        ordered_at: str
    
    
    class CartItem(BaseModel):
        product_id: str
        quantity: int = Field(gt=0)
        added_at: str
    
    
    class ShoppingCart(BaseModel):
        updated_at: str | None = None
        items: list[CartItem] = Field(default_factory=list)
    
    
    class AgentProfile(BaseModel):
        user_id: int
        source: Literal["agent_memory"] = "agent_memory"
        preferred_categories: list[str] = Field(default_factory=list)
        preferred_tags: list[str] = Field(default_factory=list)
        avoid_tags: list[str] = Field(default_factory=list)
        budget_hint_cents: int | None = None
        notes: str | None = None
        updated_at: str
    
    
    class CategoryAffinity(BaseModel):
        category: str
        score: float = Field(ge=0, le=1)
    
    
    class PlatformProfile(BaseModel):
        user_id: int
        source: Literal["recommendation_platform"]
        segments: list[str] = Field(default_factory=list)
        category_affinity: list[CategoryAffinity] = Field(default_factory=list)
        price_band_cents: tuple[int, int] | None = None
        preferred_tags: list[str] = Field(default_factory=list)
        confidence: float = Field(ge=0, le=1)
        updated_at: str
    
    
    class AdInfo(BaseModel):
        is_ad: Literal[True] = True
        ad_id: str
        campaign_id: str
        label: Literal["广告"] = "广告"
    
    
    class ProductCandidate(BaseModel):
        product: Product
        source: Literal["product_recommendation", "advertisement"]
        score: float = Field(ge=0, le=1)
        matched_signals: list[str] = Field(default_factory=list)
        ad: AdInfo | None = None
    
    
    class RecommendationDemand(BaseModel):
        query: str = Field(default="", max_length=500)
        category: str | None = Field(default=None, max_length=100)
        min_price_cents: int | None = Field(default=None, ge=0)
        max_price_cents: int | None = Field(default=None, ge=0)
        required_tags: list[str] = Field(default_factory=list)
        excluded_tags: list[str] = Field(default_factory=list)
        scenario: Literal[
            "general",
            "self",
            "gift",
            "replenishment",
        ] = "general"
        usage: str | None = Field(default=None, max_length=500)
        recipient: str | None = Field(default=None, max_length=200)
    
    
    IntentType = str
    
    
    class GoalUnderstandingDraft(BaseModel):
        intents: list[IntentType] = Field(min_length=1, max_length=5)
        goal: str = Field(min_length=1, max_length=2_000)
        confidence: float = Field(ge=0, le=1)
        slots: dict[str, object] = Field(default_factory=dict)
        missing_slots: list[str] = Field(default_factory=list)
        requires_clarification: bool = False
        clarification_question: str | None = Field(default=None, max_length=1_000)
    
    
    class GoalUnderstandingResult(BaseModel):
        primary_intent: IntentType
        intents: list[IntentType] = Field(min_length=1, max_length=5)
        pending_intents: list[IntentType] = Field(default_factory=list)
        goal: str = Field(min_length=1, max_length=2_000)
        confidence: float = Field(ge=0, le=1)
        slots: dict[str, object] = Field(default_factory=dict)
        missing_slots: list[str] = Field(default_factory=list)
        requires_clarification: bool = False
        clarification_question: str | None = Field(default=None, max_length=1_000)
        pending_intent_question: str | None = Field(default=None, max_length=1_000)
    
    
    class RecommendationSpecHardConstraints(BaseModel):
        category: str | None = Field(default=None, max_length=100)
        min_price_cents: int | None = Field(default=None, ge=0)
        max_price_cents: int | None = Field(default=None, ge=0)
        required_tags: list[str] = Field(default_factory=list)
        excluded_tags: list[str] = Field(default_factory=list)
    
    
    class RecommendationSpecEvidence(BaseModel):
        source: str = Field(min_length=1, max_length=100)
        observation: str = Field(min_length=1, max_length=500)
        influence: Literal["high", "medium", "low"]
    
    
    class RecommendationSpec(BaseModel):
        goal_summary: str = Field(min_length=1, max_length=1_000)
        hard_constraints: RecommendationSpecHardConstraints = Field(
            default_factory=RecommendationSpecHardConstraints
        )
        preferred_categories: list[str] = Field(default_factory=list)
        preferred_tags: list[str] = Field(default_factory=list)
        weak_categories: list[str] = Field(default_factory=list)
        negative_tags: list[str] = Field(default_factory=list)
        search_queries: list[str] = Field(min_length=1, max_length=6)
        scenario: Literal[
            "general",
            "self",
            "gift",
            "replenishment",
        ] = "general"
        usage: str | None = Field(default=None, max_length=500)
        recipient: str | None = Field(default=None, max_length=200)
        source_evidence: list[RecommendationSpecEvidence] = Field(
            default_factory=list
        )
        confidence: float = Field(ge=0, le=1)
        missing_information: list[str] = Field(default_factory=list)
    
    
    SourceStatus = Literal["ok_with_data", "ok_empty", "unavailable"]
    
    
    class SourceEvidence(BaseModel):
        source: Literal[
            "need",
            "cart",
            "browse",
            "order",
            "agent_profile",
            "platform_profile",
        ]
        signal_score: float = Field(ge=0, le=1)
        weighted_points: float = Field(ge=0, le=100)
        reason: str = Field(min_length=1, max_length=300)
    
    
    class ScoredProduct(BaseModel):
        product: Product
        channel: Literal["organic", "ad"]
        score: float = Field(ge=0, le=100)
        confidence: Literal["high", "medium", "low"]
        evidence: list[SourceEvidence] = Field(default_factory=list)
        penalties: list[str] = Field(default_factory=list)
        ad: AdInfo | None = None
    
    
    class RecommendationBatch(BaseModel):
        demand: RecommendationDemand
        organic_candidates: list[ScoredProduct] = Field(default_factory=list)
        ad_candidates: list[ScoredProduct] = Field(default_factory=list)
        cutoff_score: float | None = None
        competitive_ads: list[ScoredProduct] = Field(default_factory=list)
        requires_semantic_ranking: bool = False
        ad_only: bool = False
        source_statuses: dict[str, SourceStatus] = Field(default_factory=dict)
        generated_at: str
    
    
    class SemanticRankingItem(BaseModel):
        product_id: str = Field(min_length=1, max_length=100)
        channel: Literal["organic", "ad"]
        reason: str = Field(min_length=1, max_length=500)
        environmental_fit: str | None = Field(default=None, max_length=500)
    
    
    class SemanticRankingResult(BaseModel):
        items: list[SemanticRankingItem] = Field(default_factory=list)
        summary: str = Field(default="", max_length=1_000)
    
    
    PlanStepStatus = Literal[
        "pending",
        "in_progress",
        "completed",
        "blocked",
        "skipped",
    ]
    
    
    class PlanStep(BaseModel):
        step_id: str = Field(min_length=1, max_length=100)
        title: str = Field(min_length=1, max_length=200)
        objective: str = Field(min_length=1, max_length=1_000)
        kind: str | None = Field(default=None, max_length=100)
        depends_on: list[str] = Field(default_factory=list)
        metadata: dict[str, object] = Field(default_factory=dict)
    
    
    class Plan(BaseModel):
        plan_id: str = Field(min_length=1, max_length=100)
        goal: str = Field(min_length=1, max_length=1_000)
        steps: list[PlanStep] = Field(min_length=1, max_length=50)
    
    
    class PlanStepState(BaseModel):
        step_id: str = Field(min_length=1, max_length=100)
        status: PlanStepStatus
        note: str | None = Field(default=None, max_length=2_000)
    
    
    class PlanState(BaseModel):
        plan: Plan
        status: Literal["active", "completed", "blocked", "cancelled"] = "active"
        current_step_id: str | None = Field(default=None, max_length=100)
        step_states: list[PlanStepState] = Field(default_factory=list)
        summary: str = Field(default="", max_length=2_000)
        next_action: str | None = Field(default=None, max_length=1_000)
        revision: int = Field(default=1, ge=1)
        updated_at: str
    
    
    class ChatRequest(BaseModel):
        message: str = Field(min_length=1, max_length=100_000)
    
        @field_validator("message")
        @classmethod
        def message_must_not_be_blank(cls, value: str) -> str:
            value = value.strip()
            if not value:
                raise ValueError("message must not be blank")
            return value
    
    
    class ChatResponse(BaseModel):
        reply: str
        products: list[Product]
    
    
    class ConversationMessage(BaseModel):
        role: Literal["user", "assistant"]
        content: str = Field(min_length=1, max_length=100_000)
    
        @field_validator("content")
        @classmethod
        def content_must_not_be_blank(cls, value: str) -> str:
            value = value.strip()
            if not value:
                raise ValueError("content must not be blank")
            return value
    
    
    class StreamChatRequest(BaseModel):
        conversation_id: str | None = Field(default=None, max_length=64)
        message: str = Field(min_length=1, max_length=100_000)
    
        @field_validator("message")
        @classmethod
        def stream_message_must_not_be_blank(cls, value: str) -> str:
            value = value.strip()
            if not value:
                raise ValueError("message must not be blank")
            return value
    
    ✓ • 0ms

## Activity

    $ sed -n '260,760p' agent-service/src/agent_service/agent_runner.py
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
    ✓ • 0ms

## Activity

    $ sed -n '760,1320p' agent-service/src/agent_service/agent_runner.py
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
            tool_log_config = (
                get_observability_runtime().config.logs.tool
            )
            spec_payload = redact_payload(
                spec.model_dump(mode="json"),
                redact_keys=tool_log_config.redact_keys,
                max_length=tool_log_config.max_payload_chars,
            )
            recommendation_spec_logger.debug(
                "Recommendation SPEC generated",
                extra={
                    "event": "agent.recommendation_spec.generated",
                    "agent.recommendation_spec": spec_payload,
                    "agent.recommendation_spec.search_query_count": len(
                        spec.search_queries
                    ),
                    "agent.recommendation_spec.confidence": spec.confidence,
                },
            )
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
    
        tools = [
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
        return instrument_tools(
            tools,
            get_observability_runtime().config.logs.tool,
        )
    
    
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
        trace_session = AgentTraceSession(
            model=str(
                getattr(model_override, "model", config.model)
                if model_override is not None
                else config.model
            )
        )
        trace_outcome = "failed"
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
    ✓ • 0ms

## Activity

    $ sed -n '1,360p' agent-service/src/agent_service/api.py && sed -n '1,360p' agent-service/src/agent_service/storage.py
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
        GoalUnderstandingResult,
        OrderLink,
        PlanState,
        Product,
        RecommendationSpec,
        StreamChatRequest,
        StoredMessage,
        ToolTrace,
    )
    from .observability.spans import ChatObservation
    from .observability.telemetry import configure_observability
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
    
    
    def latest_goal_understanding(
        messages: Sequence[StoredMessage],
    ) -> GoalUnderstandingResult | None:
        for message in reversed(messages):
            if message.goal_understanding is not None:
                return message.goal_understanding
        return None
    
    
    async def persisted_agent_stream(
        conversation_id: str,
        conversation_title: str,
        assistant_message_id: str,
        context: Sequence[StoredMessage],
        config: LLMConfig,
        store: ConversationStore,
        mall: MallGateway,
        chat: ChatObservation,
    ) -> AsyncIterator[str]:
        content_parts: list[str] = []
        recommendations: dict[str, Product] = {}
        tool_trace: list[ToolTrace] = []
        plan_state: PlanState | None = None
        goal_understanding: GoalUnderstandingResult | None = None
        recommendation_spec: RecommendationSpec | None = None
        created_orders: dict[str, OrderLink] = {}
        persisted = False
        chat_outcome = "failed"
        chat_error: BaseException | None = None
        chat.set_conversation(
            conversation_id=conversation_id,
            turn_id=assistant_message_id,
        )
    
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
            if goal_understanding is not None:
                metadata["goal_understanding"] = goal_understanding.model_dump(
                    mode="json"
                )
            if recommendation_spec is not None:
                metadata["recommendation_spec"] = recommendation_spec.model_dump(
                    mode="json"
                )
            if created_orders:
                metadata["orders"] = [
                    order.model_dump(mode="json")
                    for order in created_orders.values()
                ]
            return metadata
    
        chat_token = chat.attach()
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
                previous_goal_understanding=latest_goal_understanding(context),
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
                    if isinstance(event.get("recommendations"), list):
                        for product_payload in event["recommendations"]:
                            if isinstance(product_payload, dict):
                                product = Product.model_validate(product_payload)
                                recommendations[product.id] = product
                    goal_payload = event.get("goal_understanding")
                    if isinstance(goal_payload, dict):
                        goal_understanding = GoalUnderstandingResult.model_validate(
                            goal_payload
                        )
                    spec_payload = event.get("recommendation_spec")
                    if isinstance(spec_payload, dict):
                        recommendation_spec = RecommendationSpec.model_validate(
                            spec_payload
                        )
                    store.finish_message(
                        assistant_message_id,
                        "".join(content_parts) or error_message,
                        "failed",
                        metadata=message_metadata(),
                    )
                    persisted = True
                    chat_outcome = "failed"
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
                    if isinstance(event.get("recommendations"), list):
                        for product_payload in event["recommendations"]:
                            if isinstance(product_payload, dict):
                                product = Product.model_validate(product_payload)
                                recommendations[product.id] = product
                    goal_payload = event.get("goal_understanding")
                    if isinstance(goal_payload, dict):
                        goal_understanding = GoalUnderstandingResult.model_validate(
                            goal_payload
                        )
                    spec_payload = event.get("recommendation_spec")
                    if isinstance(spec_payload, dict):
                        recommendation_spec = RecommendationSpec.model_validate(
                            spec_payload
                        )
                    store.finish_message(
                        assistant_message_id,
                        "".join(content_parts),
                        "completed",
                        metadata=message_metadata(),
                    )
                    persisted = True
                    chat_outcome = "completed"
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
            chat_outcome = "failed"
            yield sse_event(
                {
                    "type": "error",
                    "message_id": assistant_message_id,
                    "message": error_message,
                }
            )
        except asyncio.CancelledError:
            chat_outcome = "client_disconnected"
            raise
        except Exception as exc:
            chat_error = exc
            logger.exception("Persisted LLM stream failed")
            error_message = "对话流处理失败，请查看 agent-service 终端日志。"
            store.finish_message(
                assistant_message_id,
                "".join(content_parts) or error_message,
                "failed",
                metadata=message_metadata(),
            )
            persisted = True
            chat_outcome = "failed"
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
                chat_outcome = "client_disconnected"
            chat.detach(chat_token)
            chat.end(chat_outcome, error=chat_error)
    
    
    async def configuration_error_stream(
        conversation_id: str,
        conversation_title: str,
        assistant_message_id: str,
        message: str,
        chat: ChatObservation,
    ) -> AsyncIterator[str]:
        chat.set_conversation(
            conversation_id=conversation_id,
            turn_id=assistant_message_id,
        )
        chat_token = chat.attach()
        try:
            yield sse_event(
                {
    import json
    import os
    import sqlite3
    from datetime import datetime, timezone
    from functools import lru_cache
    from pathlib import Path
    from uuid import uuid4
    
    from .models import (
        ConversationDetail,
        ConversationSummary,
        GoalUnderstandingResult,
        OrderLink,
        PlanState,
        Product,
        RecommendationSpec,
        StoredMessage,
        ToolTrace,
    )
    from .observability.database import ObservedConnection, database_span
    from .observability.spans import repository_operation
    
    FIXED_USER_ID = 1
    
    
    def utc_now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    
    
    class ConversationStore:
        def __init__(self, database_path: str | Path) -> None:
            self.database_path = Path(database_path)
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            self.initialize()
    
        def connect(self) -> ObservedConnection:
            with database_span("CONNECT"):
                connection = sqlite3.connect(self.database_path, timeout=5)
                connection.row_factory = sqlite3.Row
            with database_span(
                "PRAGMA",
                statement="PRAGMA foreign_keys = ON",
            ):
                connection.execute("PRAGMA foreign_keys = ON")
            return ObservedConnection(connection)
    
        @repository_operation("conversation.initialize")
        def initialize(self) -> None:
            with self.connect() as connection:
                connection.executescript(
                    """
                    PRAGMA journal_mode = WAL;
    
                    CREATE TABLE IF NOT EXISTS conversations (
                        id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
    
                    CREATE TABLE IF NOT EXISTS messages (
                        id TEXT PRIMARY KEY,
                        conversation_id TEXT NOT NULL,
                        role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                        content TEXT NOT NULL,
                        status TEXT NOT NULL
                            CHECK (status IN ('streaming', 'completed', 'failed')),
                        sequence INTEGER NOT NULL,
                        created_at TEXT NOT NULL,
                        metadata TEXT NOT NULL DEFAULT '{}',
                        FOREIGN KEY (conversation_id)
                            REFERENCES conversations(id)
                            ON DELETE CASCADE
                    );
    
                    CREATE INDEX IF NOT EXISTS idx_conversations_user_updated
                        ON conversations(user_id, updated_at DESC);
                    CREATE INDEX IF NOT EXISTS idx_messages_conversation_sequence
                        ON messages(conversation_id, sequence);
    
                    UPDATE messages
                    SET status = 'failed'
                    WHERE status = 'streaming';
                    """
                )
                columns = {
                    row["name"]
                    for row in connection.execute("PRAGMA table_info(messages)")
                }
                if "metadata" not in columns:
                    connection.execute(
                        "ALTER TABLE messages ADD COLUMN metadata TEXT NOT NULL DEFAULT '{}'"
                    )
    
        @repository_operation("conversation.create")
        def create_conversation(self, user_id: int, first_message: str) -> str:
            conversation_id = f"conversation-{uuid4().hex}"
            title = " ".join(first_message.split())[:40] or "新对话"
            now = utc_now()
            with self.connect() as connection:
                connection.execute(
                    """
                    INSERT INTO conversations(id, user_id, title, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (conversation_id, user_id, title, now, now),
                )
            return conversation_id
    
        @repository_operation("conversation.exists")
        def conversation_exists(self, user_id: int, conversation_id: str) -> bool:
            with self.connect() as connection:
                row = connection.execute(
                    """
                    SELECT 1 FROM conversations
                    WHERE id = ? AND user_id = ?
                    """,
                    (conversation_id, user_id),
                ).fetchone()
            return row is not None
    
        @repository_operation("message.create")
        def add_message(
            self,
            conversation_id: str,
            role: str,
            content: str,
            status: str,
            metadata: dict[str, object] | None = None,
        ) -> str:
            message_id = f"message-{uuid4().hex}"
            now = utc_now()
            with self.connect() as connection:
                sequence_row = connection.execute(
                    """
                    SELECT COALESCE(MAX(sequence), 0) + 1
                    FROM messages
                    WHERE conversation_id = ?
                    """,
                    (conversation_id,),
                ).fetchone()
                sequence = int(sequence_row[0])
                connection.execute(
                    """
                    INSERT INTO messages(
                        id, conversation_id, role, content, status, sequence,
                        created_at, metadata
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        message_id,
                        conversation_id,
                        role,
                        content,
                        status,
                        sequence,
                        now,
                        json.dumps(metadata or {}, ensure_ascii=False),
                    ),
                )
                connection.execute(
                    "UPDATE conversations SET updated_at = ? WHERE id = ?",
                    (now, conversation_id),
                )
            return message_id
    
        @repository_operation("message.finish")
        def finish_message(
            self,
            message_id: str,
            content: str,
            status: str,
            metadata: dict[str, object] | None = None,
        ) -> None:
            now = utc_now()
            with self.connect() as connection:
                connection.execute(
                    """
                    UPDATE messages
                    SET content = ?, status = ?, metadata = ?
                    WHERE id = ? AND status = 'streaming'
                    """,
                    (
                        content,
                        status,
                        json.dumps(metadata or {}, ensure_ascii=False),
                        message_id,
                    ),
                )
                row = connection.execute(
                    "SELECT conversation_id FROM messages WHERE id = ?",
                    (message_id,),
                ).fetchone()
                if row is not None:
                    connection.execute(
                        "UPDATE conversations SET updated_at = ? WHERE id = ?",
                        (now, row["conversation_id"]),
                    )
    
        @repository_operation("conversation.list")
        def list_conversations(self, user_id: int) -> list[ConversationSummary]:
            with self.connect() as connection:
                rows = connection.execute(
                    """
                    SELECT
                        c.id,
                        c.title,
                        c.created_at,
                        c.updated_at,
                        COUNT(m.id) AS message_count
                    FROM conversations c
                    LEFT JOIN messages m ON m.conversation_id = c.id
                    WHERE c.user_id = ?
                    GROUP BY c.id
                    ORDER BY c.updated_at DESC
                    """,
                    (user_id,),
                ).fetchall()
            return [
                ConversationSummary(
                    id=row["id"],
                    title=row["title"],
                    message_count=row["message_count"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]
    
        @repository_operation("conversation.get")
        def get_conversation(
            self,
            user_id: int,
            conversation_id: str,
        ) -> ConversationDetail | None:
            with self.connect() as connection:
                conversation = connection.execute(
                    """
                    SELECT id, title, created_at, updated_at
                    FROM conversations
                    WHERE id = ? AND user_id = ?
                    """,
                    (conversation_id, user_id),
                ).fetchone()
                if conversation is None:
                    return None
    
                messages = connection.execute(
                    """
                    SELECT id, role, content, status, created_at, metadata
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY sequence ASC
                    """,
                    (conversation_id,),
                ).fetchall()
    
            return ConversationDetail(
                id=conversation["id"],
                title=conversation["title"],
                message_count=len(messages),
                created_at=conversation["created_at"],
                updated_at=conversation["updated_at"],
                messages=[self._stored_message(message) for message in messages],
            )
    
        @repository_operation("conversation.model_context")
        def model_context(self, conversation_id: str) -> list[StoredMessage]:
            with self.connect() as connection:
                rows = connection.execute(
                    """
                    SELECT id, role, content, status, created_at, metadata
                    FROM messages
                    WHERE conversation_id = ?
                      AND (role = 'user' OR status = 'completed')
                    ORDER BY sequence ASC
                    """,
                    (conversation_id,),
                ).fetchall()
            return [self._stored_message(row) for row in rows]
    
        @staticmethod
        def _stored_message(row: sqlite3.Row) -> StoredMessage:
            try:
                metadata = json.loads(row["metadata"] or "{}")
            except (json.JSONDecodeError, TypeError):
                metadata = {}
            if not isinstance(metadata, dict):
                metadata = {}
    
            recommendations = [
                Product.model_validate(product)
                for product in metadata.get("recommendations", [])
                if isinstance(product, dict)
            ]
            tool_trace = [
                ToolTrace.model_validate(trace)
                for trace in metadata.get("tool_trace", [])
                if isinstance(trace, dict)
            ]
            plan_state: PlanState | None = None
            if isinstance(metadata.get("plan_state"), dict):
                try:
                    plan_state = PlanState.model_validate(metadata["plan_state"])
                except ValueError:
                    plan_state = None
            goal_understanding: GoalUnderstandingResult | None = None
            if isinstance(metadata.get("goal_understanding"), dict):
                try:
                    goal_understanding = GoalUnderstandingResult.model_validate(
                        metadata["goal_understanding"]
                    )
                except ValueError:
                    goal_understanding = None
            recommendation_spec: RecommendationSpec | None = None
            if isinstance(metadata.get("recommendation_spec"), dict):
                try:
                    recommendation_spec = RecommendationSpec.model_validate(
                        metadata["recommendation_spec"]
                    )
                except ValueError:
                    recommendation_spec = None
            orders = [
                OrderLink.model_validate(order)
                for order in metadata.get("orders", [])
                if isinstance(order, dict)
            ]
            return StoredMessage(
                id=row["id"],
                role=row["role"],
                content=row["content"],
                status=row["status"],
                created_at=row["created_at"],
                recommendations=recommendations,
                tool_trace=tool_trace,
                plan_state=plan_state,
                goal_understanding=goal_understanding,
                recommendation_spec=recommendation_spec,
                orders=orders,
            )
    
    
    def default_database_path() -> Path:
        configured = os.getenv("AGENT_DB_PATH")
        if configured:
            return Path(configured).expanduser().resolve()
        return Path(__file__).resolve().parents[2] / "data" / "agent.db"
    
    
    @lru_cache
    def get_conversation_store() -> ConversationStore:
        return ConversationStore(default_database_path())
    ✓ • 0ms

## Activity

    $ sed -n '990,1190p' agent-service/tests/test_agent_runner.py && sed -n '180,470p' agent-service/tests/test_agent_api.py
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
                        "understand_goal",
                        {},
                        call_id="call-goal",
                    ),
                ],
                [
                    assistant_message(
                        json.dumps(
                            {
                                "intents": ["product_recommendation"],
                                "goal": "推荐预算 300 元以内的通勤商品",
                                "confidence": 0.96,
                                "slots": {
                                    "query": "通勤",
                                    "max_price_cents": 30000,
                                    "scenario": "self",
                                },
                                "missing_slots": [],
                                "requires_clarification": False,
                                "clarification_question": None,
                            },
                            ensure_ascii=False,
                        )
                    )
                ],
                [
                    function_call(
                        "collect_recommendation_context",
                        {},
                        call_id="call-context",
                    )
                ],
                [
                    function_call(
                        "generate_recommendation_spec",
                        {},
                        call_id="call-spec",
                    )
                ],
                [
                    assistant_message(
                        json.dumps(
                            {
                                "goal_summary": "推荐 300 元以内通勤商品",
                                "hard_constraints": {
                                    "category": None,
                                    "min_price_cents": None,
                                    "max_price_cents": 30000,
                                    "required_tags": [],
                                    "excluded_tags": [],
                                },
                                "preferred_categories": ["箱包"],
                                "preferred_tags": ["通勤"],
                                "weak_categories": [],
                                "negative_tags": [],
                                "search_queries": ["通勤", "办公室"],
                                "scenario": "self",
                                "usage": "通勤",
                                "recipient": None,
                                "source_evidence": [
                                    {
                                        "source": "cart",
                                        "observation": "购物车中有通勤双肩包",
                                        "influence": "high",
                                    }
                                ],
                                "confidence": 0.92,
                                "missing_information": [],
                            },
                            ensure_ascii=False,
                        )
                    )
                ],
                [
                    function_call(
                        "search_organic_candidates",
                        {},
                        call_id="call-organic-search",
                    ),
                    function_call(
                        "search_ad_candidates",
                        {},
                        call_id="call-ad-search",
                    ),
                ],
                [
                    function_call(
                        "recommend_products",
                        {},
                        call_id="call-recommend",
                    )
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
        assert len(model.last_call.tools) == 19
        assert model.first_call is not None
        assert "小牛导购" in (model.first_call.system_instructions or "")
        assert "独立语义终排" in (
            model.first_call.system_instructions or ""
        )
        assert "pending_intent_question" in (
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
        yield {
            "type": "delta",
            "message_id": "assistant-test",
            "content": "真实模型回复",
        }
        yield {
            "type": "done",
            "message_id": "assistant-test",
            "tool_trace": [
                {
                    "call_id": "call-1",
                    "tool": "search_products",
                    "arguments": '{"query":"通勤"}',
                    "status": "completed",
                    "summary": "1 product",
                }
            ],
            "plan_state": PLAN_STATE,
            "orders": [ORDER_LINK],
            "recommendations": [RECOMMENDED_PRODUCT],
            "goal_understanding": GOAL_UNDERSTANDING,
            "recommendation_spec": RECOMMENDATION_SPEC,
        }
    
    
    def test_health() -> None:
        response = client.get("/health")
    
        assert response.status_code == 200
        assert response.json()["service"] == "agent-service"
    
    
    def test_chat_uses_mall_catalog() -> None:
        previous_overrides = app.dependency_overrides.copy()
        app.dependency_overrides[get_mall_client] = lambda: FakeMallClient()
        try:
            response = client.post("/api/chat", json={"message": "推荐一件商品"})
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)
    
        assert response.status_code == 200
        assert "帆布托特包" in response.json()["reply"]
        assert response.json()["products"][0]["id"] == "tote"
    
    
    def test_chat_rejects_blank_message() -> None:
        response = client.post("/api/chat", json={"message": "   "})
    
        assert response.status_code == 422
    
    
    def test_stream_chat_persists_completed_conversation(
        store: ConversationStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            api_module,
            "load_llm_config",
            lambda: TEST_CONFIG,
        )
        monkeypatch.setattr(api_module, "stream_agent_reply", fake_agent_stream)
    
        response = client.post(
            "/api/chat/stream",
            json={"message": "A"},
        )
    
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert '"type": "conversation"' in response.text
        assert '"type": "tool_started"' in response.text
        assert '"type": "plan_updated"' in response.text
        assert '"type": "order_created"' in response.text
        assert '"type": "recommendations"' in response.text
        assert "真实模型回复" in response.text
        assert '"type": "done"' in response.text
    
        conversations = store.list_conversations(1)
        assert len(conversations) == 1
        assert conversations[0].title == "A"
        assert conversations[0].message_count == 2
    
        detail = store.get_conversation(1, conversations[0].id)
        assert detail is not None
        assert [message.role for message in detail.messages] == [
            "user",
            "assistant",
        ]
        assert detail.messages[1].content == "真实模型回复"
        assert detail.messages[1].status == "completed"
        assert detail.messages[1].recommendations[0].id == "tote"
        assert detail.messages[1].recommendations[0].is_ad is True
        assert detail.messages[1].recommendations[0].ad_label == "广告"
        assert detail.messages[1].goal_understanding is not None
        assert detail.messages[1].goal_understanding.pending_intents == [
            "order_query"
        ]
        assert detail.messages[1].recommendation_spec is not None
        assert detail.messages[1].recommendation_spec.search_queries == [
            "通勤",
            "办公室",
        ]
        assert detail.messages[1].tool_trace[0].tool == "search_products"
        assert detail.messages[1].plan_state is not None
        assert detail.messages[1].plan_state.plan.plan_id == "plan-test"
        assert detail.messages[1].plan_state.current_step_id == "submit"
        assert detail.messages[1].orders[0].order_id == "order-test"
        assert detail.messages[1].orders[0].preview_path == "/orders/order-test"
    
    
    def test_stream_chat_requires_message(
        store: ConversationStore,
    ) -> None:
        response = client.post(
            "/api/chat/stream",
            json={"messages": [{"role": "user", "content": "你好"}]},
        )
    
        assert response.status_code == 422
    
    
    def test_stream_chat_persists_configuration_error(
        store: ConversationStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def missing_config() -> LLMConfig:
            raise LLMConfigError("LLM config is not set")
    
        monkeypatch.setattr(api_module, "load_llm_config", missing_config)
    
        response = client.post(
            "/api/chat/stream",
            json={"message": "保存失败消息"},
        )
    
        assert response.status_code == 200
        assert "LLM config is not set" in response.text
    
        conversations = store.list_conversations(1)
        assert len(conversations) == 1
        detail = store.get_conversation(1, conversations[0].id)
        assert detail is not None
        assert detail.messages[0].role == "user"
        assert detail.messages[1].status == "failed"
        assert "LLM config is not set" in detail.messages[1].content
    
    
    def test_stream_chat_persists_partial_reply_on_error(
        store: ConversationStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        async def failing_stream(
            messages,
            config,
            mall,
            previous_plan_state=None,
            previous_recommendations=None,
            previous_orders=None,
            previous_goal_understanding=None,
        ):
            yield {"type": "start", "message_id": "assistant-test"}
            yield {
                "type": "delta",
                "message_id": "assistant-test",
                "content": "已经生成的部分",
            }
            yield {
                "type": "error",
                "message_id": "assistant-test",
                "message": "模型调用失败",
                "tool_trace": [],
            }
    
        monkeypatch.setattr(
            api_module,
            "load_llm_config",
            lambda: TEST_CONFIG,
        )
        monkeypatch.setattr(api_module, "stream_agent_reply", failing_stream)
    
        response = client.post(
            "/api/chat/stream",
            json={"message": "失败测试"},
        )
    
        assert "模型调用失败" in response.text
        conversation = store.list_conversations(1)[0]
        detail = store.get_conversation(1, conversation.id)
        assert detail is not None
        assert detail.messages[1].content == "已经生成的部分"
        assert detail.messages[1].status == "failed"
    
    
    def test_stream_chat_passes_previous_plan_state_to_next_turn(
        store: ConversationStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        conversation_id = store.create_conversation(1, "继续推荐")
        store.add_message(conversation_id, "user", "先推荐商品", "completed")
        store.add_message(
            conversation_id,
            "assistant",
            "已完成第一轮",
            "completed",
            metadata={
                "plan_state": PLAN_STATE,
                "recommendations": [
                    {
                        "id": "tote",
                        "name": "帆布托特包",
                        "description": "日常通勤",
                        "price_cents": 6900,
                        "category": "箱包",
                    }
                ],
                "goal_understanding": GOAL_UNDERSTANDING,
                "orders": [ORDER_LINK],
            },
        )
        captured: dict[str, object] = {}
    
        async def capturing_stream(
            messages,
            config,
            mall,
            previous_plan_state=None,
            previous_recommendations=None,
            previous_orders=None,
            previous_goal_understanding=None,
        ):
            captured["plan_state"] = previous_plan_state
            captured["previous_recommendations"] = previous_recommendations
            captured["previous_orders"] = previous_orders
            captured["previous_goal_understanding"] = previous_goal_understanding
            yield {"type": "start", "message_id": "assistant-next"}
            yield {"type": "delta", "content": "继续完成"}
            yield {
                "type": "done",
                "tool_trace": [],
                "plan_state": previous_plan_state.model_dump(mode="json")
                if previous_plan_state
                else None,
            }
    
        monkeypatch.setattr(api_module, "load_llm_config", lambda: TEST_CONFIG)
        monkeypatch.setattr(api_module, "stream_agent_reply", capturing_stream)
    
        response = client.post(
            "/api/chat/stream",
            json={
                "conversation_id": conversation_id,
                "message": "继续刚才的计划",
            },
        )
    
        assert response.status_code == 200
        assert captured["plan_state"] is not None
        assert captured["plan_state"].plan.plan_id == "plan-test"
        assert captured["plan_state"].current_step_id == "submit"
        assert captured["previous_recommendations"][0].id == "tote"
        assert captured["previous_orders"][0].order_id == "order-test"
        assert captured["previous_goal_understanding"].pending_intents == [
            "order_query"
        ]
    
    
    def test_conversation_history_endpoints(store: ConversationStore) -> None:
        conversation_id = store.create_conversation(1, "购买礼物")
        store.add_message(conversation_id, "user", "购买礼物", "completed")
        store.add_message(conversation_id, "assistant", "推荐托特包", "completed")
    
        list_response = client.get("/api/conversations")
        detail_response = client.get(f"/api/conversations/{conversation_id}")
    
        assert list_response.status_code == 200
        assert list_response.json()["items"][0]["title"] == "购买礼物"
        assert list_response.json()["items"][0]["message_count"] == 2
        assert detail_response.status_code == 200
        assert detail_response.json()["messages"][1]["content"] == "推荐托特包"
    
    
    def test_unknown_conversation_returns_404(store: ConversationStore) -> None:
        response = client.get("/api/conversations/missing")
    
        assert response.status_code == 404
    ✓ • 0ms

## Activity

    $ rg -n "recommendation_spec|goal_understanding|metadata|PlanState|plan_state" agent-service/src/agent_service/storage.py agent-service/src/agent_service/models.py agent-service/src/agent_service/api.py | head -200
    agent-service/src/agent_service/models.py:293:    metadata: dict[str, object] = Field(default_factory=dict)
    agent-service/src/agent_service/models.py:308:class PlanState(BaseModel):
    agent-service/src/agent_service/models.py:378:    plan_state: PlanState | None = None
    agent-service/src/agent_service/models.py:379:    goal_understanding: GoalUnderstandingResult | None = None
    agent-service/src/agent_service/models.py:380:    recommendation_spec: RecommendationSpec | None = None
    agent-service/src/agent_service/api.py:21:    PlanState,
    agent-service/src/agent_service/api.py:46:def latest_plan_state(
    agent-service/src/agent_service/api.py:48:) -> PlanState | None:
    agent-service/src/agent_service/api.py:50:        if message.plan_state is not None:
    agent-service/src/agent_service/api.py:51:            return message.plan_state
    agent-service/src/agent_service/api.py:73:def latest_goal_understanding(
    agent-service/src/agent_service/api.py:77:        if message.goal_understanding is not None:
    agent-service/src/agent_service/api.py:78:            return message.goal_understanding
    agent-service/src/agent_service/api.py:95:    plan_state: PlanState | None = None
    agent-service/src/agent_service/api.py:96:    goal_understanding: GoalUnderstandingResult | None = None
    agent-service/src/agent_service/api.py:97:    recommendation_spec: RecommendationSpec | None = None
    agent-service/src/agent_service/api.py:107:    def message_metadata() -> dict[str, object]:
    agent-service/src/agent_service/api.py:108:        metadata: dict[str, object] = {
    agent-service/src/agent_service/api.py:117:        if plan_state is not None:
    agent-service/src/agent_service/api.py:118:            metadata["plan_state"] = plan_state.model_dump(mode="json")
    agent-service/src/agent_service/api.py:119:        if goal_understanding is not None:
    agent-service/src/agent_service/api.py:120:            metadata["goal_understanding"] = goal_understanding.model_dump(
    agent-service/src/agent_service/api.py:123:        if recommendation_spec is not None:
    agent-service/src/agent_service/api.py:124:            metadata["recommendation_spec"] = recommendation_spec.model_dump(
    agent-service/src/agent_service/api.py:128:            metadata["orders"] = [
    agent-service/src/agent_service/api.py:132:        return metadata
    agent-service/src/agent_service/api.py:148:            previous_plan_state=latest_plan_state(context),
    agent-service/src/agent_service/api.py:151:            previous_goal_understanding=latest_goal_understanding(context),
    agent-service/src/agent_service/api.py:172:                plan_state_payload = event.get("plan_state")
    agent-service/src/agent_service/api.py:173:                if isinstance(plan_state_payload, dict):
    agent-service/src/agent_service/api.py:174:                    plan_state = PlanState.model_validate(plan_state_payload)
    agent-service/src/agent_service/api.py:220:                plan_state_payload = event.get("plan_state")
    agent-service/src/agent_service/api.py:221:                if isinstance(plan_state_payload, dict):
    agent-service/src/agent_service/api.py:222:                    plan_state = PlanState.model_validate(plan_state_payload)
    agent-service/src/agent_service/api.py:233:                goal_payload = event.get("goal_understanding")
    agent-service/src/agent_service/api.py:235:                    goal_understanding = GoalUnderstandingResult.model_validate(
    agent-service/src/agent_service/api.py:238:                spec_payload = event.get("recommendation_spec")
    agent-service/src/agent_service/api.py:240:                    recommendation_spec = RecommendationSpec.model_validate(
    agent-service/src/agent_service/api.py:247:                    metadata=message_metadata(),
    agent-service/src/agent_service/api.py:261:                plan_state_payload = event.get("plan_state")
    agent-service/src/agent_service/api.py:262:                if isinstance(plan_state_payload, dict):
    agent-service/src/agent_service/api.py:263:                    plan_state = PlanState.model_validate(plan_state_payload)
    agent-service/src/agent_service/api.py:274:                goal_payload = event.get("goal_understanding")
    agent-service/src/agent_service/api.py:276:                    goal_understanding = GoalUnderstandingResult.model_validate(
    agent-service/src/agent_service/api.py:279:                spec_payload = event.get("recommendation_spec")
    agent-service/src/agent_service/api.py:281:                    recommendation_spec = RecommendationSpec.model_validate(
    agent-service/src/agent_service/api.py:288:                    metadata=message_metadata(),
    agent-service/src/agent_service/api.py:300:            metadata=message_metadata(),
    agent-service/src/agent_service/api.py:322:            metadata=message_metadata(),
    agent-service/src/agent_service/api.py:339:                metadata=message_metadata(),
    agent-service/src/agent_service/storage.py:14:    PlanState,
    agent-service/src/agent_service/storage.py:71:                    metadata TEXT NOT NULL DEFAULT '{}',
    agent-service/src/agent_service/storage.py:91:            if "metadata" not in columns:
    agent-service/src/agent_service/storage.py:93:                    "ALTER TABLE messages ADD COLUMN metadata TEXT NOT NULL DEFAULT '{}'"
    agent-service/src/agent_service/storage.py:130:        metadata: dict[str, object] | None = None,
    agent-service/src/agent_service/storage.py:148:                    created_at, metadata
    agent-service/src/agent_service/storage.py:160:                    json.dumps(metadata or {}, ensure_ascii=False),
    agent-service/src/agent_service/storage.py:175:        metadata: dict[str, object] | None = None,
    agent-service/src/agent_service/storage.py:182:                SET content = ?, status = ?, metadata = ?
    agent-service/src/agent_service/storage.py:188:                    json.dumps(metadata or {}, ensure_ascii=False),
    agent-service/src/agent_service/storage.py:252:                SELECT id, role, content, status, created_at, metadata
    agent-service/src/agent_service/storage.py:274:                SELECT id, role, content, status, created_at, metadata
    agent-service/src/agent_service/storage.py:287:            metadata = json.loads(row["metadata"] or "{}")
    agent-service/src/agent_service/storage.py:289:            metadata = {}
    agent-service/src/agent_service/storage.py:290:        if not isinstance(metadata, dict):
    agent-service/src/agent_service/storage.py:291:            metadata = {}
    agent-service/src/agent_service/storage.py:295:            for product in metadata.get("recommendations", [])
    agent-service/src/agent_service/storage.py:300:            for trace in metadata.get("tool_trace", [])
    agent-service/src/agent_service/storage.py:303:        plan_state: PlanState | None = None
    agent-service/src/agent_service/storage.py:304:        if isinstance(metadata.get("plan_state"), dict):
    agent-service/src/agent_service/storage.py:306:                plan_state = PlanState.model_validate(metadata["plan_state"])
    agent-service/src/agent_service/storage.py:308:                plan_state = None
    agent-service/src/agent_service/storage.py:309:        goal_understanding: GoalUnderstandingResult | None = None
    agent-service/src/agent_service/storage.py:310:        if isinstance(metadata.get("goal_understanding"), dict):
    agent-service/src/agent_service/storage.py:312:                goal_understanding = GoalUnderstandingResult.model_validate(
    agent-service/src/agent_service/storage.py:313:                    metadata["goal_understanding"]
    agent-service/src/agent_service/storage.py:316:                goal_understanding = None
    agent-service/src/agent_service/storage.py:317:        recommendation_spec: RecommendationSpec | None = None
    agent-service/src/agent_service/storage.py:318:        if isinstance(metadata.get("recommendation_spec"), dict):
    agent-service/src/agent_service/storage.py:320:                recommendation_spec = RecommendationSpec.model_validate(
    agent-service/src/agent_service/storage.py:321:                    metadata["recommendation_spec"]
    agent-service/src/agent_service/storage.py:324:                recommendation_spec = None
    agent-service/src/agent_service/storage.py:327:            for order in metadata.get("orders", [])
    agent-service/src/agent_service/storage.py:338:            plan_state=plan_state,
    agent-service/src/agent_service/storage.py:339:            goal_understanding=goal_understanding,
    agent-service/src/agent_service/storage.py:340:            recommendation_spec=recommendation_spec,
    ✓ • 0ms

## Assistant

现有实现已经具备两类“缺失项”数据，但它们目前都不是真正的收集流程：Goal Understanding 的 `missing_slots` 只在意图含糊或冲突时触发追问，Recommendation SPEC 的 `missing_information` 生成后也没有消费者。也就是说，现在默认是“信息差不多就直接推荐”，还没有跨轮逐项补齐需求的明确状态机。

## Activity

    $ rg -n "需求收集|收集需求|逐项|跳过|别管那么多|直接推荐|missing_information|missing_slots" *.md agent-service web mall-service -g '*.md' -g '*.py' -g '*.tsx' -g '*.ts' -g '!node_modules'
    mall-service/src/mall_service/models.py:195:    missing_information: list[str] = Field(default_factory=list)
    agent-service/src/agent_service/goal_understanding.py:192:            missing_slots=draft.missing_slots,
    mall-service/tests/test_mall_api.py:142:        "missing_information": [],
    mall-service/tests/test_mall_api.py:183:        "missing_information": [],
    web/components/agent-chat.tsx:213:  skipped: "已跳过",
    agent-service/src/agent_service/models.py:170:    missing_slots: list[str] = Field(default_factory=list)
    agent-service/src/agent_service/models.py:182:    missing_slots: list[str] = Field(default_factory=list)
    agent-service/src/agent_service/models.py:224:    missing_information: list[str] = Field(default_factory=list)
    agent-service/prompts/goal_understanding.md:94:  "missing_slots": [],
    agent-service/prompts/recommendation_spec.md:95:  "missing_information": []
    agent-service/prompts/shopping_agent.md:125:- 如果用户已经给出足够信息，直接推荐，不要重复询问。
    agent-service/tests/test_agent_runner.py:540:                            "missing_slots": [],
    agent-service/tests/test_agent_runner.py:677:                            "missing_information": [],
    agent-service/tests/test_agent_runner.py:1023:                            "missing_slots": [],
    agent-service/tests/test_agent_runner.py:1073:                            "missing_information": [],
    agent-service/tests/test_agent_api.py:113:    "missing_slots": [],
    agent-service/tests/test_agent_api.py:138:    "missing_information": [],
    codex-session-2026.11.1.md:20859:    - 如果用户已经给出足够信息，直接推荐，不要重复询问。
    codex-session-11.8.md:3205:        "missing_slots": [],
    codex-session-11.8.md:4973:        missing_slots: list[str] = Field(default_factory=list)
    codex-session-11.8.md:4985:        missing_slots: list[str] = Field(default_factory=list)
    codex-session-11.8.md:5027:        missing_information: list[str] = Field(default_factory=list)
    codex-session-11.3.md:340:    - 如果用户已经给出足够信息，直接推荐，不要重复询问。
    codex-session-11.3.md:2809:- 大模型如果跳过明显更高分的商品，必须能引用一个具体的用户约束或多样性原因。
    codex-session-11.3.md:3705:    agent-service/prompts/shopping_agent.md:76:- 如果用户已经给出足够信息，直接推荐，不要重复询问。
    codex-session-11.3.md:12155:    agent-service/prompts/shopping_agent.md:87:- 如果用户已经给出足够信息，直接推荐，不要重复询问。
    codex-session-11.3.md:13861:      skipped: "已跳过",
    codex-session-11.2.md:106:    ./agent-service/prompts/shopping_agent.md:35:- 如果用户已经给出足够信息，直接推荐，不要重复询问。
    codex-session-11.2.md:368:    ./codex-session-2026.11.1.md:20859:    - 如果用户已经给出足够信息，直接推荐，不要重复询问。
    codex-session-11.2.md:945:    - 如果用户已经给出足够信息，直接推荐，不要重复询问。
    codex-session-11.2.md:2432:- **一个数据源失败不应拖垮整个流程**：商品推荐失败时还可以使用商城搜索结果；广告失败时直接跳过；画像失败时使用冷启动策略。
    codex-session-11.2.md:6291:    - 如果用户已经给出足够信息，直接推荐，不要重复询问。
    codex-session-11.2.md:6358:    - 如果用户已经给出足够信息，直接推荐，不要重复询问。
    codex-session-11.2.md:8178:     - 如果用户已经给出足够信息，直接推荐，不要重复询问。
    codex-session-11.2.md:12940:    +  skipped: "已跳过",
    codex-session-11.5.md:340:    - 如果用户已经给出足够信息，直接推荐，不要重复询问。
    codex-session-11.5.md:2809:- 大模型如果跳过明显更高分的商品，必须能引用一个具体的用户约束或多样性原因。
    codex-session-11.5.md:3705:    agent-service/prompts/shopping_agent.md:76:- 如果用户已经给出足够信息，直接推荐，不要重复询问。
    codex-session-11.5.md:12155:    agent-service/prompts/shopping_agent.md:87:- 如果用户已经给出足够信息，直接推荐，不要重复询问。
    codex-session-11.5.md:13861:      skipped: "已跳过",
    codex-session-11.5.md:20587:  "missing_slots": ["order_reference"]
    codex-session-11.5.md:20644:- `missing_slots`：完成任务还缺少的信息；
    codex-session-11.5.md:20666:  "missing_slots": [],
    codex-session-11.5.md:21342:    +    missing_slots: list[str] = Field(default_factory=list)
    codex-session-11.5.md:21354:    +    missing_slots: list[str] = Field(default_factory=list)
    codex-session-11.5.md:21463:      "missing_slots": [],
    codex-session-11.5.md:21662:                missing_slots=draft.missing_slots,
    codex-session-11.5.md:22419:    - 如果用户已经给出足够信息，直接推荐，不要重复询问。
    codex-session-11.5.md:22638:    +                            "missing_slots": [],
    codex-session-11.5.md:22701:    +                            "missing_slots": [],
    codex-session-11.5.md:22759:    +    "missing_slots": [],
    codex-session-11.5.md:23366:  "missing_information": []
    codex-session-11.5.md:23496:    +    missing_information: list[str] = Field(default_factory=list)
    codex-session-11.5.md:23603:      "missing_information": []
    codex-session-11.5.md:25384:       527                                "missing_slots": [],
    codex-session-11.5.md:25493:    +                            "missing_information": [],
    codex-session-11.5.md:25676:       969                                "missing_slots": [],
    codex-session-11.5.md:25867:       969                                "missing_slots": [],
    codex-session-11.5.md:25932:    +                            "missing_information": [],
    codex-session-11.5.md:25972:    +    "missing_information": [],
    codex-session-11.5.md:27067:    +    missing_information: list[str] = Field(default_factory=list)
    codex-session-11.5.md:27834:    +        "missing_information": [],
    codex-session-11.5.md:27875:    +        "missing_information": [],
    ✓ • 0ms

## Activity

    $ sed -n '360,430p' agent-service/src/agent_service/models.py && sed -n '1320,1740p' agent-service/src/agent_service/agent_runner.py
    
    
    class ToolTrace(BaseModel):
        call_id: str | None = None
        tool: str
        arguments: str = ""
        status: Literal["started", "completed", "failed"] = "started"
        summary: str | None = None
    
    
    class StoredMessage(BaseModel):
        id: str
        role: Literal["user", "assistant"]
        content: str
        status: Literal["streaming", "completed", "failed"]
        created_at: str
        recommendations: list[Product] = Field(default_factory=list)
        tool_trace: list[ToolTrace] = Field(default_factory=list)
        plan_state: PlanState | None = None
        goal_understanding: GoalUnderstandingResult | None = None
        recommendation_spec: RecommendationSpec | None = None
        orders: list[OrderLink] = Field(default_factory=list)
    
    
    class ConversationSummary(BaseModel):
        id: str
        title: str
        message_count: int
        created_at: str
        updated_at: str
    
    
    class ConversationDetail(ConversationSummary):
        messages: list[StoredMessage]
    
    
    class ConversationList(BaseModel):
        items: list[ConversationSummary]
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
    
            with trace_session.bind():
                result = Runner.run_streamed(
                    agent,
                    input=[
                        {"role": message.role, "content": message.content}
                        for message in messages
                    ],
                    context=context,
                    hooks=ObservabilityRunHooks(trace_session),
                    max_turns=config.max_turns,
                    run_config=RunConfig(tracing_disabled=True),
                )
                async for event in result.stream_events():
                    if isinstance(event, RawResponsesStreamEvent):
                        trace_session.observe_model_event(event.data)
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
                        if (
                            tool_name == "update_plan"
                            and context.plan_state is not None
                        ):
                            yield {
                                "type": "plan_updated",
                                "message_id": message_id,
                                "plan_state": context.plan_state.model_dump(
                                    mode="json"
                                ),
                            }
                        if (
                            tool_name == "create_order"
                            and context.created_orders
                        ):
                            yield {
                                "type": "order_created",
                                "message_id": message_id,
                                "order": list(
                                    context.created_orders.values()
                                )[-1].model_dump(mode="json"),
                            }
                        if (
                            context.selected_products
                            and not recommendations_emitted
                        ):
                            recommendations_emitted = True
                            yield {
                                "type": "recommendations",
                                "message_id": message_id,
                                "products": [
                                    product.model_dump(mode="json")
                                    for product in (
                                        context.selected_products.values()
                                    )
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
    
            trace_outcome = "completed"
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
            trace_session.finish("failed", exc)
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
            trace_session.finish("failed")
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
        except (asyncio.CancelledError, GeneratorExit):
            trace_outcome = "cancelled"
            raise
        except Exception as exc:
            trace_session.finish("failed", exc)
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
            trace_session.finish(trace_outcome)
            if client is not None:
                await client.close()
    ✓ • 0ms

## Activity

    $ sed -n '1,280p' mall-service/src/mall_service/search.py && sed -n '1,240p' mall-service/src/mall_service/catalog.py
    import json
    import logging
    from typing import Any, Literal
    
    from .catalog import PRODUCTS
    from .models import (
        AdInfo,
        Product,
        ProductCandidate,
        RecommendationSearchSpec,
    )
    
    
    logger = logging.getLogger(__name__)
    
    
    def build_es_query(
        spec: RecommendationSearchSpec,
        *,
        channel: Literal["organic", "ads"],
        limit: int,
    ) -> dict[str, Any]:
        hard = spec.hard_constraints
        filters: list[dict[str, Any]] = []
        must_not: list[dict[str, Any]] = []
        text_should: list[dict[str, Any]] = []
        preference_should: list[dict[str, Any]] = []
    
        if hard.category:
            filters.append({"term": {"category.keyword": hard.category}})
        if (
            hard.min_price_cents is not None
            or hard.max_price_cents is not None
        ):
            price_range: dict[str, int] = {}
            if hard.min_price_cents is not None:
                price_range["gte"] = hard.min_price_cents
            if hard.max_price_cents is not None:
                price_range["lte"] = hard.max_price_cents
            filters.append({"range": {"price_cents": price_range}})
        if hard.required_tags:
            filters.append({"terms": {"tags.keyword": hard.required_tags}})
        if hard.excluded_tags:
            must_not.append({"terms": {"tags.keyword": hard.excluded_tags}})
        if spec.negative_tags:
            must_not.append({"terms": {"tags.keyword": spec.negative_tags}})
    
        text_queries = [
            query
            for query in [*spec.search_queries, spec.usage, spec.recipient]
            if query
        ]
        for query in text_queries:
            text_should.append(
                {
                    "multi_match": {
                        "query": query,
                        "fields": [
                            "name^4",
                            "tags^3",
                            "category^2",
                            "description",
                        ],
                    }
                }
            )
        for category in spec.preferred_categories:
            preference_should.append(
                {
                    "term": {
                        "category.keyword": {
                            "value": category,
                            "boost": 1.5,
                        }
                    }
                }
            )
        for tag in spec.preferred_tags:
            preference_should.append(
                {
                    "term": {
                        "tags.keyword": {
                            "value": tag,
                            "boost": 2,
                        }
                    }
                }
            )
    
        bool_query: dict[str, Any] = {
            "filter": filters,
            "must_not": must_not,
        }
        if text_should:
            bool_query["must"] = [
                {
                    "bool": {
                        "should": text_should,
                        "minimum_should_match": 1,
                    }
                }
            ]
        if preference_should:
            bool_query["should"] = preference_should
            bool_query["minimum_should_match"] = 0
        if channel == "ads":
            filters.append({"term": {"is_ad": True}})
    
        return {
            "index": "products" if channel == "organic" else "ads",
            "size": limit,
            "query": {
                "bool": bool_query,
            },
            "sort": [
                {"_score": "desc"},
                {"price_cents": "asc"},
            ],
        }
    
    
    def log_mock_es_query(
        spec: RecommendationSearchSpec,
        *,
        channel: Literal["organic", "ads"],
        es_query: dict[str, Any],
    ) -> None:
        logger.info(
            "mock_es_query channel=%s spec=%s query=%s",
            channel,
            json.dumps(spec.model_dump(mode="json"), ensure_ascii=False),
            json.dumps(es_query, ensure_ascii=False),
        )
    
    
    def _product_text(product: Product) -> str:
        return " ".join(
            [
                product.id,
                product.name,
                product.description,
                product.category,
                *product.tags,
            ]
        ).lower()
    
    
    def _mock_score(product: Product, spec: RecommendationSearchSpec) -> float:
        text = _product_text(product)
        queries = [
            query.lower()
            for query in [*spec.search_queries, spec.usage, spec.recipient]
            if query
        ]
        score = sum(3 for query in queries if query in text)
        if product.category in spec.preferred_categories:
            score += 2
        score += sum(1 for tag in spec.preferred_tags if tag in product.tags)
        return float(score)
    
    
    def _hard_filter_pass(
        product: Product,
        spec: RecommendationSearchSpec,
    ) -> bool:
        hard = spec.hard_constraints
        if product.stock is not None and product.stock <= 0:
            return False
        if hard.category and product.category != hard.category:
            return False
        if (
            hard.min_price_cents is not None
            and product.price_cents < hard.min_price_cents
        ):
            return False
        if (
            hard.max_price_cents is not None
            and product.price_cents > hard.max_price_cents
        ):
            return False
        product_tags = set(product.tags)
        if not set(hard.required_tags).issubset(product_tags):
            return False
        if product_tags & set(hard.excluded_tags):
            return False
        if product_tags & set(spec.negative_tags):
            return False
        return True
    
    
    def mock_search_products(
        spec: RecommendationSearchSpec,
        *,
        limit: int,
    ) -> list[Product]:
        candidates = [
            (product, _mock_score(product, spec))
            for product in PRODUCTS
            if _hard_filter_pass(product, spec)
        ]
        text_queries = [
            query.lower()
            for query in [*spec.search_queries, spec.usage, spec.recipient]
            if query
        ]
        if text_queries:
            candidates = [
                (product, score)
                for product, score in candidates
                if any(
                    query in _product_text(product)
                    for query in text_queries
                )
            ]
        candidates.sort(
            key=lambda item: (-item[1], item[0].price_cents, item[0].id)
        )
        return [product for product, _ in candidates[:limit]]
    
    
    def search_mock_with_spec(
        spec: RecommendationSearchSpec,
        *,
        channel: Literal["organic", "ads"],
        limit: int,
    ) -> list[Product]:
        es_query = build_es_query(spec, channel=channel, limit=limit)
        log_mock_es_query(spec, channel=channel, es_query=es_query)
        return mock_search_products(spec, limit=limit)
    
    
    def search_mock_ads_with_spec(
        spec: RecommendationSearchSpec,
        *,
        limit: int,
    ) -> list[ProductCandidate]:
        products = search_mock_with_spec(
            spec,
            channel="ads",
            limit=limit,
        )
        return [
            ProductCandidate(
                product=product,
                source="advertisement",
                score=0.62,
                matched_signals=["Mock ES 广告检索"],
                ad=AdInfo(
                    ad_id=f"mock-ad-{product.id}",
                    campaign_id="campaign-mock-spec",
                ),
            )
            for product in products
        ]
    from .models import Product
    
    
    PRODUCTS = (
        Product(
            id="commuter-backpack",
            name="轻旅通勤双肩包",
            description="轻量防泼水面料，独立电脑夹层，适合日常通勤。",
            price_cents=29900,
            category="箱包",
            badge="通勤推荐",
            stock=18,
            tags=["通勤", "双肩包", "礼物", "电脑包"],
            image_url="/products/commuter-backpack.jpg",
        ),
        Product(
            id="canvas-tote",
            name="日常帆布托特包",
            description="厚实帆布与宽肩带，通勤和周末都能装。",
            price_cents=6900,
            category="箱包",
            badge="人气单品",
            stock=36,
            tags=["通勤", "托特包", "帆布", "礼物"],
            image_url="/products/canvas-tote.jpg",
        ),
        Product(
            id="moon-lamp",
            name="月影桌面灯",
            description="三档暖光，轻触调光，让桌面安静下来。",
            price_cents=12900,
            category="家居",
            badge="氛围好物",
            stock=12,
            tags=["居家", "台灯", "卧室", "礼物"],
            image_url="/products/moon-lamp.jpg",
        ),
        Product(
            id="matcha-soda",
            name="山野抹茶气泡水",
            description="低糖抹茶与细密气泡，午后喝一口刚刚好。",
            price_cents=1580,
            category="饮品",
            badge="本周新品",
            stock=80,
            tags=["饮品", "低糖", "抹茶", "夏日"],
            image_url="/products/matcha-soda.jpg",
        ),
        Product(
            id="hand-cream",
            name="木质香护手霜",
            description="滋润不黏腻，木质香调适合秋冬使用。",
            price_cents=4900,
            category="个护",
            badge="贴心礼物",
            stock=42,
            tags=["礼物", "护手霜", "香氛", "秋冬"],
            image_url="/products/hand-cream.jpg",
        ),
        Product(
            id="ceramic-mug",
            name="手作奶油陶瓷杯",
            description="温润奶油釉色，适合咖啡、茶和热牛奶。",
            price_cents=7900,
            category="家居",
            stock=25,
            tags=["杯子", "咖啡", "居家", "礼物"],
            image_url="/products/ceramic-mug.jpg",
        ),
        Product(
            id="linen-notebook",
            name="亚麻布面笔记本",
            description="平摊装订与细腻纸张，记录每天的灵感。",
            price_cents=3900,
            category="文创",
            stock=54,
            tags=["文具", "笔记本", "礼物", "通勤"],
            image_url="/products/linen-notebook.jpg",
        ),
        Product(
            id="portable-coffee",
            name="冷萃便携咖啡液",
            description="三秒速溶的清爽冷萃，办公室也能轻松喝。",
            price_cents=3600,
            category="饮品",
            stock=64,
            tags=["咖啡", "冷萃", "办公室", "通勤"],
            image_url="/products/portable-coffee.jpg",
        ),
        Product(
            id="linen-pillow",
            name="亚麻云朵靠枕",
            description="柔软支撑与可拆洗外套，让沙发更舒服。",
            price_cents=9900,
            category="家居",
            stock=20,
            tags=["靠枕", "居家", "客厅", "沙发"],
            image_url="/products/linen-pillow.jpg",
        ),
        Product(
            id="travel-bottle",
            name="保温随行杯",
            description="轻巧密封，保冷保温，适合通勤和短途出行。",
            price_cents=11900,
            category="家居",
            stock=31,
            tags=["水杯", "保温", "通勤", "旅行"],
            image_url="/products/travel-bottle.jpg",
        ),
    )
    
    STOP_WORDS = (
        "推荐",
        "帮我",
        "一下",
        "商品",
        "好物",
        "想要",
        "想买",
        "有没有",
        "什么",
    )
    
    
    def get_product(product_id: str) -> Product | None:
        return next((product for product in PRODUCTS if product.id == product_id), None)
    
    
    def search_products(
        query: str | None = None,
        category: str | None = None,
        max_price_cents: int | None = None,
        min_price_cents: int | None = None,
        limit: int = 5,
    ) -> list[Product]:
        clean_query = (query or "").strip().lower()
        for stop_word in STOP_WORDS:
            clean_query = clean_query.replace(stop_word, " ")
        terms = [term for term in clean_query.split() if term]
    
        candidates: list[tuple[int, Product]] = []
        for product in PRODUCTS:
            if category and category.lower() not in product.category.lower():
                continue
            if max_price_cents is not None and product.price_cents > max_price_cents:
                continue
            if min_price_cents is not None and product.price_cents < min_price_cents:
                continue
    
            searchable = " ".join(
                [
                    product.name,
                    product.description,
                    product.category,
                    *product.tags,
                ]
            ).lower()
            score = sum(1 for term in terms if term in searchable)
            if terms and score == 0:
                continue
            candidates.append((score, product))
    
        if terms:
            candidates.sort(key=lambda item: (-item[0], item[1].price_cents))
        return [product for _, product in candidates[: max(1, min(limit, 10))]]
    ✓ • 0ms

## Assistant

## 我的整体理解

你要把现在的“直接推荐”改成一次有明确状态的推荐前需求收集：

1. 先和用户确认推荐条件，再进入商城取数和推荐。
2. 每轮最多问一个需求项，例如只问价格区间，不能一次问“预算、场景、送谁、偏好什么”。
3. 用户明确表示不想回答时，跳过需求收集，立即使用已有信息和用户画像推荐。
4. 已提供的信息不能重复问；用户一轮提供了多个条件则全部记录，不强行拆成多轮。
5. 当需求足够形成可靠推荐时主动停止追问，不能为了走完流程而机械提问。

这里的“收集需求”是面向用户的对话式需求收集，不是现有的 `collect_recommendation_context`。后者收集的是购物车、浏览、订单和画像等后台数据。

## 当前项目情况

现有推荐链路是：

```text
understand_goal
  → collect_recommendation_context
  → generate_recommendation_spec
  → search_organic_candidates
  → search_ad_candidates
  → recommend_products
  → rerank_recommendations（需要时）
```

Goal Understanding 已经能够提取商品推荐槽位，包括品类、价格、场景、用途、收礼对象、必须标签和排除标签；但当前只有意图含糊或冲突时才追问。提示词甚至明确要求“信息差不多就直接推荐”，见 [shopping_agent.md](/Users/mindeng/workspace/niub-shangcheng/agent-service/prompts/shopping_agent.md:123) 和 [goal_understanding.md](/Users/mindeng/workspace/niub-shangcheng/agent-service/prompts/goal_understanding.md:65)。

Recommendation SPEC 也有 `missing_information`，见 [models.py](/Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/models.py:202)，但它是在 SPEC 生成之后产生的，目前没有代码消费它来向用户逐项提问。

因此当前缺少的不是槽位定义，而是三样东西：

- 推荐前的需求收集阶段；
- 跨轮累积、更新和跳过需求的明确状态；
- 严格保证每轮只问一个需求项的执行机制。

目前对话会保存 Goal Understanding、Plan、SPEC 和推荐结果，但没有独立的“推荐需求草稿”状态。多轮需求收集不能只依赖模型记住聊天记录，否则容易重复提问、丢失之前回答或把“预算不限”误判成整个流程跳过。

## 需要收集的内容

建议直接复用 Recommendation SPEC 已支持、且商城检索能够消费的字段：

| 需求项 | 对应字段 | 作用 | 建议优先级 |
|---|---|---|---|
| 商品目标 | `query`、`category` | 确定想买什么 | 最高 |
| 价格区间 | `min_price_cents`、`max_price_cents` | 排除超预算商品 | 高 |
| 用途 | `usage` | 通勤、居家、办公、送礼等 | 高 |
| 购买场景 | `scenario` | 自用、送礼、补货 | 中高 |
| 赠送对象 | `recipient` | 送礼时判断年龄、关系和偏好 | 仅在送礼时 |
| 必须条件 | `required_tags` | 必须轻便、必须低糖等 | 中 |
| 排除条件 | `excluded_tags` | 不要木质香、不要某类商品等 | 中 |

像 `preferred_categories`、`preferred_tags` 和 `negative_tags` 更适合从画像、浏览、订单和购物车推断，不应作为用户必答项。

当前 SPEC 没有独立支持品牌、颜色、尺寸、材质、到货时间等强字段。虽然部分表达可以暂时映射成标签，但没有可靠的结构化检索能力，因此第一阶段不建议把它们列为固定必问项。

我建议的默认提问顺序是：

1. 商品目标是什么；
2. 预算区间是多少；
3. 主要用在什么场景；
4. 是自用、送人还是补货；
5. 如果是送人，送给谁；
6. 有没有必须满足或明确不要的条件。

顺序应结合上下文动态调整。例如用户已经说“推荐一个通勤包”，那么商品目标和用途都已经有了，下一条直接问预算。

## 每轮只收集一项的理解

“每次只收集一项需求”我理解为：

- 每轮助手最多提出一个问题；
- 价格上下限算一个需求项，不拆成两次问；
- 用户在一轮中主动说出多个条件时全部接收；
- 当前答案已经提供过的槽位不重复追问；
- 已经足够推荐时直接进入推荐，不要求所有槽位全部填满；
- 用户回答“不限、都可以、你决定、没有要求”时，只跳过当前这一项，然后决定是否继续下一项，而不是默认整个流程都跳过。

示例：

```text
用户：帮我推荐个通勤包
助手：预算大概在什么区间？

用户：200 元以内
助手：主要想用来装电脑，还是日常随身物品？

用户：装电脑
助手：开始推荐
```

第二轮用户同时说“200 元以内、装电脑”，则两项一起记录，不能再问用途。

## 跳过的理解

跳过有两种范围。

第一种是跳过当前一项：

```text
助手：预算大概在什么区间？
用户：预算不限
```

此时只把预算标记为跳过，仍可继续询问下一个关键项。

第二种是跳过整个需求收集：

```text
用户：你别管那么多，直接推荐
```

此时不再提问，立即使用：

- 当前消息里已经提供的条件；
- 前几轮已经收集的累积需求；
- 用户画像、购物车、浏览和订单等后台信号；
- Recommendation SPEC 生成出的软偏好。

然后用已有信息完成 SPEC、搜索、评分和终排。不能先反问“确定要跳过吗”。

“随便推荐”“不用问了”“你直接选”“你看着办”可以归为整个流程跳过。“预算随便”则只跳过预算这一项。

## 需要形成的推荐状态

实现时建议把需求收集状态做成结构化数据，而不是仅写在 Plan 的自由文本里。至少需要表达：

- 当前是否处于需求收集中；
- 已收集的槽位及来源；
- 已经问过的槽位；
- 用户主动跳过的槽位；
- 是否要求跳过整个收集流程；
- 当前待问的一项；
- 需求是否已经足够，可以进入 SPEC 和搜索。

下一轮要“合并旧需求 + 当前回答”，而不是只使用当前消息重新理解。用户修改预算、场景或排除条件时更新对应槽位；切换成另一个完全不同的推荐目标时，再清除旧推荐需求或开启新的需求状态。

## 我目前采用的默认边界

- 只对 `product_recommendation` 启用该流程，订单查询和售后不受影响。
- 需求收集优先于 Recommendation SPEC 和商品搜索；处于提问轮时不调用推荐工具。
- 用户提供的条件可以成为硬约束，行为和画像推断仍然只能作为软偏好。
- 收集流程应该按“信息增益”停止，而不是强制问完全部字段。
- 第一版先支持自然语言跳过，不依赖新增“跳过”按钮；如果要做按钮，那是前端和协议层的额外改动。
- 当用户直接说出足够详细的条件时，例如“300 元以内、送妈妈的轻便通勤包，不要木质香”，不需要再走提问，直接进入推荐。

## User

好，根据这个需求理解，制定一个设计和实施方案

## Assistant

# 推荐需求收集设计与实施方案

## 一、核心设计结论

推荐流程调整为：

```text
understand_goal
  → 合并/推进需求收集状态
      ├─ 仍在收集：只输出一个问题，结束本轮
      └─ 已收集或用户要求跳过：继续推荐
          → collect_recommendation_context
          → generate_recommendation_spec
          → 商品/广告搜索
          → 评分与终排
```

采用“模型理解 + 代码状态机”的混合方案：

- Goal Understanding 负责识别用户本轮表达的槽位、跳过意图和新需求/需求修改。
- 确定性状态机负责合并跨轮需求、选择下一项、保证一轮只问一项、避免重复提问。
- Recommendation SPEC 继续负责召回策略和软偏好，但硬约束只能来自用户明确提供的需求。
- 需求收集状态单独持久化，不能只依赖聊天记录或 Plan 文本。

这样既保留自然语言理解能力，又避免完全依赖提示词导致一次问多项、重复问或跳过判断不稳定。

## 二、需求收集项

建议把需求划分为五个“收集项”。每个收集项内部可以包含多个关联字段，但对用户只问一个问题。

| 顺序 | 收集项 | 对应字段 | 示例问题 |
|---|---|---|---|
| 1 | 商品目标 | `query`、`category` | 你主要想买哪类商品？ |
| 2 | 价格区间 | `min_price_cents`、`max_price_cents` | 预算大概在什么区间？ |
| 3 | 使用场景 | `usage` | 这个商品主要用在什么场景？ |
| 4 | 购买对象 | `scenario` | 这次是自用、送人，还是补货？ |
| 5 | 额外条件 | `required_tags`、`excluded_tags` | 有没有必须满足或明确不要的条件？ |

补充规则：

- 如果第 4 项回答“送人”，再单独问一次收礼对象 `recipient`，不把收礼对象和使用场景放在同一个问题里。
- 上下限算一个价格区间问题，不拆分追问。
- 商品目标的 `query` 和 `category` 算同一项。
- 必须条件和排除条件合并为“额外条件”一项，但不能和其他槽位一起问。
- `preferred_categories`、`preferred_tags`、`weak_categories` 等继续由 SPEC 推断，不作为固定必答项。
- 当前不增加品牌、颜色、尺寸、材质、到货时间等固定问题，因为 SPEC 和商城搜索尚未可靠支持。

所有问题使用代码中的固定模板，由主 Agent 原样输出。主 Agent 不自行改写或追加第二个问题。

## 三、状态流转

新增 `RecommendationRequirementState`，建议包含：

```python
class RecommendationRequirementState(BaseModel):
    status: Literal["collecting", "ready", "completed"]
    bypass_all: bool = False
    slots: RecommendationRequirementSlots
    pending_slot: RequirementSlot | None = None
    next_question: str | None = None
    asked_slots: list[RequirementSlot]
    skipped_slots: list[RequirementSlot]
    revision: int = 1
    updated_at: str
```

状态含义：

- `collecting`：还有待收集项，当前回合只向用户提一个问题。
- `ready`：需求已收集或已跳过，可以进入 SPEC 和搜索。
- `completed`：本轮推荐已经完成，保留状态供后续修改。

主要流转规则：

1. 新推荐请求且没有可复用状态时，从 `collecting` 开始。
2. 当前消息提供了某个槽位时，立即合并，不再询问该槽位。
3. 当前消息一次提供多个槽位时，全部保存，只询问下一个尚未确认的槽位。
4. 某个槽位已经问过一次但用户没有回答时，将该槽位标记为跳过，不再重复追问。
5. 用户回答“不限、都可以、没有要求”时，只跳过当前收集项。
6. 用户说“你别管那么多，直接推荐”“不用问了”“随便推荐”时，整套收集流程在该轮立即结束。
7. 用户修改预算或场景时，保留其他已有需求并重新推荐，不重新走全部问题。
8. 用户明确说“重新推荐一个别的商品”时，可以清空旧的显式需求并开启新一轮收集。

最终状态由确定性代码推进，而不是让模型自行决定是否已经问完。

## 四、跳过设计

Goal Understanding 的输出增加一个结构化信号：

```python
class RecommendationCollectionSignal(BaseModel):
    skip_all: bool = False
    skipped_slots: list[RequirementSlot] = []
    restart: bool = False
```

对应行为：

- `skip_all=true`：不展示任何问题，立即使用当前需求、历史需求、画像和行为数据推荐。
- `skipped_slots=["budget"]`：仅跳过预算，继续处理其他未确认项。
- `restart=true`：清空旧的用户显式需求，开始新的推荐任务。
- 没有信号：正常合并本轮槽位并推进状态机。

需要在 Goal Understanding Prompt 中明确区分：

- “预算不限”只跳过预算。
- “都行，你推荐吧”视为跳过整个收集流程。
- “你别管那么多，直接推荐”跳过整个收集流程，而且本轮不能先确认。
- 普通回答“200 元以内”是提供预算，不属于跳过。

## 五、推荐阶段的衔接

### SPEC 生成

`generate_recommendation_spec` 增加前置校验：

- 状态为 `collecting` 时，拒绝生成 SPEC。
- 状态为 `ready` 时，使用累积后的 `RecommendationRequirementState.slots`。
- 用户显式需求和跳过状态要传给 SPEC Generator。

SPEC Prompt 新增 `requirements` 输入，并规定：

- `hard_constraints` 只能来自 `requirements.slots`。
- 用户跳过的槽位不能由画像或行为推断成硬约束。
- 画像、订单、购物车和浏览记录仍只能进入软偏好。
- `missing_information` 可以继续用于诊断，但不再直接驱动逐项提问。

现有 `_apply_explicit_goal_constraints` 需要改为从累积需求状态应用约束，而不是只读取当前轮的 `goal.slots`。

### 无商品目标的直接推荐

用户直接要求“随便推荐”，又没有任何商品目标时，不能让 SPEC 用“直接推荐”这类词做关键词搜索，否则容易召回为空。

建议给 SPEC 增加：

```python
recall_mode: Literal["targeted", "broad"] = "targeted"
```

- 有明确商品目标时使用 `targeted`。
- 整体跳过且没有目标时使用 `broad`。
- `broad` 模式仍应用价格、品类等硬过滤，但不要求关键词命中。
- 自然搜索和广告搜索都支持 broad recall。

这会同时涉及 [recommendation_spec.md](/Users/mindeng/workspace/niub-shangcheng/agent-service/prompts/recommendation_spec.md:28)、[search.py](/Users/mindeng/workspace/niub-shangcheng/mall-service/src/mall_service/search.py:14) 和两边对应的 SPEC 模型。

## 六、代码改动范围

| 文件 | 改动 |
|---|---|
| [models.py](/Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/models.py:145) | 新增需求槽位、收集信号和 `RecommendationRequirementState` |
| 新文件 `recommendation_requirements.py` | 实现合并、询问顺序、跳过、状态推进和问题模板 |
| [goal_understanding.py](/Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/goal_understanding.py:70) | 在理解结果中加入收集信号 |
| [goal_understanding.md](/Users/mindeng/workspace/niub-shangcheng/agent-service/prompts/goal_understanding.md:40) | 增加跳过、跳过单项、新任务信号定义 |
| [agent_runner.py](/Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/agent_runner.py:114) | Context 增加需求状态；`understand_goal` 后推进状态；SPEC 工具增加状态校验；SSE 返回状态 |
| [api.py](/Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/api.py:88) | 接收上一轮需求状态、保存本轮状态 |
| [storage.py](/Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/storage.py:303) | 在消息 metadata 中保存和恢复需求状态 |
| [shopping_agent.md](/Users/mindeng/workspace/niub-shangcheng/agent-service/prompts/shopping_agent.md:45) | 增加需求收集阶段；`collecting` 时只能原样输出问题并结束 |
| `recommendation_spec.py`、`recommendation_spec.md` | 接收累积需求；支持 broad recall |
| `mall-service/models.py`、`search.py`、`api.py` | 支持 broad recall 搜索 |
| 测试文件 | 覆盖状态合并、单项提问、跳过、持久化和完整推荐链路 |

不需要新增一个模型工具回合。把状态推进放在现有 `understand_goal` 工具完成后的确定性代码里，可以避免额外消耗一个 Agent turn，也不容易触发当前 `max_turns` 限制。

## 七、主 Agent 执行约束

推荐 Prompt 增加明确规则：

1. `primary_intent=product_recommendation` 且需求状态为 `collecting` 时：
   - 只能输出状态机返回的 `next_question`；
   - 不得改写问题；
   - 不得追加其他问题；
   - 不得调用上下文收集、SPEC、搜索或推荐工具；
   - 本轮结束后保存需求状态。
2. 状态为 `ready` 时：
   - 不再次确认已有需求；
   - 直接进入推荐主流程。
3. 用户整体跳过时：
   - 本轮不再出现需求问题；
   - 直接使用已知需求进行 SPEC 和推荐。
4. Plan 中可以显示“确认推荐需求”步骤，但 Plan 不是需求状态的唯一来源。

## 八、实施顺序

### 阶段 1：领域模型和状态机

- 新增需求槽位、收集信号和状态模型。
- 实现需求合并、下一项选择、单项跳过、整体跳过和重复问题保护。
- 先完成纯单元测试，不接入模型。

### 阶段 2：Goal Understanding

- 扩展 Prompt 输出收集信号。
- 在 `understand_goal` 后调用状态机。
- 保证当前轮提供的信息与历史信息合并。
- 测试价格、品类、场景、送礼对象和排除条件的提取。

### 阶段 3：推荐编排和持久化

- `collecting` 时提前结束本轮。
- `ready` 时继续调用现有推荐链路。
- 将需求状态写入 SSE `done` 和消息 metadata。
- 刷新页面或继续历史会话时恢复需求状态。
- 保留旧消息 metadata 的兼容性，旧记录没有状态时按新任务处理。

### 阶段 4：SPEC 和搜索衔接

- SPEC 从累积需求读取硬约束。
- 增加整体跳过场景的 broad recall。
- 确保跳过预算后，画像预算只能作为软偏好。
- 更新自然商品和广告搜索。

### 阶段 5：文档和验收

- 更新推荐流程文档和多轮测试说明。
- 增加真实模型对话验收，不只看单元测试。

## 九、测试清单

必须覆盖以下行为：

1. “推荐个东西”只问商品目标。
2. “推荐个通勤包”不再问目标或用途，只问预算。
3. 回答预算后只问下一项，不重复预算。
4. 一轮提供多个条件时全部记录，不重复追问。
5. “预算不限”只跳过预算。
6. “你别管那么多，直接推荐”不提问，直接进入推荐。
7. 送礼场景在确认送人后才询问收礼对象。
8. 已完成的推荐中修改预算时，保留品类和用途并重新推荐。
9. 需求收集中不调用 SPEC、搜索和推荐工具。
10. 每轮助手回答最多包含一个问题。
11. 需求状态在对话刷新后仍能恢复。
12. 无商品目标且整体跳过时，可以走 broad recall，不应因关键词为空直接无结果。
13. 现有推荐、广告、语义终排、多意图和订单流程不回归。

验证命令仍使用：

```bash
uv run pytest
pnpm --dir web build
```

核心验收标准是：需求收集阶段每轮只问一项、不重复；用户随时可以整体跳过；跳过发生在当前轮且无需二次确认；进入推荐后只使用累计的显式需求和已有软偏好，不把模型推断误写成硬约束。

## User

1. 不使用代码状态机的方案，而是改为全靠模型理解来推进；2. 不要使用固定模板，让大模型自主决定如何询问。基于此，调整你的方案。

## Assistant

# 调整后的方案：由模型自主推进需求收集

## 一、核心变化

推荐流程调整为：

```text
每轮用户消息
  → Goal Understanding 模型读取上一轮需求状态
  → 模型合并当前需求
  → 模型判断：继续询问 / 信息充分 / 用户跳过
      ├─ 继续询问：模型生成一个问题，本轮不推荐
      └─ 信息充分或跳过：进入 SPEC、搜索和推荐
```

代码不负责：

- 决定先问品类还是预算；
- 维护固定的槽位收集顺序；
- 判断哪一项需求“更难获得”；
- 自动把未回答的槽位标记为跳过；
- 生成或改写问题模板；
- 推进 `collecting → ready` 之类的状态迁移。

代码只负责：

- 向模型提供上一轮的需求状态和最近对话；
- 校验模型输出的数据结构；
- 保存模型提交的需求状态；
- 在需求仍在收集中时阻止推荐工具继续执行；
- 将模型生成的 `next_question` 原样交给用户。

## 二、模型维护的需求状态

在 Goal Understanding 的输出中增加一个模型自己维护的状态：

```json
{
  "recommendation_requirements": {
    "status": "collecting",
    "slots": {
      "query": null,
      "category": "箱包",
      "min_price_cents": null,
      "max_price_cents": null,
      "required_tags": ["通勤"],
      "excluded_tags": [],
      "scenario": "self",
      "usage": "通勤",
      "recipient": null
    },
    "next_question": "这个包你希望控制在多少预算以内？",
    "declined_requirements": [],
    "collection_reason": "已有通勤包目标，但缺少价格条件，下一项由模型选择"
  }
}
```

状态只有三种：

- `collecting`：模型认为还需要了解用户需求。
- `ready`：模型认为现有信息已经足够推荐。
- `bypassed`：用户明确跳过整个需求收集流程。

这里的 `status` 由模型输出，不由代码根据槽位数量自动计算。

`slots` 保存累计需求，而不是只保存当前消息的内容。模型需要主动完成合并：

- 当前消息补充预算时，保留之前的品类和用途。
- 用户修改预算时，以最新预算覆盖旧预算。
- 当前消息一次提供多个条件时，全部记录。
- 用户取消或修改排除条件时，由模型更新累计列表。
- 用户开始一个明显不同的推荐任务时，由模型判断是否清空旧需求。

`declined_requirements` 也是模型维护的自由文本列表，例如 `["预算不想说", "不关心具体款式"]`。代码不解析它的语义，只持久化后传回模型，帮助下一轮避免重复询问。

## 三、模型如何决定下一项

不设置固定槽位顺序或固定问题模板。Goal Understanding Prompt 只提供判断原则：

1. 优先询问对召回或排序影响最大的缺失信息。
2. 每轮只选择一个需求项询问。
3. 问题应结合当前商品目标、已收集信息、用户画像和对话语境生成。
4. 用户已经提供或明确拒绝的信息不能重复询问。
5. 已经足以形成合理推荐时，主动停止收集。
6. 不要为了覆盖所有字段而机械提问。
7. 允许不同场景下询问不同内容，不要求固定问完品类、预算、用途和偏好。

例如，模型可以自行判断以下问法：

```text
推荐一个通勤包
→ 你主要是想找装电脑的，还是日常随身用的？

想送个礼物
→ 准备送给谁？大概希望控制在什么价位？
```

第二句是否同时问对象和价格由模型决定，但输出契约要求 `next_question` 最终只包含一个问题；模型应通过自然语言选择最值得问的一项，而不是把多个槽位拼接成问卷。

无需强制模型每次都问预算。模型可以根据当前信息自行判断，例如用户已经说“送妈妈一个 300 元以内的通勤包”，它可以直接进入推荐。

## 四、跳过行为的理解

跳过完全由模型从用户表达中判断。

### 整体跳过

用户表达：

```text
你别管那么多，直接推荐
不用问了，你帮我选
随便推荐吧
```

Goal Understanding 输出：

```json
{
  "recommendation_requirements": {
    "status": "bypassed",
    "slots": {
      "...": "保留当前已有需求"
    },
    "next_question": null,
    "collection_reason": "用户明确要求直接推荐"
  }
}
```

本轮不再提问，直接进入 SPEC 和推荐流程，不需要二次确认。

### 跳过当前一项

用户表达：

```text
预算不限
价格你看着办
我不关心材质
```

模型可以：

- 将相关槽位标记为不限制；
- 或写入 `declined_requirements`；
- 然后自主决定继续问其他问题，或者认为信息足够直接推荐。

如果用户说“都行，你直接推荐吧”，模型应识别为整体跳过，而不是只跳过当前预算问题。

## 五、主 Agent 的执行约束

Goal Understanding 仍是每轮第一步。主 Agent 根据模型返回的状态路由：

### `collecting`

主 Agent 只输出 `next_question`：

```text
用户：推荐个通勤包

Goal Understanding：
status = collecting
next_question = "你希望预算控制在什么范围？"

Agent：你希望预算控制在什么范围？
```

本轮禁止调用：

- `collect_recommendation_context`
- `generate_recommendation_spec`
- 商品或广告搜索
- 推荐和终排工具

需求问题只能有一句，不追加“另外还想了解……”之类的问题。

### `ready`

不重复确认已有需求，直接进入原推荐链路。

### `bypassed`

不提问，直接使用：

- 已累计的显式需求；
- 历史对话中的有效条件；
- 用户画像、购物车、浏览和订单等软偏好；
- 模型生成的推荐召回策略。

然后进入 SPEC、搜索、评分和终排。

## 六、SPEC 阶段的调整

Recommendation SPEC Generator 接收模型维护的累计需求状态，而不是只接收当前轮 Goal Understanding 的 `slots`。

SPEC Prompt 增加：

```json
{
  "requirements": {
    "status": "collecting | ready | bypassed",
    "slots": {},
    "declined_requirements": [],
    "collection_reason": ""
  }
}
```

规则保持为：

- `hard_constraints` 只能来自用户明确提供的累计需求。
- 用户跳过或拒绝的条件不能由画像推断成硬约束。
- 浏览、订单、购物车和画像只能形成软偏好。
- `missing_information` 仍作为 SPEC 诊断信息，不再承担提问调度。
- 用户整体跳过且没有商品目标时，由 SPEC 模型自行决定是否采用宽泛召回，不要求代码套规则。
- SPEC 模型可以输出 `recall_mode: targeted | broad`，用于支持“直接推荐”场景。

## 七、代码改动范围

| 文件 | 改动 |
|---|---|
| [models.py](/Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/models.py:165) | 增加模型输出的累计需求状态结构，不增加状态迁移函数 |
| [goal_understanding.md](/Users/mindeng/workspace/niub-shangcheng/agent-service/prompts/goal_understanding.md:40) | 增加需求状态、跨轮合并、跳过判断和自主提问规则 |
| [goal_understanding.py](/Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/goal_understanding.py:70) | 将上一轮累计需求传给模型，并校验返回结构 |
| [shopping_agent.md](/Users/mindeng/workspace/niub-shangcheng/agent-service/prompts/shopping_agent.md:45) | 增加 `collecting / ready / bypassed` 路由规则 |
| [agent_runner.py](/Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/agent_runner.py:760) | `generate_recommendation_spec` 在 `collecting` 时拒绝执行；将模型问题交给主 Agent |
| [recommendation_spec.py](/Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/recommendation_spec.py:80) | 使用累计需求生成 SPEC |
| [recommendation_spec.md](/Users/mindeng/workspace/niub-shangcheng/agent-service/prompts/recommendation_spec.md:28) | 接收累计需求；支持模型决定宽泛召回 |
| [storage.py](/Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/storage.py:309) | 需求状态随 Goal Understanding 一起持久化，旧记录缺失时兼容为空 |
| [api.py](/Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/api.py:73) | 下一轮继续传递包含需求状态的上一轮 Goal Understanding |
| `mall-service/models.py`、`search.py` | 支持模型输出的 `recall_mode` |

不需要新增：

- `recommendation_requirements.py` 状态机；
- 固定槽位顺序；
- 固定问题模板；
- 代码自动推进函数；
- 额外的需求收集工具调用回合。

可以把累计需求状态直接放在 `GoalUnderstandingResult` 内，复用现有的 Goal Understanding 持久化和跨轮传递机制。

## 八、实施步骤

### 第一步：扩展模型输出契约

- 增加 `RecommendationRequirementState`。
- 增加 `status`、累计 `slots`、`next_question`、`declined_requirements` 和 `collection_reason`。
- 只做 Pydantic 校验，不写状态迁移逻辑。

### 第二步：改造 Goal Understanding Prompt

- 让模型接收并理解上一轮累计需求。
- 让模型负责合并、冲突处理和任务重置。
- 让模型自主决定是否继续询问、问什么、是否足够推荐。
- 让模型识别整体跳过和单项跳过。
- 要求模型在 `collecting` 时只生成一个问题。

### 第三步：改造主 Agent Prompt

- `collecting`：只输出模型问题，结束本轮。
- `ready`：进入推荐流程。
- `bypassed`：立即进入推荐流程。
- 明确禁止主 Agent 对模型问题追加第二问。

### 第四步：接入 SPEC 和商城搜索

- SPEC 从累计需求读取硬约束。
- 支持模型选择 targeted/broad recall。
- 保证画像推断不会覆盖用户显式条件。
- 保持现有广告、评分和语义终排规则不变。

### 第五步：持久化和可观测性

- 将累计需求状态随 Goal Understanding 保存到消息 metadata。
- 保存 `collection_reason`，便于检查模型为什么继续问、停止或跳过。
- 刷新页面和历史会话恢复时，将状态重新注入下一轮 Goal Understanding。
- 历史消息没有该字段时按空状态处理。

## 九、测试方式

由于问题和顺序不再固定，测试不能断言“第二条一定问预算”，而应验证行为不变量。

### 结构性测试

- `collecting` 时不能调用 SPEC、搜索和推荐工具。
- `collecting` 时返回的 `next_question` 必须存在。
- `ready/bypassed` 时允许进入推荐流程。
- 累计需求状态可以通过 metadata 持久化和恢复。
- 上一轮商品目标、预算和用途能传入下一轮 Goal Understanding。

### Scripted Model 测试

使用固定模型输出验证编排：

- 模型返回一个问题时，主 Agent 原样输出且不调用其他工具。
- 模型返回 `ready` 时，不展示问题，直接进入 SPEC。
- 模型返回 `bypassed` 时，跳过问题并进入推荐。
- 模型累计的需求能正确传给 SPEC Generator。

### 模型行为评测

使用真实模型跑一组对话案例，检查：

- 每轮最多一个问题；
- 已经回答的信息不会重复询问；
- 用户提供多个条件时不会拆分重问；
- “别问了，直接推荐”在当轮跳过；
- “预算不限”不被误判成整体跳过；
- 不同商品场景下问题内容可以自然变化；
- 模型认为信息足够时能主动停止；
- 需求状态跨多轮不会丢失。

关键验收标准是：

1. 代码中没有需求顺序选择和状态迁移逻辑；
2. 问题由 Goal Understanding 模型动态生成；
3. 每轮最多一个问题；
4. 模型能根据累计信息自主决定继续、停止或跳过；
5. 用户整体跳过时，本轮直接推荐，不再确认。

## User

好，按计划执行

## Assistant

我开始按调整后的模型驱动方案实施：先扩展 Goal Understanding 的累计需求契约，再接入主流程、SPEC 与宽泛召回，最后补持久化和回归测试。代码只做校验和编排，不加入固定提问顺序或问题模板。

## Activity

    $ sed -n '1,260p' agent-service/tests/test_agent_runner.py
    import asyncio
    import json
    import logging
    
    import httpx
    from agents.testing import ScriptedModel, assistant_message, function_call
    from agents.tool_context import ToolContext
    from mall_service.api import app as mall_app
    
    from agent_service.agent_runner import (
        RecommendationContextSnapshot,
        ShoppingAgentContext,
        create_tools,
        normalize_openai_base_url,
        stream_agent_reply,
    )
    from agent_service.goal_understanding import AgentGoalUnderstander
    from agent_service.llm_config import LLMConfig
    from agent_service.mall_client import MallClient
    from agent_service.models import (
        AdInfo,
        ConversationMessage,
        GoalUnderstandingResult,
        OrderLink,
        PlanState,
        Product,
        RecommendationBatch,
        RecommendationDemand,
        RecommendationSpec,
        RecommendationSpecHardConstraints,
        ScoredProduct,
        SemanticRankingItem,
        SemanticRankingResult,
        SourceEvidence,
    )
    from agent_service.recommendation_reranker import (
        AgentSemanticReranker,
        semantic_candidates,
    )
    from agent_service.recommendation_spec import AgentRecommendationSpecGenerator
    
    
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
    
    
    def prepare_recommendation_context(
        context: ShoppingAgentContext,
        *,
        spec: RecommendationSpec | None = None,
    ) -> None:
        invoke_tool(context, "collect_recommendation_context", {})
        context.recommendation_spec = spec or recommendation_spec()
        invoke_tool(context, "search_organic_candidates", {})
        invoke_tool(context, "search_ad_candidates", {})
    
    
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
    
    
    class StaticGoalUnderstander:
        def __init__(self, result: GoalUnderstandingResult) -> None:
            self.result = result
            self.previous_goal: GoalUnderstandingResult | None = None
    
        async def understand(
            self,
            *,
            current_message: str,
            recent_messages: list[ConversationMessage],
            previous_goal: GoalUnderstandingResult | None,
            previous_recommendations: list[Product],
            previous_orders: list[OrderLink],
        ) -> GoalUnderstandingResult:
            self.previous_goal = previous_goal
            return self.result
    
    
    class StaticRecommendationSpecGenerator:
        def __init__(self, result: RecommendationSpec) -> None:
            self.result = result
    
        async def generate(
            self,
            *,
            goal: GoalUnderstandingResult,
            agent_profile,
            platform_profile,
            cart,
            browse_history,
            orders,
            catalog,
        ) -> RecommendationSpec:
            return self.result
    
    
    def goal_understanding(
        *,
        query: str = "通勤",
        intents: list[str] | None = None,
    ) -> GoalUnderstandingResult:
        ordered_intents = intents or ["product_recommendation"]
        return GoalUnderstandingResult(
            primary_intent=ordered_intents[0],
            intents=ordered_intents,
            pending_intents=ordered_intents[1:],
            goal=f"推荐与 {query} 相关的商品",
            confidence=0.95,
            slots={
                "query": query,
                "max_price_cents": 30000,
                "scenario": "self",
            },
            pending_intent_question=(
                "当前已处理第一个意图。需要我继续处理后续意图吗？"
                if len(ordered_intents) > 1
                else None
            ),
        )
    
    
    def recommendation_spec(
        *,
        queries: list[str] | None = None,
    ) -> RecommendationSpec:
        return RecommendationSpec(
            goal_summary="推荐预算 300 元以内的通勤商品",
            hard_constraints=RecommendationSpecHardConstraints(
                max_price_cents=30000,
            ),
            preferred_categories=["箱包"],
            preferred_tags=["通勤"],
            search_queries=queries or ["通勤", "办公室"],
            scenario="self",
            usage="通勤",
            source_evidence=[],
            confidence=0.9,
        )
    
    
    def scored_candidate(
    ✓ • 0ms

## Activity

    $ sed -n '260,760p' agent-service/tests/test_agent_runner.py
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
        context.goal_understanding = goal_understanding()
        prepare_recommendation_context(context)
        invoke_tool(
            context,
            "recommend_products",
            {},
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
    
    
    def test_understand_goal_action_returns_first_intent_and_pending_intents() -> None:
        context = ShoppingAgentContext(
            mall=mall_client(),
            current_user_request="推荐一个通勤包，然后查一下我的订单",
        )
        context.goal_understander = StaticGoalUnderstander(
            goal_understanding(
                intents=["product_recommendation", "order_query"],
            )
        )
    
        result = json.loads(
            invoke_tool(context, "understand_goal", {})
        )
    
        assert result["status"] == "understood"
        assert result["goal_understanding"]["primary_intent"] == (
            "product_recommendation"
        )
        assert result["goal_understanding"]["pending_intents"] == ["order_query"]
        assert context.goal_understanding is not None
    
    
    def test_goal_understanding_agent_uses_its_own_prompt() -> None:
        model = ScriptedModel(
            [
                [
                    assistant_message(
                        json.dumps(
                            {
                                "intents": [
                                    "product_recommendation",
                                    "order_query",
                                ],
                                "goal": "推荐通勤包并查询订单",
                                "confidence": 0.96,
                                "slots": {"query": "通勤"},
                                "missing_slots": [],
                                "requires_clarification": False,
                                "clarification_question": None,
                            },
                            ensure_ascii=False,
                        )
                    )
                ]
            ]
        )
        understander = AgentGoalUnderstander(
            config=llm_config(),
            model=model,
        )
    
        result = asyncio.run(
            understander.understand(
                current_message="推荐一个通勤包，然后查订单",
                recent_messages=[
                    ConversationMessage(
                        role="user",
                        content="推荐一个通勤包，然后查订单",
                    )
                ],
                previous_goal=None,
                previous_recommendations=[],
                previous_orders=[],
            )
        )
    
        assert result.primary_intent == "product_recommendation"
        assert result.pending_intents == ["order_query"]
        assert model.first_call is not None
        assert "Goal Understanding" in (
            model.first_call.system_instructions or ""
        )
    
    
    def test_collect_context_and_generate_recommendation_spec_are_separate_actions(
        caplog,
    ) -> None:
        context = ShoppingAgentContext(mall=mall_client())
        context.goal_understanding = goal_understanding()
        context.recommendation_spec_generator = StaticRecommendationSpecGenerator(
            recommendation_spec()
        )
    
        collected = json.loads(
            invoke_tool(context, "collect_recommendation_context", {})
        )
        with caplog.at_level(
            logging.DEBUG,
            logger="agent_service.observability.tool",
        ):
            generated = json.loads(
                invoke_tool(context, "generate_recommendation_spec", {})
            )
    
        assert collected["status"] == "collected"
        assert collected["browse_count"] > 0
        assert generated["status"] == "generated"
        assert context.recommendation_spec is not None
        assert context.recommendation_spec.search_queries == ["通勤", "办公室"]
        spec_log = next(
            record
            for record in caplog.records
            if getattr(record, "event", "")
            == "agent.recommendation_spec.generated"
        )
        assert getattr(spec_log, "agent.recommendation_spec")[
            "search_queries"
        ] == ["通勤", "办公室"]
        assert (
            getattr(spec_log, "agent.recommendation_spec.search_query_count")
            == 2
        )
    
    
    def test_organic_and_ad_search_actions_cache_candidates_independently() -> None:
        context = ShoppingAgentContext(mall=mall_client())
        context.goal_understanding = goal_understanding()
        invoke_tool(context, "collect_recommendation_context", {})
        context.recommendation_spec = recommendation_spec()
    
        organic = json.loads(
            invoke_tool(context, "search_organic_candidates", {})
        )
        assert organic["status"] == "searched"
        assert context.organic_search_attempted is True
        assert context.organic_search_products
        assert context.ad_search_attempted is False
    
        ads = json.loads(
            invoke_tool(context, "search_ad_candidates", {})
        )
        assert ads["status"] == "searched"
        assert context.ad_search_attempted is True
        assert context.ad_search_candidates
        assert ads["source_status"] == "ok_with_data"
    
    
    def test_recommendation_spec_agent_uses_own_prompt_and_explicit_constraints() -> None:
        context = ShoppingAgentContext(mall=mall_client())
        context.goal_understanding = goal_understanding()
        invoke_tool(context, "collect_recommendation_context", {})
        snapshot = context.recommendation_context
        assert snapshot is not None
        model = ScriptedModel(
            [
                [
                    assistant_message(
                        json.dumps(
                            {
                                "goal_summary": "寻找通勤商品",
                                "hard_constraints": {
                                    "category": None,
                                    "min_price_cents": None,
                                    "max_price_cents": 50000,
                                    "required_tags": [],
                                    "excluded_tags": [],
                                },
                                "preferred_categories": ["箱包"],
                                "preferred_tags": ["通勤", "轻便"],
                                "weak_categories": ["家居"],
                                "negative_tags": [],
                                "search_queries": ["通勤包", "轻便通勤包"],
                                "scenario": "self",
                                "usage": "通勤",
                                "recipient": None,
                                "source_evidence": [
                                    {
                                        "source": "cart",
                                        "observation": "购物车中有通勤双肩包",
                                        "influence": "high",
                                    }
                                ],
                                "confidence": 0.92,
                                "missing_information": [],
                            },
                            ensure_ascii=False,
                        )
                    )
                ]
            ]
        )
        generator = AgentRecommendationSpecGenerator(
            config=llm_config(),
            model=model,
        )
    
        spec = asyncio.run(
            generator.generate(
                goal=context.goal_understanding,
                agent_profile=snapshot.agent_profile,
                platform_profile=snapshot.platform_profile,
                cart=snapshot.cart,
                browse_history=snapshot.browse_history,
                orders=snapshot.orders,
                catalog=snapshot.catalog,
            )
        )
    
        assert spec.hard_constraints.max_price_cents == 30000
        assert spec.search_queries == ["通勤包", "轻便通勤包"]
        assert model.first_call is not None
        assert "Recommendation SPEC Generator" in (
            model.first_call.system_instructions or ""
        )
    
    
    def test_recommend_products_formula_path_selects_top_two() -> None:
        context = ShoppingAgentContext(mall=mall_client(), user_id=999)
        context.goal_understanding = goal_understanding(query="家居")
        prepare_recommendation_context(
            context,
            spec=recommendation_spec(queries=["家居", "居家"]),
        )
        context.ad_search_candidates = []
        context.ad_search_status = "ok_empty"
    
        result = json.loads(
            invoke_tool(
                context,
                "recommend_products",
                {},
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
        context.goal_understanding = goal_understanding(query="宠物用品")
        no_match_spec = recommendation_spec(queries=["宠物用品"]).model_copy(
            update={
                "preferred_categories": [],
                "preferred_tags": [],
                "usage": None,
            }
        )
        prepare_recommendation_context(
            context,
            spec=no_match_spec,
        )
    
        result = json.loads(
            invoke_tool(
                context,
                "recommend_products",
                {},
            )
        )
    
    ✓ • 0ms

## Activity

    $ sed -n '760,1320p' agent-service/tests/test_agent_runner.py
    
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
                        "understand_goal",
                        {},
                        call_id="call-goal",
                    ),
                ],
                [
                    assistant_message(
                        json.dumps(
                            {
                                "intents": ["product_recommendation"],
                                "goal": "推荐预算 300 元以内的通勤商品",
                                "confidence": 0.96,
                                "slots": {
                                    "query": "通勤",
                                    "max_price_cents": 30000,
                                    "scenario": "self",
                                },
                                "missing_slots": [],
                                "requires_clarification": False,
                                "clarification_question": None,
                            },
                            ensure_ascii=False,
                        )
                    )
                ],
                [
                    function_call(
                        "collect_recommendation_context",
                        {},
                        call_id="call-context",
                    )
                ],
                [
                    function_call(
                        "generate_recommendation_spec",
                        {},
                        call_id="call-spec",
                    )
                ],
                [
                    assistant_message(
                        json.dumps(
                            {
                                "goal_summary": "推荐 300 元以内通勤商品",
                                "hard_constraints": {
                                    "category": None,
                                    "min_price_cents": None,
                                    "max_price_cents": 30000,
                                    "required_tags": [],
                                    "excluded_tags": [],
                                },
                                "preferred_categories": ["箱包"],
                                "preferred_tags": ["通勤"],
                                "weak_categories": [],
                                "negative_tags": [],
                                "search_queries": ["通勤", "办公室"],
                                "scenario": "self",
                                "usage": "通勤",
                                "recipient": None,
                                "source_evidence": [
                                    {
                                        "source": "cart",
                                        "observation": "购物车中有通勤双肩包",
                                        "influence": "high",
                                    }
                                ],
                                "confidence": 0.92,
                                "missing_information": [],
                            },
                            ensure_ascii=False,
                        )
                    )
                ],
                [
                    function_call(
                        "search_organic_candidates",
                        {},
                        call_id="call-organic-search",
                    ),
                    function_call(
                        "search_ad_candidates",
                        {},
                        call_id="call-ad-search",
                    ),
                ],
                [
                    function_call(
                        "recommend_products",
                        {},
                        call_id="call-recommend",
                    )
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
        assert len(model.last_call.tools) == 19
        assert model.first_call is not None
        assert "小牛导购" in (model.first_call.system_instructions or "")
        assert "独立语义终排" in (
            model.first_call.system_instructions or ""
        )
        assert "pending_intent_question" in (
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
    
    
    def test_observability_emits_react_llm_and_tool_spans(
        caplog,
        otel_test_exporter,
    ) -> None:
        otel_test_exporter.clear()
        model = ScriptedModel(
            [
                [
                    function_call(
                        "get_agent_profile",
                        {},
                        call_id="call-profile",
                    )
                ],
                [assistant_message("已经读取画像。")],
            ]
        )
    
        async def collect_events() -> list[dict[str, object]]:
            return [
                event
                async for event in stream_agent_reply(
                    [ConversationMessage(role="user", content="推荐通勤商品")],
                    llm_config(),
                    mall_client(),
                    model_override=model,
                )
            ]
    
        with caplog.at_level(
            logging.DEBUG,
            logger="agent_service.observability.tool",
        ):
            events = asyncio.run(collect_events())
        assert events[-1]["type"] == "done"
    
        spans = otel_test_exporter.get_finished_spans()
        span_names = [span.name for span in spans]
        assert span_names.count("agent.react") >= 2
        assert span_names.count("agent.llm") >= 2
        assert span_names.count("agent.tool") == 1
    
        llm_spans = [span for span in spans if span.name == "agent.llm"]
        assert all(
            "agent.llm.duration_ms" in span.attributes
            for span in llm_spans
        )
        assert any(
            "agent.llm.first_char_ms" in span.attributes
            for span in llm_spans
        )
    
        tool_logs = [
            record
            for record in caplog.records
            if getattr(record, "event", "").startswith("agent.tool.")
        ]
    ✓ • 0ms

## Activity

    $ sed -n '1,260p' agent-service/tests/test_agent_api.py && sed -n '1,380p' mall-service/src/mall_service/models.py && sed -n '130,220p' mall-service/src/mall_service/api.py
    from pathlib import Path
    
    import pytest
    from fastapi.testclient import TestClient
    
    import agent_service.api as api_module
    from agent_service.api import app
    from agent_service.agent_runner import sse_event
    from agent_service.llm_config import LLMConfig, LLMConfigError
    from agent_service.mall_client import get_mall_client
    from agent_service.models import Product, ProductList
    from agent_service.storage import ConversationStore, get_conversation_store
    
    client = TestClient(app)
    
    TEST_CONFIG = LLMConfig(
        base_url="http://model.test/v1",
        api_key="test-key",
        model="test-model",
    )
    
    
    @pytest.fixture
    def store(tmp_path: Path) -> ConversationStore:
        conversation_store = ConversationStore(tmp_path / "agent-test.db")
        previous_overrides = app.dependency_overrides.copy()
        app.dependency_overrides[get_conversation_store] = lambda: conversation_store
        yield conversation_store
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
    
    
    class FakeMallClient:
        async def list_products(self) -> ProductList:
            products = [
                Product(
                    id="tote",
                    name="帆布托特包",
                    description="日常通勤",
                    price_cents=6900,
                    category="文创",
                )
            ]
            return ProductList(items=products, total=1)
    
    
    PLAN_STATE = {
        "plan": {
            "plan_id": "plan-test",
            "goal": "找到合适的商品",
            "steps": [
                {
                    "step_id": "search",
                    "title": "搜索商品",
                    "objective": "获取候选商品",
                    "kind": "retrieval",
                    "depends_on": [],
                    "metadata": {},
                },
                {
                    "step_id": "submit",
                    "title": "提交推荐",
                    "objective": "生成最终推荐",
                    "kind": "decision",
                    "depends_on": ["search"],
                    "metadata": {},
                },
            ],
        },
        "status": "active",
        "current_step_id": "submit",
        "step_states": [
            {"step_id": "search", "status": "completed", "note": "找到 1 件商品"},
            {"step_id": "submit", "status": "in_progress", "note": None},
        ],
        "summary": "已完成候选搜索",
        "next_action": "提交最终推荐",
        "revision": 2,
        "updated_at": "2026-11-02T12:00:00+00:00",
    }
    
    ORDER_LINK = {
        "order_id": "order-test",
        "status": "pending_payment",
        "total_cents": 6900,
        "preview_path": "/orders/order-test",
        "ordered_at": "2026-11-02T12:10:00+00:00",
    }
    
    RECOMMENDED_PRODUCT = {
        "id": "tote",
        "name": "帆布托特包",
        "description": "通勤包",
        "price_cents": 6900,
        "category": "箱包",
        "badge": "人气单品",
        "stock": 10,
        "tags": ["通勤"],
        "image_url": None,
        "is_ad": True,
        "ad_label": "广告",
        "ad_id": "ad-test",
        "campaign_id": "campaign-test",
    }
    
    GOAL_UNDERSTANDING = {
        "primary_intent": "product_recommendation",
        "intents": ["product_recommendation", "order_query"],
        "pending_intents": ["order_query"],
        "goal": "推荐商品并查询订单",
        "confidence": 0.95,
        "slots": {"query": "通勤"},
        "missing_slots": [],
        "requires_clarification": False,
        "clarification_question": None,
        "pending_intent_question": "是否继续处理订单查询？",
    }
    
    RECOMMENDATION_SPEC = {
        "goal_summary": "推荐通勤商品",
        "hard_constraints": {
            "category": None,
            "min_price_cents": None,
            "max_price_cents": 30000,
            "required_tags": [],
            "excluded_tags": [],
        },
        "preferred_categories": ["箱包"],
        "preferred_tags": ["通勤"],
        "weak_categories": [],
        "negative_tags": [],
        "search_queries": ["通勤", "办公室"],
        "scenario": "self",
        "usage": "通勤",
        "recipient": None,
        "source_evidence": [],
        "confidence": 0.9,
        "missing_information": [],
    }
    
    
    async def fake_agent_stream(
        messages,
        config,
        mall,
        previous_plan_state=None,
        previous_recommendations=None,
        previous_orders=None,
        previous_goal_understanding=None,
    ):
        yield {"type": "start", "message_id": "assistant-test"}
        yield {
            "type": "tool_started",
            "message_id": "assistant-test",
            "call_id": "call-1",
            "tool": "search_products",
            "arguments": '{"query":"通勤"}',
        }
        yield {
            "type": "tool_completed",
            "message_id": "assistant-test",
            "call_id": "call-1",
            "tool": "search_products",
        }
        yield {
            "type": "plan_updated",
            "message_id": "assistant-test",
            "plan_state": PLAN_STATE,
        }
        yield {
            "type": "order_created",
            "message_id": "assistant-test",
            "order": ORDER_LINK,
        }
        yield {
            "type": "recommendations",
            "message_id": "assistant-test",
            "products": [RECOMMENDED_PRODUCT],
        }
        yield {
            "type": "delta",
            "message_id": "assistant-test",
            "content": "真实模型回复",
        }
        yield {
            "type": "done",
            "message_id": "assistant-test",
            "tool_trace": [
                {
                    "call_id": "call-1",
                    "tool": "search_products",
                    "arguments": '{"query":"通勤"}',
                    "status": "completed",
                    "summary": "1 product",
                }
            ],
            "plan_state": PLAN_STATE,
            "orders": [ORDER_LINK],
            "recommendations": [RECOMMENDED_PRODUCT],
            "goal_understanding": GOAL_UNDERSTANDING,
            "recommendation_spec": RECOMMENDATION_SPEC,
        }
    
    
    def test_health() -> None:
        response = client.get("/health")
    
        assert response.status_code == 200
        assert response.json()["service"] == "agent-service"
    
    
    def test_chat_uses_mall_catalog() -> None:
        previous_overrides = app.dependency_overrides.copy()
        app.dependency_overrides[get_mall_client] = lambda: FakeMallClient()
        try:
            response = client.post("/api/chat", json={"message": "推荐一件商品"})
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)
    
        assert response.status_code == 200
        assert "帆布托特包" in response.json()["reply"]
        assert response.json()["products"][0]["id"] == "tote"
    
    
    def test_chat_rejects_blank_message() -> None:
        response = client.post("/api/chat", json={"message": "   "})
    
        assert response.status_code == 422
    
    
    def test_stream_chat_persists_completed_conversation(
        store: ConversationStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            api_module,
            "load_llm_config",
            lambda: TEST_CONFIG,
        )
        monkeypatch.setattr(api_module, "stream_agent_reply", fake_agent_stream)
    
        response = client.post(
            "/api/chat/stream",
            json={"message": "A"},
        )
    
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert '"type": "conversation"' in response.text
        assert '"type": "tool_started"' in response.text
        assert '"type": "plan_updated"' in response.text
        assert '"type": "order_created"' in response.text
        assert '"type": "recommendations"' in response.text
        assert "真实模型回复" in response.text
        assert '"type": "done"' in response.text
    
        conversations = store.list_conversations(1)
        assert len(conversations) == 1
        assert conversations[0].title == "A"
    from typing import Literal
    
    from pydantic import BaseModel, Field
    
    
    class Product(BaseModel):
        id: str
        name: str
        description: str
        price_cents: int
        category: str
        badge: str | None = None
        stock: int | None = None
        tags: list[str] = Field(default_factory=list)
        image_url: str | None = None
    
    
    class ProductList(BaseModel):
        items: list[Product]
        total: int
    
    
    class BrowseEvent(BaseModel):
        event_id: str
        product_id: str
        action: Literal["view", "detail_view"]
        occurred_at: str
        dwell_seconds: int = Field(ge=0)
        source_page: str
    
    
    class BrowseHistory(BaseModel):
        status: Literal["ok"] = "ok"
        items: list[BrowseEvent]
    
    
    class OrderItem(BaseModel):
        product_id: str
        name: str
        image_url: str | None = None
        quantity: int = Field(gt=0)
        unit_price_cents: int = Field(ge=0)
        subtotal_cents: int = Field(ge=0)
    
    
    class ShippingAddress(BaseModel):
        recipient: str
        phone_masked: str
        region: str
        detail: str
    
    
    class Order(BaseModel):
        order_id: str
        user_id: int = 1
        status: Literal[
            "pending_payment",
            "paid",
            "completed",
            "cancelled",
            "refunded",
        ]
        ordered_at: str
        address: ShippingAddress | None = None
        subtotal_cents: int = Field(ge=0)
        shipping_fee_cents: int = Field(default=0, ge=0)
        total_cents: int = Field(ge=0)
        items: list[OrderItem]
        preview_path: str | None = None
        paid_at: str | None = None
        expires_at: str | None = None
    
    
    class OrderHistory(BaseModel):
        status: Literal["ok"] = "ok"
        items: list[Order]
    
    
    class CreateOrderItem(BaseModel):
        product_id: str = Field(min_length=1, max_length=100)
        quantity: int = Field(default=1, ge=1, le=99)
    
    
    class CreateOrderRequest(BaseModel):
        items: list[CreateOrderItem] = Field(min_length=1, max_length=20)
        idempotency_key: str = Field(min_length=1, max_length=200)
    
    
    class CartItem(BaseModel):
        product_id: str
        quantity: int = Field(gt=0)
        added_at: str
    
    
    class Cart(BaseModel):
        status: Literal["ok"] = "ok"
        updated_at: str | None = None
        items: list[CartItem]
    
    
    class CategoryAffinity(BaseModel):
        category: str
        score: float = Field(ge=0, le=1)
    
    
    class PlatformProfile(BaseModel):
        user_id: int
        source: Literal["recommendation_platform"] = "recommendation_platform"
        segments: list[str] = Field(default_factory=list)
        category_affinity: list[CategoryAffinity] = Field(default_factory=list)
        price_band_cents: tuple[int, int] | None = None
        preferred_tags: list[str] = Field(default_factory=list)
        confidence: float = Field(default=0, ge=0, le=1)
        updated_at: str
    
    
    class PlatformProfileResponse(BaseModel):
        status: Literal["ok"] = "ok"
        profile: PlatformProfile | None
    
    
    class AdInfo(BaseModel):
        is_ad: Literal[True] = True
        ad_id: str
        campaign_id: str
        label: Literal["广告"] = "广告"
    
    
    class ProductCandidate(BaseModel):
        product: Product
        source: Literal["product_recommendation", "advertisement"]
        score: float = Field(ge=0, le=1)
        matched_signals: list[str] = Field(default_factory=list)
        ad: AdInfo | None = None
    
    
    class RecommendationResponse(BaseModel):
        status: Literal["ok"] = "ok"
        items: list[ProductCandidate]
    
    
    class ProductRecommendationRequest(BaseModel):
        user_id: int
        query: str = Field(default="", max_length=200)
        category: str | None = Field(default=None, max_length=50)
        min_price_cents: int | None = Field(default=None, ge=0)
        max_price_cents: int | None = Field(default=None, ge=0)
        limit: int = Field(default=5, ge=1, le=10)
    
    
    class AdRecommendationRequest(BaseModel):
        user_id: int
        query: str = Field(default="", max_length=200)
        category: str | None = Field(default=None, max_length=50)
        max_price_cents: int | None = Field(default=None, ge=0)
        limit: int = Field(default=10, ge=1, le=10)
    
    
    class RecommendationSpecHardConstraints(BaseModel):
        category: str | None = Field(default=None, max_length=100)
        min_price_cents: int | None = Field(default=None, ge=0)
        max_price_cents: int | None = Field(default=None, ge=0)
        required_tags: list[str] = Field(default_factory=list)
        excluded_tags: list[str] = Field(default_factory=list)
    
    
    class RecommendationSpecEvidence(BaseModel):
        source: str = Field(min_length=1, max_length=100)
        observation: str = Field(min_length=1, max_length=500)
        influence: Literal["high", "medium", "low"]
    
    
    class RecommendationSearchSpec(BaseModel):
        goal_summary: str = Field(min_length=1, max_length=1_000)
        hard_constraints: RecommendationSpecHardConstraints = Field(
            default_factory=RecommendationSpecHardConstraints
        )
        preferred_categories: list[str] = Field(default_factory=list)
        preferred_tags: list[str] = Field(default_factory=list)
        weak_categories: list[str] = Field(default_factory=list)
        negative_tags: list[str] = Field(default_factory=list)
        search_queries: list[str] = Field(min_length=1, max_length=6)
        scenario: Literal[
            "general",
            "self",
            "gift",
            "replenishment",
        ] = "general"
        usage: str | None = Field(default=None, max_length=500)
        recipient: str | None = Field(default=None, max_length=200)
        source_evidence: list[RecommendationSpecEvidence] = Field(
            default_factory=list
        )
        confidence: float = Field(ge=0, le=1)
        missing_information: list[str] = Field(default_factory=list)
    
    
    class RecommendationSearchRequest(BaseModel):
        spec: RecommendationSearchSpec
        limit: int = Field(default=10, ge=1, le=20)
    def get_cart(user_id: int) -> Cart:
        return CARTS.get(user_id, Cart(items=[]))
    
    
    @app.get(
        "/api/users/{user_id}/platform-profile",
        response_model=PlatformProfileResponse,
    )
    def get_platform_profile(user_id: int) -> PlatformProfileResponse:
        return PlatformProfileResponse(profile=PLATFORM_PROFILES.get(user_id))
    
    
    @app.post(
        "/api/recommendations/products",
        response_model=RecommendationResponse,
    )
    def get_product_recommendations(
        request: ProductRecommendationRequest,
    ) -> RecommendationResponse:
        return RecommendationResponse(items=recommend_products(request))
    
    
    @app.post(
        "/api/recommendations/ads",
        response_model=RecommendationResponse,
    )
    def get_ad_recommendations(
        request: AdRecommendationRequest,
    ) -> RecommendationResponse:
        return RecommendationResponse(items=recommend_ads(request))
    
    
    @app.post(
        "/api/search/organic",
        response_model=ProductList,
    )
    def search_organic_with_spec(
        request: RecommendationSearchRequest,
    ) -> ProductList:
        products = search_mock_with_spec(
            request.spec,
            channel="organic",
            limit=request.limit,
        )
        return ProductList(items=products, total=len(products))
    
    
    @app.post(
        "/api/search/ads",
        response_model=RecommendationResponse,
    )
    def search_ads_with_spec(
        request: RecommendationSearchRequest,
    ) -> RecommendationResponse:
        candidates = search_mock_ads_with_spec(
            request.spec,
            limit=request.limit,
        )
        return RecommendationResponse(items=candidates)
    ✓ • 0ms

## Activity

    $ sed -n '1,240p' mall-service/tests/test_mall_api.py && sed -n '1,140p' agent-service/tests/test_mall_contract.py && sed -n '1,260p' agent-service/tests/conftest.py
    import pytest
    from fastapi.testclient import TestClient
    
    from mall_service.api import app
    from mall_service.catalog import PRODUCTS
    from mall_service.orders import reset_order_store
    
    client = TestClient(app)
    
    
    @pytest.fixture(autouse=True)
    def reset_mock_orders():
        stock = {product.id: product.stock for product in PRODUCTS}
        reset_order_store()
        yield
        reset_order_store()
        for product in PRODUCTS:
            product.stock = stock[product.id]
    
    
    def test_health() -> None:
        response = client.get("/health")
    
        assert response.status_code == 200
        assert response.json()["service"] == "mall-service"
    
    
    def test_list_products() -> None:
        response = client.get("/api/products")
    
        assert response.status_code == 200
        assert response.json()["total"] == 5
        assert response.json()["items"][0]["stock"] == 18
    
    
    def test_filter_products() -> None:
        response = client.get("/api/products", params={"q": "家居"})
    
        assert response.status_code == 200
        assert "moon-lamp" in {
            product["id"] for product in response.json()["items"]
        }
    
    
    def test_product_budget_and_limit_filters() -> None:
        response = client.get(
            "/api/products",
            params={"q": "通勤", "max_price_cents": 10000, "limit": 2},
        )
    
        assert response.status_code == 200
        products = response.json()["items"]
        assert len(products) == 2
        assert all(product["price_cents"] <= 10000 for product in products)
    
    
    def test_unknown_product_returns_404() -> None:
        response = client.get("/api/products/missing")
    
        assert response.status_code == 404
    
    
    def test_user_context_endpoints_return_demo_data() -> None:
        browse = client.get("/api/users/1/browse-history")
        orders = client.get("/api/users/1/orders")
        cart = client.get("/api/users/1/cart")
        profile = client.get("/api/users/1/platform-profile")
    
        assert browse.status_code == 200
        assert browse.json()["items"][0]["product_id"] == "moon-lamp"
        assert orders.status_code == 200
        assert orders.json()["items"][0]["order_id"] == "order-1001"
        assert cart.status_code == 200
        assert cart.json()["items"][0]["product_id"] == "commuter-backpack"
        assert profile.status_code == 200
        assert profile.json()["profile"]["confidence"] == 0.76
    
    
    def test_new_user_has_empty_context_without_errors() -> None:
        browse = client.get("/api/users/999/browse-history")
        orders = client.get("/api/users/999/orders")
        cart = client.get("/api/users/999/cart")
        profile = client.get("/api/users/999/platform-profile")
    
        assert browse.json()["items"] == []
        assert orders.json()["items"] == []
        assert cart.json()["items"] == []
        assert profile.json()["profile"] is None
    
    
    def test_product_and_ad_recommendations() -> None:
        product_response = client.post(
            "/api/recommendations/products",
            json={"user_id": 1, "query": "通勤", "limit": 3},
        )
        ad_response = client.post(
            "/api/recommendations/ads",
            json={"user_id": 1, "query": "通勤"},
        )
    
        assert product_response.status_code == 200
        products = product_response.json()["items"]
        assert 0 < len(products) <= 3
        assert all(item["source"] == "product_recommendation" for item in products)
        assert ad_response.status_code == 200
        ads = ad_response.json()["items"]
        assert 0 < len(ads) <= 10
        if ads:
            assert ads[0]["source"] == "advertisement"
            assert ads[0]["ad"]["is_ad"] is True
            assert ads[0]["ad"]["label"] == "广告"
    
    
    def test_spec_search_logs_mock_es_query_and_returns_products(
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        spec = {
            "goal_summary": "找一盏卧室桌面灯",
            "hard_constraints": {
                "category": "家居",
                "min_price_cents": 5000,
                "max_price_cents": 20000,
                "required_tags": ["台灯"],
                "excluded_tags": [],
            },
            "preferred_categories": ["家居"],
            "preferred_tags": ["卧室", "暖光"],
            "weak_categories": [],
            "negative_tags": [],
            "search_queries": ["月影桌面灯", "卧室台灯"],
            "scenario": "self",
            "usage": "卧室阅读照明",
            "recipient": None,
            "source_evidence": [
                {
                    "source": "browse",
                    "observation": "最近浏览过桌面灯",
                    "influence": "medium",
                }
            ],
            "confidence": 0.91,
            "missing_information": [],
        }
        caplog.set_level("INFO", logger="mall_service.search")
    
        response = client.post(
            "/api/search/organic",
            json={"spec": spec, "limit": 5},
        )
    
        assert response.status_code == 200
        products = response.json()["items"]
        assert products
        assert products[0]["id"] == "moon-lamp"
        assert all(product["price_cents"] <= 20000 for product in products)
        assert "mock_es_query channel=organic" in caplog.text
        assert '"category.keyword"' in caplog.text
        assert '"range"' in caplog.text
        assert '"multi_match"' in caplog.text
        assert "最近浏览过桌面灯" in caplog.text
    
    
    def test_spec_ad_search_returns_ad_candidates() -> None:
        spec = {
            "goal_summary": "找通勤小物",
            "hard_constraints": {
                "category": None,
                "min_price_cents": None,
                "max_price_cents": 30000,
                "required_tags": [],
                "excluded_tags": [],
            },
            "preferred_categories": ["箱包"],
            "preferred_tags": ["通勤"],
            "weak_categories": [],
            "negative_tags": [],
            "search_queries": ["通勤", "办公室"],
            "scenario": "self",
            "usage": "通勤",
            "recipient": None,
            "source_evidence": [],
            "confidence": 0.9,
            "missing_information": [],
        }
    
        response = client.post(
            "/api/search/ads",
            json={"spec": spec, "limit": 3},
        )
    
        assert response.status_code == 200
        ads = response.json()["items"]
        assert 0 < len(ads) <= 3
        assert all(item["source"] == "advertisement" for item in ads)
        assert all(item["ad"]["is_ad"] is True for item in ads)
    
    
    def test_create_order_uses_catalog_snapshot_and_is_idempotent() -> None:
        body = {
            "items": [{"product_id": "commuter-backpack", "quantity": 1}],
            "idempotency_key": "checkout-turn-1",
        }
    
        first = client.post("/api/users/1/orders", json=body)
        second = client.post("/api/users/1/orders", json=body)
    
        assert first.status_code == 201
        assert second.status_code == 201
        order = first.json()
        assert first.json()["order_id"] == second.json()["order_id"]
        assert order["status"] == "pending_payment"
        assert order["items"][0]["name"] == "轻旅通勤双肩包"
        assert order["items"][0]["unit_price_cents"] == 29900
        assert order["total_cents"] == 29900
        assert order["address"]["recipient"] == "演示用户"
        assert order["preview_path"] == f"/orders/{order['order_id']}"
    
    
    def test_order_preview_and_payment_flow() -> None:
        create_response = client.post(
            "/api/users/1/orders",
            json={
                "items": [{"product_id": "travel-bottle", "quantity": 1}],
                "idempotency_key": "checkout-turn-pay",
            },
        )
        order_id = create_response.json()["order_id"]
        initial_stock = next(
            product.stock for product in PRODUCTS if product.id == "travel-bottle"
        )
    
        preview = client.get(f"/api/users/1/orders/{order_id}")
        paid = client.post(f"/api/users/1/orders/{order_id}/pay")
        paid_again = client.post(f"/api/users/1/orders/{order_id}/pay")
    
        assert preview.status_code == 200
        assert preview.json()["order_id"] == order_id
        assert paid.status_code == 200
        assert paid.json()["status"] == "paid"
        assert paid_again.json()["status"] == "paid"
    import asyncio
    
    import httpx
    from mall_service.api import app as mall_app
    
    from agent_service.mall_client import MallClient
    from agent_service.models import (
        RecommendationSpec,
        RecommendationSpecHardConstraints,
    )
    
    
    def test_agent_can_read_mall_catalog_api() -> None:
        client = mall_client()
    
        catalog = asyncio.run(client.list_products())
    
        assert catalog.total == 5
        assert catalog.items[0].name == "轻旅通勤双肩包"
    
    
    def mall_client() -> MallClient:
        return MallClient(
            base_url="http://mall.test",
            transport=httpx.ASGITransport(app=mall_app),
        )
    
    
    def test_agent_can_read_user_context_and_recommendations() -> None:
        client = mall_client()
    
        async def load_data():
            return (
                await client.get_browse_history(1),
                await client.get_orders(1),
                await client.get_cart(1),
                await client.get_platform_profile(1),
                await client.get_product_recommendations(
                    1,
                    query="通勤",
                    limit=3,
                ),
                await client.get_ad_recommendations(1, query="通勤"),
            )
    
        browse, orders, cart, profile, products, ads = asyncio.run(load_data())
    
        assert browse[0].product_id == "moon-lamp"
        historical_order = next(
            order for order in orders if order.order_id == "order-1001"
        )
        assert historical_order.items[0].product_id == "hand-cream"
        assert cart.items[0].product_id == "commuter-backpack"
        assert profile is not None
        assert len(products) <= 3
        assert len(ads) <= 10
    
    
    def test_agent_passes_whole_spec_to_mock_es_search() -> None:
        client = mall_client()
        spec = RecommendationSpec(
            goal_summary="寻找通勤商品",
            hard_constraints=RecommendationSpecHardConstraints(
                max_price_cents=30000,
            ),
            preferred_categories=["箱包"],
            preferred_tags=["通勤"],
            search_queries=["通勤", "办公室"],
            scenario="self",
            usage="通勤",
            confidence=0.9,
        )
    
        async def search():
            return (
                await client.search_organic_with_spec(spec, limit=5),
                await client.search_ads_with_spec(spec, limit=3),
            )
    
        products, ads = asyncio.run(search())
    
        assert products
        assert all(product.price_cents <= 30000 for product in products)
        assert ads
        assert all(item.source == "advertisement" for item in ads)
    import pytest
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )
    
    from agent_service.observability.spans import set_observability_clients
    
    
    @pytest.fixture(scope="session")
    def otel_test_exporter() -> InMemorySpanExporter:
        provider = TracerProvider()
        exporter = InMemorySpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        set_observability_clients(
            tracer=provider.get_tracer("agent-service-tests"),
        )
        yield exporter
        provider.shutdown()
    ✓ • 0ms

## Activity

    $ sed -n '1,320p' agent-service/src/agent_service/observability/agents.py && sed -n '1,220p' agent-service/src/agent_service/mall_client.py && sed -n '220,340p' agent-service/src/agent_service/mall_client.py
    import asyncio
    import contextvars
    import json
    import logging
    import time
    from contextlib import contextmanager
    from functools import wraps
    from typing import Any, Iterator, Sequence
    
    from agents import RawResponsesStreamEvent, RunHooks, Runner
    from agents.tool_context import ToolContext
    from openai.types.responses import ResponseTextDeltaEvent
    from opentelemetry import trace
    from opentelemetry.context import attach, detach
    from opentelemetry.trace import Span, Status, StatusCode
    
    from .config import ToolLogConfig
    from .serialization import (
        json_safe,
        payload_text,
        redact_payload,
        truncate_text,
    )
    from .spans import get_runtime_metrics, get_tracer
    
    
    tool_logger = logging.getLogger("agent_service.observability.tool")
    
    
    def _elapsed_ms(start_ns: int) -> float:
        return round((time.monotonic_ns() - start_ns) / 1_000_000, 3)
    
    
    def _elapsed_seconds(start_ns: int) -> float:
        return max(0, time.monotonic_ns() - start_ns) / 1_000_000_000
    
    
    def _usage_attributes(usage: Any) -> dict[str, int]:
        if usage is None:
            return {}
        input_details = getattr(usage, "input_tokens_details", None)
        output_details = getattr(usage, "output_tokens_details", None)
        return {
            "gen_ai.usage.input_tokens": int(
                getattr(usage, "input_tokens", 0) or 0
            ),
            "gen_ai.usage.output_tokens": int(
                getattr(usage, "output_tokens", 0) or 0
            ),
            "gen_ai.usage.total_tokens": int(
                getattr(usage, "total_tokens", 0) or 0
            ),
            "gen_ai.usage.cached_input_tokens": int(
                getattr(input_details, "cached_tokens", 0) or 0
            ),
            "gen_ai.usage.reasoning_tokens": int(
                getattr(output_details, "reasoning_tokens", 0) or 0
            ),
        }
    
    
    class AgentTraceSession:
        """Tracks ReAct and LLM spans for one streamed top-level run."""
    
        def __init__(
            self,
            *,
            model: str,
            parent_context: Any | None = None,
        ) -> None:
            self.model = model
            self.parent_context = parent_context
            self.react_index = 0
            self.tool_count = 0
            self.react_span: Span | None = None
            self.react_context: Any | None = None
            self.react_start_ns = 0
            self.llm_span: Span | None = None
            self.llm_start_ns = 0
            self.llm_first_char_recorded = False
            self.llm_first_output_recorded = False
            self.llm_output_chars = 0
            self.finished = False
    
        def start_llm(self) -> None:
            if self.finished:
                return
            if self.react_span is None:
                self.react_index += 1
                self.react_start_ns = time.monotonic_ns()
                self.react_span = get_tracer().start_span(
                    "agent.react",
                    context=self.parent_context,
                )
                self.react_span.set_attribute(
                    "agent.react.index",
                    self.react_index,
                )
                self.react_context = trace.set_span_in_context(
                    self.react_span,
                    self.parent_context,
                )
            if self.llm_span is not None:
                self._finish_llm("aborted")
            self.llm_start_ns = time.monotonic_ns()
            self.llm_first_char_recorded = False
            self.llm_first_output_recorded = False
            self.llm_output_chars = 0
            self.llm_span = get_tracer().start_span(
                "agent.llm",
                context=self.react_context,
            )
            self.llm_span.set_attribute("gen_ai.operation.name", "chat")
            self.llm_span.set_attribute(
                "gen_ai.request.model",
                self.model,
            )
            self.llm_span.set_attribute("agent.react.index", self.react_index)
            self.llm_span.set_attribute("agent.llm.streaming", True)
    
        def observe_model_event(self, event: Any) -> None:
            if self.llm_span is None:
                return
            event_type = getattr(event, "type", "")
            if event_type in {
                "response.output_item.added",
                "response.function_call_arguments.delta",
                "response.output_item.done",
            }:
                self._record_first_output()
            if isinstance(event, ResponseTextDeltaEvent):
                delta = event.delta or ""
                self.llm_output_chars += len(delta)
                if delta:
                    self._record_first_output()
                    self._record_first_char()
    
        def _record_first_output(self) -> None:
            if self.llm_first_output_recorded or self.llm_span is None:
                return
            self.llm_first_output_recorded = True
            elapsed = _elapsed_seconds(self.llm_start_ns)
            self.llm_span.set_attribute(
                "agent.llm.first_output_ms",
                elapsed * 1000,
            )
            runtime_metrics = get_runtime_metrics()
            if runtime_metrics is not None:
                runtime_metrics.llm_first_output.record(
                    elapsed,
                    {"gen_ai.request.model": self.model},
                )
    
        def _record_first_char(self) -> None:
            if self.llm_first_char_recorded or self.llm_span is None:
                return
            self.llm_first_char_recorded = True
            elapsed = _elapsed_seconds(self.llm_start_ns)
            self.llm_span.set_attribute(
                "agent.llm.first_char_ms",
                elapsed * 1000,
            )
            runtime_metrics = get_runtime_metrics()
            if runtime_metrics is not None:
                runtime_metrics.llm_first_char.record(
                    elapsed,
                    {"gen_ai.request.model": self.model},
                )
    
        def finish_llm(
            self,
            response: Any,
            *,
            outcome: str = "completed",
        ) -> None:
            if self.llm_span is None:
                return
            usage = getattr(response, "usage", None)
            attrs = _usage_attributes(usage)
            for key, value in attrs.items():
                self.llm_span.set_attribute(key, value)
            response_id = getattr(response, "response_id", None)
            if response_id:
                self.llm_span.set_attribute(
                    "gen_ai.response.id",
                    str(response_id),
                )
            self._finish_llm(outcome)
    
        def _finish_llm(self, outcome: str) -> None:
            if self.llm_span is None:
                return
            duration = _elapsed_seconds(self.llm_start_ns)
            self.llm_span.set_attribute("agent.llm.outcome", outcome)
            self.llm_span.set_attribute(
                "agent.llm.duration_ms",
                duration * 1000,
            )
            self.llm_span.set_attribute(
                "agent.llm.output_chars",
                self.llm_output_chars,
            )
            if outcome == "completed":
                self.llm_span.set_status(Status(StatusCode.OK))
            elif outcome != "aborted":
                self.llm_span.set_status(
                    Status(StatusCode.ERROR, outcome)
                )
            self.llm_span.end()
            self.llm_span = None
    
            runtime_metrics = get_runtime_metrics()
            if runtime_metrics is not None:
                runtime_metrics.llm_duration.record(
                    duration,
                    {
                        "gen_ai.request.model": self.model,
                        "operation": "chat",
                        "outcome": outcome,
                    },
                )
                runtime_metrics.llm_calls.add(
                    1,
                    {
                        "gen_ai.request.model": self.model,
                        "operation": "chat",
                        "outcome": outcome,
                    },
                )
    
        def record_token_usage(self, usage: Any) -> None:
            runtime_metrics = get_runtime_metrics()
            if runtime_metrics is not None and usage is not None:
                runtime_metrics.record_token_usage(
                    usage,
                    {"gen_ai.request.model": self.model},
                )
    
        def record_tool(self) -> None:
            self.tool_count += 1
            if self.react_span is not None:
                self.react_span.set_attribute(
                    "agent.react.tool_count",
                    self.tool_count,
                )
    
        def finish_react(self, outcome: str) -> None:
            if self.react_span is None:
                return
            duration = _elapsed_seconds(self.react_start_ns)
            self.react_span.set_attribute("agent.react.outcome", outcome)
            self.react_span.set_attribute(
                "agent.react.duration_ms",
                duration * 1000,
            )
            self.react_span.set_attribute(
                "agent.react.tool_count",
                self.tool_count,
            )
            if outcome == "completed":
                self.react_span.set_status(Status(StatusCode.OK))
            else:
                self.react_span.set_status(
                    Status(StatusCode.ERROR, outcome)
                )
            self.react_span.end()
            runtime_metrics = get_runtime_metrics()
            if runtime_metrics is not None:
                runtime_metrics.react_duration.record(
                    duration,
                    {
                        "react.index": self.react_index,
                        "outcome": outcome,
                    },
                )
            self.react_span = None
            self.react_context = None
            self.tool_count = 0
    
        def finish(
            self,
            outcome: str,
            error: BaseException | None = None,
        ) -> None:
            if self.finished:
                return
            self.finished = True
            if self.llm_span is not None:
                if error is not None:
                    self.llm_span.record_exception(error)
                self._finish_llm(outcome)
            self.finish_react(outcome)
    
        @contextmanager
        def bind(self) -> Iterator["AgentTraceSession"]:
            token = _current_agent_session.set(self)
            try:
                yield self
            finally:
                _current_agent_session.reset(token)
    
    
    class ObservabilityRunHooks(RunHooks[Any]):
        def __init__(
            self,
            session: AgentTraceSession,
        ) -> None:
            self.session = session
    
        async def on_llm_start(
            self,
            context: Any,
            agent: Any,
            system_prompt: str | None,
            input_items: Any,
        ) -> None:
            if self.session.react_span is not None:
                self.session.finish_react("completed")
            self.session.start_llm()
    
    import os
    from typing import Any
    
    import httpx
    from pydantic import BaseModel, ValidationError
    
    from .models import (
        BrowseEvent,
        CreateOrderItem,
        OrderRecord,
        PlatformProfile,
        Product,
        ProductCandidate,
        ProductList,
        RecommendationSpec,
        ShoppingCart,
    )
    from .observability.http import observed_async_transport
    
    
    class CatalogUnavailable(Exception):
        """Raised when a mall-service request cannot be completed."""
    
    
    class ProductNotFound(CatalogUnavailable):
        """Raised when a requested product does not exist."""
    
    
    class MallRequestError(CatalogUnavailable):
        """Raised when mall-service rejects a business operation."""
    
        def __init__(self, status_code: int, detail: str) -> None:
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail
    
    
    class BrowseHistoryResponse(BaseModel):
        status: str
        items: list[BrowseEvent]
    
    
    class OrderHistoryResponse(BaseModel):
        status: str
        items: list[OrderRecord]
    
    
    class PlatformProfileResponse(BaseModel):
        status: str
        profile: PlatformProfile | None
    
    
    class RecommendationResponse(BaseModel):
        status: str
        items: list[ProductCandidate]
    
    
    class MallClient:
        def __init__(
            self,
            base_url: str | None = None,
            transport: httpx.AsyncBaseTransport | None = None,
            timeout: float = 3.0,
        ) -> None:
            self.base_url = (
                base_url or os.getenv("MALL_SERVICE_URL", "http://127.0.0.1:8001")
            ).rstrip("/")
            self.transport = transport
            self.timeout = timeout
    
        async def _request(
            self,
            method: str,
            path: str,
            *,
            params: dict[str, Any] | None = None,
            json: dict[str, Any] | None = None,
        ) -> Any:
            try:
                transport = self.transport
                if transport is None:
                    transport = httpx.AsyncHTTPTransport()
                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    transport=observed_async_transport(transport),
                ) as client:
                    response = await client.request(
                        method,
                        f"{self.base_url}{path}",
                        params=params,
                        json=json,
                    )
                    response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    raise ProductNotFound("product does not exist") from exc
                try:
                    payload = exc.response.json()
                    detail = (
                        payload.get("detail")
                        if isinstance(payload, dict)
                        else None
                    )
                except ValueError:
                    detail = None
                raise MallRequestError(
                    exc.response.status_code,
                    detail if isinstance(detail, str) else "mall-service rejected request",
                ) from exc
            except (httpx.HTTPError, ValueError) as exc:
                raise CatalogUnavailable("mall-service is unavailable") from exc
    
        @staticmethod
        def _validate(model: type[BaseModel], payload: Any) -> Any:
            try:
                return model.model_validate(payload)
            except ValidationError as exc:
                raise CatalogUnavailable("mall-service returned invalid data") from exc
    
        async def list_products(self) -> ProductList:
            payload = await self._request("GET", "/api/products")
            return self._validate(ProductList, payload)
    
        async def search_products(
            self,
            query: str = "",
            category: str | None = None,
            max_price_cents: int | None = None,
            min_price_cents: int | None = None,
            limit: int = 5,
        ) -> list[Product]:
            params = {
                "q": query,
                "category": category,
                "max_price_cents": max_price_cents,
                "min_price_cents": min_price_cents,
                "limit": max(1, min(limit, 10)),
            }
            payload = await self._request(
                "GET",
                "/api/products",
                params={key: value for key, value in params.items() if value is not None},
            )
            catalog = self._validate(ProductList, payload)
            return catalog.items
    
        async def search_organic_with_spec(
            self,
            spec: RecommendationSpec,
            limit: int = 10,
        ) -> list[Product]:
            payload = await self._request(
                "POST",
                "/api/search/organic",
                json={
                    "spec": spec.model_dump(mode="json"),
                    "limit": max(1, min(limit, 20)),
                },
            )
            catalog = self._validate(ProductList, payload)
            return catalog.items
    
        async def get_product(self, product_id: str) -> Product | None:
            try:
                payload = await self._request("GET", f"/api/products/{product_id}")
            except ProductNotFound:
                return None
            try:
                return Product.model_validate(payload)
            except ValidationError as exc:
                raise CatalogUnavailable("mall-service returned invalid product") from exc
    
        async def get_browse_history(
            self,
            user_id: int,
            limit: int = 10,
        ) -> list[BrowseEvent]:
            payload = await self._request(
                "GET",
                f"/api/users/{user_id}/browse-history",
                params={"limit": max(1, min(limit, 20))},
            )
            return self._validate(BrowseHistoryResponse, payload).items
    
        async def get_orders(
            self,
            user_id: int,
            limit: int = 10,
        ) -> list[OrderRecord]:
            payload = await self._request(
                "GET",
                f"/api/users/{user_id}/orders",
                params={"limit": max(1, min(limit, 20))},
            )
            return self._validate(OrderHistoryResponse, payload).items
    
        async def get_cart(self, user_id: int) -> ShoppingCart:
            payload = await self._request("GET", f"/api/users/{user_id}/cart")
            return self._validate(ShoppingCart, payload)
    
        async def get_platform_profile(
            self,
            user_id: int,
        ) -> PlatformProfile | None:
            payload = await self._request(
                "GET",
                f"/api/users/{user_id}/platform-profile",
            )
            return self._validate(PlatformProfileResponse, payload).profile
    
        async def get_product_recommendations(
            self,
            user_id: int,
            query: str = "",
            category: str | None = None,
            min_price_cents: int | None = None,
            max_price_cents: int | None = None,
            limit: int = 10,
        ) -> list[ProductCandidate]:
        ) -> list[ProductCandidate]:
            payload = await self._request(
                "POST",
                "/api/recommendations/products",
                json={
                    "user_id": user_id,
                    "query": query,
                    "category": category,
                    "min_price_cents": min_price_cents,
                    "max_price_cents": max_price_cents,
                    "limit": max(1, min(limit, 10)),
                },
            )
            return self._validate(RecommendationResponse, payload).items
    
        async def get_ad_recommendations(
            self,
            user_id: int,
            query: str = "",
            category: str | None = None,
            max_price_cents: int | None = None,
            limit: int = 10,
        ) -> list[ProductCandidate]:
            payload = await self._request(
                "POST",
                "/api/recommendations/ads",
                json={
                    "user_id": user_id,
                    "query": query,
                    "category": category,
                    "max_price_cents": max_price_cents,
                    "limit": max(1, min(limit, 10)),
                },
            )
            return self._validate(RecommendationResponse, payload).items
    
        async def search_ads_with_spec(
            self,
            spec: RecommendationSpec,
            limit: int = 10,
        ) -> list[ProductCandidate]:
            payload = await self._request(
                "POST",
                "/api/search/ads",
                json={
                    "spec": spec.model_dump(mode="json"),
                    "limit": max(1, min(limit, 20)),
                },
            )
            return self._validate(RecommendationResponse, payload).items
    
        async def create_order(
            self,
            user_id: int,
            items: list[CreateOrderItem],
            idempotency_key: str,
        ) -> OrderRecord:
            payload = await self._request(
                "POST",
                f"/api/users/{user_id}/orders",
                json={
                    "items": [item.model_dump(mode="json") for item in items],
                    "idempotency_key": idempotency_key,
                },
            )
            return self._validate(OrderRecord, payload)
    
        async def get_order(
            self,
            user_id: int,
            order_id: str,
        ) -> OrderRecord | None:
            try:
                payload = await self._request(
                    "GET",
                    f"/api/users/{user_id}/orders/{order_id}",
                )
            except ProductNotFound:
                return None
            return self._validate(OrderRecord, payload)
    
        async def pay_order(
            self,
            user_id: int,
            order_id: str,
        ) -> OrderRecord:
            payload = await self._request(
                "POST",
                f"/api/users/{user_id}/orders/{order_id}/pay",
            )
            return self._validate(OrderRecord, payload)
    
    
    def get_mall_client() -> MallClient:
        return MallClient()
    ✓ • 0ms

## Assistant

设计落点已经明确：累计需求作为 Goal Understanding 模型输出的一部分保存，主流程只读取其 `collecting / ready / bypassed` 结果；代码不会自动选择下一项，也不会生成问题。现在先改数据契约和提示词，再接 SPEC 和搜索。

## Activity

    $ sed -n '1,220p' pyproject.toml && sed -n '1,180p' agent-service/pyproject.toml && sed -n '1,160p' mall-service/pyproject.toml
    [tool.uv.workspace]
    members = ["agent-service", "mall-service"]
    
    [dependency-groups]
    dev = ["pytest>=8"]
    
    [tool.pytest.ini_options]
    pythonpath = ["agent-service/src", "mall-service/src"]
    testpaths = ["agent-service/tests", "mall-service/tests"]
    [project]
    name = "agent-service"
    version = "0.1.0"
    description = "Shopping assistant agent HTTP service"
    requires-python = ">=3.11"
    dependencies = [
        "fastapi>=0.115,<1",
        "httpx>=0.27,<1",
        "openai-agents>=0.21,<1",
        "opentelemetry-api>=1.45,<2",
        "opentelemetry-exporter-prometheus>=0.66b0,<1",
        "opentelemetry-exporter-zipkin>=1.45,<2",
        "opentelemetry-instrumentation-fastapi>=0.66b0,<1",
        "opentelemetry-instrumentation-httpx>=0.66b0,<1",
        "opentelemetry-instrumentation-sqlite3>=0.66b0,<1",
        "opentelemetry-propagator-b3>=1.45,<2",
        "opentelemetry-sdk>=1.45,<2",
        "pyyaml>=6.0,<7",
        "uvicorn>=0.34,<1",
    ]
    
    [project.scripts]
    agent-service = "agent_service.main:run"
    
    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"
    
    [tool.hatch.build.targets.wheel]
    packages = ["src/agent_service"]
    [project]
    name = "mall-service"
    version = "0.1.0"
    description = "Mall catalog HTTP service"
    requires-python = ">=3.11"
    dependencies = [
        "fastapi>=0.115,<1",
        "uvicorn>=0.34,<1",
    ]
    
    [project.scripts]
    mall-service = "mall_service.main:run"
    
    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"
    
    [tool.hatch.build.targets.wheel]
    packages = ["src/mall_service"]
    ✓ • 0ms

## Activity

    $ rg -n "GoalUnderstandingResult\(|RecommendationSpec\(|RecommendationSearchSpec\(|goal_understanding=|GOAL_UNDERSTANDING" agent-service/tests mall-service/tests agent-service/src mall-service/src -g '*.py'
    agent-service/tests/test_mall_contract.py:61:    spec = RecommendationSpec(
    agent-service/tests/test_agent_api.py:106:GOAL_UNDERSTANDING = {
    agent-service/tests/test_agent_api.py:149:    previous_goal_understanding=None,
    agent-service/tests/test_agent_api.py:200:        "goal_understanding": GOAL_UNDERSTANDING,
    agent-service/tests/test_agent_api.py:339:        previous_goal_understanding=None,
    agent-service/tests/test_agent_api.py:396:            "goal_understanding": GOAL_UNDERSTANDING,
    agent-service/tests/test_agent_api.py:409:        previous_goal_understanding=None,
    agent-service/tests/test_agent_runner.py:222:    return GoalUnderstandingResult(
    agent-service/tests/test_agent_runner.py:245:    return RecommendationSpec(
    mall-service/src/mall_service/models.py:173:class RecommendationSearchSpec(BaseModel):
    agent-service/src/agent_service/api.py:151:            previous_goal_understanding=latest_goal_understanding(context),
    agent-service/src/agent_service/storage.py:339:            goal_understanding=goal_understanding,
    agent-service/src/agent_service/models.py:175:class GoalUnderstandingResult(BaseModel):
    agent-service/src/agent_service/models.py:202:class RecommendationSpec(BaseModel):
    agent-service/src/agent_service/goal_understanding.py:22:GOAL_UNDERSTANDING_PROMPT_PATH = (
    agent-service/src/agent_service/goal_understanding.py:91:            instructions = load_prompt(GOAL_UNDERSTANDING_PROMPT_PATH)
    agent-service/src/agent_service/goal_understanding.py:185:        return GoalUnderstandingResult(
    agent-service/src/agent_service/agent_runner.py:1289:        previous_goal_understanding=previous_goal_understanding,
    ✓ • 0ms

## Activity

    $ rg -n "recommendation_spec|goal_understanding" web -g '*.ts' -g '*.tsx'
    web/components/agent-chat.tsx:190:  generate_recommendation_spec: "生成推荐 SPEC",
    ✓ • 0ms

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/models.py
    @@ -164,2 +164,36 @@
     
    +RecommendationRequirementStatus = Literal[
    +    "collecting",
    +    "ready",
    +    "bypassed",
    +]
    +
    +
    +class RecommendationRequirementSlots(BaseModel):
    +    query: str | None = Field(default=None, max_length=500)
    +    category: str | None = Field(default=None, max_length=100)
    +    min_price_cents: int | None = Field(default=None, ge=0)
    +    max_price_cents: int | None = Field(default=None, ge=0)
    +    required_tags: list[str] = Field(default_factory=list)
    +    excluded_tags: list[str] = Field(default_factory=list)
    +    scenario: Literal[
    +        "general",
    +        "self",
    +        "gift",
    +        "replenishment",
    +    ] | None = None
    +    usage: str | None = Field(default=None, max_length=500)
    +    recipient: str | None = Field(default=None, max_length=200)
    +
    +
    +class RecommendationRequirementState(BaseModel):
    +    status: RecommendationRequirementStatus
    +    slots: RecommendationRequirementSlots = Field(
    +        default_factory=RecommendationRequirementSlots
    +    )
    +    next_question: str | None = Field(default=None, max_length=2_000)
    +    declined_requirements: list[str] = Field(default_factory=list)
    +    collection_reason: str | None = Field(default=None, max_length=2_000)
    +
    +
     class GoalUnderstandingDraft(BaseModel):
    @@ -172,2 +206,3 @@
         clarification_question: str | None = Field(default=None, max_length=1_000)
    +    recommendation_requirements: RecommendationRequirementState | None = None
     
    @@ -185,2 +220,3 @@
         pending_intent_question: str | None = Field(default=None, max_length=1_000)
    +    recommendation_requirements: RecommendationRequirementState | None = None
     
    @@ -211,2 +247,3 @@
         search_queries: list[str] = Field(min_length=1, max_length=6)
    +    recall_mode: Literal["targeted", "broad"] = "targeted"
         scenario: Literal[

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/goal_understanding.py
    @@ -195,2 +195,3 @@
                 pending_intent_question=pending_question,
    +            recommendation_requirements=draft.recommendation_requirements,
             )

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/prompts/goal_understanding.md
    @@ -65,2 +65,41 @@
     
    +## 推荐需求收集
    +
    +当 `primary_intent` 为 `product_recommendation` 时，你还要维护
    +`recommendation_requirements`。这是跨轮累计的推荐需求，不是当前消息槽位的副本。
    +
    +- 读取 `previous_goal.recommendation_requirements`，合并用户本轮表达和最近对话。
    +- 用户补充条件时保留已有条件；用户修改条件时以最新表达为准；用户开始明显不同的
    +  推荐任务时，可以清空不再适用的旧需求。
    +- 用户本轮一次提供多个条件时全部保存，不要为了分步询问而丢弃其中任何一项。
    +- 用户拒绝、取消或修改某个条件时，同步更新累计需求和
    +  `declined_requirements`。
    +- 不要编造用户没有说过、也没有在历史上下文中明确保留的需求。
    +
    +`status` 只能取：
    +
    +- `collecting`：还需要向用户了解需求。必须自主生成一个 `next_question`，并结束
    +  本轮推荐业务编排。
    +- `ready`：根据当前累计需求和上下文，已经有足够信息进入推荐。
    +- `bypassed`：用户明确表示不要收集需求，例如“你别管那么多，直接推荐”“不用问了”
    +  或“随便推荐”。本轮直接进入推荐，不得二次确认。
    +
    +询问方式：
    +
    +- 每轮最多询问一个需求点，不能一次抛出问卷或多个并列问题。
    +- 具体问什么、先问什么、如何措辞完全由你根据上下文决定，不要套用固定顺序或固定
    +  模板。
    +- 优先询问最可能实质影响召回、筛选或排序的信息。
    +- 不要机械追求填满所有槽位；信息已经足够时及时设为 `ready`。
    +- 已经回答、明确拒绝或不再需要的信息不要重复询问。
    +- “预算不限”“价格你看着办”“不关心材质”等通常只表示跳过当前相关信息，不等同于
    +  跳过整个需求收集；如果用户同时表达“直接推荐”，才使用 `bypassed`。
    +- `next_question` 必须只包含一个用户需要回答的需求点。`ready` 或 `bypassed` 时
    +  必须为 `null`。
    +
    +`collection_reason` 用一句简洁中文说明你为什么继续询问、直接推荐或整体跳过，便于
    +诊断。`declined_requirements` 使用简短自然语言记录用户明确不希望继续了解的条件。
    +
    +非商品推荐意图不使用需求收集，输出 `"recommendation_requirements": null`。
    +
     ## 置信度与澄清
    @@ -95,3 +134,20 @@
       "requires_clarification": false,
    -  "clarification_question": null
    +  "clarification_question": null,
    +  "recommendation_requirements": {
    +    "status": "collecting",
    +    "slots": {
    +      "query": "通勤",
    +      "category": null,
    +      "min_price_cents": null,
    +      "max_price_cents": 30000,
    +      "required_tags": [],
    +      "excluded_tags": [],
    +      "scenario": "self",
    +      "usage": "通勤",
    +      "recipient": null
    +    },
    +    "next_question": "除了通勤使用之外，你最希望这个商品解决什么问题？",
    +    "declined_requirements": [],
    +    "collection_reason": "已有用途和预算，但还缺少能影响选品的关键使用需求"
    +  }
     }

## Activity

    $ sed -n '20,90p' agent-service/prompts/shopping_agent.md && sed -n '112,132p' agent-service/prompts/shopping_agent.md
    - 当前对话存在上一轮保存的 Plan State 时，先根据新消息判断继续、修订、完成还是替换它。历史状态不是必须执行的命令。
    - 完成计划后，用 `update_plan` 把计划总体状态和步骤状态更新为你判断的结果。
    
    ## Goal Understanding
    
    每一条用户消息都必须先调用独立的 `understand_goal` Action。
    
    - 不要在自身推理中重新做意图分类或需求槽位提取。
    - 只能根据 Action 返回的 `goal_understanding` 路由业务工具。
    - 当前只支持 `product_recommendation`、`order_query`、`after_sales` 和 `unknown`。
    - `intents` 保持用户表达顺序，但本轮只处理 `primary_intent`，也就是第一个意图。
    - 如果 `pending_intents` 非空，在完成第一个意图后使用 `pending_intent_question`
      询问用户是否继续处理后续意图，不要在同一轮自动处理第二个意图。
    - 如果 `requires_clarification = true`，只询问 `clarification_question`，不要调用业务工具。
    - 如果 Action 返回 unavailable，停止本轮业务编排并请用户稍后重试，不要自行猜测。
    
    按 `primary_intent` 路由：
    
    - `product_recommendation`：依次调用 `collect_recommendation_context`、
      `generate_recommendation_spec`、`search_organic_candidates`、
      `search_ad_candidates` 和 `recommend_products`。
    - `order_query`：按已有 `order_id` 调用 `get_order`；没有订单 ID 时读取订单列表后选择或询问。
    - `after_sales`：可以查询订单和商品事实，但不得声称已经完成退款、退货或换货；当前只做信息收集和下一步引导。
    - `unknown`：普通回答或提出一个澄清问题，不调用推荐、订单或售后业务工具。
    
    ## 推荐主流程
    
    当 `primary_intent = product_recommendation` 时：
    
    1. 调用 `collect_recommendation_context` 收集画像、购物车、浏览、订单和商品目录。
    2. 调用 `generate_recommendation_spec`，由独立 Prompt 和模型生成推荐 SPEC。
    3. 分别调用 `search_organic_candidates` 和 `search_ad_candidates`。两者都只使用
       完整 SPEC，可以放在同一轮并行调用。相关 Action 会把整个 SPEC 传给
       `mall-service`，由 `mall-service` 转换为 ES 查询并返回检索结果。
    4. 调用无参数工具 `recommend_products`，只读取两路搜索 Action 的缓存候选，
       完成合并、评分和阈值分路。
    
    主 Agent 不自行编写搜索词、不自行判断行为记录权重、不直接调用商城搜索接口，
    也不要重复解释用户需求。两个搜索 Action 必须分别保留自己的候选和状态，不要在
    主 Agent 推理中混合实现。
    如果上下文收集或 SPEC 生成返回 unavailable，应告知用户暂时无法完成推荐并请其
    稍后重试，不要自行构造替代 SPEC。
    
    Recommendation SPEC 包含：
    
    - 用户显式硬约束；
    - 浏览、订单、购物车和画像形成的偏好推测；
    - 一组搜索查询变体；
    - 推断证据和置信度。
    
    SPEC 只用于指导召回，最终评分继续使用统一权重公式，避免同一行为被重复计权。
    
    `recommend_products` 会返回以下状态之一：
    
    - `accepted`：无需语义终排，工具已经按公式提交自然推荐 Top 2。
    - `requires_semantic_ranking`：存在超过自然推荐最低分的广告候选，必须调用独立终排工具。
    - `fallback`：语义终排暂时失败，工具已按公式排序提交保底结果。
    - `no_match`：没有合适商品。
    
    信息源缺失或 unavailable 时继续执行，不得因此中断推荐，也不得谎称用户没有记录。独立数据源工具仍可用于回答用户的具体追问或排查问题。
    
    ## 独立语义终排
    
    只有 `recommend_products` 返回 `requires_semantic_ranking` 时，才调用 `rerank_recommendations`。
    
    - 该工具拥有独立 Prompt，会综合公式分数、商品语义、场景、库存、价格和候选取舍。
    - 只有存在可信环境事实时，才通过 `environment_context` 传入；不要编造天气、节日、物流或销量。
    - 终排最多选择 2 个自然商品和 1 个广告商品，总计最多 3 个。
    - 存在自然商品时，广告不能排在第一位。
    - 广告完全不达标时不得补位，也不得为了凑数选择它。
    - 自然候选为空时，允许一个合格广告作为唯一结果。
    - 只有用户明确表达“确定购买”“下单”“买第一个”等购买决定时，才能调用 `create_order`。
    - “想买”“看看”“不错”“考虑一下”等表达不代表购买确认，不得创建订单。
    - 用户使用“第一个”“刚才第二个”等指代时，结合上一轮推荐商品的结构化列表和对话确定商品；无法确定时只追问一个关键问题。
    - 创建订单时只传商品 ID 和数量，不传价格。价格、库存和总额以商城订单服务返回结果为准。
    - 订单创建成功后，采用订单服务返回的状态、总额和预览链接，引导用户前往订单预览页。
    - Agent 不得代替用户支付，也不要调用不存在的支付工具。支付只能由用户在订单预览页手动完成。
    - 购买流程是 Plan 的一部分；是否新增、切换、完成购买步骤由你自行更新 `update_plan`。
    
    ## 多轮对话
    
    - 使用已有对话理解“第一个”“这个”“更适合送礼吗”等指代。
    - 用户修改预算或场景时，以最新需求重新查询。
    - 信息不足且会影响推荐质量时，只追问一个最关键的问题，例如预算、使用场景或收礼对象。
    - 如果用户已经给出足够信息，直接推荐，不要重复询问。
    
    ## 回答风格
    
    - 使用自然、简洁的中文。
    - 先给结论，再给推荐理由。
    - 避免夸张营销语，不使用“绝对最好”“百分百适合”等无法证明的表述。
    - 不虚构折扣、销量、物流、优惠券、评分或品牌合作信息。
    ✓ • 0ms

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/prompts/shopping_agent.md
    @@ -35,2 +35,18 @@
     
    +## 推荐需求收集
    +
    +每次 `understand_goal` 返回 `recommendation_requirements` 后，严格按模型给出的状态
    +推进，不自行选择下一项需求，也不套用固定问题模板。
    +
    +- `status = collecting`：只向用户输出 `next_question` 这一项需求，并结束本轮。
    +  必须原样表达该问题，不得自行追加第二个问题，也不得调用
    +  `collect_recommendation_context`、`generate_recommendation_spec`、搜索或推荐工具。
    +- `status = ready`：需求已经足够。不要再复述或确认已收集条件，直接进入推荐主流程。
    +- `status = bypassed`：用户要求跳过需求收集。不要再询问或确认，直接使用当前已有
    +  需求、历史需求、画像和行为信息推荐。
    +
    +`recommendation_requirements.slots` 是累计需求。进入推荐后只能把其中用户明确提供的
    +内容作为硬约束；`declined_requirements` 表示用户不想继续确认的条件，不得擅自转成
    +硬约束。
    +
     按 `primary_intent` 路由：
    @@ -48,8 +64,9 @@
     
    -1. 调用 `collect_recommendation_context` 收集画像、购物车、浏览、订单和商品目录。
    -2. 调用 `generate_recommendation_spec`，由独立 Prompt 和模型生成推荐 SPEC。
    -3. 分别调用 `search_organic_candidates` 和 `search_ad_candidates`。两者都只使用
    +1. 先检查 `recommendation_requirements.status`。只有 `ready` 或 `bypassed` 才能继续。
    +2. 调用 `collect_recommendation_context` 收集画像、购物车、浏览、订单和商品目录。
    +3. 调用 `generate_recommendation_spec`，由独立 Prompt 和模型生成推荐 SPEC。
    +4. 分别调用 `search_organic_candidates` 和 `search_ad_candidates`。两者都只使用
        完整 SPEC，可以放在同一轮并行调用。相关 Action 会把整个 SPEC 传给
        `mall-service`，由 `mall-service` 转换为 ES 查询并返回检索结果。
    -4. 调用无参数工具 `recommend_products`，只读取两路搜索 Action 的缓存候选，
    +5. 调用无参数工具 `recommend_products`，只读取两路搜索 Action 的缓存候选，
        完成合并、评分和阈值分路。
    @@ -123,3 +140,6 @@
     - 用户修改预算或场景时，以最新需求重新查询。
    -- 信息不足且会影响推荐质量时，只追问一个最关键的问题，例如预算、使用场景或收礼对象。
    +- 用户修改预算、场景或其他已收集条件时，更新累计需求后重新推荐，不要重走已经完成
    +  的问题。
    +- 是否继续询问、询问什么以及何时停止由 Goal Understanding 返回的
    +  `recommendation_requirements` 决定。
     - 如果用户已经给出足够信息，直接推荐，不要重复询问。

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/prompts/recommendation_spec.md
    @@ -11,2 +11,4 @@
     - `goal`：Goal Understanding 结果。
    +- `goal.recommendation_requirements`：模型跨轮维护的累计推荐需求，包含用户显式
    +  条件、是否已足够推荐、用户跳过收集的状态和已被拒绝的需求。
     - `agent_profile`：Agent 维护的长期偏好。
    @@ -27,2 +29,5 @@
     7. 不要把弱推断写成硬约束。
    +8. 用户显式需求以 `goal.recommendation_requirements.slots` 为准；不要用历史行为
    +   覆盖或补全其中用户已经明确修改的条件。
    +9. 用户拒绝或跳过确认的条件不能擅自变成硬约束。
     
    @@ -40,2 +45,13 @@
     
    +## 召回模式
    +
    +`recall_mode` 取 `targeted` 或 `broad`：
    +
    +- `targeted`：有明确商品目标或关键词时使用，查询词参与检索命中。
    +- `broad`：用户明确跳过了需求收集且没有足够商品目标时使用，允许只依靠画像、
    +  历史行为和硬过滤条件进行宽泛召回。
    +
    +`broad` 模式仍必须提供 1～6 个有诊断价值的搜索词，但搜索服务不会要求关键词命中。
    +不得因为这个模式编造用户偏好。
    +
     ## 搜索词
    @@ -83,2 +99,3 @@
       ],
    +  "recall_mode": "targeted",
       "scenario": "self",

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/recommendation_spec.py
    @@ -97,3 +97,7 @@
     ) -> RecommendationSpec:
    -    slots = goal.slots
    +    slots = (
    +        goal.recommendation_requirements.slots.model_dump(mode="json")
    +        if goal.recommendation_requirements is not None
    +        else goal.slots
    +    )
         hard = spec.hard_constraints
    @@ -124,3 +128,3 @@
         scenario = slots.get("scenario")
    -    if scenario not in {"general", "self", "gift", "replenishment"}:
    +    if scenario not in {"general", "self", "gift", "replenishment", None}:
             scenario = spec.scenario
    @@ -139,3 +143,3 @@
                 "search_queries": queries,
    -            "scenario": scenario,
    +            "scenario": scenario or spec.scenario,
                 "usage": (

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/agent_runner.py
    @@ -270,3 +270,7 @@
     ) -> RecommendationDemand:
    -    slots = goal.slots
    +    slots = (
    +        goal.recommendation_requirements.slots.model_dump(mode="json")
    +        if goal.recommendation_requirements is not None
    +        else goal.slots
    +    )
         hard = spec.hard_constraints if spec is not None else None

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/agent_runner.py
    @@ -266,2 +266,12 @@
     
    +def recommendation_requirements_need_input(
    +    goal: GoalUnderstandingResult,
    +) -> bool:
    +    requirements = goal.recommendation_requirements
    +    return (
    +        requirements is not None
    +        and requirements.status == "collecting"
    +    )
    +
    +
     def recommendation_demand_from_goal(
    @@ -775,2 +785,6 @@
                 return rejected("当前 primary_intent 不是商品推荐")
    +        if recommendation_requirements_need_input(goal):
    +            return rejected(
    +                "推荐需求仍在收集，只能先向用户输出模型生成的 next_question"
    +            )
             if context.recommendation_context is not None:
    @@ -887,2 +901,6 @@
                 return rejected("当前 primary_intent 不是商品推荐")
    +        if recommendation_requirements_need_input(goal):
    +            return rejected(
    +                "推荐需求仍在收集，请先完成模型生成的需求问题"
    +            )
             snapshot = context.recommendation_context
    @@ -1047,2 +1065,4 @@
                 return rejected("当前 primary_intent 不是商品推荐")
    +        if recommendation_requirements_need_input(goal):
    +            return rejected("推荐需求仍在收集，暂不能提交推荐")
             snapshot = context.recommendation_context

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/mall-service/src/mall_service/models.py
    @@ -182,2 +182,3 @@
         search_queries: list[str] = Field(min_length=1, max_length=6)
    +    recall_mode: Literal["targeted", "broad"] = "targeted"
         scenario: Literal[

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/mall-service/src/mall_service/search.py
    @@ -93,3 +93,3 @@
         }
    -    if text_should:
    +    if text_should and spec.recall_mode == "targeted":
             bool_query["must"] = [
    @@ -102,2 +102,4 @@
             ]
    +    elif text_should:
    +        preference_should.extend(text_should)
         if preference_should:
    @@ -205,3 +207,3 @@
         ]
    -    if text_queries:
    +    if text_queries and spec.recall_mode == "targeted":
             candidates = [

## Assistant

核心代码路径已经接入：`collecting` 时推荐工具会被拒绝，SPEC 和评分改为读取模型维护的累计需求；商城搜索也支持模型选择的宽泛召回。接下来补测试，重点验证模型生成的问题原样输出、收集轮不触发推荐工具，以及状态可跨轮持久化。

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/tests/test_agent_runner.py
    @@ -28,2 +28,4 @@
         RecommendationDemand,
    +    RecommendationRequirementSlots,
    +    RecommendationRequirementState,
         RecommendationSpec,
    @@ -219,4 +221,11 @@
         intents: list[str] | None = None,
    +    requirement_status: str = "ready",
    +    next_question: str | None = None,
     ) -> GoalUnderstandingResult:
         ordered_intents = intents or ["product_recommendation"]
    +    slots = {
    +        "query": query,
    +        "max_price_cents": 30000,
    +        "scenario": "self",
    +    }
         return GoalUnderstandingResult(
    @@ -227,7 +236,13 @@
             confidence=0.95,
    -        slots={
    -            "query": query,
    -            "max_price_cents": 30000,
    -            "scenario": "self",
    -        },
    +        slots=slots,
    +        recommendation_requirements=RecommendationRequirementState(
    +            status=requirement_status,
    +            slots=RecommendationRequirementSlots(
    +                query=query,
    +                max_price_cents=30000,
    +                scenario="self",
    +            ),
    +            next_question=next_question,
    +            collection_reason="模型判断当前推荐需求状态",
    +        ),
             pending_intent_question=(
    @@ -525,2 +540,22 @@
     
    +def test_collecting_requirements_block_recommendation_steps() -> None:
    +    context = ShoppingAgentContext(mall=mall_client())
    +    context.goal_understanding = goal_understanding(
    +        requirement_status="collecting",
    +        next_question="你最在意这个商品的什么特点？",
    +    )
    +
    +    collected = json.loads(
    +        invoke_tool(context, "collect_recommendation_context", {})
    +    )
    +    generated = json.loads(
    +        invoke_tool(context, "generate_recommendation_spec", {})
    +    )
    +
    +    assert collected["status"] == "rejected"
    +    assert "next_question" in collected["message"]
    +    assert generated["status"] == "rejected"
    +    assert context.recommendation_context is None
    +
    +
     def test_goal_understanding_agent_uses_its_own_prompt() -> None:
    @@ -542,2 +577,19 @@
                                 "clarification_question": None,
    +                            "recommendation_requirements": {
    +                                "status": "collecting",
    +                                "slots": {
    +                                    "query": "通勤包",
    +                                    "category": "箱包",
    +                                    "min_price_cents": None,
    +                                    "max_price_cents": None,
    +                                    "required_tags": [],
    +                                    "excluded_tags": [],
    +                                    "scenario": None,
    +                                    "usage": "通勤",
    +                                    "recipient": None,
    +                                },
    +                                "next_question": "你希望大概控制在什么价位？",
    +                                "declined_requirements": [],
    +                                "collection_reason": "还需要价格信息帮助筛选",
    +                            },
                             },
    @@ -571,2 +623,7 @@
         assert result.pending_intents == ["order_query"]
    +    assert result.recommendation_requirements is not None
    +    assert result.recommendation_requirements.status == "collecting"
    +    assert result.recommendation_requirements.next_question == (
    +        "你希望大概控制在什么价位？"
    +    )
         assert model.first_call is not None

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/tests/test_agent_runner.py
    @@ -1052,2 +1052,83 @@
     
    +def test_model_generated_requirement_question_ends_turn_without_recommendation() -> None:
    +    question = "你更希望它适合通勤时装电脑，还是日常随身使用？"
    +    model = ScriptedModel(
    +        [
    +            [
    +                function_call(
    +                    "understand_goal",
    +                    {},
    +                    call_id="call-goal",
    +                )
    +            ],
    +            [
    +                assistant_message(
    +                    json.dumps(
    +                        {
    +                            "intents": ["product_recommendation"],
    +                            "goal": "推荐一个通勤包",
    +                            "confidence": 0.96,
    +                            "slots": {"query": "通勤包"},
    +                            "missing_slots": [],
    +                            "requires_clarification": False,
    +                            "clarification_question": None,
    +                            "recommendation_requirements": {
    +                                "status": "collecting",
    +                                "slots": {
    +                                    "query": "通勤包",
    +                                    "category": "箱包",
    +                                    "min_price_cents": None,
    +                                    "max_price_cents": None,
    +                                    "required_tags": [],
    +                                    "excluded_tags": [],
    +                                    "scenario": None,
    +                                    "usage": "通勤",
    +                                    "recipient": None,
    +                                },
    +                                "next_question": question,
    +                                "declined_requirements": [],
    +                                "collection_reason": "还需要明确具体使用方式",
    +                            },
    +                        },
    +                        ensure_ascii=False,
    +                    )
    +                )
    +            ],
    +            [assistant_message(question)],
    +        ]
    +    )
    +
    +    async def collect_events() -> list[dict[str, object]]:
    +        return [
    +            event
    +            async for event in stream_agent_reply(
    +                [ConversationMessage(role="user", content="推荐个通勤包")],
    +                llm_config(),
    +                mall_client(),
    +                model_override=model,
    +            )
    +        ]
    +
    +    events = asyncio.run(collect_events())
    +
    +    started_tools = [
    +        event["tool"]
    +        for event in events
    +        if event["type"] == "tool_started"
    +    ]
    +    text = "".join(
    +        str(event["content"])
    +        for event in events
    +        if event["type"] == "delta"
    +    )
    +    done = next(event for event in events if event["type"] == "done")
    +
    +    assert started_tools == ["understand_goal"]
    +    assert text == question
    +    assert done["recommendations"] == []
    +    assert done["goal_understanding"]["recommendation_requirements"][
    +        "status"
    +    ] == "collecting"
    +
    +
     def test_react_loop_loads_sources_and_streams_only_final_selection() -> None:

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/tests/test_agent_api.py
    @@ -116,2 +116,19 @@
         "pending_intent_question": "是否继续处理订单查询？",
    +    "recommendation_requirements": {
    +        "status": "ready",
    +        "slots": {
    +            "query": "通勤",
    +            "category": None,
    +            "min_price_cents": None,
    +            "max_price_cents": 30000,
    +            "required_tags": [],
    +            "excluded_tags": [],
    +            "scenario": "self",
    +            "usage": "通勤",
    +            "recipient": None,
    +        },
    +        "next_question": None,
    +        "declined_requirements": [],
    +        "collection_reason": "已有明确商品目标和预算，可以直接推荐",
    +    },
     }
    @@ -277,2 +294,7 @@
         ]
    +    assert (
    +        detail.messages[1]
    +        .goal_understanding.recommendation_requirements.status
    +        == "ready"
    +    )
         assert detail.messages[1].recommendation_spec is not None
    @@ -444,2 +466,7 @@
         ]
    +    assert (
    +        captured["previous_goal_understanding"]
    +        .recommendation_requirements.slots.max_price_cents
    +        == 30000
    +    )
     

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/mall-service/tests/test_mall_api.py
    @@ -197,2 +197,38 @@
     
    +def test_broad_spec_search_does_not_require_keyword_match() -> None:
    +    spec = {
    +        "goal_summary": "用户跳过需求收集，按历史偏好宽泛推荐",
    +        "hard_constraints": {
    +            "category": None,
    +            "min_price_cents": None,
    +            "max_price_cents": 10000,
    +            "required_tags": [],
    +            "excluded_tags": [],
    +        },
    +        "preferred_categories": ["箱包"],
    +        "preferred_tags": ["通勤"],
    +        "weak_categories": [],
    +        "negative_tags": [],
    +        "search_queries": ["通勤"],
    +        "recall_mode": "broad",
    +        "scenario": "self",
    +        "usage": None,
    +        "recipient": None,
    +        "source_evidence": [],
    +        "confidence": 0.7,
    +        "missing_information": [],
    +    }
    +
    +    response = client.post(
    +        "/api/search/organic",
    +        json={"spec": spec, "limit": 10},
    +    )
    +
    +    assert response.status_code == 200
    +    products = response.json()["items"]
    +    assert len(products) > 1
    +    assert len({product["category"] for product in products}) > 1
    +    assert all(product["price_cents"] <= 10000 for product in products)
    +
    +
     def test_create_order_uses_catalog_snapshot_and_is_idempotent() -> None:

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/tests/test_mall_contract.py
    @@ -85 +85,24 @@
         assert all(item.source == "advertisement" for item in ads)
    +
    +
    +def test_agent_spec_supports_model_selected_broad_recall() -> None:
    +    client = mall_client()
    +    spec = RecommendationSpec(
    +        goal_summary="用户跳过需求收集，按已有信息宽泛推荐",
    +        hard_constraints=RecommendationSpecHardConstraints(
    +            max_price_cents=10000,
    +        ),
    +        preferred_categories=["箱包"],
    +        preferred_tags=["通勤"],
    +        search_queries=["通勤"],
    +        recall_mode="broad",
    +        confidence=0.7,
    +    )
    +
    +    products = asyncio.run(
    +        client.search_organic_with_spec(spec, limit=10)
    +    )
    +
    +    assert len(products) > 1
    +    assert len({product.category for product in products}) > 1
    +    assert all(product.price_cents <= 10000 for product in products)

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/tests/test_agent_runner.py
    @@ -634,2 +634,65 @@
     
    +def test_goal_understanding_can_bypass_requirement_collection() -> None:
    +    model = ScriptedModel(
    +        [
    +            [
    +                assistant_message(
    +                    json.dumps(
    +                        {
    +                            "intents": ["product_recommendation"],
    +                            "goal": "直接推荐商品",
    +                            "confidence": 0.97,
    +                            "slots": {},
    +                            "missing_slots": [],
    +                            "requires_clarification": False,
    +                            "clarification_question": None,
    +                            "recommendation_requirements": {
    +                                "status": "bypassed",
    +                                "slots": {
    +                                    "query": None,
    +                                    "category": None,
    +                                    "min_price_cents": None,
    +                                    "max_price_cents": None,
    +                                    "required_tags": [],
    +                                    "excluded_tags": [],
    +                                    "scenario": None,
    +                                    "usage": None,
    +                                    "recipient": None,
    +                                },
    +                                "next_question": None,
    +                                "declined_requirements": ["不回答推荐需求问题"],
    +                                "collection_reason": "用户明确要求直接推荐",
    +                            },
    +                        },
    +                        ensure_ascii=False,
    +                    )
    +                )
    +            ]
    +        ]
    +    )
    +    understander = AgentGoalUnderstander(
    +        config=llm_config(),
    +        model=model,
    +    )
    +
    +    result = asyncio.run(
    +        understander.understand(
    +            current_message="你别管那么多，直接推荐",
    +            recent_messages=[
    +                ConversationMessage(
    +                    role="user",
    +                    content="你别管那么多，直接推荐",
    +                )
    +            ],
    +            previous_goal=None,
    +            previous_recommendations=[],
    +            previous_orders=[],
    +        )
    +    )
    +
    +    assert result.recommendation_requirements is not None
    +    assert result.recommendation_requirements.status == "bypassed"
    +    assert result.recommendation_requirements.next_question is None
    +
    +
     def test_collect_context_and_generate_recommendation_spec_are_separate_actions(

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/tests/test_agent_runner.py
    @@ -1226,2 +1226,19 @@
                                 "clarification_question": None,
    +                            "recommendation_requirements": {
    +                                "status": "ready",
    +                                "slots": {
    +                                    "query": "通勤",
    +                                    "category": None,
    +                                    "min_price_cents": None,
    +                                    "max_price_cents": 30000,
    +                                    "required_tags": [],
    +                                    "excluded_tags": [],
    +                                    "scenario": "self",
    +                                    "usage": "通勤",
    +                                    "recipient": None,
    +                                },
    +                                "next_question": None,
    +                                "declined_requirements": [],
    +                                "collection_reason": "商品目标和预算已足够",
    +                            },
                             },
    @@ -1376,2 +1393,5 @@
         )
    +    assert "status = collecting" in (
    +        model.first_call.system_instructions or ""
    +    )
     

## Activity

    $ rg -n 'recommendation_requirements|status = collecting' agent-service/tests/test_agent_runner.py && sed -n '530,700p' agent-service/tests/test_agent_runner.py && sed -n '1120,1260p' agent-service/tests/test_agent_runner.py
    238:        recommendation_requirements=RecommendationRequirementState(
    578:                            "recommendation_requirements": {
    624:    assert result.recommendation_requirements is not None
    625:    assert result.recommendation_requirements.status == "collecting"
    626:    assert result.recommendation_requirements.next_question == (
    649:                            "recommendation_requirements": {
    693:    assert result.recommendation_requirements is not None
    694:    assert result.recommendation_requirements.status == "bypassed"
    695:    assert result.recommendation_requirements.next_question is None
    1138:                            "recommendation_requirements": {
    1192:    assert done["goal_understanding"]["recommendation_requirements"][
    1227:                            "recommendation_requirements": {
    1394:    assert "status = collecting" in (
            invoke_tool(context, "understand_goal", {})
        )
    
        assert result["status"] == "understood"
        assert result["goal_understanding"]["primary_intent"] == (
            "product_recommendation"
        )
        assert result["goal_understanding"]["pending_intents"] == ["order_query"]
        assert context.goal_understanding is not None
    
    
    def test_collecting_requirements_block_recommendation_steps() -> None:
        context = ShoppingAgentContext(mall=mall_client())
        context.goal_understanding = goal_understanding(
            requirement_status="collecting",
            next_question="你最在意这个商品的什么特点？",
        )
    
        collected = json.loads(
            invoke_tool(context, "collect_recommendation_context", {})
        )
        generated = json.loads(
            invoke_tool(context, "generate_recommendation_spec", {})
        )
    
        assert collected["status"] == "rejected"
        assert "next_question" in collected["message"]
        assert generated["status"] == "rejected"
        assert context.recommendation_context is None
    
    
    def test_goal_understanding_agent_uses_its_own_prompt() -> None:
        model = ScriptedModel(
            [
                [
                    assistant_message(
                        json.dumps(
                            {
                                "intents": [
                                    "product_recommendation",
                                    "order_query",
                                ],
                                "goal": "推荐通勤包并查询订单",
                                "confidence": 0.96,
                                "slots": {"query": "通勤"},
                                "missing_slots": [],
                                "requires_clarification": False,
                                "clarification_question": None,
                                "recommendation_requirements": {
                                    "status": "collecting",
                                    "slots": {
                                        "query": "通勤包",
                                        "category": "箱包",
                                        "min_price_cents": None,
                                        "max_price_cents": None,
                                        "required_tags": [],
                                        "excluded_tags": [],
                                        "scenario": None,
                                        "usage": "通勤",
                                        "recipient": None,
                                    },
                                    "next_question": "你希望大概控制在什么价位？",
                                    "declined_requirements": [],
                                    "collection_reason": "还需要价格信息帮助筛选",
                                },
                            },
                            ensure_ascii=False,
                        )
                    )
                ]
            ]
        )
        understander = AgentGoalUnderstander(
            config=llm_config(),
            model=model,
        )
    
        result = asyncio.run(
            understander.understand(
                current_message="推荐一个通勤包，然后查订单",
                recent_messages=[
                    ConversationMessage(
                        role="user",
                        content="推荐一个通勤包，然后查订单",
                    )
                ],
                previous_goal=None,
                previous_recommendations=[],
                previous_orders=[],
            )
        )
    
        assert result.primary_intent == "product_recommendation"
        assert result.pending_intents == ["order_query"]
        assert result.recommendation_requirements is not None
        assert result.recommendation_requirements.status == "collecting"
        assert result.recommendation_requirements.next_question == (
            "你希望大概控制在什么价位？"
        )
        assert model.first_call is not None
        assert "Goal Understanding" in (
            model.first_call.system_instructions or ""
        )
    
    
    def test_goal_understanding_can_bypass_requirement_collection() -> None:
        model = ScriptedModel(
            [
                [
                    assistant_message(
                        json.dumps(
                            {
                                "intents": ["product_recommendation"],
                                "goal": "直接推荐商品",
                                "confidence": 0.97,
                                "slots": {},
                                "missing_slots": [],
                                "requires_clarification": False,
                                "clarification_question": None,
                                "recommendation_requirements": {
                                    "status": "bypassed",
                                    "slots": {
                                        "query": None,
                                        "category": None,
                                        "min_price_cents": None,
                                        "max_price_cents": None,
                                        "required_tags": [],
                                        "excluded_tags": [],
                                        "scenario": None,
                                        "usage": None,
                                        "recipient": None,
                                    },
                                    "next_question": None,
                                    "declined_requirements": ["不回答推荐需求问题"],
                                    "collection_reason": "用户明确要求直接推荐",
                                },
                            },
                            ensure_ascii=False,
                        )
                    )
                ]
            ]
        )
        understander = AgentGoalUnderstander(
            config=llm_config(),
            model=model,
        )
    
        result = asyncio.run(
            understander.understand(
                current_message="你别管那么多，直接推荐",
                recent_messages=[
                    ConversationMessage(
                        role="user",
                        content="你别管那么多，直接推荐",
                    )
                ],
                previous_goal=None,
                previous_recommendations=[],
                previous_orders=[],
            )
        )
    
        assert result.recommendation_requirements is not None
        assert result.recommendation_requirements.status == "bypassed"
        assert result.recommendation_requirements.next_question is None
    
    
    def test_collect_context_and_generate_recommendation_spec_are_separate_actions(
        caplog,
    ) -> None:
                [
                    function_call(
                        "understand_goal",
                        {},
                        call_id="call-goal",
                    )
                ],
                [
                    assistant_message(
                        json.dumps(
                            {
                                "intents": ["product_recommendation"],
                                "goal": "推荐一个通勤包",
                                "confidence": 0.96,
                                "slots": {"query": "通勤包"},
                                "missing_slots": [],
                                "requires_clarification": False,
                                "clarification_question": None,
                                "recommendation_requirements": {
                                    "status": "collecting",
                                    "slots": {
                                        "query": "通勤包",
                                        "category": "箱包",
                                        "min_price_cents": None,
                                        "max_price_cents": None,
                                        "required_tags": [],
                                        "excluded_tags": [],
                                        "scenario": None,
                                        "usage": "通勤",
                                        "recipient": None,
                                    },
                                    "next_question": question,
                                    "declined_requirements": [],
                                    "collection_reason": "还需要明确具体使用方式",
                                },
                            },
                            ensure_ascii=False,
                        )
                    )
                ],
                [assistant_message(question)],
            ]
        )
    
        async def collect_events() -> list[dict[str, object]]:
            return [
                event
                async for event in stream_agent_reply(
                    [ConversationMessage(role="user", content="推荐个通勤包")],
                    llm_config(),
                    mall_client(),
                    model_override=model,
                )
            ]
    
        events = asyncio.run(collect_events())
    
        started_tools = [
            event["tool"]
            for event in events
            if event["type"] == "tool_started"
        ]
        text = "".join(
            str(event["content"])
            for event in events
            if event["type"] == "delta"
        )
        done = next(event for event in events if event["type"] == "done")
    
        assert started_tools == ["understand_goal"]
        assert text == question
        assert done["recommendations"] == []
        assert done["goal_understanding"]["recommendation_requirements"][
            "status"
        ] == "collecting"
    
    
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
                        "understand_goal",
                        {},
                        call_id="call-goal",
                    ),
                ],
                [
                    assistant_message(
                        json.dumps(
                            {
                                "intents": ["product_recommendation"],
                                "goal": "推荐预算 300 元以内的通勤商品",
                                "confidence": 0.96,
                                "slots": {
                                    "query": "通勤",
                                    "max_price_cents": 30000,
                                    "scenario": "self",
                                },
                                "missing_slots": [],
                                "requires_clarification": False,
                                "clarification_question": None,
                                "recommendation_requirements": {
                                    "status": "ready",
                                    "slots": {
                                        "query": "通勤",
                                        "category": None,
                                        "min_price_cents": None,
                                        "max_price_cents": 30000,
                                        "required_tags": [],
                                        "excluded_tags": [],
                                        "scenario": "self",
                                        "usage": "通勤",
                                        "recipient": None,
                                    },
                                    "next_question": None,
                                    "declined_requirements": [],
                                    "collection_reason": "商品目标和预算已足够",
                                },
                            },
                            ensure_ascii=False,
                        )
                    )
                ],
                [
                    function_call(
                        "collect_recommendation_context",
                        {},
                        call_id="call-context",
                    )
                ],
                [
                    function_call(
                        "generate_recommendation_spec",
                        {},
                        call_id="call-spec",
    ✓ • 0ms

## Activity

    $ uv run pytest agent-service/tests/test_agent_runner.py agent-service/tests/test_agent_api.py agent-service/tests/test_mall_contract.py mall-service/tests/test_mall_api.py -q
    .........................................................                [100%]
    57 passed in 1.49s
    ✓ • 1.92s

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/models.py
    @@ -2,3 +2,3 @@
     
    -from pydantic import BaseModel, Field, field_validator
    +from pydantic import BaseModel, Field, field_validator, model_validator
     
    @@ -197,2 +197,15 @@
     
    +    @model_validator(mode="after")
    +    def question_matches_status(self) -> "RecommendationRequirementState":
    +        if self.status == "collecting":
    +            if not self.next_question or not self.next_question.strip():
    +                raise ValueError(
    +                    "collecting recommendation requirements need a next question"
    +                )
    +        elif self.next_question is not None:
    +            raise ValueError(
    +                "ready or bypassed recommendation requirements cannot have a question"
    +            )
    +        return self
    +
     

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/README.md
    @@ -163,3 +163,4 @@
     - `understand_goal`：独立 Goal Understanding Action，使用单独 Prompt 和模型
    -  调用识别多意图、提取槽位，并确定本轮第一个待处理意图。
    +  调用识别多意图、提取槽位，并维护跨轮累计推荐需求。模型自主决定继续询问、
    +  直接推荐或跳过需求收集，每轮最多提出一个需求问题。
     - `collect_recommendation_context`：为 Recommendation SPEC 收集画像、购物车、
    @@ -190,2 +191,9 @@
     
    +推荐需求收集同样由 Goal Understanding 模型推进。模型输出
    +`recommendation_requirements`，其中 `status` 为 `collecting`、`ready` 或
    +`bypassed`。`collecting` 时模型生成当前唯一要问的 `next_question`，主 Agent
    +原样输出并结束本轮；`ready` 时直接进入推荐；用户说“别管那么多，直接推荐”等表达
    +时，模型输出 `bypassed`，本轮不得二次确认。代码不设定固定询问顺序，也不生成
    +固定问题模板，只校验状态结构、保存累计结果并阻止收集轮提前调用推荐工具。
    +
     多意图消息由 `understand_goal` 保留完整意图顺序，但每轮只处理第一个意图。如果
    @@ -208,2 +216,6 @@
     
    +用户整体跳过需求收集且没有明确商品目标时，SPEC 模型可以选择 `broad` 召回模式。
    +该模式仍应用用户明确给出的价格、品类和排除条件，但不强制关键词命中，以便利用画像
    +和历史行为完成宽泛推荐。
    +
     两个搜索 Action 都把完整 SPEC 发送给 `mall-service`。`mall-service` 目前不连接

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/RECOMMENDATION_E2E_TEST.md
    @@ -82,2 +82,45 @@
     
    +## 推荐需求收集测试
    +
    +新建对话并发送：
    +
    +```text
    +推荐一个通勤包。
    +```
    +
    +应观察到的行为：
    +
    +- `understand_goal` 返回 `recommendation_requirements.status = collecting`。
    +- Agent 只在回答中提出一个需求问题，问题内容和顺序由模型根据上下文决定，不要求
    +  固定询问预算或固定使用某种模板。
    +- 本轮不调用 `collect_recommendation_context`、`generate_recommendation_spec`、
    +  商品搜索、广告搜索或推荐工具。
    +- 下一次回答只补充当前问题对应的信息后，模型继续自主询问或判断信息足够并开始
    +  推荐，不得重复已经回答的问题。
    +
    +新建对话并发送：
    +
    +```text
    +你别管那么多，直接推荐。
    +```
    +
    +应观察到的行为：
    +
    +- `understand_goal` 返回
    +  `recommendation_requirements.status = bypassed`。
    +- Agent 不再询问需求，也不进行“确定要跳过吗”的二次确认。
    +- 本轮直接进入 SPEC、搜索和推荐；缺少明确商品目标时可以使用 `broad` 召回模式。
    +
    +在需求收集追问期间发送：
    +
    +```text
    +预算不限。
    +```
    +
    +应观察到的行为：
    +
    +- 只跳过与预算相关的需求，不代表整个收集流程都被跳过，除非用户同时明确要求直接
    +  推荐。
    +- 模型不得重复询问预算；可以继续询问其他项，也可以判断已有信息足够并开始推荐。
    +
     ## 历史记录检查
    @@ -142,2 +185,4 @@
     - [ ] 第三轮正确理解“刚才第二个”，并遵守护手霜排除条件。
    +- [ ] 推荐需求收集轮每轮最多提出一个问题，且不调用推荐业务工具。
    +- [ ] 用户明确要求直接推荐时，当轮跳过需求收集，不进行二次确认。
     - [ ] 每轮最终推荐不超过三个商品。

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/agent_runner.py
    @@ -292,3 +292,10 @@
         query = _optional_string(slots, "query")
    -    if query is None and goal.primary_intent == "product_recommendation":
    +    if (
    +        query is None
    +        and goal.primary_intent == "product_recommendation"
    +        and not (
    +            spec is not None
    +            and spec.recall_mode == "broad"
    +        )
    +    ):
             query = (

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/tests/test_agent_runner.py
    @@ -14,2 +14,3 @@
         normalize_openai_base_url,
    +    recommendation_demand_from_goal,
         stream_agent_reply,
    @@ -274,2 +275,16 @@
     
    +def test_broad_recall_does_not_promote_diagnostic_query_to_demand() -> None:
    +    goal = goal_understanding(
    +        requirement_status="bypassed",
    +        query="",
    +    )
    +    spec = recommendation_spec(queries=["通勤"]).model_copy(
    +        update={"recall_mode": "broad"}
    +    )
    +
    +    demand = recommendation_demand_from_goal(goal, spec)
    +
    +    assert demand.query == ""
    +
    +
     def scored_candidate(

## Activity

    $ uv run pytest -q
    ........................................................................ [ 78%]
    ....................                                                     [100%]
    92 passed in 1.43s
    ✓ • 1.78s

## Assistant

后端单元与集成测试已全部通过（92 项）。我再做一轮完整构建与差异检查，确认没有破坏前端、服务契约或提示词一致性。

## Activity

    $ git diff --check && git status --short
     M README.md
     M RECOMMENDATION_E2E_TEST.md
     M agent-service/prompts/goal_understanding.md
     M agent-service/prompts/recommendation_spec.md
     M agent-service/prompts/shopping_agent.md
     M agent-service/src/agent_service/agent_runner.py
     M agent-service/src/agent_service/goal_understanding.py
     M agent-service/src/agent_service/models.py
     M agent-service/src/agent_service/recommendation_spec.py
     M agent-service/tests/test_agent_api.py
     M agent-service/tests/test_agent_runner.py
     M agent-service/tests/test_mall_contract.py
     M mall-service/src/mall_service/models.py
     M mall-service/src/mall_service/search.py
     M mall-service/tests/test_mall_api.py
    ✓ • 0ms

## Activity

    $ sed -n '140,270p' agent-service/src/agent_service/models.py && sed -n '255,345p' agent-service/src/agent_service/agent_runner.py && sed -n '770,900p' agent-service/src/agent_service/agent_runner.py
        score: float = Field(ge=0, le=1)
        matched_signals: list[str] = Field(default_factory=list)
        ad: AdInfo | None = None
    
    
    class RecommendationDemand(BaseModel):
        query: str = Field(default="", max_length=500)
        category: str | None = Field(default=None, max_length=100)
        min_price_cents: int | None = Field(default=None, ge=0)
        max_price_cents: int | None = Field(default=None, ge=0)
        required_tags: list[str] = Field(default_factory=list)
        excluded_tags: list[str] = Field(default_factory=list)
        scenario: Literal[
            "general",
            "self",
            "gift",
            "replenishment",
        ] = "general"
        usage: str | None = Field(default=None, max_length=500)
        recipient: str | None = Field(default=None, max_length=200)
    
    
    IntentType = str
    
    
    RecommendationRequirementStatus = Literal[
        "collecting",
        "ready",
        "bypassed",
    ]
    
    
    class RecommendationRequirementSlots(BaseModel):
        query: str | None = Field(default=None, max_length=500)
        category: str | None = Field(default=None, max_length=100)
        min_price_cents: int | None = Field(default=None, ge=0)
        max_price_cents: int | None = Field(default=None, ge=0)
        required_tags: list[str] = Field(default_factory=list)
        excluded_tags: list[str] = Field(default_factory=list)
        scenario: Literal[
            "general",
            "self",
            "gift",
            "replenishment",
        ] | None = None
        usage: str | None = Field(default=None, max_length=500)
        recipient: str | None = Field(default=None, max_length=200)
    
    
    class RecommendationRequirementState(BaseModel):
        status: RecommendationRequirementStatus
        slots: RecommendationRequirementSlots = Field(
            default_factory=RecommendationRequirementSlots
        )
        next_question: str | None = Field(default=None, max_length=2_000)
        declined_requirements: list[str] = Field(default_factory=list)
        collection_reason: str | None = Field(default=None, max_length=2_000)
    
        @model_validator(mode="after")
        def question_matches_status(self) -> "RecommendationRequirementState":
            if self.status == "collecting":
                if not self.next_question or not self.next_question.strip():
                    raise ValueError(
                        "collecting recommendation requirements need a next question"
                    )
            elif self.next_question is not None:
                raise ValueError(
                    "ready or bypassed recommendation requirements cannot have a question"
                )
            return self
    
    
    class GoalUnderstandingDraft(BaseModel):
        intents: list[IntentType] = Field(min_length=1, max_length=5)
        goal: str = Field(min_length=1, max_length=2_000)
        confidence: float = Field(ge=0, le=1)
        slots: dict[str, object] = Field(default_factory=dict)
        missing_slots: list[str] = Field(default_factory=list)
        requires_clarification: bool = False
        clarification_question: str | None = Field(default=None, max_length=1_000)
        recommendation_requirements: RecommendationRequirementState | None = None
    
    
    class GoalUnderstandingResult(BaseModel):
        primary_intent: IntentType
        intents: list[IntentType] = Field(min_length=1, max_length=5)
        pending_intents: list[IntentType] = Field(default_factory=list)
        goal: str = Field(min_length=1, max_length=2_000)
        confidence: float = Field(ge=0, le=1)
        slots: dict[str, object] = Field(default_factory=dict)
        missing_slots: list[str] = Field(default_factory=list)
        requires_clarification: bool = False
        clarification_question: str | None = Field(default=None, max_length=1_000)
        pending_intent_question: str | None = Field(default=None, max_length=1_000)
        recommendation_requirements: RecommendationRequirementState | None = None
    
    
    class RecommendationSpecHardConstraints(BaseModel):
        category: str | None = Field(default=None, max_length=100)
        min_price_cents: int | None = Field(default=None, ge=0)
        max_price_cents: int | None = Field(default=None, ge=0)
        required_tags: list[str] = Field(default_factory=list)
        excluded_tags: list[str] = Field(default_factory=list)
    
    
    class RecommendationSpecEvidence(BaseModel):
        source: str = Field(min_length=1, max_length=100)
        observation: str = Field(min_length=1, max_length=500)
        influence: Literal["high", "medium", "low"]
    
    
    class RecommendationSpec(BaseModel):
        goal_summary: str = Field(min_length=1, max_length=1_000)
        hard_constraints: RecommendationSpecHardConstraints = Field(
            default_factory=RecommendationSpecHardConstraints
        )
        preferred_categories: list[str] = Field(default_factory=list)
        preferred_tags: list[str] = Field(default_factory=list)
        weak_categories: list[str] = Field(default_factory=list)
        negative_tags: list[str] = Field(default_factory=list)
        search_queries: list[str] = Field(min_length=1, max_length=6)
        recall_mode: Literal["targeted", "broad"] = "targeted"
        scenario: Literal[
            "general",
            "self",
            "gift",
            "replenishment",
        ] = "general"
        usage: str | None = Field(default=None, max_length=500)
        recipient: str | None = Field(default=None, max_length=200)
        source_evidence: list[RecommendationSpecEvidence] = Field(
    
    def _optional_int(slots: dict[str, object], key: str) -> int | None:
        value = slots.get(key)
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return max(0, value)
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return None
    
    
    def recommendation_requirements_need_input(
        goal: GoalUnderstandingResult,
    ) -> bool:
        requirements = goal.recommendation_requirements
        return (
            requirements is not None
            and requirements.status == "collecting"
        )
    
    
    def recommendation_demand_from_goal(
        goal: GoalUnderstandingResult,
        spec: RecommendationSpec | None = None,
    ) -> RecommendationDemand:
        slots = (
            goal.recommendation_requirements.slots.model_dump(mode="json")
            if goal.recommendation_requirements is not None
            else goal.slots
        )
        hard = spec.hard_constraints if spec is not None else None
        required_tags = slots.get("required_tags")
        excluded_tags = slots.get("excluded_tags")
        scenario = slots.get("scenario")
        if scenario not in {"general", "self", "gift", "replenishment"}:
            scenario = spec.scenario if spec is not None else "general"
        query = _optional_string(slots, "query")
        if (
            query is None
            and goal.primary_intent == "product_recommendation"
            and not (
                spec is not None
                and spec.recall_mode == "broad"
            )
        ):
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
            if recommendation_requirements_need_input(goal):
                return rejected(
                    "推荐需求仍在收集，只能先向用户输出模型生成的 next_question"
                )
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
    ✓ • 0ms

## Activity

    $ pnpm --dir web build
    
    > niub-shangcheng-web@0.1.0 build /Users/mindeng/workspace/niub-shangcheng/web
    > next build
    
       ▲ Next.js 15.5.28
    
       Creating an optimized production build ...
     ✓ Compiled successfully in 948ms
       Linting and checking validity of types ...
       Collecting page data ...
       Generating static pages (0/7) ...
       Generating static pages (1/7)
       Generating static pages (3/7)
       Generating static pages (5/7)
     ✓ Generating static pages (7/7)
       Finalizing page optimization ...
       Collecting build traces ...
    
    Route (app)                                 Size  First Load JS
    ┌ ○ /                                    2.41 kB         105 kB
    ├ ○ /_not-found                            995 B         103 kB
    ├ ƒ /api/chat                              140 B         103 kB
    ├ ƒ /api/chat/stream                       140 B         103 kB
    ├ ƒ /api/conversations                     140 B         103 kB
    ├ ƒ /api/conversations/[conversationId]    140 B         103 kB
    ├ ƒ /api/orders/[orderId]                  140 B         103 kB
    ├ ƒ /api/orders/[orderId]/pay              140 B         103 kB
    ├ ƒ /api/products                          140 B         103 kB
    ├ ○ /chat                                6.22 kB         112 kB
    ├ ƒ /orders/[orderId]                    2.09 kB         108 kB
    └ ƒ /products/[productId]                  378 B         106 kB
    + First Load JS shared by all             102 kB
      ├ chunks/829-8dab9a64d44a51d9.js       46.2 kB
      ├ chunks/d9cbff8c-b2655549e18d6010.js  54.2 kB
      └ other shared chunks (total)          1.95 kB
    
    
    ○  (Static)   prerendered as static content
    ƒ  (Dynamic)  server-rendered on demand
    
    ✓ • 7.83s

## Activity

    $ git diff --stat && git diff -- agent-service/src/agent_service/models.py agent-service/src/agent_service/agent_runner.py agent-service/src/agent_service/recommendation_spec.py mall-service/src/mall_service/search.py
     README.md                                          |  14 +-
     RECOMMENDATION_E2E_TEST.md                         |  45 ++++
     agent-service/prompts/goal_understanding.md        |  58 ++++-
     agent-service/prompts/recommendation_spec.md       |  17 ++
     agent-service/prompts/shopping_agent.md            |  30 ++-
     agent-service/src/agent_service/agent_runner.py    |  35 ++-
     .../src/agent_service/goal_understanding.py        |   1 +
     agent-service/src/agent_service/models.py          |  52 ++++-
     .../src/agent_service/recommendation_spec.py       |  10 +-
     agent-service/tests/test_agent_api.py              |  27 +++
     agent-service/tests/test_agent_runner.py           | 246 ++++++++++++++++++++-
     agent-service/tests/test_mall_contract.py          |  23 ++
     mall-service/src/mall_service/models.py            |   1 +
     mall-service/src/mall_service/search.py            |   6 +-
     mall-service/tests/test_mall_api.py                |  36 +++
     15 files changed, 581 insertions(+), 20 deletions(-)
    diff --git a/agent-service/src/agent_service/agent_runner.py b/agent-service/src/agent_service/agent_runner.py
    index 265219f..21bd6eb 100644
    --- a/agent-service/src/agent_service/agent_runner.py
    +++ b/agent-service/src/agent_service/agent_runner.py
    @@ -264,11 +264,25 @@ def _optional_int(slots: dict[str, object], key: str) -> int | None:
         return None
    
    
    +def recommendation_requirements_need_input(
    +    goal: GoalUnderstandingResult,
    +) -> bool:
    +    requirements = goal.recommendation_requirements
    +    return (
    +        requirements is not None
    +        and requirements.status == "collecting"
    +    )
    +
    +
     def recommendation_demand_from_goal(
         goal: GoalUnderstandingResult,
         spec: RecommendationSpec | None = None,
     ) -> RecommendationDemand:
    -    slots = goal.slots
    +    slots = (
    +        goal.recommendation_requirements.slots.model_dump(mode="json")
    +        if goal.recommendation_requirements is not None
    +        else goal.slots
    +    )
         hard = spec.hard_constraints if spec is not None else None
         required_tags = slots.get("required_tags")
         excluded_tags = slots.get("excluded_tags")
    @@ -276,7 +290,14 @@ def recommendation_demand_from_goal(
         if scenario not in {"general", "self", "gift", "replenishment"}:
             scenario = spec.scenario if spec is not None else "general"
         query = _optional_string(slots, "query")
    -    if query is None and goal.primary_intent == "product_recommendation":
    +    if (
    +        query is None
    +        and goal.primary_intent == "product_recommendation"
    +        and not (
    +            spec is not None
    +            and spec.recall_mode == "broad"
    +        )
    +    ):
             query = (
                 spec.search_queries[0]
                 if spec is not None and spec.search_queries
    @@ -769,6 +790,10 @@ def create_tools(
                 return rejected("请先调用 understand_goal")
             if goal.primary_intent != "product_recommendation":
                 return rejected("当前 primary_intent 不是商品推荐")
    +        if recommendation_requirements_need_input(goal):
    +            return rejected(
    +                "推荐需求仍在收集，只能先向用户输出模型生成的 next_question"
    +            )
             if context.recommendation_context is not None:
                 snapshot = context.recommendation_context
                 return json.dumps(
    @@ -881,6 +906,10 @@ def create_tools(
                 return rejected("Goal Understanding 表示需要先澄清关键信息")
             if goal.primary_intent != "product_recommendation":
                 return rejected("当前 primary_intent 不是商品推荐")
    +        if recommendation_requirements_need_input(goal):
    +            return rejected(
    +                "推荐需求仍在收集，请先完成模型生成的需求问题"
    +            )
             snapshot = context.recommendation_context
             if snapshot is None:
                 return rejected("请先调用 collect_recommendation_context")
    @@ -1041,6 +1070,8 @@ def create_tools(
                 return rejected("Goal Understanding 表示需要先向用户澄清关键信息")
             if goal.primary_intent != "product_recommendation":
                 return rejected("当前 primary_intent 不是商品推荐")
    +        if recommendation_requirements_need_input(goal):
    +            return rejected("推荐需求仍在收集，暂不能提交推荐")
             snapshot = context.recommendation_context
             if snapshot is None:
                 return rejected("请先调用 collect_recommendation_context")
    diff --git a/agent-service/src/agent_service/models.py b/agent-service/src/agent_service/models.py
    index 936671d..5504fab 100644
    --- a/agent-service/src/agent_service/models.py
    +++ b/agent-service/src/agent_service/models.py
    @@ -1,6 +1,6 @@
     from typing import Literal
    
    -from pydantic import BaseModel, Field, field_validator
    +from pydantic import BaseModel, Field, field_validator, model_validator
    
    
     class Product(BaseModel):
    @@ -162,6 +162,53 @@ class RecommendationDemand(BaseModel):
     IntentType = str
    
    
    +RecommendationRequirementStatus = Literal[
    +    "collecting",
    +    "ready",
    +    "bypassed",
    +]
    +
    +
    +class RecommendationRequirementSlots(BaseModel):
    +    query: str | None = Field(default=None, max_length=500)
    +    category: str | None = Field(default=None, max_length=100)
    +    min_price_cents: int | None = Field(default=None, ge=0)
    +    max_price_cents: int | None = Field(default=None, ge=0)
    +    required_tags: list[str] = Field(default_factory=list)
    +    excluded_tags: list[str] = Field(default_factory=list)
    +    scenario: Literal[
    +        "general",
    +        "self",
    +        "gift",
    +        "replenishment",
    +    ] | None = None
    +    usage: str | None = Field(default=None, max_length=500)
    +    recipient: str | None = Field(default=None, max_length=200)
    +
    +
    +class RecommendationRequirementState(BaseModel):
    +    status: RecommendationRequirementStatus
    +    slots: RecommendationRequirementSlots = Field(
    +        default_factory=RecommendationRequirementSlots
    +    )
    +    next_question: str | None = Field(default=None, max_length=2_000)
    +    declined_requirements: list[str] = Field(default_factory=list)
    +    collection_reason: str | None = Field(default=None, max_length=2_000)
    +
    +    @model_validator(mode="after")
    +    def question_matches_status(self) -> "RecommendationRequirementState":
    +        if self.status == "collecting":
    +            if not self.next_question or not self.next_question.strip():
    +                raise ValueError(
    +                    "collecting recommendation requirements need a next question"
    +                )
    +        elif self.next_question is not None:
    +            raise ValueError(
    +                "ready or bypassed recommendation requirements cannot have a question"
    +            )
    +        return self
    +
    +
     class GoalUnderstandingDraft(BaseModel):
         intents: list[IntentType] = Field(min_length=1, max_length=5)
         goal: str = Field(min_length=1, max_length=2_000)
    @@ -170,6 +217,7 @@ class GoalUnderstandingDraft(BaseModel):
         missing_slots: list[str] = Field(default_factory=list)
         requires_clarification: bool = False
         clarification_question: str | None = Field(default=None, max_length=1_000)
    +    recommendation_requirements: RecommendationRequirementState | None = None
    
    
     class GoalUnderstandingResult(BaseModel):
    @@ -183,6 +231,7 @@ class GoalUnderstandingResult(BaseModel):
         requires_clarification: bool = False
         clarification_question: str | None = Field(default=None, max_length=1_000)
         pending_intent_question: str | None = Field(default=None, max_length=1_000)
    +    recommendation_requirements: RecommendationRequirementState | None = None
    
    
     class RecommendationSpecHardConstraints(BaseModel):
    @@ -209,6 +258,7 @@ class RecommendationSpec(BaseModel):
         weak_categories: list[str] = Field(default_factory=list)
         negative_tags: list[str] = Field(default_factory=list)
         search_queries: list[str] = Field(min_length=1, max_length=6)
    +    recall_mode: Literal["targeted", "broad"] = "targeted"
         scenario: Literal[
             "general",
             "self",
    diff --git a/agent-service/src/agent_service/recommendation_spec.py b/agent-service/src/agent_service/recommendation_spec.py
    index 8a376d5..9ec1ab1 100644
    --- a/agent-service/src/agent_service/recommendation_spec.py
    +++ b/agent-service/src/agent_service/recommendation_spec.py
    @@ -95,7 +95,11 @@ def _apply_explicit_goal_constraints(
         spec: RecommendationSpec,
         goal: GoalUnderstandingResult,
     ) -> RecommendationSpec:
    -    slots = goal.slots
    +    slots = (
    +        goal.recommendation_requirements.slots.model_dump(mode="json")
    +        if goal.recommendation_requirements is not None
    +        else goal.slots
    +    )
         hard = spec.hard_constraints
         category = slots.get("category")
         min_price = _non_negative_int(slots.get("min_price_cents"))
    @@ -122,7 +126,7 @@ def _apply_explicit_goal_constraints(
             ),
         )
         scenario = slots.get("scenario")
    -    if scenario not in {"general", "self", "gift", "replenishment"}:
    +    if scenario not in {"general", "self", "gift", "replenishment", None}:
             scenario = spec.scenario
         usage = slots.get("usage")
         recipient = slots.get("recipient")
    @@ -137,7 +141,7 @@ def _apply_explicit_goal_constraints(
             update={
                 "hard_constraints": normalized_hard,
                 "search_queries": queries,
    -            "scenario": scenario,
    +            "scenario": scenario or spec.scenario,
                 "usage": (
                     usage
                     if isinstance(usage, str) and usage
    diff --git a/mall-service/src/mall_service/search.py b/mall-service/src/mall_service/search.py
    index 60e9293..781f5ea 100644
    --- a/mall-service/src/mall_service/search.py
    +++ b/mall-service/src/mall_service/search.py
    @@ -91,7 +91,7 @@ def build_es_query(
             "filter": filters,
             "must_not": must_not,
         }
    -    if text_should:
    +    if text_should and spec.recall_mode == "targeted":
             bool_query["must"] = [
                 {
                     "bool": {
    @@ -100,6 +100,8 @@ def build_es_query(
                     }
                 }
             ]
    +    elif text_should:
    +        preference_should.extend(text_should)
         if preference_should:
             bool_query["should"] = preference_should
             bool_query["minimum_should_match"] = 0
    @@ -203,7 +205,7 @@ def mock_search_products(
             for query in [*spec.search_queries, spec.usage, spec.recipient]
             if query
         ]
    -    if text_queries:
    +    if text_queries and spec.recall_mode == "targeted":
             candidates = [
                 (product, score)
                 for product, score in candidates
    ✓ • 0ms

## Activity

    $ git diff -- agent-service/prompts/goal_understanding.md agent-service/prompts/shopping_agent.md agent-service/prompts/recommendation_spec.md
    diff --git a/agent-service/prompts/goal_understanding.md b/agent-service/prompts/goal_understanding.md
    index ba997b1..d2464ef 100644
    --- a/agent-service/prompts/goal_understanding.md
    +++ b/agent-service/prompts/goal_understanding.md
    @@ -63,6 +63,45 @@
    
     金额必须转换为分。用户说“300 元以内”时输出 `"max_price_cents": 30000`。
    
    +## 推荐需求收集
    +
    +当 `primary_intent` 为 `product_recommendation` 时，你还要维护
    +`recommendation_requirements`。这是跨轮累计的推荐需求，不是当前消息槽位的副本。
    +
    +- 读取 `previous_goal.recommendation_requirements`，合并用户本轮表达和最近对话。
    +- 用户补充条件时保留已有条件；用户修改条件时以最新表达为准；用户开始明显不同的
    +  推荐任务时，可以清空不再适用的旧需求。
    +- 用户本轮一次提供多个条件时全部保存，不要为了分步询问而丢弃其中任何一项。
    +- 用户拒绝、取消或修改某个条件时，同步更新累计需求和
    +  `declined_requirements`。
    +- 不要编造用户没有说过、也没有在历史上下文中明确保留的需求。
    +
    +`status` 只能取：
    +
    +- `collecting`：还需要向用户了解需求。必须自主生成一个 `next_question`，并结束
    +  本轮推荐业务编排。
    +- `ready`：根据当前累计需求和上下文，已经有足够信息进入推荐。
    +- `bypassed`：用户明确表示不要收集需求，例如“你别管那么多，直接推荐”“不用问了”
    +  或“随便推荐”。本轮直接进入推荐，不得二次确认。
    +
    +询问方式：
    +
    +- 每轮最多询问一个需求点，不能一次抛出问卷或多个并列问题。
    +- 具体问什么、先问什么、如何措辞完全由你根据上下文决定，不要套用固定顺序或固定
    +  模板。
    +- 优先询问最可能实质影响召回、筛选或排序的信息。
    +- 不要机械追求填满所有槽位；信息已经足够时及时设为 `ready`。
    +- 已经回答、明确拒绝或不再需要的信息不要重复询问。
    +- “预算不限”“价格你看着办”“不关心材质”等通常只表示跳过当前相关信息，不等同于
    +  跳过整个需求收集；如果用户同时表达“直接推荐”，才使用 `bypassed`。
    +- `next_question` 必须只包含一个用户需要回答的需求点。`ready` 或 `bypassed` 时
    +  必须为 `null`。
    +
    +`collection_reason` 用一句简洁中文说明你为什么继续询问、直接推荐或整体跳过，便于
    +诊断。`declined_requirements` 使用简短自然语言记录用户明确不希望继续了解的条件。
    +
    +非商品推荐意图不使用需求收集，输出 `"recommendation_requirements": null`。
    +
     ## 置信度与澄清
    
     - `confidence` 表示意图和主要槽位整体的可信程度。
    @@ -93,6 +132,23 @@
       },
       "missing_slots": [],
       "requires_clarification": false,
    -  "clarification_question": null
    +  "clarification_question": null,
    +  "recommendation_requirements": {
    +    "status": "collecting",
    +    "slots": {
    +      "query": "通勤",
    +      "category": null,
    +      "min_price_cents": null,
    +      "max_price_cents": 30000,
    +      "required_tags": [],
    +      "excluded_tags": [],
    +      "scenario": "self",
    +      "usage": "通勤",
    +      "recipient": null
    +    },
    +    "next_question": "除了通勤使用之外，你最希望这个商品解决什么问题？",
    +    "declined_requirements": [],
    +    "collection_reason": "已有用途和预算，但还缺少能影响选品的关键使用需求"
    +  }
     }
     ```
    diff --git a/agent-service/prompts/recommendation_spec.md b/agent-service/prompts/recommendation_spec.md
    index 8d57eeb..de314df 100644
    --- a/agent-service/prompts/recommendation_spec.md
    +++ b/agent-service/prompts/recommendation_spec.md
    @@ -9,6 +9,8 @@ Understanding、用户画像、购物车、浏览记录、订单记录和商品
     ## 输入
    
     - `goal`：Goal Understanding 结果。
    +- `goal.recommendation_requirements`：模型跨轮维护的累计推荐需求，包含用户显式
    +  条件、是否已足够推荐、用户跳过收集的状态和已被拒绝的需求。
     - `agent_profile`：Agent 维护的长期偏好。
     - `platform_profile`：平台画像。
     - `cart`：购物车及加购时间。
    @@ -25,6 +27,9 @@ Understanding、用户画像、购物车、浏览记录、订单记录和商品
     5. 平台画像和 Agent 画像用于补充长期偏好和冷启动。
     6. 当前显式需求与历史推测冲突时，必须服从显式需求。
     7. 不要把弱推断写成硬约束。
    +8. 用户显式需求以 `goal.recommendation_requirements.slots` 为准；不要用历史行为
    +   覆盖或补全其中用户已经明确修改的条件。
    +9. 用户拒绝或跳过确认的条件不能擅自变成硬约束。
    
     ## 硬约束
    
    @@ -38,6 +43,17 @@ Understanding、用户画像、购物车、浏览记录、订单记录和商品
     历史浏览、订单和画像推测出的偏好应放入 `preferred_categories`、
     `preferred_tags`、`weak_categories` 或 `negative_tags`，不能擅自变成硬约束。
    
    +## 召回模式
    +
    +`recall_mode` 取 `targeted` 或 `broad`：
    +
    +- `targeted`：有明确商品目标或关键词时使用，查询词参与检索命中。
    +- `broad`：用户明确跳过了需求收集且没有足够商品目标时使用，允许只依靠画像、
    +  历史行为和硬过滤条件进行宽泛召回。
    +
    +`broad` 模式仍必须提供 1～6 个有诊断价值的搜索词，但搜索服务不会要求关键词命中。
    +不得因为这个模式编造用户偏好。
    +
     ## 搜索词
    
     生成 1～6 个适合商城关键词搜索的查询变体：
    @@ -81,6 +97,7 @@ Understanding、用户画像、购物车、浏览记录、订单记录和商品
         "通勤电脑包",
         "轻便通勤包"
       ],
    +  "recall_mode": "targeted",
       "scenario": "self",
       "usage": "通勤并携带电脑",
       "recipient": null,
    diff --git a/agent-service/prompts/shopping_agent.md b/agent-service/prompts/shopping_agent.md
    index 5603359..edf574b 100644
    --- a/agent-service/prompts/shopping_agent.md
    +++ b/agent-service/prompts/shopping_agent.md
    @@ -33,6 +33,22 @@
     - 如果 `requires_clarification = true`，只询问 `clarification_question`，不要调用业务工具。
     - 如果 Action 返回 unavailable，停止本轮业务编排并请用户稍后重试，不要自行猜测。
    
    +## 推荐需求收集
    +
    +每次 `understand_goal` 返回 `recommendation_requirements` 后，严格按模型给出的状态
    +推进，不自行选择下一项需求，也不套用固定问题模板。
    +
    +- `status = collecting`：只向用户输出 `next_question` 这一项需求，并结束本轮。
    +  必须原样表达该问题，不得自行追加第二个问题，也不得调用
    +  `collect_recommendation_context`、`generate_recommendation_spec`、搜索或推荐工具。
    +- `status = ready`：需求已经足够。不要再复述或确认已收集条件，直接进入推荐主流程。
    +- `status = bypassed`：用户要求跳过需求收集。不要再询问或确认，直接使用当前已有
    +  需求、历史需求、画像和行为信息推荐。
    +
    +`recommendation_requirements.slots` 是累计需求。进入推荐后只能把其中用户明确提供的
    +内容作为硬约束；`declined_requirements` 表示用户不想继续确认的条件，不得擅自转成
    +硬约束。
    +
     按 `primary_intent` 路由：
    
     - `product_recommendation`：依次调用 `collect_recommendation_context`、
    @@ -46,12 +62,13 @@
    
     当 `primary_intent = product_recommendation` 时：
    
    -1. 调用 `collect_recommendation_context` 收集画像、购物车、浏览、订单和商品目录。
    -2. 调用 `generate_recommendation_spec`，由独立 Prompt 和模型生成推荐 SPEC。
    -3. 分别调用 `search_organic_candidates` 和 `search_ad_candidates`。两者都只使用
    +1. 先检查 `recommendation_requirements.status`。只有 `ready` 或 `bypassed` 才能继续。
    +2. 调用 `collect_recommendation_context` 收集画像、购物车、浏览、订单和商品目录。
    +3. 调用 `generate_recommendation_spec`，由独立 Prompt 和模型生成推荐 SPEC。
    +4. 分别调用 `search_organic_candidates` 和 `search_ad_candidates`。两者都只使用
        完整 SPEC，可以放在同一轮并行调用。相关 Action 会把整个 SPEC 传给
        `mall-service`，由 `mall-service` 转换为 ES 查询并返回检索结果。
    -4. 调用无参数工具 `recommend_products`，只读取两路搜索 Action 的缓存候选，
    +5. 调用无参数工具 `recommend_products`，只读取两路搜索 Action 的缓存候选，
        完成合并、评分和阈值分路。
    
     主 Agent 不自行编写搜索词、不自行判断行为记录权重、不直接调用商城搜索接口，
    @@ -121,7 +138,10 @@ SPEC 只用于指导召回，最终评分继续使用统一权重公式，避免
    
     - 使用已有对话理解“第一个”“这个”“更适合送礼吗”等指代。
     - 用户修改预算或场景时，以最新需求重新查询。
    -- 信息不足且会影响推荐质量时，只追问一个最关键的问题，例如预算、使用场景或收礼对象。
    +- 用户修改预算、场景或其他已收集条件时，更新累计需求后重新推荐，不要重走已经完成
    +  的问题。
    +- 是否继续询问、询问什么以及何时停止由 Goal Understanding 返回的
    +  `recommendation_requirements` 决定。
     - 如果用户已经给出足够信息，直接推荐，不要重复询问。
    
     ## 回答风格
    ✓ • 0ms

## Activity

    $ git diff -- agent-service/tests/test_agent_runner.py agent-service/tests/test_agent_api.py mall-service/tests/test_mall_api.py agent-service/tests/test_mall_contract.py | sed -n '1,520p'
    diff --git a/agent-service/tests/test_agent_api.py b/agent-service/tests/test_agent_api.py
    index fbc1785..0866325 100644
    --- a/agent-service/tests/test_agent_api.py
    +++ b/agent-service/tests/test_agent_api.py
    @@ -114,6 +114,23 @@ GOAL_UNDERSTANDING = {
         "requires_clarification": False,
         "clarification_question": None,
         "pending_intent_question": "是否继续处理订单查询？",
    +    "recommendation_requirements": {
    +        "status": "ready",
    +        "slots": {
    +            "query": "通勤",
    +            "category": None,
    +            "min_price_cents": None,
    +            "max_price_cents": 30000,
    +            "required_tags": [],
    +            "excluded_tags": [],
    +            "scenario": "self",
    +            "usage": "通勤",
    +            "recipient": None,
    +        },
    +        "next_question": None,
    +        "declined_requirements": [],
    +        "collection_reason": "已有明确商品目标和预算，可以直接推荐",
    +    },
     }
    
     RECOMMENDATION_SPEC = {
    @@ -275,6 +292,11 @@ def test_stream_chat_persists_completed_conversation(
         assert detail.messages[1].goal_understanding.pending_intents == [
             "order_query"
         ]
    +    assert (
    +        detail.messages[1]
    +        .goal_understanding.recommendation_requirements.status
    +        == "ready"
    +    )
         assert detail.messages[1].recommendation_spec is not None
         assert detail.messages[1].recommendation_spec.search_queries == [
             "通勤",
    @@ -442,6 +464,11 @@ def test_stream_chat_passes_previous_plan_state_to_next_turn(
         assert captured["previous_goal_understanding"].pending_intents == [
             "order_query"
         ]
    +    assert (
    +        captured["previous_goal_understanding"]
    +        .recommendation_requirements.slots.max_price_cents
    +        == 30000
    +    )
    
    
     def test_conversation_history_endpoints(store: ConversationStore) -> None:
    diff --git a/agent-service/tests/test_agent_runner.py b/agent-service/tests/test_agent_runner.py
    index 41cb0c9..93dcd91 100644
    --- a/agent-service/tests/test_agent_runner.py
    +++ b/agent-service/tests/test_agent_runner.py
    @@ -12,6 +12,7 @@ from agent_service.agent_runner import (
         ShoppingAgentContext,
         create_tools,
         normalize_openai_base_url,
    +    recommendation_demand_from_goal,
         stream_agent_reply,
     )
     from agent_service.goal_understanding import AgentGoalUnderstander
    @@ -26,6 +27,8 @@ from agent_service.models import (
         Product,
         RecommendationBatch,
         RecommendationDemand,
    +    RecommendationRequirementSlots,
    +    RecommendationRequirementState,
         RecommendationSpec,
         RecommendationSpecHardConstraints,
         ScoredProduct,
    @@ -217,19 +220,32 @@ def goal_understanding(
         *,
         query: str = "通勤",
         intents: list[str] | None = None,
    +    requirement_status: str = "ready",
    +    next_question: str | None = None,
     ) -> GoalUnderstandingResult:
         ordered_intents = intents or ["product_recommendation"]
    +    slots = {
    +        "query": query,
    +        "max_price_cents": 30000,
    +        "scenario": "self",
    +    }
         return GoalUnderstandingResult(
             primary_intent=ordered_intents[0],
             intents=ordered_intents,
             pending_intents=ordered_intents[1:],
             goal=f"推荐与 {query} 相关的商品",
             confidence=0.95,
    -        slots={
    -            "query": query,
    -            "max_price_cents": 30000,
    -            "scenario": "self",
    -        },
    +        slots=slots,
    +        recommendation_requirements=RecommendationRequirementState(
    +            status=requirement_status,
    +            slots=RecommendationRequirementSlots(
    +                query=query,
    +                max_price_cents=30000,
    +                scenario="self",
    +            ),
    +            next_question=next_question,
    +            collection_reason="模型判断当前推荐需求状态",
    +        ),
             pending_intent_question=(
                 "当前已处理第一个意图。需要我继续处理后续意图吗？"
                 if len(ordered_intents) > 1
    @@ -257,6 +273,20 @@ def recommendation_spec(
         )
    
    
    +def test_broad_recall_does_not_promote_diagnostic_query_to_demand() -> None:
    +    goal = goal_understanding(
    +        requirement_status="bypassed",
    +        query="",
    +    )
    +    spec = recommendation_spec(queries=["通勤"]).model_copy(
    +        update={"recall_mode": "broad"}
    +    )
    +
    +    demand = recommendation_demand_from_goal(goal, spec)
    +
    +    assert demand.query == ""
    +
    +
     def scored_candidate(
         *,
         product_id: str,
    @@ -523,6 +553,26 @@ def test_understand_goal_action_returns_first_intent_and_pending_intents() -> No
         assert context.goal_understanding is not None
    
    
    +def test_collecting_requirements_block_recommendation_steps() -> None:
    +    context = ShoppingAgentContext(mall=mall_client())
    +    context.goal_understanding = goal_understanding(
    +        requirement_status="collecting",
    +        next_question="你最在意这个商品的什么特点？",
    +    )
    +
    +    collected = json.loads(
    +        invoke_tool(context, "collect_recommendation_context", {})
    +    )
    +    generated = json.loads(
    +        invoke_tool(context, "generate_recommendation_spec", {})
    +    )
    +
    +    assert collected["status"] == "rejected"
    +    assert "next_question" in collected["message"]
    +    assert generated["status"] == "rejected"
    +    assert context.recommendation_context is None
    +
    +
     def test_goal_understanding_agent_uses_its_own_prompt() -> None:
         model = ScriptedModel(
             [
    @@ -540,6 +590,23 @@ def test_goal_understanding_agent_uses_its_own_prompt() -> None:
                                 "missing_slots": [],
                                 "requires_clarification": False,
                                 "clarification_question": None,
    +                            "recommendation_requirements": {
    +                                "status": "collecting",
    +                                "slots": {
    +                                    "query": "通勤包",
    +                                    "category": "箱包",
    +                                    "min_price_cents": None,
    +                                    "max_price_cents": None,
    +                                    "required_tags": [],
    +                                    "excluded_tags": [],
    +                                    "scenario": None,
    +                                    "usage": "通勤",
    +                                    "recipient": None,
    +                                },
    +                                "next_question": "你希望大概控制在什么价位？",
    +                                "declined_requirements": [],
    +                                "collection_reason": "还需要价格信息帮助筛选",
    +                            },
                             },
                             ensure_ascii=False,
                         )
    @@ -569,12 +636,80 @@ def test_goal_understanding_agent_uses_its_own_prompt() -> None:
    
         assert result.primary_intent == "product_recommendation"
         assert result.pending_intents == ["order_query"]
    +    assert result.recommendation_requirements is not None
    +    assert result.recommendation_requirements.status == "collecting"
    +    assert result.recommendation_requirements.next_question == (
    +        "你希望大概控制在什么价位？"
    +    )
         assert model.first_call is not None
         assert "Goal Understanding" in (
             model.first_call.system_instructions or ""
         )
    
    
    +def test_goal_understanding_can_bypass_requirement_collection() -> None:
    +    model = ScriptedModel(
    +        [
    +            [
    +                assistant_message(
    +                    json.dumps(
    +                        {
    +                            "intents": ["product_recommendation"],
    +                            "goal": "直接推荐商品",
    +                            "confidence": 0.97,
    +                            "slots": {},
    +                            "missing_slots": [],
    +                            "requires_clarification": False,
    +                            "clarification_question": None,
    +                            "recommendation_requirements": {
    +                                "status": "bypassed",
    +                                "slots": {
    +                                    "query": None,
    +                                    "category": None,
    +                                    "min_price_cents": None,
    +                                    "max_price_cents": None,
    +                                    "required_tags": [],
    +                                    "excluded_tags": [],
    +                                    "scenario": None,
    +                                    "usage": None,
    +                                    "recipient": None,
    +                                },
    +                                "next_question": None,
    +                                "declined_requirements": ["不回答推荐需求问题"],
    +                                "collection_reason": "用户明确要求直接推荐",
    +                            },
    +                        },
    +                        ensure_ascii=False,
    +                    )
    +                )
    +            ]
    +        ]
    +    )
    +    understander = AgentGoalUnderstander(
    +        config=llm_config(),
    +        model=model,
    +    )
    +
    +    result = asyncio.run(
    +        understander.understand(
    +            current_message="你别管那么多，直接推荐",
    +            recent_messages=[
    +                ConversationMessage(
    +                    role="user",
    +                    content="你别管那么多，直接推荐",
    +                )
    +            ],
    +            previous_goal=None,
    +            previous_recommendations=[],
    +            previous_orders=[],
    +        )
    +    )
    +
    +    assert result.recommendation_requirements is not None
    +    assert result.recommendation_requirements.status == "bypassed"
    +    assert result.recommendation_requirements.next_question is None
    +
    +
     def test_collect_context_and_generate_recommendation_spec_are_separate_actions(
         caplog,
     ) -> None:
    @@ -993,6 +1128,87 @@ def test_semantic_candidates_are_one_mixed_score_ordered_pool() -> None:
         ]
    
    
    +def test_model_generated_requirement_question_ends_turn_without_recommendation() -> None:
    +    question = "你更希望它适合通勤时装电脑，还是日常随身使用？"
    +    model = ScriptedModel(
    +        [
    +            [
    +                function_call(
    +                    "understand_goal",
    +                    {},
    +                    call_id="call-goal",
    +                )
    +            ],
    +            [
    +                assistant_message(
    +                    json.dumps(
    +                        {
    +                            "intents": ["product_recommendation"],
    +                            "goal": "推荐一个通勤包",
    +                            "confidence": 0.96,
    +                            "slots": {"query": "通勤包"},
    +                            "missing_slots": [],
    +                            "requires_clarification": False,
    +                            "clarification_question": None,
    +                            "recommendation_requirements": {
    +                                "status": "collecting",
    +                                "slots": {
    +                                    "query": "通勤包",
    +                                    "category": "箱包",
    +                                    "min_price_cents": None,
    +                                    "max_price_cents": None,
    +                                    "required_tags": [],
    +                                    "excluded_tags": [],
    +                                    "scenario": None,
    +                                    "usage": "通勤",
    +                                    "recipient": None,
    +                                },
    +                                "next_question": question,
    +                                "declined_requirements": [],
    +                                "collection_reason": "还需要明确具体使用方式",
    +                            },
    +                        },
    +                        ensure_ascii=False,
    +                    )
    +                )
    +            ],
    +            [assistant_message(question)],
    +        ]
    +    )
    +
    +    async def collect_events() -> list[dict[str, object]]:
    +        return [
    +            event
    +            async for event in stream_agent_reply(
    +                [ConversationMessage(role="user", content="推荐个通勤包")],
    +                llm_config(),
    +                mall_client(),
    +                model_override=model,
    +            )
    +        ]
    +
    +    events = asyncio.run(collect_events())
    +
    +    started_tools = [
    +        event["tool"]
    +        for event in events
    +        if event["type"] == "tool_started"
    +    ]
    +    text = "".join(
    +        str(event["content"])
    +        for event in events
    +        if event["type"] == "delta"
    +    )
    +    done = next(event for event in events if event["type"] == "done")
    +
    +    assert started_tools == ["understand_goal"]
    +    assert text == question
    +    assert done["recommendations"] == []
    +    assert done["goal_understanding"]["recommendation_requirements"][
    +        "status"
    +    ] == "collecting"
    +
    +
     def test_react_loop_loads_sources_and_streams_only_final_selection() -> None:
         model = ScriptedModel(
             [
    @@ -1023,6 +1239,23 @@ def test_react_loop_loads_sources_and_streams_only_final_selection() -> None:
                                 "missing_slots": [],
                                 "requires_clarification": False,
                                 "clarification_question": None,
    +                            "recommendation_requirements": {
    +                                "status": "ready",
    +                                "slots": {
    +                                    "query": "通勤",
    +                                    "category": None,
    +                                    "min_price_cents": None,
    +                                    "max_price_cents": 30000,
    +                                    "required_tags": [],
    +                                    "excluded_tags": [],
    +                                    "scenario": "self",
    +                                    "usage": "通勤",
    +                                    "recipient": None,
    +                                },
    +                                "next_question": None,
    +                                "declined_requirements": [],
    +                                "collection_reason": "商品目标和预算已足够",
    +                            },
                             },
                             ensure_ascii=False,
                         )
    @@ -1173,6 +1406,9 @@ def test_react_loop_loads_sources_and_streams_only_final_selection() -> None:
         assert "pending_intent_question" in (
             model.first_call.system_instructions or ""
         )
    +    assert "status = collecting" in (
    +        model.first_call.system_instructions or ""
    +    )
    
    
     def test_previous_plan_state_is_exposed_to_model_without_forcing_action() -> None:
    diff --git a/agent-service/tests/test_mall_contract.py b/agent-service/tests/test_mall_contract.py
    index 5c607cd..d3f6cb7 100644
    --- a/agent-service/tests/test_mall_contract.py
    +++ b/agent-service/tests/test_mall_contract.py
    @@ -83,3 +83,26 @@ def test_agent_passes_whole_spec_to_mock_es_search() -> None:
         assert all(product.price_cents <= 30000 for product in products)
         assert ads
         assert all(item.source == "advertisement" for item in ads)
    +
    +
    +def test_agent_spec_supports_model_selected_broad_recall() -> None:
    +    client = mall_client()
    +    spec = RecommendationSpec(
    +        goal_summary="用户跳过需求收集，按已有信息宽泛推荐",
    +        hard_constraints=RecommendationSpecHardConstraints(
    +            max_price_cents=10000,
    +        ),
    +        preferred_categories=["箱包"],
    +        preferred_tags=["通勤"],
    +        search_queries=["通勤"],
    +        recall_mode="broad",
    +        confidence=0.7,
    +    )
    +
    +    products = asyncio.run(
    +        client.search_organic_with_spec(spec, limit=10)
    +    )
    +
    +    assert len(products) > 1
    +    assert len({product.category for product in products}) > 1
    +    assert all(product.price_cents <= 10000 for product in products)
    diff --git a/mall-service/tests/test_mall_api.py b/mall-service/tests/test_mall_api.py
    index f057485..96b3263 100644
    --- a/mall-service/tests/test_mall_api.py
    +++ b/mall-service/tests/test_mall_api.py
    @@ -195,6 +195,42 @@ def test_spec_ad_search_returns_ad_candidates() -> None:
         assert all(item["ad"]["is_ad"] is True for item in ads)
    
    
    +def test_broad_spec_search_does_not_require_keyword_match() -> None:
    +    spec = {
    +        "goal_summary": "用户跳过需求收集，按历史偏好宽泛推荐",
    +        "hard_constraints": {
    +            "category": None,
    +            "min_price_cents": None,
    +            "max_price_cents": 10000,
    +            "required_tags": [],
    +            "excluded_tags": [],
    +        },
    +        "preferred_categories": ["箱包"],
    +        "preferred_tags": ["通勤"],
    +        "weak_categories": [],
    +        "negative_tags": [],
    +        "search_queries": ["通勤"],
    +        "recall_mode": "broad",
    +        "scenario": "self",
    +        "usage": None,
    +        "recipient": None,
    +        "source_evidence": [],
    +        "confidence": 0.7,
    +        "missing_information": [],
    +    }
    +
    +    response = client.post(
    +        "/api/search/organic",
    +        json={"spec": spec, "limit": 10},
    +    )
    +
    +    assert response.status_code == 200
    +    products = response.json()["items"]
    +    assert len(products) > 1
    +    assert len({product["category"] for product in products}) > 1
    +    assert all(product["price_cents"] <= 10000 for product in products)
    +
    +
     def test_create_order_uses_catalog_snapshot_and_is_idempotent() -> None:
         body = {
             "items": [{"product_id": "commuter-backpack", "quantity": 1}],
    ✓ • 0ms

## Activity

    $ ls -la agent-service/config && ls -la agent-service/data 2>/dev/null || true
    total 8
    drwxr-xr-x@ 3 mindeng  staff    96 Nov  1 20:52 .
    drwxr-xr-x@ 9 mindeng  staff   288 Nov  1 21:24 ..
    -rw-r--r--@ 1 mindeng  staff  1928 Nov  8 20:37 llm.example.yaml
    total 920
    drwxr-xr-x@ 5 mindeng  staff     160 Nov  8 21:02 .
    drwxr-xr-x@ 9 mindeng  staff     288 Nov  1 21:24 ..
    -rw-r--r--@ 1 mindeng  staff  339968 Nov  8 21:02 agent.db
    -rw-r--r--@ 1 mindeng  staff   32768 Nov  8 21:02 agent.db-shm
    -rw-r--r--@ 1 mindeng  staff   41232 Nov  8 21:02 agent.db-wal
    ✓ • 0ms

## Activity

    $ git diff --check && uv run pytest -q
    ........................................................................ [ 78%]
    ....................                                                     [100%]
    92 passed in 1.52s
    ✓ • 1.96s

## Activity

    $ rg -n "class RecommendationRequirementState|class RecommendationSpec\(|recommendation_requirements_need_input|推荐需求收集|recall_mode|def test_model_generated_requirement|def test_broad_spec" agent-service/src/agent_service/models.py agent-service/src/agent_service/agent_runner.py agent-service/prompts/goal_understanding.md agent-service/prompts/shopping_agent.md agent-service/prompts/recommendation_spec.md mall-service/src/mall_service/search.py agent-service/tests/test_agent_runner.py mall-service/tests/test_mall_api.py
    mall-service/tests/test_mall_api.py:198:def test_broad_spec_search_does_not_require_keyword_match() -> None:
    mall-service/tests/test_mall_api.py:213:        "recall_mode": "broad",
    agent-service/tests/test_agent_runner.py:282:        update={"recall_mode": "broad"}
    agent-service/tests/test_agent_runner.py:1131:def test_model_generated_requirement_question_ends_turn_without_recommendation() -> None:
    agent-service/prompts/recommendation_spec.md:48:`recall_mode` 取 `targeted` 或 `broad`：
    agent-service/prompts/recommendation_spec.md:100:  "recall_mode": "targeted",
    agent-service/prompts/shopping_agent.md:36:## 推荐需求收集
    mall-service/src/mall_service/search.py:94:    if text_should and spec.recall_mode == "targeted":
    mall-service/src/mall_service/search.py:208:    if text_queries and spec.recall_mode == "targeted":
    agent-service/prompts/goal_understanding.md:66:## 推荐需求收集
    agent-service/src/agent_service/models.py:189:class RecommendationRequirementState(BaseModel):
    agent-service/src/agent_service/models.py:251:class RecommendationSpec(BaseModel):
    agent-service/src/agent_service/models.py:261:    recall_mode: Literal["targeted", "broad"] = "targeted"
    agent-service/src/agent_service/agent_runner.py:267:def recommendation_requirements_need_input(
    agent-service/src/agent_service/agent_runner.py:298:            and spec.recall_mode == "broad"
    agent-service/src/agent_service/agent_runner.py:793:        if recommendation_requirements_need_input(goal):
    agent-service/src/agent_service/agent_runner.py:909:        if recommendation_requirements_need_input(goal):
    agent-service/src/agent_service/agent_runner.py:1073:        if recommendation_requirements_need_input(goal):
    ✓ • 0ms

## Activity

    $ git status --short --branch
    ## main
     M README.md
     M RECOMMENDATION_E2E_TEST.md
     M agent-service/prompts/goal_understanding.md
     M agent-service/prompts/recommendation_spec.md
     M agent-service/prompts/shopping_agent.md
     M agent-service/src/agent_service/agent_runner.py
     M agent-service/src/agent_service/goal_understanding.py
     M agent-service/src/agent_service/models.py
     M agent-service/src/agent_service/recommendation_spec.py
     M agent-service/tests/test_agent_api.py
     M agent-service/tests/test_agent_runner.py
     M agent-service/tests/test_mall_contract.py
     M mall-service/src/mall_service/models.py
     M mall-service/src/mall_service/search.py
     M mall-service/tests/test_mall_api.py
    ✓ • 0ms

## Assistant

已按调整后的方案完成实施。

核心改动：

- Goal Understanding 模型负责维护跨轮累计的 `recommendation_requirements`，包含 `collecting`、`ready`、`bypassed` 三种模型判断状态，并输出自主生成的 `next_question`，见 [models.py](/Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/models.py:189) 和 [goal_understanding.md](/Users/mindeng/workspace/niub-shangcheng/agent-service/prompts/goal_understanding.md:66)。
- 没有新增代码状态机、固定询问顺序或问题模板。代码只校验结构、持久化模型结果，并在 `collecting` 时阻止提前进入推荐，见 [agent_runner.py](/Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/agent_runner.py:267)。
- 主 Agent 在 `collecting` 时只能原样输出模型生成的问题；`ready` 直接推荐；`bypassed` 当轮跳过收集且不二次确认，见 [shopping_agent.md](/Users/mindeng/workspace/niub-shangcheng/agent-service/prompts/shopping_agent.md:36)。
- 累计需求会用于 SPEC 硬约束和最终评分需求，不再只读取当前轮槽位。
- 新增模型可选的 `recall_mode: broad`。用户直接要求推荐且没有商品目标时，可以不强制关键词命中，仍应用明确的价格、品类和排除条件，见 [search.py](/Users/mindeng/workspace/niub-shangcheng/mall-service/src/mall_service/search.py:94)。
- 需求状态随 Goal Understanding 一起写入现有消息 metadata，历史会话可以直接恢复。
- README 和推荐 E2E 文档已补充需求收集、单项跳过和整体跳过场景。

验证结果：

- `uv run pytest -q`：92 项全部通过。
- `pnpm --dir web build`：构建、类型检查和静态页面生成全部通过。
- `git diff --check`：通过。

脚本化模型测试覆盖了模型生成问题、收集轮不调用推荐工具、整体跳过、累计需求传递和 broad recall，见 [test_agent_runner.py](/Users/mindeng/workspace/niub-shangcheng/agent-service/tests/test_agent_runner.py:1131) 和 [test_mall_api.py](/Users/mindeng/workspace/niub-shangcheng/mall-service/tests/test_mall_api.py:198)。

未执行真实大模型对话验收，因为仓库中只有 `llm.example.yaml`，没有可用的私有模型配置。
