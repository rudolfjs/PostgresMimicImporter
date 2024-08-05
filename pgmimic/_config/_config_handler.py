import json
import os


class ConfigHandler:
    def __init__(self, location: str = None) -> None:
        try:
            with open(location) as config_file:
                self.config = json.load(config_file)
                # add ENVS
                self.config["database"]["username"] = os.getenv("DB_USER")
                self.config["database"]["password"] = os.getenv("DB_PASSWORD")
                config_file.close()
        except Exception as e:
            print(repr(e))
        return None

    def get_config(self) -> json:
        return self.config
