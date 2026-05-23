"""Pandera schemas for `mimiciv_icu.*` tables shipped with MIMIC-IV 3.1."""

from __future__ import annotations

import pandera.pandas as pa

icustays = pa.DataFrameSchema(
    {
        "subject_id": pa.Column(int, nullable=False),
        "hadm_id": pa.Column(int, nullable=False),
        "stay_id": pa.Column(int, nullable=False),
        "first_careunit": pa.Column(str, nullable=True),
        "last_careunit": pa.Column(str, nullable=True),
        "intime": pa.Column(pa.DateTime, nullable=True, coerce=True),
        "outtime": pa.Column(pa.DateTime, nullable=True, coerce=True),
        "los": pa.Column(float, nullable=True),
    },
    strict=True,
    coerce=True,
)

# 3.1 introduces caregiver — a one-column reference table
caregiver = pa.DataFrameSchema(
    {
        "caregiver_id": pa.Column(int, nullable=False),
    },
    strict=True,
    coerce=True,
)


SCHEMAS = {
    "icustays": icustays,
    "caregiver": caregiver,
}
