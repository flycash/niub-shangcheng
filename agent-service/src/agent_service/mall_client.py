import os

import httpx

from .models import ProductList


class CatalogUnavailable(Exception):
    """Raised when the mall catalog cannot be reached."""


class MallClient:
    def __init__(
        self,
        base_url: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = (
            base_url or os.getenv("MALL_SERVICE_URL", "http://127.0.0.1:8001")
        ).rstrip("/")
        self.transport = transport

    async def list_products(self) -> ProductList:
        try:
            async with httpx.AsyncClient(
                timeout=3.0,
                transport=self.transport,
            ) as client:
                response = await client.get(f"{self.base_url}/api/products")
                response.raise_for_status()
            return ProductList.model_validate(response.json())
        except (httpx.HTTPError, ValueError) as exc:
            raise CatalogUnavailable("mall catalog is unavailable") from exc


def get_mall_client() -> MallClient:
    return MallClient()
