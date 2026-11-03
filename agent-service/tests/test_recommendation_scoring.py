from datetime import datetime, timedelta, timezone

from agent_service.models import (
    AdInfo,
    AgentProfile,
    BrowseEvent,
    CartItem,
    OrderItem,
    OrderRecord,
    PlatformProfile,
    Product,
    ProductCandidate,
    RecommendationDemand,
    ShoppingCart,
)
from agent_service.recommendation_scoring import build_recommendation_batch


NOW = datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc)


def product(
    product_id: str,
    *,
    category: str = "家居",
    price_cents: int = 10_000,
    stock: int = 10,
    tags: list[str] | None = None,
) -> Product:
    return Product(
        id=product_id,
        name=product_id,
        description=f"{product_id} description",
        price_cents=price_cents,
        category=category,
        stock=stock,
        tags=tags or [],
    )


def ad_candidate(product_value: Product) -> ProductCandidate:
    return ProductCandidate(
        product=product_value,
        source="advertisement",
        score=0.62,
        ad=AdInfo(ad_id="ad-1", campaign_id="campaign-1"),
    )


def build_batch(
    organic: list[Product],
    ads: list[ProductCandidate] | None = None,
    *,
    demand: RecommendationDemand | None = None,
    cart: ShoppingCart | None = None,
    browse: list[BrowseEvent] | None = None,
    source_statuses: dict[str, str] | None = None,
):
    return build_recommendation_batch(
        demand=demand or RecommendationDemand(),
        organic_products=organic,
        ad_candidates=ads or [],
        browse_events=browse or [],
        orders=[],
        cart=cart or ShoppingCart(),
        agent_profile=None,
        platform_profile=None,
        source_statuses=source_statuses or {"cart": "ok_empty"},
        now=NOW,
    )


def test_cart_signal_outranks_browsing_for_equivalent_products() -> None:
    cart_product = product("cart-product")
    browse_product = product("browse-product")
    cart = ShoppingCart(
        items=[
            CartItem(
                product_id="cart-product",
                quantity=1,
                added_at=(NOW - timedelta(hours=2)).isoformat(),
            )
        ]
    )
    browse = [
        BrowseEvent(
            event_id="event-1",
            product_id="browse-product",
            action="detail_view",
            occurred_at=(NOW - timedelta(hours=2)).isoformat(),
            dwell_seconds=120,
            source_page="search",
        )
    ]

    batch = build_batch(
        [cart_product, browse_product],
        cart=cart,
        browse=browse,
    )

    assert batch.organic_candidates[0].product.id == "cart-product"
    assert (
        batch.organic_candidates[0].score
        > batch.organic_candidates[1].score
    )


def test_ad_must_strictly_exceed_organic_cutoff() -> None:
    organic = product("organic")
    equal_ad = ad_candidate(product("equal-ad"))
    higher_ad = ad_candidate(product("higher-ad"))
    browse = [
        BrowseEvent(
            event_id="event-ad",
            product_id="higher-ad",
            action="detail_view",
            occurred_at=(NOW - timedelta(hours=1)).isoformat(),
            dwell_seconds=120,
            source_page="ad",
        )
    ]

    batch = build_batch(
        [organic],
        [equal_ad, higher_ad],
        browse=browse,
    )

    assert len(batch.ad_candidates) == 2
    assert [candidate.product.id for candidate in batch.competitive_ads] == [
        "higher-ad"
    ]
    assert batch.requires_semantic_ranking is True


def test_natural_candidates_are_limited_to_ten_and_ads_to_three() -> None:
    organic = [product(f"organic-{index}") for index in range(12)]
    ads = [
        ad_candidate(product(f"ad-{index}"))
        for index in range(4)
    ]

    batch = build_batch(organic, ads)

    assert len(batch.organic_candidates) == 10
    assert len(batch.ad_candidates) == 3


def test_ad_only_path_requires_semantic_ranking() -> None:
    ads = [ad_candidate(product("ad-only"))]

    batch = build_batch([], ads)

    assert batch.ad_only is True
    assert batch.requires_semantic_ranking is True
    assert batch.cutoff_score is None
    assert [item.product.id for item in batch.competitive_ads] == ["ad-only"]


