"""DataHandler must surface SQL errors, not silently print and continue.

Bug being fixed: `_create_tables` / `_create_index` / `_create_constraint`
caught every `Exception` from `cursor.execute()`, printed `repr(e)`, and
carried on. The operator saw "MIMIC import completed" even when half the
DDL had failed — leaving the database half-populated and the next run
incorrectly skipping the create step because some tables existed.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from _config.models import Config


def _make_config(version: str) -> Config:
    """Build a Config model with a placeholder DB section (never actually dialled)."""
    from _config.models import Config

    return Config.model_validate(
        {
            "database": {
                "type": "postgresql+asyncpg",
                "host": "pg",
                "port": 5432,
                "database": "postgres",
                "schema": "public",
            },
            "data": {
                "location": "./data/mimiciv",
                "version": version,
                "schemas": ["mimic_hosp"],
                "tables": {"mimic_hosp": ["admissions"]},
            },
        }
    )


@pytest.fixture
def fake_db(tmp_path, monkeypatch):
    """A DataHandler with psycopg2 mocked out and SQL_DIR pointed at tmp_path.

    Yields (handler, mock_conn, mock_cursor). Writes to tmp_path/<version>/<file>.sql
    are the SQL the handler will execute.
    """
    from _db import _db_handler as db_mod

    mock_cursor = MagicMock(name="cursor")
    mock_conn = MagicMock(name="conn")
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.cursor.return_value.__exit__.return_value = None

    monkeypatch.setattr(db_mod.psycopg2, "connect", lambda **_: mock_conn)
    monkeypatch.setattr(db_mod.DataHandler, "SQL_DIR", tmp_path)

    version_dir = tmp_path / "test-version"
    version_dir.mkdir()

    handler = db_mod.DataHandler(_make_config("test-version"))
    yield handler, mock_conn, mock_cursor, version_dir


def test_create_tables_raises_on_bad_ddl(fake_db):
    handler, _conn, mock_cursor, version_dir = fake_db
    mock_cursor.execute.side_effect = RuntimeError("syntax error at or near 'INVALID'")
    (version_dir / "create.sql").write_text("INVALID SYNTAX HERE;")

    with pytest.raises(RuntimeError, match="syntax error"):
        handler._create_tables()


def test_create_tables_calls_rollback_on_error(fake_db):
    handler, mock_conn, mock_cursor, version_dir = fake_db
    mock_cursor.execute.side_effect = RuntimeError("boom")
    (version_dir / "create.sql").write_text("INVALID;")

    with pytest.raises(RuntimeError):
        handler._create_tables()

    mock_conn.rollback.assert_called()


def test_create_tables_commits_on_success(fake_db):
    handler, mock_conn, _cursor, version_dir = fake_db
    (version_dir / "create.sql").write_text("CREATE TABLE t (id int);")

    handler._create_tables()

    mock_conn.commit.assert_called()
    mock_conn.rollback.assert_not_called()


def test_create_index_uses_same_helper(fake_db):
    """`_create_index` and `_create_constraint` share the same error surfacing path."""
    handler, mock_conn, mock_cursor, version_dir = fake_db
    mock_cursor.execute.side_effect = RuntimeError("boom")
    (version_dir / "index.sql").write_text("CREATE INVALID INDEX;")

    with pytest.raises(RuntimeError):
        handler._create_index()

    mock_conn.rollback.assert_called()


def test_create_constraint_uses_same_helper(fake_db):
    handler, mock_conn, mock_cursor, version_dir = fake_db
    mock_cursor.execute.side_effect = RuntimeError("boom")
    (version_dir / "constraint.sql").write_text("ALTER TABLE INVALID;")

    with pytest.raises(RuntimeError):
        handler._create_constraint()

    mock_conn.rollback.assert_called()


def test_empty_statements_are_skipped(fake_db):
    """A SQL file with trailing semicolons / whitespace doesn't trip the executor."""
    handler, mock_conn, mock_cursor, version_dir = fake_db
    (version_dir / "create.sql").write_text("CREATE TABLE t (id int);\n\n  ;\n")

    handler._create_tables()

    # Two `CREATE TABLE` statements would've been called; only the non-empty one runs
    executed = [c.args[0].strip() for c in mock_cursor.execute.call_args_list]
    assert any("CREATE TABLE t" in s for s in executed)
    assert all(s for s in executed)  # no empty statements
