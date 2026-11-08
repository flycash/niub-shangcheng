import logging
import time
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any

from opentelemetry.sdk.metrics.export import (
    MetricExporter,
    MetricExportResult,
    MetricsData,
)
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from .config import LogMetricsConfig, LogTraceConfig
from .serialization import json_safe


trace_logger = logging.getLogger("agent_service.observability.trace")
metric_logger = logging.getLogger("agent_service.observability.metrics")


def _timestamp(nanoseconds: int) -> str:
    return datetime.fromtimestamp(
        nanoseconds / 1_000_000_000,
        timezone.utc,
    ).isoformat(timespec="milliseconds")


class LoggingSpanExporter(SpanExporter):
    def __init__(self, config: LogTraceConfig) -> None:
        self.config = config
        self.level = getattr(logging, config.level, logging.DEBUG)
        trace_logger.setLevel(self.level)

    def _span_payload(self, span: ReadableSpan) -> dict[str, Any]:
        context = span.context
        parent = span.parent
        events = []
        if self.config.include_events:
            events = [
                {
                    "name": event.name,
                    "timestamp": _timestamp(event.timestamp),
                    "attributes": json_safe(
                        dict(event.attributes or {}),
                        max_length=self.config.max_attribute_length,
                    ),
                }
                for event in span.events
            ]
        return {
            "event": "otel.trace.span",
            "service.name": span.resource.attributes.get("service.name", ""),
            "otel.trace_id": format(context.trace_id, "032x"),
            "otel.span_id": format(context.span_id, "016x"),
            "otel.parent_span_id": (
                format(parent.span_id, "016x") if parent is not None else ""
            ),
            "span.name": span.name,
            "kind": span.kind.name,
            "start_time": _timestamp(span.start_time or 0),
            "end_time": _timestamp(span.end_time or 0),
            "duration_ms": round(
                ((span.end_time or 0) - (span.start_time or 0)) / 1_000_000,
                3,
            ),
            "status": span.status.status_code.name,
            "status_description": span.status.description or "",
            "attributes": json_safe(
                dict(span.attributes or {}),
                max_length=self.config.max_attribute_length,
            ),
            "events": events,
            "scope": span.instrumentation_scope.name,
        }

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        for span in list(spans)[: self.config.max_spans_per_batch]:
            trace_logger.log(
                self.level,
                "OpenTelemetry span",
                extra=self._span_payload(span),
            )
        if len(spans) > self.config.max_spans_per_batch:
            trace_logger.debug(
                "OpenTelemetry span batch truncated",
                extra={
                    "event": "otel.trace.span_batch_truncated",
                    "total_spans": len(spans),
                    "logged_spans": self.config.max_spans_per_batch,
                },
            )
        return SpanExportResult.SUCCESS

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True

    def shutdown(self) -> None:
        return None


class FallbackSpanExporter(SpanExporter):
    def __init__(
        self,
        primary: SpanExporter,
        fallback: SpanExporter,
        *,
        log_primary_on_failure: bool = True,
    ) -> None:
        self.primary = primary
        self.fallback = fallback
        self.log_primary_on_failure = log_primary_on_failure
        self._last_failure_log = 0.0

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        try:
            result = self.primary.export(spans)
        except Exception as exc:
            result = SpanExportResult.FAILURE
            self._log_failure(exc)
        else:
            if result != SpanExportResult.SUCCESS:
                self._log_failure(None)
        if result == SpanExportResult.SUCCESS:
            return result
        return self.fallback.export(spans)

    def _log_failure(self, exc: Exception | None) -> None:
        if not self.log_primary_on_failure:
            return
        now = time.monotonic()
        if now - self._last_failure_log < 10:
            return
        self._last_failure_log = now
        trace_logger.warning(
            "Primary trace exporter failed; falling back to logs",
            exc_info=exc,
            extra={
                "event": "otel.trace.export_fallback",
                "error.type": type(exc).__name__ if exc else "",
            },
        )

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        primary = self.primary.force_flush(timeout_millis)
        fallback = self.fallback.force_flush(timeout_millis)
        return primary and fallback

    def shutdown(self) -> None:
        self.primary.shutdown()
        self.fallback.shutdown()


class MultiSpanExporter(SpanExporter):
    def __init__(self, exporters: Sequence[SpanExporter]) -> None:
        self.exporters = list(exporters)

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        results = [exporter.export(spans) for exporter in self.exporters]
        if any(result == SpanExportResult.SUCCESS for result in results):
            return SpanExportResult.SUCCESS
        return SpanExportResult.FAILURE

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return all(
            exporter.force_flush(timeout_millis)
            for exporter in self.exporters
        )

    def shutdown(self) -> None:
        for exporter in self.exporters:
            exporter.shutdown()


class LoggingMetricExporter(MetricExporter):
    def __init__(self, config: LogMetricsConfig) -> None:
        super().__init__()
        self.config = config
        self.level = getattr(logging, config.level, logging.DEBUG)
        metric_logger.setLevel(self.level)

    def _data_point_payload(
        self,
        metric: Any,
        data_point: Any,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "event": "otel.metric",
            "metric.name": metric.name,
            "description": metric.description,
            "unit": metric.unit,
            "type": type(metric.data).__name__,
            "attributes": json_safe(dict(data_point.attributes or {})),
            "start_time": _timestamp(data_point.start_time_unix_nano),
            "timestamp": _timestamp(data_point.time_unix_nano),
        }
        for field in ("value", "count", "sum", "min", "max"):
            field_value = getattr(data_point, field, None)
            if field_value is not None:
                payload[field] = field_value
        if self.config.include_histogram_buckets:
            bucket_counts = getattr(data_point, "bucket_counts", None)
            if bucket_counts is not None:
                payload["bucket_counts"] = list(bucket_counts)
            bucket_bounds = getattr(data_point, "explicit_bounds", None)
            if bucket_bounds is not None:
                payload["explicit_bounds"] = list(bucket_bounds)
        return payload

    def export(self, metrics_data: MetricsData) -> MetricExportResult:
        logged = 0
        for resource_metrics in metrics_data.resource_metrics:
            for scope_metrics in resource_metrics.scope_metrics:
                for metric in scope_metrics.metrics:
                    for data_point in metric.data.data_points:
                        if logged >= self.config.max_data_points_per_batch:
                            metric_logger.debug(
                                "OpenTelemetry metric batch truncated",
                                extra={
                                    "event": "otel.metric.batch_truncated",
                                    "logged_data_points": logged,
                                },
                            )
                            return MetricExportResult.SUCCESS
                        metric_logger.log(
                            self.level,
                            "OpenTelemetry metric",
                            extra=self._data_point_payload(
                                metric,
                                data_point,
                            ),
                        )
                        logged += 1
        return MetricExportResult.SUCCESS

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True

    def shutdown(self) -> None:
        return None
