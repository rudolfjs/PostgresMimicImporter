# MIMIC-IV 3.1 SQL assets — provenance

SQL files in this directory are derived from the upstream
[MIT-LCP/mimic-code](https://github.com/MIT-LCP/mimic-code) repository.
This README records the source path, upstream SHA256, and any local
modifications, so a future maintainer can diff against newer upstream
without guessing.

Copied on **2026-05-22** from the locally staged
`mimiciv3.1/` snapshot (see repo root, untracked working-tree
directory).

| File | Upstream source | Upstream SHA256 | Local SHA256 | Modifications |
|:-----|:----------------|:----------------|:-------------|:--------------|
| `create.sql` | `mimic-iv/buildmimic/postgres/create.sql` | `62d3d53259acd90f88e3d1160527faa2741c7652d86214938676d1334346c931` | `5af9c936545b9431bb7d32f6c628d255b70d3077c882324c46115c718aed85cd` | **Appended**: MIMIC-IV-ED schema and 6 ED tables (`diagnosis`, `edstays`, `medrecon`, `pyxis`, `triage`, `vitalsign`) carried verbatim from `pgmimic/_db/SQL/2.2/create.sql` lines 514–end. Upstream `mimic-iv/buildmimic/postgres` carries only `hosp` + `icu` + `derived`; MIMIC-IV-ED has not moved to 3.1 and ships separately at 2.2. |
| `constraint.sql` | `mimic-iv/buildmimic/postgres/constraint.sql` | `bec89f0c7ebfc02106fb0009309626b9d2386b866acd2ff8278f5c55fb3dc1a0` | `bec89f0c7ebfc02106fb0009309626b9d2386b866acd2ff8278f5c55fb3dc1a0` | None (byte-identical copy). |
| `index.sql` | `mimic-iv/buildmimic/postgres/index.sql` | `b77dcf933504e8bc1f42924a14182a60fcf315891da6688f299655d07e609f80` | `b77dcf933504e8bc1f42924a14182a60fcf315891da6688f299655d07e609f80` | None (byte-identical copy). |
| `postgres-functions.sql` | `mimic-iv/concepts_postgres/postgres-functions.sql` | `aa80e0c6362f83accc88c896ee7e3acd4681d58d10097555f8b657781a2cb4f5` | `aa80e0c6362f83accc88c896ee7e3acd4681d58d10097555f8b657781a2cb4f5` | None (byte-identical copy). |

## Upstream schema names — naming shift vs 2.2

Upstream chose to rename the public schemas between `2.2` and `3.1`:

| 2.2 schema | 3.1 schema |
|:-|:-|
| `mimic_hosp`    | `mimiciv_hosp` |
| `mimic_icu`     | `mimiciv_icu` |
| `mimic_derived` | `mimiciv_derived` |
| `mimiciv_ed`    | `mimiciv_ed` (unchanged) |

Downstream consumers (notebooks, BI queries) that hard-coded the 2.2
names need to update their `search_path` or fully-qualified references
when moving to 3.1.

## What's *not* in here (yet)

- The full `mimic-iv/concepts_postgres/` materialised view suite. Only
  `postgres-functions.sql` is included; the ~100 derived concept files
  are out of scope for `v0.0.6` and tracked as follow-up work.
- `load_gz.sql` — `pgmimic` drives the COPY loop from Python via
  `DataHandler._write_mimic_data`, so the upstream loader script is not
  copied.
- `validate.sql` — used by `pixi run -e dev e2e` (see `tests/e2e.py`),
  read directly from the staged `mimiciv3.1/buildmimic/validate.sql`
  rather than carried into the package.

## Refreshing from upstream

If a future MIMIC-IV `3.1.x` patch lands:

1. Re-stage the upstream tree into `mimiciv3.1/` (untracked).
2. `sha256sum mimiciv3.1/buildmimic/{create,constraint,index}.sql mimiciv3.1/concepts_postgres/postgres-functions.sql` — compare against this table.
3. Copy any changed files into `pgmimic/_db/SQL/3.1/`, re-append the
   ED block if `create.sql` changed, and update this README's hashes.
4. Run `pixi run -e dev e2e` against real 3.1 data to verify the
   upstream change is compatible.
