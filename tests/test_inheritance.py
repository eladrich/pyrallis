from dataclasses import dataclass, field

from .testutils import *


@dataclass
class Base(TestSetup):
    """Some extension of base-class `Base`"""

    a: int = 1


@dataclass
class ExtendedB(Base, TestSetup):
    b: int = 2


@dataclass
class ExtendedC(Base, TestSetup):
    c: int = 3


@dataclass
class Inheritance(TestSetup):
    ext_b: ExtendedB = ExtendedB()
    ext_c: ExtendedC = ExtendedC()


def test_simple_subclassing_no_args():
    extended = ExtendedB.setup()
    assert extended.a == 1
    assert extended.b == 2


def test_simple_subclassing_with_args():
    extended = ExtendedB.setup("--a 123 --b 56")
    assert extended.a == 123
    assert extended.b == 56


def test_subclasses_with_same_base_class_no_args():
    ext = Inheritance.setup()

    assert ext.ext_b.a == 1
    assert ext.ext_b.b == 2

    assert ext.ext_c.a == 1
    assert ext.ext_c.c == 3


def test_subclasses_with_same_base_class_with_args():
    import logging
    logging.basicConfig(level=logging.DEBUG)
    ext = Inheritance.setup(
        "--ext_b.a 10 --ext_c.a 30")
    print(ext.get_help_text())
    assert ext.ext_b.a == 10
    assert ext.ext_c.a == 30


def test_weird_structure():
    """both is-a, and has-a at the same time, a very weird inheritance structure"""

    @dataclass
    class ConvBlock:
        """A Block of Conv Layers."""

        n_layers: int = 4  # number of layers
        n_filters: List[int] = field(default_factory=[16, 32, 64, 64].copy)  # filters per layer

    from enum import Enum
    class Optimizers(Enum):
        ADAM = "ADAM"
        RMSPROP = "RMSPROP"
        SGD = "SGD"

    @dataclass
    class GeneratorHParams(ConvBlock):
        """Settings of the Generator model"""

        conv: ConvBlock = field(default_factory=ConvBlock)
        optimizer: Optimizers = field(default=Optimizers.ADAM)

    @dataclass
    class DiscriminatorHParams(ConvBlock):
        """Settings of the Discriminator model"""

        conv: ConvBlock = field(default_factory=ConvBlock)
        optimizer: Optimizers = field(default=Optimizers.ADAM)

    @dataclass
    class SomeWeirdClass(TestSetup):
        gen: GeneratorHParams = field(default_factory=GeneratorHParams)
        disc: DiscriminatorHParams = field(default_factory=DiscriminatorHParams)

    s = SomeWeirdClass.setup()
    assert s.gen.conv.n_layers == 4
    assert s.gen.n_layers == 4
    assert s.disc.conv.n_layers == 4
    assert s.disc.n_layers == 4
