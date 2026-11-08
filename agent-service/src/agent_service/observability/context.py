import contextvars
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator
from uuid import uuid4


@dataclass(frozen=True)
class RequestContext:
    request_id: str
    method: str
    path: str
    trace_id: str = ""


_request_context: contextvars.ContextVar[RequestContext | None] = (
    contextvars.ContextVar("agent_service_request_context", default=None)
)


def new_request_context(
    method: str,
    path: str,
    request_id: str | None = None,
) -> RequestContext:
    return RequestContext(
        request_id=request_id or f"req-{uuid4().hex}",
        method=method,
        path=path,
    )


def get_request_context() -> RequestContext | None:
    return _request_context.get()


@contextmanager
def bind_request_context(request: RequestContext) -> Iterator[None]:
    token = _request_context.set(request)
    try:
        yield
    finally:
        _request_context.reset(token)
