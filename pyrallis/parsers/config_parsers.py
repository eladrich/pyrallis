from abc import ABC, abstractmethod
from enum import Enum
from inspect import isclass


class Parser(ABC):

    @staticmethod
    @abstractmethod
    def parse_string(s):
        pass

    @staticmethod
    @abstractmethod
    def load_config(stream):
        pass

    @staticmethod
    @abstractmethod
    def save_config(d, stream=None, **kwargs):
        pass


class ParserEnum(Enum):
    def __init__(self, *args):
        if not isclass(self.value) or not issubclass(self.value, Parser):
            raise TypeError('All enum values must be parsers')


class YAMLParser(Parser):

    @staticmethod
    def parse_string(s):
        import yaml
        return yaml.safe_load(s)

    @staticmethod
    def load_config(stream):
        import yaml
        return yaml.full_load(stream)

    @staticmethod
    def save_config(d, stream=None, **kwargs):
        import yaml
        return yaml.dump(d, stream, **kwargs)


class JSONParser(Parser):

    @staticmethod
    def parse_string(s):
        import json
        try:
            return json.loads(s)
        except json.decoder.JSONDecodeError:
            return s  # No parsing to be done, simply return value

    @staticmethod
    def load_config(stream):
        import json
        return json.load(stream)

    @staticmethod
    def save_config(d, stream=None, **kwargs):
        import json
        if stream is None:
            return json.dumps(d, **kwargs)
        else:
            return json.dump(d, stream, **kwargs)


class TOMLParser(Parser):

    @staticmethod
    def parse_string(s):
        import toml
        try:
            return toml.loads(f'val = {s}')['val']
        except toml.decoder.TomlDecodeError:
            return s

    @staticmethod
    def load_config(stream):
        import toml
        return toml.load(stream)

    @staticmethod
    def save_config(d, stream=None, **kwargs):
        import toml
        if stream is None:
            return toml.dumps(d, **kwargs)
        else:
            return toml.dump(d, stream, **kwargs)