def test_hard_filters_remove_over_budget_out_of_stock_and_excluded_products() -> None:
    batch = build_batch(
        [
            product("valid", price_cents=10_000, tags=["礼物"]),
            product("over-budget", price_cents=30_000, tags=["礼物"]),
            product("out-of-stock", stock=0, tags=["礼物"]),
            product("excluded", tags=["礼物", "浓郁香精"]),
        ],
        demand=RecommendationDemand(
            max_price_cents=20_000,
            excluded_tags=["浓郁香精"],
        ),
    )

    assert [item.product.id for item in batch.organic_candidates] == ["valid"]


def test_product_present_in_both_paths_keeps_channel_identity() -> None:
    product_value = product("shared")

    batch = build_batch([product_value], [ad_candidate(product_value)])

    assert [item.product.id for item in batch.organic_candidates] == ["shared"]
    assert [item.product.id for item in batch.ad_candidates] == ["shared"]
    assert batch.requires_semantic_ranking is False


def test_platform_affinity_contributes_to_score() -> None:
    product_value = product("home-item", category="家居")
    platform = PlatformProfile(
        user_id=1,
        source="recommendation_platform",
        segments=[],
        category_affinity=[{"category": "家居", "score": 0.9}],
        confidence=0.8,
        updated_at=NOW.isoformat(),
    )

    with_profile = build_recommendation_batch(
        demand=RecommendationDemand(),
        organic_products=[product_value],
        ad_candidates=[],
        browse_events=[],
        orders=[],
        cart=ShoppingCart(),
        agent_profile=None,
        platform_profile=platform,
        source_statuses={"platform_profile": "ok_with_data"},
        now=NOW,
    )
    without_profile = build_batch([product_value])

    assert (
        with_profile.organic_candidates[0].score
        > without_profile.organic_candidates[0].score
    )


def test_gift_scenario_increases_current_need_weight() -> None:
    product_value = product("gift-item", tags=["礼物"])
    gift_batch = build_batch(
        [product_value],
        demand=RecommendationDemand(
            scenario="gift",
            recipient="朋友",
        ),
    )
    general_batch = build_batch([product_value])

    need = next(
        evidence
        for evidence in gift_batch.organic_candidates[0].evidence
        if evidence.source == "need"
    )
    general_need = next(
        evidence
        for evidence in general_batch.organic_candidates[0].evidence
        if evidence.source == "need"
    )
    assert need.weighted_points > general_need.weighted_points


def test_recent_durable_purchase_is_penalized() -> None:
    product_value = product("recently-bought", category="家居")
    order = OrderRecord(
        order_id="order-1",
        status="completed",
        ordered_at=(NOW - timedelta(days=1)).isoformat(),
        subtotal_cents=10_000,
        total_cents=10_000,
        items=[
            OrderItem(
                product_id=product_value.id,
                name=product_value.name,
                quantity=1,
                unit_price_cents=10_000,
                subtotal_cents=10_000,
            )
        ],
    )

    batch = build_recommendation_batch(
        demand=RecommendationDemand(),
        organic_products=[product_value],
        ad_candidates=[],
        browse_events=[],
        orders=[order],
        cart=ShoppingCart(),
        agent_profile=None,
        platform_profile=None,
        source_statuses={"orders": "ok_with_data"},
        now=NOW,
    )

    assert "近期已购买且不需要补货" in (
        batch.organic_candidates[0].penalties
    )


def test_agent_profile_is_time_decayed() -> None:
    product_value = product("preferred", category="家居")
    profile = AgentProfile(
        user_id=1,
        preferred_categories=["家居"],
        preferred_tags=[],
        avoid_tags=[],
        updated_at=(NOW - timedelta(days=90)).isoformat(),
    )
    batch = build_recommendation_batch(
        demand=RecommendationDemand(),
        organic_products=[product_value],
        ad_candidates=[],
        browse_events=[],
        orders=[],
        cart=ShoppingCart(),
        agent_profile=profile,
        platform_profile=None,
        source_statuses={"agent_profile": "ok_with_data"},
        now=NOW,
    )

    profile_evidence = next(
        item
        for item in batch.organic_candidates[0].evidence
        if item.source == "agent_profile"
    )
    assert profile_evidence.signal_score < 0.7
