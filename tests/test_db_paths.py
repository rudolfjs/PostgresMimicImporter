"""Regression: SQL files referenced by `DataHandler` must resolve regardless of CWD."""

from __future__ import annotations

import pytest


@pytest.fixture
def chdir_tmp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_data_handler_exposes_package_relative_sql_dir(chdir_tmp):
    from pgmimic._db._db_handler import DataHandler

    sql_dir = DataHandler.SQL_DIR
    assert sql_dir.is_dir(), f"SQL_DIR {sql_dir} should be a real directory"


@pytest.mark.parametrize(
    "version,filename",
    [
        ("2.2", "constraint.sql"),
        ("2.2", "index.sql"),
        ("2.2", "create.sql"),
        ("2.2", "postgres-functions.sql"),
        ("3.1", "constraint.sql"),
        ("3.1", "index.sql"),
        ("3.1", "create.sql"),
        ("3.1", "postgres-functions.sql"),
    ],
)
def test_known_sql_assets_resolve_independently_of_cwd(chdir_tmp, version, filename):
    from pgmimic._db._db_handler import DataHandler

    assert (DataHandler.SQL_DIR / version / filename).is_file()


def test_3_1_create_includes_ed_schema():
    """3.1 create.sql must include the carried-forward ED schema + tables."""
    from pgmimic._db._db_handler import DataHandler

    create_sql = (DataHandler.SQL_DIR / "3.1" / "create.sql").read_text()
    assert "CREATE SCHEMA mimiciv_ed" in create_sql
    for table in ("diagnosis", "edstays", "medrecon", "pyxis", "triage", "vitalsign"):
        assert f"mimiciv_ed.{table}" in create_sql, f"3.1 ED table {table} missing"


def test_3_1_create_includes_new_hosp_tables():
    """3.1 introduces drgcodes, provider, services in mimiciv_hosp."""
    from pgmimic._db._db_handler import DataHandler

    create_sql = (DataHandler.SQL_DIR / "3.1" / "create.sql").read_text()
    for table in ("drgcodes", "provider", "services"):
        assert f"mimiciv_hosp.{table}" in create_sql, f"3.1 hosp table {table} missing"


def test_3_1_create_includes_new_icu_table():
    """3.1 introduces caregiver in mimiciv_icu."""
    from pgmimic._db._db_handler import DataHandler

    create_sql = (DataHandler.SQL_DIR / "3.1" / "create.sql").read_text()
    assert "mimiciv_icu.caregiver" in create_sql
