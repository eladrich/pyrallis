from dataclasses import dataclass, field
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pyrallis
from .testutils import *


def test_encode_something(simple_attribute):
    some_type, passed_value, expected_value = simple_attribute

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


def test_dump_load(simple_attribute, tmp_path):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass:
        d: Dict[str, some_type] = field(default_factory=dict)
        l: List[Tuple[some_type, some_type]] = field(default_factory=list)
        t: Dict[str, Optional[some_type]] = field(default_factory=dict)

    b = SomeClass()
    b.d.update({"hey": expected_value})
    b.l.append((expected_value, expected_value))
    b.t.update({"hey": None, "hey2": expected_value})

    tmp_file = tmp_path / 'config.yaml'
    pyrallis.dump(b, tmp_file.open('w'))

    new_b = pyrallis.ArgumentParser(config_class=SomeClass, config_path=tmp_file).parse_args("")
    assert new_b == b
    new_b = pyrallis.ArgumentParser(config_class=SomeClass).parse_args(shlex.split(f"--CONFIG {tmp_file}"))
    assert new_b == b


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
