import asyncio

import httpx
from mall_service.api import app as mall_app

from agent_service.mall_client import MallClient


def test_agent_can_read_mall_catalog_api() -> None:
    client = MallClient(
        base_url="http://mall.test",
        transport=httpx.ASGITransport(app=mall_app),
    )

    catalog = asyncio.run(client.list_products())

    assert catalog.total == 3
    assert catalog.items[0].name == "山野抹茶气泡水"
