"""Regression: table-name → CSV-file lookup must use basename equality, not substring.

Bug being fixed: the original `next(s for s in files if table in s)` matches the
*first* file whose path contains the table name as a substring. For tables whose
names are prefixes of other table names (notably `poe` ⊂ `poe_detail`), the wrong
file would be loaded silently.
"""

from __future__ import annotations

import pytest


def test_resolves_exact_basename():
    from _db._db_handler import _file_for_table

    files = ["/data/mimiciv/3.1/hosp/admissions.csv.gz"]
    assert _file_for_table(files, "admissions").endswith("admissions.csv.gz")


def test_poe_does_not_match_poe_detail():
    """The original substring match would return `poe_detail.csv.gz` for table `poe`."""
    from _db._db_handler import _file_for_table

    files = [
        "/data/mimiciv/3.1/hosp/poe_detail.csv.gz",
        "/data/mimiciv/3.1/hosp/poe.csv.gz",
    ]
    assert _file_for_table(files, "poe").endswith("/poe.csv.gz")
    assert _file_for_table(files, "poe_detail").endswith("/poe_detail.csv.gz")


def test_emar_does_not_match_emar_detail():
    """Same shape, different prefix — emar / emar_detail."""
    from _db._db_handler import _file_for_table

    files = [
        "/data/mimiciv/3.1/hosp/emar_detail.csv.gz",
        "/data/mimiciv/3.1/hosp/emar.csv.gz",
    ]
    assert _file_for_table(files, "emar").endswith("/emar.csv.gz")
    assert _file_for_table(files, "emar_detail").endswith("/emar_detail.csv.gz")


def test_raises_on_missing():
    from _db._db_handler import _file_for_table

    with pytest.raises(FileNotFoundError):
        _file_for_table(["/data/admissions.csv.gz"], "patients")


def test_raises_on_duplicates():
    """Two files with the same basename in different subdirs should error, not pick blind."""
    from _db._db_handler import _file_for_table

    files = [
        "/data/mimiciv/3.1/hosp/admissions.csv.gz",
        "/data/mimiciv/3.1/ed/admissions.csv.gz",
    ]
    with pytest.raises(RuntimeError):
        _file_for_table(files, "admissions")
