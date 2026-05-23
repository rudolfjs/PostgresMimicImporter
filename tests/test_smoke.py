"""Smoke tests: confirm every importable module loads cleanly."""

from __future__ import annotations

import importlib

import pytest

MODULES = [
    "pgmimic.main",
    "pgmimic._config._config_handler",
    "pgmimic._config.models",
    "pgmimic._db._db_handler",
    "pgmimic._files._file_handler",
    "pgmimic.importer.mimic_importer",
]


@pytest.mark.parametrize("module", MODULES)
def test_module_imports(module: str) -> None:
    importlib.import_module(module)
