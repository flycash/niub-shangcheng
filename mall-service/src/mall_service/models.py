from typing import Literal

from pydantic import BaseModel, Field


class Product(BaseModel):
    id: str
    name: str
    description: str
    price_cents: int
    category: str
    badge: str | None = None
    stock: int | None = None
    tags: list[str] = Field(default_factory=list)
    image_url: str | None = None


class ProductList(BaseModel):
    items: list[Product]
    total: int


class BrowseEvent(BaseModel):
    event_id: str
    product_id: str
    action: Literal["view", "detail_view"]
    occurred_at: str
    dwell_seconds: int = Field(ge=0)
    source_page: str


class BrowseHistory(BaseModel):
    status: Literal["ok"] = "ok"
    items: list[BrowseEvent]


class OrderItem(BaseModel):
    product_id: str
    name: str
    image_url: str | None = None
    quantity: int = Field(gt=0)
    unit_price_cents: int = Field(ge=0)
    subtotal_cents: int = Field(ge=0)


class ShippingAddress(BaseModel):
    recipient: str
    phone_masked: str
    region: str
    detail: str


class Order(BaseModel):
    order_id: str
    user_id: int = 1
    status: Literal[
        "pending_payment",
        "paid",
        "completed",
        "cancelled",
        "refunded",
    ]
    ordered_at: str
    address: ShippingAddress | None = None
    subtotal_cents: int = Field(ge=0)
    shipping_fee_cents: int = Field(default=0, ge=0)
    total_cents: int = Field(ge=0)
    items: list[OrderItem]
    preview_path: str | None = None
    paid_at: str | None = None
    expires_at: str | None = None


class OrderHistory(BaseModel):
    status: Literal["ok"] = "ok"
    items: list[Order]


class CreateOrderItem(BaseModel):
    product_id: str = Field(min_length=1, max_length=100)
    quantity: int = Field(default=1, ge=1, le=99)


class CreateOrderRequest(BaseModel):
    items: list[CreateOrderItem] = Field(min_length=1, max_length=20)
    idempotency_key: str = Field(min_length=1, max_length=200)


class CartItem(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)
    added_at: str


class Cart(BaseModel):
    status: Literal["ok"] = "ok"
    updated_at: str | None = None
    items: list[CartItem]


class CategoryAffinity(BaseModel):
    category: str
    score: float = Field(ge=0, le=1)


class PlatformProfile(BaseModel):
    user_id: int
    source: Literal["recommendation_platform"] = "recommendation_platform"
    segments: list[str] = Field(default_factory=list)
    category_affinity: list[CategoryAffinity] = Field(default_factory=list)
    price_band_cents: tuple[int, int] | None = None
    preferred_tags: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0, ge=0, le=1)
    updated_at: str


class PlatformProfileResponse(BaseModel):
    status: Literal["ok"] = "ok"
    profile: PlatformProfile | None


class AdInfo(BaseModel):
    is_ad: Literal[True] = True
    ad_id: str
    campaign_id: str
    label: Literal["广告"] = "广告"


class ProductCandidate(BaseModel):
    product: Product
    source: Literal["product_recommendation", "advertisement"]
    score: float = Field(ge=0, le=1)
    matched_signals: list[str] = Field(default_factory=list)
    ad: AdInfo | None = None


class RecommendationResponse(BaseModel):
    status: Literal["ok"] = "ok"
    items: list[ProductCandidate]


class ProductRecommendationRequest(BaseModel):
    user_id: int
    query: str = Field(default="", max_length=200)
    category: str | None = Field(default=None, max_length=50)
    min_price_cents: int | None = Field(default=None, ge=0)
    max_price_cents: int | None = Field(default=None, ge=0)
    limit: int = Field(default=5, ge=1, le=10)


class AdRecommendationRequest(BaseModel):
    user_id: int
    query: str = Field(default="", max_length=200)
    category: str | None = Field(default=None, max_length=50)
    max_price_cents: int | None = Field(default=None, ge=0)
    limit: int = Field(default=10, ge=1, le=10)
