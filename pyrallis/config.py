from enum import Enum
from typing import Union


class ConfigType(str, Enum):
    YAML = 'yaml'
    JSON = 'json'
    TOML = 'toml'


class Config:
    config_type: ConfigType = ConfigType.YAML

    @staticmethod
    def set_config_type(type_val: Union[ConfigType, str]):
        if type(type_val) == str:
            type_val = ConfigType(type_val)
        Config.config_type = type_val

    @staticmethod
    def get_config_type() -> ConfigType:
        return Config.config_type
