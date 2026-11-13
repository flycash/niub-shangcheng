import asyncio
from datetime import datetime, timedelta
from pathlib import Path

from agent_service.conversation_summary import ConversationSummaryError
from agent_service.conversation_summary_worker import (
    ConversationSummarySettings,
    ConversationSummaryWorker,
)
from agent_service.models import ConversationDigest, ConversationDetail
from agent_service.storage import ConversationStore, utc_now


def _settings() -> ConversationSummarySettings:
    return ConversationSummarySettings(
        interval_seconds=3_600,
        idle_seconds=3_600,
        batch_size=50,
    )


def _digest(
    conversation_id: str,
    source_updated_at: str,
) -> ConversationDigest:
    return ConversationDigest(
        conversation_id=conversation_id,
        source_updated_at=source_updated_at,
        summary="用户咨询了商品推荐。",
        generated_at=utc_now(),
    )


def _later_than(updated_at: str, *, hours: int = 2) -> datetime:
    return datetime.fromisoformat(updated_at) + timedelta(hours=hours)


class RecordingSummarizer:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def summarize(
        self,
        *,
        conversation: ConversationDetail,
        source_updated_at: str,
    ) -> ConversationDigest:
        self.calls.append(source_updated_at)
        return _digest(conversation.id, source_updated_at)


class UpdatingSummarizer(RecordingSummarizer):
    def __init__(self, store: ConversationStore) -> None:
        super().__init__()
        self.store = store
        self.updated = False

    async def summarize(
        self,
        *,
        conversation: ConversationDetail,
        source_updated_at: str,
    ) -> ConversationDigest:
        if not self.updated:
            self.updated = True
            self.store.add_message(
                conversation.id,
                "user",
                "我又补充一个需求",
                "completed",
            )
        return await super().summarize(
            conversation=conversation,
            source_updated_at=source_updated_at,
        )


class FailingSummarizer:
    async def summarize(
        self,
        *,
        conversation: ConversationDetail,
        source_updated_at: str,
    ) -> ConversationDigest:
        raise ConversationSummaryError("model unavailable")


def _conversation(store: ConversationStore) -> ConversationDetail:
    conversation_id = store.create_conversation(1, "推荐通勤包")
    store.add_message(
        conversation_id,
        "user",
        "推荐一个通勤包",
        "completed",
    )
    store.add_message(
        conversation_id,
        "assistant",
        "推荐这款通勤包。",
        "completed",
    )
    conversation = store.get_conversation(1, conversation_id)
    assert conversation is not None
    return conversation


def test_worker_only_summarizes_idle_conversations(tmp_path: Path) -> None:
    store = ConversationStore(tmp_path / "summary.db")
    conversation = _conversation(store)
    summarizer = RecordingSummarizer()
    worker = ConversationSummaryWorker(
        store,
        settings=_settings(),
        summarizer=summarizer,
        summarizer_model="test-summary-model",
    )

    recent = asyncio.run(
        worker.run_once(now=datetime.fromisoformat(conversation.updated_at))
    )
    assert recent.completed == 0
    assert summarizer.calls == []

    due = asyncio.run(
        worker.run_once(now=_later_than(conversation.updated_at))
    )
    assert due.completed == 1
    assert summarizer.calls == [conversation.updated_at]
    stored = store.get_conversation_summary(1, conversation.id)
    assert stored is not None
    assert stored.source_updated_at == conversation.updated_at


def test_worker_reuses_summary_until_conversation_timestamp_changes(
    tmp_path: Path,
) -> None:
    store = ConversationStore(tmp_path / "summary.db")
    conversation = _conversation(store)
    summarizer = RecordingSummarizer()
    worker = ConversationSummaryWorker(
        store,
        settings=_settings(),
        summarizer=summarizer,
        summarizer_model="test-summary-model",
    )
    first_now = _later_than(conversation.updated_at)

    asyncio.run(worker.run_once(now=first_now))
    unchanged = asyncio.run(worker.run_once(now=first_now))

    assert unchanged.completed == 0
    assert len(summarizer.calls) == 1

    store.add_message(
        conversation.id,
        "user",
        "再看看更小尺寸的",
        "completed",
    )
    updated = store.get_conversation(1, conversation.id)
    assert updated is not None

    refreshed = asyncio.run(
        worker.run_once(now=_later_than(updated.updated_at))
    )
    assert refreshed.completed == 1
    assert len(summarizer.calls) == 2
    stored = store.get_conversation_summary(1, conversation.id)
    assert stored is not None
    assert stored.source_updated_at == updated.updated_at


def test_worker_saves_old_snapshot_when_conversation_changes_during_summary(
    tmp_path: Path,
) -> None:
    store = ConversationStore(tmp_path / "summary.db")
    conversation = _conversation(store)
    summarizer = UpdatingSummarizer(store)
    worker = ConversationSummaryWorker(
        store,
        settings=_settings(),
        summarizer=summarizer,
        summarizer_model="test-summary-model",
    )

    result = asyncio.run(
        worker.run_once(now=_later_than(conversation.updated_at))
    )

    assert result.completed == 1
    stored = store.get_conversation_summary(1, conversation.id)
    assert stored is not None
    assert stored.source_updated_at == conversation.updated_at
    updated = store.get_conversation(1, conversation.id)
    assert updated is not None
    assert updated.updated_at > stored.source_updated_at

    due = store.list_conversations_due_for_summary(
        _later_than(updated.updated_at).isoformat(timespec="milliseconds")
    )
    assert [candidate.conversation_id for candidate in due] == [
        conversation.id
    ]


def test_failed_summary_is_retried_on_next_cycle(tmp_path: Path) -> None:
    store = ConversationStore(tmp_path / "summary.db")
    conversation = _conversation(store)
    worker = ConversationSummaryWorker(
        store,
        settings=_settings(),
        summarizer=FailingSummarizer(),
        summarizer_model="test-summary-model",
    )
    now = _later_than(conversation.updated_at)

    first = asyncio.run(worker.run_once(now=now))
    second = asyncio.run(worker.run_once(now=now))

    assert first.failed == 1
    assert second.failed == 1
    assert store.get_conversation_summary(1, conversation.id) is None
