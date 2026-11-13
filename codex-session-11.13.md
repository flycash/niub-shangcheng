# Codex conversation

## User

现在我们准备在 agent-service 里面引入用户画像相关的模块，但是现在我准备做第一个功能：历史对话总结。它要达成：1. 在总结这个历史对话的时候，能提取出来，推荐了一些什么商品，要注意保留商品的摘要/关键信息（商品的规格，如尺寸，颜色，品牌等，一般直接对标商品系统的标签或者商品详情介绍的关键内容）；2. 要提取用户对这些推荐商品的表态，比如说我不喜欢 XXX 或者我不喜欢 XXX 特性；3. 要提取用户表达的一般性的偏好。这是一个初步的想法，你基于这三点，扩展这个历史对话总结的功能/目标，输出你对这个需求的理解。

## Assistant

我会先快速看一下 `agent-service` 现有的会话、商品推荐和记忆相关结构，确保需求理解能贴合当前架构，然后给出一份可直接用于方案评审的功能定义和目标边界。

## Activity

    $ find . -maxdepth 2 -type d -name 'agent-service' -print
    ./agent-service
    ✓ • 0ms

## Activity

    $ pwd && rg --files -g 'AGENTS.md' -g '!node_modules' -g '!dist' -g '!build'
    /Users/mindeng/workspace/niub-shangcheng
    ✗ (1) • 733ms

## Activity

    $ git status --short --branch
    ## main
    ✓ • 0ms

## Activity

    $ rg --files agent-service | sed -n '1,160p'
    agent-service/src/agent_service/prompt_loader.py
    agent-service/src/agent_service/recommendation_scoring.py
    agent-service/src/agent_service/recommendation_spec.py
    agent-service/src/agent_service/llm_config.py
    agent-service/src/agent_service/main.py
    agent-service/src/agent_service/mall_client.py
    agent-service/src/agent_service/storage.py
    agent-service/src/agent_service/mall_gateway.py
    agent-service/src/agent_service/goal_understanding.py
    agent-service/src/agent_service/chat.py
    agent-service/src/agent_service/api.py
    agent-service/src/agent_service/observability/middleware.py
    agent-service/src/agent_service/observability/serialization.py
    agent-service/src/agent_service/observability/http.py
    agent-service/src/agent_service/observability/context.py
    agent-service/src/agent_service/observability/agents.py
    agent-service/src/agent_service/observability/spans.py
    agent-service/src/agent_service/observability/telemetry.py
    agent-service/src/agent_service/observability/__init__.py
    agent-service/src/agent_service/observability/log_exporters.py
    agent-service/src/agent_service/observability/database.py
    agent-service/src/agent_service/observability/config.py
    agent-service/src/agent_service/observability/metrics.py
    agent-service/src/agent_service/observability/logging.py
    agent-service/src/agent_service/__init__.py
    agent-service/src/agent_service/agent_runner.py
    agent-service/src/agent_service/recommendation_reranker.py
    agent-service/src/agent_service/models.py
    agent-service/src/agent_service/agent_profile.py
    agent-service/.env.example
    agent-service/prompts/recommendation_reranker.md
    agent-service/prompts/recommendation_spec.md
    agent-service/prompts/goal_understanding.md
    agent-service/prompts/shopping_agent.md
    agent-service/tests/test_mall_contract.py
    agent-service/tests/test_prompt_loader.py
    agent-service/tests/test_chat.py
    agent-service/tests/test_storage.py
    agent-service/tests/test_agent_runner.py
    agent-service/tests/test_observability.py
    agent-service/tests/test_recommendation_scoring.py
    agent-service/tests/conftest.py
    agent-service/tests/test_agent_api.py
    agent-service/tests/test_llm_config.py
    agent-service/pyproject.toml
    agent-service/config/llm.example.yaml
    ✓ • 0ms

## Activity

    $ rg -n "profile|画像|memory|记忆|summar|总结|recommend|推荐|product|商品" agent-service -g '!*.lock' -g '!node_modules' -g '!dist' | sed -n '1,220p'
    agent-service/tests/test_mall_contract.py:16:    catalog = asyncio.run(client.list_products())
    agent-service/tests/test_mall_contract.py:29:def test_agent_can_read_user_context_and_recommendations() -> None:
    agent-service/tests/test_mall_contract.py:37:            await client.get_platform_profile(1),
    agent-service/tests/test_mall_contract.py:38:            await client.get_product_recommendations(
    agent-service/tests/test_mall_contract.py:43:            await client.get_ad_recommendations(1, query="通勤"),
    agent-service/tests/test_mall_contract.py:46:    browse, orders, cart, profile, products, ads = asyncio.run(load_data())
    agent-service/tests/test_mall_contract.py:48:    assert browse[0].product_id == "moon-lamp"
    agent-service/tests/test_mall_contract.py:52:    assert historical_order.items[0].product_id == "hand-cream"
    agent-service/tests/test_mall_contract.py:53:    assert cart.items[0].product_id == "commuter-backpack"
    agent-service/tests/test_mall_contract.py:54:    assert profile is not None
    agent-service/tests/test_mall_contract.py:55:    assert len(products) <= 3
    agent-service/tests/test_mall_contract.py:62:        goal_summary="寻找通勤商品",
    agent-service/tests/test_mall_contract.py:80:    products, ads = asyncio.run(search())
    agent-service/tests/test_mall_contract.py:82:    assert products
    agent-service/tests/test_mall_contract.py:83:    assert all(product.price_cents <= 30000 for product in products)
    agent-service/tests/test_mall_contract.py:91:        goal_summary="用户跳过需求收集，按已有信息宽泛推荐",
    agent-service/tests/test_mall_contract.py:102:    products = asyncio.run(
    agent-service/tests/test_mall_contract.py:106:    assert len(products) > 1
    agent-service/tests/test_mall_contract.py:107:    assert len({product.category for product in products}) > 1
    agent-service/tests/test_mall_contract.py:108:    assert all(product.price_cents <= 10000 for product in products)
    agent-service/src/agent_service/storage.py:293:        recommendations = [
    agent-service/src/agent_service/storage.py:294:            Product.model_validate(product)
    agent-service/src/agent_service/storage.py:295:            for product in metadata.get("recommendations", [])
    agent-service/src/agent_service/storage.py:296:            if isinstance(product, dict)
    agent-service/src/agent_service/storage.py:317:        recommendation_spec: RecommendationSpec | None = None
    agent-service/src/agent_service/storage.py:318:        if isinstance(metadata.get("recommendation_spec"), dict):
    agent-service/src/agent_service/storage.py:320:                recommendation_spec = RecommendationSpec.model_validate(
    agent-service/src/agent_service/storage.py:321:                    metadata["recommendation_spec"]
    agent-service/src/agent_service/storage.py:324:                recommendation_spec = None
    agent-service/src/agent_service/storage.py:336:            recommendations=recommendations,
    agent-service/src/agent_service/storage.py:340:            recommendation_spec=recommendation_spec,
    agent-service/src/agent_service/chat.py:6:def compose_reply(message: str, products: Sequence[Product]) -> str:
    agent-service/src/agent_service/chat.py:8:    if not products:
    agent-service/src/agent_service/chat.py:9:        return "商城目录暂时没有可推荐的商品，请稍后再试。"
    agent-service/src/agent_service/chat.py:11:    names = "、".join(product.name for product in products[:3])
    agent-service/src/agent_service/recommendation_scoring.py:29:    "agent_profile": 6.0,
    agent-service/src/agent_service/recommendation_scoring.py:30:    "platform_profile": 4.0,
    agent-service/src/agent_service/recommendation_scoring.py:37:    "agent_profile": 45.0,
    agent-service/src/agent_service/recommendation_scoring.py:38:    "platform_profile": 30.0,
    agent-service/src/agent_service/recommendation_scoring.py:52:    "推荐",
    agent-service/src/agent_service/recommendation_scoring.py:55:    "商品",
    agent-service/src/agent_service/recommendation_scoring.py:98:        weights["agent_profile"] *= 0.8
    agent-service/src/agent_service/recommendation_scoring.py:99:        weights["platform_profile"] *= 0.8
    agent-service/src/agent_service/recommendation_scoring.py:131:def _searchable(product: Product) -> str:
    agent-service/src/agent_service/recommendation_scoring.py:134:            product.id,
    agent-service/src/agent_service/recommendation_scoring.py:135:            product.name,
    agent-service/src/agent_service/recommendation_scoring.py:136:            product.description,
    agent-service/src/agent_service/recommendation_scoring.py:137:            product.category,
    agent-service/src/agent_service/recommendation_scoring.py:138:            *product.tags,
    agent-service/src/agent_service/recommendation_scoring.py:143:def _need_score(product: Product, demand: RecommendationDemand) -> float:
    agent-service/src/agent_service/recommendation_scoring.py:145:    product_tags = _normalized_tags(product.tags)
    agent-service/src/agent_service/recommendation_scoring.py:146:    product_text = _searchable(product)
    agent-service/src/agent_service/recommendation_scoring.py:150:        hits = sum(1 for term in terms if term in product_text)
    agent-service/src/agent_service/recommendation_scoring.py:153:        components.append(1.0 if demand.category.lower() == product.category.lower() else 0.0)
    agent-service/src/agent_service/recommendation_scoring.py:156:        components.append(len(required & product_tags) / len(required))
    agent-service/src/agent_service/recommendation_scoring.py:158:        components.append(1.0 if "礼物" in product_tags else 0.35)
    agent-service/src/agent_service/recommendation_scoring.py:163:def _hard_filters_pass(product: Product, demand: RecommendationDemand) -> bool:
    agent-service/src/agent_service/recommendation_scoring.py:164:    if product.stock is not None and product.stock <= 0:
    agent-service/src/agent_service/recommendation_scoring.py:166:    if demand.category and demand.category.lower() != product.category.lower():
    agent-service/src/agent_service/recommendation_scoring.py:170:        and product.price_cents < demand.min_price_cents
    agent-service/src/agent_service/recommendation_scoring.py:175:        and product.price_cents > demand.max_price_cents
    agent-service/src/agent_service/recommendation_scoring.py:178:    tags = _normalized_tags(product.tags)
    agent-service/src/agent_service/recommendation_scoring.py:188:    product_id: str,
    agent-service/src/agent_service/recommendation_scoring.py:189:    product_category: str,
    agent-service/src/agent_service/recommendation_scoring.py:191:    products_by_id: dict[str, Product],
    agent-service/src/agent_service/recommendation_scoring.py:203:        if event.product_id == product_id:
    agent-service/src/agent_service/recommendation_scoring.py:205:        viewed_product = products_by_id.get(event.product_id)
    agent-service/src/agent_service/recommendation_scoring.py:207:            viewed_product is not None
    agent-service/src/agent_service/recommendation_scoring.py:208:            and viewed_product.category == product_category
    agent-service/src/agent_service/recommendation_scoring.py:218:    product_id: str,
    agent-service/src/agent_service/recommendation_scoring.py:219:    product_category: str,
    agent-service/src/agent_service/recommendation_scoring.py:221:    products_by_id: dict[str, Product],
    agent-service/src/agent_service/recommendation_scoring.py:230:        if item.product_id == product_id:
    agent-service/src/agent_service/recommendation_scoring.py:232:        cart_product = products_by_id.get(item.product_id)
    agent-service/src/agent_service/recommendation_scoring.py:234:            cart_product is not None
    agent-service/src/agent_service/recommendation_scoring.py:235:            and cart_product.category == product_category
    agent-service/src/agent_service/recommendation_scoring.py:244:def _is_replenishable(product: Product) -> bool:
    agent-service/src/agent_service/recommendation_scoring.py:246:        product.category in REPLENISHABLE_CATEGORIES
    agent-service/src/agent_service/recommendation_scoring.py:247:        or bool(_normalized_tags(product.tags) & REPLENISHABLE_TAGS)
    agent-service/src/agent_service/recommendation_scoring.py:252:    product: Product,
    agent-service/src/agent_service/recommendation_scoring.py:254:    products_by_id: dict[str, Product],
    agent-service/src/agent_service/recommendation_scoring.py:270:            if item.product_id == product.id:
    agent-service/src/agent_service/recommendation_scoring.py:272:            ordered_product = products_by_id.get(item.product_id)
    agent-service/src/agent_service/recommendation_scoring.py:274:                ordered_product is not None
    agent-service/src/agent_service/recommendation_scoring.py:275:                and ordered_product.category == product.category
    agent-service/src/agent_service/recommendation_scoring.py:284:def _profile_scores(
    agent-service/src/agent_service/recommendation_scoring.py:285:    product: Product,
    agent-service/src/agent_service/recommendation_scoring.py:286:    agent_profile: AgentProfile | None,
    agent-service/src/agent_service/recommendation_scoring.py:287:    platform_profile: PlatformProfile | None,
    agent-service/src/agent_service/recommendation_scoring.py:290:    product_tags = _normalized_tags(product.tags)
    agent-service/src/agent_service/recommendation_scoring.py:294:    if agent_profile is not None:
    agent-service/src/agent_service/recommendation_scoring.py:297:            if product.category in agent_profile.preferred_categories
    agent-service/src/agent_service/recommendation_scoring.py:300:        preferred_tags = _normalized_tags(agent_profile.preferred_tags)
    agent-service/src/agent_service/recommendation_scoring.py:302:            len(product_tags & preferred_tags) / len(preferred_tags)
    agent-service/src/agent_service/recommendation_scoring.py:309:                agent_profile.updated_at,
    agent-service/src/agent_service/recommendation_scoring.py:311:                HALF_LIVES_DAYS["agent_profile"],
    agent-service/src/agent_service/recommendation_scoring.py:314:        if product_tags & _normalized_tags(agent_profile.avoid_tags):
    agent-service/src/agent_service/recommendation_scoring.py:315:            penalties.append("命中 Agent 画像禁忌标签")
    agent-service/src/agent_service/recommendation_scoring.py:318:    if platform_profile is not None:
    agent-service/src/agent_service/recommendation_scoring.py:322:                for item in platform_profile.category_affinity
    agent-service/src/agent_service/recommendation_scoring.py:323:                if item.category == product.category
    agent-service/src/agent_service/recommendation_scoring.py:329:            * platform_profile.confidence
    agent-service/src/agent_service/recommendation_scoring.py:331:                platform_profile.updated_at,
    agent-service/src/agent_service/recommendation_scoring.py:333:                HALF_LIVES_DAYS["platform_profile"],
    agent-service/src/agent_service/recommendation_scoring.py:341:    product_id: str,
    agent-service/src/agent_service/recommendation_scoring.py:355:        if any(item.product_id == product_id for item in order.items):
    agent-service/src/agent_service/recommendation_scoring.py:377:def _score_product(
    agent-service/src/agent_service/recommendation_scoring.py:378:    product: Product,
    agent-service/src/agent_service/recommendation_scoring.py:384:    products_by_id: dict[str, Product],
    agent-service/src/agent_service/recommendation_scoring.py:385:    agent_profile: AgentProfile | None,
    agent-service/src/agent_service/recommendation_scoring.py:386:    platform_profile: PlatformProfile | None,
    agent-service/src/agent_service/recommendation_scoring.py:391:    need = _need_score(product, demand)
    agent-service/src/agent_service/recommendation_scoring.py:393:        product.id,
    agent-service/src/agent_service/recommendation_scoring.py:394:        product.category,
    agent-service/src/agent_service/recommendation_scoring.py:396:        products_by_id,
    agent-service/src/agent_service/recommendation_scoring.py:400:        product.id,
    agent-service/src/agent_service/recommendation_scoring.py:401:        product.category,
    agent-service/src/agent_service/recommendation_scoring.py:403:        products_by_id,
    agent-service/src/agent_service/recommendation_scoring.py:407:        product,
    agent-service/src/agent_service/recommendation_scoring.py:409:        products_by_id,
    agent-service/src/agent_service/recommendation_scoring.py:413:    agent_score, platform_score, penalties = _profile_scores(
    agent-service/src/agent_service/recommendation_scoring.py:414:        product,
    agent-service/src/agent_service/recommendation_scoring.py:415:        agent_profile,
    agent-service/src/agent_service/recommendation_scoring.py:416:        platform_profile,
    agent-service/src/agent_service/recommendation_scoring.py:425:        "agent_profile": agent_score,
    agent-service/src/agent_service/recommendation_scoring.py:426:        "platform_profile": platform_score,
    agent-service/src/agent_service/recommendation_scoring.py:439:                "agent_profile": "符合 Agent 用户画像",
    agent-service/src/agent_service/recommendation_scoring.py:440:                "platform_profile": "符合平台画像",
    agent-service/src/agent_service/recommendation_scoring.py:449:        _has_recent_exact_purchase(product.id, orders, now)
    agent-service/src/agent_service/recommendation_scoring.py:451:        and not _is_replenishable(product)
    agent-service/src/agent_service/recommendation_scoring.py:462:        product=product,
    agent-service/src/agent_service/recommendation_scoring.py:478:        candidate.product.price_cents,
    agent-service/src/agent_service/recommendation_scoring.py:479:        candidate.product.id,
    agent-service/src/agent_service/recommendation_scoring.py:483:def build_recommendation_batch(
    agent-service/src/agent_service/recommendation_scoring.py:486:    organic_products: Sequence[Product],
    agent-service/src/agent_service/recommendation_scoring.py:492:    agent_profile: AgentProfile | None,
    agent-service/src/agent_service/recommendation_scoring.py:493:    platform_profile: PlatformProfile | None,
    agent-service/src/agent_service/recommendation_scoring.py:500:    for product in organic_products:
    agent-service/src/agent_service/recommendation_scoring.py:501:        organic_by_id.setdefault(product.id, product)
    agent-service/src/agent_service/recommendation_scoring.py:504:        ad_by_id.setdefault(candidate.product.id, candidate)
    agent-service/src/agent_service/recommendation_scoring.py:506:    all_products = {
    agent-service/src/agent_service/recommendation_scoring.py:507:        product.id: product
    agent-service/src/agent_service/recommendation_scoring.py:508:        for product in organic_by_id.values()
    agent-service/src/agent_service/recommendation_scoring.py:511:        all_products.update(
    agent-service/src/agent_service/recommendation_scoring.py:512:            {product.id: product for product in catalog.items}
    agent-service/src/agent_service/recommendation_scoring.py:514:    all_products.update(
    agent-service/src/agent_service/recommendation_scoring.py:516:            product_id: candidate.product
    agent-service/src/agent_service/recommendation_scoring.py:517:            for product_id, candidate in ad_by_id.items()
    agent-service/src/agent_service/recommendation_scoring.py:522:        _score_product(
    agent-service/src/agent_service/recommendation_scoring.py:523:            product,
    agent-service/src/agent_service/recommendation_scoring.py:529:            all_products,
    agent-service/src/agent_service/recommendation_scoring.py:530:            agent_profile,
    agent-service/src/agent_service/recommendation_scoring.py:531:            platform_profile,
    agent-service/src/agent_service/recommendation_scoring.py:535:        for product in organic_by_id.values()
    agent-service/src/agent_service/recommendation_scoring.py:536:        if _hard_filters_pass(product, demand)
    agent-service/src/agent_service/recommendation_scoring.py:539:        _score_product(
    agent-service/src/agent_service/recommendation_scoring.py:540:            candidate.product,
    agent-service/src/agent_service/recommendation_scoring.py:546:            all_products,
    agent-service/src/agent_service/recommendation_scoring.py:547:            agent_profile,
    agent-service/src/agent_service/recommendation_scoring.py:548:            platform_profile,
    agent-service/src/agent_service/recommendation_scoring.py:554:        if _hard_filters_pass(candidate.product, demand)
    agent-service/config/llm.example.yaml:11:  # 推荐主流程和可能的独立语义终排至少需要 10 个模型/工具回合。
    agent-service/prompts/recommendation_reranker.md:1:# 商品推荐语义终排器
    agent-service/prompts/recommendation_reranker.md:3:你只负责对已经通过公式筛选和资格校验的商品候选进行语义终排，不负责查询商品、修改分数或创建订单。
    agent-service/prompts/recommendation_reranker.md:12:- `cutoff_score`：自然推荐最低分；
    agent-service/prompts/recommendation_reranker.md:13:- `ad_only`：是否没有自然推荐候选；
    agent-service/prompts/recommendation_reranker.md:14:- `candidates`：自然推荐和广告混排后的单一候选池，含公式分数、来源、证据、价格、
    agent-service/prompts/recommendation_reranker.md:17:只能选择 `candidates` 中出现的商品，不能添加新商品。
    agent-service/prompts/recommendation_reranker.md:19:不要将自然商品和广告商品分别排序。应在同一个候选池中完成统一比较，再应用下面
    agent-service/prompts/recommendation_reranker.md:26:3. 同时比较商品语义、实际场景、价格、库存、使用便利性、礼物属性、品类多样性和候选间的取舍。
    agent-service/prompts/recommendation_reranker.md:28:5. 推荐理由要具体，并结合分数证据与语义判断，不要只复述“分数最高”。
    agent-service/prompts/recommendation_reranker.md:33:- 自然推荐商品最多 2 个。
    agent-service/prompts/recommendation_reranker.md:34:- 广告商品最多 1 个。
    agent-service/prompts/recommendation_reranker.md:37:- 只要存在自然推荐候选，列表中第一个商品必须是自然推荐，广告只能排在自然推荐之后。
    agent-service/prompts/recommendation_reranker.md:38:- 只有 `ad_only = true` 时，广告才可以成为第一个或唯一商品。
    agent-service/prompts/recommendation_reranker.md:39:- 需要付出取舍时，优先保留更符合当前需求且理由清晰的自然商品。
    agent-service/prompts/recommendation_reranker.md:49:      "product_id": "商品 ID",
    agent-service/prompts/recommendation_reranker.md:51:      "reason": "最终推荐理由",
    agent-service/prompts/recommendation_reranker.md:55:  "summary": "一句话说明本次终排的核心取舍"
    agent-service/tests/test_chat.py:5:def test_reply_uses_catalog_products() -> None:
    agent-service/tests/test_chat.py:6:    products = [
    agent-service/tests/test_chat.py:16:    assert "抹茶气泡水" in compose_reply("推荐一下", products)
    agent-service/tests/test_chat.py:20:    assert "暂时" in compose_reply("推荐一下", [])
    agent-service/src/agent_service/mall_gateway.py:17:    async def list_products(self) -> ProductList: ...
    agent-service/src/agent_service/mall_gateway.py:19:    async def search_products(
    agent-service/src/agent_service/mall_gateway.py:34:    async def get_product(self, product_id: str) -> Product | None: ...
    agent-service/src/agent_service/mall_gateway.py:50:    async def get_platform_profile(
    agent-service/src/agent_service/mall_gateway.py:55:    async def get_product_recommendations(
    agent-service/src/agent_service/mall_gateway.py:65:    async def get_ad_recommendations(
    agent-service/src/agent_service/recommendation_reranker.py:22:    / "recommendation_reranker.md"
    agent-service/src/agent_service/recommendation_reranker.py:27:    """Raised when semantic recommendation reranking cannot be completed."""
    agent-service/src/agent_service/recommendation_reranker.py:50:            candidate.product.price_cents,
    agent-service/src/agent_service/recommendation_reranker.py:51:            candidate.product.id,
    agent-service/src/agent_service/recommendation_reranker.py:80:        (candidate.channel, candidate.product.id): candidate
    agent-service/src/agent_service/recommendation_reranker.py:85:        raise SemanticRerankError("reranker selected more than three products")
    agent-service/src/agent_service/recommendation_reranker.py:91:        raise SemanticRerankError("reranker selected more than two organic products")
    agent-service/src/agent_service/recommendation_reranker.py:93:        raise SemanticRerankError("reranker selected more than one ad product")
    agent-service/src/agent_service/recommendation_reranker.py:94:    if len({item.product_id for item in ranking.items}) != len(ranking.items):
    agent-service/src/agent_service/recommendation_reranker.py:95:        raise SemanticRerankError("reranker selected duplicate products")
    agent-service/src/agent_service/recommendation_reranker.py:102:            "ad product cannot be first when organic candidates exist"
    agent-service/src/agent_service/recommendation_reranker.py:106:        if (item.channel, item.product_id) not in by_channel_and_id:
    agent-service/src/agent_service/recommendation_reranker.py:108:                f"reranker selected an ineligible product: {item.product_id}"
    agent-service/src/agent_service/recommendation_reranker.py:140:            name="recommendation-semantic-reranker",
    agent-service/src/agent_service/recommendation_reranker.py:171:                "semantic recommendation reranker failed: "
    agent-service/src/agent_service/recommendation_reranker.py:177:                "semantic recommendation reranker returned non-text output"
    agent-service/src/agent_service/recommendation_reranker.py:185:                "semantic recommendation reranker returned invalid data"
    agent-service/src/agent_service/mall_client.py:26:    """Raised when a requested product does not exist."""
    agent-service/src/agent_service/mall_client.py:50:    profile: PlatformProfile | None
    agent-service/src/agent_service/mall_client.py:97:                raise ProductNotFound("product does not exist") from exc
    agent-service/src/agent_service/mall_client.py:121:    async def list_products(self) -> ProductList:
    agent-service/src/agent_service/mall_client.py:122:        payload = await self._request("GET", "/api/products")
    agent-service/src/agent_service/mall_client.py:125:    async def search_products(
    agent-service/src/agent_service/mall_client.py:142:            "/api/products",
    agent-service/src/agent_service/mall_client.py:164:    async def get_product(self, product_id: str) -> Product | None:
    agent-service/src/agent_service/mall_client.py:166:            payload = await self._request("GET", f"/api/products/{product_id}")
    agent-service/src/agent_service/mall_client.py:172:            raise CatalogUnavailable("mall-service returned invalid product") from exc
    agent-service/src/agent_service/mall_client.py:202:    async def get_platform_profile(
    agent-service/src/agent_service/mall_client.py:208:            f"/api/users/{user_id}/platform-profile",
    agent-service/src/agent_service/mall_client.py:210:        return self._validate(PlatformProfileResponse, payload).profile
    agent-service/src/agent_service/mall_client.py:212:    async def get_product_recommendations(
    ✓ • 0ms

## Activity

    $ find agent-service -maxdepth 2 -type f \( -name 'README*' -o -name 'pyproject.toml' -o -name 'package.json' -o -name 'go.mod' \) -print
    agent-service/pyproject.toml
    ✓ • 0ms

## Activity

    $ sed -n '1,240p' agent-service/src/agent_service/agent_profile.py
    from .models import AgentProfile
    
    
    AGENT_PROFILES: dict[int, AgentProfile] = {
        1: AgentProfile(
            user_id=1,
            preferred_categories=["箱包", "家居"],
            preferred_tags=["通勤", "低糖", "礼物"],
            avoid_tags=["浓郁香精"],
            budget_hint_cents=30000,
            notes="用户多次表达偏好实用型商品，也会关注适合送礼的设计。",
            updated_at="2026-11-01T10:00:00+08:00",
        )
    }
    
    
    def get_agent_profile(user_id: int) -> AgentProfile | None:
        return AGENT_PROFILES.get(user_id)
    ✓ • 0ms

## Activity

    $ sed -n '1,280p' agent-service/src/agent_service/models.py
    from typing import Literal
    
    from pydantic import BaseModel, Field, field_validator, model_validator
    
    
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
        is_ad: bool = False
        ad_label: str | None = None
        ad_id: str | None = None
        campaign_id: str | None = None
    
    
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
    
    
    class OrderRecord(BaseModel):
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
    
    
    class CreateOrderItem(BaseModel):
        product_id: str = Field(min_length=1, max_length=100)
        quantity: int = Field(default=1, ge=1, le=99)
    
    
    class OrderLink(BaseModel):
        order_id: str
        status: Literal[
            "pending_payment",
            "paid",
            "completed",
            "cancelled",
            "refunded",
        ]
        total_cents: int
        preview_path: str
        ordered_at: str
    
    
    class CartItem(BaseModel):
        product_id: str
        quantity: int = Field(gt=0)
        added_at: str
    
    
    class ShoppingCart(BaseModel):
        updated_at: str | None = None
        items: list[CartItem] = Field(default_factory=list)
    
    
    class AgentProfile(BaseModel):
        user_id: int
        source: Literal["agent_memory"] = "agent_memory"
        preferred_categories: list[str] = Field(default_factory=list)
        preferred_tags: list[str] = Field(default_factory=list)
        avoid_tags: list[str] = Field(default_factory=list)
        budget_hint_cents: int | None = None
        notes: str | None = None
        updated_at: str
    
    
    class CategoryAffinity(BaseModel):
        category: str
        score: float = Field(ge=0, le=1)
    
    
    class PlatformProfile(BaseModel):
        user_id: int
        source: Literal["recommendation_platform"]
        segments: list[str] = Field(default_factory=list)
        category_affinity: list[CategoryAffinity] = Field(default_factory=list)
        price_band_cents: tuple[int, int] | None = None
        preferred_tags: list[str] = Field(default_factory=list)
        confidence: float = Field(ge=0, le=1)
        updated_at: str
    
    
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
    
    
    class RecommendationDemand(BaseModel):
        query: str = Field(default="", max_length=500)
        category: str | None = Field(default=None, max_length=100)
        min_price_cents: int | None = Field(default=None, ge=0)
        max_price_cents: int | None = Field(default=None, ge=0)
        required_tags: list[str] = Field(default_factory=list)
        excluded_tags: list[str] = Field(default_factory=list)
        scenario: Literal[
            "general",
            "self",
            "gift",
            "replenishment",
        ] = "general"
        usage: str | None = Field(default=None, max_length=500)
        recipient: str | None = Field(default=None, max_length=200)
    
    
    IntentType = str
    
    
    RecommendationRequirementStatus = Literal[
        "collecting",
        "ready",
        "bypassed",
    ]
    
    
    class RecommendationRequirementSlots(BaseModel):
        query: str | None = Field(default=None, max_length=500)
        category: str | None = Field(default=None, max_length=100)
        min_price_cents: int | None = Field(default=None, ge=0)
        max_price_cents: int | None = Field(default=None, ge=0)
        required_tags: list[str] = Field(default_factory=list)
        excluded_tags: list[str] = Field(default_factory=list)
        scenario: Literal[
            "general",
            "self",
            "gift",
            "replenishment",
        ] | None = None
        usage: str | None = Field(default=None, max_length=500)
        recipient: str | None = Field(default=None, max_length=200)
    
    
    class RecommendationRequirementState(BaseModel):
        status: RecommendationRequirementStatus
        slots: RecommendationRequirementSlots = Field(
            default_factory=RecommendationRequirementSlots
        )
        next_question: str | None = Field(default=None, max_length=2_000)
        declined_requirements: list[str] = Field(default_factory=list)
        collection_reason: str | None = Field(default=None, max_length=2_000)
    
        @model_validator(mode="after")
        def question_matches_status(self) -> "RecommendationRequirementState":
            if self.status == "collecting":
                if not self.next_question or not self.next_question.strip():
                    raise ValueError(
                        "collecting recommendation requirements need a next question"
                    )
            elif self.next_question is not None:
                raise ValueError(
                    "ready or bypassed recommendation requirements cannot have a question"
                )
            return self
    
    
    class GoalUnderstandingDraft(BaseModel):
        intents: list[IntentType] = Field(min_length=1, max_length=5)
        goal: str = Field(min_length=1, max_length=2_000)
        confidence: float = Field(ge=0, le=1)
        slots: dict[str, object] = Field(default_factory=dict)
        missing_slots: list[str] = Field(default_factory=list)
        requires_clarification: bool = False
        clarification_question: str | None = Field(default=None, max_length=1_000)
        recommendation_requirements: RecommendationRequirementState | None = None
    
    
    class GoalUnderstandingResult(BaseModel):
        primary_intent: IntentType
        intents: list[IntentType] = Field(min_length=1, max_length=5)
        pending_intents: list[IntentType] = Field(default_factory=list)
        goal: str = Field(min_length=1, max_length=2_000)
        confidence: float = Field(ge=0, le=1)
        slots: dict[str, object] = Field(default_factory=dict)
        missing_slots: list[str] = Field(default_factory=list)
        requires_clarification: bool = False
        clarification_question: str | None = Field(default=None, max_length=1_000)
        pending_intent_question: str | None = Field(default=None, max_length=1_000)
        recommendation_requirements: RecommendationRequirementState | None = None
    
    
    class RecommendationSpecHardConstraints(BaseModel):
        category: str | None = Field(default=None, max_length=100)
        min_price_cents: int | None = Field(default=None, ge=0)
        max_price_cents: int | None = Field(default=None, ge=0)
        required_tags: list[str] = Field(default_factory=list)
        excluded_tags: list[str] = Field(default_factory=list)
    
    
    class RecommendationSpecEvidence(BaseModel):
        source: str = Field(min_length=1, max_length=100)
        observation: str = Field(min_length=1, max_length=500)
        influence: Literal["high", "medium", "low"]
    
    
    class RecommendationSpec(BaseModel):
        goal_summary: str = Field(min_length=1, max_length=1_000)
        hard_constraints: RecommendationSpecHardConstraints = Field(
            default_factory=RecommendationSpecHardConstraints
        )
        preferred_categories: list[str] = Field(default_factory=list)
        preferred_tags: list[str] = Field(default_factory=list)
        weak_categories: list[str] = Field(default_factory=list)
        negative_tags: list[str] = Field(default_factory=list)
        search_queries: list[str] = Field(min_length=1, max_length=6)
        recall_mode: Literal["targeted", "broad"] = "targeted"
        scenario: Literal[
            "general",
            "self",
            "gift",
            "replenishment",
        ] = "general"
        usage: str | None = Field(default=None, max_length=500)
        recipient: str | None = Field(default=None, max_length=200)
        source_evidence: list[RecommendationSpecEvidence] = Field(
            default_factory=list
        )
        confidence: float = Field(ge=0, le=1)
        missing_information: list[str] = Field(default_factory=list)
    
    
    SourceStatus = Literal["ok_with_data", "ok_empty", "unavailable"]
    
    
    class SourceEvidence(BaseModel):
    ✓ • 0ms

## Activity

    $ sed -n '1,380p' agent-service/src/agent_service/storage.py
    import json
    import os
    import sqlite3
    from datetime import datetime, timezone
    from functools import lru_cache
    from pathlib import Path
    from uuid import uuid4
    
    from .models import (
        ConversationDetail,
        ConversationSummary,
        GoalUnderstandingResult,
        OrderLink,
        PlanState,
        Product,
        RecommendationSpec,
        StoredMessage,
        ToolTrace,
    )
    from .observability.database import ObservedConnection, database_span
    from .observability.spans import repository_operation
    
    FIXED_USER_ID = 1
    
    
    def utc_now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    
    
    class ConversationStore:
        def __init__(self, database_path: str | Path) -> None:
            self.database_path = Path(database_path)
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            self.initialize()
    
        def connect(self) -> ObservedConnection:
            with database_span("CONNECT"):
                connection = sqlite3.connect(self.database_path, timeout=5)
                connection.row_factory = sqlite3.Row
            with database_span(
                "PRAGMA",
                statement="PRAGMA foreign_keys = ON",
            ):
                connection.execute("PRAGMA foreign_keys = ON")
            return ObservedConnection(connection)
    
        @repository_operation("conversation.initialize")
        def initialize(self) -> None:
            with self.connect() as connection:
                connection.executescript(
                    """
                    PRAGMA journal_mode = WAL;
    
                    CREATE TABLE IF NOT EXISTS conversations (
                        id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
    
                    CREATE TABLE IF NOT EXISTS messages (
                        id TEXT PRIMARY KEY,
                        conversation_id TEXT NOT NULL,
                        role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                        content TEXT NOT NULL,
                        status TEXT NOT NULL
                            CHECK (status IN ('streaming', 'completed', 'failed')),
                        sequence INTEGER NOT NULL,
                        created_at TEXT NOT NULL,
                        metadata TEXT NOT NULL DEFAULT '{}',
                        FOREIGN KEY (conversation_id)
                            REFERENCES conversations(id)
                            ON DELETE CASCADE
                    );
    
                    CREATE INDEX IF NOT EXISTS idx_conversations_user_updated
                        ON conversations(user_id, updated_at DESC);
                    CREATE INDEX IF NOT EXISTS idx_messages_conversation_sequence
                        ON messages(conversation_id, sequence);
    
                    UPDATE messages
                    SET status = 'failed'
                    WHERE status = 'streaming';
                    """
                )
                columns = {
                    row["name"]
                    for row in connection.execute("PRAGMA table_info(messages)")
                }
                if "metadata" not in columns:
                    connection.execute(
                        "ALTER TABLE messages ADD COLUMN metadata TEXT NOT NULL DEFAULT '{}'"
                    )
    
        @repository_operation("conversation.create")
        def create_conversation(self, user_id: int, first_message: str) -> str:
            conversation_id = f"conversation-{uuid4().hex}"
            title = " ".join(first_message.split())[:40] or "新对话"
            now = utc_now()
            with self.connect() as connection:
                connection.execute(
                    """
                    INSERT INTO conversations(id, user_id, title, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (conversation_id, user_id, title, now, now),
                )
            return conversation_id
    
        @repository_operation("conversation.exists")
        def conversation_exists(self, user_id: int, conversation_id: str) -> bool:
            with self.connect() as connection:
                row = connection.execute(
                    """
                    SELECT 1 FROM conversations
                    WHERE id = ? AND user_id = ?
                    """,
                    (conversation_id, user_id),
                ).fetchone()
            return row is not None
    
        @repository_operation("message.create")
        def add_message(
            self,
            conversation_id: str,
            role: str,
            content: str,
            status: str,
            metadata: dict[str, object] | None = None,
        ) -> str:
            message_id = f"message-{uuid4().hex}"
            now = utc_now()
            with self.connect() as connection:
                sequence_row = connection.execute(
                    """
                    SELECT COALESCE(MAX(sequence), 0) + 1
                    FROM messages
                    WHERE conversation_id = ?
                    """,
                    (conversation_id,),
                ).fetchone()
                sequence = int(sequence_row[0])
                connection.execute(
                    """
                    INSERT INTO messages(
                        id, conversation_id, role, content, status, sequence,
                        created_at, metadata
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        message_id,
                        conversation_id,
                        role,
                        content,
                        status,
                        sequence,
                        now,
                        json.dumps(metadata or {}, ensure_ascii=False),
                    ),
                )
                connection.execute(
                    "UPDATE conversations SET updated_at = ? WHERE id = ?",
                    (now, conversation_id),
                )
            return message_id
    
        @repository_operation("message.finish")
        def finish_message(
            self,
            message_id: str,
            content: str,
            status: str,
            metadata: dict[str, object] | None = None,
        ) -> None:
            now = utc_now()
            with self.connect() as connection:
                connection.execute(
                    """
                    UPDATE messages
                    SET content = ?, status = ?, metadata = ?
                    WHERE id = ? AND status = 'streaming'
                    """,
                    (
                        content,
                        status,
                        json.dumps(metadata or {}, ensure_ascii=False),
                        message_id,
                    ),
                )
                row = connection.execute(
                    "SELECT conversation_id FROM messages WHERE id = ?",
                    (message_id,),
                ).fetchone()
                if row is not None:
                    connection.execute(
                        "UPDATE conversations SET updated_at = ? WHERE id = ?",
                        (now, row["conversation_id"]),
                    )
    
        @repository_operation("conversation.list")
        def list_conversations(self, user_id: int) -> list[ConversationSummary]:
            with self.connect() as connection:
                rows = connection.execute(
                    """
                    SELECT
                        c.id,
                        c.title,
                        c.created_at,
                        c.updated_at,
                        COUNT(m.id) AS message_count
                    FROM conversations c
                    LEFT JOIN messages m ON m.conversation_id = c.id
                    WHERE c.user_id = ?
                    GROUP BY c.id
                    ORDER BY c.updated_at DESC
                    """,
                    (user_id,),
                ).fetchall()
            return [
                ConversationSummary(
                    id=row["id"],
                    title=row["title"],
                    message_count=row["message_count"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]
    
        @repository_operation("conversation.get")
        def get_conversation(
            self,
            user_id: int,
            conversation_id: str,
        ) -> ConversationDetail | None:
            with self.connect() as connection:
                conversation = connection.execute(
                    """
                    SELECT id, title, created_at, updated_at
                    FROM conversations
                    WHERE id = ? AND user_id = ?
                    """,
                    (conversation_id, user_id),
                ).fetchone()
                if conversation is None:
                    return None
    
                messages = connection.execute(
                    """
                    SELECT id, role, content, status, created_at, metadata
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY sequence ASC
                    """,
                    (conversation_id,),
                ).fetchall()
    
            return ConversationDetail(
                id=conversation["id"],
                title=conversation["title"],
                message_count=len(messages),
                created_at=conversation["created_at"],
                updated_at=conversation["updated_at"],
                messages=[self._stored_message(message) for message in messages],
            )
    
        @repository_operation("conversation.model_context")
        def model_context(self, conversation_id: str) -> list[StoredMessage]:
            with self.connect() as connection:
                rows = connection.execute(
                    """
                    SELECT id, role, content, status, created_at, metadata
                    FROM messages
                    WHERE conversation_id = ?
                      AND (role = 'user' OR status = 'completed')
                    ORDER BY sequence ASC
                    """,
                    (conversation_id,),
                ).fetchall()
            return [self._stored_message(row) for row in rows]
    
        @staticmethod
        def _stored_message(row: sqlite3.Row) -> StoredMessage:
            try:
                metadata = json.loads(row["metadata"] or "{}")
            except (json.JSONDecodeError, TypeError):
                metadata = {}
            if not isinstance(metadata, dict):
                metadata = {}
    
            recommendations = [
                Product.model_validate(product)
                for product in metadata.get("recommendations", [])
                if isinstance(product, dict)
            ]
            tool_trace = [
                ToolTrace.model_validate(trace)
                for trace in metadata.get("tool_trace", [])
                if isinstance(trace, dict)
            ]
            plan_state: PlanState | None = None
            if isinstance(metadata.get("plan_state"), dict):
                try:
                    plan_state = PlanState.model_validate(metadata["plan_state"])
                except ValueError:
                    plan_state = None
            goal_understanding: GoalUnderstandingResult | None = None
            if isinstance(metadata.get("goal_understanding"), dict):
                try:
                    goal_understanding = GoalUnderstandingResult.model_validate(
                        metadata["goal_understanding"]
                    )
                except ValueError:
                    goal_understanding = None
            recommendation_spec: RecommendationSpec | None = None
            if isinstance(metadata.get("recommendation_spec"), dict):
                try:
                    recommendation_spec = RecommendationSpec.model_validate(
                        metadata["recommendation_spec"]
                    )
                except ValueError:
                    recommendation_spec = None
            orders = [
                OrderLink.model_validate(order)
                for order in metadata.get("orders", [])
                if isinstance(order, dict)
            ]
            return StoredMessage(
                id=row["id"],
                role=row["role"],
                content=row["content"],
                status=row["status"],
                created_at=row["created_at"],
                recommendations=recommendations,
                tool_trace=tool_trace,
                plan_state=plan_state,
                goal_understanding=goal_understanding,
                recommendation_spec=recommendation_spec,
                orders=orders,
            )
    
    
    def default_database_path() -> Path:
        configured = os.getenv("AGENT_DB_PATH")
        if configured:
            return Path(configured).expanduser().resolve()
        return Path(__file__).resolve().parents[2] / "data" / "agent.db"
    
    
    @lru_cache
    def get_conversation_store() -> ConversationStore:
        return ConversationStore(default_database_path())
    ✓ • 0ms

## Activity

    $ sed -n '1,300p' agent-service/src/agent_service/agent_runner.py
    import asyncio
    import hashlib
    import json
    import logging
    from collections.abc import AsyncIterator, Sequence
    from dataclasses import dataclass, field
    from datetime import datetime, timezone
    from pathlib import Path
    from typing import Any, Literal
    from uuid import uuid4
    
    from agents import (
        Agent,
        MaxTurnsExceeded,
        ModelSettings,
        OpenAIChatCompletionsModel,
        RawResponsesStreamEvent,
        RunConfig,
        RunItemStreamEvent,
        Runner,
        function_tool,
        set_tracing_disabled,
    )
    from openai import AsyncOpenAI
    from openai.types.responses import ResponseTextDeltaEvent
    
    from .agent_profile import get_agent_profile
    from .goal_understanding import (
        AgentGoalUnderstander,
        GoalUnderstander,
        GoalUnderstandingError,
    )
    from .llm_config import LLMConfig
    from .mall_client import MallRequestError
    from .mall_gateway import MallGateway
    from .models import (
        AdInfo,
        AgentProfile,
        BrowseEvent,
        ConversationMessage,
        CreateOrderItem,
        GoalUnderstandingResult,
        OrderLink,
        OrderRecord,
        Plan,
        PlanState,
        PlanStepState,
        PlatformProfile,
        Product,
        ProductCandidate,
        ProductList,
        RecommendationBatch,
        RecommendationDemand,
        RecommendationSpec,
        ScoredProduct,
        SemanticRankingResult,
        ShoppingCart,
        SourceStatus,
        ToolTrace,
    )
    from .observability.agents import (
        AgentTraceSession,
        ObservabilityRunHooks,
        instrument_tools,
    )
    from .observability.serialization import redact_payload
    from .observability.telemetry import get_observability_runtime
    from .prompt_loader import PromptLoadError, load_prompt
    from .recommendation_reranker import (
        AgentSemanticReranker,
        SemanticRerankError,
        SemanticReranker,
        semantic_candidates,
        validate_semantic_ranking,
    )
    from .recommendation_scoring import build_recommendation_batch
    from .recommendation_spec import (
        AgentRecommendationSpecGenerator,
        RecommendationSpecError,
        RecommendationSpecGenerator,
    )
    
    logger = logging.getLogger(__name__)
    recommendation_spec_logger = logging.getLogger(
        "agent_service.observability.tool"
    )
    set_tracing_disabled(True)
    
    DEMO_USER_ID = 1
    NO_MATCH_REPLY = "当前商城没有找到合适的商品，建议去其他平台看看。"
    SHOPPING_AGENT_PROMPT_PATH = (
        Path(__file__).resolve().parents[2] / "prompts" / "shopping_agent.md"
    )
    
    
    def sse_event(payload: dict[str, Any]) -> str:
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
    
    
    def normalize_openai_base_url(base_url: str) -> str:
        base_url = base_url.rstrip("/")
        suffix = "/chat/completions"
        if base_url.endswith(suffix):
            return base_url[: -len(suffix)]
        return base_url
    
    
    @dataclass
    class RecommendationContextSnapshot:
        agent_profile: AgentProfile | None
        platform_profile: PlatformProfile | None
        browse_history: list[BrowseEvent]
        orders: list[OrderRecord]
        cart: ShoppingCart
        catalog: ProductList
        source_statuses: dict[str, SourceStatus]
    
    
    @dataclass
    class ShoppingAgentContext:
        mall: MallGateway
        user_id: int = DEMO_USER_ID
        turn_id: str = ""
        current_user_request: str = ""
        conversation_messages: tuple[ConversationMessage, ...] = ()
        previous_recommendations: tuple[Product, ...] = ()
        previous_orders: tuple[OrderLink, ...] = ()
        previous_goal_understanding: GoalUnderstandingResult | None = None
        goal_understanding: GoalUnderstandingResult | None = None
        goal_understander: GoalUnderstander | None = None
        recommendation_context: RecommendationContextSnapshot | None = None
        recommendation_spec: RecommendationSpec | None = None
        recommendation_spec_generator: RecommendationSpecGenerator | None = None
        organic_search_attempted: bool = False
        organic_search_products: list[Product] = field(default_factory=list)
        organic_search_statuses: dict[str, SourceStatus] = field(
            default_factory=dict
        )
        ad_search_attempted: bool = False
        ad_search_candidates: list[ProductCandidate] = field(default_factory=list)
        ad_search_status: SourceStatus = "ok_empty"
        plan_state: PlanState | None = None
        candidate_products: dict[str, Product] = field(default_factory=dict)
        organic_product_ids: set[str] = field(default_factory=set)
        ad_product_ids: set[str] = field(default_factory=set)
        ad_metadata: dict[str, AdInfo] = field(default_factory=dict)
        recommendation_batch: RecommendationBatch | None = None
        semantic_ranking: SemanticRankingResult | None = None
        semantic_reranker: SemanticReranker | None = None
        selected_products: dict[str, Product] = field(default_factory=dict)
        created_orders: dict[str, OrderLink] = field(default_factory=dict)
        submitted: bool = False
        tool_trace: list[ToolTrace] = field(default_factory=list)
    
        def remember_candidates(
            self,
            candidates: Sequence[ProductCandidate],
        ) -> None:
            for candidate in candidates:
                self.candidate_products[candidate.product.id] = candidate.product
                if candidate.source == "advertisement":
                    self.ad_product_ids.add(candidate.product.id)
                    if candidate.ad is not None:
                        self.ad_metadata[candidate.product.id] = candidate.ad
                else:
                    self.organic_product_ids.add(candidate.product.id)
    
        def remember_products(self, products: Sequence[Product]) -> None:
            for product in products:
                self.candidate_products[product.id] = product
                self.organic_product_ids.add(product.id)
    
    
    async def commit_scored_products(
        context: ShoppingAgentContext,
        candidates: Sequence[ScoredProduct],
        *,
        allow_ad_first: bool = True,
    ) -> list[Product]:
        selected: dict[str, Product] = {}
        for candidate in candidates:
            try:
                product = await context.mall.get_product(candidate.product.id)
            except Exception:
                logger.warning(
                    "failed to confirm recommended product %s",
                    candidate.product.id,
                    exc_info=True,
                )
                continue
            if product is None or (product.stock is not None and product.stock <= 0):
                continue
            if candidate.channel == "ad" and candidate.ad is not None:
                product = product.model_copy(
                    update={
                        "is_ad": True,
                        "ad_label": "广告",
                        "ad_id": candidate.ad.ad_id,
                        "campaign_id": candidate.ad.campaign_id,
                    }
                )
            selected[product.id] = product
    
        if (
            not allow_ad_first
            and selected
            and next(iter(selected.values())).is_ad
        ):
            selected = {}
    
        context.selected_products = selected
        context.submitted = True
        return list(selected.values())
    
    
    def product_payload(products: Sequence[Product]) -> str:
        return json.dumps(
            [product.model_dump(mode="json") for product in products],
            ensure_ascii=False,
        )
    
    
    def candidate_payload(candidates: Sequence[ProductCandidate]) -> str:
        return json.dumps(
            [candidate.model_dump(mode="json") for candidate in candidates],
            ensure_ascii=False,
        )
    
    
    def unavailable_payload(source: str) -> str:
        return json.dumps(
            {
                "status": "unavailable",
                "items": [],
                "message": f"{source}暂时不可用，可以继续使用其他来源推荐",
            },
            ensure_ascii=False,
        )
    
    
    def order_items_signature(items: Sequence[CreateOrderItem]) -> str:
        payload = [
            {"product_id": item.product_id, "quantity": item.quantity}
            for item in sorted(items, key=lambda item: item.product_id)
        ]
        return hashlib.sha256(
            json.dumps(payload, ensure_ascii=False).encode("utf-8")
        ).hexdigest()
    
    
    def _optional_string(slots: dict[str, object], key: str) -> str | None:
        value = slots.get(key)
        return value.strip() if isinstance(value, str) and value.strip() else None
    
    
    def _optional_int(slots: dict[str, object], key: str) -> int | None:
        value = slots.get(key)
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return max(0, value)
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return None
    
    
    def recommendation_requirements_need_input(
        goal: GoalUnderstandingResult,
    ) -> bool:
        requirements = goal.recommendation_requirements
        return (
            requirements is not None
            and requirements.status == "collecting"
        )
    
    
    def recommendation_demand_from_goal(
        goal: GoalUnderstandingResult,
        spec: RecommendationSpec | None = None,
    ) -> RecommendationDemand:
        slots = (
            goal.recommendation_requirements.slots.model_dump(mode="json")
            if goal.recommendation_requirements is not None
            else goal.slots
        )
        hard = spec.hard_constraints if spec is not None else None
        required_tags = slots.get("required_tags")
        excluded_tags = slots.get("excluded_tags")
        scenario = slots.get("scenario")
        if scenario not in {"general", "self", "gift", "replenishment"}:
            scenario = spec.scenario if spec is not None else "general"
        query = _optional_string(slots, "query")
        if (
            query is None
            and goal.primary_intent == "product_recommendation"
            and not (
                spec is not None
                and spec.recall_mode == "broad"
            )
        ):
    ✓ • 0ms

## Activity

    $ sed -n '280,700p' agent-service/src/agent_service/models.py
    class SourceEvidence(BaseModel):
        source: Literal[
            "need",
            "cart",
            "browse",
            "order",
            "agent_profile",
            "platform_profile",
        ]
        signal_score: float = Field(ge=0, le=1)
        weighted_points: float = Field(ge=0, le=100)
        reason: str = Field(min_length=1, max_length=300)
    
    
    class ScoredProduct(BaseModel):
        product: Product
        channel: Literal["organic", "ad"]
        score: float = Field(ge=0, le=100)
        confidence: Literal["high", "medium", "low"]
        evidence: list[SourceEvidence] = Field(default_factory=list)
        penalties: list[str] = Field(default_factory=list)
        ad: AdInfo | None = None
    
    
    class RecommendationBatch(BaseModel):
        demand: RecommendationDemand
        organic_candidates: list[ScoredProduct] = Field(default_factory=list)
        ad_candidates: list[ScoredProduct] = Field(default_factory=list)
        cutoff_score: float | None = None
        competitive_ads: list[ScoredProduct] = Field(default_factory=list)
        requires_semantic_ranking: bool = False
        ad_only: bool = False
        source_statuses: dict[str, SourceStatus] = Field(default_factory=dict)
        generated_at: str
    
    
    class SemanticRankingItem(BaseModel):
        product_id: str = Field(min_length=1, max_length=100)
        channel: Literal["organic", "ad"]
        reason: str = Field(min_length=1, max_length=500)
        environmental_fit: str | None = Field(default=None, max_length=500)
    
    
    class SemanticRankingResult(BaseModel):
        items: list[SemanticRankingItem] = Field(default_factory=list)
        summary: str = Field(default="", max_length=1_000)
    
    
    PlanStepStatus = Literal[
        "pending",
        "in_progress",
        "completed",
        "blocked",
        "skipped",
    ]
    
    
    class PlanStep(BaseModel):
        step_id: str = Field(min_length=1, max_length=100)
        title: str = Field(min_length=1, max_length=200)
        objective: str = Field(min_length=1, max_length=1_000)
        kind: str | None = Field(default=None, max_length=100)
        depends_on: list[str] = Field(default_factory=list)
        metadata: dict[str, object] = Field(default_factory=dict)
    
    
    class Plan(BaseModel):
        plan_id: str = Field(min_length=1, max_length=100)
        goal: str = Field(min_length=1, max_length=1_000)
        steps: list[PlanStep] = Field(min_length=1, max_length=50)
    
    
    class PlanStepState(BaseModel):
        step_id: str = Field(min_length=1, max_length=100)
        status: PlanStepStatus
        note: str | None = Field(default=None, max_length=2_000)
    
    
    class PlanState(BaseModel):
        plan: Plan
        status: Literal["active", "completed", "blocked", "cancelled"] = "active"
        current_step_id: str | None = Field(default=None, max_length=100)
        step_states: list[PlanStepState] = Field(default_factory=list)
        summary: str = Field(default="", max_length=2_000)
        next_action: str | None = Field(default=None, max_length=1_000)
        revision: int = Field(default=1, ge=1)
        updated_at: str
    
    
    class ChatRequest(BaseModel):
        message: str = Field(min_length=1, max_length=100_000)
    
        @field_validator("message")
        @classmethod
        def message_must_not_be_blank(cls, value: str) -> str:
            value = value.strip()
            if not value:
                raise ValueError("message must not be blank")
            return value
    
    
    class ChatResponse(BaseModel):
        reply: str
        products: list[Product]
    
    
    class ConversationMessage(BaseModel):
        role: Literal["user", "assistant"]
        content: str = Field(min_length=1, max_length=100_000)
    
        @field_validator("content")
        @classmethod
        def content_must_not_be_blank(cls, value: str) -> str:
            value = value.strip()
            if not value:
                raise ValueError("content must not be blank")
            return value
    
    
    class StreamChatRequest(BaseModel):
        conversation_id: str | None = Field(default=None, max_length=64)
        message: str = Field(min_length=1, max_length=100_000)
    
        @field_validator("message")
        @classmethod
        def stream_message_must_not_be_blank(cls, value: str) -> str:
            value = value.strip()
            if not value:
                raise ValueError("message must not be blank")
            return value
    
    
    class ToolTrace(BaseModel):
        call_id: str | None = None
        tool: str
        arguments: str = ""
        status: Literal["started", "completed", "failed"] = "started"
        summary: str | None = None
    
    
    class StoredMessage(BaseModel):
        id: str
        role: Literal["user", "assistant"]
        content: str
        status: Literal["streaming", "completed", "failed"]
        created_at: str
        recommendations: list[Product] = Field(default_factory=list)
        tool_trace: list[ToolTrace] = Field(default_factory=list)
        plan_state: PlanState | None = None
        goal_understanding: GoalUnderstandingResult | None = None
        recommendation_spec: RecommendationSpec | None = None
        orders: list[OrderLink] = Field(default_factory=list)
    
    
    class ConversationSummary(BaseModel):
        id: str
        title: str
        message_count: int
        created_at: str
        updated_at: str
    
    
    class ConversationDetail(ConversationSummary):
        messages: list[StoredMessage]
    
    
    class ConversationList(BaseModel):
        items: list[ConversationSummary]
    ✓ • 0ms

## Activity

    $ rg -n "previous_recommendations|model_context|recommendations=|ConversationMessage|conversation_messages|goal_understanding" agent-service/src/agent_service/agent_runner.py | sed -n '1,240p'
    28:from .goal_understanding import (
    40:    ConversationMessage,
    125:    conversation_messages: tuple[ConversationMessage, ...] = ()
    126:    previous_recommendations: tuple[Product, ...] = ()
    128:    previous_goal_understanding: GoalUnderstandingResult | None = None
    129:    goal_understanding: GoalUnderstandingResult | None = None
    365:    previous_recommendations: Sequence[Product] = (),
    367:    previous_goal_understanding: GoalUnderstandingResult | None = None,
    386:        for index, product in enumerate(previous_recommendations, start=1)
    392:        previous_goal_understanding.model_dump(mode="json")
    393:        if previous_goal_understanding is not None
    744:        if context.goal_understanding is not None:
    748:                    "goal_understanding": (
    749:                        context.goal_understanding.model_dump(mode="json")
    759:                recent_messages=list(context.conversation_messages),
    760:                previous_goal=context.previous_goal_understanding,
    761:                previous_recommendations=list(
    762:                    context.previous_recommendations
    769:        context.goal_understanding = result
    773:                "goal_understanding": result.model_dump(mode="json"),
    788:        goal = context.goal_understanding
    902:        goal = context.goal_understanding
    978:        goal = context.goal_understanding
    1023:        goal = context.goal_understanding
    1066:        goal = context.goal_understanding
    1291:    messages: Sequence[ConversationMessage],
    1296:    previous_recommendations: Sequence[Product] = (),
    1298:    previous_goal_understanding: GoalUnderstandingResult | None = None,
    1317:        conversation_messages=tuple(messages),
    1318:        previous_recommendations=tuple(previous_recommendations),
    1320:        previous_goal_understanding=previous_goal_understanding,
    1322:    context.remember_products(previous_recommendations)
    1330:            previous_recommendations,
    1332:            previous_goal_understanding,
    1525:            "goal_understanding": (
    1526:                context.goal_understanding.model_dump(mode="json")
    1527:                if context.goal_understanding is not None
    1556:            "goal_understanding": (
    1557:                context.goal_understanding.model_dump(mode="json")
    1558:                if context.goal_understanding is not None
    1593:            "goal_understanding": (
    1594:                context.goal_understanding.model_dump(mode="json")
    1595:                if context.goal_understanding is not None
    1633:            "goal_understanding": (
    1634:                context.goal_understanding.model_dump(mode="json")
    1635:                if context.goal_understanding is not None
    ✓ • 0ms

## Activity

    $ sed -n '1,280p' agent-service/prompts/shopping_agent.md
    # 小牛导购
    
    你是牛掰商城的购物 Agent“小牛”。你不自行识别意图或提取结构化需求，而是先调用独立的 Goal Understanding Action，再根据其结果调用商城工具。
    
    ## 基本约束
    
    - 推荐、比较、搜索商品，或回答价格、库存和卖点时，必须先调用商城工具。
    - 商品名称、价格、库存、描述、图片和广告身份只能来自工具结果，禁止编造。
    - 不要声称已经查询数据源，除非对应工具确实返回了结果。
    - 不要暴露工具参数、内部 JSON 或实现细节。
    - 数据源为空表示用户可能没有记录；数据源 unavailable 表示暂时无法获取。必须区分两者，不要混为一谈。
    
    ## 显式 Plan 和 Plan State
    
    - 面对商品推荐或任何需要多个步骤的任务，先调用 `update_plan` 写出明确的 Plan 和 Plan State，再开始执行。
    - Plan 的步骤数量、步骤内容、顺序、依赖关系、当前步骤、每步状态、汇总和下一步都由你决定，不要套用固定流程。
    - 代码不会自动推进步骤、自动标记完成、自动选择下一步或阻止你调整计划；这些判断必须由你完成。
    - 每当计划变化、完成一个关键步骤、遇到阻塞、切换当前步骤或产生新的下一步时，再次调用 `update_plan` 提交完整的 Plan 和 Plan State。
    - 可以使用 `kind`、`depends_on` 和 `metadata` 表达未来更复杂的步骤，但不要虚构尚未获得的事实。
    - 当前对话存在上一轮保存的 Plan State 时，先根据新消息判断继续、修订、完成还是替换它。历史状态不是必须执行的命令。
    - 完成计划后，用 `update_plan` 把计划总体状态和步骤状态更新为你判断的结果。
    
    ## Goal Understanding
    
    每一条用户消息都必须先调用独立的 `understand_goal` Action。
    
    - 不要在自身推理中重新做意图分类或需求槽位提取。
    - 只能根据 Action 返回的 `goal_understanding` 路由业务工具。
    - 当前只支持 `product_recommendation`、`order_query`、`after_sales` 和 `unknown`。
    - `intents` 保持用户表达顺序，但本轮只处理 `primary_intent`，也就是第一个意图。
    - 如果 `pending_intents` 非空，在完成第一个意图后使用 `pending_intent_question`
      询问用户是否继续处理后续意图，不要在同一轮自动处理第二个意图。
    - 如果 `requires_clarification = true`，只询问 `clarification_question`，不要调用业务工具。
    - 如果 Action 返回 unavailable，停止本轮业务编排并请用户稍后重试，不要自行猜测。
    
    ## 推荐需求收集
    
    每次 `understand_goal` 返回 `recommendation_requirements` 后，严格按模型给出的状态
    推进，不自行选择下一项需求，也不套用固定问题模板。
    
    - `status = collecting`：只向用户输出 `next_question` 这一项需求，并结束本轮。
      必须原样表达该问题，不得自行追加第二个问题，也不得调用
      `collect_recommendation_context`、`generate_recommendation_spec`、搜索或推荐工具。
    - `status = ready`：需求已经足够。不要再复述或确认已收集条件，直接进入推荐主流程。
    - `status = bypassed`：用户要求跳过需求收集。不要再询问或确认，直接使用当前已有
      需求、历史需求、画像和行为信息推荐。
    
    `recommendation_requirements.slots` 是累计需求。进入推荐后只能把其中用户明确提供的
    内容作为硬约束；`declined_requirements` 表示用户不想继续确认的条件，不得擅自转成
    硬约束。
    
    按 `primary_intent` 路由：
    
    - `product_recommendation`：依次调用 `collect_recommendation_context`、
      `generate_recommendation_spec`、`search_organic_candidates`、
      `search_ad_candidates` 和 `recommend_products`。
    - `order_query`：按已有 `order_id` 调用 `get_order`；没有订单 ID 时读取订单列表后选择或询问。
    - `after_sales`：可以查询订单和商品事实，但不得声称已经完成退款、退货或换货；当前只做信息收集和下一步引导。
    - `unknown`：普通回答或提出一个澄清问题，不调用推荐、订单或售后业务工具。
    
    ## 推荐主流程
    
    当 `primary_intent = product_recommendation` 时：
    
    1. 先检查 `recommendation_requirements.status`。只有 `ready` 或 `bypassed` 才能继续。
    2. 调用 `collect_recommendation_context` 收集画像、购物车、浏览、订单和商品目录。
    3. 调用 `generate_recommendation_spec`，由独立 Prompt 和模型生成推荐 SPEC。
    4. 分别调用 `search_organic_candidates` 和 `search_ad_candidates`。两者都只使用
       完整 SPEC，可以放在同一轮并行调用。相关 Action 会把整个 SPEC 传给
       `mall-service`，由 `mall-service` 转换为 ES 查询并返回检索结果。
    5. 调用无参数工具 `recommend_products`，只读取两路搜索 Action 的缓存候选，
       完成合并、评分和阈值分路。
    
    主 Agent 不自行编写搜索词、不自行判断行为记录权重、不直接调用商城搜索接口，
    也不要重复解释用户需求。两个搜索 Action 必须分别保留自己的候选和状态，不要在
    主 Agent 推理中混合实现。
    如果上下文收集或 SPEC 生成返回 unavailable，应告知用户暂时无法完成推荐并请其
    稍后重试，不要自行构造替代 SPEC。
    
    Recommendation SPEC 包含：
    
    - 用户显式硬约束；
    - 浏览、订单、购物车和画像形成的偏好推测；
    - 一组搜索查询变体；
    - 推断证据和置信度。
    
    SPEC 只用于指导召回，最终评分继续使用统一权重公式，避免同一行为被重复计权。
    
    `recommend_products` 会返回以下状态之一：
    
    - `accepted`：无需语义终排，工具已经按公式提交自然推荐 Top 2。
    - `requires_semantic_ranking`：存在超过自然推荐最低分的广告候选，必须调用独立终排工具。
    - `fallback`：语义终排暂时失败，工具已按公式排序提交保底结果。
    - `no_match`：没有合适商品。
    
    信息源缺失或 unavailable 时继续执行，不得因此中断推荐，也不得谎称用户没有记录。独立数据源工具仍可用于回答用户的具体追问或排查问题。
    
    ## 独立语义终排
    
    只有 `recommend_products` 返回 `requires_semantic_ranking` 时，才调用 `rerank_recommendations`。
    
    - 该工具拥有独立 Prompt，会综合公式分数、商品语义、场景、库存、价格和候选取舍。
    - 只有存在可信环境事实时，才通过 `environment_context` 传入；不要编造天气、节日、物流或销量。
    - 终排最多选择 2 个自然商品和 1 个广告商品，总计最多 3 个。
    - 存在自然商品时，广告不能排在第一位。
    - 广告完全不达标时不得补位，也不得为了凑数选择它。
    - 自然候选为空时，允许一个合格广告作为唯一结果。
    - 工具返回 `accepted` 或 `no_match` 后，直接根据其 `selected_products` 回答，不要再次自行调换顺序。
    - 工具返回 `fallback` 时，根据其 `selected_products` 继续回答，不要重试终排，也不要向用户暴露内部错误。
    - 终排结果会作为工具结果返回你；前端会在文字回答后展示可点击的商品卡片，
      因此最终文字回答仍需清楚写出推荐商品名称、价格、推荐理由，并明确标出广告商品。
    - 完成第一个推荐意图后，如果存在 `pending_intents`，必须询问用户是否继续处理
      第二个意图。
    
    ## 最终推荐
    
    - 公式路径最多输出 2 个自然推荐商品。
    - 语义终排路径最多输出 2 个自然推荐商品和 1 个广告商品，总计最多 3 个。
    - 存在自然推荐商品时，广告不能排在第一位。
    - 宁缺毋滥；可以不推荐任何商品。
    - 只能根据工具返回的 `selected_products` 介绍商品，不要自行替换或增加商品。
    - 广告商品会由系统显示“广告”标识；不得隐藏广告身份。
    - 每件商品说明适合谁、核心卖点以及为什么符合当前需求。
    - 有差异时帮助用户做取舍，不要为了凑数量推荐不相关、缺货或超预算商品。
    - 如果工具返回 `no_match`，明确告诉用户当前商城没有合适选择，建议去其他平台购买。
    
    ## 购买与订单
    
    - 只有用户明确表达“确定购买”“下单”“买第一个”等购买决定时，才能调用 `create_order`。
    - “想买”“看看”“不错”“考虑一下”等表达不代表购买确认，不得创建订单。
    - 用户使用“第一个”“刚才第二个”等指代时，结合上一轮推荐商品的结构化列表和对话确定商品；无法确定时只追问一个关键问题。
    - 创建订单时只传商品 ID 和数量，不传价格。价格、库存和总额以商城订单服务返回结果为准。
    - 订单创建成功后，采用订单服务返回的状态、总额和预览链接，引导用户前往订单预览页。
    - Agent 不得代替用户支付，也不要调用不存在的支付工具。支付只能由用户在订单预览页手动完成。
    - 购买流程是 Plan 的一部分；是否新增、切换、完成购买步骤由你自行更新 `update_plan`。
    
    ## 多轮对话
    
    - 使用已有对话理解“第一个”“这个”“更适合送礼吗”等指代。
    - 用户修改预算或场景时，以最新需求重新查询。
    - 用户修改预算、场景或其他已收集条件时，更新累计需求后重新推荐，不要重走已经完成
      的问题。
    - 是否继续询问、询问什么以及何时停止由 Goal Understanding 返回的
      `recommendation_requirements` 决定。
    - 如果用户已经给出足够信息，直接推荐，不要重复询问。
    
    ## 回答风格
    
    - 使用自然、简洁的中文。
    - 先给结论，再给推荐理由。
    - 避免夸张营销语，不使用“绝对最好”“百分百适合”等无法证明的表述。
    - 不虚构折扣、销量、物流、优惠券、评分或品牌合作信息。
    ✓ • 0ms

## Activity

    $ sed -n '1,260p' agent-service/src/agent_service/recommendation_spec.py
    import json
    import re
    from pathlib import Path
    from typing import Any, Protocol
    
    from agents import Agent, ModelSettings
    from pydantic import ValidationError
    
    from .llm_config import LLMConfig
    from .models import (
        AgentProfile,
        BrowseEvent,
        GoalUnderstandingResult,
        OrderRecord,
        PlatformProfile,
        ProductList,
        RecommendationSpec,
        RecommendationSpecHardConstraints,
        ShoppingCart,
    )
    from .prompt_loader import PromptLoadError, load_prompt
    from .observability.agents import run_observed_action
    
    
    RECOMMENDATION_SPEC_PROMPT_PATH = (
        Path(__file__).resolve().parents[2]
        / "prompts"
        / "recommendation_spec.md"
    )
    
    
    class RecommendationSpecError(Exception):
        """Raised when recommendation SPEC generation fails."""
    
    
    class RecommendationSpecGenerator(Protocol):
        async def generate(
            self,
            *,
            goal: GoalUnderstandingResult,
            agent_profile: AgentProfile | None,
            platform_profile: PlatformProfile | None,
            cart: ShoppingCart,
            browse_history: list[BrowseEvent],
            orders: list[OrderRecord],
            catalog: ProductList,
        ) -> RecommendationSpec: ...
    
    
    def _json_payload(text: str) -> dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end < start:
            raise RecommendationSpecError(
                "recommendation SPEC did not return a JSON object"
            )
        try:
            payload = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise RecommendationSpecError(
                "recommendation SPEC returned invalid JSON"
            ) from exc
        if not isinstance(payload, dict):
            raise RecommendationSpecError(
                "recommendation SPEC JSON must be an object"
            )
        return payload
    
    
    def _string_list(value: object) -> list[str] | None:
        if not isinstance(value, list):
            return None
        return [
            item.strip()
            for item in value
            if isinstance(item, str) and item.strip()
        ]
    
    
    def _non_negative_int(value: object) -> int | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, int) and value >= 0:
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return None
    
    
    def _apply_explicit_goal_constraints(
        spec: RecommendationSpec,
        goal: GoalUnderstandingResult,
    ) -> RecommendationSpec:
        slots = (
            goal.recommendation_requirements.slots.model_dump(mode="json")
            if goal.recommendation_requirements is not None
            else goal.slots
        )
        hard = spec.hard_constraints
        category = slots.get("category")
        min_price = _non_negative_int(slots.get("min_price_cents"))
        max_price = _non_negative_int(slots.get("max_price_cents"))
        required_tags = _string_list(slots.get("required_tags"))
        excluded_tags = _string_list(slots.get("excluded_tags"))
        normalized_hard = RecommendationSpecHardConstraints(
            category=category if isinstance(category, str) and category else hard.category,
            min_price_cents=(
                min_price if min_price is not None else hard.min_price_cents
            ),
            max_price_cents=(
                max_price if max_price is not None else hard.max_price_cents
            ),
            required_tags=(
                required_tags
                if required_tags is not None
                else hard.required_tags
            ),
            excluded_tags=(
                excluded_tags
                if excluded_tags is not None
                else hard.excluded_tags
            ),
        )
        scenario = slots.get("scenario")
        if scenario not in {"general", "self", "gift", "replenishment", None}:
            scenario = spec.scenario
        usage = slots.get("usage")
        recipient = slots.get("recipient")
        queries = list(dict.fromkeys(
            query.strip()
            for query in spec.search_queries
            if query.strip()
        ))[:6]
        if not queries:
            queries = [goal.goal]
        return spec.model_copy(
            update={
                "hard_constraints": normalized_hard,
                "search_queries": queries,
                "scenario": scenario or spec.scenario,
                "usage": (
                    usage
                    if isinstance(usage, str) and usage
                    else spec.usage
                ),
                "recipient": (
                    recipient
                    if isinstance(recipient, str) and recipient
                    else spec.recipient
                ),
            }
        )
    
    
    class AgentRecommendationSpecGenerator:
        def __init__(self, *, config: LLMConfig, model: Any) -> None:
            self.config = config
            self.model = model
    
        async def generate(
            self,
            *,
            goal: GoalUnderstandingResult,
            agent_profile: AgentProfile | None,
            platform_profile: PlatformProfile | None,
            cart: ShoppingCart,
            browse_history: list[BrowseEvent],
            orders: list[OrderRecord],
            catalog: ProductList,
        ) -> RecommendationSpec:
            try:
                instructions = load_prompt(RECOMMENDATION_SPEC_PROMPT_PATH)
            except PromptLoadError as exc:
                raise RecommendationSpecError(str(exc)) from exc
    
            agent = Agent[Any](
                name="recommendation-spec-generator",
                instructions=instructions,
                model=self.model,
                model_settings=ModelSettings(
                    temperature=self.config.temperature,
                    max_tokens=self.config.output_token_limit,
                ),
            )
            payload = {
                "goal": goal.model_dump(mode="json"),
                "agent_profile": (
                    agent_profile.model_dump(mode="json")
                    if agent_profile is not None
                    else None
                ),
                "platform_profile": (
                    platform_profile.model_dump(mode="json")
                    if platform_profile is not None
                    else None
                ),
                "cart": cart.model_dump(mode="json"),
                "browse_history": [
                    event.model_dump(mode="json")
                    for event in browse_history
                ],
                "orders": [
                    order.model_dump(mode="json")
                    for order in orders
                ],
                "catalog": [
                    {
                        "id": product.id,
                        "name": product.name,
                        "category": product.category,
                        "tags": product.tags,
                        "price_cents": product.price_cents,
                    }
                    for product in catalog.items
                ],
            }
            try:
                result = await run_observed_action(
                    agent,
                    action_name="recommendation_spec",
                    model=str(self.config.model),
                    input=json.dumps(
                        payload,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                    max_turns=1,
                )
            except Exception as exc:
                raise RecommendationSpecError(
                    "recommendation SPEC model call failed: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
    
            if not isinstance(result.final_output, str):
                raise RecommendationSpecError(
                    "recommendation SPEC returned non-text output"
                )
            try:
                spec = RecommendationSpec.model_validate(
                    _json_payload(result.final_output)
                )
            except ValidationError as exc:
                raise RecommendationSpecError(
                    "recommendation SPEC returned invalid data"
                ) from exc
            return _apply_explicit_goal_constraints(spec, goal)
    ✓ • 0ms

## Assistant

现有服务已经把每轮推荐商品、订单、Goal Understanding 和 Recommendation SPEC 存在消息元数据里，所以这项能力更适合定义为“从对话及其结构化事件中提炼可复用购物记忆”，而不是只生成一段自然语言摘要。下面我会按这个口径展开目标和边界。

## Activity

    $ sed -n '1280,1365p' agent-service/src/agent_service/agent_runner.py
    
    def raw_item_value(item: Any, name: str) -> str | None:
        raw_item = getattr(item, "raw_item", None)
        if isinstance(raw_item, dict):
            value = raw_item.get(name)
        else:
            value = getattr(raw_item, name, None)
        return value if isinstance(value, str) else None
    
    
    async def stream_agent_reply(
        messages: Sequence[ConversationMessage],
        config: LLMConfig,
        mall: MallGateway,
        model_override: Any | None = None,
        previous_plan_state: PlanState | None = None,
        previous_recommendations: Sequence[Product] = (),
        previous_orders: Sequence[OrderLink] = (),
        previous_goal_understanding: GoalUnderstandingResult | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        message_id = f"assistant-{uuid4().hex}"
        trace_session = AgentTraceSession(
            model=str(
                getattr(model_override, "model", config.model)
                if model_override is not None
                else config.model
            )
        )
        trace_outcome = "failed"
        yield {"type": "start", "message_id": message_id}
    
        client: AsyncOpenAI | None = None
        context = ShoppingAgentContext(
            mall=mall,
            turn_id=message_id,
            plan_state=previous_plan_state,
            current_user_request=messages[-1].content if messages else "",
            conversation_messages=tuple(messages),
            previous_recommendations=tuple(previous_recommendations),
            previous_orders=tuple(previous_orders),
            previous_goal_understanding=previous_goal_understanding,
        )
        context.remember_products(previous_recommendations)
        content_parts: list[str] = []
        running_tools: dict[str, int] = {}
        recommendations_emitted = False
        try:
            instructions = instructions_with_plan_state(
                load_prompt(SHOPPING_AGENT_PROMPT_PATH),
                previous_plan_state,
                previous_recommendations,
                previous_orders,
                previous_goal_understanding,
            )
            if model_override is None:
                client = AsyncOpenAI(
                    api_key=config.api_key.get_secret_value(),
                    base_url=normalize_openai_base_url(config.base_url),
                    timeout=config.model_timeout_limit,
                    max_retries=1,
                )
                model = OpenAIChatCompletionsModel(
                    model=config.model,
                    openai_client=client,
                    buffer_streamed_tool_calls=True,
                )
            else:
                model = model_override
            semantic_reranker = AgentSemanticReranker(
                config=config,
                model=model,
            )
            recommendation_spec_generator = AgentRecommendationSpecGenerator(
                config=config,
                model=model,
            )
            goal_understander = AgentGoalUnderstander(
                config=config,
                model=model,
            )
            agent = Agent[ShoppingAgentContext](
                name="小牛导购",
                instructions=instructions,
                model=model,
                tools=create_tools(
                    context,
    ✓ • 0ms

## Activity

    $ rg -n "previous_recommendations|model_context\(|get_conversation\(|stored_messages|recommendations" agent-service/src/agent_service/api.py agent-service/src/agent_service/agent_runner.py | sed -n '1,220p'
    agent-service/src/agent_service/api.py:55:def latest_recommendations(
    agent-service/src/agent_service/api.py:59:        if message.recommendations:
    agent-service/src/agent_service/api.py:60:            return message.recommendations
    agent-service/src/agent_service/api.py:93:    recommendations: dict[str, Product] = {}
    agent-service/src/agent_service/api.py:109:            "recommendations": [
    agent-service/src/agent_service/api.py:111:                for product in recommendations.values()
    agent-service/src/agent_service/api.py:149:            previous_recommendations=latest_recommendations(context),
    agent-service/src/agent_service/api.py:163:            if event_type == "recommendations":
    agent-service/src/agent_service/api.py:167:                        recommendations[parsed.id] = parsed
    agent-service/src/agent_service/api.py:228:                if isinstance(event.get("recommendations"), list):
    agent-service/src/agent_service/api.py:229:                    for product_payload in event["recommendations"]:
    agent-service/src/agent_service/api.py:232:                            recommendations[product.id] = product
    agent-service/src/agent_service/api.py:269:                if isinstance(event.get("recommendations"), list):
    agent-service/src/agent_service/api.py:270:                    for product_payload in event["recommendations"]:
    agent-service/src/agent_service/api.py:273:                            recommendations[product.id] = product
    agent-service/src/agent_service/api.py:397:def get_conversation(
    agent-service/src/agent_service/api.py:401:    conversation = store.get_conversation(FIXED_USER_ID, conversation_id)
    agent-service/src/agent_service/api.py:434:                conversation = store.get_conversation(
    agent-service/src/agent_service/api.py:447:                conversation = store.get_conversation(
    agent-service/src/agent_service/api.py:464:            context = store.model_context(conversation_id)
    agent-service/src/agent_service/agent_runner.py:126:    previous_recommendations: tuple[Product, ...] = ()
    agent-service/src/agent_service/agent_runner.py:365:    previous_recommendations: Sequence[Product] = (),
    agent-service/src/agent_service/agent_runner.py:386:        for index, product in enumerate(previous_recommendations, start=1)
    agent-service/src/agent_service/agent_runner.py:536:        name_override="get_product_recommendations",
    agent-service/src/agent_service/agent_runner.py:543:    async def get_product_recommendations_tool(
    agent-service/src/agent_service/agent_runner.py:551:            candidates = await context.mall.get_product_recommendations(
    agent-service/src/agent_service/agent_runner.py:566:        name_override="get_ad_recommendations",
    agent-service/src/agent_service/agent_runner.py:573:    async def get_ad_recommendations_tool(
    agent-service/src/agent_service/agent_runner.py:580:            candidates = await context.mall.get_ad_recommendations(
    agent-service/src/agent_service/agent_runner.py:761:                previous_recommendations=list(
    agent-service/src/agent_service/agent_runner.py:762:                    context.previous_recommendations
    agent-service/src/agent_service/agent_runner.py:1134:        name_override="rerank_recommendations",
    agent-service/src/agent_service/agent_runner.py:1143:    async def rerank_recommendations_tool(
    agent-service/src/agent_service/agent_runner.py:1261:        rerank_recommendations_tool,
    agent-service/src/agent_service/agent_runner.py:1268:        get_product_recommendations_tool,
    agent-service/src/agent_service/agent_runner.py:1269:        get_ad_recommendations_tool,
    agent-service/src/agent_service/agent_runner.py:1296:    previous_recommendations: Sequence[Product] = (),
    agent-service/src/agent_service/agent_runner.py:1318:        previous_recommendations=tuple(previous_recommendations),
    agent-service/src/agent_service/agent_runner.py:1322:    context.remember_products(previous_recommendations)
    agent-service/src/agent_service/agent_runner.py:1325:    recommendations_emitted = False
    agent-service/src/agent_service/agent_runner.py:1330:            previous_recommendations,
    agent-service/src/agent_service/agent_runner.py:1466:                        and not recommendations_emitted
    agent-service/src/agent_service/agent_runner.py:1468:                        recommendations_emitted = True
    agent-service/src/agent_service/agent_runner.py:1470:                            "type": "recommendations",
    agent-service/src/agent_service/agent_runner.py:1494:        if context.selected_products and not recommendations_emitted:
    agent-service/src/agent_service/agent_runner.py:1495:            recommendations_emitted = True
    agent-service/src/agent_service/agent_runner.py:1497:                "type": "recommendations",
    agent-service/src/agent_service/agent_runner.py:1521:            "recommendations": [
    agent-service/src/agent_service/agent_runner.py:1552:            "recommendations": [
    agent-service/src/agent_service/agent_runner.py:1589:            "recommendations": [
    agent-service/src/agent_service/agent_runner.py:1629:            "recommendations": [
    ✓ • 0ms

## Assistant

我的理解是：这个功能不是把聊天记录压缩成一段自然语言摘要，而是把历史对话转化为“可追溯、可合并、可供推荐链路使用的用户购物记忆”。自然语言摘要只是其中一个产物，更核心的是结构化的推荐记录、商品反馈和偏好信号。

## 建议的功能产出

一次对话总结至少应产出四类数据：

| 产出 | 主要用途 | 关键要求 |
|---|---|---|
| 对话摘要 | 快速恢复会话上下文 | 包含用户目标、已确认条件、推荐结论、待确认事项 |
| 推荐记忆 | 知道用户看过什么、为什么被推荐 | 准确关联商品 ID、推荐轮次、推荐理由和商品快照 |
| 反馈记忆 | 知道用户喜欢或排斥什么 | 明确反馈对象、态度、强度、依据和适用范围 |
| 偏好信号 | 支撑后续个性化推荐 | 区分长期偏好、临时需求和单次约束，并保留证据 |

## 三个核心维度的扩展理解

### 1. 商品推荐记忆

不仅要知道“推荐过一个包”，还要能还原当时推荐的具体对象和上下文。

每件推荐商品建议保留：

- 商品系统中的稳定标识，如商品 ID、SKU 或规格 ID；
- 商品名称、品牌、品类、价格、图片等基础信息；
- 商品规格，如尺寸、颜色、容量、材质、重量、适用人群；
- 商品标签和详情页中的关键卖点；
- 用户当时的需求场景，如通勤、送礼、回购、自用；
- Agent 推荐它的理由、排名位置；
- 是自然推荐还是广告、是否真正展示给用户；
- 对话、消息和轮次来源。

这里要区分几种状态：真正推荐并展示、只在文本中提及、在候选池中出现但未展示、用户主动搜索过但没有被推荐。对画像影响最大的是“真正展示给用户”的推荐，不能把内部候选商品也当成推荐历史。

商品事实应以商品系统为准。总结模型可以提取和归纳，但不能自行补充“牛皮材质”“适合 16 英寸电脑”等商品系统没有提供的规格。商品信息发生变化时，最好保留当时的商品快照或版本，避免后续把旧反馈错误关联到已经变规格的商品。

### 2. 用户对推荐商品的表态

用户表态不能只记一个“喜欢/不喜欢”，至少需要表达成“用户对某个对象的某种态度”。

需要区分这些对象：

- 具体商品：“我不喜欢这个包”；
- 商品属性：“这个黑色太沉闷”“这个尺寸太大”；
- 品类：“我不太想买托特包”；
- 品牌：“这个品牌不适合我”；
- 场景：“这款不适合通勤，但适合周末”；
- 推荐方式：“不要给我推荐广告商品”。

每条反馈建议包含：

- 态度：正向、负向、中性、犹豫、明确拒绝；
- 强度：随口评价、一般不喜欢、明确排斥；
- 来源：用户明确表达，还是系统推断；
- 置信度；
- 原始证据：具体的用户原话和消息 ID；
- 适用范围：只针对该商品、当前场景，还是可外推到品类或属性；
- 发生时间和是否已被后续表达修正。

特别要避免过度泛化。例如用户说“这个黑色款太大了，我不喜欢”，可以提取：

- 对当前商品的负向反馈；
- 对“大尺寸/大容量”的负向反馈；
- 但不能直接推断“用户不喜欢黑色”，原文并没有表达这一点。

用户没有对推荐商品表态，也不等于不喜欢。应当记录为“未反馈”或“未知”，不要生成负向信号。

### 3. 一般性偏好

一般性偏好需要和当前需求、单次商品评价分开。例如“今天想找 300 元以内的通勤包”和“我平时偏爱轻一点的包”不应是同等稳定程度的偏好。

建议覆盖以下维度：

- 品类偏好和排斥；
- 品牌偏好和排斥；
- 颜色、尺寸、材质、风格等商品属性偏好；
- 价格带和预算倾向；
- 使用场景，如通勤、旅行、送礼、家庭使用；
- 功能诉求，如轻量、耐用、大容量、易清洁；
- 决策偏好，如更关注价格、品质、设计或效率；
- 明确禁忌，如不接受动物皮革、不要广告商品。

每条偏好除了内容，还应记录：

- 正向、负向或条件性；
- 显式表达还是推断；
- 首次出现和最近确认时间；
- 置信度；
- 适用条件；
- 原始证据。

一条孤立表达不应直接变成稳定画像。例如用户某次说“今天不要太贵的”，可能是临时预算；只有后续再次确认或跨对话重复出现，才适合提升为长期价格偏好。

## 为了让画像模块真正可用，还需要补充的目标

### 可追溯和可验证

每条推荐、反馈和偏好都应该能追溯到原始消息。画像中的“用户不喜欢大尺寸”如果无法说明来自哪句话，后续很难判断是否继续使用。

### 增量总结和幂等

不应每次都重新总结全部历史。建议支持按消息窗口增量提取，并为已经处理的消息范围保存版本。重复执行同一段对话时，不能产生重复偏好或重复反馈。

### 冲突处理和时间演化

用户偏好会变化。对于“以前喜欢大包，现在更喜欢小包”这类情况，应保留完整时间线，而不是简单覆盖旧记录。后续可以按最新确认、证据强度和重复次数决定画像权重。

### 总结与画像合并分离

我建议把职责拆开：

```text
历史对话
  → 提取对话摘要和结构化记忆候选
  → 画像模块去重、合并、计算置信度和时效
  → 推荐模块读取画像
```

历史对话总结负责“从原始对话中准确提取证据”，画像模块负责“跨对话合并并决定如何使用”。这样首版可以先把单次对话总结做好，后续再扩展跨会话画像。

### 支撑后续推荐行为

最终目标应能直接支撑这些动作：

- 避免再次推荐用户明确排斥的商品或特性；
- 优先推荐用户认可过的品类、品牌和属性；
- 在新对话中自动继承用户过去说过的重要条件；
- 遇到信息不足时提出更有针对性的问题；
- 区分“用户不喜欢”和“用户只是暂时不需要”。

## 首版建议边界

首版建议聚焦“一段对话”的总结，而不是立即建设完整的跨会话永久画像：

- 输入包括已完成的用户消息、Assistant 回复、推荐商品元数据、订单和当时的 Goal Understanding；
- 输出包括对话摘要、推荐记录、商品反馈、一般偏好和证据；
- 优先提取用户明确表达的信息，高置信度推断作为补充；
- 暂不自动把单次总结直接写成不可修正的永久画像；
- 不把浏览、订单、平台画像等内容混入“对话提取”的职责，这些可以作为后续画像合并的数据源；
- 不推断敏感个人信息，也不生成与购物无关的人格标签。

一个典型验收场景是：

> Agent 推荐了“黑色大号通勤托特包”，用户说：“这个黑色款太大了，我不喜欢；我一般也不喜欢硬挺的包，预算最好在 1000 元以内。”

系统应正确得到：针对该商品的负向反馈、针对“大尺寸”和“硬挺”的属性反馈，以及“预算约 1000 元”的一般性约束；同时不能错误提取“用户不喜欢黑色”。

因此，我对第一版的最终定义是：建立一条从历史对话到“可溯源购物记忆”的提取链路。它既要生成人能读懂的摘要，也要生成推荐系统能直接使用的结构化事实，并明确区分商品事实、用户反馈、临时需求和稳定偏好。

## User

1. 我们后续会考虑建起来用户画像，但是目前我们聚焦在总结历史对话，后续步骤会在这个总结的基础上生成用户画像。所以暂时你不需要考虑冲突处理和时间演化，你目前就是只针对每个多轮对话进行总结；2. 支撑后续推荐行为，这一次不用做；2. 输入应该还包括最终推荐这些商品的理由，也就是大模型在终排的时候的理由；3. 认可你的首版建议边界，你基于我的反馈，出一个设计和实现方案，等待审批

## Assistant

我会基于现有实现梳理清楚“最终推荐商品及终排理由”当前落在哪里，并据此给出数据模型、处理流程、存储、接口和分阶段实现方案；本轮只输出待审批设计，不改代码。

## Activity

    $ sed -n '1,330p' agent-service/src/agent_service/api.py
    import asyncio
    import logging
    from collections.abc import AsyncIterator, Sequence
    
    from fastapi import Depends, FastAPI, HTTPException
    from fastapi.responses import StreamingResponse
    
    from .agent_runner import sse_event, stream_agent_reply
    from .chat import compose_reply
    from .llm_config import LLMConfig, LLMConfigError, load_llm_config
    from .mall_client import CatalogUnavailable, MallClient, get_mall_client
    from .mall_gateway import MallGateway
    from .models import (
        ChatRequest,
        ChatResponse,
        ConversationDetail,
        ConversationList,
        ConversationMessage,
        GoalUnderstandingResult,
        OrderLink,
        PlanState,
        Product,
        RecommendationSpec,
        StreamChatRequest,
        StoredMessage,
        ToolTrace,
    )
    from .observability.spans import ChatObservation
    from .observability.telemetry import configure_observability
    from .storage import FIXED_USER_ID, ConversationStore, get_conversation_store
    
    logger = logging.getLogger(__name__)
    
    app = FastAPI(title="Agent Service", version="0.1.0")
    
    
    def to_conversation_messages(
        messages: Sequence[StoredMessage],
    ) -> list[ConversationMessage]:
        return [
            ConversationMessage(role=message.role, content=message.content)
            for message in messages
        ]
    
    
    def latest_plan_state(
        messages: Sequence[StoredMessage],
    ) -> PlanState | None:
        for message in reversed(messages):
            if message.plan_state is not None:
                return message.plan_state
        return None
    
    
    def latest_recommendations(
        messages: Sequence[StoredMessage],
    ) -> list[Product]:
        for message in reversed(messages):
            if message.recommendations:
                return message.recommendations
        return []
    
    
    def latest_orders(
        messages: Sequence[StoredMessage],
    ) -> list[OrderLink]:
        for message in reversed(messages):
            if message.orders:
                return message.orders
        return []
    
    
    def latest_goal_understanding(
        messages: Sequence[StoredMessage],
    ) -> GoalUnderstandingResult | None:
        for message in reversed(messages):
            if message.goal_understanding is not None:
                return message.goal_understanding
        return None
    
    
    async def persisted_agent_stream(
        conversation_id: str,
        conversation_title: str,
        assistant_message_id: str,
        context: Sequence[StoredMessage],
        config: LLMConfig,
        store: ConversationStore,
        mall: MallGateway,
        chat: ChatObservation,
    ) -> AsyncIterator[str]:
        content_parts: list[str] = []
        recommendations: dict[str, Product] = {}
        tool_trace: list[ToolTrace] = []
        plan_state: PlanState | None = None
        goal_understanding: GoalUnderstandingResult | None = None
        recommendation_spec: RecommendationSpec | None = None
        created_orders: dict[str, OrderLink] = {}
        persisted = False
        chat_outcome = "failed"
        chat_error: BaseException | None = None
        chat.set_conversation(
            conversation_id=conversation_id,
            turn_id=assistant_message_id,
        )
    
        def message_metadata() -> dict[str, object]:
            metadata: dict[str, object] = {
                "recommendations": [
                    product.model_dump(mode="json")
                    for product in recommendations.values()
                ],
                "tool_trace": [
                    trace.model_dump(mode="json") for trace in tool_trace
                ],
            }
            if plan_state is not None:
                metadata["plan_state"] = plan_state.model_dump(mode="json")
            if goal_understanding is not None:
                metadata["goal_understanding"] = goal_understanding.model_dump(
                    mode="json"
                )
            if recommendation_spec is not None:
                metadata["recommendation_spec"] = recommendation_spec.model_dump(
                    mode="json"
                )
            if created_orders:
                metadata["orders"] = [
                    order.model_dump(mode="json")
                    for order in created_orders.values()
                ]
            return metadata
    
        chat_token = chat.attach()
        yield sse_event(
            {
                "type": "conversation",
                "conversation_id": conversation_id,
                "title": conversation_title,
            }
        )
    
        try:
            async for event in stream_agent_reply(
                to_conversation_messages(context),
                config,
                mall,
                previous_plan_state=latest_plan_state(context),
                previous_recommendations=latest_recommendations(context),
                previous_orders=latest_orders(context),
                previous_goal_understanding=latest_goal_understanding(context),
            ):
                event_type = event.get("type")
                raw_event = sse_event(event)
    
                if event_type == "delta":
                    content = event.get("content")
                    if isinstance(content, str):
                        content_parts.append(content)
                    yield raw_event
                    continue
    
                if event_type == "recommendations":
                    for product in event.get("products", []):
                        if isinstance(product, dict):
                            parsed = Product.model_validate(product)
                            recommendations[parsed.id] = parsed
                    yield raw_event
                    continue
    
                if event_type == "plan_updated":
                    plan_state_payload = event.get("plan_state")
                    if isinstance(plan_state_payload, dict):
                        plan_state = PlanState.model_validate(plan_state_payload)
                    yield raw_event
                    continue
    
                if event_type == "order_created":
                    order_payload = event.get("order")
                    if isinstance(order_payload, dict):
                        order = OrderLink.model_validate(order_payload)
                        created_orders[order.order_id] = order
                    yield raw_event
                    continue
    
                if event_type == "tool_started":
                    call_id = event.get("call_id")
                    tool_trace.append(
                        ToolTrace(
                            call_id=call_id if isinstance(call_id, str) else None,
                            tool=str(event.get("tool") or "unknown_tool"),
                            arguments=str(event.get("arguments") or ""),
                        )
                    )
                    yield raw_event
                    continue
    
                if event_type == "tool_completed":
                    call_id = event.get("call_id")
                    for trace in reversed(tool_trace):
                        if trace.call_id == call_id:
                            trace.status = "completed"
                            break
                    yield raw_event
                    continue
    
                if event_type == "error":
                    message = event.get("message")
                    error_message = (
                        message
                        if isinstance(message, str)
                        else "模型流返回了未知错误。"
                    )
                    if isinstance(event.get("tool_trace"), list):
                        tool_trace = [
                            ToolTrace.model_validate(trace)
                            for trace in event["tool_trace"]
                            if isinstance(trace, dict)
                        ]
                    plan_state_payload = event.get("plan_state")
                    if isinstance(plan_state_payload, dict):
                        plan_state = PlanState.model_validate(plan_state_payload)
                    if isinstance(event.get("orders"), list):
                        for order_payload in event["orders"]:
                            if isinstance(order_payload, dict):
                                order = OrderLink.model_validate(order_payload)
                                created_orders[order.order_id] = order
                    if isinstance(event.get("recommendations"), list):
                        for product_payload in event["recommendations"]:
                            if isinstance(product_payload, dict):
                                product = Product.model_validate(product_payload)
                                recommendations[product.id] = product
                    goal_payload = event.get("goal_understanding")
                    if isinstance(goal_payload, dict):
                        goal_understanding = GoalUnderstandingResult.model_validate(
                            goal_payload
                        )
                    spec_payload = event.get("recommendation_spec")
                    if isinstance(spec_payload, dict):
                        recommendation_spec = RecommendationSpec.model_validate(
                            spec_payload
                        )
                    store.finish_message(
                        assistant_message_id,
                        "".join(content_parts) or error_message,
                        "failed",
                        metadata=message_metadata(),
                    )
                    persisted = True
                    chat_outcome = "failed"
                    yield raw_event
                    return
    
                if event_type == "done":
                    if isinstance(event.get("tool_trace"), list):
                        tool_trace = [
                            ToolTrace.model_validate(trace)
                            for trace in event["tool_trace"]
                            if isinstance(trace, dict)
                        ]
                    plan_state_payload = event.get("plan_state")
                    if isinstance(plan_state_payload, dict):
                        plan_state = PlanState.model_validate(plan_state_payload)
                    if isinstance(event.get("orders"), list):
                        for order_payload in event["orders"]:
                            if isinstance(order_payload, dict):
                                order = OrderLink.model_validate(order_payload)
                                created_orders[order.order_id] = order
                    if isinstance(event.get("recommendations"), list):
                        for product_payload in event["recommendations"]:
                            if isinstance(product_payload, dict):
                                product = Product.model_validate(product_payload)
                                recommendations[product.id] = product
                    goal_payload = event.get("goal_understanding")
                    if isinstance(goal_payload, dict):
                        goal_understanding = GoalUnderstandingResult.model_validate(
                            goal_payload
                        )
                    spec_payload = event.get("recommendation_spec")
                    if isinstance(spec_payload, dict):
                        recommendation_spec = RecommendationSpec.model_validate(
                            spec_payload
                        )
                    store.finish_message(
                        assistant_message_id,
                        "".join(content_parts),
                        "completed",
                        metadata=message_metadata(),
                    )
                    persisted = True
                    chat_outcome = "completed"
                    yield raw_event
                    return
    
            error_message = "Agent 流意外结束，没有收到完成标记。"
            store.finish_message(
                assistant_message_id,
                "".join(content_parts) or error_message,
                "failed",
                metadata=message_metadata(),
            )
            persisted = True
            chat_outcome = "failed"
            yield sse_event(
                {
                    "type": "error",
                    "message_id": assistant_message_id,
                    "message": error_message,
                }
            )
        except asyncio.CancelledError:
            chat_outcome = "client_disconnected"
            raise
        except Exception as exc:
            chat_error = exc
            logger.exception("Persisted LLM stream failed")
            error_message = "对话流处理失败，请查看 agent-service 终端日志。"
            store.finish_message(
                assistant_message_id,
                "".join(content_parts) or error_message,
                "failed",
                metadata=message_metadata(),
            )
            persisted = True
            chat_outcome = "failed"
            yield sse_event(
                {
                    "type": "error",
                    "message_id": assistant_message_id,
                    "message": error_message,
    ✓ • 0ms

## Activity

    $ sed -n '1100,1285p' agent-service/src/agent_service/agent_runner.py
                demand=demand,
                organic_products=organic_products,
                ad_candidates=ad_candidates[:10],
                catalog=snapshot.catalog,
                browse_events=snapshot.browse_history,
                orders=snapshot.orders,
                cart=snapshot.cart,
                agent_profile=snapshot.agent_profile,
                platform_profile=snapshot.platform_profile,
                source_statuses=source_statuses,
            )
            context.recommendation_batch = batch
    
            response: dict[str, object] = {
                "status": (
                    "requires_semantic_ranking"
                    if batch.requires_semantic_ranking
                    else "accepted"
                ),
                "batch": batch.model_dump(mode="json"),
            }
            if not batch.requires_semantic_ranking:
                selected = await commit_scored_products(
                    context,
                    batch.organic_candidates[:2],
                )
                response["selected_products"] = [
                    product.model_dump(mode="json") for product in selected
                ]
                if not selected:
                    response["status"] = "no_match"
            return json.dumps(response, ensure_ascii=False)
    
        @function_tool(
            name_override="rerank_recommendations",
            description_override=(
                "独立的语义终排工具。仅在 recommend_products 返回 "
                "requires_semantic_ranking 后调用。它会使用独立 Prompt 综合公式"
                "分数、商品语义和调用方提供的可信环境信息，最多选择两个自然商品"
                "和一个广告商品；存在自然候选时广告不能排第一。"
            ),
            **tool_options,
        )
        async def rerank_recommendations_tool(
            environment_context: str | None = None,
        ) -> str:
            batch = context.recommendation_batch
            if batch is None:
                return rejected("请先调用 recommend_products 生成候选")
            if not batch.requires_semantic_ranking:
                return rejected("当前候选不需要语义终排")
            if context.semantic_reranker is None:
                return unavailable_payload("语义终排")
    
            try:
                ranking = validate_semantic_ranking(
                    await context.semantic_reranker.rerank(
                        batch=batch,
                        user_request=context.current_user_request,
                        environment_context=environment_context,
                    ),
                    batch,
                )
            except SemanticRerankError as exc:
                logger.warning("semantic reranking failed: %s", exc)
                fallback_candidates = (
                    batch.competitive_ads[:1]
                    if batch.ad_only
                    else batch.organic_candidates[:2]
                )
                selected = await commit_scored_products(
                    context,
                    fallback_candidates,
                    allow_ad_first=batch.ad_only,
                )
                return json.dumps(
                    {
                        "status": "fallback" if selected else "no_match",
                        "fallback_reason": str(exc),
                        "selected_products": [
                            product.model_dump(mode="json")
                            for product in selected
                        ],
                    },
                    ensure_ascii=False,
                )
    
            candidates_by_key = {
                (candidate.channel, candidate.product.id): candidate
                for candidate in semantic_candidates(batch)
            }
            selected_candidates = [
                candidates_by_key[(item.channel, item.product_id)]
                for item in ranking.items
            ]
            selected = await commit_scored_products(
                context,
                selected_candidates,
                allow_ad_first=batch.ad_only,
            )
            context.semantic_ranking = ranking
            return json.dumps(
                {
                    "status": "accepted" if selected else "no_match",
                    "semantic_ranking": ranking.model_dump(mode="json"),
                    "selected_products": [
                        product.model_dump(mode="json") for product in selected
                    ],
                },
                ensure_ascii=False,
            )
    
        @function_tool(
            name_override="update_plan",
            description_override=(
                "创建或整体替换当前 Plan 和 Plan State。状态、当前步骤、下一步、"
                "步骤完成情况和计划变更全部由模型决定。代码只保存模型提交的内容。"
            ),
            **tool_options,
        )
        async def update_plan_tool(
            plan: Plan,
            status: Literal["active", "completed", "blocked", "cancelled"],
            current_step_id: str | None,
            step_states: list[PlanStepState],
            summary: str,
            next_action: str | None,
        ) -> str:
            previous_revision = 0
            if (
                context.plan_state is not None
                and context.plan_state.plan.plan_id == plan.plan_id
            ):
                previous_revision = context.plan_state.revision
            context.plan_state = PlanState(
                plan=plan,
                status=status,
                current_step_id=current_step_id,
                step_states=step_states,
                summary=summary,
                next_action=next_action,
                revision=previous_revision + 1,
                updated_at=datetime.now(timezone.utc).isoformat(
                    timespec="milliseconds"
                ),
            )
            return json.dumps(
                {
                    "status": "saved",
                    "plan_state": context.plan_state.model_dump(mode="json"),
                },
                ensure_ascii=False,
            )
    
        tools = [
            understand_goal_tool,
            collect_recommendation_context_tool,
            generate_recommendation_spec_tool,
            search_organic_candidates_tool,
            search_ad_candidates_tool,
            recommend_products_tool,
            rerank_recommendations_tool,
            update_plan_tool,
            get_agent_profile_tool,
            get_platform_profile_tool,
            get_browse_history_tool,
            get_order_history_tool,
            get_cart_tool,
            get_product_recommendations_tool,
            get_ad_recommendations_tool,
            search_products_tool,
            get_product_tool,
            create_order_tool,
            get_order_tool,
        ]
        return instrument_tools(
            tools,
            get_observability_runtime().config.logs.tool,
        )
    
    
    def raw_item_value(item: Any, name: str) -> str | None:
        raw_item = getattr(item, "raw_item", None)
        if isinstance(raw_item, dict):
            value = raw_item.get(name)
        else:
    ✓ • 0ms

## Activity

    $ sed -n '1420,1665p' agent-service/src/agent_service/agent_runner.py
                            "type": "tool_started",
                            "message_id": message_id,
                            "call_id": call_id,
                            "tool": tool_name,
                            "arguments": arguments,
                        }
    
                    elif event.name == "tool_output":
                        tool_name = "tool"
                        call_id = event.item.call_id
                        trace_index = running_tools.get(call_id or "")
                        if trace_index is not None:
                            trace = context.tool_trace[trace_index]
                            tool_name = trace.tool
                            trace.status = "completed"
                            trace.summary = str(event.item.output)[:500]
                        yield {
                            "type": "tool_completed",
                            "message_id": message_id,
                            "call_id": call_id,
                            "tool": tool_name,
                        }
                        if (
                            tool_name == "update_plan"
                            and context.plan_state is not None
                        ):
                            yield {
                                "type": "plan_updated",
                                "message_id": message_id,
                                "plan_state": context.plan_state.model_dump(
                                    mode="json"
                                ),
                            }
                        if (
                            tool_name == "create_order"
                            and context.created_orders
                        ):
                            yield {
                                "type": "order_created",
                                "message_id": message_id,
                                "order": list(
                                    context.created_orders.values()
                                )[-1].model_dump(mode="json"),
                            }
                        if (
                            context.selected_products
                            and not recommendations_emitted
                        ):
                            recommendations_emitted = True
                            yield {
                                "type": "recommendations",
                                "message_id": message_id,
                                "products": [
                                    product.model_dump(mode="json")
                                    for product in (
                                        context.selected_products.values()
                                    )
                                ],
                            }
            if not content_parts and isinstance(result.final_output, str):
                content_parts.append(result.final_output)
                yield {
                    "type": "delta",
                    "message_id": message_id,
                    "content": result.final_output,
                }
            elif not content_parts and context.submitted and not context.selected_products:
                content_parts.append(NO_MATCH_REPLY)
                yield {
                    "type": "delta",
                    "message_id": message_id,
                    "content": NO_MATCH_REPLY,
                }
    
            if context.selected_products and not recommendations_emitted:
                recommendations_emitted = True
                yield {
                    "type": "recommendations",
                    "message_id": message_id,
                    "products": [
                        product.model_dump(mode="json")
                        for product in context.selected_products.values()
                    ],
                }
    
            trace_outcome = "completed"
            yield {
                "type": "done",
                "message_id": message_id,
                "tool_trace": [
                    trace.model_dump(mode="json") for trace in context.tool_trace
                ],
                "plan_state": (
                    context.plan_state.model_dump(mode="json")
                    if context.plan_state is not None
                    else None
                ),
                "orders": [
                    order.model_dump(mode="json")
                    for order in context.created_orders.values()
                ],
                "recommendations": [
                    product.model_dump(mode="json")
                    for product in context.selected_products.values()
                ],
                "goal_understanding": (
                    context.goal_understanding.model_dump(mode="json")
                    if context.goal_understanding is not None
                    else None
                ),
                "recommendation_spec": (
                    context.recommendation_spec.model_dump(mode="json")
                    if context.recommendation_spec is not None
                    else None
                ),
            }
        except PromptLoadError as exc:
            trace_session.finish("failed", exc)
            yield {
                "type": "error",
                "message_id": message_id,
                "message": f"Agent 提示词加载失败：{exc}",
                "tool_trace": [],
                "plan_state": (
                    context.plan_state.model_dump(mode="json")
                    if context.plan_state is not None
                    else None
                ),
                "orders": [
                    order.model_dump(mode="json")
                    for order in context.created_orders.values()
                ],
                "recommendations": [
                    product.model_dump(mode="json")
                    for product in context.selected_products.values()
                ],
                "goal_understanding": (
                    context.goal_understanding.model_dump(mode="json")
                    if context.goal_understanding is not None
                    else None
                ),
                "recommendation_spec": (
                    context.recommendation_spec.model_dump(mode="json")
                    if context.recommendation_spec is not None
                    else None
                ),
            }
        except MaxTurnsExceeded:
            trace_session.finish("failed")
            yield {
                "type": "error",
                "message_id": message_id,
                "message": (
                    f"Agent 超过最大工具回合数（{config.max_turns}），"
                    "当前多源推荐流程至少需要 10 个回合。"
                    "请将配置中的 max_turns 设为 10，并重启 Agent 服务。"
                ),
                "tool_trace": [
                    trace.model_dump(mode="json") for trace in context.tool_trace
                ],
                "plan_state": (
                    context.plan_state.model_dump(mode="json")
                    if context.plan_state is not None
                    else None
                ),
                "orders": [
                    order.model_dump(mode="json")
                    for order in context.created_orders.values()
                ],
                "recommendations": [
                    product.model_dump(mode="json")
                    for product in context.selected_products.values()
                ],
                "goal_understanding": (
                    context.goal_understanding.model_dump(mode="json")
                    if context.goal_understanding is not None
                    else None
                ),
                "recommendation_spec": (
                    context.recommendation_spec.model_dump(mode="json")
                    if context.recommendation_spec is not None
                    else None
                ),
            }
        except (asyncio.CancelledError, GeneratorExit):
            trace_outcome = "cancelled"
            raise
        except Exception as exc:
            trace_session.finish("failed", exc)
            logger.exception("Agents SDK run failed")
            yield {
                "type": "error",
                "message_id": message_id,
                "message": (
                    "Agent 调用失败，请检查模型服务是否支持 Chat Completions "
                    "工具调用，并查看 agent-service 终端日志。"
                ),
                "tool_trace": [
                    trace.model_dump(mode="json") for trace in context.tool_trace
                ],
                "plan_state": (
                    context.plan_state.model_dump(mode="json")
                    if context.plan_state is not None
                    else None
                ),
                "orders": [
                    order.model_dump(mode="json")
                    for order in context.created_orders.values()
                ],
                "recommendations": [
                    product.model_dump(mode="json")
                    for product in context.selected_products.values()
                ],
                "goal_understanding": (
                    context.goal_understanding.model_dump(mode="json")
                    if context.goal_understanding is not None
                    else None
                ),
                "recommendation_spec": (
                    context.recommendation_spec.model_dump(mode="json")
                    if context.recommendation_spec is not None
                    else None
                ),
            }
        finally:
            trace_session.finish(trace_outcome)
            if client is not None:
                await client.close()
    ✓ • 0ms

## Activity

    $ rg -n "semantic_ranking|reason|summary|recommendation_spec|selected_products" agent-service/tests agent-service/src/agent_service -g '*.py' | sed -n '1,280p'
    agent-service/tests/test_mall_contract.py:62:        goal_summary="寻找通勤商品",
    agent-service/tests/test_mall_contract.py:91:        goal_summary="用户跳过需求收集，按已有信息宽泛推荐",
    agent-service/src/agent_service/recommendation_scoring.py:434:            reason={
    agent-service/src/agent_service/recommendation_scoring.py:571:            requires_semantic_ranking=bool(competitive_ads),
    agent-service/src/agent_service/recommendation_scoring.py:583:        requires_semantic_ranking=bool(ad_top),
    agent-service/src/agent_service/recommendation_spec.py:28:    / "recommendation_spec.md"
    agent-service/src/agent_service/recommendation_spec.py:224:                action_name="recommendation_spec",
    agent-service/src/agent_service/llm_config.py:49:        """Keep enough output budget for tool calls and reasoned final replies."""
    agent-service/tests/test_agent_runner.py:43:from agent_service.recommendation_spec import AgentRecommendationSpecGenerator
    agent-service/tests/test_agent_runner.py:66:    summary: str = "准备收集推荐所需信息",
    agent-service/tests/test_agent_runner.py:122:        "summary": summary,
    agent-service/tests/test_agent_runner.py:157:    context.recommendation_spec = spec or recommendation_spec()
    agent-service/tests/test_agent_runner.py:247:            collection_reason="模型判断当前推荐需求状态",
    agent-service/tests/test_agent_runner.py:257:def recommendation_spec(
    agent-service/tests/test_agent_runner.py:262:        goal_summary="推荐预算 300 元以内的通勤商品",
    agent-service/tests/test_agent_runner.py:281:    spec = recommendation_spec(queries=["通勤"]).model_copy(
    agent-service/tests/test_agent_runner.py:317:                reason="符合当前需求",
    agent-service/tests/test_agent_runner.py:337:        requires_semantic_ranking=bool(ads),
    agent-service/tests/test_agent_runner.py:418:        summary="模型判断上下文收集完成，切换到召回步骤",
    agent-service/tests/test_agent_runner.py:567:        invoke_tool(context, "generate_recommendation_spec", {})
    agent-service/tests/test_agent_runner.py:608:                                "collection_reason": "还需要价格信息帮助筛选",
    agent-service/tests/test_agent_runner.py:679:                                "collection_reason": "用户明确要求直接推荐",
    agent-service/tests/test_agent_runner.py:713:def test_collect_context_and_generate_recommendation_spec_are_separate_actions(
    agent-service/tests/test_agent_runner.py:718:    context.recommendation_spec_generator = StaticRecommendationSpecGenerator(
    agent-service/tests/test_agent_runner.py:719:        recommendation_spec()
    agent-service/tests/test_agent_runner.py:730:            invoke_tool(context, "generate_recommendation_spec", {})
    agent-service/tests/test_agent_runner.py:736:    assert context.recommendation_spec is not None
    agent-service/tests/test_agent_runner.py:737:    assert context.recommendation_spec.search_queries == ["通勤", "办公室"]
    agent-service/tests/test_agent_runner.py:742:        == "agent.recommendation_spec.generated"
    agent-service/tests/test_agent_runner.py:744:    assert getattr(spec_log, "agent.recommendation_spec")[
    agent-service/tests/test_agent_runner.py:748:        getattr(spec_log, "agent.recommendation_spec.search_query_count")
    agent-service/tests/test_agent_runner.py:757:    context.recommendation_spec = recommendation_spec()
    agent-service/tests/test_agent_runner.py:776:def test_recommendation_spec_agent_uses_own_prompt_and_explicit_constraints() -> None:
    agent-service/tests/test_agent_runner.py:788:                            "goal_summary": "寻找通勤商品",
    agent-service/tests/test_agent_runner.py:850:        spec=recommendation_spec(queries=["家居", "居家"]),
    agent-service/tests/test_agent_runner.py:865:    assert context.recommendation_batch.requires_semantic_ranking is False
    agent-service/tests/test_agent_runner.py:866:    assert len(context.selected_products) == 2
    agent-service/tests/test_agent_runner.py:869:        for product in context.selected_products.values()
    agent-service/tests/test_agent_runner.py:876:    no_match_spec = recommendation_spec(queries=["宠物用品"]).model_copy(
    agent-service/tests/test_agent_runner.py:898:    assert context.selected_products == {}
    agent-service/tests/test_agent_runner.py:920:                    reason="更符合通勤用途",
    agent-service/tests/test_agent_runner.py:925:                    reason="补充办公室饮用场景",
    agent-service/tests/test_agent_runner.py:928:            summary="自然商品优先，广告作为补充",
    agent-service/tests/test_agent_runner.py:947:    assert len(context.selected_products) == 2
    agent-service/tests/test_agent_runner.py:948:    assert list(context.selected_products) == [
    agent-service/tests/test_agent_runner.py:952:    assert context.selected_products["portable-coffee"].is_ad is True
    agent-service/tests/test_agent_runner.py:953:    assert context.selected_products["portable-coffee"].ad_label == "广告"
    agent-service/tests/test_agent_runner.py:976:                    reason="分数更高",
    agent-service/tests/test_agent_runner.py:981:                    reason="符合通勤需求",
    agent-service/tests/test_agent_runner.py:1001:    assert "cannot be first" in result["fallback_reason"]
    agent-service/tests/test_agent_runner.py:1002:    assert list(context.selected_products) == ["commuter-backpack"]
    agent-service/tests/test_agent_runner.py:1019:                    reason="当前唯一符合需求的候选",
    agent-service/tests/test_agent_runner.py:1035:    assert list(context.selected_products) == ["portable-coffee"]
    agent-service/tests/test_agent_runner.py:1036:    assert context.selected_products["portable-coffee"].is_ad is True
    agent-service/tests/test_agent_runner.py:1066:                                    "reason": "首选自然商品",
    agent-service/tests/test_agent_runner.py:1071:                                    "reason": "补充办公室场景",
    agent-service/tests/test_agent_runner.py:1074:                            "summary": "自然商品优先",
    agent-service/tests/test_agent_runner.py:1168:                                "collection_reason": "还需要明确具体使用方式",
    agent-service/tests/test_agent_runner.py:1257:                                "collection_reason": "商品目标和预算已足够",
    agent-service/tests/test_agent_runner.py:1273:                    "generate_recommendation_spec",
    agent-service/tests/test_agent_runner.py:1282:                            "goal_summary": "推荐 300 元以内通勤商品",
    agent-service/tests/test_agent_runner.py:1346:                                    "reason": "通勤容量和电脑夹层更合适",
    agent-service/tests/test_agent_runner.py:1351:                                    "reason": "补充通勤饮水场景",
    agent-service/tests/test_agent_runner.py:1354:                            "summary": "自然商品优先，广告补充",
    agent-service/tests/test_agent_runner.py:1420:                summary="上一轮已经完成上下文收集",
    agent-service/src/agent_service/storage.py:317:        recommendation_spec: RecommendationSpec | None = None
    agent-service/src/agent_service/storage.py:318:        if isinstance(metadata.get("recommendation_spec"), dict):
    agent-service/src/agent_service/storage.py:320:                recommendation_spec = RecommendationSpec.model_validate(
    agent-service/src/agent_service/storage.py:321:                    metadata["recommendation_spec"]
    agent-service/src/agent_service/storage.py:324:                recommendation_spec = None
    agent-service/src/agent_service/storage.py:340:            recommendation_spec=recommendation_spec,
    agent-service/tests/test_recommendation_scoring.py:134:    assert batch.requires_semantic_ranking is True
    agent-service/tests/test_recommendation_scoring.py:150:def test_ad_only_path_requires_semantic_ranking() -> None:
    agent-service/tests/test_recommendation_scoring.py:156:    assert batch.requires_semantic_ranking is True
    agent-service/tests/test_recommendation_scoring.py:185:    assert batch.requires_semantic_ranking is False
    agent-service/tests/test_agent_api.py:76:    "summary": "已完成候选搜索",
    agent-service/tests/test_agent_api.py:132:        "collection_reason": "已有明确商品目标和预算，可以直接推荐",
    agent-service/tests/test_agent_api.py:137:    "goal_summary": "推荐通勤商品",
    agent-service/tests/test_agent_api.py:211:                "summary": "1 product",
    agent-service/tests/test_agent_api.py:218:        "recommendation_spec": RECOMMENDATION_SPEC,
    agent-service/tests/test_agent_api.py:300:    assert detail.messages[1].recommendation_spec is not None
    agent-service/tests/test_agent_api.py:301:    assert detail.messages[1].recommendation_spec.search_queries == [
    agent-service/src/agent_service/api.py:97:    recommendation_spec: RecommendationSpec | None = None
    agent-service/src/agent_service/api.py:123:        if recommendation_spec is not None:
    agent-service/src/agent_service/api.py:124:            metadata["recommendation_spec"] = recommendation_spec.model_dump(
    agent-service/src/agent_service/api.py:238:                spec_payload = event.get("recommendation_spec")
    agent-service/src/agent_service/api.py:240:                    recommendation_spec = RecommendationSpec.model_validate(
    agent-service/src/agent_service/api.py:279:                spec_payload = event.get("recommendation_spec")
    agent-service/src/agent_service/api.py:281:                    recommendation_spec = RecommendationSpec.model_validate(
    agent-service/src/agent_service/recommendation_reranker.py:74:def validate_semantic_ranking(
    agent-service/src/agent_service/recommendation_reranker.py:187:        return validate_semantic_ranking(ranking, batch)
    agent-service/src/agent_service/models.py:196:    collection_reason: str | None = Field(default=None, max_length=2_000)
    agent-service/src/agent_service/models.py:252:    goal_summary: str = Field(min_length=1, max_length=1_000)
    agent-service/src/agent_service/models.py:291:    reason: str = Field(min_length=1, max_length=300)
    agent-service/src/agent_service/models.py:310:    requires_semantic_ranking: bool = False
    agent-service/src/agent_service/models.py:319:    reason: str = Field(min_length=1, max_length=500)
    agent-service/src/agent_service/models.py:325:    summary: str = Field(default="", max_length=1_000)
    agent-service/src/agent_service/models.py:363:    summary: str = Field(default="", max_length=2_000)
    agent-service/src/agent_service/models.py:417:    summary: str | None = None
    agent-service/src/agent_service/models.py:430:    recommendation_spec: RecommendationSpec | None = None
    agent-service/src/agent_service/observability/agents.py:56:        "gen_ai.usage.reasoning_tokens": int(
    agent-service/src/agent_service/observability/agents.py:57:            getattr(output_details, "reasoning_tokens", 0) or 0
    agent-service/src/agent_service/observability/metrics.py:69:        reasoning_tokens = (
    agent-service/src/agent_service/observability/metrics.py:70:            getattr(output_details, "reasoning_tokens", 0) or 0
    agent-service/src/agent_service/observability/metrics.py:76:            ("reasoning", reasoning_tokens),
    agent-service/src/agent_service/agent_runner.py:74:    validate_semantic_ranking,
    agent-service/src/agent_service/agent_runner.py:77:from .recommendation_spec import (
    agent-service/src/agent_service/agent_runner.py:84:recommendation_spec_logger = logging.getLogger(
    agent-service/src/agent_service/agent_runner.py:132:    recommendation_spec: RecommendationSpec | None = None
    agent-service/src/agent_service/agent_runner.py:133:    recommendation_spec_generator: RecommendationSpecGenerator | None = None
    agent-service/src/agent_service/agent_runner.py:148:    semantic_ranking: SemanticRankingResult | None = None
    agent-service/src/agent_service/agent_runner.py:150:    selected_products: dict[str, Product] = field(default_factory=dict)
    agent-service/src/agent_service/agent_runner.py:211:    context.selected_products = selected
    agent-service/src/agent_service/agent_runner.py:420:    recommendation_spec_generator: RecommendationSpecGenerator | None = None,
    agent-service/src/agent_service/agent_runner.py:425:    if recommendation_spec_generator is not None:
    agent-service/src/agent_service/agent_runner.py:426:        context.recommendation_spec_generator = recommendation_spec_generator
    agent-service/src/agent_service/agent_runner.py:893:        name_override="generate_recommendation_spec",
    agent-service/src/agent_service/agent_runner.py:901:    async def generate_recommendation_spec_tool() -> str:
    agent-service/src/agent_service/agent_runner.py:916:        if context.recommendation_spec is not None:
    agent-service/src/agent_service/agent_runner.py:920:                    "recommendation_spec": (
    agent-service/src/agent_service/agent_runner.py:921:                        context.recommendation_spec.model_dump(mode="json")
    agent-service/src/agent_service/agent_runner.py:926:        if context.recommendation_spec_generator is None:
    agent-service/src/agent_service/agent_runner.py:929:            spec = await context.recommendation_spec_generator.generate(
    agent-service/src/agent_service/agent_runner.py:941:        context.recommendation_spec = spec
    agent-service/src/agent_service/agent_runner.py:950:        recommendation_spec_logger.debug(
    agent-service/src/agent_service/agent_runner.py:953:                "event": "agent.recommendation_spec.generated",
    agent-service/src/agent_service/agent_runner.py:954:                "agent.recommendation_spec": spec_payload,
    agent-service/src/agent_service/agent_runner.py:955:                "agent.recommendation_spec.search_query_count": len(
    agent-service/src/agent_service/agent_runner.py:958:                "agent.recommendation_spec.confidence": spec.confidence,
    agent-service/src/agent_service/agent_runner.py:964:                "recommendation_spec": spec.model_dump(mode="json"),
    agent-service/src/agent_service/agent_runner.py:980:        spec = context.recommendation_spec
    agent-service/src/agent_service/agent_runner.py:985:                "generate_recommendation_spec"
    agent-service/src/agent_service/agent_runner.py:1025:        spec = context.recommendation_spec
    agent-service/src/agent_service/agent_runner.py:1030:                "generate_recommendation_spec"
    agent-service/src/agent_service/agent_runner.py:1060:            "广告分数严格高于自然最低分时返回 requires_semantic_ranking，否则"
    agent-service/src/agent_service/agent_runner.py:1078:        spec = context.recommendation_spec
    agent-service/src/agent_service/agent_runner.py:1080:            return rejected("请先调用 generate_recommendation_spec")
    agent-service/src/agent_service/agent_runner.py:1095:        context.selected_products.clear()
    agent-service/src/agent_service/agent_runner.py:1096:        context.semantic_ranking = None
    agent-service/src/agent_service/agent_runner.py:1115:                "requires_semantic_ranking"
    agent-service/src/agent_service/agent_runner.py:1116:                if batch.requires_semantic_ranking
    agent-service/src/agent_service/agent_runner.py:1121:        if not batch.requires_semantic_ranking:
    agent-service/src/agent_service/agent_runner.py:1126:            response["selected_products"] = [
    agent-service/src/agent_service/agent_runner.py:1137:            "requires_semantic_ranking 后调用。它会使用独立 Prompt 综合公式"
    agent-service/src/agent_service/agent_runner.py:1149:        if not batch.requires_semantic_ranking:
    agent-service/src/agent_service/agent_runner.py:1155:            ranking = validate_semantic_ranking(
    agent-service/src/agent_service/agent_runner.py:1178:                    "fallback_reason": str(exc),
    agent-service/src/agent_service/agent_runner.py:1179:                    "selected_products": [
    agent-service/src/agent_service/agent_runner.py:1200:        context.semantic_ranking = ranking
    agent-service/src/agent_service/agent_runner.py:1204:                "semantic_ranking": ranking.model_dump(mode="json"),
    agent-service/src/agent_service/agent_runner.py:1205:                "selected_products": [
    agent-service/src/agent_service/agent_runner.py:1225:        summary: str,
    agent-service/src/agent_service/agent_runner.py:1239:            summary=summary,
    agent-service/src/agent_service/agent_runner.py:1257:        generate_recommendation_spec_tool,
    agent-service/src/agent_service/agent_runner.py:1352:        recommendation_spec_generator = AgentRecommendationSpecGenerator(
    agent-service/src/agent_service/agent_runner.py:1368:                recommendation_spec_generator=recommendation_spec_generator,
    agent-service/src/agent_service/agent_runner.py:1435:                        trace.summary = str(event.item.output)[:500]
    agent-service/src/agent_service/agent_runner.py:1465:                        context.selected_products
    agent-service/src/agent_service/agent_runner.py:1475:                                    context.selected_products.values()
    agent-service/src/agent_service/agent_runner.py:1486:        elif not content_parts and context.submitted and not context.selected_products:
    agent-service/src/agent_service/agent_runner.py:1494:        if context.selected_products and not recommendations_emitted:
    agent-service/src/agent_service/agent_runner.py:1501:                    for product in context.selected_products.values()
    agent-service/src/agent_service/agent_runner.py:1523:                for product in context.selected_products.values()
    agent-service/src/agent_service/agent_runner.py:1530:            "recommendation_spec": (
    agent-service/src/agent_service/agent_runner.py:1531:                context.recommendation_spec.model_dump(mode="json")
    agent-service/src/agent_service/agent_runner.py:1532:                if context.recommendation_spec is not None
    agent-service/src/agent_service/agent_runner.py:1554:                for product in context.selected_products.values()
    agent-service/src/agent_service/agent_runner.py:1561:            "recommendation_spec": (
    agent-service/src/agent_service/agent_runner.py:1562:                context.recommendation_spec.model_dump(mode="json")
    agent-service/src/agent_service/agent_runner.py:1563:                if context.recommendation_spec is not None
    agent-service/src/agent_service/agent_runner.py:1591:                for product in context.selected_products.values()
    agent-service/src/agent_service/agent_runner.py:1598:            "recommendation_spec": (
    agent-service/src/agent_service/agent_runner.py:1599:                context.recommendation_spec.model_dump(mode="json")
    agent-service/src/agent_service/agent_runner.py:1600:                if context.recommendation_spec is not None
    agent-service/src/agent_service/agent_runner.py:1631:                for product in context.selected_products.values()
    agent-service/src/agent_service/agent_runner.py:1638:            "recommendation_spec": (
    agent-service/src/agent_service/agent_runner.py:1639:                context.recommendation_spec.model_dump(mode="json")
    agent-service/src/agent_service/agent_runner.py:1640:                if context.recommendation_spec is not None
    ✓ • 0ms

## Activity

    $ sed -n '330,560p' agent-service/src/agent_service/api.py
                    "message": error_message,
                }
            )
        finally:
            if not persisted:
                store.finish_message(
                    assistant_message_id,
                    "".join(content_parts) or "客户端断开，回复未完成。",
                    "failed",
                    metadata=message_metadata(),
                )
                chat_outcome = "client_disconnected"
            chat.detach(chat_token)
            chat.end(chat_outcome, error=chat_error)
    
    
    async def configuration_error_stream(
        conversation_id: str,
        conversation_title: str,
        assistant_message_id: str,
        message: str,
        chat: ChatObservation,
    ) -> AsyncIterator[str]:
        chat.set_conversation(
            conversation_id=conversation_id,
            turn_id=assistant_message_id,
        )
        chat_token = chat.attach()
        try:
            yield sse_event(
                {
                    "type": "conversation",
                    "conversation_id": conversation_id,
                    "title": conversation_title,
                }
            )
            yield sse_event(
                {"type": "start", "message_id": assistant_message_id}
            )
            yield sse_event(
                {
                    "type": "error",
                    "message_id": assistant_message_id,
                    "message": message,
                }
            )
        finally:
            chat.detach(chat_token)
            chat.end("failed")
    
    
    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "agent-service"}
    
    
    @app.get("/api/conversations", response_model=ConversationList)
    def list_conversations(
        store: ConversationStore = Depends(get_conversation_store),
    ) -> ConversationList:
        return ConversationList(items=store.list_conversations(FIXED_USER_ID))
    
    
    @app.get(
        "/api/conversations/{conversation_id}",
        response_model=ConversationDetail,
    )
    def get_conversation(
        conversation_id: str,
        store: ConversationStore = Depends(get_conversation_store),
    ) -> ConversationDetail:
        conversation = store.get_conversation(FIXED_USER_ID, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="对话不存在")
        return conversation
    
    
    @app.post("/api/chat", response_model=ChatResponse)
    async def chat(
        request: ChatRequest,
        mall_client: MallClient = Depends(get_mall_client),
    ) -> ChatResponse:
        try:
            catalog = await mall_client.list_products()
            products = catalog.items
        except CatalogUnavailable:
            products = []
    
        return ChatResponse(
            reply=compose_reply(request.message, products),
            products=list(products[:3]),
        )
    
    
    @app.post("/api/chat/stream")
    async def stream_chat(
        request: StreamChatRequest,
        store: ConversationStore = Depends(get_conversation_store),
        mall: MallGateway = Depends(get_mall_client),
    ) -> StreamingResponse:
        chat = ChatObservation()
        try:
            with chat.active():
                if request.conversation_id:
                    conversation = store.get_conversation(
                        FIXED_USER_ID,
                        request.conversation_id,
                    )
                    if conversation is None:
                        raise HTTPException(status_code=404, detail="对话不存在")
                    conversation_id = conversation.id
                    title = conversation.title
                else:
                    conversation_id = store.create_conversation(
                        FIXED_USER_ID,
                        request.message,
                    )
                    conversation = store.get_conversation(
                        FIXED_USER_ID,
                        conversation_id,
                    )
                    if conversation is None:
                        raise HTTPException(
                            status_code=500,
                            detail="创建对话失败",
                        )
                    title = conversation.title
    
                store.add_message(
                    conversation_id,
                    "user",
                    request.message,
                    "completed",
                )
                context = store.model_context(conversation_id)
                assistant_message_id = store.add_message(
                    conversation_id,
                    "assistant",
                    "",
                    "streaming",
                )
                chat.set_conversation(
                    conversation_id=conversation_id,
                    turn_id=assistant_message_id,
                )
        except BaseException as exc:
            chat.end("failed", error=exc)
            raise
    
        try:
            config = load_llm_config()
        except LLMConfigError as exc:
            message = str(exc)
            store.finish_message(assistant_message_id, message, "failed")
            stream = configuration_error_stream(
                conversation_id,
                title,
                assistant_message_id,
                message,
                chat,
            )
        else:
            stream = persisted_agent_stream(
                conversation_id,
                title,
                assistant_message_id,
                context,
                config,
                store,
                mall,
                chat,
            )
    
        return StreamingResponse(
            stream,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    
    
    configure_observability(app)
    ✓ • 0ms

## Activity

    $ sed -n '1,220p' agent-service/pyproject.toml && sed -n '1,180p' agent-service/src/agent_service/main.py && sed -n '1,220p' agent-service/src/agent_service/llm_config.py
    [project]
    name = "agent-service"
    version = "0.1.0"
    description = "Shopping assistant agent HTTP service"
    requires-python = ">=3.11"
    dependencies = [
        "fastapi>=0.115,<1",
        "httpx>=0.27,<1",
        "openai-agents>=0.21,<1",
        "opentelemetry-api>=1.45,<2",
        "opentelemetry-exporter-prometheus>=0.66b0,<1",
        "opentelemetry-exporter-zipkin>=1.45,<2",
        "opentelemetry-instrumentation-fastapi>=0.66b0,<1",
        "opentelemetry-instrumentation-httpx>=0.66b0,<1",
        "opentelemetry-instrumentation-sqlite3>=0.66b0,<1",
        "opentelemetry-propagator-b3>=1.45,<2",
        "opentelemetry-sdk>=1.45,<2",
        "pyyaml>=6.0,<7",
        "uvicorn>=0.34,<1",
    ]
    
    [project.scripts]
    agent-service = "agent_service.main:run"
    
    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"
    
    [tool.hatch.build.targets.wheel]
    packages = ["src/agent_service"]
    import argparse
    import os
    from pathlib import Path
    
    import uvicorn
    
    
    def run() -> None:
        parser = argparse.ArgumentParser(description="Start the shopping agent service")
        parser.add_argument(
            "--config",
            help="Path to the service YAML config file",
        )
        parser.add_argument(
            "--reload",
            action="store_true",
            help="Reload Python source code when files change",
        )
        args = parser.parse_args()
    
        if args.config:
            os.environ["LLM_CONFIG_FILE"] = str(Path(args.config).expanduser().resolve())
    
        uvicorn.run(
            "agent_service.api:app",
            host=os.getenv("AGENT_SERVICE_HOST", "0.0.0.0"),
            port=int(os.getenv("AGENT_SERVICE_PORT", "8002")),
            reload=args.reload,
            reload_dirs=[str(Path(__file__).resolve().parent)] if args.reload else None,
        )
    import os
    from pathlib import Path
    
    import yaml
    from pydantic import (
        BaseModel,
        Field,
        SecretStr,
        ValidationError,
        field_validator,
    )
    
    
    class LLMConfigError(Exception):
        """Raised when the LLM configuration cannot be loaded or validated."""
    
    
    MIN_RECOMMENDATION_TURNS = 10
    MAX_RECOMMENDATION_TURNS = 100
    MIN_AGENT_OUTPUT_TOKENS = 32_768
    DEFAULT_LONG_TIMEOUT_SECONDS = 1_800
    MAX_LONG_TIMEOUT_SECONDS = 3_600
    
    
    class LLMConfig(BaseModel):
        base_url: str
        api_key: SecretStr
        model: str
        temperature: float | None = Field(default=None, ge=0, le=2)
        max_tokens: int | None = Field(default=None, gt=0)
        timeout_seconds: float = Field(
            default=DEFAULT_LONG_TIMEOUT_SECONDS,
            gt=0,
            le=MAX_LONG_TIMEOUT_SECONDS,
        )
        max_turns: int = Field(
            default=MIN_RECOMMENDATION_TURNS,
            ge=MIN_RECOMMENDATION_TURNS,
            le=MAX_RECOMMENDATION_TURNS,
        )
        tool_timeout_seconds: float = Field(
            default=DEFAULT_LONG_TIMEOUT_SECONDS,
            gt=0,
            le=DEFAULT_LONG_TIMEOUT_SECONDS,
        )
    
        @property
        def output_token_limit(self) -> int:
            """Keep enough output budget for tool calls and reasoned final replies."""
            return max(self.max_tokens or 0, MIN_AGENT_OUTPUT_TOKENS)
    
        @property
        def model_timeout_limit(self) -> float:
            return max(self.timeout_seconds, DEFAULT_LONG_TIMEOUT_SECONDS)
    
        @property
        def tool_timeout_limit(self) -> float:
            return max(self.tool_timeout_seconds, DEFAULT_LONG_TIMEOUT_SECONDS)
    
        @field_validator("base_url", "model")
        @classmethod
        def strip_text_fields(cls, value: str) -> str:
            value = value.strip()
            if not value:
                raise ValueError("value must not be blank")
            return value
    
        @field_validator("base_url")
        @classmethod
        def base_url_must_be_http(cls, value: str) -> str:
            if not value.startswith(("http://", "https://")):
                raise ValueError("base_url must start with http:// or https://")
            return value.rstrip("/")
    
        @field_validator("api_key")
        @classmethod
        def api_key_must_not_be_blank(cls, value: SecretStr) -> SecretStr:
            if not value.get_secret_value().strip():
                raise ValueError("api_key must not be blank")
            return value
    
    
    def resolve_config_path(config_path: str | Path | None = None) -> Path:
        configured_path = config_path or os.getenv("LLM_CONFIG_FILE")
        if not configured_path:
            raise LLMConfigError(
                "LLM config is not set; use --config or LLM_CONFIG_FILE"
            )
        return Path(configured_path).expanduser().resolve()
    
    
    def load_llm_config(config_path: str | Path | None = None) -> LLMConfig:
        path = resolve_config_path(config_path)
        try:
            with path.open("r", encoding="utf-8") as config_file:
                data = yaml.safe_load(config_file)
        except FileNotFoundError as exc:
            raise LLMConfigError(f"LLM config file not found: {path}") from exc
        except OSError as exc:
            raise LLMConfigError(f"cannot read LLM config file: {path}") from exc
        except (UnicodeDecodeError, yaml.YAMLError) as exc:
            raise LLMConfigError(f"invalid YAML in LLM config file: {path}") from exc
    
        if not isinstance(data, dict):
            raise LLMConfigError(f"config file must contain a mapping: {path}")
    
        llm_data = data.get("llm")
        if not isinstance(llm_data, dict):
            raise LLMConfigError(f"missing llm section in config file: {path}")
    
        try:
            config = LLMConfig.model_validate(llm_data)
        except ValidationError as exc:
            fields = ", ".join(
                ".".join(str(part) for part in error["loc"]) for error in exc.errors()
            )
            raise LLMConfigError(
                f"invalid LLM config file: {path} (fields: {fields})"
            ) from exc
    
        return config
    ✓ • 0ms

## Activity

    $ sed -n '1,260p' agent-service/tests/test_agent_api.py
    from pathlib import Path
    
    import pytest
    from fastapi.testclient import TestClient
    
    import agent_service.api as api_module
    from agent_service.api import app
    from agent_service.agent_runner import sse_event
    from agent_service.llm_config import LLMConfig, LLMConfigError
    from agent_service.mall_client import get_mall_client
    from agent_service.models import Product, ProductList
    from agent_service.storage import ConversationStore, get_conversation_store
    
    client = TestClient(app)
    
    TEST_CONFIG = LLMConfig(
        base_url="http://model.test/v1",
        api_key="test-key",
        model="test-model",
    )
    
    
    @pytest.fixture
    def store(tmp_path: Path) -> ConversationStore:
        conversation_store = ConversationStore(tmp_path / "agent-test.db")
        previous_overrides = app.dependency_overrides.copy()
        app.dependency_overrides[get_conversation_store] = lambda: conversation_store
        yield conversation_store
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
    
    
    class FakeMallClient:
        async def list_products(self) -> ProductList:
            products = [
                Product(
                    id="tote",
                    name="帆布托特包",
                    description="日常通勤",
                    price_cents=6900,
                    category="文创",
                )
            ]
            return ProductList(items=products, total=1)
    
    
    PLAN_STATE = {
        "plan": {
            "plan_id": "plan-test",
            "goal": "找到合适的商品",
            "steps": [
                {
                    "step_id": "search",
                    "title": "搜索商品",
                    "objective": "获取候选商品",
                    "kind": "retrieval",
                    "depends_on": [],
                    "metadata": {},
                },
                {
                    "step_id": "submit",
                    "title": "提交推荐",
                    "objective": "生成最终推荐",
                    "kind": "decision",
                    "depends_on": ["search"],
                    "metadata": {},
                },
            ],
        },
        "status": "active",
        "current_step_id": "submit",
        "step_states": [
            {"step_id": "search", "status": "completed", "note": "找到 1 件商品"},
            {"step_id": "submit", "status": "in_progress", "note": None},
        ],
        "summary": "已完成候选搜索",
        "next_action": "提交最终推荐",
        "revision": 2,
        "updated_at": "2026-11-02T12:00:00+00:00",
    }
    
    ORDER_LINK = {
        "order_id": "order-test",
        "status": "pending_payment",
        "total_cents": 6900,
        "preview_path": "/orders/order-test",
        "ordered_at": "2026-11-02T12:10:00+00:00",
    }
    
    RECOMMENDED_PRODUCT = {
        "id": "tote",
        "name": "帆布托特包",
        "description": "通勤包",
        "price_cents": 6900,
        "category": "箱包",
        "badge": "人气单品",
        "stock": 10,
        "tags": ["通勤"],
        "image_url": None,
        "is_ad": True,
        "ad_label": "广告",
        "ad_id": "ad-test",
        "campaign_id": "campaign-test",
    }
    
    GOAL_UNDERSTANDING = {
        "primary_intent": "product_recommendation",
        "intents": ["product_recommendation", "order_query"],
        "pending_intents": ["order_query"],
        "goal": "推荐商品并查询订单",
        "confidence": 0.95,
        "slots": {"query": "通勤"},
        "missing_slots": [],
        "requires_clarification": False,
        "clarification_question": None,
        "pending_intent_question": "是否继续处理订单查询？",
        "recommendation_requirements": {
            "status": "ready",
            "slots": {
                "query": "通勤",
                "category": None,
                "min_price_cents": None,
                "max_price_cents": 30000,
                "required_tags": [],
                "excluded_tags": [],
                "scenario": "self",
                "usage": "通勤",
                "recipient": None,
            },
            "next_question": None,
            "declined_requirements": [],
            "collection_reason": "已有明确商品目标和预算，可以直接推荐",
        },
    }
    
    RECOMMENDATION_SPEC = {
        "goal_summary": "推荐通勤商品",
        "hard_constraints": {
            "category": None,
            "min_price_cents": None,
            "max_price_cents": 30000,
            "required_tags": [],
            "excluded_tags": [],
        },
        "preferred_categories": ["箱包"],
        "preferred_tags": ["通勤"],
        "weak_categories": [],
        "negative_tags": [],
        "search_queries": ["通勤", "办公室"],
        "scenario": "self",
        "usage": "通勤",
        "recipient": None,
        "source_evidence": [],
        "confidence": 0.9,
        "missing_information": [],
    }
    
    
    async def fake_agent_stream(
        messages,
        config,
        mall,
        previous_plan_state=None,
        previous_recommendations=None,
        previous_orders=None,
        previous_goal_understanding=None,
    ):
        yield {"type": "start", "message_id": "assistant-test"}
        yield {
            "type": "tool_started",
            "message_id": "assistant-test",
            "call_id": "call-1",
            "tool": "search_products",
            "arguments": '{"query":"通勤"}',
        }
        yield {
            "type": "tool_completed",
            "message_id": "assistant-test",
            "call_id": "call-1",
            "tool": "search_products",
        }
        yield {
            "type": "plan_updated",
            "message_id": "assistant-test",
            "plan_state": PLAN_STATE,
        }
        yield {
            "type": "order_created",
            "message_id": "assistant-test",
            "order": ORDER_LINK,
        }
        yield {
            "type": "recommendations",
            "message_id": "assistant-test",
            "products": [RECOMMENDED_PRODUCT],
        }
        yield {
            "type": "delta",
            "message_id": "assistant-test",
            "content": "真实模型回复",
        }
        yield {
            "type": "done",
            "message_id": "assistant-test",
            "tool_trace": [
                {
                    "call_id": "call-1",
                    "tool": "search_products",
                    "arguments": '{"query":"通勤"}',
                    "status": "completed",
                    "summary": "1 product",
                }
            ],
            "plan_state": PLAN_STATE,
            "orders": [ORDER_LINK],
            "recommendations": [RECOMMENDED_PRODUCT],
            "goal_understanding": GOAL_UNDERSTANDING,
            "recommendation_spec": RECOMMENDATION_SPEC,
        }
    
    
    def test_health() -> None:
        response = client.get("/health")
    
        assert response.status_code == 200
        assert response.json()["service"] == "agent-service"
    
    
    def test_chat_uses_mall_catalog() -> None:
        previous_overrides = app.dependency_overrides.copy()
        app.dependency_overrides[get_mall_client] = lambda: FakeMallClient()
        try:
            response = client.post("/api/chat", json={"message": "推荐一件商品"})
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)
    
        assert response.status_code == 200
        assert "帆布托特包" in response.json()["reply"]
        assert response.json()["products"][0]["id"] == "tote"
    
    
    def test_chat_rejects_blank_message() -> None:
        response = client.post("/api/chat", json={"message": "   "})
    
        assert response.status_code == 422
    
    
    def test_stream_chat_persists_completed_conversation(
        store: ConversationStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            api_module,
            "load_llm_config",
            lambda: TEST_CONFIG,
        )
        monkeypatch.setattr(api_module, "stream_agent_reply", fake_agent_stream)
    
        response = client.post(
    ✓ • 0ms

## Activity

    $ sed -n '1,240p' agent-service/tests/test_storage.py
    import sqlite3
    from pathlib import Path
    
    from agent_service.storage import ConversationStore
    
    
    def test_model_context_excludes_failed_assistant_messages(
        tmp_path: Path,
    ) -> None:
        store = ConversationStore(tmp_path / "history.db")
        conversation_id = store.create_conversation(1, "第一轮")
        store.add_message(conversation_id, "user", "第一轮", "completed")
        store.add_message(conversation_id, "assistant", "成功回复", "completed")
        store.add_message(conversation_id, "user", "第二轮", "completed")
        store.add_message(conversation_id, "assistant", "失败回复", "failed")
    
        context = store.model_context(conversation_id)
    
        assert [message.content for message in context] == [
            "第一轮",
            "成功回复",
            "第二轮",
        ]
    
    
    def test_interrupted_stream_is_recovered_as_failed(tmp_path: Path) -> None:
        database_path = tmp_path / "recovery.db"
        store = ConversationStore(database_path)
        conversation_id = store.create_conversation(1, "中断")
        message_id = store.add_message(
            conversation_id,
            "assistant",
            "",
            "streaming",
        )
    
        recovered_store = ConversationStore(database_path)
        conversation = recovered_store.get_conversation(1, conversation_id)
    
        assert conversation is not None
        assert conversation.messages[0].id == message_id
        assert conversation.messages[0].status == "failed"
    
    
    def test_existing_database_is_migrated_with_message_metadata(
        tmp_path: Path,
    ) -> None:
        database_path = tmp_path / "legacy.db"
        with sqlite3.connect(database_path) as connection:
            connection.executescript(
                """
                CREATE TABLE conversations (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    status TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                INSERT INTO conversations
                    VALUES ('conversation-old', 1, '旧对话', '2026-01-01', '2026-01-01');
                INSERT INTO messages
                    VALUES (
                        'message-old',
                        'conversation-old',
                        'assistant',
                        '旧回复',
                        'completed',
                        1,
                        '2026-01-01'
                    );
                """
            )
    
        store = ConversationStore(database_path)
        conversation = store.get_conversation(1, "conversation-old")
    
        assert conversation is not None
        assert conversation.messages[0].content == "旧回复"
        assert conversation.messages[0].recommendations == []
        assert conversation.messages[0].tool_trace == []
    ✓ • 0ms

## Assistant

当前有一个关键缺口：语义终排的 `reason` 只存在于本次 Agent 运行上下文，没有写入消息元数据，因此历史总结无法可靠取得最终推荐理由。方案会把“推荐决策记录”补齐为持久化输入，同时保持现有推荐流程和前端协议兼容。

## Activity

    $ ls -la agent-service | sed -n '1,120p' && find agent-service -maxdepth 2 -type f -name '*.toml' -o -name '*.ini' -o -name '*.cfg' | sort
    total 16
    drwxr-xr-x@  9 mindeng  staff  288 Nov  1 21:24 .
    drwxr-xr-x@ 21 mindeng  staff  672 Nov 11 20:48 ..
    -rw-r--r--@  1 mindeng  staff  178 Nov  1 20:58 .env.example
    drwxr-xr-x@  3 mindeng  staff   96 Nov  1 20:52 config
    drwxr-xr-x@  5 mindeng  staff  160 Nov 11 20:46 data
    drwxr-xr-x@  6 mindeng  staff  192 Nov  5 20:42 prompts
    -rw-r--r--@  1 mindeng  staff  852 Nov  8 20:28 pyproject.toml
    drwxr-xr-x@  3 mindeng  staff   96 Nov  1 20:13 src
    drwxr-xr-x@ 13 mindeng  staff  416 Nov  8 20:34 tests
    agent-service/pyproject.toml
    ✓ • 0ms

## Activity

    $ sed -n '180,360p' agent-service/src/agent_service/recommendation_reranker.py
                ranking = SemanticRankingResult.model_validate(
                    _json_payload(result.final_output)
                )
            except ValidationError as exc:
                raise SemanticRerankError(
                    "semantic recommendation reranker returned invalid data"
                ) from exc
            return validate_semantic_ranking(ranking, batch)
    ✓ • 0ms

## Activity

    $ sed -n '1,220p' agent-service/prompts/recommendation_reranker.md
    # 商品推荐语义终排器
    
    你只负责对已经通过公式筛选和资格校验的商品候选进行语义终排，不负责查询商品、修改分数或创建订单。
    
    ## 输入
    
    你会收到一个 JSON 对象，包含：
    
    - `user_request`：当前用户请求；
    - `demand`：结构化需求；
    - `environment_context`：调用方提供的环境信息，可能为空；
    - `cutoff_score`：自然推荐最低分；
    - `ad_only`：是否没有自然推荐候选；
    - `candidates`：自然推荐和广告混排后的单一候选池，含公式分数、来源、证据、价格、
      库存、标签和广告信息。
    
    只能选择 `candidates` 中出现的商品，不能添加新商品。
    
    不要将自然商品和广告商品分别排序。应在同一个候选池中完成统一比较，再应用下面
    的数量和顺序约束。
    
    ## 排序原则
    
    1. 用户当前明确需求、预算、用途和排除项优先。
    2. 公式分数是重要先验，但不是唯一依据。
    3. 同时比较商品语义、实际场景、价格、库存、使用便利性、礼物属性、品类多样性和候选间的取舍。
    4. `environment_context` 中提供了可信环境信息时可以使用；没有提供时不得自行编造天气、节日、物流、销量或库存。
    5. 推荐理由要具体，并结合分数证据与语义判断，不要只复述“分数最高”。
    6. 广告身份不提供额外偏好，也不得因为商业来源被优先选择。
    
    ## 数量与顺序
    
    - 自然推荐商品最多 2 个。
    - 广告商品最多 1 个。
    - 总计最多 3 个。
    - 宁缺毋滥，可以少于上限，也可以返回空列表。
    - 只要存在自然推荐候选，列表中第一个商品必须是自然推荐，广告只能排在自然推荐之后。
    - 只有 `ad_only = true` 时，广告才可以成为第一个或唯一商品。
    - 需要付出取舍时，优先保留更符合当前需求且理由清晰的自然商品。
    
    ## 输出
    
    只输出 JSON，不要输出 Markdown 或额外说明：
    
    ```json
    {
      "items": [
        {
          "product_id": "商品 ID",
          "channel": "organic",
          "reason": "最终推荐理由",
          "environmental_fit": "可选的环境或场景匹配说明"
        }
      ],
      "summary": "一句话说明本次终排的核心取舍"
    }
    ```
    
    `channel` 必须为 `organic` 或 `ad`，且必须与输入候选完全一致。
    ✓ • 0ms

## Activity

    $ sed -n '1,180p' agent-service/src/agent_service/observability/serialization.py && sed -n '1,180p' agent-service/src/agent_service/observability/agents.py
    import json
    from collections.abc import Mapping, Sequence
    from enum import Enum
    from typing import Any
    
    
    REDACTED = "[REDACTED]"
    
    
    def json_safe(value: Any, *, max_length: int = 0) -> Any:
        if value is None or isinstance(value, (bool, int, float, str)):
            if isinstance(value, str) and max_length > 0 and len(value) > max_length:
                return value[:max_length] + "...[truncated]"
            return value
        if isinstance(value, Enum):
            return value.name
        if isinstance(value, BaseException):
            return f"{type(value).__name__}: {value}"
        if isinstance(value, Mapping):
            return {
                str(key): json_safe(item, max_length=max_length)
                for key, item in value.items()
            }
        if isinstance(value, Sequence) and not isinstance(
            value, (str, bytes, bytearray)
        ):
            return [
                json_safe(item, max_length=max_length) for item in value
            ]
        model_dump = getattr(value, "model_dump", None)
        if callable(model_dump):
            try:
                return json_safe(
                    model_dump(mode="json"),
                    max_length=max_length,
                )
            except Exception:
                pass
        try:
            return json_safe(dict(value), max_length=max_length)
        except (TypeError, ValueError):
            return str(value)[:max_length] if max_length > 0 else str(value)
    
    
    def redact_payload(
        value: Any,
        *,
        redact_keys: Sequence[str],
        max_length: int,
    ) -> Any:
        normalized_keys = {key.lower() for key in redact_keys}
    
        def walk(item: Any) -> Any:
            if isinstance(item, Mapping):
                return {
                    str(key): (
                        REDACTED
                        if str(key).lower() in normalized_keys
                        else walk(child)
                    )
                    for key, child in item.items()
                }
            if isinstance(item, Sequence) and not isinstance(
                item, (str, bytes, bytearray)
            ):
                return [walk(child) for child in item]
            return json_safe(item, max_length=max_length)
    
        return walk(value)
    
    
    def payload_text(value: Any) -> str:
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            return str(value)
    
    
    def truncate_text(value: str, max_length: int) -> str:
        if max_length <= 0 or len(value) <= max_length:
            return value
        return value[:max_length] + "...[truncated]"
    import asyncio
    import contextvars
    import json
    import logging
    import time
    from contextlib import contextmanager
    from functools import wraps
    from typing import Any, Iterator, Sequence
    
    from agents import RawResponsesStreamEvent, RunHooks, Runner
    from agents.tool_context import ToolContext
    from openai.types.responses import ResponseTextDeltaEvent
    from opentelemetry import trace
    from opentelemetry.context import attach, detach
    from opentelemetry.trace import Span, Status, StatusCode
    
    from .config import ToolLogConfig
    from .serialization import (
        json_safe,
        payload_text,
        redact_payload,
        truncate_text,
    )
    from .spans import get_runtime_metrics, get_tracer
    
    
    tool_logger = logging.getLogger("agent_service.observability.tool")
    
    
    def _elapsed_ms(start_ns: int) -> float:
        return round((time.monotonic_ns() - start_ns) / 1_000_000, 3)
    
    
    def _elapsed_seconds(start_ns: int) -> float:
        return max(0, time.monotonic_ns() - start_ns) / 1_000_000_000
    
    
    def _usage_attributes(usage: Any) -> dict[str, int]:
        if usage is None:
            return {}
        input_details = getattr(usage, "input_tokens_details", None)
        output_details = getattr(usage, "output_tokens_details", None)
        return {
            "gen_ai.usage.input_tokens": int(
                getattr(usage, "input_tokens", 0) or 0
            ),
            "gen_ai.usage.output_tokens": int(
                getattr(usage, "output_tokens", 0) or 0
            ),
            "gen_ai.usage.total_tokens": int(
                getattr(usage, "total_tokens", 0) or 0
            ),
            "gen_ai.usage.cached_input_tokens": int(
                getattr(input_details, "cached_tokens", 0) or 0
            ),
            "gen_ai.usage.reasoning_tokens": int(
                getattr(output_details, "reasoning_tokens", 0) or 0
            ),
        }
    
    
    class AgentTraceSession:
        """Tracks ReAct and LLM spans for one streamed top-level run."""
    
        def __init__(
            self,
            *,
            model: str,
            parent_context: Any | None = None,
        ) -> None:
            self.model = model
            self.parent_context = parent_context
            self.react_index = 0
            self.tool_count = 0
            self.react_span: Span | None = None
            self.react_context: Any | None = None
            self.react_start_ns = 0
            self.llm_span: Span | None = None
            self.llm_start_ns = 0
            self.llm_first_char_recorded = False
            self.llm_first_output_recorded = False
            self.llm_output_chars = 0
            self.finished = False
    
        def start_llm(self) -> None:
            if self.finished:
                return
            if self.react_span is None:
                self.react_index += 1
                self.react_start_ns = time.monotonic_ns()
                self.react_span = get_tracer().start_span(
                    "agent.react",
                    context=self.parent_context,
                )
                self.react_span.set_attribute(
                    "agent.react.index",
                    self.react_index,
                )
                self.react_context = trace.set_span_in_context(
                    self.react_span,
                    self.parent_context,
                )
            if self.llm_span is not None:
                self._finish_llm("aborted")
            self.llm_start_ns = time.monotonic_ns()
            self.llm_first_char_recorded = False
            self.llm_first_output_recorded = False
            self.llm_output_chars = 0
            self.llm_span = get_tracer().start_span(
                "agent.llm",
                context=self.react_context,
            )
            self.llm_span.set_attribute("gen_ai.operation.name", "chat")
            self.llm_span.set_attribute(
                "gen_ai.request.model",
                self.model,
            )
            self.llm_span.set_attribute("agent.react.index", self.react_index)
            self.llm_span.set_attribute("agent.llm.streaming", True)
    
        def observe_model_event(self, event: Any) -> None:
            if self.llm_span is None:
                return
            event_type = getattr(event, "type", "")
            if event_type in {
                "response.output_item.added",
                "response.function_call_arguments.delta",
                "response.output_item.done",
            }:
                self._record_first_output()
            if isinstance(event, ResponseTextDeltaEvent):
                delta = event.delta or ""
                self.llm_output_chars += len(delta)
                if delta:
                    self._record_first_output()
                    self._record_first_char()
    
        def _record_first_output(self) -> None:
            if self.llm_first_output_recorded or self.llm_span is None:
                return
            self.llm_first_output_recorded = True
            elapsed = _elapsed_seconds(self.llm_start_ns)
            self.llm_span.set_attribute(
                "agent.llm.first_output_ms",
                elapsed * 1000,
            )
            runtime_metrics = get_runtime_metrics()
            if runtime_metrics is not None:
                runtime_metrics.llm_first_output.record(
                    elapsed,
                    {"gen_ai.request.model": self.model},
                )
    
        def _record_first_char(self) -> None:
            if self.llm_first_char_recorded or self.llm_span is None:
                return
            self.llm_first_char_recorded = True
            elapsed = _elapsed_seconds(self.llm_start_ns)
            self.llm_span.set_attribute(
                "agent.llm.first_char_ms",
                elapsed * 1000,
            )
            runtime_metrics = get_runtime_metrics()
            if runtime_metrics is not None:
                runtime_metrics.llm_first_char.record(
                    elapsed,
                    {"gen_ai.request.model": self.model},
                )
    
        def finish_llm(
            self,
            response: Any,
            *,
            outcome: str = "completed",
        ) -> None:
            if self.llm_span is None:
                return
            usage = getattr(response, "usage", None)
            attrs = _usage_attributes(usage)
            for key, value in attrs.items():
    ✓ • 0ms

## Activity

    $ rg -n "async def run_observed_action|def run_observed_action" agent-service/src/agent_service/observability/agents.py && sed -n '300,470p' agent-service/src/agent_service/observability/agents.py
    657:async def run_observed_action(
                _current_agent_session.reset(token)
    
    
    class ObservabilityRunHooks(RunHooks[Any]):
        def __init__(
            self,
            session: AgentTraceSession,
        ) -> None:
            self.session = session
    
        async def on_llm_start(
            self,
            context: Any,
            agent: Any,
            system_prompt: str | None,
            input_items: Any,
        ) -> None:
            if self.session.react_span is not None:
                self.session.finish_react("completed")
            self.session.start_llm()
    
        async def on_llm_end(
            self,
            context: Any,
            agent: Any,
            response: Any,
        ) -> None:
            self.session.record_token_usage(getattr(response, "usage", None))
            self.session.finish_llm(response)
    
    
    _current_agent_session: contextvars.ContextVar[
        AgentTraceSession | None
    ] = contextvars.ContextVar("agent_trace_session", default=None)
    
    
    def current_agent_session() -> AgentTraceSession | None:
        return _current_agent_session.get()
    
    
    def _parse_tool_result(result: Any) -> tuple[dict[str, Any] | str, str]:
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
            except json.JSONDecodeError:
                return result, "success"
            if isinstance(parsed, dict):
                status = str(parsed.get("status", ""))
                outcome = (
                    "business_error"
                    if status in {"rejected", "unavailable", "no_match"}
                    else "success"
                )
                return parsed, outcome
            return result, "success"
        if isinstance(result, dict):
            status = str(result.get("status", ""))
            outcome = (
                "business_error"
                if status in {"rejected", "unavailable", "no_match"}
                else "success"
            )
            return result, outcome
        return json_safe(result), "success"
    
    
    def instrument_tools(
        tools: Sequence[Any],
        tool_log_config: ToolLogConfig,
    ) -> list[Any]:
        for tool in tools:
            original = getattr(tool, "on_invoke_tool", None)
            if original is None or getattr(original, "_observability_wrapped", False):
                continue
    
            @wraps(original)
            async def observed(
                context: ToolContext[Any],
                arguments: str,
                *,
                _original: Any = original,
                _tool: Any = tool,
            ) -> Any:
                session = current_agent_session()
                if session is None:
                    return await _original(context, arguments)
    
                call_id = context.tool_call_id or ""
                tool_name = context.tool_name or getattr(_tool, "name", "tool")
                parent_context = session.react_context
                span = get_tracer().start_span(
                    "agent.tool",
                    context=parent_context,
                )
                span.set_attribute("gen_ai.tool.name", tool_name)
                span.set_attribute("agent.tool.name", tool_name)
                span.set_attribute("tool.call_id", call_id)
                span.set_attribute("agent.react.index", session.react_index)
                start_ns = time.monotonic_ns()
                session.record_tool()
                tool_token = attach(trace.set_span_in_context(span))
    
                raw_arguments: Any = arguments
                try:
                    raw_arguments = json.loads(arguments)
                except (json.JSONDecodeError, TypeError):
                    pass
                logged_arguments = redact_payload(
                    raw_arguments,
                    redact_keys=tool_log_config.redact_keys,
                    max_length=tool_log_config.max_payload_chars,
                )
                tool_logger.debug(
                    "Tool call started",
                    extra={
                        "event": "agent.tool.started",
                        "tool.name": tool_name,
                        "tool.call_id": call_id,
                        "agent.react.index": session.react_index,
                        "tool.arguments": (
                            logged_arguments
                            if tool_log_config.include_arguments
                            else "[disabled]"
                        ),
                    },
                )
    
                status = "failed"
                result_payload: Any = None
                result_text = ""
                try:
                    result = await _original(context, arguments)
                    result_payload, status = _parse_tool_result(result)
                    result_text = payload_text(result_payload)
                    return result
                except BaseException as exc:
                    if isinstance(exc, asyncio.TimeoutError):
                        status = "timeout"
                    elif isinstance(exc, asyncio.CancelledError):
                        status = "cancelled"
                    else:
                        status = "failed"
                    span.record_exception(exc)
                    span.set_status(Status(StatusCode.ERROR, str(exc)))
                    raise
                finally:
                    duration = _elapsed_ms(start_ns)
                    outcome = status
                    span.set_attribute("agent.tool.outcome", outcome)
                    span.set_attribute("agent.tool.duration_ms", duration)
                    if outcome in {"success", "business_error"}:
                        span.set_status(Status(StatusCode.OK))
                    tool_logger.debug(
                        "Tool call finished",
                        extra={
                            "event": (
                                "agent.tool.completed"
                                if outcome in {"success", "business_error"}
                                else "agent.tool.failed"
                            ),
                            "tool.name": tool_name,
                            "tool.call_id": call_id,
                            "agent.react.index": session.react_index,
                            "tool.status": outcome,
                            "duration_ms": duration,
                            "result_size": len(result_text),
                            "result_truncated": (
                                tool_log_config.max_payload_chars > 0
                                and len(result_text)
                                > tool_log_config.max_payload_chars
                            ),
    ✓ • 0ms

## Activity

    $ sed -n '640,760p' agent-service/src/agent_service/observability/agents.py
                    },
                )
                runtime_metrics.llm_calls.add(
                    1,
                    {
                        "gen_ai.request.model": self.model,
                        "operation": "chat",
                        "outcome": outcome,
                    },
                )
                if usage is not None:
                    runtime_metrics.record_token_usage(
                        usage,
                        {"gen_ai.request.model": self.model},
                    )
    
    
    async def run_observed_action(
        agent: Any,
        *,
        action_name: str,
        model: str,
        input: Any,
        max_turns: int = 1,
    ) -> Any:
        observation = ActionObservation(action_name, model)
        result: Any = None
        try:
            with observation.active():
                result = Runner.run_streamed(
                    agent,
                    input=input,
                    max_turns=max_turns,
                    run_config=_run_config(),
                )
                async for event in result.stream_events():
                    if isinstance(event, RawResponsesStreamEvent):
                        observation.observe_event(event.data)
        except BaseException as exc:
            observation.finish(result, error=exc)
            raise
        observation.finish(result)
        return result
    
    
    def _run_config() -> Any:
        from agents import RunConfig
    
        return RunConfig(tracing_disabled=True)
    ✓ • 0ms

## Assistant

## 设计结论

这一版定义为：**对单个多轮对话生成一份可持久化、可追溯、可重新生成的购物对话总结**。总结既要有人能阅读的摘要，也要有后续画像模块可以直接消费的结构化数据。

首版不建设用户画像，不做跨会话合并、不做冲突消解、不做时间衰减，也不改变现有推荐流程。

整体链路：

```text
对话消息
+ 推荐商品快照
+ 语义终排理由
+ 用户表达
        ↓
规范化对话输入
        ↓
一次 LLM 提取
        ↓
Schema 和来源校验
        ↓
合并确定性商品数据
        ↓
保存 ConversationDigest
```

## 一、需要补齐推荐决策数据

当前 `semantic_ranking.reason` 只存在于 Agent 运行上下文，完成事件和消息元数据中没有保存。因此需要新增一个与商品目录信息分离的“最终推荐决策”结构：

```text
FinalRecommendation
- product_id
- rank
- channel: organic | ad
- reason
- reason_source: semantic_reranker | formula_scoring | unavailable
- environmental_fit
```

- 语义终排成功时，直接保存 `SemanticRankingItem.reason`，不经过总结模型改写。
- 公式推荐路径没有大模型终排，保存公式证据生成的简要理由，并标记为 `formula_scoring`。
- 终排失败后的 fallback 同样保存公式理由。
- 历史旧对话没有结构化终排理由时，标记为 `unavailable`，不伪造理由。
- 现有 `recommendations` 元数据和前端事件格式保持兼容，新增字段只作为附加信息。

这样后续总结输入中就同时具备“推荐了什么商品”和“为什么最终推荐它”。

## 二、总结输出模型

建议新增 `ConversationDigest`，结构大致如下：

```json
{
  "conversation_id": "conversation-xxx",
  "summary": "用户寻找通勤包，Agent 推荐了两款商品……",
  "user_goals": ["寻找预算 1000 元以内的通勤包"],
  "explicit_constraints": ["预算不超过 1000 元"],
  "recommendation_rounds": [
    {
      "assistant_message_id": "message-xxx",
      "user_request": "给我推荐一个轻一点的通勤包",
      "ranking_summary": "优先考虑轻量和通勤容量",
      "products": [
        {
          "product_id": "bag-001",
          "product_snapshot": {},
          "key_information": [
            {
              "name": "尺寸",
              "value": "大号",
              "source_field": "description",
              "source_text": "大号容量，可放 16 英寸电脑"
            }
          ],
          "reason": "轻量且容量适合日常通勤",
          "reason_source": "semantic_reranker",
          "environmental_fit": null
        }
      ]
    }
  ],
  "product_feedback": [
    {
      "product_id": "bag-001",
      "overall": "negative",
      "aspects": [
        {
          "name": "尺寸",
          "value": "偏大",
          "polarity": "negative"
        }
      ],
      "evidence": {
        "message_id": "message-user-xxx",
        "quote": "这个黑色款太大了，我不喜欢"
      },
      "confidence": 0.98
    }
  ],
  "general_preferences": [
    {
      "dimension": "重量",
      "value": "偏轻",
      "polarity": "prefer",
      "evidence": {
        "message_id": "message-user-xxx",
        "quote": "我一般也不喜欢太重的包"
      },
      "confidence": 0.95
    }
  ],
  "unresolved_items": []
}
```

几个关键设计原则：

- 商品列表、商品快照和终排理由由代码确定性组装，不依赖总结模型完整复述。
- 总结模型主要负责提取用户目标、商品反馈、一般偏好、未解决事项和叙事摘要。
- 商品关键信息必须注明来自 `name`、`description`、`category` 或 `tags` 中的哪一段原文。
- 商品反馈必须指向本次对话中实际推荐过的商品，并引用用户原话。
- 一般偏好必须来自用户消息，不能把 Assistant 的表述当成用户偏好。
- 用户没有评价推荐商品时，不生成正向或负向反馈，直接不输出对应记录。
- “这个黑色款太大了”只能确认对大尺寸的负向反馈，不能外推为不喜欢黑色。
- 首版只提取用户明确表达的偏好；推断型偏好暂不写入总结。

## 三、总结范围与生成流程

总结对象严格限定为一段 `conversation_id`。

输入包括：

- 所有已完成用户消息；
- 所有已完成 Assistant 消息；
- Assistant 消息中的推荐商品快照；
- 最终推荐理由和终排摘要；
- Goal Understanding 和 Recommendation SPEC 中已有的事实；
- 订单信息，作为本段对话结果的一部分；
- 不含工具参数、完整工具返回和无关的 Plan 中间状态。

失败的 Assistant 消息不纳入总结，但失败轮中的用户消息仍然保留。

生成流程：

1. 校验会话存在且属于当前用户。
2. 加载已完成对话和结构化推荐元数据。
3. 按用户消息、Assistant 回复和推荐轮次组装输入。
4. 计算输入指纹，判断是否已有最新总结。
5. 输入未变化且未强制刷新时，直接返回已有总结。
6. 调用总结模型提取结构化结果。
7. 校验商品 ID、理由来源、用户原话和商品事实来源。
8. 将确定性商品数据与模型提取结果合并。
9. 保存到 SQLite 并返回。

首版建议通过显式接口触发，不自动挂在流式聊天结束事件上，避免总结失败或模型延迟影响正常导购对话。

## 四、存储设计

新增表 `conversation_summaries`，按会话保存最新一份总结：

```text
conversation_id       PRIMARY KEY
status                completed | failed
source_fingerprint    输入内容指纹
source_last_sequence  最后纳入的消息序号
prompt_version        总结 Prompt 版本
summarizer_model      生成模型
summary_json          完整 ConversationDigest
generated_at
error
```

规则：

- 同一会话只有一份当前总结。
- 输入变化后重新生成并替换当前总结。
- 重复请求相同输入时直接复用，避免重复模型成本。
- 生成失败不覆盖上一份成功的总结。
- 不建立跨会话画像表，不在本模块合并不同会话的偏好。

## 五、接口设计

新增两个接口：

```text
POST /api/conversations/{conversation_id}/summary
POST /api/conversations/{conversation_id}/summary?force=true
GET  /api/conversations/{conversation_id}/summary
```

- `POST` 生成或更新当前会话总结。
- 默认情况下，输入和 Prompt 版本未变化时复用已有结果。
- `force=true` 强制重新生成。
- `GET` 返回当前已保存的总结。
- 会话不存在返回 `404`。
- 模型调用或结果校验失败返回 `502`，不影响会话正文和已有总结。

用户体系目前仍沿用 `FIXED_USER_ID`，接口实现继续通过现有 ConversationStore 校验会话归属。

## 六、代码改动范围

计划新增：

- `agent-service/src/agent_service/conversation_summary.py`
- `agent-service/prompts/conversation_summary.md`
- `agent-service/tests/test_conversation_summary.py`
- `agent-service/tests/test_conversation_summary_api.py`

计划修改：

- `models.py`：新增 `FinalRecommendation`、`ConversationDigest`、反馈、偏好和证据模型。
- `agent_runner.py`：生成并输出最终推荐决策及理由。
- `api.py`：收集、持久化推荐决策；增加总结接口。
- `storage.py`：解析新增元数据；创建总结表及读写方法。
- `tests/test_agent_runner.py`：验证终排理由和 fallback 理由的持久化事件。
- `tests/test_agent_api.py`：验证推荐决策随消息保存。
- `tests/test_storage.py`：验证总结表读写和旧数据库兼容。

不增加新的运行时依赖，使用现有 `openai-agents`、Pydantic、SQLite 和可观测性调用封装。

## 七、验收标准

第一版至少满足：

1. 每个被推荐商品都能关联到商品 ID 和当时的商品快照。
2. 语义终排推荐商品的理由与终排模型原始 `reason` 完全一致。
3. 商品尺寸、颜色、品牌等关键信息只能来自商品系统提供的名称、描述、分类或标签。
4. 用户反馈必须关联推荐商品或具体属性，并保留用户原话。
5. “不喜欢具体商品”“不喜欢某个属性”“一般性偏好”能够分开表达。
6. 用户没有反馈时不生成态度记录。
7. 一般偏好不会从 Assistant 回复中提取。
8. 每个总结只覆盖一个 `conversation_id`，不进行跨会话合并和画像生成。
9. 相同输入重复请求不会重复调用模型。
10. 总结失败不影响聊天记录、推荐结果和已有成功总结。
11. 旧对话没有结构化终排理由时，可以生成总结，但理由标记为不可用。
12. 现有推荐接口和前端事件保持兼容。

如果这个设计范围符合预期，我下一步就按上述改动实现，并补齐模型、存储、接口和端到端测试。

## User

1. 这个提取是以定时任务的形态提取，而不是实时提取，不依赖于用户触发；2. 定时任务执行的时候，可以根据时间戳来判定多轮对话是否发生了变化，而后重新提取。例如说我认为可以考虑每小时提取；3. 定时任务不是找所有的多轮对话，而是找近 1 小时没有更新的对话（意味着用户对话已经完成，所以需要总结），如果超过一小时用户又重新复用了对话，那么下一次提取周期会再次提取并且更新； 4. 记录一个 TODO，当提取周期是一小时的时候，意味着最新的一小时内的对话，将没有可供使用的对话总结，需要结合对话细节召回以防止用户体验下降。 调整你的方案，再次输出等待我的审批

## Assistant

## 调整后的设计结论

历史对话总结改为一个独立的定时任务：

- 默认每小时扫描一次；
- 只处理最近 1 小时内没有更新的对话；
- 通过 `conversations.updated_at` 判断对话是否发生变化；
- 对话被重新启用并再次闲置超过 1 小时后，重新生成并替换该会话的总结；
- 不提供用户主动触发的总结接口；
- 本阶段不建设用户画像，也不把总结接入推荐链路。

## 一、定时任务调度

不引入 APScheduler 等额外依赖，使用 FastAPI lifespan 管理一个 `asyncio` 后台任务。

默认配置：

```text
CONVERSATION_SUMMARY_INTERVAL_SECONDS=3600
CONVERSATION_SUMMARY_IDLE_SECONDS=3600
CONVERSATION_SUMMARY_BATCH_SIZE=50
```

调度行为：

1. 服务启动后立即执行一次扫描；
2. 之后每小时执行一次；
3. 服务关闭时取消后台任务，并等待当前任务安全退出；
4. 单次任务异常只记录日志，不能导致后续周期停止；
5. 默认串行处理候选会话，避免同时发起过多模型请求。

如果将来部署多个服务实例，需要通过数据库 lease 防止同一会话被重复提取。建议首版就在 `conversation_summaries` 中预留 `lease_until` 和 `lease_owner` 字段，即使当前只运行单实例。

## 二、候选对话筛选

定时任务不扫描所有对话，而是查找“已经闲置且需要更新总结”的对话。

筛选条件：

```sql
conversation.updated_at <= now - idle_interval
AND (
    summary 不存在
    OR summary.status = 'failed'
    OR summary.source_updated_at < conversation.updated_at
)
```

另外，`status = processing` 且 lease 尚未过期的对话要跳过；lease 已过期的任务允许重新领取。

具体规则：

- 对话更新后不足 1 小时：不提取。
- 超过 1 小时且没有总结：首次提取。
- 超过 1 小时，但总结的 `source_updated_at` 等于当前 `conversation.updated_at`：说明未变化，跳过。
- 对话被复用后，`updated_at` 更新，原总结自动变成过期。
- 用户再次对话结束后，等下一次扫描确认闲置超过 1 小时，再重新提取。
- 重新提取会替换该会话的当前总结，不保留历史版本。

这里需要注意实际时延：扫描周期和闲置阈值都是 1 小时时，一段对话最后更新后通常要等待 1 到 2 小时才会获得总结。因此后续召回兜底不能只判断“最近 1 小时”，而应判断“当前是否存在与最新对话版本匹配的总结”。

## 三、处理流程

```text
每小时触发
    ↓
查询超过 1 小时未更新且总结过期的会话
    ↓
原子领取任务（lease）
    ↓
重新读取该会话已完成的消息和推荐元数据
    ↓
计算输入指纹
    ↓
生成 ConversationDigest
    ↓
校验 Schema、商品、反馈和证据
    ↓
确认处理期间会话时间戳未变化
    ↓
保存并释放 lease
```

会话在总结过程中再次发生变化时，本次结果不能覆盖新对话。保存前必须再次比较：

```text
conversation.updated_at == source_updated_at
```

如果不一致，丢弃本次结果，等待后续周期重新提取。

## 四、总结输入

定时任务读取该会话当前所有有效内容：

- 已完成用户消息；
- 已完成 Assistant 消息；
- 推荐商品快照；
- Recommendation SPEC；
- 最终推荐商品及其终排理由；
- 终排摘要；
- Goal Understanding；
- 订单结果。

失败或中断的 Assistant 消息不作为总结内容，但同一轮中的用户消息仍然保留。

推荐理由需要在 Agent 完成回复时持久化。新增的结构为：

```text
FinalRecommendation
- product_id
- rank
- channel
- reason
- reason_source
- environmental_fit
```

语义终排成功时，`reason` 直接复制终排模型的原始理由；公式路径标记为 `formula_scoring`；历史数据没有结构化理由时标记为 `unavailable`。

## 五、总结结果

每个 `conversation_id` 保存一份当前总结，内容包括：

- 对话整体摘要；
- 用户目标；
- 用户明确约束；
- 每轮推荐的商品、关键规格和最终推荐理由；
- 用户对推荐商品或商品属性的正向、负向、混合反馈；
- 用户明确表达的一般性偏好；
- 未解决事项；
- 每条反馈和偏好的消息来源及用户原话。

商品 ID、商品快照和终排理由由代码确定性组装，避免总结模型遗漏或改写；LLM 主要负责提取用户目标、反馈、一般偏好和生成对话摘要。

## 六、存储设计

新增表 `conversation_summaries`：

```text
conversation_id       PRIMARY KEY
status                completed | failed | processing
source_updated_at     本次提取对应的 conversations.updated_at
source_fingerprint    已完成消息和推荐元数据的输入指纹
source_last_sequence  最后纳入的消息序号
prompt_version        Prompt 版本
summarizer_model      生成模型
summary_json          完整 ConversationDigest
generated_at
last_attempt_at
lease_owner
lease_until
error
```

`updated_at` 用于低成本筛选，`source_fingerprint` 用于防止重复计算和确认输入确实一致。这样做没有引入跨会话画像或冲突处理，只是保证单个会话的总结能够正确刷新。

## 七、接口调整

取消原先设计的用户触发接口：

```text
POST /api/conversations/{conversation_id}/summary
```

保留一个只读接口用于调试和后续模块读取：

```text
GET /api/conversations/{conversation_id}/summary
```

该接口只查询已生成的总结，不触发模型调用。每小时的总结生成全部由后台任务完成。

## 八、记录 TODO

在定时任务模块中记录明确的 TODO：

```text
TODO(conversation-summary-freshness):
定时总结存在“没有当前有效总结”的窗口。后续对话召回和上下文组装
在 summary 不存在、source_updated_at 过期或 status=failed 时，
必须回退到原始对话细节，不能因为缺少 summary 而丢失最近上下文。
```

这个 TODO 的核心判断应基于“总结是否匹配最新对话版本”，而不是机械地只看最近 1 小时，因为一小时扫描周期会使实际未覆盖窗口接近 1 到 2 小时。

## 九、代码改动范围

新增：

- `conversation_summary.py`：总结输入构建、模型调用、结果校验。
- `conversation_summary_worker.py`：周期调度、候选扫描、lease 和任务执行。
- `prompts/conversation_summary.md`：总结提取规则。
- 对应单元测试、存储测试和调度测试。

修改：

- `models.py`：最终推荐决策和总结结果模型。
- `agent_runner.py`：产出最终推荐理由。
- `api.py`：持久化推荐决策；增加只读总结接口；配置 lifespan 启动定时任务。
- `storage.py`：总结表、候选查询、原子领取和结果写入。
- 配置和日志：增加扫描间隔、闲置阈值、批量大小等配置和任务指标。

## 十、验收标准

1. 用户无法通过接口直接触发总结。
2. 对话更新不足 1 小时时不会被提取。
3. 对话闲置超过 1 小时且没有总结时，下一次扫描会生成总结。
4. 对话未变化时，不会重复调用总结模型。
5. 对话被复用后，旧总结不会继续被当作最新版本。
6. 重新闲置超过 1 小时后，总结会被重新提取并替换。
7. 总结期间对话发生变化时，旧结果不会覆盖新对话。
8. 最终推荐理由与语义终排模型返回的理由一致。
9. 商品关键信息有明确来源，不伪造规格。
10. 商品反馈和一般偏好引用的都是用户消息。
11. 定时任务异常不会影响聊天服务，也不会终止后续周期。
12. 已记录“缺少当前总结时回退原始对话细节”的 TODO。

以上为调整后的完整方案。

## User

1. 你忽略原子领取任务的问题，也忽略 lease，你可以认为，要么只有一个节点调度，要么就是有分布式任务调度机制来触发，反正不会出现竞争问题，从而简化这个实现，但是你在注释里面讲一下这个假设；2. 不需要考虑什么指纹，你用 conversation id 和时间戳就能判定要不要重新生成；3. 保存前不需要比较conversation.updated_at == source_updated_at，即便同时发生在总结，以及用户又触发了对话，你依旧会进行总结，后续对话产生的内容，会等下一个调度周期。 基于反馈，再次调整你的设计和实施方案，等待审批。

## Assistant

## 调整后的设计

总结任务只依赖两个判断条件：

```text
conversation_id
conversation.updated_at
```

不使用输入指纹、lease、任务领取状态或保存前版本校验。

调度任务可能出现在同一节点的一个后台循环中，也可能由外部分布式任务调度系统触发。实现会明确假设：**同一对话不会同时被两个总结任务处理**，因此本模块不实现原子领取和分布式锁。

## 一、调度模型

使用 FastAPI lifespan 启动后台循环：

- 服务启动后立即扫描一次；
- 之后默认每小时扫描一次；
- 每次按顺序处理符合条件的对话；
- 服务关闭时安全取消后台任务；
- 单次执行失败只记录日志，不影响下一个周期。

配置：

```text
CONVERSATION_SUMMARY_INTERVAL_SECONDS=3600
CONVERSATION_SUMMARY_IDLE_SECONDS=3600
```

如果实际使用外部分布式任务调度，可以关闭内置循环，由外部系统按相同规则调用总结任务。

代码注释中记录以下假设：

```python
# Scheduling assumption:
# This worker does not acquire per-conversation locks or leases.
# The deployment must guarantee exactly one scheduler invocation at a time,
# either through a single scheduler node or an external distributed scheduler.
# Concurrent execution of the same conversation is explicitly out of scope.
```

## 二、候选对话判断

扫描范围不是所有对话，而是：

- 最近 1 小时内没有更新；
- 没有总结，或现有总结早于当前对话时间。

查询语义：

```sql
conversation.updated_at <= now - idle_interval
AND (
    summary.conversation_id IS NULL
    OR summary.status = 'failed'
    OR summary.source_updated_at < conversation.updated_at
)
```

具体行为：

| 情况 | 行为 |
|---|---|
| 对话更新不足 1 小时 | 本轮跳过 |
| 超过 1 小时且没有总结 | 生成总结 |
| 总结时间等于对话最新更新时间 | 跳过 |
| 对话被重新使用，更新时间变新 | 下个满足闲置条件的周期重新生成 |
| 上次总结失败 | 后续周期重新生成 |
| 对话正在被另一实例处理 | 不在本模块处理，由调度机制保证不会发生 |

这里只比较 `conversation_id` 对应的 `updated_at`，不再计算消息指纹或额外版本号。

## 三、生成与并发语义

定时任务的处理顺序：

1. 查询符合条件的对话。
2. 读取对话及其完成消息。
3. 记录扫描时得到的 `conversation.updated_at`，作为 `source_updated_at`。
4. 调用总结模型。
5. 校验结果。
6. 直接保存结果。
7. 等待下一个周期处理。

保存前不再次比较 `conversation.updated_at`。

如果总结过程中用户重新打开并继续该对话：

- 本次总结仍然保存；
- 它对应的是开始处理时看到的对话版本；
- 保存时，数据库中的 `conversation.updated_at` 已经更新；
- 下一个周期因为 `source_updated_at < conversation.updated_at`，会重新总结完整对话并覆盖本次结果。

这可能会出现短暂保存一份已经过期的总结，但不会漏掉后续总结，符合本阶段的简化目标。

任务内部不加锁，也不标记 `processing` 状态。实现和部署层共同保证单次调度执行。

## 四、存储设计

`conversation_summaries` 简化为：

```text
conversation_id       PRIMARY KEY
status                completed | failed
source_updated_at     本总结对应的 conversations.updated_at
summary_json          完整 ConversationDigest
prompt_version        总结 Prompt 版本
summarizer_model      生成模型
generated_at          生成本次总结的时间
error                  最近一次失败原因
```

不保存：

- lease owner；
- lease expiration；
- input fingerprint；
- source message sequence；
- processing 状态；
- 总结历史版本。

每个对话只保留当前一份总结，重新生成后直接替换。

## 五、总结输入与输出

输入包括：

- 已完成用户消息；
- 已完成 Assistant 消息；
- 推荐商品快照；
- 最终推荐商品及语义终排理由；
- 终排摘要；
- Recommendation SPEC；
- Goal Understanding；
- 订单结果。

输出继续使用 `ConversationDigest`，包含：

- 对话摘要；
- 用户目标；
- 明确约束；
- 每轮推荐商品及关键规格；
- 商品最终推荐理由；
- 用户对具体商品、具体属性或品类的一般表态；
- 用户明确表达的一般性偏好；
- 未解决事项；
- 每条反馈和偏好的用户原话与消息 ID。

商品 ID、商品快照和终排理由由代码组装；总结模型负责提取用户反馈、一般偏好和摘要。

## 六、接口与服务边界

不提供用户主动触发的总结接口。

保留只读接口：

```text
GET /api/conversations/{conversation_id}/summary
```

该接口只读取已有总结，不触发生成。总结生成全部由定时任务完成。

## 七、最新对话兜底 TODO

在调度模块记录：

```python
# TODO(conversation-summary-freshness):
# A conversation has no usable summary until it has been idle long enough and
# the next summary job has completed. Conversation recall must fall back to raw
# completed turns whenever the digest is absent or stale.
```

由于扫描周期和闲置阈值都为 1 小时，实际可能出现 1 到 2 小时的总结空窗。后续对话召回应基于“是否存在匹配当前 `conversation.updated_at` 的总结”判断，而不是只看最近一小时。

## 八、实施步骤

1. 新增最终推荐决策模型，并在 Agent 完成回复时持久化终排理由。
2. 新增 `ConversationDigest` 及其反馈、偏好、证据模型。
3. 新增 `prompts/conversation_summary.md`。
4. 实现总结输入构建、模型调用和结果校验。
5. 新增 `conversation_summaries` 表及按时间戳查询、覆盖写入方法。
6. 新增每小时运行的 `conversation_summary_worker.py`。
7. 在 FastAPI lifespan 中启动和停止后台任务。
8. 增加只读总结接口。
9. 增加调度、存储、模型输出校验、并发变更语义和接口测试。
10. 记录调度唯一性和最新对话兜底 TODO。

## 九、验收标准

1. 没有用户主动触发生成总结的接口。
2. 更新不足 1 小时的对话不生成总结。
3. 超过 1 小时且时间戳发生变化的对话会生成或重新生成总结。
4. 总结的 `source_updated_at` 等于对话当前更新时间时跳过。
5. 对话复用后，下个满足条件的周期会重新总结。
6. 总结期间对话被复用，旧总结仍可保存，下个周期会再次总结。
7. 不实现 lease、原子领取或任务竞争控制，并通过注释明确部署假设。
8. 不使用输入指纹。
9. 最终推荐商品理由来自持久化的终排结果。
10. 商品关键信息有明确商品数据来源。
11. 商品反馈和一般偏好均有用户消息证据。
12. 最新对话无总结时的原始对话召回兜底已记录为 TODO。

以上为基于本轮反馈调整后的设计和实施方案。

## User

很好，按计划实施

## Assistant

开始实施。我会先补齐“最终推荐理由”的持久化，再实现总结模型、SQLite 存储、每小时任务和只读接口，最后跑完整测试验证定时刷新与并发变更语义。

## Activity

    $ sed -n '150,235p' agent-service/src/agent_service/agent_runner.py && sed -n '1060,1220p' agent-service/src/agent_service/agent_runner.py
        selected_products: dict[str, Product] = field(default_factory=dict)
        created_orders: dict[str, OrderLink] = field(default_factory=dict)
        submitted: bool = False
        tool_trace: list[ToolTrace] = field(default_factory=list)
    
        def remember_candidates(
            self,
            candidates: Sequence[ProductCandidate],
        ) -> None:
            for candidate in candidates:
                self.candidate_products[candidate.product.id] = candidate.product
                if candidate.source == "advertisement":
                    self.ad_product_ids.add(candidate.product.id)
                    if candidate.ad is not None:
                        self.ad_metadata[candidate.product.id] = candidate.ad
                else:
                    self.organic_product_ids.add(candidate.product.id)
    
        def remember_products(self, products: Sequence[Product]) -> None:
            for product in products:
                self.candidate_products[product.id] = product
                self.organic_product_ids.add(product.id)
    
    
    async def commit_scored_products(
        context: ShoppingAgentContext,
        candidates: Sequence[ScoredProduct],
        *,
        allow_ad_first: bool = True,
    ) -> list[Product]:
        selected: dict[str, Product] = {}
        for candidate in candidates:
            try:
                product = await context.mall.get_product(candidate.product.id)
            except Exception:
                logger.warning(
                    "failed to confirm recommended product %s",
                    candidate.product.id,
                    exc_info=True,
                )
                continue
            if product is None or (product.stock is not None and product.stock <= 0):
                continue
            if candidate.channel == "ad" and candidate.ad is not None:
                product = product.model_copy(
                    update={
                        "is_ad": True,
                        "ad_label": "广告",
                        "ad_id": candidate.ad.ad_id,
                        "campaign_id": candidate.ad.campaign_id,
                    }
                )
            selected[product.id] = product
    
        if (
            not allow_ad_first
            and selected
            and next(iter(selected.values())).is_ad
        ):
            selected = {}
    
        context.selected_products = selected
        context.submitted = True
        return list(selected.values())
    
    
    def product_payload(products: Sequence[Product]) -> str:
        return json.dumps(
            [product.model_dump(mode="json") for product in products],
            ensure_ascii=False,
        )
    
    
    def candidate_payload(candidates: Sequence[ProductCandidate]) -> str:
        return json.dumps(
            [candidate.model_dump(mode="json") for candidate in candidates],
            ensure_ascii=False,
        )
    
    
    def unavailable_payload(source: str) -> str:
        return json.dumps(
            {
                "status": "unavailable",
                "items": [],
                "message": f"{source}暂时不可用，可以继续使用其他来源推荐",
                "广告分数严格高于自然最低分时返回 requires_semantic_ranking，否则"
                "直接提交自然 Top 2。必须先完成两个独立搜索 Action。"
            ),
            **tool_options,
        )
        async def recommend_products_tool() -> str:
            goal = context.goal_understanding
            if goal is None:
                return rejected("请先调用 understand_goal 理解用户需求")
            if goal.requires_clarification:
                return rejected("Goal Understanding 表示需要先向用户澄清关键信息")
            if goal.primary_intent != "product_recommendation":
                return rejected("当前 primary_intent 不是商品推荐")
            if recommendation_requirements_need_input(goal):
                return rejected("推荐需求仍在收集，暂不能提交推荐")
            snapshot = context.recommendation_context
            if snapshot is None:
                return rejected("请先调用 collect_recommendation_context")
            spec = context.recommendation_spec
            if spec is None:
                return rejected("请先调用 generate_recommendation_spec")
            if not context.organic_search_attempted:
                return rejected("请先调用 search_organic_candidates")
            if not context.ad_search_attempted:
                return rejected("请先调用 search_ad_candidates")
    
            demand = recommendation_demand_from_goal(goal, spec)
            organic_products = list(context.organic_search_products)
            ad_candidates = list(context.ad_search_candidates)
            source_statuses = dict(snapshot.source_statuses)
            source_statuses.update(context.organic_search_statuses)
            source_statuses["advertisement"] = context.ad_search_status
    
            context.remember_products(organic_products)
            context.remember_candidates(ad_candidates)
            context.selected_products.clear()
            context.semantic_ranking = None
            context.submitted = False
    
            batch = build_recommendation_batch(
                demand=demand,
                organic_products=organic_products,
                ad_candidates=ad_candidates[:10],
                catalog=snapshot.catalog,
                browse_events=snapshot.browse_history,
                orders=snapshot.orders,
                cart=snapshot.cart,
                agent_profile=snapshot.agent_profile,
                platform_profile=snapshot.platform_profile,
                source_statuses=source_statuses,
            )
            context.recommendation_batch = batch
    
            response: dict[str, object] = {
                "status": (
                    "requires_semantic_ranking"
                    if batch.requires_semantic_ranking
                    else "accepted"
                ),
                "batch": batch.model_dump(mode="json"),
            }
            if not batch.requires_semantic_ranking:
                selected = await commit_scored_products(
                    context,
                    batch.organic_candidates[:2],
                )
                response["selected_products"] = [
                    product.model_dump(mode="json") for product in selected
                ]
                if not selected:
                    response["status"] = "no_match"
            return json.dumps(response, ensure_ascii=False)
    
        @function_tool(
            name_override="rerank_recommendations",
            description_override=(
                "独立的语义终排工具。仅在 recommend_products 返回 "
                "requires_semantic_ranking 后调用。它会使用独立 Prompt 综合公式"
                "分数、商品语义和调用方提供的可信环境信息，最多选择两个自然商品"
                "和一个广告商品；存在自然候选时广告不能排第一。"
            ),
            **tool_options,
        )
        async def rerank_recommendations_tool(
            environment_context: str | None = None,
        ) -> str:
            batch = context.recommendation_batch
            if batch is None:
                return rejected("请先调用 recommend_products 生成候选")
            if not batch.requires_semantic_ranking:
                return rejected("当前候选不需要语义终排")
            if context.semantic_reranker is None:
                return unavailable_payload("语义终排")
    
            try:
                ranking = validate_semantic_ranking(
                    await context.semantic_reranker.rerank(
                        batch=batch,
                        user_request=context.current_user_request,
                        environment_context=environment_context,
                    ),
                    batch,
                )
            except SemanticRerankError as exc:
                logger.warning("semantic reranking failed: %s", exc)
                fallback_candidates = (
                    batch.competitive_ads[:1]
                    if batch.ad_only
                    else batch.organic_candidates[:2]
                )
                selected = await commit_scored_products(
                    context,
                    fallback_candidates,
                    allow_ad_first=batch.ad_only,
                )
                return json.dumps(
                    {
                        "status": "fallback" if selected else "no_match",
                        "fallback_reason": str(exc),
                        "selected_products": [
                            product.model_dump(mode="json")
                            for product in selected
                        ],
                    },
                    ensure_ascii=False,
                )
    
            candidates_by_key = {
                (candidate.channel, candidate.product.id): candidate
                for candidate in semantic_candidates(batch)
            }
            selected_candidates = [
                candidates_by_key[(item.channel, item.product_id)]
                for item in ranking.items
            ]
            selected = await commit_scored_products(
                context,
                selected_candidates,
                allow_ad_first=batch.ad_only,
            )
            context.semantic_ranking = ranking
            return json.dumps(
                {
                    "status": "accepted" if selected else "no_match",
                    "semantic_ranking": ranking.model_dump(mode="json"),
                    "selected_products": [
                        product.model_dump(mode="json") for product in selected
                    ],
                },
                ensure_ascii=False,
            )
    
        @function_tool(
            name_override="update_plan",
            description_override=(
                "创建或整体替换当前 Plan 和 Plan State。状态、当前步骤、下一步、"
                "步骤完成情况和计划变更全部由模型决定。代码只保存模型提交的内容。"
            ),
            **tool_options,
        )
        async def update_plan_tool(
    ✓ • 0ms

## Activity

    $ sed -n '260,380p' agent-service/tests/test_agent_api.py && sed -n '880,1060p' agent-service/tests/test_agent_runner.py
        response = client.post(
            "/api/chat/stream",
            json={"message": "A"},
        )
    
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert '"type": "conversation"' in response.text
        assert '"type": "tool_started"' in response.text
        assert '"type": "plan_updated"' in response.text
        assert '"type": "order_created"' in response.text
        assert '"type": "recommendations"' in response.text
        assert "真实模型回复" in response.text
        assert '"type": "done"' in response.text
    
        conversations = store.list_conversations(1)
        assert len(conversations) == 1
        assert conversations[0].title == "A"
        assert conversations[0].message_count == 2
    
        detail = store.get_conversation(1, conversations[0].id)
        assert detail is not None
        assert [message.role for message in detail.messages] == [
            "user",
            "assistant",
        ]
        assert detail.messages[1].content == "真实模型回复"
        assert detail.messages[1].status == "completed"
        assert detail.messages[1].recommendations[0].id == "tote"
        assert detail.messages[1].recommendations[0].is_ad is True
        assert detail.messages[1].recommendations[0].ad_label == "广告"
        assert detail.messages[1].goal_understanding is not None
        assert detail.messages[1].goal_understanding.pending_intents == [
            "order_query"
        ]
        assert (
            detail.messages[1]
            .goal_understanding.recommendation_requirements.status
            == "ready"
        )
        assert detail.messages[1].recommendation_spec is not None
        assert detail.messages[1].recommendation_spec.search_queries == [
            "通勤",
            "办公室",
        ]
        assert detail.messages[1].tool_trace[0].tool == "search_products"
        assert detail.messages[1].plan_state is not None
        assert detail.messages[1].plan_state.plan.plan_id == "plan-test"
        assert detail.messages[1].plan_state.current_step_id == "submit"
        assert detail.messages[1].orders[0].order_id == "order-test"
        assert detail.messages[1].orders[0].preview_path == "/orders/order-test"
    
    
    def test_stream_chat_requires_message(
        store: ConversationStore,
    ) -> None:
        response = client.post(
            "/api/chat/stream",
            json={"messages": [{"role": "user", "content": "你好"}]},
        )
    
        assert response.status_code == 422
    
    
    def test_stream_chat_persists_configuration_error(
        store: ConversationStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def missing_config() -> LLMConfig:
            raise LLMConfigError("LLM config is not set")
    
        monkeypatch.setattr(api_module, "load_llm_config", missing_config)
    
        response = client.post(
            "/api/chat/stream",
            json={"message": "保存失败消息"},
        )
    
        assert response.status_code == 200
        assert "LLM config is not set" in response.text
    
        conversations = store.list_conversations(1)
        assert len(conversations) == 1
        detail = store.get_conversation(1, conversations[0].id)
        assert detail is not None
        assert detail.messages[0].role == "user"
        assert detail.messages[1].status == "failed"
        assert "LLM config is not set" in detail.messages[1].content
    
    
    def test_stream_chat_persists_partial_reply_on_error(
        store: ConversationStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        async def failing_stream(
            messages,
            config,
            mall,
            previous_plan_state=None,
            previous_recommendations=None,
            previous_orders=None,
            previous_goal_understanding=None,
        ):
            yield {"type": "start", "message_id": "assistant-test"}
            yield {
                "type": "delta",
                "message_id": "assistant-test",
                "content": "已经生成的部分",
            }
            yield {
                "type": "error",
                "message_id": "assistant-test",
                "message": "模型调用失败",
                "tool_trace": [],
            }
    
        monkeypatch.setattr(
            api_module,
            "load_llm_config",
            lambda: TEST_CONFIG,
        )
                "usage": None,
            }
        )
        prepare_recommendation_context(
            context,
            spec=no_match_spec,
        )
    
        result = json.loads(
            invoke_tool(
                context,
                "recommend_products",
                {},
            )
        )
    
        assert result["status"] == "no_match"
        assert context.submitted is True
        assert context.selected_products == {}
    
    
    def test_semantic_reranker_selects_organic_before_ad() -> None:
        context = ShoppingAgentContext(mall=mall_client())
        organic = scored_candidate(
            product_id="commuter-backpack",
            channel="organic",
            score=70,
        )
        ad = scored_candidate(
            product_id="portable-coffee",
            channel="ad",
            score=74,
            ad=AdInfo(ad_id="ad-1001", campaign_id="campaign-autumn-2026"),
        )
        reranker = StaticSemanticReranker(
            SemanticRankingResult(
                items=[
                    SemanticRankingItem(
                        product_id="commuter-backpack",
                        channel="organic",
                        reason="更符合通勤用途",
                    ),
                    SemanticRankingItem(
                        product_id="portable-coffee",
                        channel="ad",
                        reason="补充办公室饮用场景",
                    ),
                ],
                summary="自然商品优先，广告作为补充",
            )
        )
        context.semantic_reranker = reranker
        context.recommendation_batch = recommendation_batch(
            organic=[organic],
            ads=[ad],
            cutoff=60,
        )
    
        accepted = json.loads(
            invoke_tool(
                context,
                "rerank_recommendations",
                {"environment_context": "明早通勤，需要轻便"},
            )
        )
    
        assert accepted["status"] == "accepted"
        assert len(context.selected_products) == 2
        assert list(context.selected_products) == [
            "commuter-backpack",
            "portable-coffee",
        ]
        assert context.selected_products["portable-coffee"].is_ad is True
        assert context.selected_products["portable-coffee"].ad_label == "广告"
        assert reranker.environment_context == "明早通勤，需要轻便"
    
    
    def test_semantic_reranker_falls_back_when_ad_is_first() -> None:
        context = ShoppingAgentContext(mall=mall_client())
        organic = scored_candidate(
            product_id="commuter-backpack",
            channel="organic",
            score=70,
        )
        ad = scored_candidate(
            product_id="portable-coffee",
            channel="ad",
            score=74,
            ad=AdInfo(ad_id="ad-1001", campaign_id="campaign-autumn-2026"),
        )
        context.semantic_reranker = StaticSemanticReranker(
            SemanticRankingResult(
                items=[
                    SemanticRankingItem(
                        product_id="portable-coffee",
                        channel="ad",
                        reason="分数更高",
                    ),
                    SemanticRankingItem(
                        product_id="commuter-backpack",
                        channel="organic",
                        reason="符合通勤需求",
                    ),
                ]
            )
        )
        context.recommendation_batch = recommendation_batch(
            organic=[organic],
            ads=[ad],
            cutoff=60,
        )
    
        result = json.loads(
            invoke_tool(
                context,
                "rerank_recommendations",
                {},
            )
        )
    
        assert result["status"] == "fallback"
        assert "cannot be first" in result["fallback_reason"]
        assert list(context.selected_products) == ["commuter-backpack"]
    
    
    def test_semantic_reranker_allows_ad_only_when_no_organic_candidate() -> None:
        context = ShoppingAgentContext(mall=mall_client())
        ad = scored_candidate(
            product_id="portable-coffee",
            channel="ad",
            score=74,
            ad=AdInfo(ad_id="ad-1001", campaign_id="campaign-autumn-2026"),
        )
        context.semantic_reranker = StaticSemanticReranker(
            SemanticRankingResult(
                items=[
                    SemanticRankingItem(
                        product_id="portable-coffee",
                        channel="ad",
                        reason="当前唯一符合需求的候选",
                    )
                ]
            )
        )
        context.recommendation_batch = recommendation_batch(
            organic=[],
            ads=[ad],
            ad_only=True,
        )
    
        result = json.loads(
            invoke_tool(context, "rerank_recommendations", {})
        )
    
        assert result["status"] == "accepted"
        assert list(context.selected_products) == ["portable-coffee"]
        assert context.selected_products["portable-coffee"].is_ad is True
    
    
    def test_semantic_reranker_agent_uses_independent_prompt() -> None:
        organic = scored_candidate(
            product_id="commuter-backpack",
            channel="organic",
            score=70,
        )
        ad = scored_candidate(
            product_id="portable-coffee",
            channel="ad",
            score=74,
            ad=AdInfo(ad_id="ad-1001", campaign_id="campaign-autumn-2026"),
        )
        batch = recommendation_batch(
            organic=[organic],
            ads=[ad],
            cutoff=60,
        )
        model = ScriptedModel(
            [
                [
                    assistant_message(
                        json.dumps(
    ✓ • 0ms

## Activity

    $ sed -n '1,260p' agent-service/tests/conftest.py && rg -n "ConversationStore\(|create_conversation|add_message\(" agent-service/tests -g '*.py' | sed -n '1,260p'
    import pytest
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )
    
    from agent_service.observability.spans import set_observability_clients
    
    
    @pytest.fixture(scope="session")
    def otel_test_exporter() -> InMemorySpanExporter:
        provider = TracerProvider()
        exporter = InMemorySpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        set_observability_clients(
            tracer=provider.get_tracer("agent-service-tests"),
        )
        yield exporter
        provider.shutdown()
    agent-service/tests/test_storage.py:10:    store = ConversationStore(tmp_path / "history.db")
    agent-service/tests/test_storage.py:11:    conversation_id = store.create_conversation(1, "第一轮")
    agent-service/tests/test_storage.py:12:    store.add_message(conversation_id, "user", "第一轮", "completed")
    agent-service/tests/test_storage.py:13:    store.add_message(conversation_id, "assistant", "成功回复", "completed")
    agent-service/tests/test_storage.py:14:    store.add_message(conversation_id, "user", "第二轮", "completed")
    agent-service/tests/test_storage.py:15:    store.add_message(conversation_id, "assistant", "失败回复", "failed")
    agent-service/tests/test_storage.py:28:    store = ConversationStore(database_path)
    agent-service/tests/test_storage.py:29:    conversation_id = store.create_conversation(1, "中断")
    agent-service/tests/test_storage.py:30:    message_id = store.add_message(
    agent-service/tests/test_storage.py:37:    recovered_store = ConversationStore(database_path)
    agent-service/tests/test_storage.py:83:    store = ConversationStore(database_path)
    agent-service/tests/test_observability.py:101:    store = ConversationStore(tmp_path / "observability.db")
    agent-service/tests/test_observability.py:102:    conversation_id = store.create_conversation(1, "你好")
    agent-service/tests/test_observability.py:103:    store.add_message(
    agent-service/tests/test_agent_api.py:25:    conversation_store = ConversationStore(tmp_path / "agent-test.db")
    agent-service/tests/test_agent_api.py:400:    conversation_id = store.create_conversation(1, "继续推荐")
    agent-service/tests/test_agent_api.py:401:    store.add_message(conversation_id, "user", "先推荐商品", "completed")
    agent-service/tests/test_agent_api.py:402:    store.add_message(
    agent-service/tests/test_agent_api.py:475:    conversation_id = store.create_conversation(1, "购买礼物")
    agent-service/tests/test_agent_api.py:476:    store.add_message(conversation_id, "user", "购买礼物", "completed")
    agent-service/tests/test_agent_api.py:477:    store.add_message(conversation_id, "assistant", "推荐托特包", "completed")
    ✓ • 0ms

## Activity

    $ find agent-service/data -maxdepth 2 -type f -print | sed -n '1,100p' && command -v pytest || true && command -v uv || true && python3 -c 'import pydantic, fastapi, agents; print("ok")' 2>&1 | sed -n '1,40p'
    agent-service/data/agent.db
    agent-service/data/agent.db-wal
    agent-service/data/agent.db-shm
    /opt/anaconda3/bin/pytest
    /opt/anaconda3/bin/uv
    Traceback (most recent call last):
      File "<string>", line 1, in <module>
    ModuleNotFoundError: No module named 'agents'
    ✓ • 249ms

## Activity

    $ sed -n '1,380p' agent-service/tests/test_agent_runner.py
    import asyncio
    import json
    import logging
    
    import httpx
    from agents.testing import ScriptedModel, assistant_message, function_call
    from agents.tool_context import ToolContext
    from mall_service.api import app as mall_app
    
    from agent_service.agent_runner import (
        RecommendationContextSnapshot,
        ShoppingAgentContext,
        create_tools,
        normalize_openai_base_url,
        recommendation_demand_from_goal,
        stream_agent_reply,
    )
    from agent_service.goal_understanding import AgentGoalUnderstander
    from agent_service.llm_config import LLMConfig
    from agent_service.mall_client import MallClient
    from agent_service.models import (
        AdInfo,
        ConversationMessage,
        GoalUnderstandingResult,
        OrderLink,
        PlanState,
        Product,
        RecommendationBatch,
        RecommendationDemand,
        RecommendationRequirementSlots,
        RecommendationRequirementState,
        RecommendationSpec,
        RecommendationSpecHardConstraints,
        ScoredProduct,
        SemanticRankingItem,
        SemanticRankingResult,
        SourceEvidence,
    )
    from agent_service.recommendation_reranker import (
        AgentSemanticReranker,
        semantic_candidates,
    )
    from agent_service.recommendation_spec import AgentRecommendationSpecGenerator
    
    
    def llm_config() -> LLMConfig:
        return LLMConfig(
            base_url="https://api.deepseek.com",
            api_key="test-key",
            model="deepseek-flash",
            max_turns=10,
        )
    
    
    def mall_client() -> MallClient:
        return MallClient(
            base_url="http://mall.test",
            transport=httpx.ASGITransport(app=mall_app),
        )
    
    
    def plan_arguments(
        *,
        plan_id: str = "plan-recommendation",
        current_step_id: str = "collect",
        summary: str = "准备收集推荐所需信息",
    ) -> dict:
        return {
            "plan": {
                "plan_id": plan_id,
                "goal": "为用户生成合适的商品推荐",
                "steps": [
                    {
                        "step_id": "collect",
                        "title": "收集用户上下文",
                        "objective": "读取画像、浏览、订单和购物车",
                        "kind": "context",
                        "depends_on": [],
                        "metadata": {},
                    },
                    {
                        "step_id": "retrieve",
                        "title": "获取商品候选",
                        "objective": "获取自然商品和广告候选",
                        "kind": "retrieval",
                        "depends_on": ["collect"],
                        "metadata": {},
                    },
                    {
                        "step_id": "submit",
                        "title": "提交最终推荐",
                        "objective": "校验并提交最多三个商品",
                        "kind": "decision",
                        "depends_on": ["retrieve"],
                        "metadata": {},
                    },
                ],
            },
            "status": "active",
            "current_step_id": current_step_id,
            "step_states": [
                {
                    "step_id": "collect",
                    "status": "in_progress"
                    if current_step_id == "collect"
                    else "completed",
                    "note": None,
                },
                {
                    "step_id": "retrieve",
                    "status": "in_progress"
                    if current_step_id == "retrieve"
                    else "pending",
                    "note": None,
                },
                {
                    "step_id": "submit",
                    "status": "pending",
                    "note": None,
                },
            ],
            "summary": summary,
            "next_action": "继续模型认为最合适的下一步",
        }
    
    
    def tool_by_name(context: ShoppingAgentContext, name: str):
        return next(
            tool
            for tool in create_tools(context, llm_config())
            if tool.name == name
        )
    
    
    def invoke_tool(context: ShoppingAgentContext, name: str, arguments: dict):
        tool = tool_by_name(context, name)
        tool_context = ToolContext(
            context=context,
            tool_name=tool.name,
            tool_call_id=f"call-{name}",
            tool_arguments=json.dumps(arguments, ensure_ascii=False),
        )
        return asyncio.run(
            tool.on_invoke_tool(
                tool_context,
                json.dumps(arguments, ensure_ascii=False),
            )
        )
    
    
    def prepare_recommendation_context(
        context: ShoppingAgentContext,
        *,
        spec: RecommendationSpec | None = None,
    ) -> None:
        invoke_tool(context, "collect_recommendation_context", {})
        context.recommendation_spec = spec or recommendation_spec()
        invoke_tool(context, "search_organic_candidates", {})
        invoke_tool(context, "search_ad_candidates", {})
    
    
    class UnavailableMall:
        async def get_browse_history(self, user_id: int, limit: int = 10):
            raise RuntimeError("mall unavailable")
    
    
    class StaticSemanticReranker:
        def __init__(self, result: SemanticRankingResult) -> None:
            self.result = result
            self.environment_context: str | None = None
    
        async def rerank(
            self,
            *,
            batch: RecommendationBatch,
            user_request: str,
            environment_context: str | None = None,
        ) -> SemanticRankingResult:
            self.environment_context = environment_context
            return self.result
    
    
    class StaticGoalUnderstander:
        def __init__(self, result: GoalUnderstandingResult) -> None:
            self.result = result
            self.previous_goal: GoalUnderstandingResult | None = None
    
        async def understand(
            self,
            *,
            current_message: str,
            recent_messages: list[ConversationMessage],
            previous_goal: GoalUnderstandingResult | None,
            previous_recommendations: list[Product],
            previous_orders: list[OrderLink],
        ) -> GoalUnderstandingResult:
            self.previous_goal = previous_goal
            return self.result
    
    
    class StaticRecommendationSpecGenerator:
        def __init__(self, result: RecommendationSpec) -> None:
            self.result = result
    
        async def generate(
            self,
            *,
            goal: GoalUnderstandingResult,
            agent_profile,
            platform_profile,
            cart,
            browse_history,
            orders,
            catalog,
        ) -> RecommendationSpec:
            return self.result
    
    
    def goal_understanding(
        *,
        query: str = "通勤",
        intents: list[str] | None = None,
        requirement_status: str = "ready",
        next_question: str | None = None,
    ) -> GoalUnderstandingResult:
        ordered_intents = intents or ["product_recommendation"]
        slots = {
            "query": query,
            "max_price_cents": 30000,
            "scenario": "self",
        }
        return GoalUnderstandingResult(
            primary_intent=ordered_intents[0],
            intents=ordered_intents,
            pending_intents=ordered_intents[1:],
            goal=f"推荐与 {query} 相关的商品",
            confidence=0.95,
            slots=slots,
            recommendation_requirements=RecommendationRequirementState(
                status=requirement_status,
                slots=RecommendationRequirementSlots(
                    query=query,
                    max_price_cents=30000,
                    scenario="self",
                ),
                next_question=next_question,
                collection_reason="模型判断当前推荐需求状态",
            ),
            pending_intent_question=(
                "当前已处理第一个意图。需要我继续处理后续意图吗？"
                if len(ordered_intents) > 1
                else None
            ),
        )
    
    
    def recommendation_spec(
        *,
        queries: list[str] | None = None,
    ) -> RecommendationSpec:
        return RecommendationSpec(
            goal_summary="推荐预算 300 元以内的通勤商品",
            hard_constraints=RecommendationSpecHardConstraints(
                max_price_cents=30000,
            ),
            preferred_categories=["箱包"],
            preferred_tags=["通勤"],
            search_queries=queries or ["通勤", "办公室"],
            scenario="self",
            usage="通勤",
            source_evidence=[],
            confidence=0.9,
        )
    
    
    def test_broad_recall_does_not_promote_diagnostic_query_to_demand() -> None:
        goal = goal_understanding(
            requirement_status="bypassed",
            query="",
        )
        spec = recommendation_spec(queries=["通勤"]).model_copy(
            update={"recall_mode": "broad"}
        )
    
        demand = recommendation_demand_from_goal(goal, spec)
    
        assert demand.query == ""
    
    
    def scored_candidate(
        *,
        product_id: str,
        channel: str,
        score: float,
        ad: AdInfo | None = None,
    ) -> ScoredProduct:
        product = Product(
            id=product_id,
            name=product_id,
            description="",
            price_cents=1000,
            category="箱包",
            stock=10,
            is_ad=ad is not None,
            ad_label="广告" if ad is not None else None,
        )
        return ScoredProduct(
            product=product,
            channel=channel,
            score=score,
            confidence="high",
            evidence=[
                SourceEvidence(
                    source="need",
                    signal_score=1,
                    weighted_points=45,
                    reason="符合当前需求",
                )
            ],
            ad=ad,
        )
    
    
    def recommendation_batch(
        *,
        organic: list[ScoredProduct],
        ads: list[ScoredProduct],
        ad_only: bool = False,
        cutoff: float | None = None,
    ) -> RecommendationBatch:
        return RecommendationBatch(
            demand=RecommendationDemand(query="通勤"),
            organic_candidates=organic,
            ad_candidates=ads,
            cutoff_score=cutoff,
            competitive_ads=ads,
            requires_semantic_ranking=bool(ads),
            ad_only=ad_only,
            source_statuses={"cart": "ok_with_data"},
            generated_at="2026-11-03T00:00:00+00:00",
        )
    
    
    def test_normalize_openai_base_url() -> None:
        assert (
            normalize_openai_base_url("https://api.deepseek.com")
            == "https://api.deepseek.com"
        )
        assert (
            normalize_openai_base_url(
                "https://api.deepseek.com/v1/chat/completions"
            )
            == "https://api.deepseek.com/v1"
        )
    
    
    def test_context_tools_read_mall_service_data() -> None:
        context = ShoppingAgentContext(mall=mall_client())
    
        browse = json.loads(invoke_tool(context, "get_browse_history", {}))
        orders = json.loads(invoke_tool(context, "get_order_history", {}))
        cart = json.loads(invoke_tool(context, "get_cart", {}))
        platform_profile = json.loads(
            invoke_tool(context, "get_platform_profile", {})
        )
        agent_profile = json.loads(invoke_tool(context, "get_agent_profile", {}))
    
        assert browse["items"][0]["product_id"] == "moon-lamp"
        assert orders["items"][0]["order_id"] == "order-1001"
        assert cart["cart"]["items"][0]["product_id"] == "commuter-backpack"
        assert platform_profile["profile"]["confidence"] == 0.76
        assert agent_profile["profile"]["source"] == "agent_memory"
    
    
    def test_unavailable_source_returns_structured_status() -> None:
        context = ShoppingAgentContext(mall=UnavailableMall())
    
        result = json.loads(invoke_tool(context, "get_browse_history", {}))
    
        assert result["status"] == "unavailable"
    ✓ • 0ms

## Activity

    $ sed -n '380,900p' agent-service/tests/test_agent_api.py
        )
        monkeypatch.setattr(api_module, "stream_agent_reply", failing_stream)
    
        response = client.post(
            "/api/chat/stream",
            json={"message": "失败测试"},
        )
    
        assert "模型调用失败" in response.text
        conversation = store.list_conversations(1)[0]
        detail = store.get_conversation(1, conversation.id)
        assert detail is not None
        assert detail.messages[1].content == "已经生成的部分"
        assert detail.messages[1].status == "failed"
    
    
    def test_stream_chat_passes_previous_plan_state_to_next_turn(
        store: ConversationStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        conversation_id = store.create_conversation(1, "继续推荐")
        store.add_message(conversation_id, "user", "先推荐商品", "completed")
        store.add_message(
            conversation_id,
            "assistant",
            "已完成第一轮",
            "completed",
            metadata={
                "plan_state": PLAN_STATE,
                "recommendations": [
                    {
                        "id": "tote",
                        "name": "帆布托特包",
                        "description": "日常通勤",
                        "price_cents": 6900,
                        "category": "箱包",
                    }
                ],
                "goal_understanding": GOAL_UNDERSTANDING,
                "orders": [ORDER_LINK],
            },
        )
        captured: dict[str, object] = {}
    
        async def capturing_stream(
            messages,
            config,
            mall,
            previous_plan_state=None,
            previous_recommendations=None,
            previous_orders=None,
            previous_goal_understanding=None,
        ):
            captured["plan_state"] = previous_plan_state
            captured["previous_recommendations"] = previous_recommendations
            captured["previous_orders"] = previous_orders
            captured["previous_goal_understanding"] = previous_goal_understanding
            yield {"type": "start", "message_id": "assistant-next"}
            yield {"type": "delta", "content": "继续完成"}
            yield {
                "type": "done",
                "tool_trace": [],
                "plan_state": previous_plan_state.model_dump(mode="json")
                if previous_plan_state
                else None,
            }
    
        monkeypatch.setattr(api_module, "load_llm_config", lambda: TEST_CONFIG)
        monkeypatch.setattr(api_module, "stream_agent_reply", capturing_stream)
    
        response = client.post(
            "/api/chat/stream",
            json={
                "conversation_id": conversation_id,
                "message": "继续刚才的计划",
            },
        )
    
        assert response.status_code == 200
        assert captured["plan_state"] is not None
        assert captured["plan_state"].plan.plan_id == "plan-test"
        assert captured["plan_state"].current_step_id == "submit"
        assert captured["previous_recommendations"][0].id == "tote"
        assert captured["previous_orders"][0].order_id == "order-test"
        assert captured["previous_goal_understanding"].pending_intents == [
            "order_query"
        ]
        assert (
            captured["previous_goal_understanding"]
            .recommendation_requirements.slots.max_price_cents
            == 30000
        )
    
    
    def test_conversation_history_endpoints(store: ConversationStore) -> None:
        conversation_id = store.create_conversation(1, "购买礼物")
        store.add_message(conversation_id, "user", "购买礼物", "completed")
        store.add_message(conversation_id, "assistant", "推荐托特包", "completed")
    
        list_response = client.get("/api/conversations")
        detail_response = client.get(f"/api/conversations/{conversation_id}")
    
        assert list_response.status_code == 200
        assert list_response.json()["items"][0]["title"] == "购买礼物"
        assert list_response.json()["items"][0]["message_count"] == 2
        assert detail_response.status_code == 200
        assert detail_response.json()["messages"][1]["content"] == "推荐托特包"
    
    
    def test_unknown_conversation_returns_404(store: ConversationStore) -> None:
        response = client.get("/api/conversations/missing")
    
        assert response.status_code == 404
    ✓ • 0ms

## Activity

    $ rg -n "model_copy|finish_message|message_metadata|done" agent-service/tests/test_agent_api.py | sed -n '1,180p'
    203:        "type": "done",
    273:    assert '"type": "done"' in response.text
    440:            "type": "done",
    ✓ • 0ms

## Activity

    $ rg -n "pythonpath|pytest" -S . -g 'pyproject.toml' -g 'pytest.ini' -g 'tox.ini' -g 'setup.cfg' -g 'uv.lock' | sed -n '1,120p'
    ./pyproject.toml:5:dev = ["pytest>=8"]
    ./pyproject.toml:7:[tool.pytest.ini_options]
    ./pyproject.toml:8:pythonpath = ["agent-service/src", "mall-service/src"]
    ./uv.lock:18:dev = [{ name = "pytest", specifier = ">=8" }]
    ./uv.lock:1231:name = "pytest"
    ./uv.lock:1241:sdist = { url = "https://files.pythonhosted.org/packages/79/42/bb4641652e58dedeac2ec51abc1f8cae4fee4ec63899a0999016229a0f2a/pytest-9.2.0.tar.gz", hash = "sha256:97c4f3b1f3c7414aa36465e09b8220f1d03627993bd51b1282e193753c80557b", size = 1797555, upload-time = "2026-10-27T21:30:20.728Z" }
    ./uv.lock:1243:    { url = "https://files.pythonhosted.org/packages/51/39/1f5d8c8877a0fa327db959c19341d4be61660de1ab6b7391f9eb805bcd67/pytest-9.2.0-py3-none-any.whl", hash = "sha256:07acdcf88ec174f907dc01af70bf52d49b014bbab03faeeade31c96b18c2e588", size = 411776, upload-time = "2026-10-27T21:30:19.131Z" },
    ✓ • 0ms

## Activity

    $ cat pyproject.toml
    [tool.uv.workspace]
    members = ["agent-service", "mall-service"]
    
    [dependency-groups]
    dev = ["pytest>=8"]
    
    [tool.pytest.ini_options]
    pythonpath = ["agent-service/src", "mall-service/src"]
    testpaths = ["agent-service/tests", "mall-service/tests"]
    ✓ • 0ms

## Activity

    $ cat agent-service/tests/test_prompt_loader.py && sed -n '1,120p' agent-service/src/agent_service/mall_gateway.py
    from pathlib import Path
    
    import pytest
    
    from agent_service.prompt_loader import (
        MAX_PROMPT_BYTES,
        PromptLoadError,
        load_prompt,
    )
    
    
    def test_load_prompt_reads_any_utf8_file(tmp_path: Path) -> None:
        prompt_path = tmp_path / "agent.md"
        prompt_path.write_text("  通用提示词  ", encoding="utf-8")
    
        assert load_prompt(prompt_path) == "通用提示词"
    
    
    def test_load_prompt_reloads_file_contents(tmp_path: Path) -> None:
        prompt_path = tmp_path / "agent.md"
        prompt_path.write_text("版本一", encoding="utf-8")
        assert load_prompt(prompt_path) == "版本一"
    
        prompt_path.write_text("版本二", encoding="utf-8")
        assert load_prompt(prompt_path) == "版本二"
    
    
    def test_missing_prompt_file_has_clear_error(tmp_path: Path) -> None:
        with pytest.raises(PromptLoadError, match="not found"):
            load_prompt(tmp_path / "missing.md")
    
    
    def test_empty_prompt_file_is_rejected(tmp_path: Path) -> None:
        prompt_path = tmp_path / "empty.md"
        prompt_path.write_text("   \n", encoding="utf-8")
    
        with pytest.raises(PromptLoadError, match="empty"):
            load_prompt(prompt_path)
    
    
    def test_oversized_prompt_file_is_rejected(tmp_path: Path) -> None:
        prompt_path = tmp_path / "large.md"
        prompt_path.write_bytes(b"x" * (MAX_PROMPT_BYTES + 1))
    
        with pytest.raises(PromptLoadError, match="exceeds"):
            load_prompt(prompt_path)
    
    
    def test_non_utf8_prompt_file_is_rejected(tmp_path: Path) -> None:
        prompt_path = tmp_path / "invalid.md"
        prompt_path.write_bytes(b"\xff\xfe\xfa")
    
        with pytest.raises(PromptLoadError, match="UTF-8"):
            load_prompt(prompt_path)
    from typing import Protocol
    
    from .models import (
        BrowseEvent,
        CreateOrderItem,
        OrderRecord,
        PlatformProfile,
        Product,
        ProductCandidate,
        ProductList,
        RecommendationSpec,
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
    
        async def search_organic_with_spec(
            self,
            spec: RecommendationSpec,
            limit: int = 10,
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
    
        async def search_ads_with_spec(
            self,
            spec: RecommendationSpec,
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
    ✓ • 0ms

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/models.py
    @@ -327,2 +327,20 @@
     
    +class FinalRecommendation(BaseModel):
    +    product_id: str = Field(min_length=1, max_length=100)
    +    rank: int = Field(ge=1)
    +    channel: Literal["organic", "ad"]
    +    reason: str = Field(min_length=1, max_length=500)
    +    reason_source: Literal[
    +        "semantic_reranker",
    +        "formula_scoring",
    +        "unavailable",
    +    ]
    +    environmental_fit: str | None = Field(default=None, max_length=500)
    +
    +
    +class RecommendationDecision(BaseModel):
    +    summary: str = Field(default="", max_length=1_000)
    +    items: list[FinalRecommendation] = Field(default_factory=list)
    +
    +
     PlanStepStatus = Literal[
    @@ -431,2 +449,3 @@
         orders: list[OrderLink] = Field(default_factory=list)
    +    recommendation_decision: RecommendationDecision | None = None
     
    @@ -447 +466,95 @@
         items: list[ConversationSummary]
    +
    +
    +class ConversationEvidence(BaseModel):
    +    message_id: str = Field(min_length=1, max_length=100)
    +    quote: str = Field(min_length=1, max_length=2_000)
    +
    +
    +class ProductKeyInformation(BaseModel):
    +    name: str = Field(min_length=1, max_length=100)
    +    value: str = Field(min_length=1, max_length=500)
    +    source_field: Literal[
    +        "name",
    +        "description",
    +        "category",
    +        "tags",
    +        "badge",
    +    ]
    +    source_text: str = Field(min_length=1, max_length=2_000)
    +
    +
    +class ProductKeyInformationGroup(BaseModel):
    +    product_id: str = Field(min_length=1, max_length=100)
    +    items: list[ProductKeyInformation] = Field(default_factory=list)
    +
    +
    +class FeedbackAspect(BaseModel):
    +    name: str = Field(min_length=1, max_length=100)
    +    value: str | None = Field(default=None, max_length=500)
    +    polarity: Literal["positive", "negative", "neutral", "uncertain"]
    +
    +
    +class ProductFeedback(BaseModel):
    +    product_id: str = Field(min_length=1, max_length=100)
    +    overall: Literal["positive", "negative", "neutral", "mixed", "unclear"]
    +    aspects: list[FeedbackAspect] = Field(default_factory=list)
    +    evidence: list[ConversationEvidence] = Field(min_length=1)
    +    confidence: float = Field(ge=0, le=1)
    +
    +
    +class GeneralPreference(BaseModel):
    +    dimension: str = Field(min_length=1, max_length=100)
    +    value: str = Field(min_length=1, max_length=500)
    +    polarity: Literal["prefer", "avoid"]
    +    evidence: list[ConversationEvidence] = Field(min_length=1)
    +    confidence: float = Field(ge=0, le=1)
    +
    +
    +class ConversationSummaryDraft(BaseModel):
    +    summary: str = Field(min_length=1, max_length=4_000)
    +    user_goals: list[str] = Field(default_factory=list)
    +    explicit_constraints: list[str] = Field(default_factory=list)
    +    product_key_information: list[ProductKeyInformationGroup] = Field(
    +        default_factory=list
    +    )
    +    product_feedback: list[ProductFeedback] = Field(default_factory=list)
    +    general_preferences: list[GeneralPreference] = Field(default_factory=list)
    +    unresolved_items: list[str] = Field(default_factory=list)
    +
    +
    +class RecommendedProductSummary(BaseModel):
    +    product: Product
    +    key_information: list[ProductKeyInformation] = Field(default_factory=list)
    +    reason: str | None = Field(default=None, max_length=500)
    +    reason_source: Literal[
    +        "semantic_reranker",
    +        "formula_scoring",
    +        "unavailable",
    +    ] = "unavailable"
    +    environmental_fit: str | None = Field(default=None, max_length=500)
    +
    +
    +class RecommendationRoundSummary(BaseModel):
    +    assistant_message_id: str = Field(min_length=1, max_length=100)
    +    user_request: str = Field(min_length=1, max_length=100_000)
    +    ranking_summary: str = Field(default="", max_length=1_000)
    +    products: list[RecommendedProductSummary] = Field(default_factory=list)
    +
    +
    +class ConversationDigest(BaseModel):
    +    conversation_id: str = Field(min_length=1, max_length=100)
    +    source_updated_at: str = Field(min_length=1, max_length=100)
    +    summary: str = Field(min_length=1, max_length=4_000)
    +    user_goals: list[str] = Field(default_factory=list)
    +    explicit_constraints: list[str] = Field(default_factory=list)
    +    recommendation_rounds: list[RecommendationRoundSummary] = Field(
    +        default_factory=list
    +    )
    +    product_feedback: list[ProductFeedback] = Field(default_factory=list)
    +    general_preferences: list[GeneralPreference] = Field(
    +        default_factory=list
    +    )
    +    unresolved_items: list[str] = Field(default_factory=list)
    +    source_message_ids: list[str] = Field(default_factory=list)
    +    generated_at: str = Field(min_length=1, max_length=100)

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/agent_runner.py
    @@ -41,2 +41,3 @@
         CreateOrderItem,
    +    FinalRecommendation,
         GoalUnderstandingResult,
    @@ -53,2 +54,3 @@
         RecommendationDemand,
    +    RecommendationDecision,
         RecommendationSpec,
    @@ -150,2 +152,3 @@
         selected_products: dict[str, Product] = field(default_factory=dict)
    +    recommendation_decision: RecommendationDecision | None = None
         created_orders: dict[str, OrderLink] = field(default_factory=dict)
    @@ -180,2 +183,3 @@
         selected: dict[str, Product] = {}
    +    selected_candidates: list[tuple[Product, ScoredProduct]] = []
         for candidate in candidates:
    @@ -202,2 +206,3 @@
             selected[product.id] = product
    +        selected_candidates.append((product, candidate))
     
    @@ -209,4 +214,20 @@
             selected = {}
    +        selected_candidates = []
     
         context.selected_products = selected
    +    context.recommendation_decision = RecommendationDecision(
    +        items=[
    +            FinalRecommendation(
    +                product_id=product.id,
    +                rank=rank,
    +                channel=candidate.channel,
    +                reason=formula_recommendation_reason(candidate),
    +                reason_source="formula_scoring",
    +            )
    +            for rank, (product, candidate) in enumerate(
    +                selected_candidates,
    +                start=1,
    +            )
    +        ]
    +    )
         context.submitted = True
    @@ -215,2 +236,15 @@
     
    +def formula_recommendation_reason(candidate: ScoredProduct) -> str:
    +    reasons = list(
    +        dict.fromkeys(
    +            evidence.reason.strip()
    +            for evidence in candidate.evidence
    +            if evidence.reason.strip()
    +        )
    +    )
    +    if reasons:
    +        return "；".join(reasons[:3])[:500]
    +    return f"综合评分 {candidate.score:.1f}，满足当前推荐条件"
    +
    +
     def product_payload(products: Sequence[Product]) -> str:

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/agent_runner.py
    @@ -249,2 +249,26 @@
     
    +def semantic_recommendation_decision(
    +    ranking: SemanticRankingResult,
    +    selected_products: Sequence[Product],
    +) -> RecommendationDecision:
    +    selected_ids = {product.id for product in selected_products}
    +    ranked_items = [
    +        item for item in ranking.items if item.product_id in selected_ids
    +    ]
    +    return RecommendationDecision(
    +        summary=ranking.summary,
    +        items=[
    +            FinalRecommendation(
    +                product_id=item.product_id,
    +                rank=rank,
    +                channel=item.channel,
    +                reason=item.reason,
    +                reason_source="semantic_reranker",
    +                environmental_fit=item.environmental_fit,
    +            )
    +            for rank, item in enumerate(ranked_items, start=1)
    +        ],
    +    )
    +
    +
     def product_payload(products: Sequence[Product]) -> str:

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/agent_runner.py
    @@ -1153,2 +1153,3 @@
             context.selected_products.clear()
    +        context.recommendation_decision = None
             context.semantic_ranking = None
    @@ -1258,2 +1259,6 @@
             context.semantic_ranking = ranking
    +        context.recommendation_decision = semantic_recommendation_decision(
    +            ranking,
    +            selected,
    +        )
             return json.dumps(

## Activity

    $ rg -n '"recommendation_spec": \(' agent-service/src/agent_service/agent_runner.py
    978:                    "recommendation_spec": (
    1593:            "recommendation_spec": (
    1624:            "recommendation_spec": (
    1661:            "recommendation_spec": (
    1701:            "recommendation_spec": (
    ✓ • 0ms

## Activity

    $ sed -n '1560,1720p' agent-service/src/agent_service/agent_runner.py
                    "type": "recommendations",
                    "message_id": message_id,
                    "products": [
                        product.model_dump(mode="json")
                        for product in context.selected_products.values()
                    ],
                }
    
            trace_outcome = "completed"
            yield {
                "type": "done",
                "message_id": message_id,
                "tool_trace": [
                    trace.model_dump(mode="json") for trace in context.tool_trace
                ],
                "plan_state": (
                    context.plan_state.model_dump(mode="json")
                    if context.plan_state is not None
                    else None
                ),
                "orders": [
                    order.model_dump(mode="json")
                    for order in context.created_orders.values()
                ],
                "recommendations": [
                    product.model_dump(mode="json")
                    for product in context.selected_products.values()
                ],
                "goal_understanding": (
                    context.goal_understanding.model_dump(mode="json")
                    if context.goal_understanding is not None
                    else None
                ),
                "recommendation_spec": (
                    context.recommendation_spec.model_dump(mode="json")
                    if context.recommendation_spec is not None
                    else None
                ),
            }
        except PromptLoadError as exc:
            trace_session.finish("failed", exc)
            yield {
                "type": "error",
                "message_id": message_id,
                "message": f"Agent 提示词加载失败：{exc}",
                "tool_trace": [],
                "plan_state": (
                    context.plan_state.model_dump(mode="json")
                    if context.plan_state is not None
                    else None
                ),
                "orders": [
                    order.model_dump(mode="json")
                    for order in context.created_orders.values()
                ],
                "recommendations": [
                    product.model_dump(mode="json")
                    for product in context.selected_products.values()
                ],
                "goal_understanding": (
                    context.goal_understanding.model_dump(mode="json")
                    if context.goal_understanding is not None
                    else None
                ),
                "recommendation_spec": (
                    context.recommendation_spec.model_dump(mode="json")
                    if context.recommendation_spec is not None
                    else None
                ),
            }
        except MaxTurnsExceeded:
            trace_session.finish("failed")
            yield {
                "type": "error",
                "message_id": message_id,
                "message": (
                    f"Agent 超过最大工具回合数（{config.max_turns}），"
                    "当前多源推荐流程至少需要 10 个回合。"
                    "请将配置中的 max_turns 设为 10，并重启 Agent 服务。"
                ),
                "tool_trace": [
                    trace.model_dump(mode="json") for trace in context.tool_trace
                ],
                "plan_state": (
                    context.plan_state.model_dump(mode="json")
                    if context.plan_state is not None
                    else None
                ),
                "orders": [
                    order.model_dump(mode="json")
                    for order in context.created_orders.values()
                ],
                "recommendations": [
                    product.model_dump(mode="json")
                    for product in context.selected_products.values()
                ],
                "goal_understanding": (
                    context.goal_understanding.model_dump(mode="json")
                    if context.goal_understanding is not None
                    else None
                ),
                "recommendation_spec": (
                    context.recommendation_spec.model_dump(mode="json")
                    if context.recommendation_spec is not None
                    else None
                ),
            }
        except (asyncio.CancelledError, GeneratorExit):
            trace_outcome = "cancelled"
            raise
        except Exception as exc:
            trace_session.finish("failed", exc)
            logger.exception("Agents SDK run failed")
            yield {
                "type": "error",
                "message_id": message_id,
                "message": (
                    "Agent 调用失败，请检查模型服务是否支持 Chat Completions "
                    "工具调用，并查看 agent-service 终端日志。"
                ),
                "tool_trace": [
                    trace.model_dump(mode="json") for trace in context.tool_trace
                ],
                "plan_state": (
                    context.plan_state.model_dump(mode="json")
                    if context.plan_state is not None
                    else None
                ),
                "orders": [
                    order.model_dump(mode="json")
                    for order in context.created_orders.values()
                ],
                "recommendations": [
                    product.model_dump(mode="json")
                    for product in context.selected_products.values()
                ],
                "goal_understanding": (
                    context.goal_understanding.model_dump(mode="json")
                    if context.goal_understanding is not None
                    else None
                ),
                "recommendation_spec": (
                    context.recommendation_spec.model_dump(mode="json")
                    if context.recommendation_spec is not None
                    else None
                ),
            }
        finally:
            trace_session.finish(trace_outcome)
            if client is not None:
                await client.close()
    ✓ • 0ms

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/agent_runner.py
    @@ -1597,2 +1597,7 @@
                 ),
    +            "recommendation_decision": (
    +                context.recommendation_decision.model_dump(mode="json")
    +                if context.recommendation_decision is not None
    +                else None
    +            ),
             }
    @@ -1628,2 +1633,7 @@
                 ),
    +            "recommendation_decision": (
    +                context.recommendation_decision.model_dump(mode="json")
    +                if context.recommendation_decision is not None
    +                else None
    +            ),
             }
    @@ -1665,2 +1675,7 @@
                 ),
    +            "recommendation_decision": (
    +                context.recommendation_decision.model_dump(mode="json")
    +                if context.recommendation_decision is not None
    +                else None
    +            ),
             }
    @@ -1705,2 +1720,7 @@
                 ),
    +            "recommendation_decision": (
    +                context.recommendation_decision.model_dump(mode="json")
    +                if context.recommendation_decision is not None
    +                else None
    +            ),
             }

## Activity

    $ rg -n 'recommendation_decision' agent-service/src/agent_service/agent_runner.py
    153:    recommendation_decision: RecommendationDecision | None = None
    218:    context.recommendation_decision = RecommendationDecision(
    250:def semantic_recommendation_decision(
    1154:        context.recommendation_decision = None
    1260:        context.recommendation_decision = semantic_recommendation_decision(
    1598:            "recommendation_decision": (
    1599:                context.recommendation_decision.model_dump(mode="json")
    1600:                if context.recommendation_decision is not None
    1634:            "recommendation_decision": (
    1635:                context.recommendation_decision.model_dump(mode="json")
    1636:                if context.recommendation_decision is not None
    1676:            "recommendation_decision": (
    1677:                context.recommendation_decision.model_dump(mode="json")
    1678:                if context.recommendation_decision is not None
    1721:            "recommendation_decision": (
    1722:                context.recommendation_decision.model_dump(mode="json")
    1723:                if context.recommendation_decision is not None
    ✓ • 0ms

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/api.py
    @@ -22,2 +22,3 @@
         Product,
    +    RecommendationDecision,
         RecommendationSpec,
    @@ -97,2 +98,3 @@
         recommendation_spec: RecommendationSpec | None = None
    +    recommendation_decision: RecommendationDecision | None = None
         created_orders: dict[str, OrderLink] = {}
    @@ -126,2 +128,6 @@
                 )
    +        if recommendation_decision is not None:
    +            metadata["recommendation_decision"] = (
    +                recommendation_decision.model_dump(mode="json")
    +            )
             if created_orders:
    @@ -242,2 +248,9 @@
                         )
    +                decision_payload = event.get("recommendation_decision")
    +                if isinstance(decision_payload, dict):
    +                    recommendation_decision = (
    +                        RecommendationDecision.model_validate(
    +                            decision_payload
    +                        )
    +                    )
                     store.finish_message(
    @@ -283,2 +296,9 @@
                         )
    +                decision_payload = event.get("recommendation_decision")
    +                if isinstance(decision_payload, dict):
    +                    recommendation_decision = (
    +                        RecommendationDecision.model_validate(
    +                            decision_payload
    +                        )
    +                    )
                     store.finish_message(

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/storage.py
    @@ -3,2 +3,3 @@
     import sqlite3
    +from dataclasses import dataclass
     from datetime import datetime, timezone
    @@ -9,2 +10,3 @@
     from .models import (
    +    ConversationDigest,
         ConversationDetail,
    @@ -15,2 +17,3 @@
         Product,
    +    RecommendationDecision,
         RecommendationSpec,
    @@ -25,2 +28,9 @@
     
    +@dataclass(frozen=True)
    +class ConversationSummaryCandidate:
    +    conversation_id: str
    +    user_id: int
    +    updated_at: str
    +
    +
     def utc_now() -> str:
    @@ -81,2 +91,21 @@
     
    +                CREATE TABLE IF NOT EXISTS conversation_summaries (
    +                    conversation_id TEXT PRIMARY KEY,
    +                    status TEXT NOT NULL
    +                        CHECK (status IN ('completed', 'failed')),
    +                    source_updated_at TEXT NOT NULL,
    +                    summary_json TEXT,
    +                    prompt_version TEXT NOT NULL,
    +                    summarizer_model TEXT NOT NULL,
    +                    generated_at TEXT,
    +                    last_attempt_at TEXT NOT NULL,
    +                    error TEXT,
    +                    FOREIGN KEY (conversation_id)
    +                        REFERENCES conversations(id)
    +                        ON DELETE CASCADE
    +                );
    +
    +                CREATE INDEX IF NOT EXISTS idx_conversation_summaries_status
    +                    ON conversation_summaries(status, source_updated_at);
    +
                     UPDATE messages

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/storage.py
    @@ -353,2 +353,12 @@
                     recommendation_spec = None
    +        recommendation_decision: RecommendationDecision | None = None
    +        if isinstance(metadata.get("recommendation_decision"), dict):
    +            try:
    +                recommendation_decision = (
    +                    RecommendationDecision.model_validate(
    +                        metadata["recommendation_decision"]
    +                    )
    +                )
    +            except ValueError:
    +                recommendation_decision = None
             orders = [
    @@ -370,2 +380,3 @@
                 orders=orders,
    +            recommendation_decision=recommendation_decision,
             )

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/storage.py
    @@ -312,2 +312,163 @@
     
    +    @repository_operation("conversation_summary.list_due")
    +    def list_conversations_due_for_summary(
    +        self,
    +        cutoff: str,
    +        *,
    +        limit: int = 50,
    +    ) -> list[ConversationSummaryCandidate]:
    +        with self.connect() as connection:
    +            rows = connection.execute(
    +                """
    +                SELECT c.id, c.user_id, c.updated_at
    +                FROM conversations c
    +                LEFT JOIN conversation_summaries s
    +                    ON s.conversation_id = c.id
    +                WHERE c.updated_at <= ?
    +                  AND (
    +                      s.conversation_id IS NULL
    +                      OR s.status = 'failed'
    +                      OR s.summary_json IS NULL
    +                      OR s.source_updated_at < c.updated_at
    +                  )
    +                ORDER BY c.updated_at ASC
    +                LIMIT ?
    +                """,
    +                (cutoff, limit),
    +            ).fetchall()
    +        return [
    +            ConversationSummaryCandidate(
    +                conversation_id=row["id"],
    +                user_id=row["user_id"],
    +                updated_at=row["updated_at"],
    +            )
    +            for row in rows
    +        ]
    +
    +    @repository_operation("conversation_summary.get")
    +    def get_conversation_summary(
    +        self,
    +        user_id: int,
    +        conversation_id: str,
    +    ) -> ConversationDigest | None:
    +        with self.connect() as connection:
    +            row = connection.execute(
    +                """
    +                SELECT s.summary_json
    +                FROM conversation_summaries s
    +                JOIN conversations c ON c.id = s.conversation_id
    +                WHERE c.id = ?
    +                  AND c.user_id = ?
    +                  AND s.summary_json IS NOT NULL
    +                """,
    +                (conversation_id, user_id),
    +            ).fetchone()
    +        if row is None:
    +            return None
    +        try:
    +            return ConversationDigest.model_validate_json(row["summary_json"])
    +        except ValueError:
    +            return None
    +
    +    @repository_operation("conversation_summary.save")
    +    def save_conversation_summary(
    +        self,
    +        digest: ConversationDigest,
    +        *,
    +        prompt_version: str,
    +        summarizer_model: str,
    +    ) -> None:
    +        now = utc_now()
    +        with self.connect() as connection:
    +            connection.execute(
    +                """
    +                INSERT INTO conversation_summaries(
    +                    conversation_id,
    +                    status,
    +                    source_updated_at,
    +                    summary_json,
    +                    prompt_version,
    +                    summarizer_model,
    +                    generated_at,
    +                    last_attempt_at,
    +                    error
    +                )
    +                VALUES (?, 'completed', ?, ?, ?, ?, ?, ?, NULL)
    +                ON CONFLICT(conversation_id) DO UPDATE SET
    +                    status = 'completed',
    +                    source_updated_at = excluded.source_updated_at,
    +                    summary_json = excluded.summary_json,
    +                    prompt_version = excluded.prompt_version,
    +                    summarizer_model = excluded.summarizer_model,
    +                    generated_at = excluded.generated_at,
    +                    last_attempt_at = excluded.last_attempt_at,
    +                    error = NULL
    +                """,
    +                (
    +                    digest.conversation_id,
    +                    digest.source_updated_at,
    +                    digest.model_dump_json(),
    +                    prompt_version,
    +                    summarizer_model,
    +                    digest.generated_at,
    +                    now,
    +                ),
    +            )
    +
    +    @repository_operation("conversation_summary.fail")
    +    def record_conversation_summary_failure(
    +        self,
    +        conversation_id: str,
    +        *,
    +        source_updated_at: str,
    +        prompt_version: str,
    +        summarizer_model: str,
    +        error: str,
    +    ) -> None:
    +        now = utc_now()
    +        with self.connect() as connection:
    +            existing = connection.execute(
    +                """
    +                SELECT 1 FROM conversation_summaries
    +                WHERE conversation_id = ?
    +                """,
    +                (conversation_id,),
    +            ).fetchone()
    +            if existing is None:
    +                connection.execute(
    +                    """
    +                    INSERT INTO conversation_summaries(
    +                        conversation_id,
    +                        status,
    +                        source_updated_at,
    +                        summary_json,
    +                        prompt_version,
    +                        summarizer_model,
    +                        generated_at,
    +                        last_attempt_at,
    +                        error
    +                    )
    +                    VALUES (?, 'failed', ?, NULL, ?, ?, NULL, ?, ?)
    +                    """,
    +                    (
    +                        conversation_id,
    +                        source_updated_at,
    +                        prompt_version,
    +                        summarizer_model,
    +                        now,
    +                        error,
    +                    ),
    +                )
    +                return
    +            connection.execute(
    +                """
    +                UPDATE conversation_summaries
    +                SET status = 'failed',
    +                    last_attempt_at = ?,
    +                    error = ?
    +                WHERE conversation_id = ?
    +                """,
    +                (now, error, conversation_id),
    +            )
    +
         @staticmethod

## Assistant

最终推荐决策的数据通路已经补齐：公式推荐会记录公式证据理由，语义终排会覆盖为终排模型返回的原始理由和排序摘要。现在开始实现单会话总结器和严格的来源校验。

## Activity

    file changes: Completed · 1 changes
    Add: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/conversation_summary.py
    import json
    import re
    from pathlib import Path
    from typing import Any, Protocol
    
    from agents import Agent, ModelSettings
    from pydantic import ValidationError
    
    from .llm_config import LLMConfig
    from .models import (
        ConversationDetail,
        ConversationDigest,
        ConversationEvidence,
        ConversationSummaryDraft,
        Product,
        ProductKeyInformation,
        ProductKeyInformationGroup,
        RecommendedProductSummary,
        RecommendationRoundSummary,
        StoredMessage,
    )
    from .observability.agents import run_observed_action
    from .prompt_loader import PromptLoadError, load_prompt
    from .storage import utc_now
    
    
    CONVERSATION_SUMMARY_PROMPT_VERSION = "conversation-summary-v1"
    CONVERSATION_SUMMARY_PROMPT_PATH = (
        Path(__file__).resolve().parents[2]
        / "prompts"
        / "conversation_summary.md"
    )
    
    
    class ConversationSummaryError(Exception):
        """Raised when a conversation digest cannot be generated or validated."""
    
    
    class ConversationSummarizer(Protocol):
        async def summarize(
            self,
            *,
            conversation: ConversationDetail,
            source_updated_at: str,
        ) -> ConversationDigest: ...
    
    
    def _json_payload(text: str) -> dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end < start:
            raise ConversationSummaryError(
                "conversation summary did not return a JSON object"
            )
        try:
            payload = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ConversationSummaryError(
                "conversation summary returned invalid JSON"
            ) from exc
        if not isinstance(payload, dict):
            raise ConversationSummaryError(
                "conversation summary JSON must be an object"
            )
        return payload
    
    
    def _completed_messages(
        conversation: ConversationDetail,
    ) -> list[StoredMessage]:
        return [
            message
            for message in conversation.messages
            if message.role == "user" or message.status == "completed"
        ]
    
    
    def _summary_input(conversation: ConversationDetail) -> dict[str, object]:
        messages: list[dict[str, object]] = []
        for message in _completed_messages(conversation):
            payload: dict[str, object] = {
                "message_id": message.id,
                "role": message.role,
                "content": message.content,
            }
            if message.recommendations:
                payload["recommendations"] = [
                    product.model_dump(mode="json")
                    for product in message.recommendations
                ]
            if message.recommendation_decision is not None:
                payload["recommendation_decision"] = (
                    message.recommendation_decision.model_dump(mode="json")
                )
            messages.append(payload)
        return {
            "conversation_id": conversation.id,
            "conversation_title": conversation.title,
            "messages": messages,
        }
    
    
    def _normalized_text(value: str) -> str:
        return " ".join(value.split())
    
    
    def _validate_evidence(
        evidence: ConversationEvidence,
        *,
        user_messages: dict[str, StoredMessage],
    ) -> None:
        message = user_messages.get(evidence.message_id)
        if message is None:
            raise ConversationSummaryError(
                f"evidence references non-user message {evidence.message_id}"
            )
        if _normalized_text(evidence.quote) not in _normalized_text(message.content):
            raise ConversationSummaryError(
                f"evidence quote is not present in message {evidence.message_id}"
            )
    
    
    def _product_source_text(product: Product, source_field: str) -> str:
        if source_field == "name":
            return product.name
        if source_field == "description":
            return product.description
        if source_field == "category":
            return product.category
        if source_field == "tags":
            return "\n".join(product.tags)
        if source_field == "badge":
            return product.badge or ""
        return ""
    
    
    def _validate_key_information(
        information: ProductKeyInformation,
        product: Product,
    ) -> None:
        source_text = _product_source_text(product, information.source_field)
        if _normalized_text(information.source_text) not in _normalized_text(
            source_text
        ):
            raise ConversationSummaryError(
                f"product {product.id} key information for "
                f"{information.name} is not grounded in {information.source_field}"
            )
    
    
    def _validate_draft(
        draft: ConversationSummaryDraft,
        conversation: ConversationDetail,
    ) -> None:
        messages = _completed_messages(conversation)
        user_messages = {
            message.id: message for message in messages if message.role == "user"
        }
        products = {
            product.id: product
            for message in messages
            for product in message.recommendations
        }
    
        seen_groups: set[str] = set()
        for group in draft.product_key_information:
            if group.product_id in seen_groups:
                raise ConversationSummaryError(
                    f"duplicate product key information for {group.product_id}"
                )
            seen_groups.add(group.product_id)
            product = products.get(group.product_id)
            if product is None:
                raise ConversationSummaryError(
                    f"product key information references unknown product "
                    f"{group.product_id}"
                )
            for information in group.items:
                _validate_key_information(information, product)
    
        for feedback in draft.product_feedback:
            if feedback.product_id not in products:
                raise ConversationSummaryError(
                    f"feedback references unknown product {feedback.product_id}"
                )
            for evidence in feedback.evidence:
                _validate_evidence(evidence, user_messages=user_messages)
    
        for preference in draft.general_preferences:
            for evidence in preference.evidence:
                _validate_evidence(evidence, user_messages=user_messages)
    
    
    def assemble_conversation_digest(
        *,
        conversation: ConversationDetail,
        draft: ConversationSummaryDraft,
        source_updated_at: str,
        generated_at: str | None = None,
    ) -> ConversationDigest:
        _validate_draft(draft, conversation)
        messages = _completed_messages(conversation)
        key_information = {
            group.product_id: group.items
            for group in draft.product_key_information
        }
        rounds: list[RecommendationRoundSummary] = []
        last_user_request = ""
    
        for message in messages:
            if message.role == "user":
                last_user_request = message.content
                continue
            if not message.recommendations:
                continue
    
            decision_items = (
                {
                    item.product_id: item
                    for item in message.recommendation_decision.items
                }
                if message.recommendation_decision is not None
                else {}
            )
            products = []
            for product in message.recommendations:
                decision_item = decision_items.get(product.id)
                products.append(
                    RecommendedProductSummary(
                        product=product,
                        key_information=key_information.get(product.id, []),
                        reason=decision_item.reason if decision_item else None,
                        reason_source=(
                            decision_item.reason_source
                            if decision_item
                            else "unavailable"
                        ),
                        environmental_fit=(
                            decision_item.environmental_fit
                            if decision_item
                            else None
                        ),
                    )
                )
            rounds.append(
                RecommendationRoundSummary(
                    assistant_message_id=message.id,
                    user_request=last_user_request or "(用户请求未记录)",
                    ranking_summary=(
                        message.recommendation_decision.summary
                        if message.recommendation_decision is not None
                        else ""
                    ),
                    products=products,
                )
            )
    
        return ConversationDigest(
            conversation_id=conversation.id,
            source_updated_at=source_updated_at,
            summary=draft.summary,
            user_goals=draft.user_goals,
            explicit_constraints=draft.explicit_constraints,
            recommendation_rounds=rounds,
            product_feedback=draft.product_feedback,
            general_preferences=draft.general_preferences,
            unresolved_items=draft.unresolved_items,
            source_message_ids=[message.id for message in messages],
            generated_at=generated_at or utc_now(),
        )
    
    
    class AgentConversationSummarizer:
        def __init__(self, *, config: LLMConfig, model: Any) -> None:
            self.config = config
            self.model = model
    
        async def summarize(
            self,
            *,
            conversation: ConversationDetail,
            source_updated_at: str,
        ) -> ConversationDigest:
            try:
                instructions = load_prompt(CONVERSATION_SUMMARY_PROMPT_PATH)
            except PromptLoadError as exc:
                raise ConversationSummaryError(str(exc)) from exc
    
            agent = Agent[Any](
                name="conversation-summarizer",
                instructions=instructions,
                model=self.model,
                model_settings=ModelSettings(
                    temperature=self.config.temperature,
                    max_tokens=self.config.output_token_limit,
                ),
            )
            payload = _summary_input(conversation)
            try:
                result = await run_observed_action(
                    agent,
                    action_name="conversation_summary",
                    model=str(self.config.model),
                    input=json.dumps(
                        payload,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                    max_turns=1,
                )
            except Exception as exc:
                raise ConversationSummaryError(
                    "conversation summary model call failed: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
    
            if not isinstance(result.final_output, str):
                raise ConversationSummaryError(
                    "conversation summary returned non-text output"
                )
            try:
                draft = ConversationSummaryDraft.model_validate(
                    _json_payload(result.final_output)
                )
            except ValidationError as exc:
                raise ConversationSummaryError(
                    "conversation summary returned invalid data"
                ) from exc
            return assemble_conversation_digest(
                conversation=conversation,
                draft=draft,
                source_updated_at=source_updated_at,
            )

## Activity

    file changes: Completed · 1 changes
    Add: /Users/mindeng/workspace/niub-shangcheng/agent-service/prompts/conversation_summary.md
    # 单会话购物对话总结器
    
    你只负责总结一段已经结束或暂时闲置的多轮购物对话。不要生成用户画像，不要合并其他
    会话，不要提出新的推荐，也不要修改商品或推荐理由。
    
    ## 输入
    
    你会收到一个 JSON 对象，包含：
    
    - `conversation_id` 和 `conversation_title`；
    - `messages`：按时间顺序排列的已完成对话消息；
    - 每条消息的 `message_id`、`role` 和 `content`；
    - Assistant 推荐消息中的 `recommendations` 商品快照；
    - Assistant 推荐消息中的 `recommendation_decision` 最终推荐决策。
    
    `recommendation_decision.items` 中的 `reason` 是最终推荐理由。代码会原样保留这些理由，
    你不需要重新编写商品推荐理由。
    
    ## 提取规则
    
    1. 只从用户消息中提取用户目标、商品反馈和一般偏好。
    2. Assistant 的陈述只能帮助理解上下文，不能作为用户偏好的证据。
    3. 商品反馈必须指向 `recommendations` 中实际出现的商品。
    4. 用户没有评价商品时，不生成 `product_feedback`。
    5. 区分具体商品、具体属性和一般偏好：
       - “我不喜欢这个包”是对具体商品的反馈；
       - “这个包太重了”是对具体商品重量属性的反馈；
       - “我平时不喜欢太重的包”是一般偏好。
    6. 不要过度泛化。“这个黑色款太大了”不能提取成“不喜欢黑色”。
    7. 用户表达含糊时，将 `polarity` 或 `overall` 标为 `uncertain` / `unclear`，不要猜测。
    8. 商品关键信息只能来自输入商品快照的 `name`、`description`、`category`、
       `tags` 或 `badge`。保留尺寸、颜色、品牌、材质、容量等对理解商品重要的信息。
    9. `source_text` 必须逐字复制对应商品字段中支持该信息的原文片段。
    10. 每条商品反馈和一般偏好都必须引用用户消息，`quote` 必须逐字出现在用户消息中。
    11. 只提取用户明确表达的一般偏好，不推断隐含偏好。
    12. 总结只覆盖当前 `conversation_id`，不要假设其他会话的内容。
    
    ## 商品关键信息
    
    为每件推荐商品选择少量最有用的关键信息，通常 1 到 8 条。优先保留：
    
    - 品牌；
    - 尺寸、规格、容量、重量；
    - 颜色、材质、风格；
    - 适用场景；
    - 决定性功能或限制。
    
    不要选择只用于营销但没有辨识度的形容词。
    
    ## 输出
    
    只输出 JSON，不要输出 Markdown 或额外说明。必须使用以下结构：
    
    ```json
    {
      "summary": "对整段购买需求和推荐过程的简洁总结",
      "user_goals": ["用户希望完成的目标"],
      "explicit_constraints": ["用户明确给出的预算、品类、规格或场景约束"],
      "product_key_information": [
        {
          "product_id": "商品 ID",
          "items": [
            {
              "name": "尺寸",
              "value": "大号",
              "source_field": "description",
              "source_text": "商品描述中的原始片段"
            }
          ]
        }
      ],
      "product_feedback": [
        {
          "product_id": "商品 ID",
          "overall": "negative",
          "aspects": [
            {
              "name": "尺寸",
              "value": "偏大",
              "polarity": "negative"
            }
          ],
          "evidence": [
            {
              "message_id": "用户消息 ID",
              "quote": "用户原话"
            }
          ],
          "confidence": 0.98
        }
      ],
      "general_preferences": [
        {
          "dimension": "重量",
          "value": "偏轻",
          "polarity": "prefer",
          "evidence": [
            {
              "message_id": "用户消息 ID",
              "quote": "用户原话"
            }
          ],
          "confidence": 0.95
        }
      ],
      "unresolved_items": ["对话中没有确认或仍待后续处理的事项"]
    }
    ```
    
    枚举约束：
    
    - `source_field` 只能是 `name`、`description`、`category`、`tags`、`badge`；
    - `overall` 只能是 `positive`、`negative`、`neutral`、`mixed`、`unclear`；
    - `aspects[].polarity` 只能是 `positive`、`negative`、`neutral`、`uncertain`；
    - `general_preferences[].polarity` 只能是 `prefer`、`avoid`；
    - `confidence` 必须在 0 到 1 之间。
    
    没有对应内容时返回空数组，不要编造。

## Activity

    file changes: Completed · 1 changes
    Add: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/conversation_summary_worker.py
    import asyncio
    import logging
    import os
    from collections.abc import Callable
    from dataclasses import dataclass
    from datetime import datetime, timedelta, timezone
    
    from agents import OpenAIChatCompletionsModel
    from openai import AsyncOpenAI
    
    from .agent_runner import normalize_openai_base_url
    from .conversation_summary import (
        CONVERSATION_SUMMARY_PROMPT_VERSION,
        AgentConversationSummarizer,
        ConversationSummarizer,
    )
    from .llm_config import LLMConfig, load_llm_config
    from .storage import ConversationStore
    
    
    logger = logging.getLogger(__name__)
    
    DEFAULT_SUMMARY_INTERVAL_SECONDS = 3_600
    DEFAULT_SUMMARY_IDLE_SECONDS = 3_600
    DEFAULT_SUMMARY_BATCH_SIZE = 50
    
    
    # Scheduling assumption:
    # This worker does not acquire per-conversation locks or leases. The deployment
    # must guarantee exactly one scheduler invocation at a time, either through one
    # scheduler node or an external distributed scheduler. Concurrent execution for
    # the same conversation is explicitly out of scope.
    
    
    # TODO(conversation-summary-freshness):
    # A conversation has no usable summary until it has been idle long enough and
    # the next summary job has completed. Conversation recall must fall back to raw
    # completed turns whenever the digest is absent or stale.
    
    
    @dataclass(frozen=True)
    class ConversationSummarySettings:
        interval_seconds: int = DEFAULT_SUMMARY_INTERVAL_SECONDS
        idle_seconds: int = DEFAULT_SUMMARY_IDLE_SECONDS
        batch_size: int = DEFAULT_SUMMARY_BATCH_SIZE
        enabled: bool = True
    
    
    @dataclass(frozen=True)
    class ConversationSummaryCycleResult:
        completed: int = 0
        failed: int = 0
        skipped: int = 0
    
    
    def load_conversation_summary_settings() -> ConversationSummarySettings:
        return ConversationSummarySettings(
            interval_seconds=_positive_int_env(
                "CONVERSATION_SUMMARY_INTERVAL_SECONDS",
                DEFAULT_SUMMARY_INTERVAL_SECONDS,
            ),
            idle_seconds=_positive_int_env(
                "CONVERSATION_SUMMARY_IDLE_SECONDS",
                DEFAULT_SUMMARY_IDLE_SECONDS,
            ),
            batch_size=_positive_int_env(
                "CONVERSATION_SUMMARY_BATCH_SIZE",
                DEFAULT_SUMMARY_BATCH_SIZE,
            ),
            enabled=_bool_env("CONVERSATION_SUMMARY_SCHEDULER_ENABLED", True),
        )
    
    
    def _positive_int_env(name: str, default: int) -> int:
        value = os.getenv(name)
        if value is None:
            return default
        try:
            parsed = int(value)
        except ValueError:
            logger.warning("invalid %s=%r; using %s", name, value, default)
            return default
        if parsed <= 0:
            logger.warning("non-positive %s=%r; using %s", name, value, default)
            return default
        return parsed
    
    
    def _bool_env(name: str, default: bool) -> bool:
        value = os.getenv(name)
        if value is None:
            return default
        return value.strip().lower() not in {"0", "false", "no", "off"}
    
    
    class ConversationSummaryWorker:
        def __init__(
            self,
            store: ConversationStore,
            *,
            settings: ConversationSummarySettings | None = None,
            summarizer: ConversationSummarizer | None = None,
            summarizer_model: str | None = None,
            config_loader: Callable[[], LLMConfig] = load_llm_config,
        ) -> None:
            self.store = store
            self.settings = settings or load_conversation_summary_settings()
            self.summarizer = summarizer
            self.summarizer_model = summarizer_model
            self.config_loader = config_loader
    
        async def run_forever(self) -> None:
            while True:
                try:
                    await self.run_once()
                except asyncio.CancelledError:
                    raise
                except Exception:
                    logger.exception("conversation summary cycle failed")
                await asyncio.sleep(self.settings.interval_seconds)
    
        async def run_once(
            self,
            *,
            now: datetime | None = None,
        ) -> ConversationSummaryCycleResult:
            current_time = now or datetime.now(timezone.utc)
            cutoff = (current_time - timedelta(
                seconds=self.settings.idle_seconds
            )).isoformat(timespec="milliseconds")
            candidates = self.store.list_conversations_due_for_summary(
                cutoff,
                limit=self.settings.batch_size,
            )
            if not candidates:
                return ConversationSummaryCycleResult()
    
            client: AsyncOpenAI | None = None
            summarizer = self.summarizer
            model_name = self.summarizer_model
            try:
                if summarizer is None:
                    config = self.config_loader()
                    client = AsyncOpenAI(
                        api_key=config.api_key.get_secret_value(),
                        base_url=normalize_openai_base_url(config.base_url),
                        timeout=config.model_timeout_limit,
                        max_retries=1,
                    )
                    model = OpenAIChatCompletionsModel(
                        model=config.model,
                        openai_client=client,
                        buffer_streamed_tool_calls=True,
                    )
                    summarizer = AgentConversationSummarizer(
                        config=config,
                        model=model,
                    )
                    model_name = config.model
    
                resolved_model_name = model_name or "injected-summarizer"
                completed = 0
                failed = 0
                skipped = 0
                for candidate in candidates:
                    conversation = self.store.get_conversation(
                        candidate.user_id,
                        candidate.conversation_id,
                    )
                    if conversation is None:
                        skipped += 1
                        continue
                    try:
                        digest = await summarizer.summarize(
                            conversation=conversation,
                            source_updated_at=candidate.updated_at,
                        )
                        self.store.save_conversation_summary(
                            digest,
                            prompt_version=CONVERSATION_SUMMARY_PROMPT_VERSION,
                            summarizer_model=resolved_model_name,
                        )
                        completed += 1
                    except asyncio.CancelledError:
                        raise
                    except Exception as exc:
                        failed += 1
                        logger.exception(
                            "conversation summary failed for %s",
                            candidate.conversation_id,
                        )
                        self.store.record_conversation_summary_failure(
                            candidate.conversation_id,
                            source_updated_at=candidate.updated_at,
                            prompt_version=CONVERSATION_SUMMARY_PROMPT_VERSION,
                            summarizer_model=resolved_model_name,
                            error=f"{type(exc).__name__}: {exc}",
                        )
                return ConversationSummaryCycleResult(
                    completed=completed,
                    failed=failed,
                    skipped=skipped,
                )
            finally:
                if client is not None:
                    await client.close()

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/api.py
    @@ -3,2 +3,3 @@
     from collections.abc import AsyncIterator, Sequence
    +from contextlib import asynccontextmanager, suppress
     
    @@ -9,2 +10,6 @@
     from .chat import compose_reply
    +from .conversation_summary_worker import (
    +    ConversationSummaryWorker,
    +    load_conversation_summary_settings,
    +)
     from .llm_config import LLMConfig, LLMConfigError, load_llm_config
    @@ -15,2 +20,3 @@
         ChatResponse,
    +    ConversationDigest,
         ConversationDetail,
    @@ -34,4 +40,31 @@
     
    -app = FastAPI(title="Agent Service", version="0.1.0")
     
    +@asynccontextmanager
    +async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    +    settings = load_conversation_summary_settings()
    +    task: asyncio.Task[None] | None = None
    +    if settings.enabled:
    +        worker = ConversationSummaryWorker(
    +            get_conversation_store(),
    +            settings=settings,
    +        )
    +        task = asyncio.create_task(
    +            worker.run_forever(),
    +            name="conversation-summary-worker",
    +        )
    +    try:
    +        yield
    +    finally:
    +        if task is not None:
    +            task.cancel()
    +            with suppress(asyncio.CancelledError):
    +                await task
    +
    +
    +app = FastAPI(
    +    title="Agent Service",
    +    version="0.1.0",
    +    lifespan=lifespan,
    +)
    +
     

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/api.py
    @@ -459,2 +459,19 @@
     
    +@app.get(
    +    "/api/conversations/{conversation_id}/summary",
    +    response_model=ConversationDigest,
    +)
    +def get_conversation_summary(
    +    conversation_id: str,
    +    store: ConversationStore = Depends(get_conversation_store),
    +) -> ConversationDigest:
    +    conversation = store.get_conversation(FIXED_USER_ID, conversation_id)
    +    if conversation is None:
    +        raise HTTPException(status_code=404, detail="对话不存在")
    +    summary = store.get_conversation_summary(FIXED_USER_ID, conversation_id)
    +    if summary is None:
    +        raise HTTPException(status_code=404, detail="对话总结尚未生成")
    +    return summary
    +
    +
     @app.post("/api/chat", response_model=ChatResponse)

## Activity

    $ uv run python -m compileall -q agent-service/src agent-service/tests
    ✓ • 0ms

## Activity

    $ git diff --check
    ✓ • 0ms

## Assistant

核心模块已落地，代码可以通过语法编译。接下来我会补测试，重点覆盖：同一时间戳不重复生成、对话复用后重新生成、总结期间对话继续更新时的旧版本保存语义，以及缺少总结时的只读接口行为。

## Activity

    $ uv run pytest agent-service/tests/test_agent_runner.py agent-service/tests/test_agent_api.py agent-service/tests/test_storage.py -q
    ..........................................                               [100%]
    42 passed in 1.58s
    ✓ • 2.06s

## Activity

    $ rg -n '^def test_.*recommend|^def test_.*formula|invoke_tool\(.*recommend_products' agent-service/tests/test_agent_runner.py | sed -n '1,100p'
    429:def test_recommendation_and_ad_tools_register_candidates() -> None:
    519:def test_create_order_rejects_product_outside_known_recommendations() -> None:
    556:def test_collecting_requirements_block_recommendation_steps() -> None:
    713:def test_collect_context_and_generate_recommendation_spec_are_separate_actions(
    776:def test_recommendation_spec_agent_uses_own_prompt_and_explicit_constraints() -> None:
    845:def test_recommend_products_formula_path_selects_top_two() -> None:
    873:def test_recommend_products_returns_no_match_without_eligible_candidates() -> None:
    1131:def test_model_generated_requirement_question_ends_turn_without_recommendation() -> None:
    1452:def test_purchase_turn_uses_previous_recommendation_and_emits_order() -> None:
    ✓ • 0ms

## Activity

    $ sed -n '835,875p' agent-service/tests/test_agent_runner.py
        )
    
        assert spec.hard_constraints.max_price_cents == 30000
        assert spec.search_queries == ["通勤包", "轻便通勤包"]
        assert model.first_call is not None
        assert "Recommendation SPEC Generator" in (
            model.first_call.system_instructions or ""
        )
    
    
    def test_recommend_products_formula_path_selects_top_two() -> None:
        context = ShoppingAgentContext(mall=mall_client(), user_id=999)
        context.goal_understanding = goal_understanding(query="家居")
        prepare_recommendation_context(
            context,
            spec=recommendation_spec(queries=["家居", "居家"]),
        )
        context.ad_search_candidates = []
        context.ad_search_status = "ok_empty"
    
        result = json.loads(
            invoke_tool(
                context,
                "recommend_products",
                {},
            )
        )
    
        assert result["status"] == "accepted"
        assert context.recommendation_batch is not None
        assert context.recommendation_batch.requires_semantic_ranking is False
        assert len(context.selected_products) == 2
        assert all(
            product.is_ad is False
            for product in context.selected_products.values()
        )
    
    
    def test_recommend_products_returns_no_match_without_eligible_candidates() -> None:
        context = ShoppingAgentContext(mall=mall_client(), user_id=999)
        context.goal_understanding = goal_understanding(query="宠物用品")
    ✓ • 0ms

## Activity

    file changes: Completed · 1 changes
    Add: /Users/mindeng/workspace/niub-shangcheng/agent-service/tests/test_conversation_summary.py
    import pytest
    
    from agent_service.conversation_summary import (
        ConversationSummaryError,
        assemble_conversation_digest,
    )
    from agent_service.models import (
        ConversationDetail,
        ConversationEvidence,
        ConversationSummaryDraft,
        FeedbackAspect,
        FinalRecommendation,
        GeneralPreference,
        Product,
        ProductFeedback,
        ProductKeyInformation,
        ProductKeyInformationGroup,
        RecommendationDecision,
        StoredMessage,
    )
    
    
    def _conversation(*, feedback_quote: str = "这个黑色款太大了，我不喜欢") -> ConversationDetail:
        product = Product(
            id="tote-large",
            name="通勤托特包",
            description="黑色大号容量，可放 16 英寸电脑",
            price_cents=69900,
            category="箱包",
            badge="通勤推荐",
            tags=["通勤", "大容量"],
        )
        return ConversationDetail(
            id="conversation-summary",
            title="通勤包推荐",
            message_count=4,
            created_at="2026-11-13T00:00:00.000+00:00",
            updated_at="2026-11-13T00:05:00.000+00:00",
            messages=[
                StoredMessage(
                    id="user-1",
                    role="user",
                    content="推荐一个适合通勤的包，预算 1000 元以内",
                    status="completed",
                    created_at="2026-11-13T00:00:00.000+00:00",
                ),
                StoredMessage(
                    id="assistant-1",
                    role="assistant",
                    content="推荐这款通勤托特包，容量大。",
                    status="completed",
                    created_at="2026-11-13T00:01:00.000+00:00",
                    recommendations=[product],
                    recommendation_decision=RecommendationDecision(
                        summary="容量和通勤场景更匹配",
                        items=[
                            FinalRecommendation(
                                product_id="tote-large",
                                rank=1,
                                channel="organic",
                                reason="大容量适合携带电脑，且符合通勤场景",
                                reason_source="semantic_reranker",
                            )
                        ],
                    ),
                ),
                StoredMessage(
                    id="user-2",
                    role="user",
                    content=feedback_quote,
                    status="completed",
                    created_at="2026-11-13T00:02:00.000+00:00",
                ),
                StoredMessage(
                    id="assistant-2",
                    role="assistant",
                    content="理解，你更希望尺寸小一些。",
                    status="completed",
                    created_at="2026-11-13T00:03:00.000+00:00",
                ),
            ],
        )
    
    
    def _draft(quote: str = "这个黑色款太大了，我不喜欢") -> ConversationSummaryDraft:
        return ConversationSummaryDraft(
            summary="用户寻找预算 1000 元内的通勤包，并认为推荐款尺寸偏大。",
            user_goals=["寻找适合通勤的包"],
            explicit_constraints=["预算不超过 1000 元"],
            product_key_information=[
                ProductKeyInformationGroup(
                    product_id="tote-large",
                    items=[
                        ProductKeyInformation(
                            name="尺寸",
                            value="大号",
                            source_field="description",
                            source_text="黑色大号容量",
                        ),
                        ProductKeyInformation(
                            name="场景",
                            value="通勤",
                            source_field="tags",
                            source_text="通勤",
                        ),
                    ],
                )
            ],
            product_feedback=[
                ProductFeedback(
                    product_id="tote-large",
                    overall="negative",
                    aspects=[
                        FeedbackAspect(
                            name="尺寸",
                            value="偏大",
                            polarity="negative",
                        )
                    ],
                    evidence=[
                        ConversationEvidence(
                            message_id="user-2",
                            quote=quote,
                        )
                    ],
                    confidence=0.98,
                )
            ],
            general_preferences=[
                GeneralPreference(
                    dimension="重量",
                    value="偏轻",
                    polarity="prefer",
                    evidence=[
                        ConversationEvidence(
                            message_id="user-2",
                            quote=quote,
                        )
                    ],
                    confidence=0.8,
                )
            ],
            unresolved_items=["尚未确认更小尺寸的替代款"],
        )
    
    
    def test_summary_keeps_final_reason_and_grounded_product_information() -> None:
        digest = assemble_conversation_digest(
            conversation=_conversation(),
            draft=_draft(),
            source_updated_at="2026-11-13T00:05:00.000+00:00",
            generated_at="2026-11-13T02:00:00.000+00:00",
        )
    
        assert digest.source_updated_at == "2026-11-13T00:05:00.000+00:00"
        assert len(digest.recommendation_rounds) == 1
        product = digest.recommendation_rounds[0].products[0]
        assert product.product.id == "tote-large"
        assert product.reason == "大容量适合携带电脑，且符合通勤场景"
        assert product.reason_source == "semantic_reranker"
        assert product.key_information[0].value == "大号"
        assert digest.product_feedback[0].evidence[0].message_id == "user-2"
    
    
    def test_summary_rejects_feedback_that_does_not_quote_user_message() -> None:
        with pytest.raises(ConversationSummaryError, match="quote is not present"):
            assemble_conversation_digest(
                conversation=_conversation(),
                draft=_draft("我从来不喜欢黑色"),
                source_updated_at="2026-11-13T00:05:00.000+00:00",
            )
    
    
    def test_summary_rejects_ungrounded_product_information() -> None:
        draft = _draft()
        draft.product_key_information[0].items[0].source_text = "限量真皮材质"
    
        with pytest.raises(ConversationSummaryError, match="not grounded"):
            assemble_conversation_digest(
                conversation=_conversation(),
                draft=draft,
                source_updated_at="2026-11-13T00:05:00.000+00:00",
            )
    
    
    def test_summary_rejects_assistant_text_as_user_evidence() -> None:
        draft = _draft()
        draft.product_feedback[0].evidence[0].message_id = "assistant-2"
        draft.product_feedback[0].evidence[0].quote = "你更希望尺寸小一些"
    
        with pytest.raises(ConversationSummaryError, match="non-user message"):
            assemble_conversation_digest(
                conversation=_conversation(),
                draft=draft,
                source_updated_at="2026-11-13T00:05:00.000+00:00",
            )
    
    
    def test_summary_without_product_feedback_keeps_empty_feedback() -> None:
        draft = _draft()
        draft.product_feedback = []
        draft.general_preferences = []
    
        digest = assemble_conversation_digest(
            conversation=_conversation(),
            draft=draft,
            source_updated_at="2026-11-13T00:05:00.000+00:00",
        )
    
        assert digest.product_feedback == []
        assert digest.general_preferences == []

## Activity

    file changes: Completed · 1 changes
    Add: /Users/mindeng/workspace/niub-shangcheng/agent-service/tests/test_conversation_summary_worker.py
    from datetime import datetime, timedelta, timezone
    from pathlib import Path
    
    from agent_service.conversation_summary import ConversationSummaryError
    from agent_service.conversation_summary_worker import (
        ConversationSummarySettings,
        ConversationSummaryWorker,
    )
    from agent_service.models import ConversationDigest, ConversationDetail
    from agent_service.storage import ConversationStore, utc_now
    
    
    def _settings() -> ConversationSummarySettings:
        return ConversationSummarySettings(
            interval_seconds=3_600,
            idle_seconds=3_600,
            batch_size=50,
        )
    
    
    def _digest(
        conversation_id: str,
        source_updated_at: str,
    ) -> ConversationDigest:
        return ConversationDigest(
            conversation_id=conversation_id,
            source_updated_at=source_updated_at,
            summary="用户咨询了商品推荐。",
            generated_at=utc_now(),
        )
    
    
    def _later_than(updated_at: str, *, hours: int = 2) -> datetime:
        return datetime.fromisoformat(updated_at) + timedelta(hours=hours)
    
    
    class RecordingSummarizer:
        def __init__(self) -> None:
            self.calls: list[str] = []
    
        async def summarize(
            self,
            *,
            conversation: ConversationDetail,
            source_updated_at: str,
        ) -> ConversationDigest:
            self.calls.append(source_updated_at)
            return _digest(conversation.id, source_updated_at)
    
    
    class UpdatingSummarizer(RecordingSummarizer):
        def __init__(self, store: ConversationStore) -> None:
            super().__init__()
            self.store = store
            self.updated = False
    
        async def summarize(
            self,
            *,
            conversation: ConversationDetail,
            source_updated_at: str,
        ) -> ConversationDigest:
            if not self.updated:
                self.updated = True
                self.store.add_message(
                    conversation.id,
                    "user",
                    "我又补充一个需求",
                    "completed",
                )
            return await super().summarize(
                conversation=conversation,
                source_updated_at=source_updated_at,
            )
    
    
    class FailingSummarizer:
        async def summarize(
            self,
            *,
            conversation: ConversationDetail,
            source_updated_at: str,
        ) -> ConversationDigest:
            raise ConversationSummaryError("model unavailable")
    
    
    def _conversation(store: ConversationStore) -> ConversationDetail:
        conversation_id = store.create_conversation(1, "推荐通勤包")
        store.add_message(
            conversation_id,
            "user",
            "推荐一个通勤包",
            "completed",
        )
        store.add_message(
            conversation_id,
            "assistant",
            "推荐这款通勤包。",
            "completed",
        )
        conversation = store.get_conversation(1, conversation_id)
        assert conversation is not None
        return conversation
    
    
    def test_worker_only_summarizes_idle_conversations(tmp_path: Path) -> None:
        store = ConversationStore(tmp_path / "summary.db")
        conversation = _conversation(store)
        summarizer = RecordingSummarizer()
        worker = ConversationSummaryWorker(
            store,
            settings=_settings(),
            summarizer=summarizer,
            summarizer_model="test-summary-model",
        )
    
        recent = worker.run_once(
            now=datetime.fromisoformat(conversation.updated_at)
        )
        assert recent.completed == 0
        assert summarizer.calls == []
    
        due = worker.run_once(now=_later_than(conversation.updated_at))
        assert due.completed == 1
        assert summarizer.calls == [conversation.updated_at]
        stored = store.get_conversation_summary(1, conversation.id)
        assert stored is not None
        assert stored.source_updated_at == conversation.updated_at
    
    
    def test_worker_reuses_summary_until_conversation_timestamp_changes(
        tmp_path: Path,
    ) -> None:
        store = ConversationStore(tmp_path / "summary.db")
        conversation = _conversation(store)
        summarizer = RecordingSummarizer()
        worker = ConversationSummaryWorker(
            store,
            settings=_settings(),
            summarizer=summarizer,
            summarizer_model="test-summary-model",
        )
        first_now = _later_than(conversation.updated_at)
    
        worker.run_once(now=first_now)
        unchanged = worker.run_once(now=first_now)
    
        assert unchanged.completed == 0
        assert len(summarizer.calls) == 1
    
        store.add_message(
            conversation.id,
            "user",
            "再看看更小尺寸的",
            "completed",
        )
        updated = store.get_conversation(1, conversation.id)
        assert updated is not None
    
        refreshed = worker.run_once(now=_later_than(updated.updated_at))
        assert refreshed.completed == 1
        assert len(summarizer.calls) == 2
        stored = store.get_conversation_summary(1, conversation.id)
        assert stored is not None
        assert stored.source_updated_at == updated.updated_at
    
    
    def test_worker_saves_old_snapshot_when_conversation_changes_during_summary(
        tmp_path: Path,
    ) -> None:
        store = ConversationStore(tmp_path / "summary.db")
        conversation = _conversation(store)
        summarizer = UpdatingSummarizer(store)
        worker = ConversationSummaryWorker(
            store,
            settings=_settings(),
            summarizer=summarizer,
            summarizer_model="test-summary-model",
        )
    
        result = worker.run_once(now=_later_than(conversation.updated_at))
    
        assert result.completed == 1
        stored = store.get_conversation_summary(1, conversation.id)
        assert stored is not None
        assert stored.source_updated_at == conversation.updated_at
        updated = store.get_conversation(1, conversation.id)
        assert updated is not None
        assert updated.updated_at > stored.source_updated_at
    
        due = store.list_conversations_due_for_summary(
            _later_than(updated.updated_at).isoformat(timespec="milliseconds")
        )
        assert [candidate.conversation_id for candidate in due] == [
            conversation.id
        ]
    
    
    def test_failed_summary_is_retried_on_next_cycle(tmp_path: Path) -> None:
        store = ConversationStore(tmp_path / "summary.db")
        conversation = _conversation(store)
        worker = ConversationSummaryWorker(
            store,
            settings=_settings(),
            summarizer=FailingSummarizer(),
            summarizer_model="test-summary-model",
        )
        now = _later_than(conversation.updated_at)
    
        first = worker.run_once(now=now)
        second = worker.run_once(now=now)
    
        assert first.failed == 1
        assert second.failed == 1
        assert store.get_conversation_summary(1, conversation.id) is None

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/tests/test_agent_runner.py
    @@ -870,2 +870,8 @@
         )
    +    assert context.recommendation_decision is not None
    +    assert len(context.recommendation_decision.items) == 2
    +    assert {
    +        item.reason_source
    +        for item in context.recommendation_decision.items
    +    } == {"formula_scoring"}
     
    @@ -954,2 +960,13 @@
         assert reranker.environment_context == "明早通勤，需要轻便"
    +    assert context.recommendation_decision is not None
    +    assert [
    +        item.reason for item in context.recommendation_decision.items
    +    ] == [
    +        "更符合通勤用途",
    +        "补充办公室饮用场景",
    +    ]
    +    assert {
    +        item.reason_source
    +        for item in context.recommendation_decision.items
    +    } == {"semantic_reranker"}
     

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/tests/test_agent_api.py
    @@ -157,2 +157,16 @@
     
    +RECOMMENDATION_DECISION = {
    +    "summary": "自然商品优先",
    +    "items": [
    +        {
    +            "product_id": "tote",
    +            "rank": 1,
    +            "channel": "ad",
    +            "reason": "通勤容量和现有需求最匹配",
    +            "reason_source": "semantic_reranker",
    +            "environmental_fit": "适合办公室通勤",
    +        }
    +    ],
    +}
    +
     
    @@ -218,2 +232,3 @@
             "recommendation_spec": RECOMMENDATION_SPEC,
    +        "recommendation_decision": RECOMMENDATION_DECISION,
         }
    @@ -304,2 +319,7 @@
         ]
    +    assert detail.messages[1].recommendation_decision is not None
    +    assert (
    +        detail.messages[1].recommendation_decision.items[0].reason
    +        == "通勤容量和现有需求最匹配"
    +    )
         assert detail.messages[1].tool_trace[0].tool == "search_products"

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/tests/test_agent_api.py
    @@ -10,3 +10,3 @@
     from agent_service.mall_client import get_mall_client
    -from agent_service.models import Product, ProductList
    +from agent_service.models import ConversationDigest, Product, ProductList
     from agent_service.storage import ConversationStore, get_conversation_store
    @@ -508,2 +508,38 @@
     
    +def test_conversation_summary_is_read_only_and_requires_saved_digest(
    +    store: ConversationStore,
    +) -> None:
    +    conversation_id = store.create_conversation(1, "购买礼物")
    +    store.add_message(conversation_id, "user", "购买礼物", "completed")
    +    store.add_message(conversation_id, "assistant", "推荐托特包", "completed")
    +    conversation = store.get_conversation(1, conversation_id)
    +    assert conversation is not None
    +
    +    missing = client.get(f"/api/conversations/{conversation_id}/summary")
    +    manual_trigger = client.post(
    +        f"/api/conversations/{conversation_id}/summary"
    +    )
    +    assert missing.status_code == 404
    +    assert manual_trigger.status_code == 405
    +
    +    store.save_conversation_summary(
    +        ConversationDigest(
    +            conversation_id=conversation_id,
    +            source_updated_at=conversation.updated_at,
    +            summary="用户为送礼场景咨询了托特包。",
    +            generated_at="2026-11-13T03:00:00.000+00:00",
    +        ),
    +        prompt_version="conversation-summary-v1",
    +        summarizer_model="test-model",
    +    )
    +
    +    response = client.get(
    +        f"/api/conversations/{conversation_id}/summary"
    +    )
    +
    +    assert response.status_code == 200
    +    assert response.json()["source_updated_at"] == conversation.updated_at
    +    assert response.json()["summary"] == "用户为送礼场景咨询了托特包。"
    +
    +
     def test_unknown_conversation_returns_404(store: ConversationStore) -> None:

## Activity

    $ uv run pytest agent-service/tests -q
    ...............................................FFFF..................... [ 82%]
    ...............                                                          [100%]
    =================================== FAILURES ===================================
    ________________ test_worker_only_summarizes_idle_conversations ________________
    
    tmp_path = PosixPath('/private/var/folders/9n/3ct2r_2s2rq3mc7xw1xqqjpc0000gn/T/pytest-of-mindeng/pytest-389/test_worker_only_summarizes_id0')
    
        def test_worker_only_summarizes_idle_conversations(tmp_path: Path) -> None:
            store = ConversationStore(tmp_path / "summary.db")
            conversation = _conversation(store)
            summarizer = RecordingSummarizer()
            worker = ConversationSummaryWorker(
                store,
                settings=_settings(),
                summarizer=summarizer,
                summarizer_model="test-summary-model",
            )
    
            recent = worker.run_once(
                now=datetime.fromisoformat(conversation.updated_at)
            )
    >       assert recent.completed == 0
                   ^^^^^^^^^^^^^^^^
    E       AttributeError: 'coroutine' object has no attribute 'completed'
    
    agent-service/tests/test_conversation_summary_worker.py:120: AttributeError
    _______ test_worker_reuses_summary_until_conversation_timestamp_changes ________
    
    tmp_path = PosixPath('/private/var/folders/9n/3ct2r_2s2rq3mc7xw1xqqjpc0000gn/T/pytest-of-mindeng/pytest-389/test_worker_reuses_summary_unt0')
    
        def test_worker_reuses_summary_until_conversation_timestamp_changes(
            tmp_path: Path,
        ) -> None:
            store = ConversationStore(tmp_path / "summary.db")
            conversation = _conversation(store)
            summarizer = RecordingSummarizer()
            worker = ConversationSummaryWorker(
                store,
                settings=_settings(),
                summarizer=summarizer,
                summarizer_model="test-summary-model",
            )
            first_now = _later_than(conversation.updated_at)
    
            worker.run_once(now=first_now)
            unchanged = worker.run_once(now=first_now)
    
    >       assert unchanged.completed == 0
                   ^^^^^^^^^^^^^^^^^^^
    E       AttributeError: 'coroutine' object has no attribute 'completed'
    
    agent-service/tests/test_conversation_summary_worker.py:148: AttributeError
    ___ test_worker_saves_old_snapshot_when_conversation_changes_during_summary ____
    
    tmp_path = PosixPath('/private/var/folders/9n/3ct2r_2s2rq3mc7xw1xqqjpc0000gn/T/pytest-of-mindeng/pytest-389/test_worker_saves_old_snapshot0')
    
        def test_worker_saves_old_snapshot_when_conversation_changes_during_summary(
            tmp_path: Path,
        ) -> None:
            store = ConversationStore(tmp_path / "summary.db")
            conversation = _conversation(store)
            summarizer = UpdatingSummarizer(store)
            worker = ConversationSummaryWorker(
                store,
                settings=_settings(),
                summarizer=summarizer,
                summarizer_model="test-summary-model",
            )
    
            result = worker.run_once(now=_later_than(conversation.updated_at))
    
    >       assert result.completed == 1
                   ^^^^^^^^^^^^^^^^
    E       AttributeError: 'coroutine' object has no attribute 'completed'
    
    agent-service/tests/test_conversation_summary_worker.py:183: AttributeError
    _________________ test_failed_summary_is_retried_on_next_cycle _________________
    
    tmp_path = PosixPath('/private/var/folders/9n/3ct2r_2s2rq3mc7xw1xqqjpc0000gn/T/pytest-of-mindeng/pytest-389/test_failed_summary_is_retried0')
    
        def test_failed_summary_is_retried_on_next_cycle(tmp_path: Path) -> None:
            store = ConversationStore(tmp_path / "summary.db")
            conversation = _conversation(store)
            worker = ConversationSummaryWorker(
                store,
                settings=_settings(),
                summarizer=FailingSummarizer(),
                summarizer_model="test-summary-model",
            )
            now = _later_than(conversation.updated_at)
    
            first = worker.run_once(now=now)
            second = worker.run_once(now=now)
    
    >       assert first.failed == 1
                   ^^^^^^^^^^^^
    E       AttributeError: 'coroutine' object has no attribute 'failed'
    
    agent-service/tests/test_conversation_summary_worker.py:213: AttributeError
    =============================== warnings summary ===============================
    agent-service/tests/test_conversation_summary_worker.py::test_worker_reuses_summary_until_conversation_timestamp_changes
      /Users/mindeng/workspace/niub-shangcheng/agent-service/tests/test_conversation_summary_worker.py:145: RuntimeWarning: coroutine 'ConversationSummaryWorker.run_once' was never awaited
        worker.run_once(now=first_now)
      Enable tracemalloc to get traceback where the object was allocated.
      See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.
    
    agent-service/tests/test_storage.py::test_model_context_excludes_failed_assistant_messages
      /Users/mindeng/workspace/niub-shangcheng/.venv/lib/python3.12/site-packages/opentelemetry/context/contextvars_context.py:28: RuntimeWarning: coroutine 'ConversationSummaryWorker.run_once' was never awaited
        return self._current_context.set(context)
      Enable tracemalloc to get traceback where the object was allocated.
      See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.
    
    -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
    =========================== short test summary info ============================
    FAILED agent-service/tests/test_conversation_summary_worker.py::test_worker_only_summarizes_idle_conversations
    FAILED agent-service/tests/test_conversation_summary_worker.py::test_worker_reuses_summary_until_conversation_timestamp_changes
    FAILED agent-service/tests/test_conversation_summary_worker.py::test_worker_saves_old_snapshot_when_conversation_changes_during_summary
    FAILED agent-service/tests/test_conversation_summary_worker.py::test_failed_summary_is_retried_on_next_cycle
    4 failed, 83 passed, 2 warnings in 1.58s
    ✗ (1) • 2.00s

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/tests/test_conversation_summary_worker.py
    @@ -1,2 +1,3 @@
    -from datetime import datetime, timedelta, timezone
    +import asyncio
    +from datetime import datetime, timedelta
     from pathlib import Path
    @@ -116,4 +117,4 @@
     
    -    recent = worker.run_once(
    -        now=datetime.fromisoformat(conversation.updated_at)
    +    recent = asyncio.run(
    +        worker.run_once(now=datetime.fromisoformat(conversation.updated_at))
         )
    @@ -122,3 +123,5 @@
     
    -    due = worker.run_once(now=_later_than(conversation.updated_at))
    +    due = asyncio.run(
    +        worker.run_once(now=_later_than(conversation.updated_at))
    +    )
         assert due.completed == 1
    @@ -144,4 +147,4 @@
     
    -    worker.run_once(now=first_now)
    -    unchanged = worker.run_once(now=first_now)
    +    asyncio.run(worker.run_once(now=first_now))
    +    unchanged = asyncio.run(worker.run_once(now=first_now))
     
    @@ -159,3 +162,5 @@
     
    -    refreshed = worker.run_once(now=_later_than(updated.updated_at))
    +    refreshed = asyncio.run(
    +        worker.run_once(now=_later_than(updated.updated_at))
    +    )
         assert refreshed.completed == 1
    @@ -180,3 +185,5 @@
     
    -    result = worker.run_once(now=_later_than(conversation.updated_at))
    +    result = asyncio.run(
    +        worker.run_once(now=_later_than(conversation.updated_at))
    +    )
     
    @@ -209,4 +216,4 @@
     
    -    first = worker.run_once(now=now)
    -    second = worker.run_once(now=now)
    +    first = asyncio.run(worker.run_once(now=now))
    +    second = asyncio.run(worker.run_once(now=now))
     

## Activity

    $ uv run pytest agent-service/tests -q
    ........................................................................ [ 82%]
    ...............                                                          [100%]
    87 passed in 1.59s
    ✓ • 1.99s

## Activity

    $ cat agent-service/.env.example && sed -n '1,120p' agent-service/config/llm.example.yaml
    MALL_SERVICE_URL=http://127.0.0.1:8001
    LLM_CONFIG_FILE=agent-service/config/llm.yaml
    AGENT_DB_PATH=agent-service/data/agent.db
    AGENT_SERVICE_HOST=0.0.0.0
    AGENT_SERVICE_PORT=8002
    llm:
      base_url: "https://api.deepseek.com"
      api_key: "replace-with-your-api-key"
      model: "deepseek-flash"
    
      # Optional generation settings. Remove them if your provider does not support them.
      temperature: 0.7
      # 800 等过小值会触发 finish_reason=length，运行时最低按 32768 处理。
      max_tokens: 32768
      timeout_seconds: 1800
      # 推荐主流程和可能的独立语义终排至少需要 10 个模型/工具回合。
      max_turns: 10
      tool_timeout_seconds: 1800
    
    observability:
      enabled: true
    
      service:
        name: "agent-service"
        environment: "local"
        version: "0.1.0"
    
      logs:
        enabled: true
        level: "INFO"
        format: "json"
        access_log: true
    
        # 工具调用明细单独使用 DEBUG，避免把整个服务日志级别切到 DEBUG。
        tool_level: "DEBUG"
        tool:
          include_arguments: true
          include_result: true
          max_payload_chars: 16000
          redact_keys:
            - "authorization"
            - "api_key"
            - "token"
            - "password"
    
      metrics:
        enabled: true
    
        prometheus:
          enabled: true
          path: "/metrics"
    
        log:
          enabled: false
          level: "DEBUG"
          export_interval_millis: 30000
          include_histogram_buckets: true
          max_data_points_per_batch: 1000
    
      traces:
        enabled: true
        sample_ratio: 1.0
        excluded_paths:
          - "/health"
          - "/metrics"
        propagators:
          - "tracecontext"
          - "baggage"
          - "b3multi"
    
        zipkin:
          enabled: true
          endpoint: "http://127.0.0.1:9411/api/v2/spans"
          timeout_millis: 3000
    
        log:
          enabled: true
          # Zipkin 成功时不重复输出；未启用或导出失败时把 trace 输出到日志。
          fallback_only: true
          level: "DEBUG"
          include_events: true
          max_attribute_length: 4000
          max_spans_per_batch: 512
    
        batch:
          max_queue_size: 2048
          schedule_delay_millis: 2000
          max_export_batch_size: 512
    ✓ • 0ms

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/.env.example
    @@ -5 +5,5 @@
     AGENT_SERVICE_PORT=8002
    +CONVERSATION_SUMMARY_SCHEDULER_ENABLED=true
    +CONVERSATION_SUMMARY_INTERVAL_SECONDS=3600
    +CONVERSATION_SUMMARY_IDLE_SECONDS=3600
    +CONVERSATION_SUMMARY_BATCH_SIZE=50

## Activity

    $ git status --short && git diff --stat
     M agent-service/.env.example
     M agent-service/src/agent_service/agent_runner.py
     M agent-service/src/agent_service/api.py
     M agent-service/src/agent_service/models.py
     M agent-service/src/agent_service/storage.py
     M agent-service/tests/test_agent_api.py
     M agent-service/tests/test_agent_runner.py
    ?? agent-service/prompts/conversation_summary.md
    ?? agent-service/src/agent_service/conversation_summary.py
    ?? agent-service/src/agent_service/conversation_summary_worker.py
    ?? agent-service/tests/test_conversation_summary.py
    ?? agent-service/tests/test_conversation_summary_worker.py
     agent-service/.env.example                      |   4 +
     agent-service/src/agent_service/agent_runner.py |  83 ++++++++++
     agent-service/src/agent_service/api.py          |  72 ++++++++-
     agent-service/src/agent_service/models.py       | 113 +++++++++++++
     agent-service/src/agent_service/storage.py      | 201 ++++++++++++++++++++++++
     agent-service/tests/test_agent_api.py           |  58 ++++++-
     agent-service/tests/test_agent_runner.py        |  17 ++
     7 files changed, 546 insertions(+), 2 deletions(-)
    ✓ • 0ms

## Activity

    $ git diff -- agent-service/src/agent_service/models.py agent-service/src/agent_service/storage.py | sed -n '1,320p'
    diff --git a/agent-service/src/agent_service/models.py b/agent-service/src/agent_service/models.py
    index 5504fab..dcbbe2f 100644
    --- a/agent-service/src/agent_service/models.py
    +++ b/agent-service/src/agent_service/models.py
    @@ -325,6 +325,24 @@ class SemanticRankingResult(BaseModel):
         summary: str = Field(default="", max_length=1_000)
    
    
    +class FinalRecommendation(BaseModel):
    +    product_id: str = Field(min_length=1, max_length=100)
    +    rank: int = Field(ge=1)
    +    channel: Literal["organic", "ad"]
    +    reason: str = Field(min_length=1, max_length=500)
    +    reason_source: Literal[
    +        "semantic_reranker",
    +        "formula_scoring",
    +        "unavailable",
    +    ]
    +    environmental_fit: str | None = Field(default=None, max_length=500)
    +
    +
    +class RecommendationDecision(BaseModel):
    +    summary: str = Field(default="", max_length=1_000)
    +    items: list[FinalRecommendation] = Field(default_factory=list)
    +
    +
     PlanStepStatus = Literal[
         "pending",
         "in_progress",
    @@ -429,6 +447,7 @@ class StoredMessage(BaseModel):
         goal_understanding: GoalUnderstandingResult | None = None
         recommendation_spec: RecommendationSpec | None = None
         orders: list[OrderLink] = Field(default_factory=list)
    +    recommendation_decision: RecommendationDecision | None = None
    
    
     class ConversationSummary(BaseModel):
    @@ -445,3 +464,97 @@ class ConversationDetail(ConversationSummary):
    
     class ConversationList(BaseModel):
         items: list[ConversationSummary]
    +
    +
    +class ConversationEvidence(BaseModel):
    +    message_id: str = Field(min_length=1, max_length=100)
    +    quote: str = Field(min_length=1, max_length=2_000)
    +
    +
    +class ProductKeyInformation(BaseModel):
    +    name: str = Field(min_length=1, max_length=100)
    +    value: str = Field(min_length=1, max_length=500)
    +    source_field: Literal[
    +        "name",
    +        "description",
    +        "category",
    +        "tags",
    +        "badge",
    +    ]
    +    source_text: str = Field(min_length=1, max_length=2_000)
    +
    +
    +class ProductKeyInformationGroup(BaseModel):
    +    product_id: str = Field(min_length=1, max_length=100)
    +    items: list[ProductKeyInformation] = Field(default_factory=list)
    +
    +
    +class FeedbackAspect(BaseModel):
    +    name: str = Field(min_length=1, max_length=100)
    +    value: str | None = Field(default=None, max_length=500)
    +    polarity: Literal["positive", "negative", "neutral", "uncertain"]
    +
    +
    +class ProductFeedback(BaseModel):
    +    product_id: str = Field(min_length=1, max_length=100)
    +    overall: Literal["positive", "negative", "neutral", "mixed", "unclear"]
    +    aspects: list[FeedbackAspect] = Field(default_factory=list)
    +    evidence: list[ConversationEvidence] = Field(min_length=1)
    +    confidence: float = Field(ge=0, le=1)
    +
    +
    +class GeneralPreference(BaseModel):
    +    dimension: str = Field(min_length=1, max_length=100)
    +    value: str = Field(min_length=1, max_length=500)
    +    polarity: Literal["prefer", "avoid"]
    +    evidence: list[ConversationEvidence] = Field(min_length=1)
    +    confidence: float = Field(ge=0, le=1)
    +
    +
    +class ConversationSummaryDraft(BaseModel):
    +    summary: str = Field(min_length=1, max_length=4_000)
    +    user_goals: list[str] = Field(default_factory=list)
    +    explicit_constraints: list[str] = Field(default_factory=list)
    +    product_key_information: list[ProductKeyInformationGroup] = Field(
    +        default_factory=list
    +    )
    +    product_feedback: list[ProductFeedback] = Field(default_factory=list)
    +    general_preferences: list[GeneralPreference] = Field(default_factory=list)
    +    unresolved_items: list[str] = Field(default_factory=list)
    +
    +
    +class RecommendedProductSummary(BaseModel):
    +    product: Product
    +    key_information: list[ProductKeyInformation] = Field(default_factory=list)
    +    reason: str | None = Field(default=None, max_length=500)
    +    reason_source: Literal[
    +        "semantic_reranker",
    +        "formula_scoring",
    +        "unavailable",
    +    ] = "unavailable"
    +    environmental_fit: str | None = Field(default=None, max_length=500)
    +
    +
    +class RecommendationRoundSummary(BaseModel):
    +    assistant_message_id: str = Field(min_length=1, max_length=100)
    +    user_request: str = Field(min_length=1, max_length=100_000)
    +    ranking_summary: str = Field(default="", max_length=1_000)
    +    products: list[RecommendedProductSummary] = Field(default_factory=list)
    +
    +
    +class ConversationDigest(BaseModel):
    +    conversation_id: str = Field(min_length=1, max_length=100)
    +    source_updated_at: str = Field(min_length=1, max_length=100)
    +    summary: str = Field(min_length=1, max_length=4_000)
    +    user_goals: list[str] = Field(default_factory=list)
    +    explicit_constraints: list[str] = Field(default_factory=list)
    +    recommendation_rounds: list[RecommendationRoundSummary] = Field(
    +        default_factory=list
    +    )
    +    product_feedback: list[ProductFeedback] = Field(default_factory=list)
    +    general_preferences: list[GeneralPreference] = Field(
    +        default_factory=list
    +    )
    +    unresolved_items: list[str] = Field(default_factory=list)
    +    source_message_ids: list[str] = Field(default_factory=list)
    +    generated_at: str = Field(min_length=1, max_length=100)
    diff --git a/agent-service/src/agent_service/storage.py b/agent-service/src/agent_service/storage.py
    index 1a5de7e..be4c867 100644
    --- a/agent-service/src/agent_service/storage.py
    +++ b/agent-service/src/agent_service/storage.py
    @@ -1,18 +1,21 @@
     import json
     import os
     import sqlite3
    +from dataclasses import dataclass
     from datetime import datetime, timezone
     from functools import lru_cache
     from pathlib import Path
     from uuid import uuid4
    
     from .models import (
    +    ConversationDigest,
         ConversationDetail,
         ConversationSummary,
         GoalUnderstandingResult,
         OrderLink,
         PlanState,
         Product,
    +    RecommendationDecision,
         RecommendationSpec,
         StoredMessage,
         ToolTrace,
    @@ -23,6 +26,13 @@ from .observability.spans import repository_operation
     FIXED_USER_ID = 1
    
    
    +@dataclass(frozen=True)
    +class ConversationSummaryCandidate:
    +    conversation_id: str
    +    user_id: int
    +    updated_at: str
    +
    +
     def utc_now() -> str:
         return datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    
    @@ -79,6 +89,25 @@ class ConversationStore:
                     CREATE INDEX IF NOT EXISTS idx_messages_conversation_sequence
                         ON messages(conversation_id, sequence);
    
    +                CREATE TABLE IF NOT EXISTS conversation_summaries (
    +                    conversation_id TEXT PRIMARY KEY,
    +                    status TEXT NOT NULL
    +                        CHECK (status IN ('completed', 'failed')),
    +                    source_updated_at TEXT NOT NULL,
    +                    summary_json TEXT,
    +                    prompt_version TEXT NOT NULL,
    +                    summarizer_model TEXT NOT NULL,
    +                    generated_at TEXT,
    +                    last_attempt_at TEXT NOT NULL,
    +                    error TEXT,
    +                    FOREIGN KEY (conversation_id)
    +                        REFERENCES conversations(id)
    +                        ON DELETE CASCADE
    +                );
    +
    +                CREATE INDEX IF NOT EXISTS idx_conversation_summaries_status
    +                    ON conversation_summaries(status, source_updated_at);
    +
                     UPDATE messages
                     SET status = 'failed'
                     WHERE status = 'streaming';
    @@ -281,6 +310,167 @@ class ConversationStore:
                 ).fetchall()
             return [self._stored_message(row) for row in rows]
    
    +    @repository_operation("conversation_summary.list_due")
    +    def list_conversations_due_for_summary(
    +        self,
    +        cutoff: str,
    +        *,
    +        limit: int = 50,
    +    ) -> list[ConversationSummaryCandidate]:
    +        with self.connect() as connection:
    +            rows = connection.execute(
    +                """
    +                SELECT c.id, c.user_id, c.updated_at
    +                FROM conversations c
    +                LEFT JOIN conversation_summaries s
    +                    ON s.conversation_id = c.id
    +                WHERE c.updated_at <= ?
    +                  AND (
    +                      s.conversation_id IS NULL
    +                      OR s.status = 'failed'
    +                      OR s.summary_json IS NULL
    +                      OR s.source_updated_at < c.updated_at
    +                  )
    +                ORDER BY c.updated_at ASC
    +                LIMIT ?
    +                """,
    +                (cutoff, limit),
    +            ).fetchall()
    +        return [
    +            ConversationSummaryCandidate(
    +                conversation_id=row["id"],
    +                user_id=row["user_id"],
    +                updated_at=row["updated_at"],
    +            )
    +            for row in rows
    +        ]
    +
    +    @repository_operation("conversation_summary.get")
    +    def get_conversation_summary(
    +        self,
    +        user_id: int,
    +        conversation_id: str,
    +    ) -> ConversationDigest | None:
    +        with self.connect() as connection:
    +            row = connection.execute(
    +                """
    +                SELECT s.summary_json
    +                FROM conversation_summaries s
    +                JOIN conversations c ON c.id = s.conversation_id
    +                WHERE c.id = ?
    +                  AND c.user_id = ?
    +                  AND s.summary_json IS NOT NULL
    +                """,
    +                (conversation_id, user_id),
    +            ).fetchone()
    +        if row is None:
    +            return None
    +        try:
    +            return ConversationDigest.model_validate_json(row["summary_json"])
    +        except ValueError:
    +            return None
    +
    +    @repository_operation("conversation_summary.save")
    +    def save_conversation_summary(
    +        self,
    +        digest: ConversationDigest,
    +        *,
    +        prompt_version: str,
    +        summarizer_model: str,
    +    ) -> None:
    +        now = utc_now()
    +        with self.connect() as connection:
    +            connection.execute(
    +                """
    +                INSERT INTO conversation_summaries(
    +                    conversation_id,
    +                    status,
    +                    source_updated_at,
    +                    summary_json,
    +                    prompt_version,
    +                    summarizer_model,
    +                    generated_at,
    +                    last_attempt_at,
    +                    error
    +                )
    +                VALUES (?, 'completed', ?, ?, ?, ?, ?, ?, NULL)
    +                ON CONFLICT(conversation_id) DO UPDATE SET
    +                    status = 'completed',
    +                    source_updated_at = excluded.source_updated_at,
    +                    summary_json = excluded.summary_json,
    +                    prompt_version = excluded.prompt_version,
    +                    summarizer_model = excluded.summarizer_model,
    +                    generated_at = excluded.generated_at,
    +                    last_attempt_at = excluded.last_attempt_at,
    +                    error = NULL
    +                """,
    +                (
    +                    digest.conversation_id,
    +                    digest.source_updated_at,
    +                    digest.model_dump_json(),
    +                    prompt_version,
    +                    summarizer_model,
    +                    digest.generated_at,
    +                    now,
    +                ),
    +            )
    +
    +    @repository_operation("conversation_summary.fail")
    +    def record_conversation_summary_failure(
    +        self,
    +        conversation_id: str,
    +        *,
    +        source_updated_at: str,
    +        prompt_version: str,
    +        summarizer_model: str,
    +        error: str,
    +    ) -> None:
    ✓ • 0ms

## Activity

    $ git diff -- agent-service/src/agent_service/api.py agent-service/src/agent_service/agent_runner.py | sed -n '1,360p'
    diff --git a/agent-service/src/agent_service/agent_runner.py b/agent-service/src/agent_service/agent_runner.py
    index 21bd6eb..97be774 100644
    --- a/agent-service/src/agent_service/agent_runner.py
    +++ b/agent-service/src/agent_service/agent_runner.py
    @@ -39,6 +39,7 @@ from .models import (
         BrowseEvent,
         ConversationMessage,
         CreateOrderItem,
    +    FinalRecommendation,
         GoalUnderstandingResult,
         OrderLink,
         OrderRecord,
    @@ -51,6 +52,7 @@ from .models import (
         ProductList,
         RecommendationBatch,
         RecommendationDemand,
    +    RecommendationDecision,
         RecommendationSpec,
         ScoredProduct,
         SemanticRankingResult,
    @@ -148,6 +150,7 @@ class ShoppingAgentContext:
         semantic_ranking: SemanticRankingResult | None = None
         semantic_reranker: SemanticReranker | None = None
         selected_products: dict[str, Product] = field(default_factory=dict)
    +    recommendation_decision: RecommendationDecision | None = None
         created_orders: dict[str, OrderLink] = field(default_factory=dict)
         submitted: bool = False
         tool_trace: list[ToolTrace] = field(default_factory=list)
    @@ -178,6 +181,7 @@ async def commit_scored_products(
         allow_ad_first: bool = True,
     ) -> list[Product]:
         selected: dict[str, Product] = {}
    +    selected_candidates: list[tuple[Product, ScoredProduct]] = []
         for candidate in candidates:
             try:
                 product = await context.mall.get_product(candidate.product.id)
    @@ -200,6 +204,7 @@ async def commit_scored_products(
                     }
                 )
             selected[product.id] = product
    +        selected_candidates.append((product, candidate))
    
         if (
             not allow_ad_first
    @@ -207,12 +212,65 @@ async def commit_scored_products(
             and next(iter(selected.values())).is_ad
         ):
             selected = {}
    +        selected_candidates = []
    
         context.selected_products = selected
    +    context.recommendation_decision = RecommendationDecision(
    +        items=[
    +            FinalRecommendation(
    +                product_id=product.id,
    +                rank=rank,
    +                channel=candidate.channel,
    +                reason=formula_recommendation_reason(candidate),
    +                reason_source="formula_scoring",
    +            )
    +            for rank, (product, candidate) in enumerate(
    +                selected_candidates,
    +                start=1,
    +            )
    +        ]
    +    )
         context.submitted = True
         return list(selected.values())
    
    
    +def formula_recommendation_reason(candidate: ScoredProduct) -> str:
    +    reasons = list(
    +        dict.fromkeys(
    +            evidence.reason.strip()
    +            for evidence in candidate.evidence
    +            if evidence.reason.strip()
    +        )
    +    )
    +    if reasons:
    +        return "；".join(reasons[:3])[:500]
    +    return f"综合评分 {candidate.score:.1f}，满足当前推荐条件"
    +
    +
    +def semantic_recommendation_decision(
    +    ranking: SemanticRankingResult,
    +    selected_products: Sequence[Product],
    +) -> RecommendationDecision:
    +    selected_ids = {product.id for product in selected_products}
    +    ranked_items = [
    +        item for item in ranking.items if item.product_id in selected_ids
    +    ]
    +    return RecommendationDecision(
    +        summary=ranking.summary,
    +        items=[
    +            FinalRecommendation(
    +                product_id=item.product_id,
    +                rank=rank,
    +                channel=item.channel,
    +                reason=item.reason,
    +                reason_source="semantic_reranker",
    +                environmental_fit=item.environmental_fit,
    +            )
    +            for rank, item in enumerate(ranked_items, start=1)
    +        ],
    +    )
    +
    +
     def product_payload(products: Sequence[Product]) -> str:
         return json.dumps(
             [product.model_dump(mode="json") for product in products],
    @@ -1093,6 +1151,7 @@ def create_tools(
             context.remember_products(organic_products)
             context.remember_candidates(ad_candidates)
             context.selected_products.clear()
    +        context.recommendation_decision = None
             context.semantic_ranking = None
             context.submitted = False
    
    @@ -1198,6 +1257,10 @@ def create_tools(
                 allow_ad_first=batch.ad_only,
             )
             context.semantic_ranking = ranking
    +        context.recommendation_decision = semantic_recommendation_decision(
    +            ranking,
    +            selected,
    +        )
             return json.dumps(
                 {
                     "status": "accepted" if selected else "no_match",
    @@ -1532,6 +1595,11 @@ async def stream_agent_reply(
                     if context.recommendation_spec is not None
                     else None
                 ),
    +            "recommendation_decision": (
    +                context.recommendation_decision.model_dump(mode="json")
    +                if context.recommendation_decision is not None
    +                else None
    +            ),
             }
         except PromptLoadError as exc:
             trace_session.finish("failed", exc)
    @@ -1563,6 +1631,11 @@ async def stream_agent_reply(
                     if context.recommendation_spec is not None
                     else None
                 ),
    +            "recommendation_decision": (
    +                context.recommendation_decision.model_dump(mode="json")
    +                if context.recommendation_decision is not None
    +                else None
    +            ),
             }
         except MaxTurnsExceeded:
             trace_session.finish("failed")
    @@ -1600,6 +1673,11 @@ async def stream_agent_reply(
                     if context.recommendation_spec is not None
                     else None
                 ),
    +            "recommendation_decision": (
    +                context.recommendation_decision.model_dump(mode="json")
    +                if context.recommendation_decision is not None
    +                else None
    +            ),
             }
         except (asyncio.CancelledError, GeneratorExit):
             trace_outcome = "cancelled"
    @@ -1640,6 +1718,11 @@ async def stream_agent_reply(
                     if context.recommendation_spec is not None
                     else None
                 ),
    +            "recommendation_decision": (
    +                context.recommendation_decision.model_dump(mode="json")
    +                if context.recommendation_decision is not None
    +                else None
    +            ),
             }
         finally:
             trace_session.finish(trace_outcome)
    diff --git a/agent-service/src/agent_service/api.py b/agent-service/src/agent_service/api.py
    index 50e41c6..27f7f4f 100644
    --- a/agent-service/src/agent_service/api.py
    +++ b/agent-service/src/agent_service/api.py
    @@ -1,18 +1,24 @@
     import asyncio
     import logging
     from collections.abc import AsyncIterator, Sequence
    +from contextlib import asynccontextmanager, suppress
    
     from fastapi import Depends, FastAPI, HTTPException
     from fastapi.responses import StreamingResponse
    
     from .agent_runner import sse_event, stream_agent_reply
     from .chat import compose_reply
    +from .conversation_summary_worker import (
    +    ConversationSummaryWorker,
    +    load_conversation_summary_settings,
    +)
     from .llm_config import LLMConfig, LLMConfigError, load_llm_config
     from .mall_client import CatalogUnavailable, MallClient, get_mall_client
     from .mall_gateway import MallGateway
     from .models import (
         ChatRequest,
         ChatResponse,
    +    ConversationDigest,
         ConversationDetail,
         ConversationList,
         ConversationMessage,
    @@ -20,6 +26,7 @@ from .models import (
         OrderLink,
         PlanState,
         Product,
    +    RecommendationDecision,
         RecommendationSpec,
         StreamChatRequest,
         StoredMessage,
    @@ -31,7 +38,34 @@ from .storage import FIXED_USER_ID, ConversationStore, get_conversation_store
    
     logger = logging.getLogger(__name__)
    
    -app = FastAPI(title="Agent Service", version="0.1.0")
    +
    +@asynccontextmanager
    +async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    +    settings = load_conversation_summary_settings()
    +    task: asyncio.Task[None] | None = None
    +    if settings.enabled:
    +        worker = ConversationSummaryWorker(
    +            get_conversation_store(),
    +            settings=settings,
    +        )
    +        task = asyncio.create_task(
    +            worker.run_forever(),
    +            name="conversation-summary-worker",
    +        )
    +    try:
    +        yield
    +    finally:
    +        if task is not None:
    +            task.cancel()
    +            with suppress(asyncio.CancelledError):
    +                await task
    +
    +
    +app = FastAPI(
    +    title="Agent Service",
    +    version="0.1.0",
    +    lifespan=lifespan,
    +)
    
    
     def to_conversation_messages(
    @@ -95,6 +129,7 @@ async def persisted_agent_stream(
         plan_state: PlanState | None = None
         goal_understanding: GoalUnderstandingResult | None = None
         recommendation_spec: RecommendationSpec | None = None
    +    recommendation_decision: RecommendationDecision | None = None
         created_orders: dict[str, OrderLink] = {}
         persisted = False
         chat_outcome = "failed"
    @@ -124,6 +159,10 @@ async def persisted_agent_stream(
                 metadata["recommendation_spec"] = recommendation_spec.model_dump(
                     mode="json"
                 )
    +        if recommendation_decision is not None:
    +            metadata["recommendation_decision"] = (
    +                recommendation_decision.model_dump(mode="json")
    +            )
             if created_orders:
                 metadata["orders"] = [
                     order.model_dump(mode="json")
    @@ -240,6 +279,13 @@ async def persisted_agent_stream(
                         recommendation_spec = RecommendationSpec.model_validate(
                             spec_payload
                         )
    +                decision_payload = event.get("recommendation_decision")
    +                if isinstance(decision_payload, dict):
    +                    recommendation_decision = (
    +                        RecommendationDecision.model_validate(
    +                            decision_payload
    +                        )
    +                    )
                     store.finish_message(
                         assistant_message_id,
                         "".join(content_parts) or error_message,
    @@ -281,6 +327,13 @@ async def persisted_agent_stream(
                         recommendation_spec = RecommendationSpec.model_validate(
                             spec_payload
                         )
    +                decision_payload = event.get("recommendation_decision")
    +                if isinstance(decision_payload, dict):
    +                    recommendation_decision = (
    +                        RecommendationDecision.model_validate(
    +                            decision_payload
    +                        )
    +                    )
                     store.finish_message(
                         assistant_message_id,
                         "".join(content_parts),
    @@ -404,6 +457,23 @@ def get_conversation(
         return conversation
    
    
    +@app.get(
    +    "/api/conversations/{conversation_id}/summary",
    +    response_model=ConversationDigest,
    +)
    +def get_conversation_summary(
    +    conversation_id: str,
    +    store: ConversationStore = Depends(get_conversation_store),
    +) -> ConversationDigest:
    +    conversation = store.get_conversation(FIXED_USER_ID, conversation_id)
    +    if conversation is None:
    +        raise HTTPException(status_code=404, detail="对话不存在")
    +    summary = store.get_conversation_summary(FIXED_USER_ID, conversation_id)
    +    if summary is None:
    +        raise HTTPException(status_code=404, detail="对话总结尚未生成")
    +    return summary
    +
    +
     @app.post("/api/chat", response_model=ChatResponse)
     async def chat(
         request: ChatRequest,
    ✓ • 0ms

## Activity

    $ uv run pytest -q
    ........................................................................ [ 70%]
    ..............................                                           [100%]
    102 passed in 1.49s
    ✓ • 1.86s

## Assistant

功能链路已完成并通过全部 102 个测试。最后我会做一次差异化检查，确认没有引入用户触发入口、没有 lease/指纹逻辑，并核对定时任务的时间戳筛选和 TODO 都已落在代码中。

## Activity

    $ rg -n "lease|fingerprint|@app.post\(.*summary|TODO\(conversation-summary-freshness\)|Scheduling assumption|source_updated_at < c.updated_at|updated_at <= \?" agent-service/src agent-service/prompts agent-service/tests | sed -n '1,220p'
    agent-service/src/agent_service/storage.py:327:                WHERE c.updated_at <= ?
    agent-service/src/agent_service/storage.py:332:                      OR s.source_updated_at < c.updated_at
    agent-service/src/agent_service/conversation_summary_worker.py:28:# Scheduling assumption:
    agent-service/src/agent_service/conversation_summary_worker.py:29:# This worker does not acquire per-conversation locks or leases. The deployment
    agent-service/src/agent_service/conversation_summary_worker.py:35:# TODO(conversation-summary-freshness):
    ✓ • 0ms

## Activity

    $ git diff --check && uv run python -m compileall -q agent-service/src agent-service/tests
    ✓ • 0ms

## Activity

    $ git status --short
     M agent-service/.env.example
     M agent-service/src/agent_service/agent_runner.py
     M agent-service/src/agent_service/api.py
     M agent-service/src/agent_service/models.py
     M agent-service/src/agent_service/storage.py
     M agent-service/tests/test_agent_api.py
     M agent-service/tests/test_agent_runner.py
    ?? agent-service/prompts/conversation_summary.md
    ?? agent-service/src/agent_service/conversation_summary.py
    ?? agent-service/src/agent_service/conversation_summary_worker.py
    ?? agent-service/tests/test_conversation_summary.py
    ?? agent-service/tests/test_conversation_summary_worker.py
    ✓ • 0ms

## Assistant

已按批准方案完成实施。

主要落地内容：

- [conversation_summary_worker.py](/Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/conversation_summary_worker.py) 实现启动即扫描、之后每小时运行的后台任务；按 `conversation.updated_at` 和 1 小时闲置阈值选择对话。代码中已注释单调度实例假设，未实现 lease、原子领取和输入指纹。
- [conversation_summary.py](/Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/conversation_summary.py) 实现单会话总结、商品关键信息提取、商品反馈、一般偏好和来源校验。
- [conversation_summary.md](/Users/mindeng/workspace/niub-shangcheng/agent-service/prompts/conversation_summary.md) 定义总结模型的提取规则和 JSON 结构。
- `agent_runner` 现在持久化最终推荐商品、终排理由、推荐排序和终排摘要；语义终排理由原样保留。
- `storage` 新增 `conversation_summaries` 表，按 `conversation_id + source_updated_at` 判断复用或更新。
- 总结期间对话继续更新时仍保存旧版本快照，下个满足条件的周期会根据新时间戳重新生成。
- 新增只读接口 `GET /api/conversations/{conversation_id}/summary`，没有用户主动触发生成接口。
- 最新对话缺少总结时回退原始对话细节的 TODO 已记录。
- [.env.example](/Users/mindeng/workspace/niub-shangcheng/agent-service/.env.example) 增加扫描开关、周期、闲置阈值和批量大小配置。

验证结果：

```text
uv run pytest -q
102 passed
```

同时通过 `compileall` 和 `git diff --check`。测试覆盖了闲置筛选、时间戳刷新、同一时间戳跳过、失败重试、总结期间对话更新，以及商品理由和用户证据的来源校验；未调用真实外部 LLM 做在线端到端测试。

## User

好，现在你在这个系统里面增加一个轻量级的 admin 模块，分为前端和后端（admin-web, admin-backend），然后在里面增加一个对话管理的功能，我能通过对话列表查看有哪些对话，并且能查看对话的详情，里面会有这个对话的相应的总结。

## Assistant

我先检查当前仓库的技术栈、服务启动方式和现有前端样式，再确定 `admin-backend` 的代理设计与 `admin-web` 的页面结构，然后直接实现对话列表、详情和总结展示。

## Activity

    $ ls -la && find . -maxdepth 2 -type d | sort | sed -n '1,200p'
    total 10864
    drwxr-xr-x@ 21 mindeng  staff      672 Nov 11 20:48 .
    drwxr-xr-x  23 mindeng  staff      736 Nov  1 20:43 ..
    drwxr-xr-x  12 mindeng  staff      384 Nov 11 20:49 .git
    -rw-r--r--@  1 mindeng  staff      833 Nov  1 21:36 .gitignore
    drwxr-xr-x@  9 mindeng  staff      288 Nov 13 19:54 .idea
    drwxr-xr-x@  6 mindeng  staff      192 Nov  1 20:15 .pytest_cache
    drwxr-xr-x@  8 mindeng  staff      256 Nov  1 20:18 .venv
    -rw-r--r--@  1 mindeng  staff    12109 Nov 11 20:32 README.md
    -rw-r--r--@  1 mindeng  staff     7828 Nov 11 20:32 RECOMMENDATION_E2E_TEST.md
    -rw-r--r--@  1 mindeng  staff     2475 Nov  2 21:11 TODO.md
    drwxr-xr-x@  9 mindeng  staff      288 Nov  1 21:24 agent-service
    -rw-------@  1 mindeng  staff   561558 Nov 11 20:48 codex-session-11.11.md
    -rw-------@  1 mindeng  staff   768160 Nov  2 21:19 codex-session-11.2.md
    -rw-------@  1 mindeng  staff   832983 Nov  3 21:18 codex-session-11.3.md
    -rw-------@  1 mindeng  staff  1159785 Nov  6 19:24 codex-session-11.5.md
    -rw-------@  1 mindeng  staff  1010837 Nov  8 21:06 codex-session-11.8.md
    -rw-------@  1 mindeng  staff   840874 Nov  1 21:29 codex-session-2026.11.1.md
    drwxr-xr-x@  6 mindeng  staff      192 Nov  1 20:13 mall-service
    -rw-r--r--@  1 mindeng  staff      245 Nov  1 20:13 pyproject.toml
    -rw-r--r--@  1 mindeng  staff   338986 Nov  8 20:28 uv.lock
    drwxr-xr-x@ 12 mindeng  staff      384 Nov  1 20:28 web
    .
    ./.git
    ./.git/hooks
    ./.git/info
    ./.git/logs
    ./.git/objects
    ./.git/refs
    ./.idea
    ./.idea/inspectionProfiles
    ./.pytest_cache
    ./.pytest_cache/v
    ./.venv
    ./.venv/bin
    ./.venv/lib
    ./agent-service
    ./agent-service/config
    ./agent-service/data
    ./agent-service/prompts
    ./agent-service/src
    ./agent-service/tests
    ./mall-service
    ./mall-service/src
    ./mall-service/tests
    ./web
    ./web/.next
    ./web/app
    ./web/components
    ./web/node_modules
    ✓ • 0ms

## Activity

    $ rg --files -g 'package.json' -g 'pnpm-workspace.yaml' -g 'vite.config.*' -g 'next.config.*' -g 'go.mod' -g 'pyproject.toml' -g 'README*' -g 'AGENTS.md' | sed -n '1,240p'
    mall-service/pyproject.toml
    README.md
    pyproject.toml
    agent-service/pyproject.toml
    web/next.config.ts
    web/package.json
    ✓ • 0ms

## Activity

    $ git status --short --branch && git log -5 --oneline
    ## main
     M agent-service/.env.example
     M agent-service/src/agent_service/agent_runner.py
     M agent-service/src/agent_service/api.py
     M agent-service/src/agent_service/models.py
     M agent-service/src/agent_service/storage.py
     M agent-service/tests/test_agent_api.py
     M agent-service/tests/test_agent_runner.py
    ?? agent-service/prompts/conversation_summary.md
    ?? agent-service/src/agent_service/conversation_summary.py
    ?? agent-service/src/agent_service/conversation_summary_worker.py
    ?? agent-service/tests/test_conversation_summary.py
    ?? agent-service/tests/test_conversation_summary_worker.py
    0d9ee0b 引入了收集用户需求的步骤
    289c057 初步接入可观测性
    7e60b4a 拆解意图识别 + 目标理解
    f3f4803 引入比较复杂的商品推荐分数计算算法
    8f432e8 完成了商品推荐 + 下单的全流程
    ✓ • 0ms

## Activity

    $ cat web/package.json && cat web/next.config.ts && find web/app web/components -maxdepth 3 -type f | sort | sed -n '1,220p'
    {
      "name": "niub-shangcheng-web",
      "version": "0.1.0",
      "private": true,
      "scripts": {
        "dev": "next dev",
        "build": "next build",
        "start": "next start"
      },
      "dependencies": {
        "next": "^15.5.4",
        "react": "^19.1.0",
        "react-dom": "^19.1.0"
      },
      "devDependencies": {
        "@types/node": "^22.10.0",
        "@types/react": "^19.0.0",
        "@types/react-dom": "^19.0.0",
        "typescript": "^5.7.2"
      }
    }
    import type { NextConfig } from "next";
    
    const nextConfig: NextConfig = {
      poweredByHeader: false,
    };
    
    export default nextConfig;
    web/app/api/chat/route.ts
    web/app/api/conversations/route.ts
    web/app/api/products/route.ts
    web/app/chat/page.tsx
    web/app/globals.css
    web/app/layout.tsx
    web/app/orders/[orderId]/page.tsx
    web/app/page.tsx
    web/app/products/[productId]/page.tsx
    web/app/products/[productId]/product-detail.module.css
    web/components/agent-chat.module.css
    web/components/agent-chat.tsx
    web/components/order-preview.module.css
    web/components/order-preview.tsx
    web/components/storefront.tsx
    ✓ • 0ms

## Activity

    $ sed -n '1,260p' README.md
    # 牛掰商城
    
    项目拆分为三个可独立运行的模块：
    
    ```text
    浏览器
      │
      ▼
    web (Next.js :3000)
      ├── /api/products ──► mall-service (:8001)
      └── /api/chat ──────► agent-service (:8002)
                                  ├── OpenAI Agents SDK
                                  └── HTTP ──► mall-service Mock APIs
    ```
    
    - `mall-service`：商城商品目录，以及浏览、订单、购物车、平台画像、商品推荐和广告的 Mock HTTP API。
    - `agent-service`：基于 OpenAI Agents SDK 的商城导购 Agent，通过工具调用
      `mall-service`，并使用 Agent 本地维护的用户画像。
    - `web`：Next.js 商城页面，浏览器只访问同源的 Next.js API 路由。
    
    ## 启动
    
    首次安装 Python 依赖：
    
    ```bash
    uv sync --all-packages
    ```
    
    分别在三个终端启动服务：
    
    ```bash
    uv run --package mall-service mall-service
    ```
    
    ```bash
    uv run --package agent-service agent-service
    ```
    
    ```bash
    pnpm --dir web install
    pnpm --dir web dev
    ```
    
    打开 <http://localhost:3000>。
    
    ## 大模型配置
    
    复制配置样例并填写 OpenAI-compatible 服务信息：
    
    ```bash
    cp agent-service/config/llm.example.yaml agent-service/config/llm.yaml
    chmod 600 agent-service/config/llm.yaml
    ```
    
    配置文件路径既可以通过 `LLM_CONFIG_FILE` 环境变量提供：
    
    ```bash
    LLM_CONFIG_FILE=/absolute/path/to/llm.yaml \
      uv run --package agent-service agent-service
    ```
    
    也可以通过命令行参数传入：
    
    ```bash
    uv run --package agent-service agent-service \
      --config agent-service/config/llm.yaml
    ```
    
    `agent-service/config/llm.yaml` 已被 Git 忽略，不要把真实 API Key 提交到仓库。
    
    ### 热加载
    
    Python 源码热加载：
    
    ```bash
    uv run --package agent-service agent-service \
      --config agent-service/config/llm.yaml \
      --reload
    ```
    
    `--reload` 使用 Uvicorn 的代码监听机制，修改 `agent-service/src` 下的 Python
    文件后会自动重启进程。
    
    大模型配置不需要重启：服务会在每次模型请求开始时重新读取 YAML 文件，因此
    修改 Base URL、API Key 或模型名称后，下一次对话立即生效。
    
    ## 提示词管理
    
    Agent 提示词保存在：
    
    ```text
    agent-service/prompts/shopping_agent.md
    agent-service/prompts/goal_understanding.md
    agent-service/prompts/recommendation_spec.md
    agent-service/prompts/recommendation_reranker.md
    ```
    
    主 Agent、Goal Understanding Agent 和语义终排 Agent 各自在所属模块中声明
    Prompt 路径，并通过
    [`prompt_loader.py`](agent-service/src/agent_service/prompt_loader.py)
    提供的通用 `load_prompt(path)` 读取文件。YAML 不保存 Prompt 路径。提示词在每次
    请求时重新读取，因此修改 Markdown 后下一轮对话立即生效，不需要重启服务。提示词
    文件限制为 UTF-8、内容非空且不超过 1 MiB。
    
    ## 服务接口
    
    - 商城健康检查：`GET http://localhost:8001/health`
    - 商品列表：`GET http://localhost:8001/api/products`
    - 商品详情：`GET http://localhost:8001/api/products/{product_id}`
    - 浏览记录：`GET http://localhost:8001/api/users/{user_id}/browse-history`
    - 订单记录：`GET http://localhost:8001/api/users/{user_id}/orders`
    - 创建待支付订单：`POST http://localhost:8001/api/users/{user_id}/orders`
    - 订单详情：`GET http://localhost:8001/api/users/{user_id}/orders/{order_id}`
    - 模拟支付：`POST http://localhost:8001/api/users/{user_id}/orders/{order_id}/pay`
    - 购物车：`GET http://localhost:8001/api/users/{user_id}/cart`
    - 平台画像：`GET http://localhost:8001/api/users/{user_id}/platform-profile`
    - 商品推荐：`POST http://localhost:8001/api/recommendations/products`
    - 广告推荐：`POST http://localhost:8001/api/recommendations/ads`
    - SPEC 自然商品检索：`POST http://localhost:8001/api/search/organic`
    - SPEC 广告检索：`POST http://localhost:8001/api/search/ads`
    - Agent 健康检查：`GET http://localhost:8002/health`
    - Agent 对话：`POST http://localhost:8002/api/chat`
    - Agent SSE 多轮对话：`POST http://localhost:8002/api/chat/stream`
    - 历史对话列表：`GET http://localhost:8002/api/conversations`
    - 历史对话详情：`GET http://localhost:8002/api/conversations/{conversation_id}`
    
    对话请求示例：
    
    ```json
    {"message": "推荐几件商品"}
    ```
    
    ## 测试
    
    ```bash
    uv run pytest
    pnpm --dir web build
    ```
    
    `/api/chat/stream` 使用 OpenAI Agents SDK 的 Chat Completions 模型适配器，
    支持自定义 `base_url` 和 API Key。Runner 会自动执行 ReAct 循环：模型自主选择
    用户记录、画像、商品推荐、广告和商品详情工具，然后把工具结果交回模型综合判断。
    `/api/chat` 暂时保留为商城首页使用的简单规则接口。
    
    独立对话页面：<http://localhost:3000/chat>。页面发送当前对话 ID 和新消息，
    后端从 SQLite 加载完整的多轮上下文。
    
    ## 对话持久化
    
    多轮对话保存在 SQLite 中，默认数据库位置为
    `agent-service/data/agent.db`，可通过 `AGENT_DB_PATH` 修改。当前所有对话固定
    归属 `user_id = 1`。
    
    服务保存用户消息、完整回复、失败回复及中断时已经生成的部分内容。模型上下文
    只使用用户消息和状态为 `completed` 的助手消息。`/chat` 页面会展示历史对话
    列表，并允许选择历史会话继续对话。
    
    ## 推荐商品 Agent
    
    当前固定演示用户为 `user_id = 1`。Agent 工具包括：
    
    - `update_plan`：由模型创建或整体替换 Plan 和 Plan State。
    - `understand_goal`：独立 Goal Understanding Action，使用单独 Prompt 和模型
      调用识别多意图、提取槽位，并维护跨轮累计推荐需求。模型自主决定继续询问、
      直接推荐或跳过需求收集，每轮最多提出一个需求问题。
    - `collect_recommendation_context`：为 Recommendation SPEC 收集画像、购物车、
      浏览记录、订单和商品目录，不向主 Agent暴露原始行为数据。
    - `generate_recommendation_spec`：独立 SPEC Action，根据 Goal Understanding 和
      用户行为生成查询变体、硬约束、推断偏好及证据。
    - `search_organic_candidates`：独立自然商品搜索 Action，只使用 SPEC 搜索并缓存
      自然候选，将完整 SPEC 发送给 `mall-service`。
    - `search_ad_candidates`：独立广告搜索 Action，只使用 SPEC 搜索并缓存广告候选。
    - `recommend_products`：读取两路搜索 Action 的缓存结果，结合用户行为按统一公式
      生成自然商品 Top 10 与广告 Top 3，并执行阈值分路。
    - `rerank_recommendations`：独立的语义终排工具，使用单独 Prompt 综合公式分数、
      商品语义和可信环境信息，最多选择两个自然商品和一个广告商品。
    - `get_agent_profile`：读取 Agent 自己维护的用户画像。
    - `get_platform_profile`：读取 `mall-service` 中的大数据/推荐平台画像。
    - `get_browse_history`、`get_order_history` 和 `get_cart`：读取用户行为。
    - `get_product_recommendations`：获取自然商品候选。
    - `get_ad_recommendations`：获取广告候选池，公式评分后由推荐流程截取 Top 3。
    - `search_products` 和 `get_product`：补充搜索及确认权威商品详情。
    - `create_order`：在用户明确确认购买后创建待支付订单。
    - `get_order`：查询当前用户的订单状态，但不能执行支付。
    
    推荐请求使用显式 Plan 驱动。Plan 的步骤、依赖、当前步骤、步骤状态、下一步以及
    是否继续、修订或替换计划全部由模型决定；代码只保存和回传 Plan State，不会自动
    推进步骤或根据工具调用推断状态。上一轮保存的 Plan State 会注入下一轮模型上下文，
    模型仍需自行决定如何使用它。Plan State 通过 SSE 的 `plan_updated` 事件实时更新，
    并随助手消息保存到 SQLite。
    
    推荐需求收集同样由 Goal Understanding 模型推进。模型输出
    `recommendation_requirements`，其中 `status` 为 `collecting`、`ready` 或
    `bypassed`。`collecting` 时模型生成当前唯一要问的 `next_question`，主 Agent
    原样输出并结束本轮；`ready` 时直接进入推荐；用户说“别管那么多，直接推荐”等表达
    时，模型输出 `bypassed`，本轮不得二次确认。代码不设定固定询问顺序，也不生成
    固定问题模板，只校验状态结构、保存累计结果并阻止收集轮提前调用推荐工具。
    
    多意图消息由 `understand_goal` 保留完整意图顺序，但每轮只处理第一个意图。如果
    还有待处理意图，主 Agent 在完成第一个目标后询问用户是否继续；用户确认后，下一轮
    继续处理第一个 `pending_intent`。Goal Understanding 结果会随助手消息保存，用于
    恢复待处理意图。
    
    所有记录和广告 Mock 数据均位于 `mall-service`。自然推荐和广告分别使用统一公式
    评分；广告最高分严格高于自然 Top 10 最低分时，最多三个达标广告与自然候选一起
    进入独立语义终排。最终最多两个自然商品和一个广告，存在自然商品时广告不能排在
    第一位；只有自然候选为空时才允许广告单独出现。广告由服务端添加“广告”标识。
    没有合格商品时，Agent 会建议用户去其他平台购买。SSE 会发送 `tool_started`、
    `tool_completed`、`recommendations`、`delta` 和 `done` 事件。终排完成后，工具
    结果会返回主 Agent，由主 Agent 继续生成最终文字回答，并在文字后展示可点击的
    商品卡片。推荐商品同时作为内部元数据保存，以支持“第一个商品”等后续指代和下单。
    
    推荐召回前会先生成 Recommendation SPEC。搜索与广告搜索共同使用 SPEC 中的硬约束
    和查询变体；SPEC 中的行为推断只指导召回，候选评分仍由统一公式计算，避免同一信号
    重复计权。SPEC 结果会持久化用于诊断。
    
    用户整体跳过需求收集且没有明确商品目标时，SPEC 模型可以选择 `broad` 召回模式。
    该模式仍应用用户明确给出的价格、品类和排除条件，但不强制关键词命中，以便利用画像
    和历史行为完成宽泛推荐。
    
    两个搜索 Action 都把完整 SPEC 发送给 `mall-service`。`mall-service` 目前不连接
    真实 Elasticsearch，而是把 SPEC 转换为模拟 ES DSL，通过日志打印完整查询条件，
    然后使用本地商品目录返回 mock 检索结果。
    
    ## 购买与订单预览
    
    推荐只负责候选商品，不会自动下单。只有用户在对话中明确确认购买并确定购买对象
    后，模型才会调用 `create_order`。服务端重新读取商品权威价格和库存，生成待支付
    订单及商品快照；相同幂等请求返回同一笔订单。
    
    订单创建成功后，SSE 会发送 `order_created`，聊天页面展示“查看订单并支付”入口。
    订单预览页地址为：
    
    ```text
    http://localhost:3000/orders/{order_id}
    ```
    
    预览页展示商品、Mock 收货地址、运费和应付金额。用户点击“模拟支付”后，订单通过
    `pending_payment → paid` 状态变化完成手动支付。重复支付已支付订单不会重复扣减
    库存。当前不接入真实支付渠道，订单存储也是 `mall-service` 进程内的 Mock 仓库。
    本次未接入的复杂购买决策因素记录在根目录的 `TODO.md`。
    
    推荐流程由 `recommend_products` 统一加载画像、行为、商品和广告，阈值命中后再由
    `rerank_recommendations` 完成语义终排。`max_turns` 默认值和最小值为 10，
    最大值为 100；模型请求和单个工具默认超时均为 30 分钟。主 Agent 和终排 Agent
    的运行时输出预算最低为 32768 token，Prompt 文件上限为 1 MiB，单条对话消息上限
    为 100000 字符，避免较小的配置导致工具调用、最终回答或长上下文被截断。
    如果语义终排暂时失败，工具会退回公式排序结果，主 Agent 仍可继续生成回答。
    Agents SDK 的远程 tracing 已关闭，以避免把 DeepSeek 对话发送到 OpenAI tracing
    服务。
    ✓ • 0ms

## Activity

    $ sed -n '1,240p' web/app/page.tsx && sed -n '1,260p' web/app/globals.css
    import { Storefront } from "@/components/storefront";
    
    export default function Home() {
      return <Storefront />;
    }
    :root {
      --ink: #20241d;
      --paper: #f3f0e8;
      --cream: #e8e1d2;
      --green: #244c3a;
      --lime: #d6f06a;
      --orange: #ed7440;
      --line: rgba(32, 36, 29, 0.16);
    }
    
    * {
      box-sizing: border-box;
    }
    
    html {
      scroll-behavior: smooth;
    }
    
    body {
      margin: 0;
      color: var(--ink);
      background: var(--paper);
      font-family:
        "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    }
    
    button,
    input {
      font: inherit;
    }
    
    button,
    a {
      -webkit-tap-highlight-color: transparent;
    }
    
    a {
      color: inherit;
      text-decoration: none;
    }
    
    .nav-shell {
      width: min(1180px, calc(100% - 48px));
      height: 88px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--line);
    }
    
    .brand {
      font-size: 24px;
      font-weight: 900;
      letter-spacing: -1px;
    }
    
    .brand span {
      color: var(--orange);
    }
    
    .nav-links {
      display: flex;
      gap: 36px;
      font-size: 14px;
      font-weight: 600;
    }
    
    .nav-links a:hover {
      color: var(--orange);
    }
    
    .bag-button,
    .product-action {
      border: 0;
      cursor: pointer;
    }
    
    .bag-button {
      padding: 10px 14px;
      border: 1px solid var(--ink);
      background: transparent;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 700;
    }
    
    .bag-button span {
      display: inline-grid;
      width: 20px;
      height: 20px;
      margin-left: 5px;
      place-items: center;
      border-radius: 50%;
      color: white;
      background: var(--orange);
    }
    
    .hero {
      width: min(1180px, calc(100% - 48px));
      min-height: 610px;
      margin: 28px auto 0;
      display: grid;
      grid-template-columns: 1.05fr 0.95fr;
      overflow: hidden;
      border-radius: 6px;
      background: var(--cream);
    }
    
    .hero-copy {
      padding: 90px 70px;
    }
    
    .eyebrow {
      margin: 0 0 24px;
      color: var(--green);
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 2.2px;
    }
    
    .hero h1 {
      margin: 0;
      font-family: "Songti SC", "STSong", serif;
      font-size: clamp(48px, 6vw, 82px);
      font-weight: 900;
      line-height: 1.08;
      letter-spacing: -4px;
    }
    
    .hero h1 span,
    .guide-section h2 span {
      color: var(--orange);
    }
    
    .hero-description {
      max-width: 430px;
      margin: 32px 0;
      color: #53594f;
      font-size: 16px;
      line-height: 1.8;
    }
    
    .primary-link {
      display: inline-block;
      padding: 16px 23px;
      color: white;
      background: var(--green);
      border-radius: 3px;
      font-size: 14px;
      font-weight: 700;
      transition: transform 160ms ease;
    }
    
    .primary-link:hover {
      transform: translateY(-2px);
    }
    
    .hero-art {
      position: relative;
      min-height: 520px;
      overflow: hidden;
      background: var(--green);
    }
    
    .hero-art .sun {
      position: absolute;
      width: 390px;
      height: 390px;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -52%);
      border-radius: 50%;
      background: var(--lime);
    }
    
    .hero-art .object {
      position: absolute;
      box-shadow: 0 24px 60px rgba(0, 0, 0, 0.2);
    }
    
    .object-one {
      width: 200px;
      height: 270px;
      left: 18%;
      bottom: 12%;
      display: grid;
      place-items: center;
      color: var(--lime);
      background: var(--orange);
      border-radius: 100px 100px 18px 18px;
      font-family: "Songti SC", serif;
      font-size: 78px;
      font-weight: 900;
      transform: rotate(-12deg);
    }
    
    .object-two {
      width: 145px;
      height: 210px;
      right: 12%;
      bottom: 18%;
      border: 15px solid var(--paper);
      background: rgba(255, 255, 255, 0.08);
      border-radius: 70px 70px 8px 8px;
      transform: rotate(16deg);
    }
    
    .hero-art p {
      position: absolute;
      right: 32px;
      bottom: 20px;
      margin: 0;
      color: var(--cream);
      font-size: 10px;
      font-weight: 800;
      line-height: 1.6;
      letter-spacing: 2px;
      text-align: right;
    }
    
    .goods-section,
    .guide-section {
      width: min(1180px, calc(100% - 48px));
      margin: 0 auto;
      padding: 110px 0;
    }
    
    .section-heading {
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      margin-bottom: 46px;
    }
    
    .section-heading .eyebrow,
    .guide-intro .eyebrow {
      margin-bottom: 12px;
    }
    
    .section-heading h2,
    .guide-section h2 {
      margin: 0;
      font-family: "Songti SC", "STSong", serif;
      font-size: clamp(40px, 5vw, 64px);
      letter-spacing: -3px;
    }
    
    .section-heading > p {
      color: #6d7369;
      font-size: 13px;
    }
    
    .status-card {
      padding: 50px;
      text-align: center;
      border: 1px dashed var(--line);
    }
    
    .product-grid {
    ✓ • 0ms

## Activity

    $ cat .gitignore
    # Environment and secrets
    .env
    .env.*
    *.local
    *.pem
    *.key
    *.p12
    *.pfx
    secrets/
    !.env.example
    !**/.env.example
    
    # Local model configuration
    agent-service/config/llm.yaml
    agent-service/config/*.local.yaml
    agent-service/config/*.secret.yaml
    !agent-service/config/llm.example.yaml
    
    # Generated conversation data
    agent-service/data/
    *.db
    *.db-shm
    *.db-wal
    *.sqlite
    *.sqlite3
    
    # Python
    .venv/
    venv/
    __pycache__/
    *.py[cod]
    *.so
    .pytest_cache/
    .mypy_cache/
    .ruff_cache/
    .coverage
    htmlcov/
    dist/
    build/
    *.egg-info/
    
    # Node.js and Next.js
    node_modules/
    .pnpm-store/
    .next/
    out/
    coverage/
    *.tsbuildinfo
    .turbo/
    
    # IDE and operating system
    .idea/
    .vscode/
    .DS_Store
    Thumbs.db
    
    # Logs and temporary files
    *.log
    logs/
    tmp/
    .tmp/
    
    # Agent session exports and packaged artifacts
    # codex-session-*.md
    .codex/
    exports/
    artifacts/
    *.tar
    *.tar.gz
    *.zip
    ✓ • 0ms

## Activity

    $ find web -maxdepth 1 -type f -print -exec basename {} \; | sed -n '1,100p' && cat web/tsconfig.json 2>/dev/null && cat web/app/layout.tsx && sed -n '1,220p' web/app/api/conversations/route.ts
    web/pnpm-lock.yaml
    pnpm-lock.yaml
    web/next-env.d.ts
    next-env.d.ts
    web/package.json
    package.json
    web/tsconfig.json
    tsconfig.json
    web/.env.example
    .env.example
    web/next.config.ts
    next.config.ts
    {
      "compilerOptions": {
        "target": "ES2017",
        "lib": ["dom", "dom.iterable", "esnext"],
        "allowJs": false,
        "skipLibCheck": true,
        "strict": true,
        "noEmit": true,
        "esModuleInterop": true,
        "module": "esnext",
        "moduleResolution": "bundler",
        "resolveJsonModule": true,
        "isolatedModules": true,
        "jsx": "preserve",
        "incremental": true,
        "plugins": [{ "name": "next" }],
        "paths": {
          "@/*": ["./*"]
        }
      },
      "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
      "exclude": ["node_modules"]
    }
    import type { Metadata } from "next";
    
    import "./globals.css";
    
    export const metadata: Metadata = {
      title: "牛掰商城",
      description: "有温度的日常好物商城",
    };
    
    export default function RootLayout({
      children,
    }: Readonly<{
      children: React.ReactNode;
    }>) {
      return (
        <html lang="zh-CN">
          <body>{children}</body>
        </html>
      );
    }
    import { NextResponse } from "next/server";
    
    const agentServiceUrl =
      process.env.AGENT_SERVICE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8002";
    
    export const dynamic = "force-dynamic";
    
    export async function GET() {
      try {
        const response = await fetch(`${agentServiceUrl}/api/conversations`, {
          cache: "no-store",
        });
        const body: unknown = await response.json();
        return NextResponse.json(body, { status: response.status });
      } catch {
        return NextResponse.json(
          { detail: "历史对话服务暂时不可用" },
          { status: 502 },
        );
      }
    }
    ✓ • 0ms

## Activity

    $ cat mall-service/pyproject.toml && find mall-service/src -maxdepth 3 -type f | sort | sed -n '1,100p' && sed -n '1,120p' mall-service/src/mall_service/main.py
    [project]
    name = "mall-service"
    version = "0.1.0"
    description = "Mall catalog HTTP service"
    requires-python = ">=3.11"
    dependencies = [
        "fastapi>=0.115,<1",
        "uvicorn>=0.34,<1",
    ]
    
    [project.scripts]
    mall-service = "mall_service.main:run"
    
    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"
    
    [tool.hatch.build.targets.wheel]
    packages = ["src/mall_service"]
    mall-service/src/mall_service/__init__.py
    mall-service/src/mall_service/__pycache__/__init__.cpython-312.pyc
    mall-service/src/mall_service/__pycache__/api.cpython-312.pyc
    mall-service/src/mall_service/__pycache__/catalog.cpython-312.pyc
    mall-service/src/mall_service/__pycache__/main.cpython-312.pyc
    mall-service/src/mall_service/__pycache__/mock_data.cpython-312.pyc
    mall-service/src/mall_service/__pycache__/models.cpython-312.pyc
    mall-service/src/mall_service/__pycache__/orders.cpython-312.pyc
    mall-service/src/mall_service/__pycache__/recommendations.cpython-312.pyc
    mall-service/src/mall_service/__pycache__/search.cpython-312.pyc
    mall-service/src/mall_service/api.py
    mall-service/src/mall_service/catalog.py
    mall-service/src/mall_service/main.py
    mall-service/src/mall_service/mock_data.py
    mall-service/src/mall_service/models.py
    mall-service/src/mall_service/orders.py
    mall-service/src/mall_service/recommendations.py
    mall-service/src/mall_service/search.py
    import os
    
    import uvicorn
    
    
    def run() -> None:
        uvicorn.run(
            "mall_service.api:app",
            host=os.getenv("MALL_SERVICE_HOST", "0.0.0.0"),
            port=int(os.getenv("MALL_SERVICE_PORT", "8001")),
        )
    ✓ • 0ms

## Activity

    $ sed -n '1,200p' web/components/agent-chat.module.css
    .page {
      --chat-ink: #17221a;
      --chat-paper: #f4f1e8;
      --chat-green: #1d4936;
      --chat-lime: #d6f06a;
      --chat-orange: #ef7643;
      --chat-line: rgba(23, 34, 26, 0.14);
      min-height: 100vh;
      color: var(--chat-ink);
      background:
        radial-gradient(circle at 75% -10%, rgba(214, 240, 106, 0.3), transparent 26%),
        var(--chat-paper);
    }
    
    .topbar {
      width: min(1420px, calc(100% - 56px));
      height: 82px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--chat-line);
    }
    
    .brand {
      color: var(--chat-ink);
      font-size: 23px;
      font-weight: 900;
      letter-spacing: -1px;
      text-decoration: none;
    }
    
    .brand span {
      color: var(--chat-orange);
    }
    
    .topbarActions {
      display: flex;
      align-items: center;
      gap: 28px;
    }
    
    .connection {
      display: flex;
      align-items: center;
      gap: 9px;
      color: #6b7169;
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 1.4px;
    }
    
    .connection i {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #47a960;
      box-shadow: 0 0 0 4px rgba(71, 169, 96, 0.13);
    }
    
    .backLink {
      padding: 9px 15px;
      color: var(--chat-ink);
      border: 1px solid var(--chat-line);
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      text-decoration: none;
      transition:
        border-color 160ms ease,
        color 160ms ease;
    }
    
    .backLink:hover {
      color: var(--chat-orange);
      border-color: var(--chat-orange);
    }
    
    .workspace {
      width: min(1420px, calc(100% - 56px));
      min-height: calc(100vh - 126px);
      margin: 22px auto;
      display: grid;
      grid-template-columns: 340px minmax(0, 1fr);
      overflow: hidden;
      border: 1px solid var(--chat-line);
      background: #fffdf8;
      box-shadow: 0 24px 70px rgba(28, 50, 36, 0.08);
    }
    
    .sidebar {
      position: relative;
      padding: 52px 38px 34px;
      display: flex;
      flex-direction: column;
      justify-content: flex-start;
      gap: 30px;
      color: white;
      background:
        linear-gradient(rgba(29, 73, 54, 0.95), rgba(29, 73, 54, 0.98)),
        repeating-linear-gradient(
          -45deg,
          transparent,
          transparent 8px,
          rgba(255, 255, 255, 0.08) 8px,
          rgba(255, 255, 255, 0.08) 9px
        );
    }
    
    .sidebar::after {
      content: "AI";
      position: absolute;
      right: -16px;
      top: 38%;
      color: rgba(214, 240, 106, 0.07);
      font-family: Georgia, serif;
      font-size: 190px;
      font-weight: 900;
      line-height: 1;
      pointer-events: none;
    }
    
    .kicker {
      position: relative;
      z-index: 1;
      margin: 0 0 28px;
      color: var(--chat-lime);
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 2.1px;
    }
    
    .sidebar h1 {
      position: relative;
      z-index: 1;
      margin: 0;
      font-family: "Songti SC", "STSong", serif;
      font-size: 54px;
      line-height: 1.08;
      letter-spacing: -3px;
    }
    
    .sidebarHeading {
      position: relative;
      z-index: 1;
      flex: 0 0 auto;
    }
    
    .intro {
      position: relative;
      z-index: 1;
      max-width: 250px;
      margin: 26px 0 0;
      color: rgba(255, 255, 255, 0.62);
      font-size: 13px;
      line-height: 1.8;
    }
    
    .history {
      position: relative;
      z-index: 1;
      min-height: 0;
      flex: 1;
      display: flex;
      flex-direction: column;
    }
    
    .historyHeading {
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    
    .historyHeading p {
      margin: 0;
      color: rgba(255, 255, 255, 0.45);
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 1.4px;
    }
    
    .historyHeading span {
      min-width: 22px;
      padding: 3px 7px;
      color: var(--chat-green);
      background: var(--chat-lime);
      border-radius: 999px;
      font-size: 9px;
      font-weight: 900;
      text-align: center;
    }
    
    .historyList {
      min-height: 0;
      max-height: 260px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      overflow-y: auto;
    ✓ • 0ms

## Activity

    $ node -v && pnpm -v && ls web/node_modules/.bin/next 2>/dev/null && ls node_modules/.bin 2>/dev/null | sed -n '1,30p'
    v24.18.0
    10.29.3
    web/node_modules/.bin/next
    ✓ • 21ms

## Assistant

现有商城前端使用 Next.js，后端是 FastAPI。我会让 `admin-backend` 作为内部聚合层代理 `agent-service`，`admin-web` 只访问同源的内部 API；这样对话列表和详情不需要复制业务表结构，后续也能在 admin 后端继续增加审计或权限能力。

## Activity

    file changes: Completed · 6 changes
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-backend/.env.example
    ADMIN_BACKEND_HOST=127.0.0.1
    ADMIN_BACKEND_PORT=8003
    AGENT_SERVICE_URL=http://127.0.0.1:8002
    AGENT_SERVICE_TIMEOUT_SECONDS=10
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-backend/pyproject.toml
    [project]
    name = "admin-backend"
    version = "0.1.0"
    description = "Internal admin API for niub-shangcheng"
    requires-python = ">=3.11"
    dependencies = [
        "fastapi>=0.115,<1",
        "httpx>=0.27,<1",
        "uvicorn>=0.34,<1",
    ]
    
    [project.scripts]
    admin-backend = "admin_backend.main:run"
    
    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"
    
    [tool.hatch.build.targets.wheel]
    packages = ["src/admin_backend"]
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-backend/src/admin_backend/__init__.py
    """Internal admin backend."""
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-backend/src/admin_backend/agent_client.py
    import httpx
    
    
    class AgentServiceError(Exception):
        """Raised when the agent service cannot provide the requested data."""
    
    
    class AgentServiceClient:
        def __init__(
            self,
            *,
            base_url: str,
            timeout_seconds: float = 10.0,
            transport: httpx.AsyncBaseTransport | None = None,
        ) -> None:
            self.base_url = base_url.rstrip("/")
            self.timeout_seconds = timeout_seconds
            self.transport = transport
    
        async def _request(
            self,
            method: str,
            path: str,
        ) -> tuple[int, object]:
            try:
                async with httpx.AsyncClient(
                    base_url=self.base_url,
                    timeout=self.timeout_seconds,
                    transport=self.transport,
                ) as client:
                    response = await client.request(method, path)
            except httpx.RequestError as exc:
                raise AgentServiceError(
                    f"agent service request failed: {type(exc).__name__}: {exc}"
                ) from exc
            try:
                payload: object = response.json()
            except ValueError:
                payload = {"detail": "agent service returned a non-JSON response"}
            return response.status_code, payload
    
        async def list_conversations(self) -> object:
            status, payload = await self._request("GET", "/api/conversations")
            if status != 200:
                raise AgentServiceError(
                    f"agent service conversation list returned HTTP {status}"
                )
            return payload
    
        async def get_conversation(self, conversation_id: str) -> object | None:
            status, payload = await self._request(
                "GET",
                f"/api/conversations/{conversation_id}",
            )
            if status == 404:
                return None
            if status != 200:
                raise AgentServiceError(
                    f"agent service conversation detail returned HTTP {status}"
                )
            return payload
    
        async def get_conversation_summary(
            self,
            conversation_id: str,
        ) -> object | None:
            status, payload = await self._request(
                "GET",
                f"/api/conversations/{conversation_id}/summary",
            )
            if status == 404:
                return None
            if status != 200:
                raise AgentServiceError(
                    f"agent service conversation summary returned HTTP {status}"
                )
            return payload
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-backend/src/admin_backend/api.py
    import asyncio
    import os
    
    from fastapi import Depends, FastAPI, HTTPException
    
    from .agent_client import AgentServiceClient, AgentServiceError
    
    
    app = FastAPI(title="Niub Admin Backend", version="0.1.0")
    
    
    def get_agent_service_client() -> AgentServiceClient:
        return AgentServiceClient(
            base_url=os.getenv(
                "AGENT_SERVICE_URL",
                "http://127.0.0.1:8002",
            ),
            timeout_seconds=float(os.getenv("AGENT_SERVICE_TIMEOUT_SECONDS", "10")),
        )
    
    
    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "admin-backend"}
    
    
    @app.get("/api/conversations")
    async def list_conversations(
        client: AgentServiceClient = Depends(get_agent_service_client),
    ) -> object:
        try:
            return await client.list_conversations()
        except AgentServiceError as exc:
            raise HTTPException(
                status_code=502,
                detail="对话服务暂时不可用",
            ) from exc
    
    
    @app.get("/api/conversations/{conversation_id}")
    async def get_conversation(
        conversation_id: str,
        client: AgentServiceClient = Depends(get_agent_service_client),
    ) -> dict[str, object | None]:
        try:
            conversation, summary = await asyncio.gather(
                client.get_conversation(conversation_id),
                client.get_conversation_summary(conversation_id),
            )
        except AgentServiceError as exc:
            raise HTTPException(
                status_code=502,
                detail="对话服务暂时不可用",
            ) from exc
        if conversation is None:
            raise HTTPException(status_code=404, detail="对话不存在")
        return {
            "conversation": conversation,
            "summary": summary,
        }
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-backend/src/admin_backend/main.py
    import os
    
    import uvicorn
    
    
    def run() -> None:
        uvicorn.run(
            "admin_backend.api:app",
            host=os.getenv("ADMIN_BACKEND_HOST", "127.0.0.1"),
            port=int(os.getenv("ADMIN_BACKEND_PORT", "8003")),
        )

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/pyproject.toml
    @@ -1,3 +1,3 @@
     [tool.uv.workspace]
    -members = ["agent-service", "mall-service"]
    +members = ["agent-service", "mall-service", "admin-backend"]
     
    @@ -7,3 +7,7 @@
     [tool.pytest.ini_options]
    -pythonpath = ["agent-service/src", "mall-service/src"]
    -testpaths = ["agent-service/tests", "mall-service/tests"]
    +pythonpath = ["agent-service/src", "mall-service/src", "admin-backend/src"]
    +testpaths = [
    +    "agent-service/tests",
    +    "mall-service/tests",
    +    "admin-backend/tests",
    +]

## Activity

    file changes: Completed · 1 changes
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-backend/tests/test_admin_api.py
    import httpx
    from fastapi.testclient import TestClient
    
    from admin_backend.agent_client import AgentServiceClient
    from admin_backend.api import app, get_agent_service_client
    
    
    client = TestClient(app)
    
    CONVERSATION_LIST = {
        "items": [
            {
                "id": "conversation-1",
                "title": "推荐通勤包",
                "message_count": 6,
                "created_at": "2026-11-13T01:00:00.000+00:00",
                "updated_at": "2026-11-13T01:10:00.000+00:00",
            }
        ]
    }
    
    CONVERSATION_DETAIL = {
        "id": "conversation-1",
        "title": "推荐通勤包",
        "message_count": 2,
        "created_at": "2026-11-13T01:00:00.000+00:00",
        "updated_at": "2026-11-13T01:10:00.000+00:00",
        "messages": [
            {
                "id": "message-1",
                "role": "user",
                "content": "推荐一个通勤包",
                "status": "completed",
                "created_at": "2026-11-13T01:00:00.000+00:00",
            },
            {
                "id": "message-2",
                "role": "assistant",
                "content": "推荐这款轻量通勤包。",
                "status": "completed",
                "created_at": "2026-11-13T01:01:00.000+00:00",
            },
        ],
    }
    
    CONVERSATION_SUMMARY = {
        "conversation_id": "conversation-1",
        "source_updated_at": "2026-11-13T01:10:00.000+00:00",
        "summary": "用户寻找适合通勤的包。",
        "generated_at": "2026-11-13T02:10:00.000+00:00",
    }
    
    
    def _override_client(transport: httpx.AsyncBaseTransport) -> AgentServiceClient:
        return AgentServiceClient(
            base_url="http://agent.test",
            transport=transport,
        )
    
    
    def test_health() -> None:
        response = client.get("/health")
    
        assert response.status_code == 200
        assert response.json()["service"] == "admin-backend"
    
    
    def test_list_conversations_proxies_agent_service() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/conversations"
            return httpx.Response(200, json=CONVERSATION_LIST)
    
        app.dependency_overrides[get_agent_service_client] = lambda: (
            _override_client(httpx.MockTransport(handler))
        )
        try:
            response = client.get("/api/conversations")
        finally:
            app.dependency_overrides.clear()
    
        assert response.status_code == 200
        assert response.json()["items"][0]["id"] == "conversation-1"
    
    
    def test_conversation_detail_includes_summary() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/summary"):
                return httpx.Response(200, json=CONVERSATION_SUMMARY)
            return httpx.Response(200, json=CONVERSATION_DETAIL)
    
        app.dependency_overrides[get_agent_service_client] = lambda: (
            _override_client(httpx.MockTransport(handler))
        )
        try:
            response = client.get("/api/conversations/conversation-1")
        finally:
            app.dependency_overrides.clear()
    
        assert response.status_code == 200
        assert response.json()["conversation"]["title"] == "推荐通勤包"
        assert response.json()["summary"]["summary"] == "用户寻找适合通勤的包。"
    
    
    def test_conversation_detail_allows_missing_summary() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/summary"):
                return httpx.Response(404, json={"detail": "总结尚未生成"})
            return httpx.Response(200, json=CONVERSATION_DETAIL)
    
        app.dependency_overrides[get_agent_service_client] = lambda: (
            _override_client(httpx.MockTransport(handler))
        )
        try:
            response = client.get("/api/conversations/conversation-1")
        finally:
            app.dependency_overrides.clear()
    
        assert response.status_code == 200
        assert response.json()["summary"] is None
    
    
    def test_unknown_conversation_is_not_found() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"detail": "对话不存在"})
    
        app.dependency_overrides[get_agent_service_client] = lambda: (
            _override_client(httpx.MockTransport(handler))
        )
        try:
            response = client.get("/api/conversations/missing")
        finally:
            app.dependency_overrides.clear()
    
        assert response.status_code == 404
    
    
    def test_agent_service_failure_returns_bad_gateway() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)
    
        app.dependency_overrides[get_agent_service_client] = lambda: (
            _override_client(httpx.MockTransport(handler))
        )
        try:
            response = client.get("/api/conversations")
        finally:
            app.dependency_overrides.clear()
    
        assert response.status_code == 502

## Activity

    file changes: Completed · 10 changes
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-web/.env.example
    ADMIN_BACKEND_URL=http://127.0.0.1:8003
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-web/app/layout.tsx
    import type { Metadata } from "next";
    import Link from "next/link";
    
    import "./globals.css";
    
    export const metadata: Metadata = {
      title: "牛掰商城 · 运营后台",
      description: "牛掰商城内部运营管理后台",
    };
    
    export default function RootLayout({
      children,
    }: Readonly<{
      children: React.ReactNode;
    }>) {
      return (
        <html lang="zh-CN">
          <body>
            <header className="admin-header">
              <div className="admin-header__inner">
                <Link className="admin-brand" href="/conversations">
                  <span>NIUB</span>
                  <strong>运营后台</strong>
                </Link>
                <nav aria-label="后台导航">
                  <Link href="/conversations">对话管理</Link>
                </nav>
                <div className="environment-pill">
                  <i />
                  INTERNAL
                </div>
              </div>
            </header>
            <main className="admin-main">{children}</main>
          </body>
        </html>
      );
    }
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-web/app/not-found.tsx
    import Link from "next/link";
    
    export default function NotFound() {
      return (
        <section className="empty-state">
          <p className="eyebrow">404 / NOT FOUND</p>
          <h1>没有找到这个对话</h1>
          <p>对话可能已被删除，或者链接中的 ID 不正确。</p>
          <Link className="primary-button" href="/conversations">
            返回对话列表
          </Link>
        </section>
      );
    }
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-web/app/page.tsx
    import { redirect } from "next/navigation";
    
    export default function HomePage() {
      redirect("/conversations");
    }
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-web/lib/admin-api.ts
    import type {
      ConversationAdminDetail,
      ConversationListPayload,
    } from "@/lib/types";
    
    const adminBackendUrl =
      process.env.ADMIN_BACKEND_URL?.replace(/\/$/, "") ??
      "http://127.0.0.1:8003";
    
    export class AdminApiError extends Error {
      constructor(
        message: string,
        readonly status: number,
      ) {
        super(message);
        this.name = "AdminApiError";
      }
    }
    
    async function adminFetch<T>(path: string): Promise<T> {
      const response = await fetch(`${adminBackendUrl}${path}`, {
        cache: "no-store",
      });
      const payload = (await response.json().catch(() => null)) as
        | { detail?: unknown }
        | T
        | null;
      if (!response.ok) {
        const detail =
          payload &&
          typeof payload === "object" &&
          "detail" in payload &&
          typeof payload.detail === "string"
            ? payload.detail
            : "管理服务返回了未知错误";
        throw new AdminApiError(detail, response.status);
      }
      return payload as T;
    }
    
    export async function listConversations(): Promise<ConversationListPayload> {
      return adminFetch<ConversationListPayload>("/api/conversations");
    }
    
    export async function getConversation(
      conversationId: string,
    ): Promise<ConversationAdminDetail | null> {
      try {
        return await adminFetch<ConversationAdminDetail>(
          `/api/conversations/${encodeURIComponent(conversationId)}`,
        );
      } catch (error) {
        if (error instanceof AdminApiError && error.status === 404) {
          return null;
        }
        throw error;
      }
    }
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-web/lib/types.ts
    export interface ConversationSummaryItem {
      id: string;
      title: string;
      message_count: number;
      created_at: string;
      updated_at: string;
    }
    
    export interface ConversationListPayload {
      items: ConversationSummaryItem[];
    }
    
    export interface Product {
      id: string;
      name: string;
      description: string;
      price_cents: number;
      category: string;
      badge?: string | null;
      tags?: string[];
      image_url?: string | null;
      is_ad?: boolean;
      ad_label?: string | null;
    }
    
    export interface StoredMessage {
      id: string;
      role: "user" | "assistant";
      content: string;
      status: "streaming" | "completed" | "failed";
      created_at: string;
      recommendations?: Product[];
      orders?: Array<{
        order_id: string;
        status: string;
        total_cents: number;
        preview_path: string;
      }>;
    }
    
    export interface ConversationDetail {
      id: string;
      title: string;
      message_count: number;
      created_at: string;
      updated_at: string;
      messages: StoredMessage[];
    }
    
    export interface ProductKeyInformation {
      name: string;
      value: string;
      source_field: string;
      source_text: string;
    }
    
    export interface RecommendedProductSummary {
      product: Product;
      key_information: ProductKeyInformation[];
      reason: string | null;
      reason_source: string;
      environmental_fit?: string | null;
    }
    
    export interface RecommendationRoundSummary {
      assistant_message_id: string;
      user_request: string;
      ranking_summary: string;
      products: RecommendedProductSummary[];
    }
    
    export interface ProductFeedback {
      product_id: string;
      overall: "positive" | "negative" | "neutral" | "mixed" | "unclear";
      aspects: Array<{
        name: string;
        value?: string | null;
        polarity: "positive" | "negative" | "neutral" | "uncertain";
      }>;
      evidence: Array<{
        message_id: string;
        quote: string;
      }>;
      confidence: number;
    }
    
    export interface GeneralPreference {
      dimension: string;
      value: string;
      polarity: "prefer" | "avoid";
      evidence: Array<{
        message_id: string;
        quote: string;
      }>;
      confidence: number;
    }
    
    export interface ConversationDigest {
      conversation_id: string;
      source_updated_at: string;
      summary: string;
      user_goals?: string[];
      explicit_constraints?: string[];
      recommendation_rounds?: RecommendationRoundSummary[];
      product_feedback?: ProductFeedback[];
      general_preferences?: GeneralPreference[];
      unresolved_items?: string[];
      source_message_ids?: string[];
      generated_at: string;
    }
    
    export interface ConversationAdminDetail {
      conversation: ConversationDetail;
      summary: ConversationDigest | null;
    }
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-web/next-env.d.ts
    /// <reference types="next" />
    /// <reference types="next/image-types/global" />
    
    // This file is generated and managed by Next.js.
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-web/next.config.ts
    import type { NextConfig } from "next";
    
    const nextConfig: NextConfig = {
      poweredByHeader: false,
    };
    
    export default nextConfig;
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-web/package.json
    {
      "name": "niub-admin-web",
      "version": "0.1.0",
      "private": true,
      "scripts": {
        "dev": "next dev -p 3001",
        "build": "next build",
        "start": "next start -p 3001"
      },
      "dependencies": {
        "next": "^15.5.4",
        "react": "^19.1.0",
        "react-dom": "^19.1.0"
      },
      "devDependencies": {
        "@types/node": "^22.10.0",
        "@types/react": "^19.0.0",
        "@types/react-dom": "^19.0.0",
        "typescript": "^5.7.2"
      }
    }
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-web/tsconfig.json
    {
      "compilerOptions": {
        "target": "ES2017",
        "lib": ["dom", "dom.iterable", "esnext"],
        "allowJs": false,
        "skipLibCheck": true,
        "strict": true,
        "noEmit": true,
        "esModuleInterop": true,
        "module": "esnext",
        "moduleResolution": "bundler",
        "resolveJsonModule": true,
        "isolatedModules": true,
        "jsx": "preserve",
        "incremental": true,
        "plugins": [{ "name": "next" }],
        "paths": {
          "@/*": ["./*"]
        }
      },
      "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
      "exclude": ["node_modules"]
    }

## Activity

    file changes: Completed · 2 changes
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-web/app/conversations/page.tsx
    import Link from "next/link";
    
    import { AdminApiError, listConversations } from "@/lib/admin-api";
    import { formatDate } from "@/lib/format";
    
    export const dynamic = "force-dynamic";
    
    export default async function ConversationsPage() {
      let conversations;
      try {
        conversations = await listConversations();
      } catch (error) {
        const message =
          error instanceof AdminApiError
            ? error.message
            : "无法连接管理后端，请确认服务已经启动。";
        return (
          <section className="empty-state">
            <p className="eyebrow">SERVICE UNAVAILABLE</p>
            <h1>对话服务暂时不可用</h1>
            <p>{message}</p>
            <code>ADMIN_BACKEND_URL=http://127.0.0.1:8003</code>
          </section>
        );
      }
    
      const totalMessages = conversations.items.reduce(
        (total, conversation) => total + conversation.message_count,
        0,
      );
    
      return (
        <div className="page-stack">
          <section className="page-heading">
            <div>
              <p className="eyebrow">CONVERSATION OPERATIONS</p>
              <h1>对话管理</h1>
              <p className="page-description">
                查看商城 Agent 的历史会话、完整消息和定时生成的对话总结。
              </p>
            </div>
            <div className="metric-grid">
              <div className="metric-card">
                <span>对话总数</span>
                <strong>{conversations.items.length}</strong>
              </div>
              <div className="metric-card">
                <span>消息总数</span>
                <strong>{totalMessages}</strong>
              </div>
            </div>
          </section>
    
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>全部对话</h2>
                <p>按最近更新时间倒序排列</p>
              </div>
              <span className="count-badge">
                {conversations.items.length} 条记录
              </span>
            </div>
    
            {conversations.items.length === 0 ? (
              <div className="empty-row">暂时还没有对话记录。</div>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>对话</th>
                      <th>消息数</th>
                      <th>创建时间</th>
                      <th>最近更新</th>
                      <th aria-label="操作" />
                    </tr>
                  </thead>
                  <tbody>
                    {conversations.items.map((conversation) => (
                      <tr key={conversation.id}>
                        <td>
                          <Link
                            className="conversation-title"
                            href={`/conversations/${conversation.id}`}
                          >
                            {conversation.title}
                          </Link>
                          <span className="mono-id">{conversation.id}</span>
                        </td>
                        <td>{conversation.message_count}</td>
                        <td>{formatDate(conversation.created_at)}</td>
                        <td>{formatDate(conversation.updated_at)}</td>
                        <td className="action-cell">
                          <Link
                            className="text-link"
                            href={`/conversations/${conversation.id}`}
                          >
                            查看详情
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      );
    }
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-web/lib/format.ts
    export function formatDate(value: string): string {
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) {
        return value;
      }
      return new Intl.DateTimeFormat("zh-CN", {
        timeZone: "Asia/Shanghai",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      }).format(date);
    }
    
    export function formatFullDate(value: string): string {
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) {
        return value;
      }
      return new Intl.DateTimeFormat("zh-CN", {
        timeZone: "Asia/Shanghai",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      }).format(date);
    }
    
    export function formatMoney(value: number): string {
      return new Intl.NumberFormat("zh-CN", {
        style: "currency",
        currency: "CNY",
      }).format(value / 100);
    }

## Activity

    file changes: Completed · 1 changes
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-web/app/conversations/[conversationId]/page.tsx
    import Link from "next/link";
    import { notFound } from "next/navigation";
    
    import { AdminApiError, getConversation } from "@/lib/admin-api";
    import { formatFullDate, formatMoney } from "@/lib/format";
    import type {
      ProductFeedback,
      RecommendedProductSummary,
    } from "@/lib/types";
    
    export const dynamic = "force-dynamic";
    
    const feedbackLabels: Record<ProductFeedback["overall"], string> = {
      positive: "正面",
      negative: "负面",
      neutral: "中性",
      mixed: "褒贬不一",
      unclear: "不明确",
    };
    
    function ProductCard({
      item,
    }: {
      item: RecommendedProductSummary;
    }) {
      return (
        <article className="product-summary-card">
          <div className="product-summary-card__heading">
            <div>
              <span className="product-category">{item.product.category}</span>
              <h4>{item.product.name}</h4>
            </div>
            <div className="product-price">
              {formatMoney(item.product.price_cents)}
              {item.product.is_ad ? <span>广告</span> : null}
            </div>
          </div>
          <p className="product-description">{item.product.description}</p>
          {item.key_information.length > 0 ? (
            <dl className="key-information">
              {item.key_information.map((information, index) => (
                <div key={`${information.name}-${index}`}>
                  <dt>{information.name}</dt>
                  <dd>{information.value}</dd>
                </div>
              ))}
            </dl>
          ) : null}
          {item.reason ? (
            <div className="reason-block">
              <span>最终推荐理由</span>
              <p>{item.reason}</p>
              {item.environmental_fit ? (
                <small>场景匹配：{item.environmental_fit}</small>
              ) : null}
            </div>
          ) : null}
        </article>
      );
    }
    
    export default async function ConversationDetailPage({
      params,
    }: {
      params: Promise<{ conversationId: string }>;
    }) {
      const { conversationId } = await params;
      let result;
      try {
        result = await getConversation(conversationId);
      } catch (error) {
        const message =
          error instanceof AdminApiError
            ? error.message
            : "无法连接管理后端。";
        return (
          <section className="empty-state">
            <p className="eyebrow">CONVERSATION UNAVAILABLE</p>
            <h1>暂时无法加载对话</h1>
            <p>{message}</p>
            <Link className="primary-button" href="/conversations">
              返回对话列表
            </Link>
          </section>
        );
      }
      if (result === null) {
        notFound();
      }
    
      const { conversation, summary } = result;
      const productNames = new Map<string, string>();
      summary?.recommendation_rounds?.forEach((round) => {
        round.products.forEach((item) => {
          productNames.set(item.product.id, item.product.name);
        });
      });
    
      return (
        <div className="detail-page">
          <div className="detail-breadcrumb">
            <Link href="/conversations">对话管理</Link>
            <span>/</span>
            <strong>{conversation.title}</strong>
          </div>
    
          <section className="detail-hero">
            <div>
              <p className="eyebrow">CONVERSATION DETAIL</p>
              <h1>{conversation.title}</h1>
              <p className="mono-id">{conversation.id}</p>
            </div>
            <dl className="detail-metadata">
              <div>
                <dt>消息数量</dt>
                <dd>{conversation.message_count}</dd>
              </div>
              <div>
                <dt>创建时间</dt>
                <dd>{formatFullDate(conversation.created_at)}</dd>
              </div>
              <div>
                <dt>最近更新</dt>
                <dd>{formatFullDate(conversation.updated_at)}</dd>
              </div>
            </dl>
          </section>
    
          <section className="summary-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">GENERATED DIGEST</p>
                <h2>对话总结</h2>
              </div>
              {summary ? (
                <span className="summary-time">
                  生成于 {formatFullDate(summary.generated_at)}
                </span>
              ) : null}
            </div>
    
            {summary ? (
              <>
                <p className="summary-lead">{summary.summary}</p>
    
                <div className="summary-columns">
                  <div className="summary-block">
                    <h3>用户目标</h3>
                    {summary.user_goals?.length ? (
                      <ul className="plain-list">
                        {summary.user_goals.map((goal, index) => (
                          <li key={`${goal}-${index}`}>{goal}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="muted">未提取到明确目标</p>
                    )}
                  </div>
                  <div className="summary-block">
                    <h3>明确约束</h3>
                    {summary.explicit_constraints?.length ? (
                      <div className="tag-list">
                        {summary.explicit_constraints.map((constraint, index) => (
                          <span key={`${constraint}-${index}`}>{constraint}</span>
                        ))}
                      </div>
                    ) : (
                      <p className="muted">未提取到明确约束</p>
                    )}
                  </div>
                </div>
    
                <div className="summary-section">
                  <div className="section-title-row">
                    <h3>推荐商品与理由</h3>
                    <span>
                      {summary.recommendation_rounds?.reduce(
                        (total, round) => total + round.products.length,
                        0,
                      ) ?? 0}{" "}
                      件
                    </span>
                  </div>
                  {summary.recommendation_rounds?.length ? (
                    <div className="recommendation-rounds">
                      {summary.recommendation_rounds.map((round, roundIndex) => (
                        <div
                          className="recommendation-round"
                          key={round.assistant_message_id}
                        >
                          <div className="round-heading">
                            <span>推荐轮次 {roundIndex + 1}</span>
                            <p>{round.user_request}</p>
                          </div>
                          {round.ranking_summary ? (
                            <p className="ranking-summary">
                              终排摘要：{round.ranking_summary}
                            </p>
                          ) : null}
                          <div className="product-card-grid">
                            {round.products.map((item) => (
                              <ProductCard
                                item={item}
                                key={item.product.id}
                              />
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="muted">本对话没有记录到最终推荐商品。</p>
                  )}
                </div>
    
                <div className="summary-columns summary-columns--wide">
                  <div className="summary-block">
                    <h3>商品反馈</h3>
                    {summary.product_feedback?.length ? (
                      <div className="feedback-list">
                        {summary.product_feedback.map((feedback, index) => (
                          <article
                            className="feedback-card"
                            key={`${feedback.product_id}-${index}`}
                          >
                            <div>
                              <strong>
                                {productNames.get(feedback.product_id) ??
                                  feedback.product_id}
                              </strong>
                              <span
                                className={`polarity polarity--${feedback.overall}`}
                              >
                                {feedbackLabels[feedback.overall]}
                              </span>
                            </div>
                            {feedback.aspects.length ? (
                              <p>
                                {feedback.aspects
                                  .map(
                                    (aspect) =>
                                      `${aspect.name}${
                                        aspect.value ? `：${aspect.value}` : ""
                                      }`,
                                  )
                                  .join(" · ")}
                              </p>
                            ) : null}
                            {feedback.evidence.map((evidence) => (
                              <blockquote key={`${evidence.message_id}-${evidence.quote}`}>
                                “{evidence.quote}”
                              </blockquote>
                            ))}
                          </article>
                        ))}
                      </div>
                    ) : (
                      <p className="muted">用户尚未对推荐商品作出明确评价。</p>
                    )}
                  </div>
    
                  <div className="summary-block">
                    <h3>一般偏好</h3>
                    {summary.general_preferences?.length ? (
                      <div className="preference-list">
                        {summary.general_preferences.map((preference, index) => (
                          <article
                            className="preference-card"
                            key={`${preference.dimension}-${index}`}
                          >
                            <div>
                              <span>{preference.dimension}</span>
                              <strong>{preference.value}</strong>
                              <em>
                                {preference.polarity === "prefer"
                                  ? "偏好"
                                  : "排斥"}
                              </em>
                            </div>
                            {preference.evidence[0] ? (
                              <blockquote>
                                “{preference.evidence[0].quote}”
                              </blockquote>
                            ) : null}
                          </article>
                        ))}
                      </div>
                    ) : (
                      <p className="muted">本对话没有提取到一般偏好。</p>
                    )}
                  </div>
                </div>
    
                {summary.unresolved_items?.length ? (
                  <div className="unresolved-block">
                    <h3>待处理事项</h3>
                    <ul className="plain-list">
                      {summary.unresolved_items.map((item, index) => (
                        <li key={`${item}-${index}`}>{item}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </>
            ) : (
              <div className="summary-missing">
                <strong>总结尚未生成</strong>
                <p>
                  对话超过一小时未更新后，定时任务会在下一周期生成总结。当前仍可查看
                  下方完整对话。
                </p>
              </div>
            )}
          </section>
    
          <section className="panel message-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">CONVERSATION TRANSCRIPT</p>
                <h2>完整对话</h2>
              </div>
              <span className="count-badge">
                {conversation.messages.length} 条消息
              </span>
            </div>
            <div className="message-list">
              {conversation.messages.map((message, index) => (
                <article
                  className={`message message--${message.role}`}
                  key={message.id}
                >
                  <div className="message-rail">
                    <span>{String(index + 1).padStart(2, "0")}</span>
                    <i />
                  </div>
                  <div className="message-body">
                    <div className="message-heading">
                      <strong>
                        {message.role === "user" ? "用户" : "小牛导购"}
                      </strong>
                      <span
                        className={`message-status message-status--${message.status}`}
                      >
                        {message.status}
                      </span>
                      <time>{formatFullDate(message.created_at)}</time>
                    </div>
                    <p className="message-content">{message.content}</p>
                    {message.recommendations?.length ? (
                      <div className="inline-products">
                        {message.recommendations.map((product) => (
                          <div
                            className="inline-product"
                            key={product.id}
                          >
                            <div>
                              <strong>{product.name}</strong>
                              <span>{product.category}</span>
                            </div>
                            <b>{formatMoney(product.price_cents)}</b>
                          </div>
                        ))}
                      </div>
                    ) : null}
                    {message.orders?.length ? (
                      <p className="order-note">
                        创建订单：
                        {message.orders
                          .map((order) => order.order_id)
                          .join("、")}
                      </p>
                    ) : null}
                  </div>
                </article>
              ))}
            </div>
          </section>
        </div>
      );
    }

## Activity

    file changes: Completed · 1 changes
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-web/app/globals.css
    :root {
      --ink: #17201a;
      --muted: #69736c;
      --paper: #f4f5f1;
      --surface: #fff;
      --green: #1f4d38;
      --green-soft: #e6efe9;
      --lime: #d8ef72;
      --orange: #e96f3d;
      --line: #dfe4de;
      --danger: #a84136;
      --shadow: 0 16px 50px rgba(26, 47, 35, 0.07);
    }
    
    * {
      box-sizing: border-box;
    }
    
    body {
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(
          circle at 82% -10%,
          rgba(216, 239, 114, 0.24),
          transparent 30%
        ),
        var(--paper);
      font-family:
        "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    }
    
    a {
      color: inherit;
      text-decoration: none;
    }
    
    button,
    input {
      font: inherit;
    }
    
    .admin-header {
      position: sticky;
      z-index: 20;
      top: 0;
      border-bottom: 1px solid var(--line);
      background: rgba(244, 245, 241, 0.94);
      backdrop-filter: blur(14px);
    }
    
    .admin-header__inner {
      width: min(1440px, calc(100% - 56px));
      height: 72px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      gap: 46px;
    }
    
    .admin-brand {
      display: flex;
      align-items: baseline;
      gap: 10px;
    }
    
    .admin-brand span {
      color: var(--orange);
      font-size: 21px;
      font-weight: 950;
      letter-spacing: -1.2px;
    }
    
    .admin-brand strong {
      font-size: 14px;
    }
    
    .admin-header nav {
      align-self: stretch;
      display: flex;
      align-items: center;
    }
    
    .admin-header nav a {
      height: 100%;
      padding: 0 4px;
      display: flex;
      align-items: center;
      border-bottom: 2px solid var(--green);
      font-size: 13px;
      font-weight: 700;
    }
    
    .environment-pill {
      margin-left: auto;
      padding: 7px 10px;
      display: flex;
      align-items: center;
      gap: 7px;
      color: var(--green);
      border: 1px solid rgba(31, 77, 56, 0.17);
      border-radius: 999px;
      background: var(--green-soft);
      font-size: 9px;
      font-weight: 900;
      letter-spacing: 1.1px;
    }
    
    .environment-pill i {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #3d9b62;
    }
    
    .admin-main {
      width: min(1440px, calc(100% - 56px));
      margin: 0 auto;
      padding: 48px 0 90px;
    }
    
    .page-stack,
    .detail-page {
      display: flex;
      flex-direction: column;
      gap: 24px;
    }
    
    .page-heading {
      min-height: 220px;
      padding: 42px 46px;
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 40px;
      color: white;
      background:
        linear-gradient(110deg, rgba(23, 56, 40, 0.98), rgba(35, 76, 54, 0.92)),
        repeating-linear-gradient(
          -45deg,
          transparent,
          transparent 12px,
          rgba(255, 255, 255, 0.04) 12px,
          rgba(255, 255, 255, 0.04) 13px
        );
      border-radius: 4px;
    }
    
    .eyebrow {
      margin: 0 0 14px;
      color: var(--orange);
      font-size: 10px;
      font-weight: 900;
      letter-spacing: 2px;
    }
    
    .page-heading .eyebrow {
      color: var(--lime);
    }
    
    h1,
    h2,
    h3,
    h4,
    p {
      margin-top: 0;
    }
    
    .page-heading h1,
    .detail-hero h1,
    .empty-state h1 {
      margin-bottom: 16px;
      font-family: "Songti SC", "STSong", serif;
      font-size: clamp(42px, 5vw, 68px);
      line-height: 1;
      letter-spacing: -3px;
    }
    
    .page-description {
      max-width: 580px;
      margin: 0;
      color: rgba(255, 255, 255, 0.63);
      font-size: 14px;
      line-height: 1.8;
    }
    
    .metric-grid {
      display: grid;
      grid-template-columns: repeat(2, 120px);
      gap: 10px;
    }
    
    .metric-card {
      min-height: 88px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      border: 1px solid rgba(255, 255, 255, 0.16);
      background: rgba(255, 255, 255, 0.06);
    }
    
    .metric-card span {
      color: rgba(255, 255, 255, 0.55);
      font-size: 10px;
    }
    
    .metric-card strong {
      color: var(--lime);
      font-family: Georgia, serif;
      font-size: 34px;
      font-weight: 500;
    }
    
    .panel,
    .summary-panel {
      border: 1px solid var(--line);
      background: var(--surface);
      box-shadow: var(--shadow);
    }
    
    .panel {
      overflow: hidden;
    }
    
    .summary-panel {
      padding: 38px 42px 42px;
    }
    
    .panel-heading {
      margin-bottom: 26px;
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 24px;
    }
    
    .panel-heading h2 {
      margin: 0 0 6px;
      font-family: "Songti SC", "STSong", serif;
      font-size: 30px;
      letter-spacing: -1.4px;
    }
    
    .panel-heading p:not(.eyebrow) {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
    }
    
    .count-badge,
    .summary-time {
      padding: 7px 10px;
      color: var(--green);
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #f8faf7;
      font-size: 10px;
      font-weight: 800;
    }
    
    .table-wrap {
      overflow-x: auto;
    }
    
    table {
      width: 100%;
      border-collapse: collapse;
    }
    
    th {
      padding: 13px 20px;
      color: #7e8780;
      background: #f8faf7;
      border-top: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 1px;
      text-align: left;
    }
    
    td {
      padding: 20px;
      border-bottom: 1px solid var(--line);
      color: #465049;
      font-size: 12px;
      vertical-align: middle;
    }
    
    tbody tr {
      transition: background 140ms ease;
    }
    
    tbody tr:hover {
      background: #fafbf8;
    }
    
    .conversation-title {
      display: block;
      margin-bottom: 5px;
      color: var(--ink);
      font-size: 14px;
      font-weight: 800;
    }
    
    .conversation-title:hover,
    .text-link:hover,
    .detail-breadcrumb a:hover {
      color: var(--orange);
    }
    
    .mono-id {
      color: #8b948d;
      font-family: "SFMono-Regular", Consolas, monospace;
      font-size: 9px;
      letter-spacing: 0.2px;
      word-break: break-all;
    }
    
    .action-cell {
      text-align: right;
    }
    
    .text-link {
      color: var(--green);
      font-weight: 800;
    }
    
    .empty-row {
      padding: 76px 20px;
      color: var(--muted);
      text-align: center;
      border-top: 1px solid var(--line);
    }
    
    .empty-state {
      min-height: calc(100vh - 250px);
      padding: 80px;
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      justify-content: center;
      border: 1px dashed #cbd2ca;
      background: rgba(255, 255, 255, 0.72);
    }
    
    .empty-state p:not(.eyebrow) {
      max-width: 600px;
      color: var(--muted);
      line-height: 1.8;
    }
    
    .empty-state code {
      margin: 12px 0 26px;
      padding: 10px 12px;
      color: var(--green);
      background: var(--green-soft);
    }
    
    .primary-button {
      padding: 12px 18px;
      color: white;
      border-radius: 2px;
      background: var(--green);
      font-size: 12px;
      font-weight: 800;
    }
    
    .detail-breadcrumb {
      display: flex;
      align-items: center;
      gap: 10px;
      color: #818a83;
      font-size: 11px;
    }
    
    .detail-breadcrumb a {
      color: var(--green);
      font-weight: 800;
    }
    
    .detail-breadcrumb strong {
      max-width: 50vw;
      overflow: hidden;
      color: var(--ink);
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .detail-hero {
      padding: 36px 42px;
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 40px;
      border: 1px solid var(--line);
      background: var(--surface);
      box-shadow: var(--shadow);
    }
    
    .detail-hero h1 {
      margin-bottom: 10px;
      font-size: clamp(36px, 4vw, 56px);
    }
    
    .detail-metadata {
      margin: 0;
      display: grid;
      grid-template-columns: repeat(3, minmax(110px, auto));
      gap: 1px;
      overflow: hidden;
      border: 1px solid var(--line);
      background: var(--line);
    }
    
    .detail-metadata div {
      padding: 15px 18px;
      background: #f8faf7;
    }
    
    .detail-metadata dt {
      margin-bottom: 6px;
      color: var(--muted);
      font-size: 9px;
      font-weight: 800;
    }
    
    .detail-metadata dd {
      margin: 0;
      font-size: 12px;
      font-weight: 700;
    }
    
    .summary-lead {
      margin: 0 0 30px;
      padding: 24px 28px;
      color: #21352a;
      border-left: 4px solid var(--lime);
      background: var(--green-soft);
      font-family: "Songti SC", "STSong", serif;
      font-size: 21px;
      line-height: 1.65;
    }
    
    .summary-columns {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 20px;
    }
    
    .summary-columns--wide {
      margin-top: 30px;
    }
    
    .summary-block {
      min-width: 0;
      padding: 22px;
      border: 1px solid var(--line);
      background: #fbfcfa;
    }
    
    .summary-block h3,
    .summary-section h3,
    .unresolved-block h3 {
      margin-bottom: 16px;
      font-size: 13px;
      letter-spacing: 0.2px;
    }
    
    .plain-list {
      margin: 0;
      padding-left: 18px;
      color: #4d5750;
      font-size: 12px;
      line-height: 1.8;
    }
    
    .tag-list {
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
    }
    
    .tag-list span {
      padding: 6px 9px;
      color: var(--green);
      border: 1px solid #d3ded6;
      border-radius: 999px;
      background: white;
      font-size: 10px;
      font-weight: 700;
    }
    
    .muted {
      margin: 0;
      color: #8a938c;
      font-size: 11px;
      line-height: 1.7;
    }
    
    .summary-section {
      margin-top: 30px;
      padding-top: 28px;
      border-top: 1px solid var(--line);
    }
    
    .section-title-row {
      margin-bottom: 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    
    .section-title-row h3 {
      margin: 0;
    }
    
    .section-title-row span {
      color: var(--muted);
      font-size: 10px;
    }
    
    .recommendation-rounds {
      display: flex;
      flex-direction: column;
      gap: 18px;
    }
    
    .recommendation-round {
      padding: 20px;
      border: 1px solid var(--line);
      background: #fafbf8;
    }
    
    .round-heading {
      margin-bottom: 14px;
      display: flex;
      align-items: baseline;
      gap: 14px;
    }
    
    .round-heading span {
      flex: 0 0 auto;
      color: var(--orange);
      font-size: 9px;
      font-weight: 900;
      letter-spacing: 1px;
    }
    
    .round-heading p {
      margin: 0;
      color: #4f5952;
      font-size: 12px;
    }
    
    .ranking-summary {
      margin: -2px 0 16px;
      color: var(--muted);
      font-size: 11px;
    }
    
    .product-card-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }
    
    .product-summary-card {
      padding: 18px;
      border: 1px solid var(--line);
      background: white;
    }
    
    .product-summary-card__heading {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 18px;
    }
    
    .product-category {
      color: var(--orange);
      font-size: 9px;
      font-weight: 900;
      letter-spacing: 1px;
    }
    
    .product-summary-card h4 {
      margin: 5px 0 0;
      font-size: 15px;
    }
    
    .product-price {
      color: var(--green);
      font-family: Georgia, serif;
      font-size: 17px;
      white-space: nowrap;
    }
    
    .product-price span {
      margin-left: 6px;
      padding: 3px 5px;
      color: var(--orange);
      border: 1px solid rgba(233, 111, 61, 0.3);
      font-family: inherit;
      font-size: 8px;
    }
    
    .product-description {
      margin: 12px 0;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.7;
    }
    
    .key-information {
      margin: 0 0 14px;
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    
    .key-information div {
      padding: 5px 7px;
      display: flex;
      gap: 5px;
      background: var(--green-soft);
      font-size: 9px;
    }
    
    .key-information dt {
      color: var(--muted);
    }
    
    .key-information dd {
      margin: 0;
      color: var(--green);
      font-weight: 800;
    }
    
    .reason-block {
      padding-top: 12px;
      border-top: 1px solid var(--line);
    }
    
    .reason-block > span {
      color: var(--orange);
      font-size: 9px;
      font-weight: 900;
    }
    
    .reason-block p {
      margin: 6px 0;
      color: #38443c;
      font-size: 11px;
      line-height: 1.7;
    }
    
    .reason-block small {
      color: var(--muted);
      font-size: 9px;
    }
    
    .feedback-list,
    .preference-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    
    .feedback-card,
    .preference-card {
      padding: 14px;
      border: 1px solid var(--line);
      background: white;
    }
    
    .feedback-card > div,
    .preference-card > div {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
    }
    
    .feedback-card strong,
    .preference-card strong {
      font-size: 12px;
    }
    
    .feedback-card p {
      margin: 8px 0;
      color: var(--muted);
      font-size: 10px;
    }
    
    .polarity,
    .preference-card em {
      padding: 3px 6px;
      border-radius: 999px;
      background: #eef1ed;
      color: #626c65;
      font-size: 8px;
      font-style: normal;
      font-weight: 800;
    }
    
    .polarity--positive {
      color: #276b45;
      background: #e7f4eb;
    }
    
    .polarity--negative {
      color: var(--danger);
      background: #faeae6;
    }
    
    .polarity--mixed {
      color: #986018;
      background: #faf0df;
    }
    
    .preference-card span {
      color: var(--muted);
      font-size: 9px;
    }
    
    blockquote {
      margin: 10px 0 0;
      padding-left: 10px;
      color: #626b64;
      border-left: 2px solid #d6ddd7;
      font-size: 10px;
      line-height: 1.65;
    }
    
    .unresolved-block {
      margin-top: 22px;
      padding: 20px 22px;
      border: 1px dashed #cbd4cc;
    }
    
    .summary-missing {
      padding: 30px;
      color: #6a4b2e;
      border: 1px dashed #dbc09c;
      background: #fcf6ea;
    }
    
    .summary-missing strong {
      display: block;
      margin-bottom: 8px;
    }
    
    .summary-missing p {
      margin: 0;
      font-size: 12px;
      line-height: 1.8;
    }
    
    .message-panel {
      padding-top: 34px;
    }
    
    .message-panel .panel-heading {
      padding: 0 34px;
    }
    
    .message-list {
      border-top: 1px solid var(--line);
    }
    
    .message {
      display: grid;
      grid-template-columns: 58px minmax(0, 1fr);
      padding: 0 34px;
    }
    
    .message-rail {
      padding-top: 27px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 10px;
    }
    
    .message-rail span {
      color: #98a19a;
      font-family: Georgia, serif;
      font-size: 13px;
    }
    
    .message-rail i {
      width: 1px;
      flex: 1;
      background: var(--line);
    }
    
    .message-body {
      padding: 24px 0 28px;
      border-bottom: 1px solid var(--line);
    }
    
    .message:last-child .message-body {
      border-bottom: 0;
    }
    
    .message--user .message-body {
      margin: 14px 0;
      padding: 22px;
      border: 1px solid #dce4de;
      background: #f7faf7;
    }
    
    .message:last-child .message--user .message-body {
      border-bottom: 1px solid #dce4de;
    }
    
    .message-heading {
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 9px;
    }
    
    .message-heading strong {
      font-size: 12px;
    }
    
    .message-heading time {
      margin-left: auto;
      color: #929a94;
      font-size: 9px;
    }
    
    .message-status {
      padding: 3px 6px;
      color: #687269;
      border-radius: 999px;
      background: #eef1ed;
      font-size: 8px;
      font-weight: 800;
    }
    
    .message-status--failed {
      color: var(--danger);
      background: #faeae6;
    }
    
    .message-status--completed {
      color: #276b45;
      background: #e7f4eb;
    }
    
    .message-content {
      margin: 0;
      color: #354139;
      font-size: 13px;
      line-height: 1.9;
      white-space: pre-wrap;
    }
    
    .inline-products {
      margin-top: 16px;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }
    
    .inline-product {
      padding: 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      border: 1px solid var(--line);
      background: white;
    }
    
    .inline-product div {
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    
    .inline-product strong {
      overflow: hidden;
      font-size: 11px;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .inline-product span {
      color: var(--muted);
      font-size: 9px;
    }
    
    .inline-product b {
      color: var(--green);
      font-family: Georgia, serif;
      font-size: 12px;
      white-space: nowrap;
    }
    
    .order-note {
      margin: 12px 0 0;
      color: #8b5d35;
      font-size: 10px;
    }
    
    @media (max-width: 900px) {
      .admin-header__inner,
      .admin-main {
        width: min(100% - 28px, 1440px);
      }
    
      .admin-main {
        padding-top: 24px;
      }
    
      .page-heading,
      .detail-hero {
        padding: 30px;
        align-items: flex-start;
        flex-direction: column;
      }
    
      .metric-grid {
        width: 100%;
      }
    
      .metric-card {
        flex: 1;
      }
    
      .summary-panel {
        padding: 28px 22px;
      }
    
      .summary-columns,
      .product-card-grid,
      .inline-products {
        grid-template-columns: 1fr;
      }
    
      .detail-metadata {
        width: 100%;
        grid-template-columns: 1fr;
      }
    }
    
    @media (max-width: 560px) {
      .admin-header nav {
        display: none;
      }
    
      .admin-main {
        width: calc(100% - 20px);
      }
    
      .page-heading h1,
      .detail-hero h1,
      .empty-state h1 {
        font-size: 38px;
        letter-spacing: -2px;
      }
    
      .panel-heading {
        align-items: flex-start;
        flex-direction: column;
      }
    
      th:nth-child(3),
      td:nth-child(3) {
        display: none;
      }
    
      .message {
        grid-template-columns: 34px minmax(0, 1fr);
        padding: 0 16px;
      }
    
      .message-panel .panel-heading {
        padding: 0 20px;
      }
    }

## Assistant

`admin-backend` 和 `admin-web` 的主体已完成：列表、详情、总结缺失状态、商品理由、用户反馈与偏好、完整消息记录都已接入。现在安装前端依赖并做类型检查与生产构建，之后会修正构建中发现的问题。

## Activity

    $ pnpm install
     WARN  Request took 11046ms: https://registry.npmmirror.com/@types%2Freact-dom
    Progress: resolved 1, reused 0, downloaded 0, added 0
    Progress: resolved 1, reused 1, downloaded 0, added 0
     WARN  Request took 18512ms: https://registry.npmmirror.com/pnpm
    
       ╭──────────────────────────────────────────╮
       │                                          │
       │   Update available! 10.29.3 → 12.18.0.   │
       │   Changelog: https://pnpm.io/v/12.18.0   │
       │     To update, run: pnpm self-update     │
       │                                          │
       ╰──────────────────────────────────────────╯
    
     WARN  Request took 18562ms: https://registry.npmmirror.com/@types%2Fnode
    Progress: resolved 2, reused 1, downloaded 0, added 0
    Progress: resolved 2, reused 2, downloaded 0, added 0
     WARN  Request took 20235ms: https://registry.npmmirror.com/@types%2Freact
     WARN  Request took 20312ms: https://registry.npmmirror.com/react
    Progress: resolved 4, reused 4, downloaded 0, added 0
     WARN  Request took 22108ms: https://registry.npmmirror.com/typescript
    Progress: resolved 5, reused 4, downloaded 0, added 0
    Progress: resolved 5, reused 5, downloaded 0, added 0
     WARN  Request took 23363ms: https://registry.npmmirror.com/next
    Progress: resolved 6, reused 5, downloaded 0, added 0
     WARN  Request took 28020ms: https://registry.npmmirror.com/react-dom
    Progress: resolved 7, reused 5, downloaded 0, added 0
    Progress: resolved 12, reused 11, downloaded 0, added 0
    Progress: resolved 14, reused 12, downloaded 0, added 0
    Progress: resolved 15, reused 12, downloaded 0, added 0
    Progress: resolved 16, reused 12, downloaded 0, added 0
    Progress: resolved 17, reused 12, downloaded 0, added 0
    Progress: resolved 18, reused 13, downloaded 2, added 0
    Progress: resolved 20, reused 13, downloaded 2, added 0
    Progress: resolved 22, reused 13, downloaded 2, added 0
     WARN  Request took 11716ms: https://registry.npmmirror.com/@next%2Fswc-win32-arm64-msvc
    Progress: resolved 23, reused 13, downloaded 2, added 0
     WARN  Request took 12139ms: https://registry.npmmirror.com/@next%2Fswc-linux-arm64-gnu
    Packages: +27
    +++++++++++++++++++++++++++
    Progress: resolved 59, reused 24, downloaded 2, added 24
    Progress: resolved 59, reused 24, downloaded 3, added 25
    Progress: resolved 59, reused 24, downloaded 4, added 25
    Progress: resolved 59, reused 24, downloaded 4, added 26
    Progress: resolved 59, reused 24, downloaded 5, added 26
    Progress: resolved 59, reused 24, downloaded 5, added 27, done
    
    dependencies:
    + next 15.5.29 (16.4.6 is available)
    + react 19.3.1
    + react-dom 19.3.1
    
    devDependencies:
    + @types/node 22.20.5 (26.6.6 is available)
    + @types/react 19.3.0
    + @types/react-dom 19.3.0
    + typescript 5.9.3 (7.0.2 is available)
    
    Done in 3m 2.7s using pnpm v10.29.3
    ✓ • 3m 02s

## Activity

    $ uv lock
    Resolved 72 packages in 3.25s
    Added admin-backend v0.1.0
    ✓ • 3.16s

## Activity

    $ uv run pytest admin-backend/tests -q
       Building admin-backend @ file:///Users/mindeng/workspace/niub-shangcheng/admin-backend
          Built admin-backend @ file:///Users/mindeng/workspace/niub-shangcheng/admin-backend
    Installed 1 package in 1ms
    ......                                                                   [100%]
    6 passed in 0.17s
    ✓ • 1.93s

## Activity

    $ pnpm build
    
    > niub-admin-web@0.1.0 build /Users/mindeng/workspace/niub-shangcheng/admin-web
    > next build
    
       ▲ Next.js 15.5.29
    
       Creating an optimized production build ...
     ✓ Compiled successfully in 2.0s
       Linting and checking validity of types ...
       Collecting page data ...
       Generating static pages (0/4) ...
       Generating static pages (1/4)
       Generating static pages (2/4)
       Generating static pages (3/4)
     ✓ Generating static pages (4/4)
       Finalizing page optimization ...
       Collecting build traces ...
    
    Route (app)                                 Size  First Load JS
    ┌ ○ /                                      127 B         102 kB
    ├ ○ /_not-found                            127 B         102 kB
    ├ ƒ /conversations                         166 B         105 kB
    └ ƒ /conversations/[conversationId]        166 B         105 kB
    + First Load JS shared by all             102 kB
      ├ chunks/0453825f-c8a6ffc8aac4ea8b.js  54.2 kB
      ├ chunks/708-f76e100034acd83a.js       45.8 kB
      └ other shared chunks (total)           1.9 kB
    
    
    ○  (Static)   prerendered as static content
    ƒ  (Dynamic)  server-rendered on demand
    
    ✓ • 11.20s

## Assistant

前后端构建和 admin 后端测试都已通过。接下来补齐项目启动文档和服务拓扑，并做一次完整回归；同时会实际启动 admin 服务验证页面路由和 API 组合链路。

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/README.md
    @@ -2,3 +2,3 @@
     
    -项目拆分为三个可独立运行的模块：
    +项目拆分为以下可独立运行的模块：
     
    @@ -13,2 +13,9 @@
                                   └── HTTP ──► mall-service Mock APIs
    +
    +运营人员
    +  │
    +  ▼
    +admin-web (Next.js :3001)
    +  └── HTTP ──► admin-backend (:8003)
    +                    └── HTTP ──► agent-service (:8002)
     ```
    @@ -19,2 +26,4 @@
     - `web`：Next.js 商城页面，浏览器只访问同源的 Next.js API 路由。
    +- `admin-backend`：内部运营 API，聚合 `agent-service` 的对话、消息和定时总结。
    +- `admin-web`：内部运营后台，提供对话列表和对话详情查看。
     
    @@ -28,3 +37,3 @@
     
    -分别在三个终端启动服务：
    +分别在需要的终端启动服务：
     
    @@ -45,2 +54,17 @@
     
    +启动运营后台：
    +
    +```bash
    +uv run --package admin-backend admin-backend
    +```
    +
    +```bash
    +pnpm --dir admin-web install
    +pnpm --dir admin-web dev
    +```
    +
    +打开 <http://localhost:3001>，默认进入 `/conversations`。`admin-backend` 默认只
    +监听 `127.0.0.1:8003`，通过 `AGENT_SERVICE_URL` 访问 Agent 服务。该模块当前定位
    +为内部轻量后台，不包含登录和权限系统，因此不应直接暴露到公网。
    +
     ## 大模型配置
    @@ -95,2 +119,3 @@
     agent-service/prompts/recommendation_reranker.md
    +agent-service/prompts/conversation_summary.md
     ```
    @@ -125,2 +150,5 @@
     - 历史对话详情：`GET http://localhost:8002/api/conversations/{conversation_id}`
    +- 对话总结：`GET http://localhost:8002/api/conversations/{conversation_id}/summary`
    +- Admin 对话列表：`GET http://localhost:8003/api/conversations`
    +- Admin 对话详情及总结：`GET http://localhost:8003/api/conversations/{conversation_id}`
     
    @@ -137,2 +165,3 @@
     pnpm --dir web build
    +pnpm --dir admin-web build
     ```
    @@ -157,2 +186,16 @@
     
    +## 对话总结与运营后台
    +
    +`agent-service` 每小时扫描一次，只总结超过一小时没有更新、且时间戳表明内容发生
    +变化的对话。对话被重新使用后，下一次满足闲置条件的扫描会重新生成并替换当前
    +总结。总结任务不提供用户主动触发接口。
    +
    +总结包括对话目标、约束、推荐商品和最终推荐理由、商品规格等关键信息、用户的商品
    +反馈、明确表达的一般偏好以及未解决事项。`admin-web` 在对话详情页展示总结和完整
    +消息；尚未生成总结的对话会显示等待定时任务处理的状态。
    +
    +最新一小时内的对话可能还没有可用总结。后续对话召回需要回退到原始消息，该事项
    +记录在 `conversation_summary_worker.py` 的
    +`TODO(conversation-summary-freshness)` 中。
    +
     ## 推荐商品 Agent

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/admin-web/app/globals.css
    @@ -815,6 +815,2 @@
     
    -.message:last-child .message--user .message-body {
    -  border-bottom: 1px solid #dce4de;
    -}
    -
     .message-heading {

## Activity

    $ lsof -nP -iTCP:8002 -sTCP:LISTEN || true
    COMMAND    PID    USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
    python3.1 6337 mindeng    3u  IPv4 0x96a5c72968893176      0t0  TCP *:8002 (LISTEN)
    python3.1 6339 mindeng    3u  IPv4 0x96a5c72968893176      0t0  TCP *:8002 (LISTEN)
    ✓ • 0ms

## Activity

    $ lsof -nP -iTCP:8003 -sTCP:LISTEN || true
    ✓ • 0ms

## Activity

    $ lsof -nP -iTCP:3001 -sTCP:LISTEN || true
    ✓ • 0ms

## Activity

    $ curl -sS http://127.0.0.1:8002/api/conversations | head -c 2000
    curl: (7) Failed to connect to 127.0.0.1 port 8002 after 0 ms: Could not connect to server
    ✓ • 0ms

## Activity

    $ curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8002/health
    curl: (7) Failed to connect to 127.0.0.1 port 8002 after 0 ms: Could not connect to server
    000
    ✗ (7) • 0ms

## Activity

    $ curl -sS http://127.0.0.1:8003/health
    curl: (7) Failed to connect to 127.0.0.1 port 8003 after 0 ms: Could not connect to server
    ✗ (7) • 0ms

## Activity

    $ curl -sS -o /tmp/admin-list-response.json -w '%{http_code}\n' http://127.0.0.1:8003/api/conversations
    curl: (7) Failed to connect to 127.0.0.1 port 8003 after 0 ms: Could not connect to server
    000
    ✗ (7) • 0ms

## Activity

    $ uv run --package admin-backend admin-backend
    INFO:     Started server process [7744]
    INFO:     Waiting for application startup.
    INFO:     Application startup complete.
    INFO:     Uvicorn running on http://127.0.0.1:8003 (Press CTRL+C to quit)
    ^CINFO:     Shutting down
    INFO:     Waiting for application shutdown.
    INFO:     Application shutdown complete.
    INFO:     Finished server process [7744]
    ✓ • 44.48s

## Activity

    $ git diff --check
    ✓ • 0ms

## Activity

    $ uv run pytest -q
    ........................................................................ [ 66%]
    ....................................                                     [100%]
    108 passed in 1.74s
    ✓ • 2.22s

## Activity

    $ pnpm build
    
    > niub-shangcheng-web@0.1.0 build /Users/mindeng/workspace/niub-shangcheng/web
    > next build
    
       ▲ Next.js 15.5.28
    
       Creating an optimized production build ...
     ✓ Compiled successfully in 990ms
       Linting and checking validity of types ...
       Collecting page data ...
       Generating static pages (0/7) ...
       Generating static pages (1/7)
       Generating static pages (3/7)
       Generating static pages (5/7)
     ✓ Generating static pages (7/7)
       Finalizing page optimization ...
       Collecting build traces ...
    
    Route (app)                                 Size  First Load JS
    ┌ ○ /                                    2.41 kB         105 kB
    ├ ○ /_not-found                            995 B         103 kB
    ├ ƒ /api/chat                              140 B         103 kB
    ├ ƒ /api/chat/stream                       140 B         103 kB
    ├ ƒ /api/conversations                     140 B         103 kB
    ├ ƒ /api/conversations/[conversationId]    140 B         103 kB
    ├ ƒ /api/orders/[orderId]                  140 B         103 kB
    ├ ƒ /api/orders/[orderId]/pay              140 B         103 kB
    ├ ƒ /api/products                          140 B         103 kB
    ├ ○ /chat                                6.22 kB         112 kB
    ├ ƒ /orders/[orderId]                    2.09 kB         108 kB
    └ ƒ /products/[productId]                  378 B         106 kB
    + First Load JS shared by all             102 kB
      ├ chunks/829-8dab9a64d44a51d9.js       46.2 kB
      ├ chunks/d9cbff8c-b2655549e18d6010.js  54.2 kB
      └ other shared chunks (total)          1.95 kB
    
    
    ○  (Static)   prerendered as static content
    ƒ  (Dynamic)  server-rendered on demand
    
    ✓ • 7.97s

## Activity

    $ git status --short && find admin-web admin-backend -maxdepth 3 -type f | sort | sed -n '1,240p'
     M README.md
     M agent-service/.env.example
     M agent-service/src/agent_service/agent_runner.py
     M agent-service/src/agent_service/api.py
     M agent-service/src/agent_service/models.py
     M agent-service/src/agent_service/storage.py
     M agent-service/tests/test_agent_api.py
     M agent-service/tests/test_agent_runner.py
     M pyproject.toml
     M uv.lock
    ?? admin-backend/
    ?? admin-web/
    ?? agent-service/prompts/conversation_summary.md
    ?? agent-service/src/agent_service/conversation_summary.py
    ?? agent-service/src/agent_service/conversation_summary_worker.py
    ?? agent-service/tests/test_conversation_summary.py
    ?? agent-service/tests/test_conversation_summary_worker.py
    admin-backend/.env.example
    admin-backend/pyproject.toml
    admin-backend/src/admin_backend/__init__.py
    admin-backend/src/admin_backend/agent_client.py
    admin-backend/src/admin_backend/api.py
    admin-backend/src/admin_backend/main.py
    admin-backend/tests/__pycache__/test_admin_api.cpython-312-pytest-9.2.0.pyc
    admin-backend/tests/test_admin_api.py
    admin-web/.env.example
    admin-web/.next/BUILD_ID
    admin-web/.next/app-build-manifest.json
    admin-web/.next/app-path-routes-manifest.json
    admin-web/.next/build-manifest.json
    admin-web/.next/cache/.previewinfo
    admin-web/.next/cache/.rscinfo
    admin-web/.next/cache/.tsbuildinfo
    admin-web/.next/diagnostics/build-diagnostics.json
    admin-web/.next/diagnostics/framework.json
    admin-web/.next/export-marker.json
    admin-web/.next/images-manifest.json
    admin-web/.next/next-minimal-server.js.nft.json
    admin-web/.next/next-server.js.nft.json
    admin-web/.next/package.json
    admin-web/.next/prerender-manifest.json
    admin-web/.next/react-loadable-manifest.json
    admin-web/.next/required-server-files.json
    admin-web/.next/routes-manifest.json
    admin-web/.next/server/app-paths-manifest.json
    admin-web/.next/server/functions-config-manifest.json
    admin-web/.next/server/interception-route-rewrite-manifest.js
    admin-web/.next/server/middleware-build-manifest.js
    admin-web/.next/server/middleware-manifest.json
    admin-web/.next/server/middleware-react-loadable-manifest.js
    admin-web/.next/server/next-font-manifest.js
    admin-web/.next/server/next-font-manifest.json
    admin-web/.next/server/pages-manifest.json
    admin-web/.next/server/server-reference-manifest.js
    admin-web/.next/server/server-reference-manifest.json
    admin-web/.next/server/webpack-runtime.js
    admin-web/.next/trace
    admin-web/.next/types/cache-life.d.ts
    admin-web/.next/types/package.json
    admin-web/.next/types/routes.d.ts
    admin-web/.next/types/validator.ts
    admin-web/app/conversations/page.tsx
    admin-web/app/globals.css
    admin-web/app/layout.tsx
    admin-web/app/not-found.tsx
    admin-web/app/page.tsx
    admin-web/lib/admin-api.ts
    admin-web/lib/format.ts
    admin-web/lib/types.ts
    admin-web/next-env.d.ts
    admin-web/next.config.ts
    admin-web/node_modules/.bin/next
    admin-web/node_modules/.bin/tsc
    admin-web/node_modules/.bin/tsserver
    admin-web/node_modules/.modules.yaml
    admin-web/node_modules/.pnpm-workspace-state-v1.json
    admin-web/node_modules/.pnpm/lock.yaml
    admin-web/package.json
    admin-web/pnpm-lock.yaml
    admin-web/tsconfig.json
    ✓ • 0ms

## Activity

    $ pnpm build
    
    > niub-admin-web@0.1.0 build /Users/mindeng/workspace/niub-shangcheng/admin-web
    > next build
    
       ▲ Next.js 15.5.29
    
       Creating an optimized production build ...
     ✓ Compiled successfully in 1087ms
       Linting and checking validity of types ...
       Collecting page data ...
       Generating static pages (0/4) ...
       Generating static pages (1/4)
       Generating static pages (2/4)
       Generating static pages (3/4)
     ✓ Generating static pages (4/4)
       Finalizing page optimization ...
       Collecting build traces ...
    
    Route (app)                                 Size  First Load JS
    ┌ ○ /                                      127 B         102 kB
    ├ ○ /_not-found                            127 B         102 kB
    ├ ƒ /conversations                         166 B         105 kB
    └ ƒ /conversations/[conversationId]        166 B         105 kB
    + First Load JS shared by all             102 kB
      ├ chunks/0453825f-c8a6ffc8aac4ea8b.js  54.2 kB
      ├ chunks/708-f76e100034acd83a.js       45.8 kB
      └ other shared chunks (total)           1.9 kB
    
    
    ○  (Static)   prerendered as static content
    ƒ  (Dynamic)  server-rendered on demand
    
    ✓ • 7.62s

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/admin-backend/src/admin_backend/agent_client.py
    @@ -1,2 +1,3 @@
     import httpx
    +from urllib.parse import quote
     
    @@ -52,3 +53,3 @@
                 "GET",
    -            f"/api/conversations/{conversation_id}",
    +            f"/api/conversations/{quote(conversation_id, safe='')}",
             )
    @@ -68,3 +69,3 @@
                 "GET",
    -            f"/api/conversations/{conversation_id}/summary",
    +            f"/api/conversations/{quote(conversation_id, safe='')}/summary",
             )

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/admin-backend/src/admin_backend/agent_client.py
    @@ -1,4 +1,5 @@
    -import httpx
     from urllib.parse import quote
     
    +import httpx
    +
     

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/admin-web/app/conversations/[conversationId]/page.tsx
    @@ -91,2 +91,4 @@
       const { conversation, summary } = result;
    +  const summaryIsCurrent =
    +    summary !== null && summary.source_updated_at === conversation.updated_at;
       const productNames = new Map<string, string>();
    @@ -135,5 +137,10 @@
               {summary ? (
    -            <span className="summary-time">
    -              生成于 {formatFullDate(summary.generated_at)}
    -            </span>
    +            <div className="summary-heading-meta">
    +              {!summaryIsCurrent ? (
    +                <span className="summary-stale">等待重新生成</span>
    +              ) : null}
    +              <span className="summary-time">
    +                生成于 {formatFullDate(summary.generated_at)}
    +              </span>
    +            </div>
               ) : null}
    @@ -144,2 +151,7 @@
                 <p className="summary-lead">{summary.summary}</p>
    +            {!summaryIsCurrent ? (
    +              <div className="summary-stale-notice">
    +                这份总结生成后对话又发生了更新，最新内容将在下个定时周期重新总结。
    +              </div>
    +            ) : null}
     

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/admin-web/app/globals.css
    @@ -261,2 +261,27 @@
     
    +.summary-heading-meta {
    +  display: flex;
    +  align-items: center;
    +  gap: 8px;
    +}
    +
    +.summary-stale {
    +  padding: 7px 10px;
    +  color: #936020;
    +  border: 1px solid #ead4b5;
    +  border-radius: 999px;
    +  background: #fcf4e8;
    +  font-size: 10px;
    +  font-weight: 800;
    +}
    +
    +.summary-stale-notice {
    +  margin: -14px 0 28px;
    +  padding: 12px 14px;
    +  color: #76542f;
    +  border: 1px solid #ead4b5;
    +  background: #fcf8f0;
    +  font-size: 11px;
    +}
    +
     .table-wrap {

## Activity

    $ git diff --check
    ✓ • 0ms

## Activity

    $ uv run pytest -q
    ........................................................................ [ 66%]
    ....................................                                     [100%]
    108 passed in 1.53s
    ✓ • 1.93s

## Activity

    $ pnpm build
    
    > niub-admin-web@0.1.0 build /Users/mindeng/workspace/niub-shangcheng/admin-web
    > next build
    
       ▲ Next.js 15.5.29
    
       Creating an optimized production build ...
     ✓ Compiled successfully in 1040ms
       Linting and checking validity of types ...
       Collecting page data ...
       Generating static pages (0/4) ...
       Generating static pages (1/4)
       Generating static pages (2/4)
       Generating static pages (3/4)
     ✓ Generating static pages (4/4)
       Finalizing page optimization ...
       Collecting build traces ...
    
    Route (app)                                 Size  First Load JS
    ┌ ○ /                                      127 B         102 kB
    ├ ○ /_not-found                            127 B         102 kB
    ├ ƒ /conversations                         166 B         105 kB
    └ ƒ /conversations/[conversationId]        166 B         105 kB
    + First Load JS shared by all             102 kB
      ├ chunks/0453825f-c8a6ffc8aac4ea8b.js  54.2 kB
      ├ chunks/708-f76e100034acd83a.js       45.8 kB
      └ other shared chunks (total)           1.9 kB
    
    
    ○  (Static)   prerendered as static content
    ƒ  (Dynamic)  server-rendered on demand
    
    ✓ • 7.43s

## Activity

    $ uv lock --check
    Resolved 72 packages in 8ms
    ✓ • 0ms

## Activity

    $ git status --short --branch
    ## main
     M README.md
     M agent-service/.env.example
     M agent-service/src/agent_service/agent_runner.py
     M agent-service/src/agent_service/api.py
     M agent-service/src/agent_service/models.py
     M agent-service/src/agent_service/storage.py
     M agent-service/tests/test_agent_api.py
     M agent-service/tests/test_agent_runner.py
     M pyproject.toml
     M uv.lock
    ?? admin-backend/
    ?? admin-web/
    ?? agent-service/prompts/conversation_summary.md
    ?? agent-service/src/agent_service/conversation_summary.py
    ?? agent-service/src/agent_service/conversation_summary_worker.py
    ?? agent-service/tests/test_conversation_summary.py
    ?? agent-service/tests/test_conversation_summary_worker.py
    ✓ • 0ms

## Activity

    $ rg -n "admin-backend|admin-web|conversation_summary" README.md pyproject.toml | sed -n '1,160p'
    pyproject.toml:2:members = ["agent-service", "mall-service", "admin-backend"]
    pyproject.toml:8:pythonpath = ["agent-service/src", "mall-service/src", "admin-backend/src"]
    pyproject.toml:12:    "admin-backend/tests",
    README.md:18:admin-web (Next.js :3001)
    README.md:19:  └── HTTP ──► admin-backend (:8003)
    README.md:27:- `admin-backend`：内部运营 API，聚合 `agent-service` 的对话、消息和定时总结。
    README.md:28:- `admin-web`：内部运营后台，提供对话列表和对话详情查看。
    README.md:58:uv run --package admin-backend admin-backend
    README.md:62:pnpm --dir admin-web install
    README.md:63:pnpm --dir admin-web dev
    README.md:66:打开 <http://localhost:3001>，默认进入 `/conversations`。`admin-backend` 默认只
    README.md:120:agent-service/prompts/conversation_summary.md
    README.md:166:pnpm --dir admin-web build
    README.md:194:反馈、明确表达的一般偏好以及未解决事项。`admin-web` 在对话详情页展示总结和完整
    README.md:198:记录在 `conversation_summary_worker.py` 的
    ✓ • 0ms

## Assistant

已新增轻量级运营后台模块。

`admin-backend` 默认运行在 `http://127.0.0.1:8003`，代理 `agent-service` 并聚合对话详情与总结：

- [admin-backend API](/Users/mindeng/workspace/niub-shangcheng/admin-backend/src/admin_backend/api.py)
- `GET /api/conversations`
- `GET /api/conversations/{conversation_id}`，返回对话详情和对应总结，尚未生成总结时返回 `summary: null`

`admin-web` 默认运行在 `http://localhost:3001`，默认进入对话管理：

- [对话列表](/Users/mindeng/workspace/niub-shangcheng/admin-web/app/conversations/page.tsx)：展示标题、消息数量、创建时间和更新时间。
- [对话详情](/Users/mindeng/workspace/niub-shangcheng/admin-web/app/conversations/[conversationId]/page.tsx)：展示完整消息，以及总结中的用户目标、约束、推荐商品、商品关键信息、终排理由、商品反馈、一般偏好和待处理事项。
- 总结尚未生成或已落后于对话最新时间时，会显示明确状态。

启动方式已补充到 [README.md](/Users/mindeng/workspace/niub-shangcheng/README.md)：

```bash
uv run --package admin-backend admin-backend
pnpm --dir admin-web dev
```

验证结果：

```text
uv run pytest -q        # 108 passed
pnpm --dir admin-web build  # 构建成功
pnpm --dir web build        # 构建成功
uv lock --check             # 通过
```

admin 后端测试使用 Mock Agent Service 覆盖列表、详情加总结、总结缺失、404 和服务不可用场景。当前模块定位为内部后台，没有实现登录与权限控制，默认只监听本机地址。

## User

好你在 admin 里面增加一个手动触发对话总结的功能，通过对话详情页来触发

## Assistant

我会把“手动触发”限制在 admin 内部链路：`admin-web` 发起服务端操作，调用 `admin-backend`，再由后者调用 `agent-service` 的 admin 专用生成接口。这样浏览器不直接接触 Agent 服务，现有公用的对话总结 GET 接口和定时任务逻辑也保持不变。

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/conversation_summary_worker.py
    @@ -3,3 +3,4 @@
     import os
    -from collections.abc import Callable
    +from collections.abc import AsyncIterator, Callable
    +from contextlib import asynccontextmanager
     from dataclasses import dataclass
    @@ -17,2 +18,3 @@
     from .llm_config import LLMConfig, load_llm_config
    +from .models import ConversationDetail, ConversationDigest
     from .storage import ConversationStore
    @@ -95,2 +97,59 @@
     
    +@asynccontextmanager
    +async def configured_conversation_summarizer(
    +    config_loader: Callable[[], LLMConfig] = load_llm_config,
    +) -> AsyncIterator[tuple[ConversationSummarizer, str]]:
    +    config = config_loader()
    +    client = AsyncOpenAI(
    +        api_key=config.api_key.get_secret_value(),
    +        base_url=normalize_openai_base_url(config.base_url),
    +        timeout=config.model_timeout_limit,
    +        max_retries=1,
    +    )
    +    try:
    +        model = OpenAIChatCompletionsModel(
    +            model=config.model,
    +            openai_client=client,
    +            buffer_streamed_tool_calls=True,
    +        )
    +        yield (
    +            AgentConversationSummarizer(config=config, model=model),
    +            config.model,
    +        )
    +    finally:
    +        await client.close()
    +
    +
    +async def summarize_and_store_conversation(
    +    store: ConversationStore,
    +    *,
    +    conversation: ConversationDetail,
    +    source_updated_at: str,
    +    summarizer: ConversationSummarizer,
    +    summarizer_model: str,
    +) -> ConversationDigest:
    +    try:
    +        digest = await summarizer.summarize(
    +            conversation=conversation,
    +            source_updated_at=source_updated_at,
    +        )
    +        store.save_conversation_summary(
    +            digest,
    +            prompt_version=CONVERSATION_SUMMARY_PROMPT_VERSION,
    +            summarizer_model=summarizer_model,
    +        )
    +        return digest
    +    except asyncio.CancelledError:
    +        raise
    +    except Exception as exc:
    +        store.record_conversation_summary_failure(
    +            conversation.id,
    +            source_updated_at=source_updated_at,
    +            prompt_version=CONVERSATION_SUMMARY_PROMPT_VERSION,
    +            summarizer_model=summarizer_model,
    +            error=f"{type(exc).__name__}: {exc}",
    +        )
    +        raise
    +
    +
     class ConversationSummaryWorker:
    @@ -137,70 +196,56 @@
     
    -        client: AsyncOpenAI | None = None
    -        summarizer = self.summarizer
    -        model_name = self.summarizer_model
    -        try:
    -            if summarizer is None:
    -                config = self.config_loader()
    -                client = AsyncOpenAI(
    -                    api_key=config.api_key.get_secret_value(),
    -                    base_url=normalize_openai_base_url(config.base_url),
    -                    timeout=config.model_timeout_limit,
    -                    max_retries=1,
    -                )
    -                model = OpenAIChatCompletionsModel(
    -                    model=config.model,
    -                    openai_client=client,
    -                    buffer_streamed_tool_calls=True,
    -                )
    -                summarizer = AgentConversationSummarizer(
    -                    config=config,
    -                    model=model,
    -                )
    -                model_name = config.model
    +        if self.summarizer is not None:
    +            return await self._run_candidates(
    +                candidates,
    +                summarizer=self.summarizer,
    +                model_name=self.summarizer_model or "injected-summarizer",
    +            )
    +        async with configured_conversation_summarizer(
    +            self.config_loader
    +        ) as (summarizer, model_name):
    +            return await self._run_candidates(
    +                candidates,
    +                summarizer=summarizer,
    +                model_name=model_name,
    +            )
     
    -            resolved_model_name = model_name or "injected-summarizer"
    -            completed = 0
    -            failed = 0
    -            skipped = 0
    -            for candidate in candidates:
    -                conversation = self.store.get_conversation(
    -                    candidate.user_id,
    +    async def _run_candidates(
    +        self,
    +        candidates: list,
    +        *,
    +        summarizer: ConversationSummarizer,
    +        model_name: str,
    +    ) -> ConversationSummaryCycleResult:
    +        completed = 0
    +        failed = 0
    +        skipped = 0
    +        for candidate in candidates:
    +            conversation = self.store.get_conversation(
    +                candidate.user_id,
    +                candidate.conversation_id,
    +            )
    +            if conversation is None:
    +                skipped += 1
    +                continue
    +            try:
    +                await summarize_and_store_conversation(
    +                    self.store,
    +                    conversation=conversation,
    +                    source_updated_at=candidate.updated_at,
    +                    summarizer=summarizer,
    +                    summarizer_model=model_name,
    +                )
    +                completed += 1
    +            except asyncio.CancelledError:
    +                raise
    +            except Exception:
    +                failed += 1
    +                logger.exception(
    +                    "conversation summary failed for %s",
                         candidate.conversation_id,
                     )
    -                if conversation is None:
    -                    skipped += 1
    -                    continue
    -                try:
    -                    digest = await summarizer.summarize(
    -                        conversation=conversation,
    -                        source_updated_at=candidate.updated_at,
    -                    )
    -                    self.store.save_conversation_summary(
    -                        digest,
    -                        prompt_version=CONVERSATION_SUMMARY_PROMPT_VERSION,
    -                        summarizer_model=resolved_model_name,
    -                    )
    -                    completed += 1
    -                except asyncio.CancelledError:
    -                    raise
    -                except Exception as exc:
    -                    failed += 1
    -                    logger.exception(
    -                        "conversation summary failed for %s",
    -                        candidate.conversation_id,
    -                    )
    -                    self.store.record_conversation_summary_failure(
    -                        candidate.conversation_id,
    -                        source_updated_at=candidate.updated_at,
    -                        prompt_version=CONVERSATION_SUMMARY_PROMPT_VERSION,
    -                        summarizer_model=resolved_model_name,
    -                        error=f"{type(exc).__name__}: {exc}",
    -                    )
    -            return ConversationSummaryCycleResult(
    -                completed=completed,
    -                failed=failed,
    -                skipped=skipped,
    -            )
    -        finally:
    -            if client is not None:
    -                await client.close()
    +        return ConversationSummaryCycleResult(
    +            completed=completed,
    +            failed=failed,
    +            skipped=skipped,
    +        )

## Activity

    $ sed -n '1,300p' agent-service/src/agent_service/conversation_summary_worker.py
    import asyncio
    import logging
    import os
    from collections.abc import AsyncIterator, Callable
    from contextlib import asynccontextmanager
    from dataclasses import dataclass
    from datetime import datetime, timedelta, timezone
    
    from agents import OpenAIChatCompletionsModel
    from openai import AsyncOpenAI
    
    from .agent_runner import normalize_openai_base_url
    from .conversation_summary import (
        CONVERSATION_SUMMARY_PROMPT_VERSION,
        AgentConversationSummarizer,
        ConversationSummarizer,
    )
    from .llm_config import LLMConfig, load_llm_config
    from .models import ConversationDetail, ConversationDigest
    from .storage import ConversationStore
    
    
    logger = logging.getLogger(__name__)
    
    DEFAULT_SUMMARY_INTERVAL_SECONDS = 3_600
    DEFAULT_SUMMARY_IDLE_SECONDS = 3_600
    DEFAULT_SUMMARY_BATCH_SIZE = 50
    
    
    # Scheduling assumption:
    # This worker does not acquire per-conversation locks or leases. The deployment
    # must guarantee exactly one scheduler invocation at a time, either through one
    # scheduler node or an external distributed scheduler. Concurrent execution for
    # the same conversation is explicitly out of scope.
    
    
    # TODO(conversation-summary-freshness):
    # A conversation has no usable summary until it has been idle long enough and
    # the next summary job has completed. Conversation recall must fall back to raw
    # completed turns whenever the digest is absent or stale.
    
    
    @dataclass(frozen=True)
    class ConversationSummarySettings:
        interval_seconds: int = DEFAULT_SUMMARY_INTERVAL_SECONDS
        idle_seconds: int = DEFAULT_SUMMARY_IDLE_SECONDS
        batch_size: int = DEFAULT_SUMMARY_BATCH_SIZE
        enabled: bool = True
    
    
    @dataclass(frozen=True)
    class ConversationSummaryCycleResult:
        completed: int = 0
        failed: int = 0
        skipped: int = 0
    
    
    def load_conversation_summary_settings() -> ConversationSummarySettings:
        return ConversationSummarySettings(
            interval_seconds=_positive_int_env(
                "CONVERSATION_SUMMARY_INTERVAL_SECONDS",
                DEFAULT_SUMMARY_INTERVAL_SECONDS,
            ),
            idle_seconds=_positive_int_env(
                "CONVERSATION_SUMMARY_IDLE_SECONDS",
                DEFAULT_SUMMARY_IDLE_SECONDS,
            ),
            batch_size=_positive_int_env(
                "CONVERSATION_SUMMARY_BATCH_SIZE",
                DEFAULT_SUMMARY_BATCH_SIZE,
            ),
            enabled=_bool_env("CONVERSATION_SUMMARY_SCHEDULER_ENABLED", True),
        )
    
    
    def _positive_int_env(name: str, default: int) -> int:
        value = os.getenv(name)
        if value is None:
            return default
        try:
            parsed = int(value)
        except ValueError:
            logger.warning("invalid %s=%r; using %s", name, value, default)
            return default
        if parsed <= 0:
            logger.warning("non-positive %s=%r; using %s", name, value, default)
            return default
        return parsed
    
    
    def _bool_env(name: str, default: bool) -> bool:
        value = os.getenv(name)
        if value is None:
            return default
        return value.strip().lower() not in {"0", "false", "no", "off"}
    
    
    @asynccontextmanager
    async def configured_conversation_summarizer(
        config_loader: Callable[[], LLMConfig] = load_llm_config,
    ) -> AsyncIterator[tuple[ConversationSummarizer, str]]:
        config = config_loader()
        client = AsyncOpenAI(
            api_key=config.api_key.get_secret_value(),
            base_url=normalize_openai_base_url(config.base_url),
            timeout=config.model_timeout_limit,
            max_retries=1,
        )
        try:
            model = OpenAIChatCompletionsModel(
                model=config.model,
                openai_client=client,
                buffer_streamed_tool_calls=True,
            )
            yield (
                AgentConversationSummarizer(config=config, model=model),
                config.model,
            )
        finally:
            await client.close()
    
    
    async def summarize_and_store_conversation(
        store: ConversationStore,
        *,
        conversation: ConversationDetail,
        source_updated_at: str,
        summarizer: ConversationSummarizer,
        summarizer_model: str,
    ) -> ConversationDigest:
        try:
            digest = await summarizer.summarize(
                conversation=conversation,
                source_updated_at=source_updated_at,
            )
            store.save_conversation_summary(
                digest,
                prompt_version=CONVERSATION_SUMMARY_PROMPT_VERSION,
                summarizer_model=summarizer_model,
            )
            return digest
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            store.record_conversation_summary_failure(
                conversation.id,
                source_updated_at=source_updated_at,
                prompt_version=CONVERSATION_SUMMARY_PROMPT_VERSION,
                summarizer_model=summarizer_model,
                error=f"{type(exc).__name__}: {exc}",
            )
            raise
    
    
    class ConversationSummaryWorker:
        def __init__(
            self,
            store: ConversationStore,
            *,
            settings: ConversationSummarySettings | None = None,
            summarizer: ConversationSummarizer | None = None,
            summarizer_model: str | None = None,
            config_loader: Callable[[], LLMConfig] = load_llm_config,
        ) -> None:
            self.store = store
            self.settings = settings or load_conversation_summary_settings()
            self.summarizer = summarizer
            self.summarizer_model = summarizer_model
            self.config_loader = config_loader
    
        async def run_forever(self) -> None:
            while True:
                try:
                    await self.run_once()
                except asyncio.CancelledError:
                    raise
                except Exception:
                    logger.exception("conversation summary cycle failed")
                await asyncio.sleep(self.settings.interval_seconds)
    
        async def run_once(
            self,
            *,
            now: datetime | None = None,
        ) -> ConversationSummaryCycleResult:
            current_time = now or datetime.now(timezone.utc)
            cutoff = (current_time - timedelta(
                seconds=self.settings.idle_seconds
            )).isoformat(timespec="milliseconds")
            candidates = self.store.list_conversations_due_for_summary(
                cutoff,
                limit=self.settings.batch_size,
            )
            if not candidates:
                return ConversationSummaryCycleResult()
    
            if self.summarizer is not None:
                return await self._run_candidates(
                    candidates,
                    summarizer=self.summarizer,
                    model_name=self.summarizer_model or "injected-summarizer",
                )
            async with configured_conversation_summarizer(
                self.config_loader
            ) as (summarizer, model_name):
                return await self._run_candidates(
                    candidates,
                    summarizer=summarizer,
                    model_name=model_name,
                )
    
        async def _run_candidates(
            self,
            candidates: list,
            *,
            summarizer: ConversationSummarizer,
            model_name: str,
        ) -> ConversationSummaryCycleResult:
            completed = 0
            failed = 0
            skipped = 0
            for candidate in candidates:
                conversation = self.store.get_conversation(
                    candidate.user_id,
                    candidate.conversation_id,
                )
                if conversation is None:
                    skipped += 1
                    continue
                try:
                    await summarize_and_store_conversation(
                        self.store,
                        conversation=conversation,
                        source_updated_at=candidate.updated_at,
                        summarizer=summarizer,
                        summarizer_model=model_name,
                    )
                    completed += 1
                except asyncio.CancelledError:
                    raise
                except Exception:
                    failed += 1
                    logger.exception(
                        "conversation summary failed for %s",
                        candidate.conversation_id,
                    )
            return ConversationSummaryCycleResult(
                completed=completed,
                failed=failed,
                skipped=skipped,
            )
    ✓ • 0ms

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/conversation_summary_worker.py
    @@ -19,3 +19,3 @@
     from .models import ConversationDetail, ConversationDigest
    -from .storage import ConversationStore
    +from .storage import ConversationStore, ConversationSummaryCandidate
     
    @@ -213,3 +213,3 @@
             self,
    -        candidates: list,
    +        candidates: list[ConversationSummaryCandidate],
             *,

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/api.py
    @@ -12,3 +12,5 @@
         ConversationSummaryWorker,
    +    configured_conversation_summarizer,
         load_conversation_summary_settings,
    +    summarize_and_store_conversation,
     )
    @@ -476,2 +478,41 @@
     
    +@app.post(
    +    "/api/admin/conversations/{conversation_id}/summary",
    +    response_model=ConversationDigest,
    +)
    +async def trigger_conversation_summary(
    +    conversation_id: str,
    +    store: ConversationStore = Depends(get_conversation_store),
    +) -> ConversationDigest:
    +    conversation = store.get_conversation(FIXED_USER_ID, conversation_id)
    +    if conversation is None:
    +        raise HTTPException(status_code=404, detail="对话不存在")
    +    try:
    +        async with configured_conversation_summarizer() as (
    +            summarizer,
    +            summarizer_model,
    +        ):
    +            return await summarize_and_store_conversation(
    +                store,
    +                conversation=conversation,
    +                source_updated_at=conversation.updated_at,
    +                summarizer=summarizer,
    +                summarizer_model=summarizer_model,
    +            )
    +    except LLMConfigError as exc:
    +        raise HTTPException(
    +            status_code=503,
    +            detail=f"总结模型配置不可用：{exc}",
    +        ) from exc
    +    except Exception as exc:
    +        logger.exception(
    +            "manual conversation summary failed for %s",
    +            conversation_id,
    +        )
    +        raise HTTPException(
    +            status_code=502,
    +            detail="对话总结生成失败，请稍后重试",
    +        ) from exc
    +
    +
     @app.post("/api/chat", response_model=ChatResponse)

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/agent-service/tests/test_agent_api.py
    @@ -1 +1,2 @@
    +from contextlib import asynccontextmanager
     from pathlib import Path
    @@ -544,2 +545,47 @@
     
    +def test_admin_can_manually_generate_conversation_summary(
    +    store: ConversationStore,
    +    monkeypatch: pytest.MonkeyPatch,
    +) -> None:
    +    conversation_id = store.create_conversation(1, "手动总结")
    +    store.add_message(conversation_id, "user", "推荐一个通勤包", "completed")
    +    store.add_message(
    +        conversation_id,
    +        "assistant",
    +        "推荐这款轻量通勤包。",
    +        "completed",
    +    )
    +    conversation = store.get_conversation(1, conversation_id)
    +    assert conversation is not None
    +
    +    class FakeSummarizer:
    +        async def summarize(self, *, conversation, source_updated_at):
    +            return ConversationDigest(
    +                conversation_id=conversation.id,
    +                source_updated_at=source_updated_at,
    +                summary="用户正在寻找通勤包。",
    +                generated_at="2026-11-13T04:00:00.000+00:00",
    +            )
    +
    +    @asynccontextmanager
    +    async def fake_summarizer_factory():
    +        yield FakeSummarizer(), "test-summary-model"
    +
    +    monkeypatch.setattr(
    +        api_module,
    +        "configured_conversation_summarizer",
    +        fake_summarizer_factory,
    +    )
    +
    +    response = client.post(
    +        f"/api/admin/conversations/{conversation_id}/summary"
    +    )
    +
    +    assert response.status_code == 200
    +    assert response.json()["summary"] == "用户正在寻找通勤包。"
    +    stored = store.get_conversation_summary(1, conversation_id)
    +    assert stored is not None
    +    assert stored.source_updated_at == conversation.updated_at
    +
    +
     def test_unknown_conversation_returns_404(store: ConversationStore) -> None:

## Activity

    file changes: Completed · 2 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/admin-backend/src/admin_backend/agent_client.py
    @@ -79 +79,17 @@
             return payload
    +
    +    async def trigger_conversation_summary(
    +        self,
    +        conversation_id: str,
    +    ) -> object | None:
    +        status, payload = await self._request(
    +            "POST",
    +            f"/api/admin/conversations/{quote(conversation_id, safe='')}/summary",
    +        )
    +        if status == 404:
    +            return None
    +        if status != 200:
    +            raise AgentServiceError(
    +                f"agent service manual summary returned HTTP {status}"
    +            )
    +        return payload
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/admin-backend/src/admin_backend/api.py
    @@ -60 +60,18 @@
         }
    +
    +
    +@app.post("/api/conversations/{conversation_id}/summary")
    +async def trigger_conversation_summary(
    +    conversation_id: str,
    +    client: AgentServiceClient = Depends(get_agent_service_client),
    +) -> object:
    +    try:
    +        summary = await client.trigger_conversation_summary(conversation_id)
    +    except AgentServiceError as exc:
    +        raise HTTPException(
    +            status_code=502,
    +            detail="对话总结生成失败",
    +        ) from exc
    +    if summary is None:
    +        raise HTTPException(status_code=404, detail="对话不存在")
    +    return summary

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/admin-backend/tests/test_admin_api.py
    @@ -149 +149,39 @@
         assert response.status_code == 502
    +
    +
    +def test_manual_summary_trigger_proxies_to_agent_admin_endpoint() -> None:
    +    def handler(request: httpx.Request) -> httpx.Response:
    +        assert request.method == "POST"
    +        assert (
    +            request.url.path
    +            == "/api/admin/conversations/conversation-1/summary"
    +        )
    +        return httpx.Response(200, json=CONVERSATION_SUMMARY)
    +
    +    app.dependency_overrides[get_agent_service_client] = lambda: (
    +        _override_client(httpx.MockTransport(handler))
    +    )
    +    try:
    +        response = client.post(
    +            "/api/conversations/conversation-1/summary"
    +        )
    +    finally:
    +        app.dependency_overrides.clear()
    +
    +    assert response.status_code == 200
    +    assert response.json()["summary"] == "用户寻找适合通勤的包。"
    +
    +
    +def test_manual_summary_trigger_rejects_unknown_conversation() -> None:
    +    def handler(request: httpx.Request) -> httpx.Response:
    +        return httpx.Response(404, json={"detail": "对话不存在"})
    +
    +    app.dependency_overrides[get_agent_service_client] = lambda: (
    +        _override_client(httpx.MockTransport(handler))
    +    )
    +    try:
    +        response = client.post("/api/conversations/missing/summary")
    +    finally:
    +        app.dependency_overrides.clear()
    +
    +    assert response.status_code == 404

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/admin-web/lib/admin-api.ts
    @@ -19,5 +19,9 @@
     
    -async function adminFetch<T>(path: string): Promise<T> {
    +async function adminFetch<T>(
    +  path: string,
    +  init?: RequestInit,
    +): Promise<T> {
       const response = await fetch(`${adminBackendUrl}${path}`, {
         cache: "no-store",
    +    ...init,
       });
    @@ -58 +62,10 @@
     }
    +
    +export async function triggerConversationSummary(
    +  conversationId: string,
    +): Promise<void> {
    +  await adminFetch(
    +    `/api/conversations/${encodeURIComponent(conversationId)}/summary`,
    +    { method: "POST" },
    +  );
    +}

## Activity

    file changes: Completed · 2 changes
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-web/app/conversations/[conversationId]/actions.ts
    "use server";
    
    import { revalidatePath } from "next/cache";
    
    import {
      AdminApiError,
      triggerConversationSummary,
    } from "@/lib/admin-api";
    
    export interface TriggerSummaryState {
      status: "idle" | "success" | "error";
      message: string;
    }
    
    export async function triggerSummaryAction(
      _previousState: TriggerSummaryState,
      formData: FormData,
    ): Promise<TriggerSummaryState> {
      const conversationId = formData.get("conversationId");
      if (typeof conversationId !== "string" || !conversationId) {
        return {
          status: "error",
          message: "缺少对话 ID，无法生成总结。",
        };
      }
    
      try {
        await triggerConversationSummary(conversationId);
        revalidatePath(`/conversations/${conversationId}`);
        revalidatePath("/conversations");
        return {
          status: "success",
          message: "对话总结已生成并更新。",
        };
      } catch (error) {
        return {
          status: "error",
          message:
            error instanceof AdminApiError
              ? error.message
              : "总结生成失败，请稍后重试。",
        };
      }
    }
    Add: /Users/mindeng/workspace/niub-shangcheng/admin-web/app/conversations/[conversationId]/trigger-summary-button.tsx
    "use client";
    
    import { useActionState } from "react";
    
    import {
      triggerSummaryAction,
      type TriggerSummaryState,
    } from "./actions";
    
    const initialState: TriggerSummaryState = {
      status: "idle",
      message: "",
    };
    
    export function TriggerSummaryButton({
      conversationId,
      hasSummary,
    }: {
      conversationId: string;
      hasSummary: boolean;
    }) {
      const [state, formAction, pending] = useActionState(
        triggerSummaryAction,
        initialState,
      );
    
      return (
        <form className="summary-trigger" action={formAction}>
          <input
            type="hidden"
            name="conversationId"
            value={conversationId}
          />
          <button type="submit" disabled={pending}>
            {pending
              ? "正在生成总结…"
              : hasSummary
                ? "重新生成总结"
                : "立即生成总结"}
          </button>
          {state.message ? (
            <span
              className={`trigger-message trigger-message--${state.status}`}
              role="status"
            >
              {state.message}
            </span>
          ) : null}
        </form>
      );
    }

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/admin-web/app/conversations/[conversationId]/page.tsx
    @@ -9,2 +9,3 @@
     } from "@/lib/types";
    +import { TriggerSummaryButton } from "./trigger-summary-button";
     
    @@ -136,12 +137,18 @@
               </div>
    -          {summary ? (
    -            <div className="summary-heading-meta">
    -              {!summaryIsCurrent ? (
    -                <span className="summary-stale">等待重新生成</span>
    -              ) : null}
    -              <span className="summary-time">
    -                生成于 {formatFullDate(summary.generated_at)}
    -              </span>
    -            </div>
    -          ) : null}
    +          <div className="summary-heading-actions">
    +            {summary ? (
    +              <div className="summary-heading-meta">
    +                {!summaryIsCurrent ? (
    +                  <span className="summary-stale">等待重新生成</span>
    +                ) : null}
    +                <span className="summary-time">
    +                  生成于 {formatFullDate(summary.generated_at)}
    +                </span>
    +              </div>
    +            ) : null}
    +            <TriggerSummaryButton
    +              conversationId={conversation.id}
    +              hasSummary={summary !== null}
    +            />
    +          </div>
             </div>

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/admin-web/app/globals.css
    @@ -267,2 +267,57 @@
     
    +.summary-heading-actions {
    +  display: flex;
    +  align-items: center;
    +  flex-wrap: wrap;
    +  justify-content: flex-end;
    +  gap: 10px;
    +}
    +
    +.summary-trigger {
    +  display: flex;
    +  align-items: center;
    +  flex-wrap: wrap;
    +  justify-content: flex-end;
    +  gap: 9px;
    +}
    +
    +.summary-trigger button {
    +  min-width: 116px;
    +  padding: 9px 13px;
    +  color: white;
    +  border: 0;
    +  border-radius: 2px;
    +  background: var(--green);
    +  cursor: pointer;
    +  font-size: 10px;
    +  font-weight: 800;
    +  transition:
    +    background 150ms ease,
    +    opacity 150ms ease;
    +}
    +
    +.summary-trigger button:hover:not(:disabled) {
    +  background: #163d2b;
    +}
    +
    +.summary-trigger button:disabled {
    +  cursor: wait;
    +  opacity: 0.58;
    +}
    +
    +.trigger-message {
    +  max-width: 230px;
    +  color: var(--muted);
    +  font-size: 9px;
    +  line-height: 1.5;
    +}
    +
    +.trigger-message--success {
    +  color: #276b45;
    +}
    +
    +.trigger-message--error {
    +  color: var(--danger);
    +}
    +
     .summary-stale {
    @@ -995,2 +1050,9 @@
     
    +  .summary-heading-actions,
    +  .summary-trigger {
    +    width: 100%;
    +    align-items: flex-start;
    +    justify-content: flex-start;
    +  }
    +
       th:nth-child(3),

## Activity

    file changes: Completed · 1 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/README.md
    @@ -151,4 +151,6 @@
     - 对话总结：`GET http://localhost:8002/api/conversations/{conversation_id}/summary`
    +- Admin 手动生成总结：`POST http://localhost:8002/api/admin/conversations/{conversation_id}/summary`
     - Admin 对话列表：`GET http://localhost:8003/api/conversations`
     - Admin 对话详情及总结：`GET http://localhost:8003/api/conversations/{conversation_id}`
    +- Admin 手动生成总结：`POST http://localhost:8003/api/conversations/{conversation_id}/summary`
     
    @@ -188,5 +190,6 @@
     
    -`agent-service` 每小时扫描一次，只总结超过一小时没有更新、且时间戳表明内容发生
    -变化的对话。对话被重新使用后，下一次满足闲置条件的扫描会重新生成并替换当前
    -总结。总结任务不提供用户主动触发接口。
    +`agent-service` 每小时扫描一次，只自动总结超过一小时没有更新、且时间戳表明内容
    +发生变化的对话。对话被重新使用后，下一次满足闲置条件的扫描会重新生成并替换当前
    +总结。商城用户没有主动触发接口；运营人员可以在 admin 对话详情页手动生成或重新
    +生成总结。
     

## Activity

    $ git diff --check
    ✓ • 0ms

## Activity

    $ uv run pytest agent-service/tests/test_agent_api.py admin-backend/tests/test_admin_api.py agent-service/tests/test_conversation_summary_worker.py -q
    ........................                                                 [100%]
    24 passed in 0.98s
    ✓ • 1.33s

## Activity

    $ pnpm build
    
    > niub-admin-web@0.1.0 build /Users/mindeng/workspace/niub-shangcheng/admin-web
    > next build
    
       ▲ Next.js 15.5.29
    
       Creating an optimized production build ...
     ✓ Compiled successfully in 1564ms
       Linting and checking validity of types ...
       Collecting page data ...
       Generating static pages (0/4) ...
       Generating static pages (1/4)
       Generating static pages (2/4)
       Generating static pages (3/4)
     ✓ Generating static pages (4/4)
       Finalizing page optimization ...
       Collecting build traces ...
    
    Route (app)                                 Size  First Load JS
    ┌ ○ /                                      127 B         102 kB
    ├ ○ /_not-found                            127 B         102 kB
    ├ ƒ /conversations                         164 B         105 kB
    └ ƒ /conversations/[conversationId]        771 B         106 kB
    + First Load JS shared by all             102 kB
      ├ chunks/0453825f-c8a6ffc8aac4ea8b.js  54.2 kB
      ├ chunks/708-f76e100034acd83a.js       45.8 kB
      └ other shared chunks (total)           1.9 kB
    
    
    ○  (Static)   prerendered as static content
    ƒ  (Dynamic)  server-rendered on demand
    
    ✓ • 8.10s

## Assistant

手动触发链路已贯通：详情页按钮通过 Next.js Server Action 调用 admin 后端，再由 admin 后端调用 Agent 的 admin 专用接口生成并保存总结，成功后自动刷新详情页。现在做完整回归并核对错误状态。

## Activity

    $ uv run python -m compileall -q agent-service/src admin-backend/src
    ✓ • 0ms

## Activity

    $ rg -n "POST /api/admin|手动生成|立即生成总结|重新生成总结|trigger_conversation_summary" README.md agent-service/src admin-backend/src admin-web | sed -n '1,240p'
    README.md:152:- Admin 手动生成总结：`POST http://localhost:8002/api/admin/conversations/{conversation_id}/summary`
    README.md:155:- Admin 手动生成总结：`POST http://localhost:8003/api/conversations/{conversation_id}/summary`
    README.md:193:总结。商城用户没有主动触发接口；运营人员可以在 admin 对话详情页手动生成或重新
    admin-backend/src/admin_backend/api.py:64:async def trigger_conversation_summary(
    admin-backend/src/admin_backend/api.py:69:        summary = await client.trigger_conversation_summary(conversation_id)
    admin-backend/src/admin_backend/agent_client.py:81:    async def trigger_conversation_summary(
    agent-service/src/agent_service/api.py:483:async def trigger_conversation_summary(
    admin-web/app/conversations/[conversationId]/trigger-summary-button.tsx:38:            ? "重新生成总结"
    admin-web/app/conversations/[conversationId]/trigger-summary-button.tsx:39:            : "立即生成总结"}
    ✓ • 0ms

## Activity

    $ uv run pytest -q
    ........................................................................ [ 64%]
    .......................................                                  [100%]
    111 passed in 1.50s
    ✓ • 1.85s

## Activity

    file changes: Completed · 3 changes
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/admin-backend/.env.example
    @@ -4 +4,2 @@
     AGENT_SERVICE_TIMEOUT_SECONDS=10
    +AGENT_SERVICE_SUMMARY_TIMEOUT_SECONDS=1800
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/admin-backend/src/admin_backend/agent_client.py
    @@ -15,2 +15,3 @@
             timeout_seconds: float = 10.0,
    +        summary_timeout_seconds: float = 1_800.0,
             transport: httpx.AsyncBaseTransport | None = None,
    @@ -19,2 +20,3 @@
             self.timeout_seconds = timeout_seconds
    +        self.summary_timeout_seconds = summary_timeout_seconds
             self.transport = transport
    @@ -25,2 +27,4 @@
             path: str,
    +        *,
    +        timeout_seconds: float | None = None,
         ) -> tuple[int, object]:
    @@ -29,3 +33,3 @@
                     base_url=self.base_url,
    -                timeout=self.timeout_seconds,
    +                timeout=timeout_seconds or self.timeout_seconds,
                     transport=self.transport,
    @@ -87,2 +91,3 @@
                 f"/api/admin/conversations/{quote(conversation_id, safe='')}/summary",
    +            timeout_seconds=self.summary_timeout_seconds,
             )
    Update { move_path: None }: /Users/mindeng/workspace/niub-shangcheng/admin-backend/src/admin_backend/api.py
    @@ -18,2 +18,5 @@
             timeout_seconds=float(os.getenv("AGENT_SERVICE_TIMEOUT_SECONDS", "10")),
    +        summary_timeout_seconds=float(
    +            os.getenv("AGENT_SERVICE_SUMMARY_TIMEOUT_SECONDS", "1800")
    +        ),
         )

## Activity

    $ git diff --check && uv lock --check
    Resolved 72 packages in 6ms
    ✓ • 0ms

## Activity

    $ uv run pytest -q
    ........................................................................ [ 64%]
    .......................................                                  [100%]
    111 passed in 1.58s
    ✓ • 1.94s

## Activity

    $ pnpm build
    
    > niub-admin-web@0.1.0 build /Users/mindeng/workspace/niub-shangcheng/admin-web
    > next build
    
       ▲ Next.js 15.5.29
    
       Creating an optimized production build ...
     ✓ Compiled successfully in 790ms
       Linting and checking validity of types ...
       Collecting page data ...
       Generating static pages (0/4) ...
       Generating static pages (1/4)
       Generating static pages (2/4)
       Generating static pages (3/4)
     ✓ Generating static pages (4/4)
       Finalizing page optimization ...
       Collecting build traces ...
    
    Route (app)                                 Size  First Load JS
    ┌ ○ /                                      127 B         102 kB
    ├ ○ /_not-found                            127 B         102 kB
    ├ ƒ /conversations                         164 B         105 kB
    └ ƒ /conversations/[conversationId]        771 B         106 kB
    + First Load JS shared by all             102 kB
      ├ chunks/0453825f-c8a6ffc8aac4ea8b.js  54.2 kB
      ├ chunks/708-f76e100034acd83a.js       45.8 kB
      └ other shared chunks (total)           1.9 kB
    
    
    ○  (Static)   prerendered as static content
    ƒ  (Dynamic)  server-rendered on demand
    
    ✓ • 7.23s

## Assistant

已在 admin 对话详情页增加手动总结功能。

交互流程：

```text
对话详情页按钮
  → Next.js Server Action
  → admin-backend
  → agent-service admin 专用接口
  → 总结模型
  → 保存总结并刷新详情页
```

实现内容：

- [详情页按钮](/Users/mindeng/workspace/niub-shangcheng/admin-web/app/conversations/[conversationId]/trigger-summary-button.tsx)：根据状态显示“立即生成总结”或“重新生成总结”，生成期间禁用按钮并展示进度。
- [Server Action](/Users/mindeng/workspace/niub-shangcheng/admin-web/app/conversations/[conversationId]/actions.ts)：调用 admin 后端，成功后刷新列表和详情页路由。
- [admin-backend 接口](/Users/mindeng/workspace/niub-shangcheng/admin-backend/src/admin_backend/api.py)：新增 `POST /api/conversations/{conversation_id}/summary`。
- [agent-service admin 接口](/Users/mindeng/workspace/niub-shangcheng/agent-service/src/agent_service/api.py)：新增 `POST /api/admin/conversations/{conversation_id}/summary`，直接使用当前对话内容生成并保存总结，不要求对话已闲置一小时。
- 手动总结的代理超时默认单独设置为 1800 秒，避免长模型调用被普通查询的 10 秒超时中断。
- 原有商城用户接口仍然没有手动触发能力；只开放给 admin 内部链路。

验证结果：

```text
uv run pytest -q          # 111 passed
pnpm --dir admin-web build  # 构建成功
uv lock --check             # 通过
```

测试覆盖了手动触发成功、总结落库、admin 代理转发、未知对话返回 404 等场景；真实 LLM 的生成仍使用现有 `agent-service` 模型配置。
