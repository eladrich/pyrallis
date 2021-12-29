from dataclasses import dataclass

from .testutils import TestSetup


@dataclass
class Base(TestSetup):
    """Some extension of base-class `Base`"""

    a: int = 5
    f: bool = False


def test_bool_attributes_work():
    true_strings = ["True", "true"]
    for s in true_strings:
        ext = Base.setup(f"--a 5 --f {s}")
        assert ext.f == True

    false_strings = ["False", "false"]
    for s in false_strings:
        ext = Base.setup(f"--a 5 --f {s}")
        assert ext.f == False
