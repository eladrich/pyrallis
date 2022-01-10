from dataclasses import dataclass, field
from enum import Enum
from typing import Type, Any

import pyrallis
from pyrallis import ParsingError
from .testutils import parametrize, TestSetup, raises_missing_required_arg, raises


def test_basic_required_argument(simple_attribute, silent):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeDataclass(TestSetup):
        some_attribute: some_type  # type: ignore

    actual = SomeDataclass.setup(f"--some_attribute {passed_value}")
    assert actual.some_attribute == expected_value
    assert isinstance(actual.some_attribute, some_type)


def test_not_passing_required_argument_raises_error(simple_attribute):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeDataclass(TestSetup):
        some_attribute: some_type  # type: ignore

    with raises(ParsingError):
        _ = SomeDataclass.setup("")


def test_basic_optional_argument(simple_attribute, silent):
    some_type, _, expected_value = simple_attribute

    @dataclass
    class SomeDataclass(TestSetup):
        some_attribute: some_type = expected_value  # type: ignore

    actual = SomeDataclass.setup("")
    assert actual.some_attribute == expected_value
    assert isinstance(actual.some_attribute, some_type)


@parametrize(
    "some_type, default_value,  arg_value",
    [
        (int, 0, 1234),
        (float, 0.0, 123.456),
        (str, "", "bobby_boots"),
        (bool, False, True),
    ],
)
def test_arg_value_is_set_when_args_are_provided(
        some_type: Type, default_value: Any, arg_value: Any
):
    @dataclass
    class SomeClass(TestSetup):
        a: some_type = default_value  # type: ignore
        """some docstring for attribute 'a'"""

    class_a = SomeClass.setup(f"--a {arg_value}")
    assert class_a.a != default_value
    assert class_a.a == arg_value
    assert isinstance(class_a.a, some_type)


@parametrize(
    "some_type",
    [
        int,
        float,
        str,
        bool,
    ],
)
def test_not_providing_required_argument_throws_error(some_type):
    @dataclass
    class SomeClass(TestSetup):
        a: some_type  # type: ignore
        """some docstring for attribute 'a'"""

    with raises(ParsingError):
        _ = SomeClass.setup("")


@parametrize("some_type", [int, float, str])
def test_not_providing_required_argument_name_but_no_value_throws_error(some_type):
    @dataclass
    class SomeClass(TestSetup):
        a: some_type  # type: ignore
        """some docstring for attribute 'a'"""

    with raises(SystemExit):
        _ = SomeClass.setup("--a")


class Color(Enum):
    RED = "RED"
    ORANGE = "ORANGE"
    BLUE = "BLUE"


@dataclass
class Base(TestSetup):
    """A simple base-class example"""

    a: int  # TODO: finetune this
    """docstring for attribute 'a'"""
    b: float = 5.0  # inline comment on attribute 'b'
    c: str = ""


@dataclass
class Extended(Base):
    """Some extension of base-class `Base`"""

    d: int = 5
    """ docstring for 'd' in Extended. """
    e: Color = Color.BLUE


def test_parse_base_simple_works():
    b = Base.setup("--a 10 --b 3 --c Hello")
    assert b.a == 10
    assert b.b == 3
    assert b.c == "Hello"


def test_help_displays_class_docstring_text():
    assert Base.__doc__ in Base.get_help_text()


def test_enum_attributes_work():
    ext = Extended.setup("--a 5 --e RED")
    assert ext.e == Color.RED

    ext = Extended.setup("--a 5")
    assert ext.e == Color.BLUE


def test_parsing_twice():
    @dataclass
    class Foo:
        a: int = 123

    cfg = pyrallis.parse(config_class=Foo, args="")
    assert cfg.a == 123
    cfg = pyrallis.parse(config_class=Foo, args="--a 456".split())
    assert cfg.a == 456


def test_using_a_Type_type():
    @dataclass
    class Base:
        a: str = "a"

    @dataclass
    class Extended(Base):
        a: str = "extended_a"

    @dataclass
    class Foo(TestSetup):
        a_class: Type[Base] = field(default=Base, init=False)
        a: Base = field(default=None, init=False)

        def __post_init__(self):
            self.a = self.a_class()

    foo = Foo.setup("")
    from pyrallis.utils import contains_dataclass_type_arg

    assert not contains_dataclass_type_arg(Type[Base])
    assert foo.a_class() == Base()

    @dataclass
    class OtherFoo(Foo):
        a_class: Type[Base] = field(default=Extended, init=False)

    foo = OtherFoo.setup("")
    assert foo.a == Extended()
