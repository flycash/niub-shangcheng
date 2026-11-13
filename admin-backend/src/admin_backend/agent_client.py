from urllib.parse import quote

import httpx


class AgentServiceError(Exception):
    """Raised when the agent service cannot provide the requested data."""


class AgentServiceClient:
    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float = 10.0,
        summary_timeout_seconds: float = 1_800.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.summary_timeout_seconds = summary_timeout_seconds
        self.transport = transport

    async def _request(
        self,
        method: str,
        path: str,
        *,
        timeout_seconds: float | None = None,
    ) -> tuple[int, object]:
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=timeout_seconds or self.timeout_seconds,
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
            f"/api/conversations/{quote(conversation_id, safe='')}",
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
            f"/api/conversations/{quote(conversation_id, safe='')}/summary",
        )
        if status == 404:
            return None
        if status != 200:
            raise AgentServiceError(
                f"agent service conversation summary returned HTTP {status}"
            )
        return payload

    async def trigger_conversation_summary(
        self,
        conversation_id: str,
    ) -> object | None:
        status, payload = await self._request(
            "POST",
            f"/api/admin/conversations/{quote(conversation_id, safe='')}/summary",
            timeout_seconds=self.summary_timeout_seconds,
        )
        if status == 404:
            return None
        if status != 200:
            raise AgentServiceError(
                f"agent service manual summary returned HTTP {status}"
            )
        return payload
