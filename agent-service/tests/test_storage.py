import sqlite3
from pathlib import Path

from agent_service.storage import ConversationStore


def test_model_context_excludes_failed_assistant_messages(
    tmp_path: Path,
) -> None:
    store = ConversationStore(tmp_path / "history.db")
    conversation_id = store.create_conversation(1, "第一轮")
    store.add_message(conversation_id, "user", "第一轮", "completed")
    store.add_message(conversation_id, "assistant", "成功回复", "completed")
    store.add_message(conversation_id, "user", "第二轮", "completed")
    store.add_message(conversation_id, "assistant", "失败回复", "failed")

    context = store.model_context(conversation_id)

    assert [message.content for message in context] == [
        "第一轮",
        "成功回复",
        "第二轮",
    ]


def test_interrupted_stream_is_recovered_as_failed(tmp_path: Path) -> None:
    database_path = tmp_path / "recovery.db"
    store = ConversationStore(database_path)
    conversation_id = store.create_conversation(1, "中断")
    message_id = store.add_message(
        conversation_id,
        "assistant",
        "",
        "streaming",
    )

    recovered_store = ConversationStore(database_path)
    conversation = recovered_store.get_conversation(1, conversation_id)

    assert conversation is not None
    assert conversation.messages[0].id == message_id
    assert conversation.messages[0].status == "failed"


def test_existing_database_is_migrated_with_message_metadata(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "legacy.db"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE conversations (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                status TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            INSERT INTO conversations
                VALUES ('conversation-old', 1, '旧对话', '2026-01-01', '2026-01-01');
            INSERT INTO messages
                VALUES (
                    'message-old',
                    'conversation-old',
                    'assistant',
                    '旧回复',
                    'completed',
                    1,
                    '2026-01-01'
                );
            """
        )

    store = ConversationStore(database_path)
    conversation = store.get_conversation(1, "conversation-old")

    assert conversation is not None
    assert conversation.messages[0].content == "旧回复"
    assert conversation.messages[0].recommendations == []
    assert conversation.messages[0].tool_trace == []
