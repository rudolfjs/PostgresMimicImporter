r"""DataHandler must shell out to `psql` via argv lists + PGPASSWORD env.

Bug being fixed: `_create_postgres_functions` and `_write_mimic_data`
built psql commands as f-strings — interpolating the password into
`postgresql://user:password@host:port/db` — and ran them via
`subprocess.Popen(cmd, shell=True)`. A password containing `'`, `;`,
`$`, or `\`` could corrupt the command string and either fail silently
or execute arbitrary shell. The fix passes the password via
`PGPASSWORD` env and the rest via psql's argv flags (`-h`, `-p`, `-U`,
`-d`, `-c`).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from _config.models import Config


def _make_config(password: str = "pw") -> Config:
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
                "version": "2.2",
                "schemas": ["mimic_hosp"],
                "tables": {"mimic_hosp": ["admissions"]},
            },
        }
    )


@pytest.fixture
def fake_db(tmp_path, monkeypatch):
    """DataHandler with psycopg2.connect + subprocess.run mocked."""
    from _db import _db_handler as db_mod

    mock_conn = MagicMock(name="conn")
    monkeypatch.setattr(db_mod.psycopg2, "connect", lambda **_: mock_conn)
    monkeypatch.setattr(db_mod.DataHandler, "SQL_DIR", tmp_path)

    (tmp_path / "2.2").mkdir()
    (tmp_path / "2.2" / "postgres-functions.sql").write_text("-- noop")

    mock_run = MagicMock(name="subprocess.run")
    mock_run.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")
    monkeypatch.setattr(db_mod.subprocess, "run", mock_run)

    cfg = _make_config()
    cfg.database.username = "alice"
    cfg.database.password = "p@ss'word$injection;rm -rf /"
    handler = db_mod.DataHandler(cfg)
    yield handler, mock_run


def test_psql_subprocess_uses_argv_not_shell(fake_db):
    """`subprocess.run` is called with an argv list, no `shell=True`."""
    handler, mock_run = fake_db
    handler._create_postgres_functions()

    call = mock_run.call_args
    args = call.args[0]
    assert isinstance(args, list), f"args must be list (got {type(args)})"
    assert args[0] == "psql"
    # shell=False is the default; explicitly assert it's not True
    assert call.kwargs.get("shell", False) is False


def test_psql_subprocess_passes_password_via_pgpassword_env(fake_db):
    """Password is in PGPASSWORD env, NOT in the argv list."""
    handler, mock_run = fake_db
    handler._create_postgres_functions()

    call = mock_run.call_args
    env = call.kwargs["env"]
    assert env["PGPASSWORD"] == "p@ss'word$injection;rm -rf /"

    # The argv list must not contain the password anywhere
    argv = call.args[0]
    joined = " ".join(argv)
    assert "p@ss'word" not in joined
    assert "rm -rf" not in joined


def test_psql_subprocess_check_true_propagates_failures(fake_db):
    """`check=True` so a non-zero psql exit raises `CalledProcessError`."""
    import subprocess as real_subprocess

    handler, mock_run = fake_db
    # The mock must be `check=True`-aware to validate this
    call_kwargs_capture = {}

    def capture_call(*args, **kwargs):
        call_kwargs_capture.update(kwargs)
        return MagicMock(returncode=0)

    mock_run.side_effect = capture_call
    handler._create_postgres_functions()

    assert call_kwargs_capture.get("check") is True
    # Sanity: real_subprocess has CalledProcessError defined
    assert hasattr(real_subprocess, "CalledProcessError")


def test_psql_subprocess_includes_connection_flags(fake_db):
    """argv should pass host, port, user, db via -h / -p / -U / -d."""
    handler, mock_run = fake_db
    handler._create_postgres_functions()

    argv = mock_run.call_args.args[0]
    assert "-h" in argv
    assert argv[argv.index("-h") + 1] == "pg"
    assert "-p" in argv
    assert argv[argv.index("-p") + 1] == "5432"
    assert "-U" in argv
    assert argv[argv.index("-U") + 1] == "alice"
    assert "-d" in argv
    assert argv[argv.index("-d") + 1] == "postgres"
