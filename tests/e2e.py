"""Opt-in end-to-end test against a real MIMIC-IV 3.1 dataset.

Run on the maintainer's server (not in CI) before merging changes to
the importer or SQL assets:

    MIMIC_DATA_PATH=/srv/mimic pixi run -e dev e2e

What it does:

  1. Asserts `MIMIC_DATA_PATH` is set (friendly exit 2 otherwise).
  2. Picks `podman-compose` if available, else `docker compose`.
  3. Brings up the `pg` service from `docker-compose.yaml` and polls
     until `pg_isready`.
  4. Runs the importer via `<runtime> run --rm --build mimic_import`
     so the container has the `MIMIC_DATA_PATH` bind-mount and can
     reach the `pg` hostname on the compose network (the host shell
     cannot). `--build` rebuilds the image when the Dockerfile or
     pixi manifest changes; `.dockerignore` keeps `data/` out of the
     build context.
  5. Connects to localhost on the host port published by compose
     (`PGMIMIC_HOST_PORT`, default 5432; override for a host where
     5432 is already taken) via psycopg2, using the same
     `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB` values compose
     substitutes into the `pg` container (read from `.env` if the
     shell hasn't exported them, matching compose's own behaviour),
     and runs `mimiciv3.1/buildmimic/validate.sql`. Reports per
     table; exits non-zero on any FAILED row.

The container is left running by default (so you can poke around).
Pass `--teardown` to bring it back down.

This script is NOT part of the pytest collection (filename does not
match `test_*`). It is invoked through the pixi `e2e` task only.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
VALIDATE_SQL = REPO_ROOT / "mimiciv3.1" / "buildmimic" / "validate.sql"
ENV_FILE = REPO_ROOT / ".env"


def _dotenv_defaults() -> dict[str, str]:
    """Parse the tracked .env the same way docker-compose does.

    Compose reads `.env` to substitute `${POSTGRES_USER}` etc. into
    the `pg` container's environment. Our host-side psycopg2 connect
    needs the same values — but `os.environ` only sees them if the
    shell exported them. Read `.env` ourselves so a bare
    `MIMIC_DATA_PATH=... pixi run -e dev e2e` still works.
    """
    out: dict[str, str] = {}
    if not ENV_FILE.is_file():
        return out
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def _pick_runtime() -> list[str]:
    """Return the `compose` argv prefix for the available container runtime."""
    if shutil.which("podman-compose"):
        return ["podman-compose"]
    if shutil.which("docker"):
        return ["docker", "compose"]
    print("ERROR: neither podman-compose nor docker compose found on PATH", file=sys.stderr)
    sys.exit(2)


def _require_env() -> str:
    path = os.getenv("MIMIC_DATA_PATH")
    if not path:
        print(
            "ERROR: MIMIC_DATA_PATH must be set to the directory containing\n"
            "       data/mimiciv/3.1/{hosp,icu,ed}/<table>.csv.gz before running e2e.\n"
            "Example: MIMIC_DATA_PATH=/srv/mimic pixi run -e dev e2e",
            file=sys.stderr,
        )
        sys.exit(2)
    if not Path(path).is_dir():
        print(f"ERROR: MIMIC_DATA_PATH={path!r} is not a directory", file=sys.stderr)
        sys.exit(2)
    return path


def _wait_for_postgres(runtime: list[str], timeout_s: int = 60) -> None:
    """Poll the pg container's healthcheck until it reports healthy."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        result = subprocess.run(
            [*runtime, "exec", "-T", "pg", "pg_isready"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return
        time.sleep(2)
    print(f"ERROR: postgres did not become ready within {timeout_s}s", file=sys.stderr)
    sys.exit(1)


def _run_validate_sql() -> int:
    """Run the upstream row-count validator via psycopg2; return number of mismatches."""
    try:
        import psycopg2
    except ImportError:
        print("ERROR: psycopg2 not importable — run inside the default pixi env", file=sys.stderr)
        return 1

    if not VALIDATE_SQL.is_file():
        print(
            f"ERROR: upstream validate.sql not found at {VALIDATE_SQL}.\n"
            "       Make sure the mimiciv3.1/ snapshot is staged locally.",
            file=sys.stderr,
        )
        return 1

    env = _dotenv_defaults()
    conn = psycopg2.connect(
        host="localhost",
        port=int(os.getenv("PGMIMIC_HOST_PORT", env.get("PGMIMIC_HOST_PORT", "5432"))),
        dbname=os.getenv("POSTGRES_DB", env.get("POSTGRES_DB", "postgres")),
        user=os.getenv("POSTGRES_USER", env.get("POSTGRES_USER", "postgres")),
        password=os.getenv("POSTGRES_PASSWORD", env.get("POSTGRES_PASSWORD", "")),
    )
    try:
        with conn.cursor() as cur:
            cur.execute(VALIDATE_SQL.read_text())
            rows = cur.fetchall()
    finally:
        conn.close()

    mismatches = 0
    for tbl, expected, actual, check in rows:
        ok = check == "PASSED"
        status = "ok " if ok else "FAIL"
        print(f"  {status}  {tbl:<25} expected={expected:>12} actual={actual:>12}")
        if not ok:
            mismatches += 1
    return mismatches


def main() -> int:
    summary = (__doc__ or "").strip().splitlines()[0]
    parser = argparse.ArgumentParser(description=summary)
    parser.add_argument(
        "--teardown",
        action="store_true",
        help="Bring the postgres container down after the run (default: leave running).",
    )
    parser.add_argument(
        "--skip-import",
        action="store_true",
        help="Skip the importer step (use when re-running validate against an already-loaded DB).",
    )
    args = parser.parse_args()

    _require_env()
    runtime = _pick_runtime()
    print(f"using compose runtime: {' '.join(runtime)}")

    print("bringing up pg service...")
    subprocess.run([*runtime, "up", "-d", "pg"], check=True, cwd=REPO_ROOT)
    _wait_for_postgres(runtime)
    print("pg is ready.")

    if not args.skip_import:
        print("running mimic-import inside the compose network...")
        subprocess.run(
            [*runtime, "run", "--rm", "--build", "mimic_import"],
            check=True,
            cwd=REPO_ROOT,
        )

    print("\nvalidating row counts against upstream expected values...\n")
    mismatches = _run_validate_sql()

    if args.teardown:
        print("\ntearing down compose stack...")
        subprocess.run([*runtime, "down"], cwd=REPO_ROOT)

    if mismatches:
        print(f"\n{mismatches} row-count mismatch(es) — see FAIL rows above.", file=sys.stderr)
        return 1

    print("\nall row counts match upstream expected values. e2e passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
