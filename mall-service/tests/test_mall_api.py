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
    current_stock = next(
        product.stock for product in PRODUCTS if product.id == "travel-bottle"
    )
    assert current_stock == initial_stock - 1


def test_order_is_hidden_from_other_users() -> None:
    create_response = client.post(
        "/api/users/1/orders",
        json={
            "items": [{"product_id": "moon-lamp", "quantity": 1}],
            "idempotency_key": "checkout-private",
        },
    )
    order_id = create_response.json()["order_id"]

    other_user = client.get(f"/api/users/2/orders/{order_id}")

    assert other_user.status_code == 404


def test_create_order_rejects_missing_product() -> None:
    response = client.post(
        "/api/users/1/orders",
        json={
            "items": [{"product_id": "missing", "quantity": 1}],
            "idempotency_key": "checkout-missing",
        },
    )

    assert response.status_code == 404
