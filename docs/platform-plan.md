# Platform Expansion Plan

> **Status:** Draft (WIP)
> **Branch:** `feat/expand-platform`
> **Scope of this document:** the decisions and module changes needed to add **DuckDB, MySQL, and SQLite** as additional engines alongside Postgres, and to rename the project to reflect a multi-engine vision. Future engines (Spark, BigQuery) and platforms (k3s) are deliberately out of scope here.

## Goal

Expand `PostgresMimicImporter` from a Postgres-only loader into a multi-engine MIMIC data builder. First additions: **DuckDB, MySQL, SQLite** — leveraging the engine-specific build artifacts that [MIT-LCP/mimic-code](https://github.com/MIT-LCP/mimic-code/tree/main/mimic-iv/buildmimic) already maintains. Rename the project to **`MimicDataStack`** to signal that engines and platforms are now composable layers.

User-facing model after this work:

| Engine | Runtime | Result | Output |
| --- | --- | --- | --- |
| `postgresql` | docker / podman | Postgres container on `:5432` | Running service (today's behaviour) |
| `mysql` | docker / podman | MySQL container on `:3306` | Running service |
| `duckdb` | docker / podman | Builder container | `mimic.duckdb` file on mounted volume |
| `sqlite` | docker / podman | Builder container | `mimic4.db` file on mounted volume |

The matrix collapses cleanly into two families:

- **Server-mode engines** (Postgres, MySQL) — listen on a TCP port; importer connects, creates schemas/tables, bulk-loads. End state is a long-running service.
- **File-mode engines** (DuckDB, SQLite) — in-process libraries; the build container produces a single database file and exits. Clients (DataGrip, DBeaver, native CLI) connect to the file directly. There is no port.

## Constraints discovered during planning

### Server-mode engines

- Postgres and MySQL behave alike at the "runtime container with a port" level. The Postgres path is what exists today; MySQL is symmetrical.
- MySQL has **no schemas in the Postgres sense** — only databases. This breaks the assumption baked into `config.json` and the existing DDL that `schema.table` is universal. See Decision 3.

### File-mode engines

- **DuckDB is in-process.** No TCP port, no client/server wire protocol. The official `duckdb/duckdb` Docker image is just a CLI in a container.
- **SQLite is also in-process**, with the same constraint.
- Server-mode-style options for DuckDB exist (`pg_duckdb`, MotherDuck, `duckdb-httpserver`, Arrow Flight SQL) but each is a meaningful architectural commitment. **Explicitly out of scope** for this iteration.
- Docker / Podman are still valuable here: they bundle the build environment so users don't install DuckDB / SQLite / Python / pandas locally.

### DDL divergence across engines

This is the most consequential finding. The four engines diverge in DDL compatibility far enough that **one canonical DDL with transforms does not work for all four**:

| Engine | DDL approach in MIT-LCP | Why it can / cannot share PG's DDL |
| --- | --- | --- |
| Postgres | Hand-written `create.sql` | Canonical |
| DuckDB | Same `create.sql` with three regex transforms applied at script runtime | Minor divergence (`TIMESTAMP(N)`, a few `NOT NULL`s) |
| MySQL | Hand-written `load.sql` (46 KB) | `DATETIME` vs `TIMESTAMP`, `BOOLEAN` vs `SMALLINT`, no schemas, `CHARACTER SET = UTF8MB4`, `LOAD DATA LOCAL INFILE` with per-column `trim()` / NULL conditionals — not regex-transformable from PG |
| SQLite | `import.py` — schema built **dynamically** from CSV columns via `pandas` | SQLite's dynamic typing makes pre-baked DDL unnecessary |

## Out of scope (this iteration)

- k3s / Kubernetes manifests for any engine.
- Spark engine.
- BigQuery engine (MIT-LCP supports it; cloud-only, deferred).
- DuckDB-as-server in any form (HTTP extension, MotherDuck, `pg_duckdb`, Flight SQL).
- Repository rename on GitHub — handled as a separate operation once the in-tree rename lands.
- Schema changes to MIMIC data itself.

## Current state

Already on `main`:

- Postgres importer (`pgmimic/` package, `psycopg2` + shelled-out `psql` for bulk load).
- Docker support (`docker-compose.yaml`, `mimic_import.dockerfile`).
- **Podman / podman-compose support** (added in `c2d2864`, refined in `6d06394`).
- Pixi-managed Python environment (added in `6d2b8fc`).

The runtime side (docker, podman) is covered. This plan focuses on the **engine** axis.

### Where Postgres-specific code lives today

`pgmimic/_db/_db_handler.py:1-169` is a single `DataHandler` class mashing four concerns:

| Concern | Implementation | Postgres-coupled? |
| --- | --- | --- |
| Connection | `psycopg2.connect()` (line 13) | Yes |
| Existence check | `information_schema.tables` query (lines 36-41) | Mostly (DuckDB and MySQL also have it; SQLite uses `sqlite_master`) |
| DDL application | Reads `_db/SQL/{version}/*.sql`, naive `split(";")` (lines 102-121) | Yes — DDL is Postgres syntax |
| Bulk load | Shells out to `psql` with `\copy ... FROM PROGRAM 'gzip -dc ...'` (lines 143-167) | Heavily |

`pgmimic/_files/_file_handler.py` and `pgmimic/_config/_config_handler.py` are mostly engine-neutral already and need only minor adjustments.

## Target architecture

### Module layout

Rename `pgmimic/` → `mimicstack/`. Within it, split the engine concern out of `DataHandler`:

```
mimicstack/
├── _config/_config_handler.py        # adds engine-aware validation
├── _files/_file_handler.py           # unchanged
├── importer/mimic_importer.py        # depends on Engine, not DataHandler
└── _db/
    ├── engine.py                     # NEW: Engine Protocol + make_engine factory
    ├── postgres_engine.py            # NEW: existing PG logic, mechanically moved
    ├── duckdb_engine.py              # NEW: in-process duckdb Python package
    ├── mysql_engine.py               # NEW: PyMySQL or mysql-connector-python
    ├── sqlite_engine.py              # NEW: stdlib sqlite3 + pandas
    └── SQL/
        └── 2.2/
            ├── postgres/             # MOVED: existing *.sql, unchanged
            ├── mysql/                # NEW: vendored copy of MIT-LCP load.sql
            └── (no duckdb/, no sqlite/)   # DDL generated at runtime — see Decision 1
```

### Engine contract

```python
# mimicstack/_db/engine.py  (sketch — not yet implemented)
from pathlib import Path
from typing import Protocol


class Engine(Protocol):
    def connect(self) -> None: ...
    def close(self) -> None: ...
    def data_exists(self, schemas: dict[str, list[str]]) -> bool: ...
    def apply_ddl(self, schemas: dict[str, list[str]]) -> None: ...   # may be no-op for SQLite
    def load_table(self, schema: str, table: str, csv_gz_path: Path) -> None: ...
    def apply_post_load(self) -> None: ...   # PG functions on PG; no-op elsewhere


def make_engine(config: dict) -> Engine:
    db = config["database"]
    match db["type"]:
        case "postgresql":
            return PostgresEngine(host=db["host"], port=db["port"], database=db["database"],
                                  schema=db["schema"], user=db["username"], password=db["password"])
        case "mysql":
            return MySQLEngine(host=db["host"], port=db["port"], database=db["database"],
                               user=db["user"], password=db["password"])
        case "duckdb":
            return DuckDBEngine(path=Path(db["path"]))
        case "sqlite":
            return SQLiteEngine(path=Path(db["path"]))
        case t:
            raise ValueError(f"unknown engine type: {t!r}")
```

`MimicImporter` collapses to a ~30-line orchestrator that depends only on `Engine`; no `psycopg2` import survives outside `postgres_engine.py`.

**Note on `apply_ddl()` signature:** changed from `apply_ddl(sql_path: Path)` to `apply_ddl(schemas: dict[str, list[str]])`. This is to accommodate engines that build schema dynamically (SQLite) or have no schema concept at all (MySQL's flat namespace, depending on Decision 3). Each engine decides how to materialise the structured schema info — by reading a SQL file, by transforming one, by introspecting CSVs, or by issuing `CREATE DATABASE` per schema.

## Decisions

### Decision 1 — DDL strategy: per-engine, three different approaches

**Chosen.** A single canonical DDL across all four engines was the original plan, but inspection of MIT-LCP's per-engine artifacts shows the divergence is too large. Each engine uses the artifact that best matches its model:

| Engine | DDL source | Lives in |
| --- | --- | --- |
| Postgres | Existing hand-written `create.sql` (canonical for *this project*) | `_db/SQL/2.2/postgres/` |
| DuckDB | Postgres DDL + 3 regex transforms at runtime | Generated; no file |
| MySQL | Vendored copy of MIT-LCP's `mimic-iv/buildmimic/mysql/load.sql` | `_db/SQL/2.2/mysql/` |
| SQLite | Generated dynamically from CSV columns via `pandas` | Generated; no file |

DuckDB transforms (lifted from MIT-LCP's `mimic-iv/buildmimic/duckdb/import_duckdb.sh`):

| # | Pattern | Replacement | Why |
| --- | --- | --- | --- |
| 1 | `TIMESTAMP\([0-9]+\)` | `TIMESTAMP` | DuckDB rejects `TIMESTAMP(N)` precision syntax |
| 2 | `spec_type_desc(.+)NOT NULL` | `spec_type_desc\1` | One zero-length string in source data, treated as NULL by DuckDB import |
| 3 | `drug +(VARCHAR.+)NOT NULL` | `drug \1` | Multiple zero-length strings in source data |

**Trade-off accepted:** each engine carries the artifact best-suited to its idioms; PRs that update a single engine touch one file. **Risk:** drift between engines when MIMIC schema versions change — each engine's DDL needs an independent update from MIT-LCP upstream. Mitigation: pin the MIT-LCP commit hash in `docs/upstream-sources.md` (future doc) so updates are auditable.

**Alternatives considered:**

- *Single canonical PG DDL + transforms for every engine* — rejected: MySQL diverges too far (type system, namespace, load syntax); SQLite has no use for pre-baked DDL.
- *SQLGlot transpilation* — rejected for DuckDB (overkill for 3 regexes), unsuitable for MySQL (transpilation doesn't generate `LOAD DATA LOCAL INFILE` clauses), inapplicable for SQLite (dynamic schema).

### Decision 2 — Config shape: discriminated union by `type`

**Chosen.** Each engine reads only its own block; `make_engine` enforces the shape per type.

```jsonc
// Postgres (existing shape; drop "+asyncpg" suffix — psycopg2 is what we use)
"database": { "type": "postgresql", "host": "pg", "port": 5432, "database": "postgres", "schema": "public" }

// MySQL (new)
"database": { "type": "mysql", "host": "mysql", "port": 3306, "database": "mimic" }

// DuckDB (new)
"database": { "type": "duckdb", "path": "/data/mimic.duckdb" }

// SQLite (new)
"database": { "type": "sqlite", "path": "/data/mimic4.db" }
```

**Trade-off accepted:** cleanest engine boundary; invalid fields surface immediately at engine construction. **Risk:** small backwards-incompatibility for anyone with a hand-edited `config.json` using `"postgresql+asyncpg"` — a one-character migration; note in CHANGELOG.

**Alternatives considered:**

- *Optional fields, engine ignores what it doesn't need* — rejected: hides config errors until runtime.
- *Nested per-engine blocks* — rejected: most blocks dead at any moment; verbose without benefit.

### Decision 3 — MySQL schema model

MySQL has no `schema` concept in the Postgres sense; it has *databases*. The existing config / DDL assumes `mimic_hosp.admissions`-style schema-qualified names. Three options for MySQL:

| Option | Mapping | Trade-off |
| --- | --- | --- |
| (a) One DB per schema | `mimic_hosp.admissions` → DB `mimic_hosp`, table `admissions` | Preserves structural grouping; importer must `CREATE DATABASE` per schema and switch contexts (`USE db` or fully-qualified names). Multiple JDBC connections from one client to query across "schemas". |
| (b) Single DB, prefixed tables | `mimic_hosp.admissions` → `mimic_hosp__admissions` in one DB | One connection from any client. Loses semantic grouping in tooling. |
| (c) Single DB, flat (MIT-LCP's choice) | `admissions` (no prefix) | Simplest. Loses the hosp/icu/ed/derived separation entirely. |

**Recommendation:** (a) — preserves the structural grouping that exists in every other engine in this stack, in exchange for some importer complexity. The cross-engine consistency is worth more than the per-engine simplicity.

**Status:** unconfirmed — needs sign-off before Phase 3b.

### Bulk-load mechanics per engine

| Engine | Mechanism | Notes |
| --- | --- | --- |
| Postgres | `\copy ... FROM PROGRAM 'gzip -dc ...'` via shelled-out `psql` | Unchanged from today |
| MySQL | `LOAD DATA LOCAL INFILE '...' INTO TABLE ... FIELDS TERMINATED BY ',' ...` | Requires `local_infile=1` server-side and on client; per-column `trim()` / NULL handling per MIT-LCP `load.sql` |
| DuckDB | `COPY {schema}.{table} FROM '{path}' (HEADER, DELIM ',', QUOTE '"', ESCAPE '"', COMPRESSION 'gzip')` | DuckDB reads `.csv.gz` natively, no decompression pipe |
| SQLite | `pandas.read_csv(...)` then `df.to_sql(table, conn, chunksize=10**6)` | Per MIT-LCP `import.py`; chunked for memory; dynamic schema inferred from CSV |

## Open questions

### Schema naming alignment (cross-engine)

MIT-LCP's DuckDB script writes to `mimiciv_hosp` / `mimiciv_icu`. MIT-LCP's MySQL `load.sql` uses no schemas at all (option (c) above). This repo's Postgres side uses `mimic_hosp` / `mimic_icu`.

**Recommendation:** keep this repo's existing `mimic_hosp` / `mimic_icu` everywhere. Users coming from MIT-LCP's DuckDB notebooks or MySQL examples will need to rename schemas / tables in queries — accepted one-time cost for internal consistency across the four engines this project ships.

**Status:** unconfirmed — sign off in conjunction with Decision 3.

### Pandas dependency for SQLite

`SQLiteEngine` needs `pandas` if we follow MIT-LCP's `import.py` approach. Pandas is a heavy dependency (numpy transitively). Alternatives:

- *Stream CSV with stdlib `csv` + `executemany`* — much smaller dep footprint; more code to write; we re-invent MIT-LCP's logic.
- *Accept pandas as a SQLite-only dependency* — `pixi.toml` can scope the dep to the `sqlite-builder` feature so the Postgres importer image stays slim.

**Recommendation:** scope pandas to the SQLite builder via pixi features; don't make every install pay for it.

**Status:** unconfirmed.

## Image / packaging changes

Today: one `mimic_import.dockerfile` installs `postgresql-client`.

Target — one builder/importer image per engine, scoped via pixi features:

| Image | Base | Engine deps | Output |
| --- | --- | --- | --- |
| `images/postgres-importer.dockerfile` | python-slim | `psycopg2`, `postgresql-client` (binary) | Loads into running PG container |
| `images/mysql-importer.dockerfile` | python-slim | `PyMySQL` or `mysql-connector-python`, `mysql-client` (for `LOAD DATA LOCAL INFILE`) | Loads into running MySQL container |
| `images/duckdb-builder.dockerfile` | python-slim | `duckdb` (pip) | `mimic.duckdb` on mounted volume |
| `images/sqlite-builder.dockerfile` | python-slim | `pandas`, `sqlite3` (stdlib) | `mimic4.db` on mounted volume |

`docker-compose.yaml` grows compose profiles per engine (e.g. `docker compose --profile duckdb up`); decide concrete shape during Phase 4.

## Implementation phases

Each phase is a reviewable PR. Later phases assume earlier ones are merged.

| Phase | Scope | Risk |
| --- | --- | --- |
| 0 | This plan doc | None |
| 1 | Module rename `pgmimic/` → `mimicstack/`; no behaviour change | Low — pure rename + import-path fixups |
| 2 | Scaffold `Engine` Protocol + `make_engine`; move existing PG logic into `PostgresEngine` behind the new interface | Medium — refactor of working code, needs end-to-end smoke test |
| 3a | Add `DuckDBEngine` with three regex DDL transforms + native `csv.gz` load | Medium — new dep, new code path |
| 3b | Add `MySQLEngine`: vendor MIT-LCP `load.sql`, `LOAD DATA LOCAL INFILE`, MySQL container in compose | Medium-high — schema model decision, MySQL-specific load quirks (`local_infile`) |
| 3c | Add `SQLiteEngine`: port MIT-LCP `import.py` approach (pandas chunked load + dynamic schema) | Medium — new dep (pandas), scoped via pixi |
| 4 | Per-engine Dockerfiles + compose profiles | Low — packaging |
| 5 | README rewrite; rename GitHub repository to `MimicDataStack` | Low — coordination only |

Phases 3a / 3b / 3c can in principle proceed in parallel after Phase 2 lands, but reviewing them serially is recommended to catch Engine-contract issues that surface only when the second or third implementation reveals an unworkable abstraction.

## Future work (deliberately deferred)

- **Spark engine** slotting into the same `Engine` Protocol: `{"type": "spark", "master": "spark://...", "warehouse": "s3://..."}`. The `match` statement in `make_engine` is the extension point.
- **BigQuery engine** — MIT-LCP supports it (`mimic-iv/buildmimic/bigquery/`); cloud-only, deferred until cloud-account onboarding story is solved.
- **k3s deployment** — Helm chart for the Postgres and MySQL paths. The file-mode engines (DuckDB, SQLite) won't benefit (in-process file producers; nothing to orchestrate).
- **DuckDB server-mode** — revisit if/when DuckDB ships a stable wire protocol that JDBC clients can speak directly.
