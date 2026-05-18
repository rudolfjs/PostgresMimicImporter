# Platform Expansion Plan

> **Status:** Draft (WIP) — revised after independent review.
> **Branch:** `feat/expand-platform`
> **Scope of this document:** the decisions and module changes needed to add **DuckDB, MySQL, and SQLite** as additional engines alongside Postgres. A rebrand to `MimicDataStack` is *contingent* on the multi-engine premise being proven (see Phase 5); it is not a commitment of this plan.

## Goal

Expand `PostgresMimicImporter` from a Postgres-only loader into a multi-engine MIMIC data builder by reusing the per-engine build artifacts that [MIT-LCP/mimic-code](https://github.com/MIT-LCP/mimic-code/tree/main/mimic-iv/buildmimic) already maintains.

User-facing model after this work:

| Engine | Runtime | Result | Output |
| --- | --- | --- | --- |
| `postgresql` | docker / podman | Postgres container on `:5432` | Running service (today's behaviour) |
| `mysql` | docker / podman | MySQL container on `:3306` | Running service |
| `duckdb` | docker / podman | Builder container | `mimic.duckdb` file on mounted volume |
| `sqlite` | docker / podman | Builder container | `mimic4.db` file on mounted volume |

The four engines split into two families:

- **Server-mode** (Postgres, MySQL) — listen on a TCP port; importer connects, creates namespaces/tables, bulk-loads. End state is a long-running service.
- **File-mode** (DuckDB, SQLite) — in-process libraries; the build container produces a single database file and exits. Clients (DataGrip, DBeaver, native CLI) connect to the file directly. There is no port.

## Constraints discovered during planning

### Server-mode engines

- Postgres and MySQL behave alike at the "runtime container with a port" level.
- **MySQL has no schemas in the Postgres sense** — only databases. The upstream MIT-LCP MySQL DDL is namespace-flat. See Decision 3.
- **MySQL DDL is implicitly auto-committed** — no transactional DDL. Partial failures leave the database half-built; failure semantics must handle this explicitly. See "Failure semantics."

### File-mode engines

- **DuckDB and SQLite are in-process.** No TCP port; no client/server wire protocol. Clients open the file directly.
- DuckDB supports `CREATE SCHEMA` natively; SQLite does not (only `ATTACH DATABASE`, which is a different model). Therefore SQLite is forced into flat-table naming, matching MIT-LCP's `import.py`. See Decision 3.
- Server-mode-style options for DuckDB exist (`pg_duckdb`, MotherDuck, `duckdb-httpserver`, Arrow Flight SQL) but each is a meaningful architectural commitment. **Explicitly out of scope** for this iteration.

### Cross-engine namespace inconsistency (accepted)

| Engine | Namespace model | Source |
| --- | --- | --- |
| Postgres | Schemas (`mimic_hosp.admissions`) | Our existing DDL |
| DuckDB | Schemas (`mimic_hosp.admissions`) | PG DDL + 3 regex transforms |
| MySQL | Flat tables (`admissions`) | Vendored from MIT-LCP `load.sql` |
| SQLite | Flat tables (`admissions`) | Built dynamically by ported MIT-LCP `import.py` |

This asymmetry is an accepted trade-off, not a bug. Forcing schemas onto MySQL/SQLite would require maintaining our own DDL fork and breaking compatibility with MIT-LCP's reference implementations — see "Future work" for the eventual unification option.

### DDL divergence across engines

| Engine | DDL source | Why it diverges |
| --- | --- | --- |
| Postgres | Hand-written `create.sql` (this repo) | Canonical for this project |
| DuckDB | PG DDL + 3 regex transforms at runtime | Minor divergence (`TIMESTAMP(N)`, two `NOT NULL`s) |
| MySQL | **Generated upstream by `csv2mysql`**, vendored as `load.sql` (46 KB) | `DATETIME` vs `TIMESTAMP`, `BOOLEAN` vs `SMALLINT`, no schemas, `CHARACTER SET = UTF8MB4`, `LOAD DATA LOCAL INFILE` with per-column `trim()` / NULL conditionals — not regex-transformable from PG |
| SQLite | Built dynamically from CSV columns via `pandas.read_csv` | SQLite's dynamic typing makes pre-baked DDL unnecessary |

The MySQL `load.sql` is *generated*, not hand-written — the file header confirms `csv2mysql -o 1-load-no-keys.sql ...`. We vendor it as-is; updates from upstream are regenerated upstream, not edited by us.

## Upstream source pinning

We vendor or port behaviour from three MIT-LCP files. Pin them by commit SHA and blob SHA so future updates are auditable.

| Engine | Upstream path | Commit SHA | Blob SHA |
| --- | --- | --- | --- |
| DuckDB | `mimic-iv/buildmimic/duckdb/import_duckdb.sh` | `5706978309` | `3181611c16` |
| MySQL | `mimic-iv/buildmimic/mysql/load.sql` | `5706978309` | `4570f4da39` |
| SQLite | `mimic-iv/buildmimic/sqlite/import.py` | `5706978309` | `1cb8eb0d2d` |

Pinned commit: [`5706978309`](https://github.com/MIT-LCP/mimic-code/commit/57069783095e7770e66ea97da264c0200078ddbf) (2025-11-10). When refreshing, update the table above in the same PR that re-vendors.

## Out of scope (this iteration)

- k3s / Kubernetes manifests for any engine.
- Spark engine.
- BigQuery engine (MIT-LCP supports it; cloud-only, deferred).
- DuckDB-as-server in any form (HTTP extension, MotherDuck, `pg_duckdb`, Flight SQL).
- GitHub repository rename — **contingent on Phase 3a succeeding**; see Phase 5.
- Per-DB MySQL schemas (would unify the namespace model across engines but requires forking MIT-LCP's MySQL DDL). See "Future work."
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
| Existence check | `information_schema.tables` query (lines 36-41) | Mostly |
| DDL application | Reads `_db/SQL/{version}/*.sql`, naive `split(";")` (lines 102-121) | Yes |
| Bulk load | Shells out to `psql` with `\copy ... FROM PROGRAM 'gzip -dc ...'` (lines 143-167) | Heavily |

`pgmimic/_files/_file_handler.py` and `pgmimic/_config/_config_handler.py` are mostly engine-neutral already.

## Target architecture

### Module layout

In-tree rename `pgmimic/` → `mimicstack/`. (The user-facing `MimicDataStack` rebrand is separate and conditional — see Phase 5.)

```
mimicstack/
├── _config/_config_handler.py        # adds engine-aware validation
├── _files/_file_handler.py           # unchanged
├── importer/mimic_importer.py        # depends on Engine, not DataHandler
└── _db/
    ├── engine.py                     # NEW: Engine Protocol + make_engine factory
    ├── postgres_engine.py            # NEW: existing PG logic, mechanically moved
    ├── duckdb_engine.py              # NEW: in-process duckdb Python package
    ├── mysql_engine.py               # NEW: PyMySQL + LOAD DATA LOCAL INFILE
    ├── sqlite_engine.py              # NEW: stdlib sqlite3 + pandas
    └── SQL/2.2/
        ├── postgres/                 # MOVED: existing *.sql, unchanged
        └── mysql/                    # NEW: vendored MIT-LCP load.sql (see SHA above)
                                      # (no duckdb/, no sqlite/ — generated at runtime)

tests/
├── fixtures/                         # NEW: tiny CSVs per table, ~10 rows each
└── engines/                          # NEW: smoke test per engine
```

### Engine contract (lifecycle-explicit)

The Protocol below decomposes the build into distinct lifecycle stages. Each stage is allowed to be a no-op for engines that fold its work into another stage — but the *boundaries* are uniform, which lets the orchestrator be engine-agnostic.

```python
# mimicstack/_db/engine.py  (sketch — not yet implemented)
from pathlib import Path
from typing import Protocol


class Engine(Protocol):
    # ── Connection lifecycle ───────────────────────────────────────────────
    def connect(self) -> None: ...
    def close(self) -> None: ...

    # ── Idempotency check ──────────────────────────────────────────────────
    def data_loaded(self, expected: dict[str, list[str]]) -> bool:
        """True iff every expected table exists AND contains rows."""
        ...

    # ── Schema-build lifecycle (each step may be no-op for some engines) ──
    def prepare_namespaces(self, schemas: list[str]) -> None:
        """PG: CREATE SCHEMA. MySQL: CREATE DATABASE (currently only `mimic`).
        DuckDB: CREATE SCHEMA. SQLite: no-op."""
        ...

    def create_tables(self, schemas: dict[str, list[str]]) -> None:
        """PG/DuckDB: execute create.sql (transformed for DuckDB).
        MySQL: execute create+load file (interleaved — see load_dataset).
        SQLite: no-op (tables built during load_dataset by pandas)."""
        ...

    # ── Data load (engine chooses internal granularity) ───────────────────
    def load_dataset(self, schemas: dict[str, list[str]], files: list[Path]) -> None:
        """Load all CSVs. Engine chooses per-table streaming (PG, DuckDB),
        per-file chunked-pandas (SQLite), or interleaved create+load
        (MySQL via LOAD DATA LOCAL INFILE)."""
        ...

    # ── Post-load (each step may be no-op) ────────────────────────────────
    def create_indexes(self) -> None: ...
    def create_constraints(self) -> None: ...
    def apply_engine_functions(self) -> None:
        """PG materialised functions only; no-op for the others."""
        ...


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

**`MimicImporter` orchestration** then becomes:

```python
engine.connect()
if not engine.data_loaded(expected):
    engine.prepare_namespaces(list(schemas))
    engine.create_tables(schemas)
    engine.load_dataset(schemas, files)
    engine.create_indexes()
    engine.create_constraints()
    engine.apply_engine_functions()
engine.close()
```

Every engine implements every stage; some stages are deliberate no-ops. The orchestrator never branches on engine type.

## Decisions

### Decision 1 — DDL strategy: per-engine, three different approaches

**Chosen.** Each engine uses the artifact that best matches its model:

| Engine | DDL source | Storage |
| --- | --- | --- |
| Postgres | Existing hand-written `create.sql` | `_db/SQL/2.2/postgres/` |
| DuckDB | Postgres DDL + 3 regex transforms at runtime | Generated; no file |
| MySQL | Vendored `load.sql` (generated upstream by `csv2mysql`) | `_db/SQL/2.2/mysql/` |
| SQLite | Built dynamically from CSV columns via `pandas` | Generated; no file |

DuckDB transforms (lifted from MIT-LCP's `import_duckdb.sh`):

| # | Pattern | Replacement | Why |
| --- | --- | --- | --- |
| 1 | `TIMESTAMP\([0-9]+\)` | `TIMESTAMP` | DuckDB rejects `TIMESTAMP(N)` precision |
| 2 | `spec_type_desc(.+)NOT NULL` | `spec_type_desc\1` | One zero-length string in source data |
| 3 | `drug +(VARCHAR.+)NOT NULL` | `drug \1` | Multiple zero-length strings in source data |

**Trade-off accepted:** each engine carries the artifact best-suited to its idioms; PRs that update a single engine touch one file. **Risk:** drift between engines when MIMIC schema versions change — mitigated by SHA pinning (see "Upstream source pinning").

**Alternatives considered and rejected:**

- *Single canonical PG DDL + transforms for every engine* — MySQL diverges too far; SQLite has no use for pre-baked DDL.
- *SQLGlot transpilation* — overkill for DuckDB's 3 regexes; can't generate `LOAD DATA LOCAL INFILE` for MySQL; inapplicable for SQLite.

### Decision 2 — Config shape: discriminated union by `type`

**Chosen.** Each engine reads only its own block; `make_engine` enforces shape per type.

```jsonc
"database": { "type": "postgresql", "host": "pg", "port": 5432, "database": "postgres", "schema": "public" }
"database": { "type": "mysql",      "host": "mysql", "port": 3306, "database": "mimic" }
"database": { "type": "duckdb",     "path": "/data/mimic.duckdb" }
"database": { "type": "sqlite",     "path": "/data/mimic4.db" }
```

**Trade-off accepted:** cleanest engine boundary; invalid fields surface immediately at construction.
**Risk:** drop the `"+asyncpg"` suffix in the PG `type` string — note in CHANGELOG; one-character migration for existing users.

### Decision 3 — Namespace model: per-engine; accept MIT-LCP conventions where they diverge

**Chosen.** PG and DuckDB keep Postgres-style schemas; MySQL and SQLite use flat tables matching MIT-LCP's upstream conventions.

| Engine | Tables look like | Reason |
| --- | --- | --- |
| Postgres | `mimic_hosp.admissions` | Existing repo convention |
| DuckDB | `mimic_hosp.admissions` | DuckDB supports schemas; shares PG DDL |
| MySQL | `admissions` (no prefix) | MIT-LCP's vendored `load.sql` is namespace-flat; forcing one-DB-per-schema requires forking MIT-LCP DDL |
| SQLite | `admissions` (no prefix) | SQLite has no schemas; matches MIT-LCP `import.py` |

**Trade-off accepted:** cross-engine queries can't use uniform `schema.table` names. Users querying MIMIC across engines need to know each engine's convention. In exchange, we vendor MIT-LCP's reference implementations unchanged — fewer surprises, easier upstream updates.

**Earlier draft had this as "one MySQL database per Postgres schema."** That option was rejected on review: it would require maintaining a fork of MIT-LCP's MySQL DDL (splitting one `load.sql` into N per-schema files), it doesn't fix SQLite's flat-namespace constraint, and the user-visible benefit (uniform names in tooling) is achievable post-hoc via view-only schema mappings if demand surfaces.

**Status:** confirmed (this revision).

### Bulk-load mechanics per engine

| Engine | Mechanism | Internal granularity |
| --- | --- | --- |
| Postgres | `\copy ... FROM PROGRAM 'gzip -dc ...'` via shelled-out `psql` | Per table |
| MySQL | `LOAD DATA LOCAL INFILE '...' INTO TABLE ... FIELDS TERMINATED BY ',' ...` (requires `local_infile=1`) | Interleaved with table creation in vendored `load.sql` |
| DuckDB | `COPY {schema}.{table} FROM '{path}' (HEADER, DELIM ',', QUOTE '"', ESCAPE '"', COMPRESSION 'gzip')` | Per table |
| SQLite | `pandas.read_csv(..., chunksize=10**6)` → `df.to_sql(table, conn)` | Per file (chunked) |

The Engine Protocol's `load_dataset(schemas, files)` hides this granularity from the orchestrator.

## Failure semantics and partial-load policy

Each engine must declare a failure mode and a recovery mode. Codified explicitly so the importer doesn't leave half-built artifacts that the next run silently treats as "data already loaded."

| Engine | Failure mode | Recovery |
| --- | --- | --- |
| Postgres | DDL is transactional; bulk-load is not (per-table commits). Partial load → some tables full, others empty. | `data_loaded()` checks row counts per expected table; partial state forces a full re-run (drop + recreate). |
| MySQL | DDL is **implicitly auto-committed**. Partial load can leave half the DB created. | Same: row-count check; partial state forces drop + recreate. Document privilege requirement (`DROP`, `CREATE`, `FILE` for `LOAD DATA LOCAL INFILE`). |
| DuckDB | Single-process writer; crash mid-build leaves a truncated file. | Build into `{path}.tmp`; `os.rename({path}.tmp, {path})` only after `create_indexes`/`create_constraints` succeed. Atomic on POSIX. |
| SQLite | Same as DuckDB (single file). | Same `.tmp` + atomic rename strategy. |

`data_loaded()` is the integrity gate: it returns True only if **every** expected table is present **and** non-empty. Today's `_check_data()` (`_db_handler.py:27-55`) checks only existence — we are explicitly tightening this contract.

## Test strategy (must land with Phase 1)

A test matrix is non-negotiable before any engine-specific code lands. Codex review flagged this; the plan is:

- `tests/fixtures/2.2/` — tiny CSV files (~10 rows per table) covering at least one table from each schema (`mimic_hosp`, `mimic_icu`, `mimiciv_ed`). Include at least one row exercising the NULL/zero-length-string corner case that drives DuckDB's two `NOT NULL` regex transforms.
- `tests/engines/test_<engine>_smoke.py` — one per engine: build from fixtures, assert table counts, assert representative row, assert one cross-table JOIN works (validates relational integrity).
- `tests/engines/test_parity.py` — same query against all four engines, identical results modulo namespace prefix.
- CI runs the smoke matrix on every PR; parity test runs on `feat/expand-platform` branch PRs.

## Image / packaging changes

| Image | Base | Engine deps | Output |
| --- | --- | --- | --- |
| `images/postgres-importer.dockerfile` | python-slim | `psycopg2`, `postgresql-client` (binary) | Loads into running PG container |
| `images/mysql-importer.dockerfile` | python-slim | `PyMySQL`, `mysql-client` (for `LOAD DATA LOCAL INFILE`) | Loads into running MySQL container |
| `images/duckdb-builder.dockerfile` | python-slim | `duckdb` (pip) | `mimic.duckdb` on mounted volume |
| `images/sqlite-builder.dockerfile` | python-slim | `pandas`, `sqlite3` (stdlib) | `mimic4.db` on mounted volume |

Pandas is scoped to the SQLite builder feature in `pixi.toml`; other images don't pay for it.

`docker-compose.yaml` grows compose profiles per engine — concrete shape decided during Phase 4.

## Implementation phases

| Phase | Scope | Risk |
| --- | --- | --- |
| 0 | This plan doc | None |
| 1 | In-tree rename `pgmimic/` → `mimicstack/`; **add test fixtures and Postgres smoke test** (validates the renamed structure works end-to-end) | Low — pure rename + first tests |
| 2 | Scaffold `Engine` Protocol with the lifecycle-explicit shape; move existing PG logic into `PostgresEngine`; tighten `data_loaded()` to check row counts; add partial-load recovery for PG | Medium — refactor, but covered by Phase 1 smoke tests |
| 3a | Add `DuckDBEngine`: regex DDL transforms, native csv.gz load, `.tmp` + atomic rename | Medium — first non-PG engine; will reveal Protocol gaps if any |
| 3b | Add `MySQLEngine`: vendor MIT-LCP `load.sql` (flat namespace), `LOAD DATA LOCAL INFILE`, MySQL container in compose, document `local_infile=1` and required GRANTs | Medium-high — `LOAD DATA LOCAL INFILE` privilege footgun |
| 3c | Add `SQLiteEngine`: port MIT-LCP `import.py` (pandas chunked load + dynamic schema), `.tmp` + atomic rename, scope pandas via pixi feature | Medium — new dep (pandas) |
| 4 | Per-engine Dockerfiles + compose profiles | Low |
| 5 | **Conditional rebrand:** if Phases 3a–3c all shipped successfully, rename GitHub repo to `MimicDataStack`, rewrite README. **If 3a uncovered fundamental abstraction problems, do not rebrand** — the rebrand commits us publicly to a multi-engine story; we shouldn't commit until the story works. | Low (coordination) or N/A (abort) |

Phase 1 is the gate that protects everything downstream. If you skip the test fixtures here, every later phase reviews itself blind.

## Future work (deliberately deferred)

- **Per-DB MySQL schemas** — unify the cross-engine namespace model by mapping each Postgres schema to a separate MySQL database. Requires forking MIT-LCP's `load.sql` into per-schema chunks and accepting the resulting maintenance burden. Worth it only if real users hit the inconsistency.
- **View-based schema mapping for MySQL/SQLite** — create views like `mimic_hosp.admissions` over the flat tables. Cheap; could land as a Phase 6 polish if demand exists.
- **Spark engine** slotting into the same `Engine` Protocol: `{"type": "spark", "master": "spark://...", "warehouse": "s3://..."}`. The `match` statement in `make_engine` is the extension point.
- **BigQuery engine** — MIT-LCP supports it; cloud-only, deferred until cloud-account onboarding story exists.
- **k3s deployment** — Helm chart for PG and MySQL paths. File-mode engines won't benefit.
- **DuckDB server-mode** — revisit if/when DuckDB ships a stable wire protocol JDBC clients can speak directly.
