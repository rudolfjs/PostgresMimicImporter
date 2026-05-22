"""Pandera schemas for `mimiciv_ed.*` (carried verbatim from MIMIC-IV-ED 2.2)."""

from __future__ import annotations

import pandera.pandas as pa

edstays = pa.DataFrameSchema(
    {
        "subject_id": pa.Column(int, nullable=False),
        "hadm_id": pa.Column("Int64", nullable=True),
        "stay_id": pa.Column(int, nullable=False),
        "intime": pa.Column(pa.DateTime, nullable=False, coerce=True),
        "outtime": pa.Column(pa.DateTime, nullable=False, coerce=True),
        "gender": pa.Column(str, nullable=False),
        "race": pa.Column(str, nullable=True),
        "arrival_transport": pa.Column(str, nullable=False),
        "disposition": pa.Column(str, nullable=True),
    },
    strict=True,
    coerce=True,
)


SCHEMAS = {
    "edstays": edstays,
}
