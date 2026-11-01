from pathlib import Path

import pytest

from agent_service.llm_config import LLMConfig
from agent_service.prompt_loader import (
    MAX_PROMPT_BYTES,
    PromptLoadError,
    load_agent_prompt,
)


def make_config(prompt_path: Path) -> LLMConfig:
    return LLMConfig(
        base_url="https://model.example/v1",
        api_key="test-key",
        model="example-model",
        prompt_file=str(prompt_path),
    )


def test_load_agent_prompt_from_file(tmp_path: Path) -> None:
    prompt_path = tmp_path / "agent.md"
    prompt_path.write_text("  文件提示词  ", encoding="utf-8")

    assert load_agent_prompt(make_config(prompt_path)) == "文件提示词"


def test_prompt_file_is_reloaded_for_each_request(tmp_path: Path) -> None:
    prompt_path = tmp_path / "agent.md"
    prompt_path.write_text("版本一", encoding="utf-8")
    config = make_config(prompt_path)
    assert load_agent_prompt(config) == "版本一"

    prompt_path.write_text("版本二", encoding="utf-8")

    assert load_agent_prompt(config) == "版本二"


def test_missing_prompt_file_has_clear_error(tmp_path: Path) -> None:
    config = make_config(tmp_path / "missing.md")

    with pytest.raises(PromptLoadError, match="not found"):
        load_agent_prompt(config)


def test_empty_prompt_file_is_rejected(tmp_path: Path) -> None:
    prompt_path = tmp_path / "empty.md"
    prompt_path.write_text("   \n", encoding="utf-8")

    with pytest.raises(PromptLoadError, match="empty"):
        load_agent_prompt(make_config(prompt_path))


def test_oversized_prompt_file_is_rejected(tmp_path: Path) -> None:
    prompt_path = tmp_path / "large.md"
    prompt_path.write_bytes(b"x" * (MAX_PROMPT_BYTES + 1))

    with pytest.raises(PromptLoadError, match="exceeds"):
        load_agent_prompt(make_config(prompt_path))


def test_non_utf8_prompt_file_is_rejected(tmp_path: Path) -> None:
    prompt_path = tmp_path / "invalid.md"
    prompt_path.write_bytes(b"\xff\xfe\xfa")

    with pytest.raises(PromptLoadError, match="UTF-8"):
        load_agent_prompt(make_config(prompt_path))


def test_legacy_system_prompt_remains_supported() -> None:
    config = LLMConfig(
        base_url="https://model.example/v1",
        api_key="test-key",
        model="example-model",
        system_prompt="兼容提示词",
    )

    assert load_agent_prompt(config) == "兼容提示词"
