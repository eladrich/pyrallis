from dataclasses import dataclass, field
from typing import *

import pyrallis.utils as utils
from .testutils import *


@dataclass
class SomeDataclass:
    x: float = 123


@parametrize(
    "t",
    [
        Tuple[int, ...],
        Tuple[str],
        Tuple,
        tuple,
    ],
)
def test_is_tuple(t: Type):
    assert utils.is_tuple(t)
    assert not utils.is_list(t)


@parametrize(
    "t",
    [
        List[int],
        List[str],
        List,
        list,
        List[SomeDataclass],
    ],
)
def test_is_list(t: Type):
    assert utils.is_list(t)
    assert not utils.is_tuple(t)


@parametrize(
    "t",
    [
        List[SomeDataclass],
        Tuple[SomeDataclass],
    ],
)
def test_is_list_of_dataclasses(t: Type):
    assert utils.is_tuple_or_list_of_dataclasses(t)


@dataclass
class A:
    a: str = "bob"


import enum


class Color(enum.Enum):
    RED = "RED"
    ORANGE = "ORANGE"
    BLUE = "BLUE"


class Temperature(enum.IntEnum):
    HOT = 1
    WARM = 0
    COLD = -1
    MONTREAL = -35


@parametrize(
    "t",
    [
        Color,
        Temperature,
    ],
)
def test_is_enum(t: Type):
    assert utils.is_enum(t)


def test_list_field():
    @dataclass
    class A:
        a: List[str] = field(default_factory=["bob", "john", "bart"].copy)

    a1 = A()
    a2 = A()
    assert id(a1.a) != id(a2.a)


def test_set_field():
    @dataclass
    class A:
        a: Set[str] = field(default_factory=lambda: {"bob", "john", "bart"})

    a1 = A()
    a2 = A()
    assert id(a1.a) != id(a2.a)


def test_dict_field():
    default = {"bob": 0, "john": 1, "bart": 2}

    @dataclass
    class A:
        a: Dict[str, int] = field(default_factory=default.copy)

    a1 = A()
    print(a1.a)
    assert a1.a == default
    a2 = A()
    assert id(a1.a) != id(a2.a)


def test_dict_field_with_keyword_args():
    default = {"bob": 0, "john": 1, "bart": 2}

    @dataclass
    class A(TestSetup):
        a: Dict[str, int] = field(default_factory=dict(bob=0, john=1, bart=2).copy)

    a1 = A()
    a2 = A()
    assert a1.a == a2.a == default
    assert id(a1.a) != id(a2.a)


def test_dict_field_without_args():
    default = {}

    @dataclass
    class A(TestSetup):
        a: Dict[str, int] = field(default_factory=dict)

    a1 = A()
    a2 = A()
    assert a1.a == a2.a == default
    assert id(a1.a) != id(a2.a)
