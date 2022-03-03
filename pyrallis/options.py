import contextlib
from typing import Union

from pyrallis.parsers.config_parsers import ParserEnum, YAMLParser, JSONParser, TOMLParser


class ConfigType(ParserEnum):
    YAML = YAMLParser
    JSON = JSONParser
    TOML = TOMLParser


class Options:
    _config_type: ConfigType = ConfigType.YAML

    @staticmethod
    def set_config_type(new_type: Union[ConfigType, str]):
        if isinstance(new_type, str):
            new_type = ConfigType[new_type.upper()]
        Options._config_type = new_type

    @staticmethod
    def get_config_type() -> ConfigType:
        return Options._config_type


@contextlib.contextmanager
def config_type(new_type: Union[ConfigType, str]):
    current_type = Options.get_config_type()
    try:
        Options.set_config_type(new_type)
        yield
    finally:
        Options.set_config_type(current_type)
