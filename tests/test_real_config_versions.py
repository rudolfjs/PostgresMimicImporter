"""Real config.json: 2.2 default still resolves; 3.1 opt-in resolves to mimiciv_* schemas."""

from __future__ import annotations

import json
import pathlib


def test_default_2_2_resolves_legacy(monkeypatch):
    """Shipped config.json with version=2.2 keeps the legacy mimic_* schemas."""
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    from pgmimic._config._config_handler import ConfigHandler

    repo_root = pathlib.Path(__file__).parent.parent
    cfg = ConfigHandler(str(repo_root / "config.json")).get_config()

    assert cfg.data.version == "2.2"
    assert cfg.data.schemas == ["mimic_hosp", "mimic_icu", "mimiciv_ed", "mimic_derived"]
    assert "admissions" in cfg.data.tables["mimic_hosp"]
    # 3.1-only tables must NOT leak into 2.2 default
    assert "drgcodes" not in cfg.data.tables["mimic_hosp"]


def test_3_1_opt_in_resolves_versions_map(tmp_path, monkeypatch):
    """Flipping version to 3.1 picks up versions[3.1] schemas."""
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    from pgmimic._config._config_handler import ConfigHandler

    repo_root = pathlib.Path(__file__).parent.parent
    raw = json.loads((repo_root / "config.json").read_text())
    raw["data"]["version"] = "3.1"

    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps(raw))

    cfg = ConfigHandler(str(cfg_file)).get_config()
    assert cfg.data.version == "3.1"
    assert cfg.data.schemas == ["mimiciv_hosp", "mimiciv_icu", "mimiciv_ed", "mimiciv_derived"]
    assert "drgcodes" in cfg.data.tables["mimiciv_hosp"]
    assert "provider" in cfg.data.tables["mimiciv_hosp"]
    assert "services" in cfg.data.tables["mimiciv_hosp"]
    assert "caregiver" in cfg.data.tables["mimiciv_icu"]
