from agent_service.chat import compose_reply
from agent_service.models import Product


def test_reply_uses_catalog_products() -> None:
    products = [
        Product(
            id="matcha",
            name="抹茶气泡水",
            description="清爽",
            price_cents=1580,
            category="饮品",
        )
    ]

    assert "抹茶气泡水" in compose_reply("推荐一下", products)


def test_reply_handles_empty_catalog() -> None:
    assert "暂时" in compose_reply("推荐一下", [])
