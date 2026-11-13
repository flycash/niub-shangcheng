import asyncio
import logging
import os
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from agents import OpenAIChatCompletionsModel
from openai import AsyncOpenAI

from .agent_runner import normalize_openai_base_url
from .conversation_summary import (
    CONVERSATION_SUMMARY_PROMPT_VERSION,
    AgentConversationSummarizer,
    ConversationSummarizer,
)
from .llm_config import LLMConfig, load_llm_config
from .models import ConversationDetail, ConversationDigest
from .storage import ConversationStore, ConversationSummaryCandidate


logger = logging.getLogger(__name__)

DEFAULT_SUMMARY_INTERVAL_SECONDS = 3_600
DEFAULT_SUMMARY_IDLE_SECONDS = 3_600
DEFAULT_SUMMARY_BATCH_SIZE = 50


# Scheduling assumption:
# This worker does not acquire per-conversation locks or leases. The deployment
# must guarantee exactly one scheduler invocation at a time, either through one
# scheduler node or an external distributed scheduler. Concurrent execution for
# the same conversation is explicitly out of scope.


# TODO(conversation-summary-freshness):
# A conversation has no usable summary until it has been idle long enough and
# the next summary job has completed. Conversation recall must fall back to raw
# completed turns whenever the digest is absent or stale.


@dataclass(frozen=True)
class ConversationSummarySettings:
    interval_seconds: int = DEFAULT_SUMMARY_INTERVAL_SECONDS
    idle_seconds: int = DEFAULT_SUMMARY_IDLE_SECONDS
    batch_size: int = DEFAULT_SUMMARY_BATCH_SIZE
    enabled: bool = True


@dataclass(frozen=True)
class ConversationSummaryCycleResult:
    completed: int = 0
    failed: int = 0
    skipped: int = 0


def load_conversation_summary_settings() -> ConversationSummarySettings:
    return ConversationSummarySettings(
        interval_seconds=_positive_int_env(
            "CONVERSATION_SUMMARY_INTERVAL_SECONDS",
            DEFAULT_SUMMARY_INTERVAL_SECONDS,
        ),
        idle_seconds=_positive_int_env(
            "CONVERSATION_SUMMARY_IDLE_SECONDS",
            DEFAULT_SUMMARY_IDLE_SECONDS,
        ),
        batch_size=_positive_int_env(
            "CONVERSATION_SUMMARY_BATCH_SIZE",
            DEFAULT_SUMMARY_BATCH_SIZE,
        ),
        enabled=_bool_env("CONVERSATION_SUMMARY_SCHEDULER_ENABLED", True),
    )


def _positive_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError:
        logger.warning("invalid %s=%r; using %s", name, value, default)
        return default
    if parsed <= 0:
        logger.warning("non-positive %s=%r; using %s", name, value, default)
        return default
    return parsed


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


@asynccontextmanager
async def configured_conversation_summarizer(
    config_loader: Callable[[], LLMConfig] = load_llm_config,
) -> AsyncIterator[tuple[ConversationSummarizer, str]]:
    config = config_loader()
    client = AsyncOpenAI(
        api_key=config.api_key.get_secret_value(),
        base_url=normalize_openai_base_url(config.base_url),
        timeout=config.model_timeout_limit,
        max_retries=1,
    )
    try:
        model = OpenAIChatCompletionsModel(
            model=config.model,
            openai_client=client,
            buffer_streamed_tool_calls=True,
        )
        yield (
            AgentConversationSummarizer(config=config, model=model),
            config.model,
        )
    finally:
        await client.close()


async def summarize_and_store_conversation(
    store: ConversationStore,
    *,
    conversation: ConversationDetail,
    source_updated_at: str,
    summarizer: ConversationSummarizer,
    summarizer_model: str,
) -> ConversationDigest:
    try:
        digest = await summarizer.summarize(
            conversation=conversation,
            source_updated_at=source_updated_at,
        )
        store.save_conversation_summary(
            digest,
            prompt_version=CONVERSATION_SUMMARY_PROMPT_VERSION,
            summarizer_model=summarizer_model,
        )
        return digest
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        store.record_conversation_summary_failure(
            conversation.id,
            source_updated_at=source_updated_at,
            prompt_version=CONVERSATION_SUMMARY_PROMPT_VERSION,
            summarizer_model=summarizer_model,
            error=f"{type(exc).__name__}: {exc}",
        )
        raise


class ConversationSummaryWorker:
    def __init__(
        self,
        store: ConversationStore,
        *,
        settings: ConversationSummarySettings | None = None,
        summarizer: ConversationSummarizer | None = None,
        summarizer_model: str | None = None,
        config_loader: Callable[[], LLMConfig] = load_llm_config,
    ) -> None:
        self.store = store
        self.settings = settings or load_conversation_summary_settings()
        self.summarizer = summarizer
        self.summarizer_model = summarizer_model
        self.config_loader = config_loader

    async def run_forever(self) -> None:
        while True:
            try:
                await self.run_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("conversation summary cycle failed")
            await asyncio.sleep(self.settings.interval_seconds)

    async def run_once(
        self,
        *,
        now: datetime | None = None,
    ) -> ConversationSummaryCycleResult:
        current_time = now or datetime.now(timezone.utc)
        cutoff = (current_time - timedelta(
            seconds=self.settings.idle_seconds
        )).isoformat(timespec="milliseconds")
        candidates = self.store.list_conversations_due_for_summary(
            cutoff,
            limit=self.settings.batch_size,
        )
        if not candidates:
            return ConversationSummaryCycleResult()

        if self.summarizer is not None:
            return await self._run_candidates(
                candidates,
                summarizer=self.summarizer,
                model_name=self.summarizer_model or "injected-summarizer",
            )
        async with configured_conversation_summarizer(
            self.config_loader
        ) as (summarizer, model_name):
            return await self._run_candidates(
                candidates,
                summarizer=summarizer,
                model_name=model_name,
            )

    async def _run_candidates(
        self,
        candidates: list[ConversationSummaryCandidate],
        *,
        summarizer: ConversationSummarizer,
        model_name: str,
    ) -> ConversationSummaryCycleResult:
        completed = 0
        failed = 0
        skipped = 0
        for candidate in candidates:
            conversation = self.store.get_conversation(
                candidate.user_id,
                candidate.conversation_id,
            )
            if conversation is None:
                skipped += 1
                continue
            try:
                await summarize_and_store_conversation(
                    self.store,
                    conversation=conversation,
                    source_updated_at=candidate.updated_at,
                    summarizer=summarizer,
                    summarizer_model=model_name,
                )
                completed += 1
            except asyncio.CancelledError:
                raise
            except Exception:
                failed += 1
                logger.exception(
                    "conversation summary failed for %s",
                    candidate.conversation_id,
                )
        return ConversationSummaryCycleResult(
            completed=completed,
            failed=failed,
            skipped=skipped,
        )
