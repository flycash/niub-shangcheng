from fastapi.testclient import TestClient

from mall_service.api import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "mall-service"


def test_list_products() -> None:
    response = client.get("/api/products")

    assert response.status_code == 200
    assert response.json()["total"] == 3


def test_filter_products() -> None:
    response = client.get("/api/products", params={"q": "家居"})

    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == "moon-lamp"


def test_unknown_product_returns_404() -> None:
    response = client.get("/api/products/missing")

    assert response.status_code == 404
