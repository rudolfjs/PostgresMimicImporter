import json

from _config.models import Config


class ConfigHandler:
    def __init__(self, location: str) -> None:
        with open(location) as config_file:
            raw = json.load(config_file)
        self.config: Config = Config.model_validate(raw)

    def get_config(self) -> Config:
        return self.config
