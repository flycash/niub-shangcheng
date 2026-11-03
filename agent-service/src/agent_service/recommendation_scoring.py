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
    return exact, category


def _profile_scores(
    product: Product,
    agent_profile: AgentProfile | None,
    platform_profile: PlatformProfile | None,
    now: datetime,
) -> tuple[float, float, list[str]]:
    product_tags = _normalized_tags(product.tags)
    penalties: list[str] = []

    agent_score = 0.0
    if agent_profile is not None:
        category_match = (
            1.0
            if product.category in agent_profile.preferred_categories
            else 0.0
        )
        preferred_tags = _normalized_tags(agent_profile.preferred_tags)
        tag_match = (
            len(product_tags & preferred_tags) / len(preferred_tags)
            if preferred_tags
            else 0.0
        )
        agent_score = _clamp(
            (0.7 * category_match + 0.3 * tag_match)
            * _decay(
                agent_profile.updated_at,
                now,
                HALF_LIVES_DAYS["agent_profile"],
            )
        )
        if product_tags & _normalized_tags(agent_profile.avoid_tags):
            penalties.append("命中 Agent 画像禁忌标签")

    platform_score = 0.0
    if platform_profile is not None:
        affinity = next(
            (
                item.score
                for item in platform_profile.category_affinity
                if item.category == product.category
            ),
            0.0,
        )
        platform_score = _clamp(
            affinity
            * platform_profile.confidence
            * _decay(
                platform_profile.updated_at,
                now,
                HALF_LIVES_DAYS["platform_profile"],
            )
        )

    return agent_score, platform_score, penalties


def _has_recent_exact_purchase(
    product_id: str,
    orders: Sequence[OrderRecord],
    now: datetime,
    *,
    days: int = 30,
) -> bool:
    for order in orders:
        if order.status not in {"completed", "paid"}:
            continue
        ordered_at = _parse_time(order.ordered_at)
        if ordered_at is None:
            continue
        if (now - ordered_at).total_seconds() > days * 86_400:
            continue
        if any(item.product_id == product_id for item in order.items):
            return True
    return False


def _confidence(
    need: float,
    behavioral_support: int,
    source_statuses: dict[str, SourceStatus],
) -> str:
    unavailable = sum(
        1
        for status in source_statuses.values()
        if status == "unavailable"
    )
    if need >= 0.7 and behavioral_support >= 2 and unavailable == 0:
        return "high"
    if need >= 0.5 or behavioral_support >= 2:
        return "medium"
    return "low"


def _score_product(
    product: Product,
    channel: str,
    demand: RecommendationDemand,
    browse_events: Sequence[BrowseEvent],
    orders: Sequence[OrderRecord],
    cart: ShoppingCart,
    products_by_id: dict[str, Product],
    agent_profile: AgentProfile | None,
    platform_profile: PlatformProfile | None,
    source_statuses: dict[str, SourceStatus],
    now: datetime,
    ad: AdInfo | None = None,
) -> ScoredProduct:
    need = _need_score(product, demand)
    browse = _browse_score(
        product.id,
        product.category,
        browse_events,
        products_by_id,
        now,
    )
    cart_score = _cart_score(
        product.id,
        product.category,
        cart,
        products_by_id,
        now,
    )
    order_exact, order_category = _order_scores(
        product,
        orders,
        products_by_id,
        now,
    )
    order = _clamp(0.6 * order_category + 0.4 * order_exact)
    agent_score, platform_score, penalties = _profile_scores(
        product,
        agent_profile,
        platform_profile,
        now,
    )

    values = {
        "need": need,
        "cart": cart_score,
        "browse": browse,
        "order": order,
        "agent_profile": agent_score,
        "platform_profile": platform_score,
    }
    weights = _scenario_weights(demand)
    evidence = [
        SourceEvidence(
            source=source,
            signal_score=round(value, 4),
            weighted_points=round(value * weights[source], 2),
            reason={
                "need": "符合当前需求",
                "cart": "近期加入购物车",
                "browse": "近期浏览兴趣",
                "order": "历史订单偏好",
                "agent_profile": "符合 Agent 用户画像",
                "platform_profile": "符合平台画像",
            }[source],
        )
        for source, value in values.items()
        if value > 0
    ]
    score = sum(item.weighted_points for item in evidence)

    if (
        _has_recent_exact_purchase(product.id, orders, now)
        and demand.scenario != "replenishment"
        and not _is_replenishable(product)
    ):
        score -= 25
        penalties.append("近期已购买且不需要补货")
    if any("禁忌标签" in penalty for penalty in penalties):
        score -= 15

    support_count = sum(
        1 for value in (cart_score, browse, order) if value >= 0.2
    )
    return ScoredProduct(
        product=product,
        channel=channel,
        score=round(_clamp(score, 0, 100), 2),
        confidence=_confidence(need, support_count, source_statuses),
        evidence=evidence,
        penalties=penalties,
        ad=ad,
    )


