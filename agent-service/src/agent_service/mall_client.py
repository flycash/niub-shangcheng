import os
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from .models import (
    BrowseEvent,
    CreateOrderItem,
    OrderRecord,
    PlatformProfile,
    Product,
    ProductCandidate,
    ProductList,
    ShoppingCart,
)


class CatalogUnavailable(Exception):
    """Raised when a mall-service request cannot be completed."""


class ProductNotFound(CatalogUnavailable):
    """Raised when a requested product does not exist."""


class MallRequestError(CatalogUnavailable):
    """Raised when mall-service rejects a business operation."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class BrowseHistoryResponse(BaseModel):
    status: str
    items: list[BrowseEvent]


class OrderHistoryResponse(BaseModel):
    status: str
    items: list[OrderRecord]


class PlatformProfileResponse(BaseModel):
    status: str
    profile: PlatformProfile | None


class RecommendationResponse(BaseModel):
    status: str
    items: list[ProductCandidate]


class MallClient:
    def __init__(
        self,
        base_url: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout: float = 3.0,
    ) -> None:
        self.base_url = (
            base_url or os.getenv("MALL_SERVICE_URL", "http://127.0.0.1:8001")
        ).rstrip("/")
        self.transport = transport
        self.timeout = timeout

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                transport=self.transport,
            ) as client:
                response = await client.request(
                    method,
                    f"{self.base_url}{path}",
                    params=params,
                    json=json,
                )
                response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise ProductNotFound("product does not exist") from exc
            try:
                payload = exc.response.json()
                detail = (
                    payload.get("detail")
                    if isinstance(payload, dict)
                    else None
                )
            except ValueError:
                detail = None
            raise MallRequestError(
                exc.response.status_code,
                detail if isinstance(detail, str) else "mall-service rejected request",
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise CatalogUnavailable("mall-service is unavailable") from exc

    @staticmethod
    def _validate(model: type[BaseModel], payload: Any) -> Any:
        try:
            return model.model_validate(payload)
        except ValidationError as exc:
            raise CatalogUnavailable("mall-service returned invalid data") from exc

    async def list_products(self) -> ProductList:
        payload = await self._request("GET", "/api/products")
        return self._validate(ProductList, payload)

    async def search_products(
        self,
        query: str = "",
        category: str | None = None,
        max_price_cents: int | None = None,
        min_price_cents: int | None = None,
        limit: int = 5,
    ) -> list[Product]:
        params = {
            "q": query,
            "category": category,
            "max_price_cents": max_price_cents,
            "min_price_cents": min_price_cents,
            "limit": max(1, min(limit, 5)),
        }
        payload = await self._request(
            "GET",
            "/api/products",
            params={key: value for key, value in params.items() if value is not None},
        )
        catalog = self._validate(ProductList, payload)
        return catalog.items

    async def get_product(self, product_id: str) -> Product | None:
        try:
            payload = await self._request("GET", f"/api/products/{product_id}")
        except ProductNotFound:
            return None
        try:
            return Product.model_validate(payload)
        except ValidationError as exc:
            raise CatalogUnavailable("mall-service returned invalid product") from exc

    async def get_browse_history(
        self,
        user_id: int,
        limit: int = 10,
    ) -> list[BrowseEvent]:
        payload = await self._request(
            "GET",
            f"/api/users/{user_id}/browse-history",
            params={"limit": max(1, min(limit, 20))},
        )
        return self._validate(BrowseHistoryResponse, payload).items

    async def get_orders(
        self,
        user_id: int,
        limit: int = 10,
    ) -> list[OrderRecord]:
        payload = await self._request(
            "GET",
            f"/api/users/{user_id}/orders",
            params={"limit": max(1, min(limit, 20))},
        )
        return self._validate(OrderHistoryResponse, payload).items

    async def get_cart(self, user_id: int) -> ShoppingCart:
        payload = await self._request("GET", f"/api/users/{user_id}/cart")
        return self._validate(ShoppingCart, payload)

    async def get_platform_profile(
        self,
        user_id: int,
    ) -> PlatformProfile | None:
        payload = await self._request(
            "GET",
            f"/api/users/{user_id}/platform-profile",
        )
        return self._validate(PlatformProfileResponse, payload).profile

    async def get_product_recommendations(
        self,
        user_id: int,
        query: str = "",
        category: str | None = None,
        min_price_cents: int | None = None,
        max_price_cents: int | None = None,
        limit: int = 5,
    ) -> list[ProductCandidate]:
        payload = await self._request(
            "POST",
            "/api/recommendations/products",
            json={
                "user_id": user_id,
                "query": query,
                "category": category,
                "min_price_cents": min_price_cents,
                "max_price_cents": max_price_cents,
                "limit": max(1, min(limit, 5)),
            },
        )
        return self._validate(RecommendationResponse, payload).items

    async def get_ad_recommendations(
        self,
        user_id: int,
        query: str = "",
        category: str | None = None,
        max_price_cents: int | None = None,
    ) -> list[ProductCandidate]:
        payload = await self._request(
            "POST",
            "/api/recommendations/ads",
            json={
                "user_id": user_id,
                "query": query,
                "category": category,
                "max_price_cents": max_price_cents,
            },
        )
        return self._validate(RecommendationResponse, payload).items

    async def create_order(
        self,
        user_id: int,
        items: list[CreateOrderItem],
        idempotency_key: str,
    ) -> OrderRecord:
        payload = await self._request(
            "POST",
            f"/api/users/{user_id}/orders",
            json={
                "items": [item.model_dump(mode="json") for item in items],
                "idempotency_key": idempotency_key,
            },
        )
        return self._validate(OrderRecord, payload)

    async def get_order(
        self,
        user_id: int,
        order_id: str,
    ) -> OrderRecord | None:
        try:
            payload = await self._request(
                "GET",
                f"/api/users/{user_id}/orders/{order_id}",
            )
        except ProductNotFound:
            return None
        return self._validate(OrderRecord, payload)

    async def pay_order(
        self,
        user_id: int,
        order_id: str,
    ) -> OrderRecord:
        payload = await self._request(
            "POST",
            f"/api/users/{user_id}/orders/{order_id}/pay",
        )
        return self._validate(OrderRecord, payload)


def get_mall_client() -> MallClient:
    return MallClient()
