from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3Format, B3MultiFormat
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import (
    ParentBased,
    TraceIdRatioBased,
)
from opentelemetry.trace.propagation.tracecontext import (
    TraceContextTextMapPropagator,
)
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from prometheus_client import CollectorRegistry, make_asgi_app
from starlette.routing import Route

from .config import ObservabilityConfig
from .logging import configure_logging
from .log_exporters import (
    FallbackSpanExporter,
    LoggingMetricExporter,
    LoggingSpanExporter,
    MultiSpanExporter,
)
from .metrics import ObservabilityMetrics, initialize_metrics


class _MetricsASGIApp:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Any,
        send: Any,
    ) -> None:
        await self.app(scope, receive, send)


@dataclass
class ObservabilityRuntime:
    config: ObservabilityConfig
    tracer_provider: TracerProvider | None = None
    meter_provider: MeterProvider | None = None
    metrics: ObservabilityMetrics | None = None
    prometheus_registry: CollectorRegistry | None = None
    instrumented: bool = False

    def shutdown(self) -> None:
        if self.tracer_provider is not None:
            self.tracer_provider.shutdown()
        if self.meter_provider is not None:
            self.meter_provider.shutdown()


_runtime = ObservabilityRuntime(
    config=ObservabilityConfig(enabled=False)
)


def get_observability_runtime() -> ObservabilityRuntime:
    return _runtime


def _propagator(config: ObservabilityConfig) -> CompositePropagator:
    propagators: list[Any] = []
    for item in config.traces.propagators:
        if item == "tracecontext":
            propagators.append(TraceContextTextMapPropagator())
        elif item == "baggage":
            propagators.append(W3CBaggagePropagator())
        elif item == "b3":
            propagators.append(B3Format())
        elif item == "b3multi":
            propagators.append(B3MultiFormat())
    return CompositePropagator(propagators)


def _span_exporters(config: ObservabilityConfig) -> list[Any]:
    exporters: list[Any] = []
    if config.traces.zipkin.enabled:
        exporters.append(
            ZipkinExporter(
                endpoint=config.traces.zipkin.endpoint,
                timeout=config.traces.zipkin.timeout_millis,
            )
        )
    logging_exporter = (
        LoggingSpanExporter(config.traces.log)
        if config.traces.log.enabled
        else None
    )
    if not exporters:
        return [logging_exporter] if logging_exporter is not None else []
    if logging_exporter is None:
        return exporters
    if config.traces.log.fallback_only:
        return [
            FallbackSpanExporter(
                primary=exporter,
                fallback=logging_exporter,
                log_primary_on_failure=True,
            )
            for exporter in exporters
        ]
    return [*exporters, logging_exporter]


def _configure_trace_provider(
    config: ObservabilityConfig,
) -> tuple[TracerProvider | None, list[Any]]:
    if not config.traces.enabled:
        return None, []
    exporters = _span_exporters(config)
    if not exporters:
        return None, []

    resource = Resource.create(
        {
            "service.name": config.service.name,
            "service.version": config.service.version,
            "deployment.environment.name": config.service.environment,
        }
    )
    provider = TracerProvider(
        resource=resource,
        sampler=ParentBased(TraceIdRatioBased(config.traces.sample_ratio)),
    )
    exporter: Any
    if len(exporters) == 1:
        exporter = exporters[0]
    else:
        exporter = MultiSpanExporter(exporters)
    provider.add_span_processor(
        BatchSpanProcessor(
            exporter,
            max_queue_size=config.traces.batch.max_queue_size,
            schedule_delay_millis=config.traces.batch.schedule_delay_millis,
            max_export_batch_size=config.traces.batch.max_export_batch_size,
        )
    )
    trace.set_tracer_provider(provider)
    return provider, exporters


def _configure_meter_provider(
    config: ObservabilityConfig,
) -> tuple[MeterProvider | None, CollectorRegistry | None]:
    if not config.metrics.enabled:
        return None, None
    resource = Resource.create(
        {
            "service.name": config.service.name,
            "service.version": config.service.version,
            "deployment.environment.name": config.service.environment,
        }
    )
    registry: CollectorRegistry | None = None
    readers: list[Any] = []
    if config.metrics.prometheus.enabled:
        registry = CollectorRegistry()
        readers.append(PrometheusMetricReader(registry=registry))
    if config.metrics.log.enabled:
        readers.append(
            PeriodicExportingMetricReader(
                LoggingMetricExporter(config.metrics.log),
                export_interval_millis=(
                    config.metrics.log.export_interval_millis
                ),
            )
        )
    if not readers:
        return None, None
    provider = MeterProvider(resource=resource, metric_readers=readers)
    metrics.set_meter_provider(provider)
    return provider, registry


def configure_observability(app: FastAPI) -> ObservabilityRuntime:
    global _runtime
    from .config import load_observability_config

    config = load_observability_config()
    _runtime = ObservabilityRuntime(config=config)
    if not config.enabled:
        return _runtime

    configure_logging(config.logs, config.service)
    set_global_textmap(_propagator(config))
    tracer_provider, _ = _configure_trace_provider(config)
    meter_provider, registry = _configure_meter_provider(config)
    _runtime.tracer_provider = tracer_provider
    _runtime.meter_provider = meter_provider
    _runtime.prometheus_registry = registry
    if tracer_provider is not None or meter_provider is not None:
        from .spans import set_observability_clients

        set_observability_clients(
            tracer=(
                tracer_provider.get_tracer("agent-service")
                if tracer_provider is not None
                else trace.get_tracer("agent-service")
            )
        )
    if meter_provider is not None:
        _runtime.metrics = initialize_metrics(meter_provider)

    if registry is not None:
        app.router.routes.append(
            Route(
                config.metrics.prometheus.path,
                endpoint=_MetricsASGIApp(
                    make_asgi_app(registry=registry)
                ),
                methods=["GET"],
                include_in_schema=False,
            )
        )

    if tracer_provider is not None or meter_provider is not None:
        FastAPIInstrumentor.instrument_app(
            app,
            tracer_provider=tracer_provider,
            meter_provider=meter_provider,
            excluded_urls=",".join(config.traces.excluded_paths),
        )
        SQLite3Instrumentor().instrument(
            tracer_provider=tracer_provider,
            meter_provider=meter_provider,
        )

    from .middleware import RequestLifecycleMiddleware

    app.add_middleware(
        RequestLifecycleMiddleware,
        config=config,
    )
    previous_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def observed_lifespan(application: FastAPI) -> Any:
        async with previous_lifespan(application):
            try:
                yield
            finally:
                _runtime.shutdown()

    app.router.lifespan_context = observed_lifespan
    _runtime.instrumented = True
    return _runtime
