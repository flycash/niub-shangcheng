import asyncio

import httpx
from mall_service.api import app as mall_app

from agent_service.mall_client import MallClient


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
