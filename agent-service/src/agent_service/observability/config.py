import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class ObservabilityConfigError(Exception):
    """Raised when observability configuration cannot be loaded or validated."""


class ServiceMetadataConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = "agent-service"
    environment: str = "local"
    version: str = "0.1.0"

    @field_validator("name", "environment", "version")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value


class ToolLogConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    include_arguments: bool = True
    include_result: bool = True
    max_payload_chars: int = Field(default=16000, ge=0)
    redact_keys: list[str] = Field(
        default_factory=lambda: [
            "authorization",
            "api_key",
            "token",
            "password",
        ]
    )


class LogsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    level: str = "INFO"
    format: Literal["json", "text"] = "json"
    access_log: bool = True
    tool_level: str = "DEBUG"
    tool: ToolLogConfig = Field(default_factory=ToolLogConfig)

    @field_validator("level", "tool_level")
    @classmethod
    def normalize_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {
            "CRITICAL",
            "ERROR",
            "WARNING",
            "INFO",
            "DEBUG",
            "NOTSET",
        }:
            raise ValueError("invalid logging level")
        return normalized


class PrometheusMetricsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    path: str = "/metrics"

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        path = value.strip()
        if not path.startswith("/") or "?" in path or "#" in path:
            raise ValueError("metrics path must be an absolute path")
        return path.rstrip("/") or "/"


class LogMetricsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    level: str = "DEBUG"
    export_interval_millis: int = Field(default=30000, ge=1000)
    include_histogram_buckets: bool = True
    max_data_points_per_batch: int = Field(default=1000, ge=1)

    @field_validator("level")
    @classmethod
    def normalize_level(cls, value: str) -> str:
        return value.upper()


class MetricsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    prometheus: PrometheusMetricsConfig = Field(
        default_factory=PrometheusMetricsConfig
    )
    log: LogMetricsConfig = Field(default_factory=LogMetricsConfig)


class ZipkinTraceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    endpoint: str = "http://127.0.0.1:9411/api/v2/spans"
    timeout_millis: int = Field(default=3000, ge=100)

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, value: str) -> str:
        endpoint = value.strip()
        if not endpoint.startswith(("http://", "https://")):
            raise ValueError("endpoint must start with http:// or https://")
        return endpoint


class LogTraceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    fallback_only: bool = True
    level: str = "DEBUG"
    include_events: bool = True
    max_attribute_length: int = Field(default=4000, ge=0)
    max_spans_per_batch: int = Field(default=512, ge=1)

    @field_validator("level")
    @classmethod
    def normalize_level(cls, value: str) -> str:
        return value.upper()


class BatchTraceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_queue_size: int = Field(default=2048, ge=1)
    schedule_delay_millis: int = Field(default=2000, ge=100)
    max_export_batch_size: int = Field(default=512, ge=1)


class TracesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    sample_ratio: float = Field(default=1.0, ge=0.0, le=1.0)
    excluded_paths: list[str] = Field(
        default_factory=lambda: ["/health", "/metrics"]
    )
    propagators: list[
        Literal["tracecontext", "baggage", "b3", "b3multi"]
    ] = Field(default_factory=lambda: ["tracecontext", "baggage", "b3multi"])
    zipkin: ZipkinTraceConfig = Field(default_factory=ZipkinTraceConfig)
    log: LogTraceConfig = Field(default_factory=LogTraceConfig)
    batch: BatchTraceConfig = Field(default_factory=BatchTraceConfig)

    @field_validator("excluded_paths")
    @classmethod
    def validate_excluded_paths(cls, value: list[str]) -> list[str]:
        paths = [path.strip() for path in value if path.strip()]
        if any(not path.startswith("/") for path in paths):
            raise ValueError("excluded paths must start with /")
        return paths


class ObservabilityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    service: ServiceMetadataConfig = Field(default_factory=ServiceMetadataConfig)
    logs: LogsConfig = Field(default_factory=LogsConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    traces: TracesConfig = Field(default_factory=TracesConfig)


def resolve_observability_config_path(
    config_path: str | Path | None = None,
) -> Path | None:
    configured_path = config_path or os.getenv("LLM_CONFIG_FILE")
    if not configured_path:
        return None
    return Path(configured_path).expanduser().resolve()


def load_observability_config(
    config_path: str | Path | None = None,
) -> ObservabilityConfig:
    path = resolve_observability_config_path(config_path)
    if path is None:
        return ObservabilityConfig(enabled=False)
    try:
        with path.open("r", encoding="utf-8") as config_file:
            data = yaml.safe_load(config_file)
    except FileNotFoundError as exc:
        raise ObservabilityConfigError(
            f"observability config file not found: {path}"
        ) from exc
    except OSError as exc:
        raise ObservabilityConfigError(
            f"cannot read observability config file: {path}"
        ) from exc
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ObservabilityConfigError(
            f"invalid YAML in observability config file: {path}"
        ) from exc

    if not isinstance(data, dict):
        raise ObservabilityConfigError(
            f"config file must contain a mapping: {path}"
        )
    section = data.get("observability")
    if section is None:
        return ObservabilityConfig(enabled=False)
    if not isinstance(section, dict):
        raise ObservabilityConfigError(
            f"observability section must be a mapping: {path}"
        )
    try:
        return ObservabilityConfig.model_validate(section)
    except ValidationError as exc:
        fields = ", ".join(
            ".".join(str(part) for part in error["loc"])
            for error in exc.errors()
        )
        raise ObservabilityConfigError(
            f"invalid observability config file: {path} (fields: {fields})"
        ) from exc
