import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from .models import (
    ConversationDigest,
    ConversationDetail,
    ConversationSummary,
    GoalUnderstandingResult,
    OrderLink,
    PlanState,
    Product,
    RecommendationDecision,
    RecommendationSpec,
    StoredMessage,
    ToolTrace,
)
from .observability.database import ObservedConnection, database_span
from .observability.spans import repository_operation

FIXED_USER_ID = 1


@dataclass(frozen=True)
class ConversationSummaryCandidate:
    conversation_id: str
    user_id: int
    updated_at: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class ConversationStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> ObservedConnection:
        with database_span("CONNECT"):
            connection = sqlite3.connect(self.database_path, timeout=5)
            connection.row_factory = sqlite3.Row
        with database_span(
            "PRAGMA",
            statement="PRAGMA foreign_keys = ON",
        ):
            connection.execute("PRAGMA foreign_keys = ON")
        return ObservedConnection(connection)

    @repository_operation("conversation.initialize")
    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode = WAL;

                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    status TEXT NOT NULL
                        CHECK (status IN ('streaming', 'completed', 'failed')),
                    sequence INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    FOREIGN KEY (conversation_id)
                        REFERENCES conversations(id)
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_conversations_user_updated
                    ON conversations(user_id, updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_sequence
                    ON messages(conversation_id, sequence);

                CREATE TABLE IF NOT EXISTS conversation_summaries (
                    conversation_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL
                        CHECK (status IN ('completed', 'failed')),
                    source_updated_at TEXT NOT NULL,
                    summary_json TEXT,
                    prompt_version TEXT NOT NULL,
                    summarizer_model TEXT NOT NULL,
                    generated_at TEXT,
                    last_attempt_at TEXT NOT NULL,
                    error TEXT,
                    FOREIGN KEY (conversation_id)
                        REFERENCES conversations(id)
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_conversation_summaries_status
                    ON conversation_summaries(status, source_updated_at);

                UPDATE messages
                SET status = 'failed'
                WHERE status = 'streaming';
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(messages)")
            }
            if "metadata" not in columns:
                connection.execute(
                    "ALTER TABLE messages ADD COLUMN metadata TEXT NOT NULL DEFAULT '{}'"
                )

    @repository_operation("conversation.create")
    def create_conversation(self, user_id: int, first_message: str) -> str:
        conversation_id = f"conversation-{uuid4().hex}"
        title = " ".join(first_message.split())[:40] or "新对话"
        now = utc_now()
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO conversations(id, user_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (conversation_id, user_id, title, now, now),
            )
        return conversation_id

    @repository_operation("conversation.exists")
    def conversation_exists(self, user_id: int, conversation_id: str) -> bool:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT 1 FROM conversations
                WHERE id = ? AND user_id = ?
                """,
                (conversation_id, user_id),
            ).fetchone()
        return row is not None

    @repository_operation("message.create")
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        status: str,
        metadata: dict[str, object] | None = None,
    ) -> str:
        message_id = f"message-{uuid4().hex}"
        now = utc_now()
        with self.connect() as connection:
            sequence_row = connection.execute(
                """
                SELECT COALESCE(MAX(sequence), 0) + 1
                FROM messages
                WHERE conversation_id = ?
                """,
                (conversation_id,),
            ).fetchone()
            sequence = int(sequence_row[0])
            connection.execute(
                """
                INSERT INTO messages(
                    id, conversation_id, role, content, status, sequence,
                    created_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    conversation_id,
                    role,
                    content,
                    status,
                    sequence,
                    now,
                    json.dumps(metadata or {}, ensure_ascii=False),
                ),
            )
            connection.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conversation_id),
            )
        return message_id

    @repository_operation("message.finish")
    def finish_message(
        self,
        message_id: str,
        content: str,
        status: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        now = utc_now()
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE messages
                SET content = ?, status = ?, metadata = ?
                WHERE id = ? AND status = 'streaming'
                """,
                (
                    content,
                    status,
                    json.dumps(metadata or {}, ensure_ascii=False),
                    message_id,
                ),
            )
            row = connection.execute(
                "SELECT conversation_id FROM messages WHERE id = ?",
                (message_id,),
            ).fetchone()
            if row is not None:
                connection.execute(
                    "UPDATE conversations SET updated_at = ? WHERE id = ?",
                    (now, row["conversation_id"]),
                )

    @repository_operation("conversation.list")
    def list_conversations(self, user_id: int) -> list[ConversationSummary]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    c.id,
                    c.title,
                    c.created_at,
                    c.updated_at,
                    COUNT(m.id) AS message_count
                FROM conversations c
                LEFT JOIN messages m ON m.conversation_id = c.id
                WHERE c.user_id = ?
                GROUP BY c.id
                ORDER BY c.updated_at DESC
                """,
                (user_id,),
            ).fetchall()
        return [
            ConversationSummary(
                id=row["id"],
                title=row["title"],
                message_count=row["message_count"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    @repository_operation("conversation.get")
    def get_conversation(
        self,
        user_id: int,
        conversation_id: str,
    ) -> ConversationDetail | None:
        with self.connect() as connection:
            conversation = connection.execute(
                """
                SELECT id, title, created_at, updated_at
                FROM conversations
                WHERE id = ? AND user_id = ?
                """,
                (conversation_id, user_id),
            ).fetchone()
            if conversation is None:
                return None

            messages = connection.execute(
                """
                SELECT id, role, content, status, created_at, metadata
                FROM messages
                WHERE conversation_id = ?
                ORDER BY sequence ASC
                """,
                (conversation_id,),
            ).fetchall()

        return ConversationDetail(
            id=conversation["id"],
            title=conversation["title"],
            message_count=len(messages),
            created_at=conversation["created_at"],
            updated_at=conversation["updated_at"],
            messages=[self._stored_message(message) for message in messages],
        )

    @repository_operation("conversation.model_context")
    def model_context(self, conversation_id: str) -> list[StoredMessage]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, role, content, status, created_at, metadata
                FROM messages
                WHERE conversation_id = ?
                  AND (role = 'user' OR status = 'completed')
                ORDER BY sequence ASC
                """,
                (conversation_id,),
            ).fetchall()
        return [self._stored_message(row) for row in rows]

    @repository_operation("conversation_summary.list_due")
    def list_conversations_due_for_summary(
        self,
        cutoff: str,
        *,
        limit: int = 50,
    ) -> list[ConversationSummaryCandidate]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT c.id, c.user_id, c.updated_at
                FROM conversations c
                LEFT JOIN conversation_summaries s
                    ON s.conversation_id = c.id
                WHERE c.updated_at <= ?
                  AND (
                      s.conversation_id IS NULL
                      OR s.status = 'failed'
                      OR s.summary_json IS NULL
                      OR s.source_updated_at < c.updated_at
                  )
                ORDER BY c.updated_at ASC
                LIMIT ?
                """,
                (cutoff, limit),
            ).fetchall()
        return [
            ConversationSummaryCandidate(
                conversation_id=row["id"],
                user_id=row["user_id"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    @repository_operation("conversation_summary.get")
    def get_conversation_summary(
        self,
        user_id: int,
        conversation_id: str,
    ) -> ConversationDigest | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT s.summary_json
                FROM conversation_summaries s
                JOIN conversations c ON c.id = s.conversation_id
                WHERE c.id = ?
                  AND c.user_id = ?
                  AND s.summary_json IS NOT NULL
                """,
                (conversation_id, user_id),
            ).fetchone()
        if row is None:
            return None
        try:
            return ConversationDigest.model_validate_json(row["summary_json"])
        except ValueError:
            return None

    @repository_operation("conversation_summary.save")
    def save_conversation_summary(
        self,
        digest: ConversationDigest,
        *,
        prompt_version: str,
        summarizer_model: str,
    ) -> None:
        now = utc_now()
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO conversation_summaries(
                    conversation_id,
                    status,
                    source_updated_at,
                    summary_json,
                    prompt_version,
                    summarizer_model,
                    generated_at,
                    last_attempt_at,
                    error
                )
                VALUES (?, 'completed', ?, ?, ?, ?, ?, ?, NULL)
                ON CONFLICT(conversation_id) DO UPDATE SET
                    status = 'completed',
                    source_updated_at = excluded.source_updated_at,
                    summary_json = excluded.summary_json,
                    prompt_version = excluded.prompt_version,
                    summarizer_model = excluded.summarizer_model,
                    generated_at = excluded.generated_at,
                    last_attempt_at = excluded.last_attempt_at,
                    error = NULL
                """,
                (
                    digest.conversation_id,
                    digest.source_updated_at,
                    digest.model_dump_json(),
                    prompt_version,
                    summarizer_model,
                    digest.generated_at,
                    now,
                ),
            )

    @repository_operation("conversation_summary.fail")
    def record_conversation_summary_failure(
        self,
        conversation_id: str,
        *,
        source_updated_at: str,
        prompt_version: str,
        summarizer_model: str,
        error: str,
    ) -> None:
        now = utc_now()
        with self.connect() as connection:
            existing = connection.execute(
                """
                SELECT 1 FROM conversation_summaries
                WHERE conversation_id = ?
                """,
                (conversation_id,),
            ).fetchone()
            if existing is None:
                connection.execute(
                    """
                    INSERT INTO conversation_summaries(
                        conversation_id,
                        status,
                        source_updated_at,
                        summary_json,
                        prompt_version,
                        summarizer_model,
                        generated_at,
                        last_attempt_at,
                        error
                    )
                    VALUES (?, 'failed', ?, NULL, ?, ?, NULL, ?, ?)
                    """,
                    (
                        conversation_id,
                        source_updated_at,
                        prompt_version,
                        summarizer_model,
                        now,
                        error,
                    ),
                )
                return
            connection.execute(
                """
                UPDATE conversation_summaries
                SET status = 'failed',
                    last_attempt_at = ?,
                    error = ?
                WHERE conversation_id = ?
                """,
                (now, error, conversation_id),
            )

    @staticmethod
    def _stored_message(row: sqlite3.Row) -> StoredMessage:
        try:
            metadata = json.loads(row["metadata"] or "{}")
        except (json.JSONDecodeError, TypeError):
            metadata = {}
        if not isinstance(metadata, dict):
            metadata = {}

        recommendations = [
            Product.model_validate(product)
            for product in metadata.get("recommendations", [])
            if isinstance(product, dict)
        ]
        tool_trace = [
            ToolTrace.model_validate(trace)
            for trace in metadata.get("tool_trace", [])
            if isinstance(trace, dict)
        ]
        plan_state: PlanState | None = None
        if isinstance(metadata.get("plan_state"), dict):
            try:
                plan_state = PlanState.model_validate(metadata["plan_state"])
            except ValueError:
                plan_state = None
        goal_understanding: GoalUnderstandingResult | None = None
        if isinstance(metadata.get("goal_understanding"), dict):
            try:
                goal_understanding = GoalUnderstandingResult.model_validate(
                    metadata["goal_understanding"]
                )
            except ValueError:
                goal_understanding = None
        recommendation_spec: RecommendationSpec | None = None
        if isinstance(metadata.get("recommendation_spec"), dict):
            try:
                recommendation_spec = RecommendationSpec.model_validate(
                    metadata["recommendation_spec"]
                )
            except ValueError:
                recommendation_spec = None
        recommendation_decision: RecommendationDecision | None = None
        if isinstance(metadata.get("recommendation_decision"), dict):
            try:
                recommendation_decision = (
                    RecommendationDecision.model_validate(
                        metadata["recommendation_decision"]
                    )
                )
            except ValueError:
                recommendation_decision = None
        orders = [
            OrderLink.model_validate(order)
            for order in metadata.get("orders", [])
            if isinstance(order, dict)
        ]
        return StoredMessage(
            id=row["id"],
            role=row["role"],
            content=row["content"],
            status=row["status"],
            created_at=row["created_at"],
            recommendations=recommendations,
            tool_trace=tool_trace,
            plan_state=plan_state,
            goal_understanding=goal_understanding,
            recommendation_spec=recommendation_spec,
            orders=orders,
            recommendation_decision=recommendation_decision,
        )


def default_database_path() -> Path:
    configured = os.getenv("AGENT_DB_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[2] / "data" / "agent.db"


@lru_cache
def get_conversation_store() -> ConversationStore:
    return ConversationStore(default_database_path())
