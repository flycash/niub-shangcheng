from typing import Annotated

from fastapi import FastAPI, HTTPException, Query

from .catalog import get_product as find_product
from .catalog import search_products
from .mock_data import BROWSE_HISTORY, CARTS, PLATFORM_PROFILES
from .models import (
    AdRecommendationRequest,
    BrowseHistory,
    Cart,
    CreateOrderRequest,
    Order,
    OrderHistory,
    PlatformProfileResponse,
    Product,
    ProductList,
    ProductRecommendationRequest,
    RecommendationSearchRequest,
    RecommendationResponse,
)
from .orders import (
    InsufficientStock,
    OrderConflict,
    OrderNotFound,
    create_order,
    get_order,
    list_user_orders,
    pay_order,
)
from .recommendations import recommend_ads, recommend_products
from .search import search_mock_ads_with_spec, search_mock_with_spec

app = FastAPI(title="Mall Service", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "mall-service"}


@app.get("/api/products", response_model=ProductList)
def list_products(
    q: Annotated[str | None, Query(max_length=100)] = None,
    category: Annotated[str | None, Query(max_length=50)] = None,
    max_price_cents: Annotated[int | None, Query(ge=0)] = None,
    min_price_cents: Annotated[int | None, Query(ge=0)] = None,
    limit: Annotated[int, Query(ge=1, le=10)] = 5,
) -> ProductList:
    products = search_products(
        q,
        category=category,
        max_price_cents=max_price_cents,
        min_price_cents=min_price_cents,
        limit=limit,
    )
    return ProductList(items=products, total=len(products))


@app.get("/api/products/{product_id}", response_model=Product)
def get_product(product_id: str) -> Product:
    product = find_product(product_id)
    if product is not None:
        return product
    raise HTTPException(status_code=404, detail="商品不存在")


@app.get(
    "/api/users/{user_id}/browse-history",
    response_model=BrowseHistory,
)
def get_browse_history(
    user_id: int,
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
) -> BrowseHistory:
    return BrowseHistory(items=BROWSE_HISTORY.get(user_id, [])[:limit])


@app.get("/api/users/{user_id}/orders", response_model=OrderHistory)
def get_orders(
    user_id: int,
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
) -> OrderHistory:
    return OrderHistory(items=list_user_orders(user_id)[:limit])


@app.post(
    "/api/users/{user_id}/orders",
    response_model=Order,
    status_code=201,
)
def create_user_order(user_id: int, request: CreateOrderRequest) -> Order:
    try:
        return create_order(
            user_id,
            request.items,
            request.idempotency_key,
        )
    except OrderNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InsufficientStock as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get(
    "/api/users/{user_id}/orders/{order_id}",
    response_model=Order,
)
def get_user_order(user_id: int, order_id: str) -> Order:
    order = get_order(user_id, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order


@app.post(
    "/api/users/{user_id}/orders/{order_id}/pay",
    response_model=Order,
)
def pay_user_order(user_id: int, order_id: str) -> Order:
    try:
        return pay_order(user_id, order_id)
    except OrderNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (OrderConflict, InsufficientStock) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/api/users/{user_id}/cart", response_model=Cart)
def get_cart(user_id: int) -> Cart:
    return CARTS.get(user_id, Cart(items=[]))


@app.get(
    "/api/users/{user_id}/platform-profile",
    response_model=PlatformProfileResponse,
)
def get_platform_profile(user_id: int) -> PlatformProfileResponse:
    return PlatformProfileResponse(profile=PLATFORM_PROFILES.get(user_id))


@app.post(
    "/api/recommendations/products",
    response_model=RecommendationResponse,
)
def get_product_recommendations(
    request: ProductRecommendationRequest,
) -> RecommendationResponse:
    return RecommendationResponse(items=recommend_products(request))


@app.post(
    "/api/recommendations/ads",
    response_model=RecommendationResponse,
)
def get_ad_recommendations(
    request: AdRecommendationRequest,
) -> RecommendationResponse:
    return RecommendationResponse(items=recommend_ads(request))


@app.post(
    "/api/search/organic",
    response_model=ProductList,
)
def search_organic_with_spec(
    request: RecommendationSearchRequest,
) -> ProductList:
    products = search_mock_with_spec(
        request.spec,
        channel="organic",
        limit=request.limit,
    )
    return ProductList(items=products, total=len(products))


@app.post(
    "/api/search/ads",
    response_model=RecommendationResponse,
)
def search_ads_with_spec(
    request: RecommendationSearchRequest,
) -> RecommendationResponse:
    candidates = search_mock_ads_with_spec(
        request.spec,
        limit=request.limit,
    )
    return RecommendationResponse(items=candidates)
