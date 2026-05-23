"""Regenerate `tests/fixtures/mimiciv/3.1/{hosp,icu,ed}/*.csv.gz`.

Run when schemas drift or new tables are covered:

    pixi run -e dev python -m tests.fixtures.generate

Synthetic data is deliberately minimal (2 rows/table) — fixtures exist
to exercise the importer's plumbing and to detect schema drift, not to
approximate clinical reality. For full-fidelity validation use the
opt-in `pixi run -e dev e2e` task against real MIMIC-IV data.
"""

from __future__ import annotations

import gzip
import io
import pathlib

import pandas as pd

FIXTURES_ROOT = pathlib.Path(__file__).parent / "mimiciv" / "3.1"


# Each value is a list-of-dicts: 2 rows per table, column-keyed.
HOSP: dict[str, list[dict]] = {
    "admissions": [
        {
            "subject_id": 10000001,
            "hadm_id": 20000001,
            "admittime": "2180-01-01 12:00:00",
            "dischtime": "2180-01-05 09:00:00",
            "deathtime": "",
            "admission_type": "URGENT",
            "admit_provider_id": "P0001",
            "admission_location": "EMERGENCY ROOM",
            "discharge_location": "HOME",
            "insurance": "Medicare",
            "language": "ENGLISH",
            "marital_status": "MARRIED",
            "race": "WHITE",
            "edregtime": "2180-01-01 10:00:00",
            "edouttime": "2180-01-01 11:30:00",
            "hospital_expire_flag": 0,
        },
        {
            "subject_id": 10000002,
            "hadm_id": 20000002,
            "admittime": "2181-06-15 08:00:00",
            "dischtime": "2181-06-20 14:00:00",
            "deathtime": "",
            "admission_type": "ELECTIVE",
            "admit_provider_id": "P0002",
            "admission_location": "PHYSICIAN REFERRAL",
            "discharge_location": "SKILLED NURSING FACILITY",
            "insurance": "Private",
            "language": "ENGLISH",
            "marital_status": "SINGLE",
            "race": "BLACK/AFRICAN AMERICAN",
            "edregtime": "",
            "edouttime": "",
            "hospital_expire_flag": 0,
        },
    ],
    "patients": [
        {
            "subject_id": 10000001,
            "gender": "F",
            "anchor_age": 65,
            "anchor_year": 2180,
            "anchor_year_group": "2017 - 2019",
            "dod": "",
        },
        {
            "subject_id": 10000002,
            "gender": "M",
            "anchor_age": 52,
            "anchor_year": 2181,
            "anchor_year_group": "2017 - 2019",
            "dod": "",
        },
    ],
    "drgcodes": [
        {
            "subject_id": 10000001,
            "hadm_id": 20000001,
            "drg_type": "HCFA",
            "drg_code": "470",
            "description": "MAJOR JOINT REPLACEMENT",
            "drg_severity": "",
            "drg_mortality": "",
        },
        {
            "subject_id": 10000002,
            "hadm_id": 20000002,
            "drg_type": "APR",
            "drg_code": "302",
            "description": "PNEUMONIA",
            "drg_severity": 2,
            "drg_mortality": 1,
        },
    ],
    "provider": [
        {"provider_id": "P0001"},
        {"provider_id": "P0002"},
    ],
    "services": [
        {
            "subject_id": 10000001,
            "hadm_id": 20000001,
            "transfertime": "2180-01-01 12:30:00",
            "prev_service": "",
            "curr_service": "ORTHO",
        },
        {
            "subject_id": 10000002,
            "hadm_id": 20000002,
            "transfertime": "2181-06-15 08:30:00",
            "prev_service": "MED",
            "curr_service": "SURG",
        },
    ],
}

ICU: dict[str, list[dict]] = {
    "icustays": [
        {
            "subject_id": 10000001,
            "hadm_id": 20000001,
            "stay_id": 30000001,
            "first_careunit": "MICU",
            "last_careunit": "MICU",
            "intime": "2180-01-02 06:00:00",
            "outtime": "2180-01-04 12:00:00",
            "los": 2.25,
        },
        {
            "subject_id": 10000002,
            "hadm_id": 20000002,
            "stay_id": 30000002,
            "first_careunit": "SICU",
            "last_careunit": "SICU",
            "intime": "2181-06-16 03:00:00",
            "outtime": "2181-06-19 18:00:00",
            "los": 3.625,
        },
    ],
    "caregiver": [
        {"caregiver_id": 100001},
        {"caregiver_id": 100002},
    ],
}

ED: dict[str, list[dict]] = {
    "edstays": [
        {
            "subject_id": 10000001,
            "hadm_id": 20000001,
            "stay_id": 40000001,
            "intime": "2180-01-01 10:00:00",
            "outtime": "2180-01-01 11:30:00",
            "gender": "F",
            "race": "WHITE",
            "arrival_transport": "AMBULANCE",
            "disposition": "ADMITTED",
        },
        {
            "subject_id": 10000003,
            "hadm_id": "",
            "stay_id": 40000002,
            "intime": "2182-03-10 14:00:00",
            "outtime": "2182-03-10 18:00:00",
            "gender": "M",
            "race": "ASIAN",
            "arrival_transport": "WALK IN",
            "disposition": "DISCHARGED",
        },
    ],
}


def _write_gz(rows: list[dict], path: pathlib.Path) -> None:
    """Write a list-of-dicts as gzipped CSV with empty-string for missing values."""
    df = pd.DataFrame(rows)
    buf = io.StringIO()
    df.to_csv(buf, index=False, na_rep="")
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wb") as fh:
        fh.write(buf.getvalue().encode("utf-8"))


def generate() -> dict[str, int]:
    """Regenerate every fixture; return {table: row_count} for reporting."""
    counts: dict[str, int] = {}
    for table, rows in HOSP.items():
        _write_gz(rows, FIXTURES_ROOT / "hosp" / f"{table}.csv.gz")
        counts[table] = len(rows)
    for table, rows in ICU.items():
        _write_gz(rows, FIXTURES_ROOT / "icu" / f"{table}.csv.gz")
        counts[table] = len(rows)
    for table, rows in ED.items():
        _write_gz(rows, FIXTURES_ROOT / "ed" / f"{table}.csv.gz")
        counts[table] = len(rows)
    return counts


if __name__ == "__main__":
    counts = generate()
    for table, n in counts.items():
        print(f"{table}: {n} rows")
