from pydantic import BaseModel


class Product(BaseModel):
    id: str
    name: str
    description: str
    price_cents: int
    category: str
    badge: str | None = None


class ProductList(BaseModel):
    items: list[Product]
    total: int
