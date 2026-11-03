from typing import Protocol

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


class MallGateway(Protocol):
    async def list_products(self) -> ProductList: ...

    async def search_products(
        self,
        query: str = "",
        category: str | None = None,
        max_price_cents: int | None = None,
        min_price_cents: int | None = None,
        limit: int = 5,
    ) -> list[Product]: ...

    async def get_product(self, product_id: str) -> Product | None: ...

    async def get_browse_history(
        self,
        user_id: int,
        limit: int = 10,
    ) -> list[BrowseEvent]: ...

    async def get_orders(
        self,
        user_id: int,
        limit: int = 10,
    ) -> list[OrderRecord]: ...

    async def get_cart(self, user_id: int) -> ShoppingCart: ...

    async def get_platform_profile(
        self,
        user_id: int,
    ) -> PlatformProfile | None: ...

    async def get_product_recommendations(
        self,
        user_id: int,
        query: str = "",
        category: str | None = None,
        min_price_cents: int | None = None,
        max_price_cents: int | None = None,
        limit: int = 10,
    ) -> list[ProductCandidate]: ...

    async def get_ad_recommendations(
        self,
        user_id: int,
        query: str = "",
        category: str | None = None,
        max_price_cents: int | None = None,
        limit: int = 10,
    ) -> list[ProductCandidate]: ...

    async def create_order(
        self,
        user_id: int,
        items: list[CreateOrderItem],
        idempotency_key: str,
    ) -> OrderRecord: ...

    async def get_order(
        self,
        user_id: int,
        order_id: str,
    ) -> OrderRecord | None: ...

    async def pay_order(
        self,
        user_id: int,
        order_id: str,
    ) -> OrderRecord: ...