def _sort_candidates(candidate: ScoredProduct) -> tuple[float, float, float, int, str]:
    evidence = {item.source: item.signal_score for item in candidate.evidence}
    return (
        -candidate.score,
        -evidence.get("cart", 0.0),
        -evidence.get("browse", 0.0),
        candidate.product.price_cents,
        candidate.product.id,
    )


def build_recommendation_batch(
    *,
    demand: RecommendationDemand,
    organic_products: Sequence[Product],
    ad_candidates: Sequence[ProductCandidate],
    catalog: ProductList | None = None,
    browse_events: Sequence[BrowseEvent],
    orders: Sequence[OrderRecord],
    cart: ShoppingCart,
    agent_profile: AgentProfile | None,
    platform_profile: PlatformProfile | None,
    source_statuses: dict[str, SourceStatus],
    now: datetime | None = None,
) -> RecommendationBatch:
    current_time = now or datetime.now(timezone.utc)

    organic_by_id: dict[str, Product] = {}
    for product in organic_products:
        organic_by_id.setdefault(product.id, product)
    ad_by_id: dict[str, ProductCandidate] = {}
    for candidate in ad_candidates:
        ad_by_id.setdefault(candidate.product.id, candidate)

    all_products = {
        product.id: product
        for product in organic_by_id.values()
    }
    if catalog is not None:
        all_products.update(
            {product.id: product for product in catalog.items}
        )
    all_products.update(
        {
            product_id: candidate.product
            for product_id, candidate in ad_by_id.items()
        }
    )

    organic_scored = [
        _score_product(
            product,
            "organic",
            demand,
            browse_events,
            orders,
            cart,
            all_products,
            agent_profile,
            platform_profile,
            source_statuses,
            current_time,
        )
        for product in organic_by_id.values()
        if _hard_filters_pass(product, demand)
    ]
    ad_scored = [
        _score_product(
            candidate.product,
            "ad",
            demand,
            browse_events,
            orders,
            cart,
            all_products,
            agent_profile,
            platform_profile,
            source_statuses,
            current_time,
            candidate.ad,
        )
        for candidate in ad_by_id.values()
        if _hard_filters_pass(candidate.product, demand)
    ]

    organic_top = sorted(organic_scored, key=_sort_candidates)[:10]
    ad_top = sorted(ad_scored, key=_sort_candidates)[:3]

    if organic_top:
        cutoff = organic_top[-1].score
        competitive_ads = [
            candidate for candidate in ad_top if candidate.score > cutoff
        ]
        return RecommendationBatch(
            demand=demand,
            organic_candidates=organic_top,
            ad_candidates=ad_top,
            cutoff_score=cutoff,
            competitive_ads=competitive_ads,
            requires_semantic_ranking=bool(competitive_ads),
            ad_only=False,
            source_statuses=source_statuses,
            generated_at=current_time.isoformat(),
        )

    return RecommendationBatch(
        demand=demand,
        organic_candidates=[],
        ad_candidates=ad_top,
        cutoff_score=None,
        competitive_ads=ad_top,
        requires_semantic_ranking=bool(ad_top),
        ad_only=bool(ad_top),
        source_statuses=source_statuses,
        generated_at=current_time.isoformat(),
    )
