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
                              └── Mock Mall tools
```

- `mall-service`：商城商品目录和 HTTP API。
- `agent-service`：基于 OpenAI Agents SDK 的商城导购 Agent，通过工具调用
  Mock 商城搜索和查询商品。
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
```

YAML 只配置提示词文件路径：

```yaml
llm:
  prompt_file: "../prompts/shopping_agent.md"
```

相对路径以 `llm.yaml` 所在目录为基准，也可以填写绝对路径。提示词在每次 Agent
请求开始时重新读取，因此修改 Markdown 后下一轮对话立即生效，不需要重启服务。

提示词文件限制为 UTF-8、内容非空且不超过 64 KiB。旧的
`system_prompt` 配置暂时兼容，但会产生弃用警告；配置了 `prompt_file` 时优先
使用文件内容。

## 服务接口

- 商城健康检查：`GET http://localhost:8001/health`
- 商品列表：`GET http://localhost:8001/api/products`
- 商品详情：`GET http://localhost:8001/api/products/{product_id}`
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
支持自定义 `base_url` 和 API Key。Runner 会自动执行 ReAct 循环：模型选择
`search_products` 或 `get_product`，Agent 执行 Mock 商城工具，然后把工具结果
交回模型生成最终回复。`/api/chat` 暂时保留为商城首页使用的本地规则接口。

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

当前工具：

- `search_products`：按关键词、分类、价格区间搜索商品。
- `get_product`：按商品 ID 查询价格、库存和描述。

Mock 商城数据位于
`agent-service/src/agent_service/mock_mall.py`。SSE 会额外发送
`tool_started`、`tool_completed` 和 `recommendations` 事件。推荐商品卡片与工具
轨迹会随助手消息保存，并在历史对话中恢复。

每个 Agent 请求最多执行 `max_turns` 个模型/工具回合，单个工具默认超时 8 秒。
Agents SDK 的远程 tracing 已关闭，以避免把 DeepSeek 对话发送到 OpenAI tracing
服务。
