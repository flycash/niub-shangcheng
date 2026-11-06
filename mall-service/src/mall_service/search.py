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
