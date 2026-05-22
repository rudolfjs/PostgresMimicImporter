"""Smoke tests: every shipped fixture has a registered schema and validates."""

from __future__ import annotations

import pathlib


def test_validate_returns_zero():
    """`tests.fixtures.validate.validate_all()` returns 0 when fixtures are healthy."""
    from tests.fixtures.validate import validate_all

    assert validate_all() == 0


def test_every_fixture_has_a_schema():
    """No orphan CSV: every `.csv.gz` under fixtures/mimiciv/3.1 must have a Pandera schema."""
    from tests.fixtures.schemas import ALL_SCHEMAS

    fixtures_root = pathlib.Path(__file__).parent / "fixtures" / "mimiciv" / "3.1"
    fixtures = sorted(fixtures_root.glob("**/*.csv.gz"))
    assert fixtures, "no fixtures found — generator must have failed"

    orphans = [f for f in fixtures if f.name.removesuffix(".csv.gz") not in ALL_SCHEMAS]
    assert not orphans, f"fixtures without schemas: {orphans}"


def test_schemas_cover_new_3_1_tables():
    """The 3.1 additions (drgcodes, provider, services, caregiver) must have schemas."""
    from tests.fixtures.schemas import ALL_SCHEMAS

    for table in ("drgcodes", "provider", "services", "caregiver"):
        assert table in ALL_SCHEMAS, f"3.1 table {table!r} missing from ALL_SCHEMAS"
