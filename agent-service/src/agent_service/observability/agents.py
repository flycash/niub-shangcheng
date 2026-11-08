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
            self.llm_span.set_attribute(key, value)
        response_id = getattr(response, "response_id", None)
        if response_id:
            self.llm_span.set_attribute(
                "gen_ai.response.id",
                str(response_id),
            )
        self._finish_llm(outcome)

    def _finish_llm(self, outcome: str) -> None:
        if self.llm_span is None:
            return
        duration = _elapsed_seconds(self.llm_start_ns)
        self.llm_span.set_attribute("agent.llm.outcome", outcome)
        self.llm_span.set_attribute(
            "agent.llm.duration_ms",
            duration * 1000,
        )
        self.llm_span.set_attribute(
            "agent.llm.output_chars",
            self.llm_output_chars,
        )
        if outcome == "completed":
            self.llm_span.set_status(Status(StatusCode.OK))
        elif outcome != "aborted":
            self.llm_span.set_status(
                Status(StatusCode.ERROR, outcome)
            )
        self.llm_span.end()
        self.llm_span = None

        runtime_metrics = get_runtime_metrics()
        if runtime_metrics is not None:
            runtime_metrics.llm_duration.record(
                duration,
                {
                    "gen_ai.request.model": self.model,
                    "operation": "chat",
                    "outcome": outcome,
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

    def record_token_usage(self, usage: Any) -> None:
        runtime_metrics = get_runtime_metrics()
        if runtime_metrics is not None and usage is not None:
            runtime_metrics.record_token_usage(
                usage,
                {"gen_ai.request.model": self.model},
            )

    def record_tool(self) -> None:
        self.tool_count += 1
        if self.react_span is not None:
            self.react_span.set_attribute(
                "agent.react.tool_count",
                self.tool_count,
            )

    def finish_react(self, outcome: str) -> None:
        if self.react_span is None:
            return
        duration = _elapsed_seconds(self.react_start_ns)
        self.react_span.set_attribute("agent.react.outcome", outcome)
        self.react_span.set_attribute(
            "agent.react.duration_ms",
            duration * 1000,
        )
        self.react_span.set_attribute(
            "agent.react.tool_count",
            self.tool_count,
        )
        if outcome == "completed":
            self.react_span.set_status(Status(StatusCode.OK))
        else:
            self.react_span.set_status(
                Status(StatusCode.ERROR, outcome)
            )
        self.react_span.end()
        runtime_metrics = get_runtime_metrics()
        if runtime_metrics is not None:
            runtime_metrics.react_duration.record(
                duration,
                {
                    "react.index": self.react_index,
                    "outcome": outcome,
                },
            )
        self.react_span = None
        self.react_context = None
        self.tool_count = 0

    def finish(
        self,
        outcome: str,
        error: BaseException | None = None,
    ) -> None:
        if self.finished:
            return
        self.finished = True
        if self.llm_span is not None:
            if error is not None:
                self.llm_span.record_exception(error)
            self._finish_llm(outcome)
        self.finish_react(outcome)

    @contextmanager
    def bind(self) -> Iterator["AgentTraceSession"]:
        token = _current_agent_session.set(self)
        try:
            yield self
        finally:
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
                        "tool.result": (
                            truncate_text(
                                result_text,
                                tool_log_config.max_payload_chars,
                            )
                            if tool_log_config.include_result
                            else "[disabled]"
                        ),
                    },
                )
                runtime_metrics = get_runtime_metrics()
                if runtime_metrics is not None:
                    runtime_metrics.tool_duration.record(
                        duration / 1000,
                        {
                            "tool.name": tool_name,
                            "outcome": outcome,
                        },
                    )
                    runtime_metrics.tool_calls.add(
                        1,
                        {
                            "tool.name": tool_name,
                            "outcome": outcome,
                        },
                    )
                detach(tool_token)
                span.end()

        observed._observability_wrapped = True
        tool.on_invoke_tool = observed
    return list(tools)


class ActionObservation:
    def __init__(self, name: str, model: str) -> None:
        self.name = name
        self.model = model
        self.start_ns = time.monotonic_ns()
        self.action_span = get_tracer().start_span("agent.action")
        self.action_span.set_attribute("agent.action.name", name)
        self.action_context = trace.set_span_in_context(self.action_span)
        self.llm_start_ns = time.monotonic_ns()
        self.llm_span = get_tracer().start_span(
            "agent.llm",
            context=self.action_context,
        )
        self.llm_span.set_attribute("gen_ai.operation.name", "chat")
        self.llm_span.set_attribute("gen_ai.request.model", model)
        self.llm_span.set_attribute("agent.action.name", name)
        self.llm_span.set_attribute("agent.llm.streaming", True)
        self.first_char_recorded = False
        self.first_output_recorded = False
        self.output_chars = 0
        self.ended = False

    @contextmanager
    def active(self) -> Iterator[None]:
        with (
            trace.use_span(self.action_span, end_on_exit=False),
            trace.use_span(self.llm_span, end_on_exit=False),
        ):
            yield

    def observe_event(self, event: Any) -> None:
        event_type = getattr(event, "type", "")
        if event_type in {
            "response.output_item.added",
            "response.function_call_arguments.delta",
            "response.output_item.done",
        }:
            self._record_first_output()
        if isinstance(event, ResponseTextDeltaEvent):
            delta = event.delta or ""
            self.output_chars += len(delta)
            if delta:
                self._record_first_output()
                self._record_first_char()

    def _record_first_output(self) -> None:
        if self.first_output_recorded:
            return
        self.first_output_recorded = True
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
        if self.first_char_recorded:
            return
        self.first_char_recorded = True
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

    def finish(
        self,
        result: Any,
        *,
        error: BaseException | None = None,
    ) -> None:
        if self.ended:
            return
        self.ended = True
        outcome = "completed" if error is None else "failed"
        usage = getattr(
            getattr(result, "context_wrapper", None),
            "usage",
            None,
        )
        for key, value in _usage_attributes(usage).items():
            self.llm_span.set_attribute(key, value)
        response_id = getattr(result, "last_response_id", None)
        if response_id:
            self.llm_span.set_attribute(
                "gen_ai.response.id",
                str(response_id),
            )
        duration = _elapsed_seconds(self.llm_start_ns)
        self.llm_span.set_attribute("agent.llm.outcome", outcome)
        self.llm_span.set_attribute(
            "agent.llm.duration_ms",
            duration * 1000,
        )
        self.llm_span.set_attribute(
            "agent.llm.output_chars",
            self.output_chars,
        )
        if error is not None:
            self.llm_span.record_exception(error)
            self.llm_span.set_status(Status(StatusCode.ERROR, str(error)))
            self.action_span.record_exception(error)
            self.action_span.set_status(
                Status(StatusCode.ERROR, str(error))
            )
        else:
            self.llm_span.set_status(Status(StatusCode.OK))
            self.action_span.set_status(Status(StatusCode.OK))
        self.llm_span.end()
        self.action_span.set_attribute(
            "agent.action.duration_ms",
            _elapsed_ms(self.start_ns),
        )
        self.action_span.end()

        runtime_metrics = get_runtime_metrics()
        if runtime_metrics is not None:
            runtime_metrics.llm_duration.record(
                duration,
                {
                    "gen_ai.request.model": self.model,
                    "operation": "chat",
                    "outcome": outcome,
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
