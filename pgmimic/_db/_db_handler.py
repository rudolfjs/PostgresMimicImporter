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

    def _check_data(self) -> bool:
        # TODO - needs to change to check data in table,
        # not just that fact that the table exists.
        table_e_list = []
        exists = False
        db = self.config.database.database
        curr = self.conn.cursor()
        for schema in self.config.data.schemas:
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

    def _create_constraint(self):
        curr = self.conn.cursor()
        sql_path = self.SQL_DIR / self.config.data.version / "constraint.sql"
        with open(sql_path) as sql_file:
            sql = sql_file.read()
            for statement in sql.split(";"):
                curr = self.conn.cursor()
                if len(statement) < 1:
                    pass
                else:
                    try:
                        curr.execute(statement)
                        self.conn.commit()
                    except Exception as e:
                        print(f"FATAL: Error creating tables. {repr(e)}")
                try:
                    self.conn.commit()
                except Exception as e:
                    self.conn.rollback()
                    print(f"FATAL: Error creating tables. {repr(e)}")
                curr.close()
        return None

    def _create_index(self):
        curr = self.conn.cursor()
        sql_path = self.SQL_DIR / self.config.data.version / "index.sql"
        with open(sql_path) as sql_file:
            sql = sql_file.read()
            for statement in sql.split(";"):
                curr = self.conn.cursor()
                if len(statement) < 1:
                    pass
                else:
                    try:
                        curr.execute(statement)
                        self.conn.commit()
                    except Exception as e:
                        print(f"FATAL: Error creating tables. {repr(e)}")
                try:
                    self.conn.commit()
                except Exception as e:
                    self.conn.rollback()
                    print(f"FATAL: Error creating tables. {repr(e)}")
                curr.close()
        return None

    def _create_tables(self):
        curr = self.conn.cursor()
        sql_path = self.SQL_DIR / self.config.data.version / "create.sql"
        with open(sql_path) as sql_file:
            sql = sql_file.read()
            for statement in sql.split(";"):
                curr = self.conn.cursor()
                if len(statement) < 1:
                    pass
                else:
                    try:
                        curr.execute(statement)
                        self.conn.commit()
                    except Exception as e:
                        print(f"FATAL: Error creating tables. {repr(e)}")
                try:
                    self.conn.commit()
                except Exception as e:
                    self.conn.rollback()
                    print(f"FATAL: Error creating tables. {repr(e)}")
                curr.close()
        return None

    def _create_postgres_functions(self):
        sql_path = self.SQL_DIR / self.config.data.version / "postgres-functions.sql"
        psql_template = 'psql "postgresql://{}:{}@{}:{}/{}" --command "{}"'
        command = f"\\i {sql_path}"
        bash_command = psql_template.format(
            self.config.database.username,
            self.config.database.password,
            self.config.database.host,
            self.config.database.port,
            self.config.database.database,
            command.strip(),
        )
        print(bash_command)
        process = subprocess.Popen(bash_command, stdout=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        print(output)
        return None

    def _write_mimic_data(self, files: list[str]) -> None:
        # TODO - need to progress here
        psql_template = 'psql "postgresql://{}:{}@{}:{}/{}" --command "{}"'
        for schema in self.config.data.schemas:
            if schema == "mimic_derived":
                pass
            else:
                for table in self.config.data.tables[schema]:
                    file_path = _file_for_table(files, table)
                    command = (
                        f"\\copy {schema}.{table} FROM PROGRAM "
                        f"'gzip -dc {file_path}' "
                        f"DELIMITER ',' CSV HEADER NULL ''"
                    )
                    bash_command = psql_template.format(
                        self.config.database.username,
                        self.config.database.password,
                        self.config.database.host,
                        self.config.database.port,
                        self.config.database.database,
                        command.strip(),
                    )
                    print(bash_command)
                    process = subprocess.Popen(bash_command, stdout=subprocess.PIPE, shell=True)
                    output, error = process.communicate()
                    print(output)

        return None
