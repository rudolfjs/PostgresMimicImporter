"""Pandera schemas for MIMIC-IV 3.1 fixture validation.

Each module declares a `SCHEMAS: dict[str, DataFrameSchema]` mapping the
table name (without schema prefix) to its Pandera schema. The
`validate_fixtures` runner imports `ALL_SCHEMAS` and resolves CSVs by
filename → table name.

Coverage today is representative (not exhaustive): the new-in-3.1
tables (`drgcodes`, `provider`, `services`, `caregiver`) and a sample
of stable tables (`admissions`, `patients`, `icustays`, `edstays`).
The pattern is in place; expanding to the full ~37 tables is a
follow-up chore.
"""

from __future__ import annotations

from .mimiciv_ed import SCHEMAS as ED_SCHEMAS
from .mimiciv_hosp import SCHEMAS as HOSP_SCHEMAS
from .mimiciv_icu import SCHEMAS as ICU_SCHEMAS

ALL_SCHEMAS = {**HOSP_SCHEMAS, **ICU_SCHEMAS, **ED_SCHEMAS}
