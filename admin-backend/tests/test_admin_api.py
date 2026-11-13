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


def test_manual_summary_trigger_proxies_to_agent_admin_endpoint() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert (
            request.url.path
            == "/api/admin/conversations/conversation-1/summary"
        )
        return httpx.Response(200, json=CONVERSATION_SUMMARY)

    app.dependency_overrides[get_agent_service_client] = lambda: (
        _override_client(httpx.MockTransport(handler))
    )
    try:
        response = client.post(
            "/api/conversations/conversation-1/summary"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["summary"] == "用户寻找适合通勤的包。"


def test_manual_summary_trigger_rejects_unknown_conversation() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "对话不存在"})

    app.dependency_overrides[get_agent_service_client] = lambda: (
        _override_client(httpx.MockTransport(handler))
    )
    try:
        response = client.post("/api/conversations/missing/summary")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
