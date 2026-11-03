from pathlib import Path

import pytest

from agent_service.prompt_loader import (
    MAX_PROMPT_BYTES,
    PromptLoadError,
    load_prompt,
)


def test_load_prompt_reads_any_utf8_file(tmp_path: Path) -> None:
    prompt_path = tmp_path / "agent.md"
    prompt_path.write_text("  通用提示词  ", encoding="utf-8")

    assert load_prompt(prompt_path) == "通用提示词"


def test_load_prompt_reloads_file_contents(tmp_path: Path) -> None:
    prompt_path = tmp_path / "agent.md"
    prompt_path.write_text("版本一", encoding="utf-8")
    assert load_prompt(prompt_path) == "版本一"

    prompt_path.write_text("版本二", encoding="utf-8")
    assert load_prompt(prompt_path) == "版本二"


def test_missing_prompt_file_has_clear_error(tmp_path: Path) -> None:
    with pytest.raises(PromptLoadError, match="not found"):
        load_prompt(tmp_path / "missing.md")


def test_empty_prompt_file_is_rejected(tmp_path: Path) -> None:
    prompt_path = tmp_path / "empty.md"
    prompt_path.write_text("   \n", encoding="utf-8")

    with pytest.raises(PromptLoadError, match="empty"):
        load_prompt(prompt_path)


def test_oversized_prompt_file_is_rejected(tmp_path: Path) -> None:
    prompt_path = tmp_path / "large.md"
    prompt_path.write_bytes(b"x" * (MAX_PROMPT_BYTES + 1))

    with pytest.raises(PromptLoadError, match="exceeds"):
        load_prompt(prompt_path)


def test_non_utf8_prompt_file_is_rejected(tmp_path: Path) -> None:
    prompt_path = tmp_path / "invalid.md"
    prompt_path.write_bytes(b"\xff\xfe\xfa")

    with pytest.raises(PromptLoadError, match="UTF-8"):
        load_prompt(prompt_path)
