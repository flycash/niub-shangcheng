import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Iterator

from opentelemetry import trace
from opentelemetry.context import attach, detach
from opentelemetry.trace import Span, Status, StatusCode

from .metrics import ObservabilityMetrics
from .serialization import json_safe


_tracer: trace.Tracer = trace.get_tracer("agent-service")
_metrics: ObservabilityMetrics | None = None


def set_observability_clients(
    *,
    tracer: trace.Tracer,
) -> None:
    global _tracer
    _tracer = tracer


def get_tracer() -> trace.Tracer:
    return _tracer


def get_runtime_metrics() -> ObservabilityMetrics | None:
    from .metrics import get_metrics

    return get_metrics()


def _duration_seconds(start_ns: int, end_ns: int | None = None) -> float:
    return max(0, (end_ns or time.monotonic_ns()) - start_ns) / 1_000_000_000


@dataclass
class ChatObservation:
    conversation_id: str = ""
    turn_id: str = ""
    start_ns: int = field(default_factory=time.monotonic_ns)
    span: Span = field(init=False)
    _ended: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.span = _tracer.start_span("agent.chat")
        self.span.set_attribute("agent.chat.kind", "stream")
        if self.conversation_id:
            self.span.set_attribute(
                "agent.conversation.id",
                self.conversation_id,
            )
        if self.turn_id:
            self.span.set_attribute("agent.turn.id", self.turn_id)

    def set_conversation(
        self,
        *,
        conversation_id: str,
        turn_id: str,
    ) -> None:
        self.conversation_id = conversation_id
        self.turn_id = turn_id
        self.span.set_attribute(
            "agent.conversation.id",
            conversation_id,
        )
        self.span.set_attribute("agent.turn.id", turn_id)

    @contextmanager
    def active(self) -> Iterator[None]:
        with trace.use_span(self.span, end_on_exit=False):
            yield

    def attach(self) -> object:
        return attach(trace.set_span_in_context(self.span))

    @staticmethod
    def detach(token: object) -> None:
        detach(token)

    def end(
        self,
        outcome: str,
        *,
        error: BaseException | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        if self._ended:
            return
        self._ended = True
        duration = _duration_seconds(self.start_ns)
        self.span.set_attribute("agent.chat.outcome", outcome)
        self.span.set_attribute("agent.chat.duration_ms", duration * 1000)
        for key, value in (attributes or {}).items():
            self.span.set_attribute(key, json_safe(value))
        if outcome == "failed" and error is not None:
            self.span.record_exception(error)
            self.span.set_status(
                Status(StatusCode.ERROR, str(error))
            )
        else:
            self.span.set_status(Status(StatusCode.OK))
        self.span.end()

        runtime_metrics = get_runtime_metrics()
        if runtime_metrics is not None:
            runtime_metrics.chat_duration.record(
                duration,
                {"outcome": outcome},
            )
            runtime_metrics.chat_requests.add(
                1,
                {"outcome": outcome},
            )
            if outcome in {"cancelled", "client_disconnected"}:
                runtime_metrics.stream_disconnects.add(1)


@contextmanager
def repository_span(
    operation: str,
    *,
    system: str = "sqlite",
) -> Iterator[Span]:
    span = _tracer.start_span("db.repository")
    span.set_attribute("db.system", system)
    span.set_attribute("db.operation", operation)
    start_ns = time.monotonic_ns()
    with trace.use_span(span, end_on_exit=False):
        try:
            yield span
        except BaseException as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise
        else:
            span.set_status(Status(StatusCode.OK))
        finally:
            span.set_attribute(
                "duration_ms",
                _duration_seconds(start_ns) * 1000,
            )
            span.end()


def mark_span_error(span: Span, exc: BaseException) -> None:
    span.record_exception(exc)
    span.set_status(Status(StatusCode.ERROR, str(exc)))


def repository_operation(operation: str) -> Any:
    def decorator(func: Any) -> Any:
        @wraps(func)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            with repository_span(operation):
                return func(*args, **kwargs)

        return wrapped

    return decorator
