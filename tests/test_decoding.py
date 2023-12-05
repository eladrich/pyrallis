from dataclasses import dataclass, field
from enum import Enum, auto

import yaml
import json
import toml

from pyrallis.utils import PyrallisException
from .testutils import *


class Color(Enum):
    blue: str = auto()
    red: str = auto()


def test_encode_something(simple_attribute):
    some_type, _, expected_value = simple_attribute

    @dataclass
    class SomeClass:
        d: Dict[str, some_type] = field(default_factory=dict)
        l: List[Tuple[some_type, some_type]] = field(default_factory=list)
        t: Dict[str, Optional[some_type]] = field(default_factory=dict)

    b = SomeClass()
    b.d.update({"hey": expected_value})
    b.l.append((expected_value, expected_value))
    b.t.update({"hey": None, "hey2": expected_value})

    assert pyrallis.decode(SomeClass, pyrallis.encode(b)) == b


@parametrize('config_type', ['', 'yaml', 'json', 'toml'])
def test_dump_load(simple_attribute, config_type, tmp_path):
    some_type, _, expected_value = simple_attribute

    if config_type != '':
        pyrallis.set_config_type(config_type)

    @dataclass
    class SomeClass:
        val: Optional[some_type] = None

    b = SomeClass(val=expected_value)

    tmp_file = tmp_path / 'config'
    pyrallis.dump(b, tmp_file.open('w'))

    new_b = pyrallis.parse(config_class=SomeClass, config_path=tmp_file, args="")
    assert new_b == b

    arguments = ['--config_path', str(tmp_file)]
    new_b = pyrallis.parse(config_class=SomeClass, args=arguments)
    assert new_b == b

    new_b = pyrallis.parse(config_class=SomeClass, args="")
    assert new_b != b

    pyrallis.set_config_type('yaml')


def test_dump_load_context():
    @dataclass
    class SomeClass:
        val: str = 'hello'

    b = SomeClass()

    yaml_str = pyrallis.dump(b)
    assert yaml_str == yaml.dump(pyrallis.encode(b))

    with pyrallis.config_type('json'):
        json_str = pyrallis.dump(b)
        assert json_str == json.dumps(pyrallis.encode(b))

    yaml_str = pyrallis.dump(b)
    assert yaml_str == yaml.dump(pyrallis.encode(b))

    assert pyrallis.get_config_type() is pyrallis.ConfigType.YAML


def test_dump_load_dicts(simple_attribute, tmp_path):
    some_type, _, expected_value = simple_attribute

    @dataclass
    class SomeClass:
        d: Dict[str, some_type] = field(default_factory=dict)
        l: List[Tuple[some_type, some_type]] = field(default_factory=list)
        t: Dict[str, Optional[some_type]] = field(default_factory=dict)

    b = SomeClass()
    b.d.update({"hey": expected_value})
    b.l.append((expected_value, expected_value))
    b.t.update({"hey": None, "hey2": expected_value})

    tmp_file = tmp_path / 'config'
    pyrallis.dump(b, tmp_file.open('w'))

    new_b = pyrallis.parse(config_class=SomeClass, config_path=tmp_file, args="")
    assert new_b == b
    arguments = ['--config_path', str(tmp_file)]
    new_b = pyrallis.parse(config_class=SomeClass, args=arguments)
    assert new_b == b


def test_dump_load_enum(tmp_path):
    @dataclass
    class SomeClass:
        color: Color = Color.red

    b = SomeClass()
    tmp_file = tmp_path / 'config.yaml'
    pyrallis.dump(b, tmp_file.open('w'))

    new_b = pyrallis.parse(config_class=SomeClass, config_path=tmp_file, args="")
    assert new_b == b


def test_reserved_config_word():
    @dataclass
    class MainClass:
        config_path: str = ""

    with raises(PyrallisException):
        pyrallis.parse(MainClass)


def test_super_nesting():
    @dataclass
    class Complicated:
        x: List[
            List[List[Dict[int, Tuple[int, float, str, List[float]]]]]
        ] = field(default_factory=list)

    c = Complicated()
    c.x = [[[{0: (2, 1.23, "bob", [1.2, 1.3])}]]]
    assert pyrallis.decode(Complicated, pyrallis.encode(c)) == c
#
#
