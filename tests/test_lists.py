from dataclasses import dataclass, field
from typing import *
import pytest
from .testutils import *


def test_list_one_element(simple_attribute):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class Container(TestSetup):
        a: List[some_type] = field(default_factory=list)

    c = Container.setup("")
    assert c.a == []
    c = Container.setup(f"--a [{passed_value}]")
    assert c.a == [expected_value], Container.get_help_text()


@pytest.fixture
def ContainerClass():
    @dataclass
    class ContainerClass(TestSetup):
        a: Tuple[int]
        b: List[int]
        c: Tuple[str] = tuple()
        d: List[int] = field(default_factory=list)

    return ContainerClass


def test_single_element_list(ContainerClass):
    container = ContainerClass.setup("--a [1] --b [4] --c [7] --d [10]")
    assert container.a == (1,)
    assert container.b == [4]
    assert container.c == ("7",)
    assert container.d == [10]


def test_required_attributes_works(ContainerClass):
    with raises(ParsingError):
        ContainerClass.setup("--b [4]")

    with raises(ParsingError):
        ContainerClass.setup("--a [4]")

    container = ContainerClass.setup("--a [4] --b [5]")
    assert container == ContainerClass(a=(4,), b=[5])


def test_default_value(ContainerClass):
    container = ContainerClass.setup("--a [1] --b '[4, 5, 6]'")
    assert container.a == (1,)
    assert container.b == [4, 5, 6]
    assert container.c == tuple()
    assert container.d == list()


@parametrize(
    "item_type, passed_values",
    [
        (int, [[1, 2], [4, 5], [7, 8]]),
        (float, [[1.1, 2.1], [4.2, 5.2], [7.2, 8.2]]),
        (str, [["a", "b"], ["c", "d"], ["e", "f"]]),
        (bool, [[True, True], [True, False], [False, True]]),
    ],
)
def test_parse_multiple_with_list_attributes(
        item_type: Type,
        passed_values: List[List[Any]],
):
    @dataclass
    class SomeClass(TestSetup):
        a: List[item_type] = field(default_factory=list)  # type: ignore
        """some docstring for attribute 'a'"""

    for value in passed_values:
        arguments = "--a " + format_list_using_brackets(value)
        result = SomeClass.setup(arguments)
        assert result == SomeClass(a=value)


@parametrize(
    "item_type, type_hint, value, arg",
    [
        (list, List, [1, 2, 3], '[1, 2, 3]'),
        (set, Set, {1, 2, 3}, '[1, 2, 3]'),
        (tuple, Tuple, (1, 2, 3), '[1, 2, 3]'),
        (dict, Dict, {1: 2}, '{1: 2}')
    ],
)
def test_collection_no_type(item_type, type_hint, value, arg):
    @dataclass
    class ContainerHint(TestSetup):
        a: type_hint

    c = ContainerHint.setup(f"--a '{arg}'")
    assert c.a == value

    @dataclass
    class ContainerType(TestSetup):
        a: item_type

    c = ContainerType.setup(f"--a '{arg}'")
    assert c.a == value

