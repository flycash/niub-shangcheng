from .models import (
    BrowseEvent,
    Cart,
    CartItem,
    CategoryAffinity,
    Order,
    OrderItem,
    PlatformProfile,
)


BROWSE_HISTORY: dict[int, list[BrowseEvent]] = {
    1: [
        BrowseEvent(
            event_id="browse-1001",
            product_id="moon-lamp",
            action="detail_view",
            occurred_at="2026-11-02T09:10:00+08:00",
            dwell_seconds=48,
            source_page="search",
        ),
        BrowseEvent(
            event_id="browse-1002",
            product_id="commuter-backpack",
            action="view",
            occurred_at="2026-11-01T18:25:00+08:00",
            dwell_seconds=22,
            source_page="category",
        ),
        BrowseEvent(
            event_id="browse-1003",
            product_id="ceramic-mug",
            action="detail_view",
            occurred_at="2026-10-30T14:05:00+08:00",
            dwell_seconds=35,
            source_page="recommendation",
        ),
        BrowseEvent(
            event_id="browse-1004",
            product_id="matcha-soda",
            action="view",
            occurred_at="2026-10-28T16:40:00+08:00",
            dwell_seconds=12,
            source_page="home",
        ),
    ]
}


ORDERS: dict[int, list[Order]] = {
    1: [
        Order(
            order_id="order-1001",
            status="completed",
            ordered_at="2026-10-20T09:00:00+08:00",
            total_cents=14800,
            items=[
                OrderItem(
                    product_id="hand-cream",
                    name="木质香护手霜",
                    image_url="/products/hand-cream.jpg",
                    quantity=1,
                    unit_price_cents=4900,
                    subtotal_cents=4900,
                ),
                OrderItem(
                    product_id="linen-pillow",
                    name="亚麻云朵靠枕",
                    image_url="/products/linen-pillow.jpg",
                    quantity=1,
                    unit_price_cents=9900,
                    subtotal_cents=9900,
                ),
            ],
            subtotal_cents=14800,
        ),
        Order(
            order_id="order-1002",
            status="completed",
            ordered_at="2026-09-11T20:15:00+08:00",
            total_cents=3600,
            items=[
                OrderItem(
                    product_id="portable-coffee",
                    name="冷萃便携咖啡液",
                    image_url="/products/portable-coffee.jpg",
                    quantity=1,
                    unit_price_cents=3600,
                    subtotal_cents=3600,
                )
            ],
            subtotal_cents=3600,
        ),
    ]
}


CARTS: dict[int, Cart] = {
    1: Cart(
        updated_at="2026-11-02T09:20:00+08:00",
        items=[
            CartItem(
                product_id="commuter-backpack",
                quantity=1,
                added_at="2026-11-02T09:18:00+08:00",
            )
        ],
    )
}


PLATFORM_PROFILES: dict[int, PlatformProfile] = {
    1: PlatformProfile(
        user_id=1,
        segments=["都市通勤", "品质生活"],
        category_affinity=[
            CategoryAffinity(category="箱包", score=0.88),
            CategoryAffinity(category="家居", score=0.72),
            CategoryAffinity(category="个护", score=0.61),
        ],
        price_band_cents=(5000, 30000),
        preferred_tags=["通勤", "实用", "礼物"],
        confidence=0.76,
        updated_at="2026-11-02T06:00:00+08:00",
    )
}
