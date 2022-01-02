from dataclasses import dataclass

from .testutils import *


def test_no_default_argument(simple_attribute):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass:
        a: some_type

    parser = ArgumentParser(config_class=SomeClass)

    cfg = parser.parse_args(shlex.split(f"--a {passed_value}"))
    assert cfg == SomeClass(a=expected_value)

    with raises(ParsingError):
        parser.parse_args("")


def test_default_dataclass_argument(simple_attribute, silent):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass:
        a: some_type = expected_value

    parser = ArgumentParser(config_class=SomeClass)

    cfg = parser.parse_args("")
    assert cfg == SomeClass(a=expected_value)
