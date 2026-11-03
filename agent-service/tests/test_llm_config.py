from pathlib import Path

import pytest

from agent_service.llm_config import LLMConfigError, load_llm_config


def test_load_llm_config_contains_only_model_settings(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "llm.yaml"
    config_path.write_text(
        """
llm:
  base_url: "https://model.example/v1/"
  api_key: "secret-key"
  model: "example-model"
  temperature: 0.4
  max_tokens: 500
""".strip(),
        encoding="utf-8",
    )

    config = load_llm_config(config_path)

    assert config.base_url == "https://model.example/v1"
    assert config.api_key.get_secret_value() == "secret-key"
    assert "secret-key" not in repr(config)
    assert config.model == "example-model"
    assert config.temperature == 0.4
    assert config.max_tokens == 500
    assert config.output_token_limit == 32768
    assert config.timeout_seconds == 1800
    assert config.tool_timeout_seconds == 1800


def test_load_llm_config_rejects_invalid_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "llm.yaml"
    config_path.write_text("llm: [invalid", encoding="utf-8")

    with pytest.raises(LLMConfigError, match="invalid YAML"):
        load_llm_config(config_path)


def test_load_llm_config_rejects_too_few_recommendation_turns(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "llm.yaml"
    config_path.write_text(
        """
llm:
  base_url: "https://model.example/v1"
  api_key: "secret-key"
  model: "example-model"
  max_turns: 5
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(LLMConfigError, match="max_turns"):
        load_llm_config(config_path)


def test_load_llm_config_accepts_high_recommendation_turn_limit(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "llm.yaml"
    config_path.write_text(
        """
llm:
  base_url: "https://model.example/v1"
  api_key: "secret-key"
  model: "example-model"
  max_turns: 100
""".strip(),
        encoding="utf-8",
    )

    config = load_llm_config(config_path)

    assert config.max_turns == 100


def test_runtime_limits_upgrade_small_legacy_values(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "llm.yaml"
    config_path.write_text(
        """
llm:
  base_url: "https://model.example/v1"
  api_key: "secret-key"
  model: "example-model"
  max_tokens: 800
  timeout_seconds: 60
  tool_timeout_seconds: 8
""".strip(),
        encoding="utf-8",
    )

    config = load_llm_config(config_path)

    assert config.output_token_limit == 32768
    assert config.model_timeout_limit == 1800
    assert config.tool_timeout_limit == 1800
