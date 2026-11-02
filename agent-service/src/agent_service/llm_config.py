import os
import warnings
from pathlib import Path

import yaml
from pydantic import (
    BaseModel,
    Field,
    SecretStr,
    ValidationError,
    field_validator,
    model_validator,
)


class LLMConfigError(Exception):
    """Raised when the LLM configuration cannot be loaded or validated."""


MIN_RECOMMENDATION_TURNS = 10
MAX_RECOMMENDATION_TURNS = 100


class LLMConfig(BaseModel):
    base_url: str
    api_key: SecretStr
    model: str
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, gt=0)
    timeout_seconds: float = Field(default=60, gt=0, le=600)
    max_turns: int = Field(
        default=MIN_RECOMMENDATION_TURNS,
        ge=MIN_RECOMMENDATION_TURNS,
        le=MAX_RECOMMENDATION_TURNS,
    )
    tool_timeout_seconds: float = Field(default=8, gt=0, le=60)
    prompt_file: str | None = None
    system_prompt: str | None = None

    @field_validator("base_url", "model")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value

    @field_validator("prompt_file", "system_prompt")
    @classmethod
    def strip_optional_text_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

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

    @model_validator(mode="after")
    def require_prompt_source(self) -> "LLMConfig":
        if not self.prompt_file and not self.system_prompt:
            raise ValueError("prompt_file or system_prompt is required")
        return self


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
        if not fields:
            fields = "prompt_file/system_prompt"
        raise LLMConfigError(
            f"invalid LLM config file: {path} (fields: {fields})"
        ) from exc

    if config.system_prompt and not config.prompt_file:
        warnings.warn(
            "llm.system_prompt is deprecated; migrate to llm.prompt_file",
            DeprecationWarning,
            stacklevel=2,
        )
    elif config.system_prompt and config.prompt_file:
        warnings.warn(
            "llm.system_prompt is ignored because llm.prompt_file is set",
            DeprecationWarning,
            stacklevel=2,
        )

    if config.prompt_file:
        prompt_path = Path(config.prompt_file).expanduser()
        if not prompt_path.is_absolute():
            prompt_path = path.parent / prompt_path
        config.prompt_file = str(prompt_path.resolve())

    return config
