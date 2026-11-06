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
