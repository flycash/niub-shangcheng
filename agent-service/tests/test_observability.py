import asyncio
import logging
from pathlib import Path

import httpx
import pytest
from agents import Agent
from agents.testing import ScriptedModel, assistant_message
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.instrumentation.httpx import AsyncOpenTelemetryTransport

from agent_service.observability.config import (
    LogMetricsConfig,
    LogTraceConfig,
    ObservabilityConfigError,
    load_observability_config,
)
from agent_service.observability.log_exporters import (
    FallbackSpanExporter,
    LoggingMetricExporter,
    LoggingSpanExporter,
)
from agent_service.observability.agents import run_observed_action
from agent_service.observability.spans import get_tracer
from agent_service.mall_client import MallClient
from agent_service.storage import ConversationStore


def test_load_observability_config_from_existing_service_file(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "service.yaml"
    config_path.write_text(
        """
llm:
  base_url: http://model.test/v1
  api_key: secret
  model: test-model
observability:
  enabled: true
  service:
    name: agent-service
    environment: test
  traces:
    zipkin:
      enabled: false
    log:
      enabled: true
      fallback_only: false
  metrics:
    prometheus:
      enabled: true
      path: /internal/metrics
    log:
      enabled: true
""",
        encoding="utf-8",
    )

    config = load_observability_config(config_path)

    assert config.enabled is True
    assert config.service.environment == "test"
    assert config.traces.zipkin.enabled is False
    assert config.traces.log.enabled is True
    assert config.metrics.prometheus.path == "/internal/metrics"
    assert config.metrics.log.enabled is True


def test_invalid_observability_field_is_rejected(tmp_path: Path) -> None:
    config_path = tmp_path / "service.yaml"
    config_path.write_text(
        """
observability:
  enabled: true
  traces:
    zipkin:
      enabled: false
      endpiont: http://zipkin.invalid/api/v2/spans
""",
        encoding="utf-8",
    )

    with pytest.raises(ObservabilityConfigError, match="fields"):
        load_observability_config(config_path)


def test_database_repository_connect_and_queries_are_exported(
    tmp_path: Path,
    otel_test_exporter,
) -> None:
    otel_test_exporter.clear()

    store = ConversationStore(tmp_path / "observability.db")
    conversation_id = store.create_conversation(1, "你好")
    store.add_message(
        conversation_id,
        "user",
        "你好",
        "completed",
    )
    store.list_conversations(1)

    span_names = [span.name for span in otel_test_exporter.get_finished_spans()]
    assert "db.repository" in span_names
    assert "db.connect" in span_names
    assert "db.query" in span_names

    sqlite_spans = [
        span
        for span in otel_test_exporter.get_finished_spans()
        if span.name in {"db.connect", "db.query"}
    ]
    assert sqlite_spans
    assert all(
        span.attributes.get("db.system") == "sqlite"
        for span in sqlite_spans
    )


def test_trace_can_be_exported_to_structured_log(
    caplog: pytest.LogCaptureFixture,
    otel_test_exporter,
) -> None:
    otel_test_exporter.clear()
    span = get_tracer().start_span("test.log-export")
    span.set_attribute("test.value", "yes")
    span.end()
    otel_test_exporter.force_flush()
    spans = otel_test_exporter.get_finished_spans()

    exporter = LoggingSpanExporter(LogTraceConfig())
    with caplog.at_level(
        logging.DEBUG,
        logger="agent_service.observability.trace",
    ):
        assert exporter.export(spans) == SpanExportResult.SUCCESS

    record = next(
        record
        for record in caplog.records
        if getattr(record, "event", "") == "otel.trace.span"
    )
    assert getattr(record, "span.name") == "test.log-export"
    assert getattr(record, "otel.trace_id")
    assert getattr(record, "otel.span_id")
    assert record.attributes["test.value"] == "yes"


class _FailingSpanExporter(SpanExporter):
    def export(self, spans) -> SpanExportResult:
        raise ConnectionError("zipkin unavailable")

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return False

    def shutdown(self) -> None:
        return None


def test_zipkin_failure_falls_back_to_trace_log(
    caplog: pytest.LogCaptureFixture,
    otel_test_exporter,
) -> None:
    otel_test_exporter.clear()
    span = get_tracer().start_span("test.fallback")
    span.end()
    otel_test_exporter.force_flush()

    fallback = LoggingSpanExporter(LogTraceConfig())
    exporter = FallbackSpanExporter(
        _FailingSpanExporter(),
        fallback,
    )
    with caplog.at_level(
        logging.DEBUG,
        logger="agent_service.observability.trace",
    ):
        assert (
            exporter.export(otel_test_exporter.get_finished_spans())
            == SpanExportResult.SUCCESS
        )

    assert any(
        getattr(record, "event", "") == "otel.trace.export_fallback"
        for record in caplog.records
    )
    assert any(
        getattr(record, "event", "") == "otel.trace.span"
        for record in caplog.records
    )


def test_metrics_can_be_exported_to_structured_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    counter = provider.get_meter("metrics-test").create_counter(
        "agent.test.calls"
    )
    counter.add(2, {"outcome": "success"})
    metrics_data = reader.get_metrics_data()

    exporter = LoggingMetricExporter(
        LogMetricsConfig(
            enabled=True,
            max_data_points_per_batch=10,
        )
    )
    with caplog.at_level(
        logging.DEBUG,
        logger="agent_service.observability.metrics",
    ):
        exporter.export(metrics_data)

    record = next(
        record
        for record in caplog.records
        if getattr(record, "event", "") == "otel.metric"
    )
    assert getattr(record, "metric.name") == "agent.test.calls"
    assert record.value == 2
    assert record.attributes == {"outcome": "success"}


def test_streamed_action_exports_action_and_llm_spans(
    otel_test_exporter,
) -> None:
    otel_test_exporter.clear()
    model = ScriptedModel([[assistant_message("action-result")]])
    agent = Agent(name="test-action", model=model)

    result = asyncio.run(
        run_observed_action(
            agent,
            action_name="test_action",
            model="test-model",
            input="run",
        )
    )
    assert result.final_output == "action-result"

    spans = otel_test_exporter.get_finished_spans()
    action_spans = [span for span in spans if span.name == "agent.action"]
    llm_spans = [span for span in spans if span.name == "agent.llm"]
    assert len(action_spans) == 1
    assert len(llm_spans) == 1
    assert action_spans[0].attributes["agent.action.name"] == "test_action"
    assert "agent.llm.first_char_ms" in llm_spans[0].attributes
    assert "agent.llm.duration_ms" in llm_spans[0].attributes


def test_each_mall_http_request_gets_a_child_span() -> None:
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("httpx-test")
    transport = AsyncOpenTelemetryTransport(
        httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={"items": [], "total": 0},
            )
        ),
        tracer_provider=provider,
    )
    client = MallClient(
        base_url="http://mall.test",
        transport=transport,
    )
    with tracer.start_as_current_span("agent.tool"):
        asyncio.run(client.list_products())
        asyncio.run(client.list_products())

    spans = exporter.get_finished_spans()
    http_spans = [
        span for span in spans if span.kind.name == "CLIENT"
    ]
    assert len(http_spans) == 2
    parent_span = next(
        span for span in spans if span.name == "agent.tool"
    )
    assert all(
        span.parent.span_id == parent_span.context.span_id
        for span in http_spans
    )
