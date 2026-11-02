from .catalog import PRODUCTS, search_products
from .mock_data import BROWSE_HISTORY, CARTS, PLATFORM_PROFILES
from .models import (
    AdInfo,
    AdRecommendationRequest,
    ProductCandidate,
    ProductRecommendationRequest,
)
from .orders import list_user_orders


def _profile_affinity(user_id: int, category: str) -> float:
    profile = PLATFORM_PROFILES.get(user_id)
    if profile is None:
        return 0
    return next(
        (
            item.score
            for item in profile.category_affinity
            if item.category == category
        ),
        0,
    )


def _recommend_scores(user_id: int) -> dict[str, tuple[float, list[str]]]:
    scores: dict[str, tuple[float, list[str]]] = {}
    browse_by_product: dict[str, int] = {}
    dwell_by_product: dict[str, int] = {}
    for event in BROWSE_HISTORY.get(user_id, []):
        browse_by_product[event.product_id] = (
            browse_by_product.get(event.product_id, 0) + 1
        )
        dwell_by_product[event.product_id] = (
            dwell_by_product.get(event.product_id, 0) + event.dwell_seconds
        )

    cart_ids = {
        item.product_id for item in CARTS.get(user_id, None).items
    } if user_id in CARTS else set()
    ordered_ids = {
        item.product_id
        for order in list_user_orders(user_id)
        if order.status in {"paid", "completed"}
        for item in order.items
    }
    for product in PRODUCTS:
        score = 0.35
        signals: list[str] = []
        if product.id in browse_by_product:
            score += min(0.2, browse_by_product[product.id] * 0.06)
            score += min(0.08, dwell_by_product[product.id] / 600)
            signals.append("最近浏览")
        if product.id in cart_ids:
            score += 0.18
            signals.append("已在购物车")
        if product.id in ordered_ids:
            score += 0.08
            signals.append("历史购买")
        affinity = _profile_affinity(user_id, product.category)
        if affinity:
            score += affinity * 0.2
            signals.append("平台品类偏好")
        scores[product.id] = (min(score, 0.99), signals)
    return scores


def recommend_products(
    request: ProductRecommendationRequest,
) -> list[ProductCandidate]:
    products = search_products(
        query=request.query,
        category=request.category,
        max_price_cents=request.max_price_cents,
        min_price_cents=request.min_price_cents,
        limit=5,
    )
    scores = _recommend_scores(request.user_id)
    candidates = [
        ProductCandidate(
            product=product,
            source="product_recommendation",
            score=scores[product.id][0],
            matched_signals=scores[product.id][1],
        )
        for product in products
    ]
    candidates.sort(key=lambda item: (-item.score, item.product.price_cents))
    return candidates[: request.limit]


def recommend_ads(request: AdRecommendationRequest) -> list[ProductCandidate]:
    if request.user_id not in PLATFORM_PROFILES:
        return []
    products = search_products(
        query=request.query,
        category=request.category,
        max_price_cents=request.max_price_cents,
        limit=1,
    )
    if not products:
        return []
    product = products[0]
    return [
        ProductCandidate(
            product=product,
            source="advertisement",
            score=0.62,
            matched_signals=["广告投放匹配"],
            ad=AdInfo(
                ad_id="ad-1001",
                campaign_id="campaign-autumn-2026",
            ),
        )
    ]
