import os
import subprocess
from pathlib import Path

import psycopg2
from _config.models import Config


def _file_for_table(files: list[str], table: str) -> str:
    """Return the single CSV file in ``files`` whose basename is ``{table}.csv.gz``.

    Replaces the original substring match (``table in s``) which would silently
    pick the wrong file when one table name is a prefix of another — notably
    ``poe`` matching ``poe_detail.csv.gz`` first. Basename equality is exact and
    unambiguous; duplicates or absences raise instead of being papered over.
    """
    target = f"{table}.csv.gz"
    matches = [s for s in files if Path(s).name == target]
    if not matches:
        raise FileNotFoundError(f"No CSV found for table {table!r}")
    if len(matches) > 1:
        raise RuntimeError(f"Multiple CSVs found for table {table!r}: {matches}")
    return matches[0]


class DataHandler:
    SQL_DIR = (Path(__file__).parent / "SQL").resolve()

    def __init__(self, config: Config) -> None:
        self.config = config
        self._connect()

    def _connect(self) -> None:
        try:
            self.conn = psycopg2.connect(
                user=self.config.database.username,
                password=self.config.database.password,
                host=self.config.database.host,
                port=self.config.database.port,
                database=self.config.database.database,
            )
            return self.conn
        except ConnectionError as ce:
            print(f"FATAL: Connection error. {repr(ce)}")

    def _close(self) -> None:
        self.conn.close()

    def _data_schemas(self) -> list[str]:
        """Schemas whose `tables` entry is a `list[str]` of CSV-backed tables.

        Schemas whose entry is a `dict` (e.g. `mimic_derived` in 2.x or
        `mimiciv_derived` in 3.1) hold SQL-function outputs — there are no
        CSVs to COPY for them, and no rows to assert in `_check_data`. The
        previous implementation hardcoded the schema *name*, which broke
        silently when 3.1 renamed `mimic_derived` to `mimiciv_derived`.
        """
        return [s for s in self.config.data.schemas if isinstance(self.config.data.tables[s], list)]

    def _check_data(self) -> bool:
        # TODO - needs to change to check data in table,
        # not just that fact that the table exists.
        table_e_list = []
        exists = False
        db = self.config.database.database
        curr = self.conn.cursor()
        for schema in self._data_schemas():
            for table in self.config.data.tables[schema]:
                sql = f"""
                    SELECT EXISTS(SELECT 1 FROM information_schema.tables
                    WHERE table_catalog='{db}' AND
                        table_schema='{schema}' AND
                        table_name='{table}');
                """
                curr.execute(sql)
                result = curr.fetchone()
                result = result[0]
                if result is True:
                    table_e_list.append(True)
                else:
                    table_e_list.append(False)
        curr.close()
        if all(table_e_list) is True:
            exists = True
        else:
            exists = False

        return exists

    def _run_sql_file(self, filename: str) -> None:
        """Execute a whole versioned SQL file in one server round-trip.

        The previous implementation split on `;` and looped — but a
        `sql.split(";")` cuts straight through `/* ... ; ... */` block
        comments, dollar-quoted blocks, and single-quoted strings, feeding
        the server malformed statements. Postgres' own parser handles these
        correctly; pass the whole file in one `execute()` call and let the
        server do the parsing.

        On any error: rollback and re-raise. Loud failure beats silent
        partial import (the prior swallow-and-print behaviour left
        half-populated tables that the next run skipped because
        `_check_data` saw them as "already imported").
        """
        sql_path = self.SQL_DIR / self.config.data.version / filename
        sql = sql_path.read_text()
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql)
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def _create_constraint(self) -> None:
        self._run_sql_file("constraint.sql")

    def _create_index(self) -> None:
        self._run_sql_file("index.sql")

    def _create_tables(self) -> None:
        self._run_sql_file("create.sql")

    def _psql_args(self, command: str) -> list[str]:
        """Build the psql argv list. Credentials go via env, not the URL."""
        return [
            "psql",
            "-h",
            self.config.database.host,
            "-p",
            str(self.config.database.port),
            "-U",
            self.config.database.username or "",
            "-d",
            self.config.database.database,
            "-c",
            command,
        ]

    def _psql_env(self) -> dict[str, str]:
        """Inject `PGPASSWORD` so the password never appears in argv or process listing."""
        return {**os.environ, "PGPASSWORD": self.config.database.password or ""}

    def _create_postgres_functions(self) -> None:
        sql_path = self.SQL_DIR / self.config.data.version / "postgres-functions.sql"
        args = self._psql_args(f"\\i {sql_path}")
        subprocess.run(args, env=self._psql_env(), check=True)

    def _write_mimic_data(self, files: list[str]) -> None:
        for schema in self._data_schemas():
            for table in self.config.data.tables[schema]:
                file_path = _file_for_table(files, table)
                command = (
                    f"\\copy {schema}.{table} FROM PROGRAM "
                    f"'gzip -dc {file_path}' "
                    f"DELIMITER ',' CSV HEADER NULL ''"
                )
                args = self._psql_args(command)
                subprocess.run(args, env=self._psql_env(), check=True)
