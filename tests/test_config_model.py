"""Pydantic-based config validation and ConfigHandler contract."""

from __future__ import annotations

import json

import pytest


@pytest.fixture
def minimal_config_dict() -> dict:
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


def test_config_raises_on_missing_required_field(minimal_config_dict, monkeypatch):
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    from _config.models import Config
    from pydantic import ValidationError

    broken = dict(minimal_config_dict)
    broken["data"] = dict(broken["data"])
    del broken["data"]["version"]

    with pytest.raises(ValidationError):
        Config.model_validate(broken)


def test_config_exposes_dotted_access(minimal_config_dict, monkeypatch):
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    from _config.models import Config

    cfg = Config.model_validate(minimal_config_dict)
    assert cfg.database.host == "pg"
    assert cfg.database.port == 5432
    assert cfg.database.schema_ == "public"
    assert cfg.data.version == "2.2"
    assert cfg.data.schemas == ["mimic_hosp"]
    assert cfg.database.username is None
    assert cfg.database.password is None


def test_config_populates_credentials_from_env(minimal_config_dict, monkeypatch):
    monkeypatch.setenv("DB_USER", "alice")
    monkeypatch.setenv("DB_PASSWORD", "s3cret")
    from _config.models import Config

    cfg = Config.model_validate(minimal_config_dict)
    assert cfg.database.username == "alice"
    assert cfg.database.password == "s3cret"


def test_config_handler_returns_model(tmp_path, minimal_config_dict, monkeypatch):
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    from _config._config_handler import ConfigHandler
    from _config.models import Config

    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps(minimal_config_dict))

    handler = ConfigHandler(str(cfg_file))
    cfg = handler.get_config()
    assert isinstance(cfg, Config)
    assert cfg.data.version == "2.2"


def test_config_handler_raises_on_bad_json(tmp_path):
    """Bad config no longer silently swallowed (loud failure)."""
    from _config._config_handler import ConfigHandler
    from pydantic import ValidationError

    cfg_file = tmp_path / "config.json"
    cfg_file.write_text('{"database": "not a dict"}')

    with pytest.raises(ValidationError):
        ConfigHandler(str(cfg_file))


def test_real_config_json_loads(monkeypatch):
    """Shipped config.json validates against the Config model."""
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    import pathlib

    from _config._config_handler import ConfigHandler

    repo_root = pathlib.Path(__file__).parent.parent
    cfg = ConfigHandler(str(repo_root / "config.json")).get_config()
    assert cfg.data.version == "2.2"
    assert "mimic_hosp" in cfg.data.schemas
