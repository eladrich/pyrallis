from dataclasses import dataclass
from enum import Enum, auto

import yaml
import json

from pyrallis.utils import PyrallisException
from .testutils import *


# List of simple attributes to use in tests:
two_arguments: List[Tuple[Type, Any, Any]] = [
    # type, first (parsed) value, second (parsed) different value
    (int,   123,     124),
    (int,   -1,      1),
    (float, 123.0,   124.0),
    (float, 0.123,   0.124),
    (bool,  True,    False),
    (str,   "bob",   "alice"),
    (str,   "[123]", "[124]"),
    (str,   "123",   "124"),
]

def switch_args(args):
    for t, a, b in args:
        yield (t, a, b)
        yield (t, b, a)

@pytest.fixture(params=list(switch_args(two_arguments)))
def two_attribute(request):
    """Test fixture that produces an tuple of (type, value 1, value 2) where
    both values are different"""
    return request.param


def test_multi_load(two_attribute, tmp_path):
    some_type, val_a, val_b = two_attribute

    @dataclass
    class SomeClass:
        val_a: Optional[some_type] = None
        val_b: Optional[some_type] = None
        val_c: Optional[some_type] = None

    a = SomeClass(val_a=val_a)
    b = SomeClass(val_a=val_b, val_b=val_b)
    d = SomeClass(val_b=val_b)

    # c = b, a
    c = SomeClass(val_a=val_a, val_b=val_b)

    tmp_file_a = tmp_path / 'config_a'
    pyrallis.dump(a, tmp_file_a.open('w'), omit_defaults=True)
    tmp_file_b = tmp_path / 'config_b'
    pyrallis.dump(b, tmp_file_b.open('w'), omit_defaults=True)
    tmp_file_d = tmp_path / 'config_d'
    pyrallis.dump(d, tmp_file_d.open('w'), omit_defaults=True)

    # b at second place overrides a
    # both as python arguments
    new_b = pyrallis.parse(config_class=SomeClass,
                           config_path=[tmp_file_a, tmp_file_b],
                           args="",
                           )
    assert new_b == b

    # both as commandline arguments
    arguments = shlex.split(f"--config_path {tmp_file_a} {tmp_file_b}")
    new_b = pyrallis.parse(config_class=SomeClass, args=arguments)
    assert new_b == b

    # mixed command line and python arguments
    arguments = shlex.split(f"--config_path {tmp_file_b}")
    new_b = pyrallis.parse(config_class=SomeClass, config_path=tmp_file_a, args=arguments)
    assert new_b == b

    # a at second place overrides b for some value only
    # both as python arguments
    new_c = pyrallis.parse(config_class=SomeClass,
                           config_path=[tmp_file_b, tmp_file_a],
                           args="",
                               )
    assert new_c == c

    # both as commandline arguments
    arguments = shlex.split(f"--config_path {tmp_file_b} {tmp_file_a}")
    new_c = pyrallis.parse(config_class=SomeClass, args=arguments)
    assert new_c == c


    # mixed command line and python arguments
    arguments = shlex.split(f"--config_path {tmp_file_a}")
    new_c = pyrallis.parse(config_class=SomeClass, config_path=tmp_file_b, args=arguments)
    assert new_c == c

    # merge files with mutually exclusive parameters
    # both as python arguments
    new_c = pyrallis.parse(config_class=SomeClass,
                           config_path=[tmp_file_a, tmp_file_d],
                           args="",
                               )
    assert new_c == c
