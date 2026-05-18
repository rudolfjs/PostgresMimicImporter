"""Smoke tests: confirm every importable module loads cleanly."""

from __future__ import annotations

import importlib

import pytest

MODULES = [
    "main",
    "_config._config_handler",
    "_db._db_handler",
    "_files._file_handler",
    "importer.mimic_importer",
]


@pytest.mark.parametrize("module", MODULES)
def test_module_imports(module: str) -> None:
    importlib.import_module(module)
