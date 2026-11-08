import sqlite3
from contextlib import contextmanager
from typing import Any, Iterator

from opentelemetry import trace
from opentelemetry.trace import SpanKind, Status, StatusCode

from .serialization import truncate_text
from .spans import get_tracer


def sql_operation(statement: str) -> str:
    normalized = " ".join(statement.strip().split())
    if not normalized:
        return "unknown"
    return normalized.split(" ", 1)[0].upper()


@contextmanager
def database_span(
    operation: str,
    *,
    statement: str | None = None,
) -> Iterator[Any]:
    span = get_tracer().start_span(
        "db.connect" if operation == "CONNECT" else "db.query",
        kind=SpanKind.CLIENT,
    )
    span.set_attribute("db.system", "sqlite")
    span.set_attribute("db.operation", operation)
    if statement is not None:
        span.set_attribute(
            "db.statement",
            truncate_text(" ".join(statement.split()), 2000),
        )
    with trace.use_span(span, end_on_exit=False):
        try:
            yield span
        except BaseException as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise
        else:
            span.set_status(Status(StatusCode.OK))
        finally:
            span.end()


class ObservedCursor:
    def __init__(
        self,
        cursor: sqlite3.Cursor,
        statement: str,
    ) -> None:
        self._cursor = cursor
        self._statement = statement

    def fetchone(self) -> Any:
        with database_span(
            "FETCH",
            statement=self._statement,
        ):
            return self._cursor.fetchone()

    def fetchmany(self, size: int | None = None) -> Any:
        with database_span(
            "FETCHMANY",
            statement=self._statement,
        ):
            return (
                self._cursor.fetchmany(size)
                if size is not None
                else self._cursor.fetchmany()
            )

    def fetchall(self) -> Any:
        with database_span(
            "FETCHALL",
            statement=self._statement,
        ):
            return self._cursor.fetchall()

    def __iter__(self) -> Any:
        with database_span(
            "ITERATE",
            statement=self._statement,
        ):
            return iter(list(self._cursor))

    def __getattr__(self, name: str) -> Any:
        return getattr(self._cursor, name)


class ObservedConnection:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def execute(
        self,
        statement: str,
        parameters: Any = (),
    ) -> ObservedCursor:
        with database_span(
            sql_operation(statement),
            statement=statement,
        ):
            cursor = self._connection.execute(statement, parameters)
        return ObservedCursor(cursor, statement)

    def executemany(
        self,
        statement: str,
        parameters: Any,
    ) -> ObservedCursor:
        with database_span(
            sql_operation(statement),
            statement=statement,
        ):
            cursor = self._connection.executemany(statement, parameters)
        return ObservedCursor(cursor, statement)

    def executescript(self, script: str) -> ObservedCursor:
        with database_span("EXECUTESCRIPT", statement=script):
            cursor = self._connection.executescript(script)
        return ObservedCursor(cursor, script)

    def cursor(self) -> ObservedCursor:
        return ObservedCursor(self._connection.cursor(), "")

    def commit(self) -> None:
        with database_span("COMMIT"):
            self._connection.commit()

    def rollback(self) -> None:
        with database_span("ROLLBACK"):
            self._connection.rollback()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "ObservedConnection":
        self._connection.__enter__()
        return self

    def __exit__(
        self,
        exc_type: Any,
        exc_value: Any,
        traceback: Any,
    ) -> Any:
        operation = "ROLLBACK" if exc_type is not None else "COMMIT"
        with database_span(operation):
            return self._connection.__exit__(
                exc_type,
                exc_value,
                traceback,
            )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._connection, name)
