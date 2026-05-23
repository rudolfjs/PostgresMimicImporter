"""Version-aware schema/table resolution.

`data.versions[data.version]` wins; legacy keys fall back.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def base_config() -> dict:
    return {
        "database": {
            "type": "postgresql+asyncpg",
            "host": "pg",
            "port": 5432,
            "database": "postgres",
            "schema": "public",
        },
        "data": {
            "location": "./data/mimiciv",
            "version": "2.2",
            "schemas": ["mimic_hosp"],
            "tables": {"mimic_hosp": ["admissions"]},
        },
    }


def test_legacy_shape_still_works(base_config, monkeypatch):
    """Config without `versions` map continues to use top-level schemas/tables."""
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    from pgmimic._config.models import Config

    cfg = Config.model_validate(base_config)
    assert cfg.data.schemas == ["mimic_hosp"]
    assert cfg.data.tables == {"mimic_hosp": ["admissions"]}


def test_versions_map_takes_precedence(base_config, monkeypatch):
    """When `versions[version]` is present, its schemas/tables override top-level."""
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    from pgmimic._config.models import Config

    cfg_dict = dict(base_config)
    cfg_dict["data"] = dict(cfg_dict["data"])
    cfg_dict["data"]["version"] = "3.1"
    cfg_dict["data"]["versions"] = {
        "3.1": {
            "schemas": ["mimiciv_hosp", "mimiciv_icu"],
            "tables": {
                "mimiciv_hosp": ["admissions", "patients"],
                "mimiciv_icu": ["icustays"],
            },
        }
    }

    cfg = Config.model_validate(cfg_dict)
    assert cfg.data.schemas == ["mimiciv_hosp", "mimiciv_icu"]
    assert cfg.data.tables["mimiciv_hosp"] == ["admissions", "patients"]
    assert cfg.data.tables["mimiciv_icu"] == ["icustays"]


def test_versions_miss_falls_back_to_legacy(base_config, monkeypatch):
    """If `versions[version]` is absent but `versions` itself exists, legacy keys win."""
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    from pgmimic._config.models import Config

    cfg_dict = dict(base_config)
    cfg_dict["data"] = dict(cfg_dict["data"])
    cfg_dict["data"]["version"] = "2.2"
    cfg_dict["data"]["versions"] = {
        "3.1": {
            "schemas": ["mimiciv_hosp"],
            "tables": {"mimiciv_hosp": ["admissions"]},
        }
    }

    cfg = Config.model_validate(cfg_dict)
    assert cfg.data.schemas == ["mimic_hosp"]
    assert cfg.data.tables == {"mimic_hosp": ["admissions"]}


def test_both_versions_resolve_in_same_config(base_config, monkeypatch):
    """A config with both 2.2 and 3.1 in `versions` resolves correctly by selecting `version`."""
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    from pgmimic._config.models import Config

    versions_map = {
        "2.2": {
            "schemas": ["mimic_hosp"],
            "tables": {"mimic_hosp": ["admissions"]},
        },
        "3.1": {
            "schemas": ["mimiciv_hosp"],
            "tables": {"mimiciv_hosp": ["admissions", "drgcodes"]},
        },
    }

    cfg_dict = dict(base_config)
    cfg_dict["data"] = dict(cfg_dict["data"])
    cfg_dict["data"]["version"] = "3.1"
    cfg_dict["data"]["versions"] = versions_map

    cfg = Config.model_validate(cfg_dict)
    assert cfg.data.schemas == ["mimiciv_hosp"]
    assert cfg.data.tables["mimiciv_hosp"] == ["admissions", "drgcodes"]

    cfg_dict["data"]["version"] = "2.2"
    cfg = Config.model_validate(cfg_dict)
    assert cfg.data.schemas == ["mimic_hosp"]
    assert cfg.data.tables == {"mimic_hosp": ["admissions"]}
