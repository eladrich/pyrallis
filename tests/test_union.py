from dataclasses import dataclass
from typing import Union

from .testutils import *


def test_union_type():
    @dataclass
    class Foo(TestSetup):
        x: Union[float, str] = 0

    foo = Foo.setup("--x 1.2")
    assert foo.x == 1.2

    foo = Foo.setup("--x bob")
    assert foo.x == "bob"
