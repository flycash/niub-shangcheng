import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from agent_service.observability.spans import set_observability_clients


@pytest.fixture(scope="session")
def otel_test_exporter() -> InMemorySpanExporter:
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    set_observability_clients(
        tracer=provider.get_tracer("agent-service-tests"),
    )
    yield exporter
    provider.shutdown()
