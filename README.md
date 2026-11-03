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
agent-service/prompts/recommendation_reranker.md
```

主 Agent 和语义终排 Agent 各自在所属模块中声明 Prompt 路径，并通过
[`prompt_loader.py`](agent-service/src/agent_service/prompt_loader.py)
提供的通用 `load_prompt(path)` 读取文件。YAML 不保存 Prompt 路径。提示词在每次
请求时重新读取，因此修改 Markdown 后下一轮对话立即生效，不需要重启服务。提示词
文件限制为 UTF-8、内容非空且不超过 64 KiB。

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
- `recommend_products`：并行读取画像、浏览、订单、购物车和两路候选，按统一
  公式生成自然商品 Top 10 与广告 Top 3，并执行阈值分路。
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

所有记录和广告 Mock 数据均位于 `mall-service`。自然推荐和广告分别使用统一公式
评分；广告最高分严格高于自然 Top 10 最低分时，最多三个达标广告与自然候选一起
进入独立语义终排。最终最多两个自然商品和一个广告，存在自然商品时广告不能排在
第一位；只有自然候选为空时才允许广告单独出现。广告由服务端添加“广告”标识。
没有合格商品时，Agent 会建议用户去其他平台购买。SSE 会发送 `tool_started`、
`tool_completed`、`recommendations`、`delta` 和 `done` 事件。终排完成后，工具
结果会返回主 Agent，由主 Agent 继续生成最终文字回答，并在文字后展示可点击的
商品卡片。推荐商品同时作为内部元数据保存，以支持“第一个商品”等后续指代和下单。

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
