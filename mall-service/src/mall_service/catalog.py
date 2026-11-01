from .models import Product

PRODUCTS = (
    Product(
        id="matcha-soda",
        name="山野抹茶气泡水",
        description="低糖抹茶与细密气泡，午后喝一口刚刚好。",
        price_cents=1580,
        category="饮品",
        badge="本周新品",
    ),
    Product(
        id="canvas-tote",
        name="日常帆布托特包",
        description="厚实帆布与宽肩带，通勤和周末都能装。",
        price_cents=6900,
        category="文创",
        badge="人气单品",
    ),
    Product(
        id="moon-lamp",
        name="月影桌面灯",
        description="三档暖光，轻触调光，让桌面安静下来。",
        price_cents=12900,
        category="家居",
    ),
)


def search_products(query: str | None = None) -> list[Product]:
    if not query:
        return list(PRODUCTS)

    keyword = query.strip().lower()
    return [
        product
        for product in PRODUCTS
        if keyword in product.name.lower()
        or keyword in product.description.lower()
        or keyword in product.category.lower()
    ]
