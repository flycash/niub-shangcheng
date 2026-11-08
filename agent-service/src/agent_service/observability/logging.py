import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from opentelemetry import trace

from .config import LogsConfig, ServiceMetadataConfig
from .context import get_request_context


STANDARD_LOG_RECORD_FIELDS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "taskName",
    "thread",
    "threadName",
}


class TraceContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        span_context = trace.get_current_span().get_span_context()
        record.trace_id = (
            format(span_context.trace_id, "032x")
            if span_context.is_valid
            else ""
        )
        record.span_id = (
            format(span_context.span_id, "016x")
            if span_context.is_valid
            else ""
        )
        record.trace_sampled = bool(
            span_context.is_valid and span_context.trace_flags.sampled
        )
        request = get_request_context()
        if request is not None:
            record.request_id = request.request_id
        return True


class JsonLogFormatter(logging.Formatter):
    def __init__(
        self,
        service: ServiceMetadataConfig,
        *,
        include_trace: bool = True,
    ) -> None:
        super().__init__()
        self.service = service
        self.include_trace = include_trace

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                timezone.utc,
            ).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "service": self.service.name,
            "environment": self.service.environment,
            "service.version": self.service.version,
            "message": record.getMessage(),
        }
        if self.include_trace:
            payload["trace_id"] = getattr(record, "trace_id", "")
            payload["span_id"] = getattr(record, "span_id", "")
            payload["trace_sampled"] = getattr(
                record,
                "trace_sampled",
                False,
            )
        request_id = getattr(record, "request_id", None)
        if request_id:
            payload["request_id"] = request_id

        for key, value in record.__dict__.items():
            if (
                key in STANDARD_LOG_RECORD_FIELDS
                or key.startswith("_")
                or key in payload
            ):
                continue
            payload[key] = value
        if not payload.get("trace_id"):
            exported_trace_id = getattr(record, "otel.trace_id", "")
            if exported_trace_id:
                payload["trace_id"] = exported_trace_id
        if not payload.get("span_id"):
            exported_span_id = getattr(record, "otel.span_id", "")
            if exported_span_id:
                payload["span_id"] = exported_span_id

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)
        try:
            return json.dumps(payload, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            payload = {
                key: str(value) for key, value in payload.items()
            }
            return json.dumps(payload, ensure_ascii=False)


def configure_logging(
    config: LogsConfig,
    service: ServiceMetadataConfig,
) -> None:
    if not config.enabled:
        return

    root = logging.getLogger()
    managed_handlers = [
        handler
        for handler in root.handlers
        if getattr(handler, "_agent_service_observability", False)
    ]
    for handler in managed_handlers:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler._agent_service_observability = True
    handler.addFilter(TraceContextFilter())
    if config.format == "json":
        handler.setFormatter(JsonLogFormatter(service))
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s "
                "trace_id=%(trace_id)s span_id=%(span_id)s %(message)s"
            )
        )
    root.addHandler(handler)
    root.setLevel(config.level)

    logging.getLogger("agent_service.observability.tool").setLevel(
        config.tool_level
    )
    logging.getLogger("agent_service.observability.trace").setLevel(
        "DEBUG"
    )
    logging.getLogger("agent_service.observability.metrics").setLevel(
        "DEBUG"
    )

    for name in ("uvicorn", "uvicorn.error"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
    for name in ("httpx", "httpx2"):
        logging.getLogger(name).setLevel("WARNING")

    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers.clear()
    access_logger.propagate = False
    access_logger.disabled = True
