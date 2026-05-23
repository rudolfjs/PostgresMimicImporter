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


def test_create_tables_passes_full_file_in_single_execute(fake_db):
    """The entire SQL file is sent to the server in one `cur.execute()` call.

    We delegate statement parsing (and skipping of `;;` empties) to the postgres
    server, which has a robust SQL grammar — unlike a `sql.split(";")` loop which
    mishandles strings, comments, and dollar-quoted blocks.
    """
    handler, mock_conn, mock_cursor, version_dir = fake_db
    sql = "CREATE TABLE t (id int);\n\n  ;\n"
    (version_dir / "create.sql").write_text(sql)

    handler._create_tables()

    assert mock_cursor.execute.call_count == 1
    assert mock_cursor.execute.call_args.args[0] == sql
    mock_conn.commit.assert_called_once()


def test_create_tables_does_not_split_on_semicolons_inside_block_comments(fake_db):
    """Multi-line `/* ... ; ... */` block comments must reach the server intact.

    Regression test for the bug surfaced by the first real-data e2e run: the
    MIMIC-IV-ED appendage in `pgmimic/_db/SQL/3.1/create.sql` has a block
    comment containing a `;` ("...to a 3.1 release;"). The previous
    split-on-`;` implementation cut the comment in half, feeding postgres
    an unterminated `/*` and raising `psycopg2.errors.SyntaxError`.
    """
    handler, _conn, mock_cursor, version_dir = fake_db
    sql = (
        "/*\n"
        " * Header note;\n"
        " * second line with another; semicolon\n"
        " */\n"
        "CREATE TABLE t (id int);\n"
    )
    (version_dir / "create.sql").write_text(sql)

    handler._create_tables()

    assert mock_cursor.execute.call_count == 1
    assert mock_cursor.execute.call_args.args[0] == sql
