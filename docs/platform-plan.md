# Platform Expansion Plan

> **Status:** Draft (WIP)
> **Branch:** `feat/expand-platform`
> **Scope of this document:** the decisions and module changes needed to add DuckDB as a second engine alongside Postgres, and to rename the project to reflect a multi-engine vision. Future engines (Spark) and platforms (k3s) are deliberately out of scope here.

## Goal

Expand `PostgresMimicImporter` from a Postgres-only loader into a multi-engine MIMIC data builder. First addition: **DuckDB as a flat-file artifact** (`mimic.duckdb`). Rename the project to **`MimicDataStack`** to signal that engines and platforms are now composable layers.

User-facing model after this work:

| Pick an engine | Pick a runtime | Result |
| --- | --- | --- |
| `postgresql` | docker / podman | Postgres container on `:5432`, importer loads MIMIC into it (today's behaviour) |
| `duckdb` | docker / podman | Builder container produces a `mimic.duckdb` file on a mounted volume; open it locally with DuckDB CLI, DataGrip, or any DuckDB client |

## Constraints discovered during planning

- **DuckDB is in-process.** No TCP port, no client/server wire protocol. The official `duckdb/duckdb` Docker image is a CLI in a container; there is no `:5432`-equivalent.
- Clients like DataGrip connect to DuckDB by pointing the JDBC driver at a **`.duckdb` file on disk**, not over a network. This pipeline therefore produces a file artifact, not a running service.
- Docker / Podman are still valuable here: they bundle the build environment so users don't install DuckDB or Python locally to produce the file.
- Server-mode-style options exist (`pg_duckdb`, MotherDuck, `duckdb-httpserver` community extension, Arrow Flight SQL) but each is a meaningful architectural commitment. **Explicitly out of scope** for this iteration.

## Out of scope (this iteration)

- k3s / Kubernetes manifests for either engine.
- Spark engine.
- DuckDB-as-server in any form (HTTP extension, MotherDuck, `pg_duckdb`, Flight SQL).
- Repository rename on GitHub — handled as a separate operation once the in-tree rename lands.
- Schema changes to MIMIC data itself.

## Current state

Already on `main`:

- Postgres importer (`pgmimic/` package, `psycopg2` + shelled-out `psql` for bulk load).
- Docker support (`docker-compose.yaml`, `mimic_import.dockerfile`).
- **Podman / podman-compose support** (added in `c2d2864`, refined in `6d06394`).
- Pixi-managed Python environment (added in `6d2b8fc`).

The runtime side of the matrix (docker, podman) is therefore mostly covered; this plan focuses on the **engine** axis.

### Where Postgres-specific code lives today

`pgmimic/_db/_db_handler.py:1-169` is a single `DataHandler` class mashing four concerns:

| Concern | Implementation | Postgres-coupled? |
| --- | --- | --- |
| Connection | `psycopg2.connect()` (line 13) | Yes |
| Existence check | `information_schema.tables` query (lines 36-41) | Mostly (DuckDB supports `information_schema` too) |
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
    └── SQL/
        └── 2.2/
            ├── postgres/             # MOVED: existing *.sql, unchanged
            └── (no duckdb/ folder)   # DuckDB DDL is generated at runtime — see Decision 1
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
    def apply_ddl(self, sql_path: Path) -> None: ...
    def load_table(self, schema: str, table: str, csv_gz_path: Path) -> None: ...
    def apply_post_load(self) -> None: ...   # PG functions on PG; no-op on DuckDB


def make_engine(config: dict) -> Engine:
    db = config["database"]
    match db["type"]:
        case "postgresql":
            return PostgresEngine(
                host=db["host"], port=db["port"],
                database=db["database"], schema=db["schema"],
                user=db["username"], password=db["password"],
            )
        case "duckdb":
            return DuckDBEngine(path=Path(db["path"]))
        case t:
            raise ValueError(f"unknown engine type: {t!r}")
```

`MimicImporter` collapses to a ~30-line orchestrator that depends only on `Engine`; no `psycopg2` import survives outside `postgres_engine.py`.

## Decisions

### Decision 1 — DDL strategy: canonical Postgres + regex transforms

**Chosen.** Postgres DDL remains the single source of truth. `DuckDBEngine.apply_ddl` applies three regex transforms (lifted from MIT-LCP's `mimic-iv/buildmimic/duckdb/import_duckdb.sh`) before executing:

| # | Pattern | Replacement | Why |
| --- | --- | --- | --- |
| 1 | `TIMESTAMP\([0-9]+\)` | `TIMESTAMP` | DuckDB rejects `TIMESTAMP(N)` precision syntax |
| 2 | `spec_type_desc(.+)NOT NULL` | `spec_type_desc\1` | One zero-length string in source data, treated as NULL by DuckDB import |
| 3 | `drug +(VARCHAR.+)NOT NULL` | `drug \1` | Multiple zero-length strings in source data |

**Trade-off accepted:** single source of truth for DDL; transforms live in Python and are easy to extend. **Risk:** future Postgres-isms in upstream MIMIC DDL may require new regexes.

**Alternatives considered:**

- *Per-engine SQL files* — rejected: dual maintenance burden whenever MIMIC schema changes.
- *SQLGlot transpilation* — rejected for now: adds a heavy dependency for only three currently-known divergences. Reconsider if the regex list grows beyond ~6 patterns.

### Decision 2 — Config shape: discriminated union by `type`

**Chosen.** Each engine reads only its own block; `make_engine` enforces the shape per type.

```jsonc
// Postgres (existing shape, but drop the "+asyncpg" suffix — psycopg2 is what we use)
"database": {
  "type": "postgresql",
  "host": "pg",
  "port": 5432,
  "database": "postgres",
  "schema": "public"
}

// DuckDB (new)
"database": {
  "type": "duckdb",
  "path": "/data/mimic.duckdb"
}
```

**Trade-off accepted:** cleanest engine boundary; invalid fields surface immediately at engine construction. **Risk:** small backwards-incompatibility for anyone with a hand-edited `config.json` using `"postgresql+asyncpg"` — a one-character migration; note in CHANGELOG.

**Alternatives considered:**

- *Optional fields, engine ignores what it doesn't need* — rejected: hides config errors until runtime.
- *Nested per-engine blocks (`{"engine": ..., "postgres": {...}, "duckdb": {...}}`)* — rejected: most blocks are dead at any given moment; verbosity without benefit.

### Bulk-load mechanics per engine

- **Postgres** (unchanged): `\copy ... FROM PROGRAM 'gzip -dc ...'` via shelled-out `psql`.
- **DuckDB** (new): native gzip support, no decompression pipe:

  ```sql
  COPY {schema}.{table}
  FROM '{csv_gz_path}'
  (HEADER, DELIM ',', QUOTE '"', ESCAPE '"', COMPRESSION 'gzip');
  ```

## Open questions

### Schema naming alignment

MIT-LCP's DuckDB script writes to `mimiciv_hosp` / `mimiciv_icu`. This repo's Postgres side uses `mimic_hosp` / `mimic_icu`. Because we share a single canonical DDL across engines, both engines will produce identical schema names — they cannot diverge by construction.

**Recommendation:** keep this repo's existing `mimic_hosp` / `mimic_icu`. Users coming from MIT-LCP's DuckDB notebooks will need to rename schemas in their queries; that's an accepted, one-time cost in exchange for internal consistency between the engines this project ships.

**Status:** unconfirmed — needs sign-off before Phase 3.

## Image / packaging changes

Today: one `mimic_import.dockerfile` installs `postgresql-client`.

Target:

- `images/postgres-importer.dockerfile` — current image, unchanged behaviour.
- `images/duckdb-builder.dockerfile` — slim Python + `pip install duckdb`. No client binaries. Output: `mimic.duckdb` file on a mounted volume.
- `docker-compose.yaml` either stays Postgres-focused or grows a `--profile duckdb`. Decide during Phase 4 when the actual surface area is visible.

## Implementation phases

Each phase is a reviewable PR. Later phases assume earlier ones are merged.

| Phase | Scope | Risk |
| --- | --- | --- |
| 0 | This plan doc | None |
| 1 | Module rename `pgmimic/` → `mimicstack/`; no behaviour change | Low — pure rename + import-path fixups |
| 2 | Scaffold `Engine` Protocol + `make_engine`; move existing PG logic into `PostgresEngine` behind the new interface | Medium — refactor of working code, needs end-to-end smoke test |
| 3 | Add `DuckDBEngine` with the three regex DDL transforms + native `csv.gz` load | Medium — new dependency, new code path |
| 4 | New Dockerfile for DuckDB builder; docker-compose profile or separate compose file | Low — packaging |
| 5 | README rewrite; rename GitHub repository to `MimicDataStack` | Low — coordination only |

## Future work (deliberately deferred)

- **Spark engine** slotting into the same `Engine` Protocol: `{"type": "spark", "master": "spark://...", "warehouse": "s3://..."}`. The `match` statement in `make_engine` is the extension point.
- **k3s deployment** — Helm chart for the Postgres path. The DuckDB path is unlikely to benefit (in-process file producer; nothing to orchestrate).
- **DuckDB server-mode** — revisit if/when DuckDB ships a stable wire protocol that JDBC clients can speak directly.
