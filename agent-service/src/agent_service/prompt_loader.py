from pathlib import Path
from typing import Protocol

from .llm_config import LLMConfig

MAX_PROMPT_BYTES = 64 * 1024


class PromptLoadError(Exception):
    """Raised when the configured agent prompt cannot be loaded."""


class PromptProvider(Protocol):
    def load(self) -> str: ...


class LocalFilePromptProvider:
    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    def load(self) -> str:
        if self.config.prompt_file:
            return self._load_file(Path(self.config.prompt_file))
        if self.config.system_prompt:
            return self.config.system_prompt
        raise PromptLoadError(
            "agent prompt is not configured; set llm.prompt_file"
        )

    @staticmethod
    def _load_file(path: Path) -> str:
        try:
            size = path.stat().st_size
        except FileNotFoundError as exc:
            raise PromptLoadError(f"agent prompt file not found: {path}") from exc
        except OSError as exc:
            raise PromptLoadError(f"cannot read agent prompt file: {path}") from exc

        if size > MAX_PROMPT_BYTES:
            raise PromptLoadError(
                f"agent prompt file exceeds {MAX_PROMPT_BYTES} bytes: {path}"
            )

        try:
            prompt = path.read_text(encoding="utf-8").strip()
        except UnicodeDecodeError as exc:
            raise PromptLoadError(
                f"agent prompt file is not valid UTF-8: {path}"
            ) from exc
        except OSError as exc:
            raise PromptLoadError(f"cannot read agent prompt file: {path}") from exc

        if not prompt:
            raise PromptLoadError(f"agent prompt file is empty: {path}")
        return prompt


def load_agent_prompt(config: LLMConfig) -> str:
    return LocalFilePromptProvider(config).load()
