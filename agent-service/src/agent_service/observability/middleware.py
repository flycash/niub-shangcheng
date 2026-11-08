import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from opentelemetry import trace

from .config import ObservabilityConfig
from .context import bind_request_context, new_request_context


logger = logging.getLogger(__name__)


class RequestLifecycleMiddleware:
    def __init__(
        self,
        app: Callable[..., Awaitable[None]],
        config: ObservabilityConfig,
    ) -> None:
        self.app = app
        self.config = config

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            key.decode("latin1").lower(): value.decode("latin1")
            for key, value in scope.get("headers", [])
        }
        supplied_request_id = headers.get("x-request-id", "").strip()
        request_id = (
            supplied_request_id[:128]
            if supplied_request_id
            else None
        )
        request = new_request_context(
            scope.get("method", ""),
            scope.get("path", ""),
            request_id,
        )
        started = time.monotonic()
        status_code = 500
        response_bytes = 0
        response_started = False
        body_completed = False
        failed = False

        async def observed_send(message: dict[str, Any]) -> None:
            nonlocal status_code
            nonlocal response_bytes
            nonlocal response_started
            nonlocal body_completed
            message_type = message.get("type")
            if message_type == "http.response.start":
                response_started = True
                status_code = int(message.get("status", 500))
                response_headers = list(message.get("headers", []))
                if not any(
                    key.lower() == b"x-request-id"
                    for key, _ in response_headers
                ):
                    response_headers.append(
                        (b"x-request-id", request.request_id.encode())
                    )
                message["headers"] = response_headers
            elif message_type == "http.response.body":
                response_bytes += len(message.get("body", b""))
                body_completed = not bool(message.get("more_body", False))
            await send(message)

        with bind_request_context(request):
            try:
                await self.app(scope, receive, observed_send)
            except BaseException:
                failed = True
                raise
            finally:
                if self.config.logs.enabled and self.config.logs.access_log:
                    span_context = trace.get_current_span().get_span_context()
                    logger.info(
                        "HTTP request completed",
                        extra={
                            "event": "http.request.completed",
                            "http.method": scope.get("method", ""),
                            "http.route": scope.get("path", ""),
                            "http.status_code": status_code,
                            "http.response_started": response_started,
                            "http.response_completed": body_completed,
                            "http.response_bytes": response_bytes,
                            "duration_ms": round(
                                (time.monotonic() - started) * 1000,
                                3,
                            ),
                            "outcome": "failed" if failed else "completed",
                            "otel.trace_id": (
                                format(span_context.trace_id, "032x")
                                if span_context.is_valid
                                else ""
                            ),
                        },
                    )
