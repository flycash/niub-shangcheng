from pathlib import Path

MAX_PROMPT_BYTES = 1024 * 1024


class PromptLoadError(Exception):
    """Raised when the configured agent prompt cannot be loaded."""


def load_prompt(path: str | Path) -> str:
    prompt_path = Path(path)
    try:
        size = prompt_path.stat().st_size
    except FileNotFoundError as exc:
        raise PromptLoadError(
            f"agent prompt file not found: {prompt_path}"
        ) from exc
    except OSError as exc:
        raise PromptLoadError(
            f"cannot read agent prompt file: {prompt_path}"
        ) from exc

    if size > MAX_PROMPT_BYTES:
        raise PromptLoadError(
            f"agent prompt file exceeds {MAX_PROMPT_BYTES} bytes: {prompt_path}"
        )

    try:
        prompt = prompt_path.read_text(encoding="utf-8").strip()
    except UnicodeDecodeError as exc:
        raise PromptLoadError(
            f"agent prompt file is not valid UTF-8: {prompt_path}"
        ) from exc
    except OSError as exc:
        raise PromptLoadError(
            f"cannot read agent prompt file: {prompt_path}"
        ) from exc

    if not prompt:
        raise PromptLoadError(f"agent prompt file is empty: {prompt_path}")
    return prompt
