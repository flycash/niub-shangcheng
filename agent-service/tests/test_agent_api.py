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


async def fake_agent_stream(
    messages,
    config,
    mall,
    previous_plan_state=None,
    previous_recommendations=None,
    previous_orders=None,
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
    ):
        captured["plan_state"] = previous_plan_state
        captured["previous_recommendations"] = previous_recommendations
        captured["previous_orders"] = previous_orders
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
