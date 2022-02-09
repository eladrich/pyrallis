from builtins import TypeError
from dataclasses import dataclass, field
from enum import Enum, auto

from tests.testutils import *


class Color(Enum):
    blue: str = auto()
    red: str = auto()
    green: str = auto()
    orange: str = auto()


def test_passing_enum_to_choice():
    @dataclass
    class Something(TestSetup):
        favorite_color: Color = field(default=Color.green)
        colors: List[Color] = field(default_factory=[Color.green].copy)

    s = Something.setup("")
    assert s.favorite_color == Color.green
    assert s.colors == [Color.green]

    s = Something.setup("--colors [blue,red]")
    assert s.colors == [Color.blue, Color.red]


#
#
def test_passing_enum_to_choice_no_default_makes_required_arg():
    @dataclass
    class Something(TestSetup):
        favorite_color: Color = field()

    with raises(ParsingError):
        s = Something.setup("")

    s = Something.setup("--favorite_color blue")
    assert s.favorite_color == Color.blue


def test_passing_enum_to_choice_is_same_as_enum_attr():
    @dataclass
    class Something1(TestSetup):
        favorite_color: Color = Color.orange

    @dataclass
    class Something2(TestSetup):
        favorite_color: Color = field(default=Color.orange)

    s1 = Something1.setup("--favorite_color green")
    s2 = Something2.setup("--favorite_color green")
    assert s1.favorite_color == s2.favorite_color

    s = Something1.setup("--favorite_color blue")
    assert s.favorite_color == Color.blue
    s = Something2.setup("--favorite_color blue")
    assert s.favorite_color == Color.blue
