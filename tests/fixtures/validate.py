"""Pandera-validate every CSV fixture in `tests/fixtures/mimiciv/3.1/**/*.csv.gz`.

Run via:

    pixi run -e dev validate-fixtures

Exits non-zero with a count and per-table summary if any CSV fails its
schema check. Used as a CI matrix entry and a lefthook pre-push command.
"""

from __future__ import annotations

import pathlib
import sys

import pandas as pd

from tests.fixtures.schemas import ALL_SCHEMAS

FIXTURES_ROOT = pathlib.Path(__file__).parent / "mimiciv" / "3.1"


def validate_all() -> int:
    """Return the number of failing fixtures (0 = clean)."""
    failures: list[tuple[pathlib.Path, str]] = []
    fixtures = sorted(FIXTURES_ROOT.glob("**/*.csv.gz"))
    if not fixtures:
        print(f"No fixtures found under {FIXTURES_ROOT}", file=sys.stderr)
        return 1

    for fixture in fixtures:
        table = fixture.name.removesuffix(".csv.gz")
        schema = ALL_SCHEMAS.get(table)
        if schema is None:
            failures.append((fixture, f"no schema registered for table {table!r}"))
            continue

        try:
            df = pd.read_csv(fixture, compression="gzip", keep_default_na=False, na_values=[""])
            schema.validate(df, lazy=True)
        except Exception as exc:
            failures.append((fixture, str(exc).splitlines()[0]))
        else:
            print(f"  ok  {table:<20} ({len(df)} rows)")

    if failures:
        print(file=sys.stderr)
        print(f"{len(failures)} fixture(s) failed:", file=sys.stderr)
        for path, msg in failures:
            print(f"  FAIL  {path.relative_to(FIXTURES_ROOT)}: {msg}", file=sys.stderr)
        return len(failures)

    print(f"\n{len(fixtures)} fixtures validated against Pandera schemas.")
    return 0


if __name__ == "__main__":
    sys.exit(validate_all())
