from _config._config_handler import ConfigHandler
from _files._file_handler import FileHandler
from _db._db_handler import DataHandler


class MimicImporter:
    def __init__(self, config) -> None:
        # set config
        try:
            self._config_handler = ConfigHandler(config)
            self.config = self._config_handler.get_config()
        except Exception as e:
            print(repr(e))
        return None

    def connect(self) -> None:
        # Expects that config is loaded
        """
        Connect to PostgreSQL server per config
        """
        self._db_handler = DataHandler(self.config)
        return None

    def import_mimic(self) -> None:
        # Expects that config is loaded, connection established
        # check if data already loaded
        if self._db_handler._check_data():
            print("Data already imported...")
            pass
        else:
            # create tables
            print("Creating tables...\n")
            self._db_handler._create_tables()
            print("Tables created...\n")
            # check data is available in path
            self._file_handler = FileHandler()
            try:
                self.file_path = self._file_handler.path(
                    f"{self.config['data']['location']}/{self.config['data']['version']}"
                )
            except Exception as e:
                print(
                    f"FATAL: Error finding files in path. Error Message: {repr(e)}"
                )
            files = self._file_handler.files()
            # import data
            self._db_handler._write_mimic_data(files)
            # create constraints
            print("Creating constraints...")
            self._db_handler._create_constraint()
            # create index
            print("Creating indexes...")
            self._db_handler._create_index()
            print("Creating Postgres functions...")
            self._db_handler._create_postgres_functions()
            print("MIMIC import completed")
        return None

    def close(self) -> None:
        """
        Close MIMIC Importer created connections
        """
        # close database connection
        self._db_handler._close()
        return None
