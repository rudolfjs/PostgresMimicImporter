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
    ],
)
def test_known_sql_assets_resolve_independently_of_cwd(chdir_tmp, version, filename):
    from pgmimic._db._db_handler import DataHandler

    assert (DataHandler.SQL_DIR / version / filename).is_file()
