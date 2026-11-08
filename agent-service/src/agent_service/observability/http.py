from typing import Any

import httpx
from opentelemetry.instrumentation.httpx import AsyncOpenTelemetryTransport

from .telemetry import get_observability_runtime


def observed_async_transport(
    transport: httpx.AsyncBaseTransport,
) -> httpx.AsyncBaseTransport:
    if isinstance(transport, AsyncOpenTelemetryTransport):
        return transport
    runtime = get_observability_runtime()
    if (
        runtime.tracer_provider is None
        and runtime.meter_provider is None
    ):
        return transport
    return AsyncOpenTelemetryTransport(
        transport,
        tracer_provider=runtime.tracer_provider,
        meter_provider=runtime.meter_provider,
    )
