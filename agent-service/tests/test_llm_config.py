from pathlib import Path

import pytest

from agent_service.llm_config import LLMConfigError, load_llm_config


def test_load_llm_config_resolves_prompt_relative_to_yaml(
    tmp_path: Path,
) -> None:
    config_dir = tmp_path / "config"
    prompt_dir = tmp_path / "prompts"
    config_dir.mkdir()
    prompt_dir.mkdir()
    prompt_path = prompt_dir / "agent.md"
    prompt_path.write_text("测试提示词", encoding="utf-8")
    config_path = config_dir / "llm.yaml"
    config_path.write_text(
        """
llm:
  base_url: "https://model.example/v1/"
  api_key: "secret-key"
  model: "example-model"
  temperature: 0.4
  max_tokens: 500
  prompt_file: "../prompts/agent.md"
""".strip(),
        encoding="utf-8",
    )

    config = load_llm_config(config_path)

    assert config.base_url == "https://model.example/v1"
    assert config.api_key.get_secret_value() == "secret-key"
    assert "secret-key" not in repr(config)
    assert config.model == "example-model"
    assert config.prompt_file == str(prompt_path.resolve())


def test_load_llm_config_supports_absolute_prompt_path(
    tmp_path: Path,
) -> None:
    prompt_path = tmp_path / "agent.md"
    prompt_path.write_text("绝对路径提示词", encoding="utf-8")
    config_path = tmp_path / "llm.yaml"
    config_path.write_text(
        f"""
llm:
  base_url: "https://model.example/v1"
  api_key: "secret-key"
  model: "example-model"
  prompt_file: "{prompt_path}"
""".strip(),
        encoding="utf-8",
    )

    config = load_llm_config(config_path)

    assert config.prompt_file == str(prompt_path.resolve())


def test_load_llm_config_requires_prompt_source(tmp_path: Path) -> None:
    config_path = tmp_path / "llm.yaml"
    config_path.write_text(
        """
llm:
  base_url: "https://model.example/v1"
  api_key: "secret-key"
  model: "example-model"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(LLMConfigError, match="prompt_file"):
        load_llm_config(config_path)


def test_legacy_system_prompt_emits_deprecation_warning(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "llm.yaml"
    config_path.write_text(
        """
llm:
  base_url: "https://model.example/v1"
  api_key: "secret-key"
  model: "example-model"
  system_prompt: "旧提示词"
""".strip(),
        encoding="utf-8",
    )

    with pytest.warns(DeprecationWarning, match="prompt_file"):
        config = load_llm_config(config_path)

    assert config.system_prompt == "旧提示词"
    assert config.prompt_file is None


def test_load_llm_config_rejects_invalid_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "llm.yaml"
    config_path.write_text("llm: [invalid", encoding="utf-8")

    with pytest.raises(LLMConfigError, match="invalid YAML"):
        load_llm_config(config_path)
