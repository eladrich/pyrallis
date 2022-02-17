from typing import Type, TypeVar

from pyrallis import utils
from pyrallis.options import Options
from pyrallis.parsers.decoding import decode
from pyrallis.parsers.encoding import encode

Dataclass = TypeVar("Dataclass")


def parse_string(s):
    parser = Options.get_config_type().value
    return parser.parse_string(s)


def load_config(stream):
    parser = Options.get_config_type().value
    return parser.load_config(stream)


def save_config(d, stream=None, **kwargs):
    parser = Options.get_config_type().value
    return parser.save_config(d, stream, **kwargs)


def load(t: Type[Dataclass], stream):
    dict = load_config(stream)
    return decode(t, dict)


def dump(config: Dataclass, stream=None, omit_defaults: bool = False, **kwargs):
    """
    Dump the config file to yaml.
    optionally omit any value that still has a default value
    """
    config_dict = encode(config)
    if omit_defaults:
        defaults_dict = encode(utils.get_defaults_dict(config))
        config_dict = utils.remove_matching(config_dict, defaults_dict)
    return save_config(config_dict, stream, **kwargs)
