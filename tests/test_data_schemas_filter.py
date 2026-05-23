"""Schemas whose `tables` entry is a dict (e.g. `mimic_derived` /
`mimiciv_derived`) hold SQL-function outputs, not raw data CSVs, and
must be skipped by both `_check_data` and `_write_mimic_data`.

Bug being fixed: `_write_mimic_data` hardcoded `if schema == "mimic_derived"`,
which silently failed to skip 3.1's `mimiciv_derived` schema. The loop
then iterated the dict `{"demographics": ["age"]}` as if it were a
table list, hit `_file_for_table(files, "demographics")`, and raised
`FileNotFoundError`. The fix dispatches on value type, not name —
keeps the rule version-agnostic.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


def _config(*, schemas: list[str], tables: dict) -> object:
    from pgmimic._config.models import Config

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
                "version": "test",
                "schemas": schemas,
                "tables": tables,
            },
        }
    )


@pytest.fixture
def fake_handler(monkeypatch):
    from pgmimic._db import _db_handler as db_mod

    mock_conn = MagicMock(name="conn")
    monkeypatch.setattr(db_mod.psycopg2, "connect", lambda **_: mock_conn)
    mock_run = MagicMock(name="subprocess.run", return_value=MagicMock(returncode=0))
    monkeypatch.setattr(db_mod.subprocess, "run", mock_run)

    def _build(cfg):
        return db_mod.DataHandler(cfg), mock_conn, mock_run

    return _build


def _copied_schemas(mock_run) -> list[str]:
    """Extract the `<schema>.<table>` targets the importer COPYed to."""
    targets: list[str] = []
    for call in mock_run.call_args_list:
        args = call.args[0] if call.args else call.kwargs.get("args", [])
        if not args or args[0] != "psql":
            continue
        cmd = args[-1]  # `-c <command>` — the COPY string
        if "\\copy" in cmd:
            targets.append(cmd.split()[1])
    return targets


def test_22_path_still_skips_mimic_derived(fake_handler):
    """Existing 2.2 behaviour preserved — `mimic_derived` schema not COPYed."""
    cfg = _config(
        schemas=["mimic_hosp", "mimic_derived"],
        tables={
            "mimic_hosp": ["admissions"],
            "mimic_derived": {"demographics": ["age"]},
        },
    )
    handler, _conn, mock_run = fake_handler(cfg)
    handler._write_mimic_data(["/data/admissions.csv.gz"])

    targets = _copied_schemas(mock_run)
    assert targets == ["mimic_hosp.admissions"]
    assert not any(t.startswith("mimic_derived") for t in targets)


def test_31_path_skips_mimiciv_derived(fake_handler):
    """The new 3.1 schema name `mimiciv_derived` must also be skipped."""
    cfg = _config(
        schemas=["mimiciv_hosp", "mimiciv_derived"],
        tables={
            "mimiciv_hosp": ["admissions"],
            "mimiciv_derived": {"demographics": ["age"]},
        },
    )
    handler, _conn, mock_run = fake_handler(cfg)
    handler._write_mimic_data(["/data/admissions.csv.gz"])

    targets = _copied_schemas(mock_run)
    assert targets == ["mimiciv_hosp.admissions"]
    assert not any(t.startswith("mimiciv_derived") for t in targets)


def test_any_dict_valued_schema_is_skipped(fake_handler):
    """The rule is type-based: dict value → skip, list value → load. Name doesn't matter."""
    cfg = _config(
        schemas=["mimic_hosp", "future_concept_schema"],
        tables={
            "mimic_hosp": ["admissions"],
            "future_concept_schema": {"some_subdir": ["some_view"]},
        },
    )
    handler, _conn, mock_run = fake_handler(cfg)
    handler._write_mimic_data(["/data/admissions.csv.gz"])

    targets = _copied_schemas(mock_run)
    assert targets == ["mimic_hosp.admissions"]


def test_check_data_skips_dict_valued_schemas(fake_handler):
    """`_check_data` must use the same skip rule, otherwise it queries
    for `demographics` as a table inside `mimiciv_derived` (which is a
    function, not a table) and always returns False — forcing a
    re-import even when the real tables are populated."""
    cfg = _config(
        schemas=["mimiciv_hosp", "mimiciv_derived"],
        tables={
            "mimiciv_hosp": ["admissions"],
            "mimiciv_derived": {"demographics": ["age"]},
        },
    )
    handler, mock_conn, _run = fake_handler(cfg)

    mock_cur = MagicMock(name="cursor")
    mock_cur.fetchone.return_value = (True,)
    mock_conn.cursor.return_value = mock_cur

    assert handler._check_data() is True

    queried_tables: list[str] = []
    for call in mock_cur.execute.call_args_list:
        sql = call.args[0]
        for line in sql.splitlines():
            line = line.strip()
            if line.startswith("table_name="):
                queried_tables.append(line.split("'", 2)[1])
    assert "admissions" in queried_tables
    assert "demographics" not in queried_tables
