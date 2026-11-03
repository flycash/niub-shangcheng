from .models import Product


PRODUCTS = (
    Product(
        id="commuter-backpack",
        name="轻旅通勤双肩包",
        description="轻量防泼水面料，独立电脑夹层，适合日常通勤。",
        price_cents=29900,
        category="箱包",
        badge="通勤推荐",
        stock=18,
        tags=["通勤", "双肩包", "礼物", "电脑包"],
        image_url="/products/commuter-backpack.jpg",
    ),
    Product(
        id="canvas-tote",
        name="日常帆布托特包",
        description="厚实帆布与宽肩带，通勤和周末都能装。",
        price_cents=6900,
        category="箱包",
        badge="人气单品",
        stock=36,
        tags=["通勤", "托特包", "帆布", "礼物"],
        image_url="/products/canvas-tote.jpg",
    ),
    Product(
        id="moon-lamp",
        name="月影桌面灯",
        description="三档暖光，轻触调光，让桌面安静下来。",
        price_cents=12900,
        category="家居",
        badge="氛围好物",
        stock=12,
        tags=["居家", "台灯", "卧室", "礼物"],
        image_url="/products/moon-lamp.jpg",
    ),
    Product(
        id="matcha-soda",
        name="山野抹茶气泡水",
        description="低糖抹茶与细密气泡，午后喝一口刚刚好。",
        price_cents=1580,
        category="饮品",
        badge="本周新品",
        stock=80,
        tags=["饮品", "低糖", "抹茶", "夏日"],
        image_url="/products/matcha-soda.jpg",
    ),
    Product(
        id="hand-cream",
        name="木质香护手霜",
        description="滋润不黏腻，木质香调适合秋冬使用。",
        price_cents=4900,
        category="个护",
        badge="贴心礼物",
        stock=42,
        tags=["礼物", "护手霜", "香氛", "秋冬"],
        image_url="/products/hand-cream.jpg",
    ),
    Product(
        id="ceramic-mug",
        name="手作奶油陶瓷杯",
        description="温润奶油釉色，适合咖啡、茶和热牛奶。",
        price_cents=7900,
        category="家居",
        stock=25,
        tags=["杯子", "咖啡", "居家", "礼物"],
        image_url="/products/ceramic-mug.jpg",
    ),
    Product(
        id="linen-notebook",
        name="亚麻布面笔记本",
        description="平摊装订与细腻纸张，记录每天的灵感。",
        price_cents=3900,
        category="文创",
        stock=54,
        tags=["文具", "笔记本", "礼物", "通勤"],
        image_url="/products/linen-notebook.jpg",
    ),
    Product(
        id="portable-coffee",
        name="冷萃便携咖啡液",
        description="三秒速溶的清爽冷萃，办公室也能轻松喝。",
        price_cents=3600,
        category="饮品",
        stock=64,
        tags=["咖啡", "冷萃", "办公室", "通勤"],
        image_url="/products/portable-coffee.jpg",
    ),
    Product(
        id="linen-pillow",
        name="亚麻云朵靠枕",
        description="柔软支撑与可拆洗外套，让沙发更舒服。",
        price_cents=9900,
        category="家居",
        stock=20,
        tags=["靠枕", "居家", "客厅", "沙发"],
        image_url="/products/linen-pillow.jpg",
    ),
    Product(
        id="travel-bottle",
        name="保温随行杯",
        description="轻巧密封，保冷保温，适合通勤和短途出行。",
        price_cents=11900,
        category="家居",
        stock=31,
        tags=["水杯", "保温", "通勤", "旅行"],
        image_url="/products/travel-bottle.jpg",
    ),
)

STOP_WORDS = (
    "推荐",
    "帮我",
    "一下",
    "商品",
    "好物",
    "想要",
    "想买",
    "有没有",
    "什么",
)


def get_product(product_id: str) -> Product | None:
    return next((product for product in PRODUCTS if product.id == product_id), None)


def search_products(
    query: str | None = None,
    category: str | None = None,
    max_price_cents: int | None = None,
    min_price_cents: int | None = None,
    limit: int = 5,
) -> list[Product]:
    clean_query = (query or "").strip().lower()
    for stop_word in STOP_WORDS:
        clean_query = clean_query.replace(stop_word, " ")
    terms = [term for term in clean_query.split() if term]

    candidates: list[tuple[int, Product]] = []
    for product in PRODUCTS:
        if category and category.lower() not in product.category.lower():
            continue
        if max_price_cents is not None and product.price_cents > max_price_cents:
            continue
        if min_price_cents is not None and product.price_cents < min_price_cents:
            continue

        searchable = " ".join(
            [
                product.name,
                product.description,
                product.category,
                *product.tags,
            ]
        ).lower()
        score = sum(1 for term in terms if term in searchable)
        if terms and score == 0:
            continue
        candidates.append((score, product))

    if terms:
        candidates.sort(key=lambda item: (-item[0], item[1].price_cents))
    return [product for _, product in candidates[: max(1, min(limit, 10))]]
