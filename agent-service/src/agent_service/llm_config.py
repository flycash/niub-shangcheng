import os
from pathlib import Path

import yaml
from pydantic import (
    BaseModel,
    Field,
    SecretStr,
    ValidationError,
    field_validator,
)


class LLMConfigError(Exception):
    """Raised when the LLM configuration cannot be loaded or validated."""


MIN_RECOMMENDATION_TURNS = 10
MAX_RECOMMENDATION_TURNS = 100
MIN_AGENT_OUTPUT_TOKENS = 32_768
DEFAULT_LONG_TIMEOUT_SECONDS = 1_800
MAX_LONG_TIMEOUT_SECONDS = 3_600


class LLMConfig(BaseModel):
    base_url: str
    api_key: SecretStr
    model: str
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, gt=0)
    timeout_seconds: float = Field(
        default=DEFAULT_LONG_TIMEOUT_SECONDS,
        gt=0,
        le=MAX_LONG_TIMEOUT_SECONDS,
    )
    max_turns: int = Field(
        default=MIN_RECOMMENDATION_TURNS,
        ge=MIN_RECOMMENDATION_TURNS,
        le=MAX_RECOMMENDATION_TURNS,
    )
    tool_timeout_seconds: float = Field(
        default=DEFAULT_LONG_TIMEOUT_SECONDS,
        gt=0,
        le=DEFAULT_LONG_TIMEOUT_SECONDS,
    )

    @property
    def output_token_limit(self) -> int:
        """Keep enough output budget for tool calls and reasoned final replies."""
        return max(self.max_tokens or 0, MIN_AGENT_OUTPUT_TOKENS)

    @property
    def model_timeout_limit(self) -> float:
        return max(self.timeout_seconds, DEFAULT_LONG_TIMEOUT_SECONDS)

    @property
    def tool_timeout_limit(self) -> float:
        return max(self.tool_timeout_seconds, DEFAULT_LONG_TIMEOUT_SECONDS)

    @field_validator("base_url", "model")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value

    @field_validator("base_url")
    @classmethod
    def base_url_must_be_http(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        return value.rstrip("/")

    @field_validator("api_key")
    @classmethod
    def api_key_must_not_be_blank(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("api_key must not be blank")
        return value


def resolve_config_path(config_path: str | Path | None = None) -> Path:
    configured_path = config_path or os.getenv("LLM_CONFIG_FILE")
    if not configured_path:
        raise LLMConfigError(
            "LLM config is not set; use --config or LLM_CONFIG_FILE"
        )
    return Path(configured_path).expanduser().resolve()


def load_llm_config(config_path: str | Path | None = None) -> LLMConfig:
    path = resolve_config_path(config_path)
    try:
        with path.open("r", encoding="utf-8") as config_file:
            data = yaml.safe_load(config_file)
    except FileNotFoundError as exc:
        raise LLMConfigError(f"LLM config file not found: {path}") from exc
    except OSError as exc:
        raise LLMConfigError(f"cannot read LLM config file: {path}") from exc
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise LLMConfigError(f"invalid YAML in LLM config file: {path}") from exc

    if not isinstance(data, dict):
        raise LLMConfigError(f"config file must contain a mapping: {path}")

    llm_data = data.get("llm")
    if not isinstance(llm_data, dict):
        raise LLMConfigError(f"missing llm section in config file: {path}")

    try:
        config = LLMConfig.model_validate(llm_data)
    except ValidationError as exc:
        fields = ", ".join(
            ".".join(str(part) for part in error["loc"]) for error in exc.errors()
        )
        raise LLMConfigError(
            f"invalid LLM config file: {path} (fields: {fields})"
        ) from exc

    return config
