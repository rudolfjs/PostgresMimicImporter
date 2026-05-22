"""Pandera schemas for `mimiciv_hosp.*` tables shipped with MIMIC-IV 3.1.

Mirror the column shape declared in `pgmimic/_db/SQL/3.1/create.sql`. If
upstream drifts, the fixture validation step (`pixi run -e dev
validate-fixtures`) raises before CI/lefthook turns green.
"""

from __future__ import annotations

import pandera.pandas as pa

admissions = pa.DataFrameSchema(
    {
        "subject_id": pa.Column(int, nullable=False),
        "hadm_id": pa.Column(int, nullable=False),
        "admittime": pa.Column(pa.DateTime, nullable=False, coerce=True),
        "dischtime": pa.Column(pa.DateTime, nullable=True, coerce=True),
        "deathtime": pa.Column(pa.DateTime, nullable=True, coerce=True),
        "admission_type": pa.Column(str, nullable=False),
        "admit_provider_id": pa.Column(str, nullable=True),
        "admission_location": pa.Column(str, nullable=True),
        "discharge_location": pa.Column(str, nullable=True),
        "insurance": pa.Column(str, nullable=True),
        "language": pa.Column(str, nullable=True),
        "marital_status": pa.Column(str, nullable=True),
        "race": pa.Column(str, nullable=True),
        "edregtime": pa.Column(pa.DateTime, nullable=True, coerce=True),
        "edouttime": pa.Column(pa.DateTime, nullable=True, coerce=True),
        "hospital_expire_flag": pa.Column("Int64", nullable=True),
    },
    strict=True,
    coerce=True,
)

patients = pa.DataFrameSchema(
    {
        "subject_id": pa.Column(int, nullable=False),
        "gender": pa.Column(str, nullable=False),
        "anchor_age": pa.Column("Int64", nullable=True),
        "anchor_year": pa.Column(int, nullable=False),
        "anchor_year_group": pa.Column(str, nullable=False),
        "dod": pa.Column(pa.DateTime, nullable=True, coerce=True),
    },
    strict=True,
    coerce=True,
)

# 3.1 introduces drgcodes — present in upstream buildmimic/postgres/create.sql
drgcodes = pa.DataFrameSchema(
    {
        "subject_id": pa.Column(int, nullable=False),
        "hadm_id": pa.Column(int, nullable=False),
        "drg_type": pa.Column(str, nullable=True),
        "drg_code": pa.Column(str, nullable=False),
        "description": pa.Column(str, nullable=True),
        "drg_severity": pa.Column("Int64", nullable=True),
        "drg_mortality": pa.Column("Int64", nullable=True),
    },
    strict=True,
    coerce=True,
)

# 3.1 introduces provider — a one-column reference table
provider = pa.DataFrameSchema(
    {
        "provider_id": pa.Column(str, nullable=False),
    },
    strict=True,
    coerce=True,
)

# 3.1 introduces services
services = pa.DataFrameSchema(
    {
        "subject_id": pa.Column(int, nullable=False),
        "hadm_id": pa.Column(int, nullable=False),
        "transfertime": pa.Column(pa.DateTime, nullable=False, coerce=True),
        "prev_service": pa.Column(str, nullable=True),
        "curr_service": pa.Column(str, nullable=True),
    },
    strict=True,
    coerce=True,
)


SCHEMAS = {
    "admissions": admissions,
    "patients": patients,
    "drgcodes": drgcodes,
    "provider": provider,
    "services": services,
}
