import psycopg2
import subprocess


class DataHandler:
    def __init__(self, config):
        self.config = config
        self._connect()
        return None

    def _connect(self) -> None:
        try:
            self.conn = psycopg2.connect(
                user=self.config["database"]["username"],
                password=self.config["database"]["password"],
                host=self.config["database"]["host"],
                port=self.config["database"]["port"],
                database=self.config["database"]["database"],
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
        db = self.config["database"]["database"]
        curr = self.conn.cursor()
        for schema in self.config["data"]["schemas"]:
            for table in self.config["data"]["tables"][schema]:
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
        with open(f"_db/SQL/{self.config['data']['version']}/constraint.sql") as sql_file:
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
        with open(f"_db/SQL/{self.config['data']['version']}/index.sql") as sql_file:
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
        with open(f"_db/SQL/{self.config['data']['version']}/create.sql") as sql_file:
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
        file_path = f"{self.config['data']['version']}/postgres-functions.sql"
        psql_template = 'psql "postgresql://{}:{}@{}:{}/{}" --command "{}"'
        command = f"\i _db/SQL/{file_path}"
        bash_command = psql_template.format(
                    self.config["database"]["username"],
                    self.config["database"]["password"],
                    self.config["database"]["host"],
                    self.config["database"]["port"],
                    self.config["database"]["database"],
                    command.strip()
                )
        print(bash_command)
        process = subprocess.Popen(
            bash_command, stdout=subprocess.PIPE, shell=True
        )
        output, error = process.communicate()
        print(output)
        return None
    
    def _write_mimic_data(self, files: list = None) -> None:
        # TODO - need to progress here
        psql_template = 'psql "postgresql://{}:{}@{}:{}/{}" --command "{}"'
        for schema in self.config["data"]["schemas"]:
            if schema == "mimic_derived":
                pass
            else:
                for table in self.config["data"]["tables"][schema]:
                    file_path = [s for s in files if table in s][0]
                    command = f"\copy {schema}.{table} FROM PROGRAM 'gzip -dc \
                        {file_path} ' DELIMITER ',' CSV HEADER NULL ''"
                    bash_command = psql_template.format(
                        self.config["database"]["username"],
                        self.config["database"]["password"],
                        self.config["database"]["host"],
                        self.config["database"]["port"],
                        self.config["database"]["database"],
                        command.strip(),
                    )
                    print(bash_command)
                    process = subprocess.Popen(
                        bash_command, stdout=subprocess.PIPE, shell=True
                    )
                    output, error = process.communicate()
                    print(output)

        return None
