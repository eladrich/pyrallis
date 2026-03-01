"""Tests for nested dataclass containers: List[Dataclass], Dict[str, Dataclass], etc.

Tests cover pyrallis.encode, pyrallis.decode, and pyrallis.parse (via config files).
"""
import shlex
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

import pyrallis


# ── Shared dataclasses used across tests ─────────────────────────────────────


class Color(Enum):
    red = auto()
    blue = auto()
    green = auto()


@dataclass
class Point:
    x: float = 0.0
    y: float = 0.0


@dataclass
class Person:
    name: str = ""
    age: int = 0


@dataclass
class Tag:
    key: str = ""
    value: str = ""


@dataclass
class NestedInner:
    label: str = ""
    scores: List[float] = field(default_factory=list)


@dataclass
class WithEnum:
    color: Color = Color.red
    intensity: float = 1.0


# ── Encode / Decode: List of dataclasses ─────────────────────────────────────


class TestEncodeDecodeListOfDataclasses:

    def test_list_of_simple_dataclass_roundtrip(self):
        @dataclass
        class Config:
            points: List[Point] = field(default_factory=list)

        cfg = Config(points=[Point(1.0, 2.0), Point(3.0, 4.0)])
        encoded = pyrallis.encode(cfg)
        assert encoded == {"points": [{"x": 1.0, "y": 2.0}, {"x": 3.0, "y": 4.0}]}
        decoded = pyrallis.decode(Config, encoded)
        assert decoded == cfg

    def test_list_of_dataclass_empty(self):
        @dataclass
        class Config:
            points: List[Point] = field(default_factory=list)

        cfg = Config(points=[])
        encoded = pyrallis.encode(cfg)
        assert encoded == {"points": []}
        decoded = pyrallis.decode(Config, encoded)
        assert decoded == cfg

    def test_list_of_dataclass_single_item(self):
        @dataclass
        class Config:
            people: List[Person] = field(default_factory=list)

        cfg = Config(people=[Person("Alice", 30)])
        encoded = pyrallis.encode(cfg)
        assert encoded == {"people": [{"name": "Alice", "age": 30}]}
        decoded = pyrallis.decode(Config, encoded)
        assert decoded == cfg

    def test_list_of_dataclass_many_items(self):
        @dataclass
        class Config:
            people: List[Person] = field(default_factory=list)

        people = [Person(f"person_{i}", i) for i in range(20)]
        cfg = Config(people=people)
        decoded = pyrallis.decode(Config, pyrallis.encode(cfg))
        assert decoded == cfg

    def test_list_of_dataclass_with_nested_list(self):
        """Dataclass inside list itself contains a list field."""

        @dataclass
        class Config:
            items: List[NestedInner] = field(default_factory=list)

        cfg = Config(items=[
            NestedInner("a", [1.0, 2.0]),
            NestedInner("b", [3.0]),
            NestedInner("c", []),
        ])
        encoded = pyrallis.encode(cfg)
        decoded = pyrallis.decode(Config, encoded)
        assert decoded == cfg

    def test_list_of_dataclass_with_enum(self):
        @dataclass
        class Config:
            items: List[WithEnum] = field(default_factory=list)

        cfg = Config(items=[
            WithEnum(Color.red, 0.5),
            WithEnum(Color.blue, 1.0),
        ])
        encoded = pyrallis.encode(cfg)
        decoded = pyrallis.decode(Config, encoded)
        assert decoded == cfg

    def test_list_of_dataclass_preserves_order(self):
        @dataclass
        class Config:
            tags: List[Tag] = field(default_factory=list)

        tags = [Tag(f"k{i}", f"v{i}") for i in range(10)]
        cfg = Config(tags=tags)
        decoded = pyrallis.decode(Config, pyrallis.encode(cfg))
        assert decoded.tags == tags

    def test_list_of_dataclass_alongside_plain_fields(self):
        @dataclass
        class Config:
            name: str = "default"
            count: int = 0
            points: List[Point] = field(default_factory=list)

        cfg = Config(name="test", count=5, points=[Point(1.0, 2.0)])
        decoded = pyrallis.decode(Config, pyrallis.encode(cfg))
        assert decoded == cfg


# ── Encode / Decode: Dict of dataclasses ─────────────────────────────────────


class TestEncodeDecodeDictOfDataclasses:

    def test_dict_of_simple_dataclass_roundtrip(self):
        @dataclass
        class Config:
            points: Dict[str, Point] = field(default_factory=dict)

        cfg = Config(points={"origin": Point(0.0, 0.0), "target": Point(1.0, 2.0)})
        encoded = pyrallis.encode(cfg)
        assert encoded == {
            "points": {
                "origin": {"x": 0.0, "y": 0.0},
                "target": {"x": 1.0, "y": 2.0},
            }
        }
        decoded = pyrallis.decode(Config, encoded)
        assert decoded == cfg

    def test_dict_of_dataclass_empty(self):
        @dataclass
        class Config:
            mapping: Dict[str, Person] = field(default_factory=dict)

        cfg = Config(mapping={})
        encoded = pyrallis.encode(cfg)
        assert encoded == {"mapping": {}}
        decoded = pyrallis.decode(Config, encoded)
        assert decoded == cfg

    def test_dict_of_dataclass_single_entry(self):
        @dataclass
        class Config:
            mapping: Dict[str, Person] = field(default_factory=dict)

        cfg = Config(mapping={"alice": Person("Alice", 30)})
        encoded = pyrallis.encode(cfg)
        assert encoded == {"mapping": {"alice": {"name": "Alice", "age": 30}}}
        decoded = pyrallis.decode(Config, encoded)
        assert decoded == cfg

    def test_dict_of_dataclass_many_entries(self):
        @dataclass
        class Config:
            mapping: Dict[str, Person] = field(default_factory=dict)

        mapping = {f"person_{i}": Person(f"name_{i}", i) for i in range(20)}
        cfg = Config(mapping=mapping)
        decoded = pyrallis.decode(Config, pyrallis.encode(cfg))
        assert decoded == cfg

    def test_dict_of_dataclass_with_nested_list(self):
        """Dict values are dataclasses that themselves contain lists."""

        @dataclass
        class Config:
            mapping: Dict[str, NestedInner] = field(default_factory=dict)

        cfg = Config(mapping={
            "first": NestedInner("a", [1.0, 2.0]),
            "second": NestedInner("b", []),
        })
        decoded = pyrallis.decode(Config, pyrallis.encode(cfg))
        assert decoded == cfg

    def test_dict_of_dataclass_with_enum(self):
        @dataclass
        class Config:
            items: Dict[str, WithEnum] = field(default_factory=dict)

        cfg = Config(items={
            "warm": WithEnum(Color.red, 0.8),
            "cool": WithEnum(Color.blue, 0.2),
        })
        decoded = pyrallis.decode(Config, pyrallis.encode(cfg))
        assert decoded == cfg

    def test_dict_of_dataclass_int_keys(self):
        @dataclass
        class Config:
            mapping: Dict[int, Point] = field(default_factory=dict)

        cfg = Config(mapping={1: Point(1.0, 2.0), 2: Point(3.0, 4.0)})
        decoded = pyrallis.decode(Config, pyrallis.encode(cfg))
        assert decoded == cfg

    def test_dict_of_dataclass_alongside_plain_fields(self):
        @dataclass
        class Config:
            name: str = "default"
            count: int = 0
            mapping: Dict[str, Point] = field(default_factory=dict)

        cfg = Config(name="test", count=5, mapping={"p": Point(1.0, 2.0)})
        decoded = pyrallis.decode(Config, pyrallis.encode(cfg))
        assert decoded == cfg


# ── Encode / Decode: Mixed containers ────────────────────────────────────────


class TestEncodeDecodeMixedContainers:

    def test_both_list_and_dict_of_dataclasses(self):
        @dataclass
        class Config:
            points: List[Point] = field(default_factory=list)
            people: Dict[str, Person] = field(default_factory=dict)

        cfg = Config(
            points=[Point(1.0, 2.0), Point(3.0, 4.0)],
            people={"alice": Person("Alice", 30), "bob": Person("Bob", 25)},
        )
        decoded = pyrallis.decode(Config, pyrallis.encode(cfg))
        assert decoded == cfg

    def test_nested_dataclass_with_list_of_dataclasses(self):
        """Outer dataclass has a nested dataclass field AND a list-of-dataclass field."""

        @dataclass
        class Inner:
            value: int = 0

        @dataclass
        class Config:
            primary: Inner = field(default_factory=Inner)
            others: List[Inner] = field(default_factory=list)

        cfg = Config(primary=Inner(42), others=[Inner(1), Inner(2), Inner(3)])
        decoded = pyrallis.decode(Config, pyrallis.encode(cfg))
        assert decoded == cfg

    def test_nested_dataclass_with_dict_of_dataclasses(self):
        @dataclass
        class Inner:
            value: int = 0

        @dataclass
        class Config:
            primary: Inner = field(default_factory=Inner)
            named: Dict[str, Inner] = field(default_factory=dict)

        cfg = Config(primary=Inner(42), named={"a": Inner(1), "b": Inner(2)})
        decoded = pyrallis.decode(Config, pyrallis.encode(cfg))
        assert decoded == cfg

    def test_dict_of_dataclass_containing_list_of_dataclass(self):
        """Dict values are dataclasses that contain a list-of-dataclass field."""

        @dataclass
        class Team:
            members: List[Person] = field(default_factory=list)

        @dataclass
        class Config:
            teams: Dict[str, Team] = field(default_factory=dict)

        cfg = Config(teams={
            "alpha": Team(members=[Person("Alice", 30), Person("Bob", 25)]),
            "beta": Team(members=[Person("Charlie", 35)]),
        })
        decoded = pyrallis.decode(Config, pyrallis.encode(cfg))
        assert decoded == cfg

    def test_list_of_dataclass_containing_dict(self):
        """List items are dataclasses that contain a dict field."""

        @dataclass
        class Entry:
            metadata: Dict[str, str] = field(default_factory=dict)

        @dataclass
        class Config:
            entries: List[Entry] = field(default_factory=list)

        cfg = Config(entries=[
            Entry(metadata={"key1": "val1", "key2": "val2"}),
            Entry(metadata={"key3": "val3"}),
        ])
        decoded = pyrallis.decode(Config, pyrallis.encode(cfg))
        assert decoded == cfg

    def test_tuple_of_dataclasses(self):
        @dataclass
        class Config:
            points: Tuple[Point, ...] = field(default_factory=tuple)

        cfg = Config(points=(Point(1.0, 2.0), Point(3.0, 4.0)))
        decoded = pyrallis.decode(Config, pyrallis.encode(cfg))
        assert decoded == cfg

    def test_deeply_nested_containers(self):
        """Multiple levels of nesting: dataclass -> dict -> dataclass -> list -> dataclass."""

        @dataclass
        class Leaf:
            val: int = 0

        @dataclass
        class Branch:
            leaves: List[Leaf] = field(default_factory=list)

        @dataclass
        class Tree:
            branches: Dict[str, Branch] = field(default_factory=dict)

        cfg = Tree(branches={
            "left": Branch(leaves=[Leaf(1), Leaf(2)]),
            "right": Branch(leaves=[Leaf(3)]),
        })
        decoded = pyrallis.decode(Tree, pyrallis.encode(cfg))
        assert decoded == cfg


# ── pyrallis.parse via config file ───────────────────────────────────────────


class TestParseListOfDataclasses:

    def test_parse_list_of_dataclass_from_yaml(self, tmp_path):
        @dataclass
        class Config:
            points: List[Point] = field(default_factory=list)

        cfg = Config(points=[Point(1.0, 2.0), Point(3.0, 4.0)])

        tmp_file = tmp_path / "config.yaml"
        pyrallis.dump(cfg, tmp_file.open("w"))

        loaded = pyrallis.parse(config_class=Config, config_path=tmp_file, args="")
        assert loaded == cfg

    def test_parse_list_of_dataclass_empty_from_yaml(self, tmp_path):
        @dataclass
        class Config:
            points: List[Point] = field(default_factory=list)

        cfg = Config(points=[])

        tmp_file = tmp_path / "config.yaml"
        pyrallis.dump(cfg, tmp_file.open("w"))

        loaded = pyrallis.parse(config_class=Config, config_path=tmp_file, args="")
        assert loaded == cfg

    def test_parse_list_of_dataclass_many_items_from_yaml(self, tmp_path):
        @dataclass
        class Config:
            people: List[Person] = field(default_factory=list)

        people = [Person(f"person_{i}", i) for i in range(10)]
        cfg = Config(people=people)

        tmp_file = tmp_path / "config.yaml"
        pyrallis.dump(cfg, tmp_file.open("w"))

        loaded = pyrallis.parse(config_class=Config, config_path=tmp_file, args="")
        assert loaded == cfg

    def test_parse_list_of_nested_dataclass_from_yaml(self, tmp_path):
        @dataclass
        class Config:
            items: List[NestedInner] = field(default_factory=list)

        cfg = Config(items=[
            NestedInner("a", [1.0, 2.0]),
            NestedInner("b", [3.0]),
        ])

        tmp_file = tmp_path / "config.yaml"
        pyrallis.dump(cfg, tmp_file.open("w"))

        loaded = pyrallis.parse(config_class=Config, config_path=tmp_file, args="")
        assert loaded == cfg

    def test_parse_list_of_dataclass_with_enum_from_yaml(self, tmp_path):
        @dataclass
        class Config:
            items: List[WithEnum] = field(default_factory=list)

        cfg = Config(items=[WithEnum(Color.red, 0.5), WithEnum(Color.blue, 1.0)])

        tmp_file = tmp_path / "config.yaml"
        pyrallis.dump(cfg, tmp_file.open("w"))

        loaded = pyrallis.parse(config_class=Config, config_path=tmp_file, args="")
        assert loaded == cfg

    def test_parse_list_of_dataclass_config_path_via_args(self, tmp_path):
        """Pass config_path via --config_path CLI arg."""

        @dataclass
        class Config:
            points: List[Point] = field(default_factory=list)

        cfg = Config(points=[Point(1.0, 2.0)])

        tmp_file = tmp_path / "config.yaml"
        pyrallis.dump(cfg, tmp_file.open("w"))

        arguments = shlex.split(f"--config_path {tmp_file}")
        loaded = pyrallis.parse(config_class=Config, args=arguments)
        assert loaded == cfg


class TestParseDictOfDataclasses:

    def test_parse_dict_of_dataclass_from_yaml(self, tmp_path):
        @dataclass
        class Config:
            mapping: Dict[str, Point] = field(default_factory=dict)

        cfg = Config(mapping={"origin": Point(0.0, 0.0), "target": Point(1.0, 2.0)})

        tmp_file = tmp_path / "config.yaml"
        pyrallis.dump(cfg, tmp_file.open("w"))

        loaded = pyrallis.parse(config_class=Config, config_path=tmp_file, args="")
        assert loaded == cfg

    def test_parse_dict_of_dataclass_empty_from_yaml(self, tmp_path):
        @dataclass
        class Config:
            mapping: Dict[str, Person] = field(default_factory=dict)

        cfg = Config(mapping={})

        tmp_file = tmp_path / "config.yaml"
        pyrallis.dump(cfg, tmp_file.open("w"))

        loaded = pyrallis.parse(config_class=Config, config_path=tmp_file, args="")
        assert loaded == cfg

    def test_parse_dict_of_dataclass_many_entries_from_yaml(self, tmp_path):
        @dataclass
        class Config:
            mapping: Dict[str, Person] = field(default_factory=dict)

        mapping = {f"person_{i}": Person(f"name_{i}", i) for i in range(10)}
        cfg = Config(mapping=mapping)

        tmp_file = tmp_path / "config.yaml"
        pyrallis.dump(cfg, tmp_file.open("w"))

        loaded = pyrallis.parse(config_class=Config, config_path=tmp_file, args="")
        assert loaded == cfg

    def test_parse_dict_of_nested_dataclass_from_yaml(self, tmp_path):
        @dataclass
        class Config:
            mapping: Dict[str, NestedInner] = field(default_factory=dict)

        cfg = Config(mapping={
            "first": NestedInner("a", [1.0, 2.0]),
            "second": NestedInner("b", []),
        })

        tmp_file = tmp_path / "config.yaml"
        pyrallis.dump(cfg, tmp_file.open("w"))

        loaded = pyrallis.parse(config_class=Config, config_path=tmp_file, args="")
        assert loaded == cfg

    def test_parse_dict_of_dataclass_with_enum_from_yaml(self, tmp_path):
        @dataclass
        class Config:
            items: Dict[str, WithEnum] = field(default_factory=dict)

        cfg = Config(items={
            "warm": WithEnum(Color.red, 0.8),
            "cool": WithEnum(Color.blue, 0.2),
        })

        tmp_file = tmp_path / "config.yaml"
        pyrallis.dump(cfg, tmp_file.open("w"))

        loaded = pyrallis.parse(config_class=Config, config_path=tmp_file, args="")
        assert loaded == cfg

    def test_parse_dict_of_dataclass_config_path_via_args(self, tmp_path):
        @dataclass
        class Config:
            mapping: Dict[str, Point] = field(default_factory=dict)

        cfg = Config(mapping={"p": Point(1.0, 2.0)})

        tmp_file = tmp_path / "config.yaml"
        pyrallis.dump(cfg, tmp_file.open("w"))

        arguments = shlex.split(f"--config_path {tmp_file}")
        loaded = pyrallis.parse(config_class=Config, args=arguments)
        assert loaded == cfg


class TestParseMixedContainers:

    def test_parse_both_list_and_dict_from_yaml(self, tmp_path):
        @dataclass
        class Config:
            points: List[Point] = field(default_factory=list)
            people: Dict[str, Person] = field(default_factory=dict)

        cfg = Config(
            points=[Point(1.0, 2.0)],
            people={"alice": Person("Alice", 30)},
        )

        tmp_file = tmp_path / "config.yaml"
        pyrallis.dump(cfg, tmp_file.open("w"))

        loaded = pyrallis.parse(config_class=Config, config_path=tmp_file, args="")
        assert loaded == cfg

    def test_parse_nested_dataclass_alongside_list_from_yaml(self, tmp_path):
        """Config has both a direct nested dataclass and a list-of-dataclass."""

        @dataclass
        class Inner:
            value: int = 0

        @dataclass
        class Config:
            primary: Inner = field(default_factory=Inner)
            others: List[Inner] = field(default_factory=list)

        cfg = Config(primary=Inner(42), others=[Inner(1), Inner(2)])

        tmp_file = tmp_path / "config.yaml"
        pyrallis.dump(cfg, tmp_file.open("w"))

        loaded = pyrallis.parse(config_class=Config, config_path=tmp_file, args="")
        assert loaded == cfg

    def test_parse_nested_dataclass_alongside_dict_from_yaml(self, tmp_path):
        @dataclass
        class Inner:
            value: int = 0

        @dataclass
        class Config:
            primary: Inner = field(default_factory=Inner)
            named: Dict[str, Inner] = field(default_factory=dict)

        cfg = Config(primary=Inner(42), named={"a": Inner(1), "b": Inner(2)})

        tmp_file = tmp_path / "config.yaml"
        pyrallis.dump(cfg, tmp_file.open("w"))

        loaded = pyrallis.parse(config_class=Config, config_path=tmp_file, args="")
        assert loaded == cfg

    def test_parse_deeply_nested_from_yaml(self, tmp_path):
        @dataclass
        class Leaf:
            val: int = 0

        @dataclass
        class Branch:
            leaves: List[Leaf] = field(default_factory=list)

        @dataclass
        class Tree:
            branches: Dict[str, Branch] = field(default_factory=dict)

        cfg = Tree(branches={
            "left": Branch(leaves=[Leaf(1), Leaf(2)]),
            "right": Branch(leaves=[Leaf(3)]),
        })

        tmp_file = tmp_path / "config.yaml"
        pyrallis.dump(cfg, tmp_file.open("w"))

        loaded = pyrallis.parse(config_class=Tree, config_path=tmp_file, args="")
        assert loaded == cfg

    def test_parse_defaults_without_config_file(self):
        """When no config file is provided, default (empty) containers should work."""

        @dataclass
        class Config:
            points: List[Point] = field(default_factory=list)
            mapping: Dict[str, Person] = field(default_factory=dict)
            name: str = "default"

        loaded = pyrallis.parse(config_class=Config, args="")
        assert loaded == Config()
        assert loaded.points == []
        assert loaded.mapping == {}
        assert loaded.name == "default"


# ── Dump / Load roundtrip (cfgparsing) ──────────────────────────────────────


class TestDumpLoadRoundtrip:

    def test_dump_load_list_of_dataclass(self, tmp_path):
        @dataclass
        class Config:
            points: List[Point] = field(default_factory=list)

        cfg = Config(points=[Point(1.0, 2.0), Point(3.0, 4.0)])

        tmp_file = tmp_path / "config.yaml"
        pyrallis.dump(cfg, tmp_file.open("w"))

        loaded = pyrallis.load(Config, tmp_file.open("r"))
        assert loaded == cfg

    def test_dump_load_dict_of_dataclass(self, tmp_path):
        @dataclass
        class Config:
            mapping: Dict[str, Person] = field(default_factory=dict)

        cfg = Config(mapping={"alice": Person("Alice", 30), "bob": Person("Bob", 25)})

        tmp_file = tmp_path / "config.yaml"
        pyrallis.dump(cfg, tmp_file.open("w"))

        loaded = pyrallis.load(Config, tmp_file.open("r"))
        assert loaded == cfg

    def test_dump_load_mixed(self, tmp_path):
        @dataclass
        class Config:
            name: str = "test"
            points: List[Point] = field(default_factory=list)
            people: Dict[str, Person] = field(default_factory=dict)

        cfg = Config(
            name="experiment",
            points=[Point(1.0, 2.0)],
            people={"alice": Person("Alice", 30)},
        )

        tmp_file = tmp_path / "config.yaml"
        pyrallis.dump(cfg, tmp_file.open("w"))

        loaded = pyrallis.load(Config, tmp_file.open("r"))
        assert loaded == cfg


# ── Edge cases ───────────────────────────────────────────────────────────────


class TestEdgeCases:

    def test_list_of_dataclass_with_default_values_only(self):
        """Dataclass items use all default values."""

        @dataclass
        class Config:
            points: List[Point] = field(default_factory=list)

        cfg = Config(points=[Point(), Point()])
        decoded = pyrallis.decode(Config, pyrallis.encode(cfg))
        assert decoded == cfg
        assert all(p.x == 0.0 and p.y == 0.0 for p in decoded.points)

    def test_dict_of_dataclass_with_default_values_only(self):
        @dataclass
        class Config:
            mapping: Dict[str, Point] = field(default_factory=dict)

        cfg = Config(mapping={"a": Point(), "b": Point()})
        decoded = pyrallis.decode(Config, pyrallis.encode(cfg))
        assert decoded == cfg

    def test_encode_produces_plain_dicts_and_lists(self):
        """Verify encoded output contains only plain dicts and lists, no dataclass instances."""

        @dataclass
        class Config:
            points: List[Point] = field(default_factory=list)
            mapping: Dict[str, Person] = field(default_factory=dict)

        cfg = Config(
            points=[Point(1.0, 2.0)],
            mapping={"alice": Person("Alice", 30)},
        )
        encoded = pyrallis.encode(cfg)

        # Top level is dict
        assert isinstance(encoded, dict)
        # points is a list of dicts
        assert isinstance(encoded["points"], list)
        assert all(isinstance(p, dict) for p in encoded["points"])
        # mapping is a dict of dicts
        assert isinstance(encoded["mapping"], dict)
        assert all(isinstance(v, dict) for v in encoded["mapping"].values())

    def test_list_of_dataclass_identity_decode_encode(self):
        """decode(encode(x)) == x for list of dataclasses."""

        @dataclass
        class Config:
            items: List[Tag] = field(default_factory=list)

        cfg = Config(items=[Tag("a", "1"), Tag("b", "2"), Tag("c", "3")])
        assert pyrallis.decode(Config, pyrallis.encode(cfg)) == cfg

    def test_dict_of_dataclass_identity_decode_encode(self):
        @dataclass
        class Config:
            items: Dict[str, Tag] = field(default_factory=dict)

        cfg = Config(items={"x": Tag("a", "1"), "y": Tag("b", "2")})
        assert pyrallis.decode(Config, pyrallis.encode(cfg)) == cfg


# ── CLI arg support for container-of-dataclass fields ────────────────────────


class TestCLIListOfDataclasses:
    """List[Dataclass] fields can be set via CLI as a YAML/JSON string."""

    def test_list_of_dataclass_via_cli_yaml_sequence(self):
        @dataclass
        class Config:
            points: List[Point] = field(default_factory=list)

        result = pyrallis.parse(Config, args=["--points", "[{x: 1.0, y: 2.0}, {x: 3.0, y: 4.0}]"])
        assert result.points == [Point(1.0, 2.0), Point(3.0, 4.0)]

    def test_list_of_dataclass_via_cli_json_string(self):
        @dataclass
        class Config:
            points: List[Point] = field(default_factory=list)

        result = pyrallis.parse(Config, args=["--points", '[{"x": 1.0, "y": 2.0}]'])
        assert result.points == [Point(1.0, 2.0)]

    def test_list_of_dataclass_via_cli_single_item(self):
        @dataclass
        class Config:
            people: List[Person] = field(default_factory=list)

        result = pyrallis.parse(Config, args=["--people", "[{name: Alice, age: 30}]"])
        assert result.people == [Person("Alice", 30)]

    def test_list_of_dataclass_via_cli_empty_list(self):
        @dataclass
        class Config:
            points: List[Point] = field(default_factory=list)

        result = pyrallis.parse(Config, args=["--points", "[]"])
        assert result.points == []

    def test_list_of_dataclass_via_cli_default_used_when_not_provided(self):
        @dataclass
        class Config:
            points: List[Point] = field(default_factory=list)
            name: str = "default"

        result = pyrallis.parse(Config, args=["--name", "test"])
        assert result.points == []
        assert result.name == "test"

    def test_list_of_dataclass_via_cli_mixed_with_plain_fields(self):
        @dataclass
        class Config:
            name: str = "default"
            count: int = 0
            points: List[Point] = field(default_factory=list)

        result = pyrallis.parse(Config, args=[
            "--name", "exp",
            "--count", "5",
            "--points", "[{x: 1.0, y: 2.0}]",
        ])
        assert result.name == "exp"
        assert result.count == 5
        assert result.points == [Point(1.0, 2.0)]

    def test_list_of_dataclass_via_cli_with_enum_field(self):
        @dataclass
        class Config:
            items: List[WithEnum] = field(default_factory=list)

        result = pyrallis.parse(Config, args=["--items", "[{color: red, intensity: 0.5}]"])
        assert result.items == [WithEnum(Color.red, 0.5)]

    def test_list_of_dataclass_via_cli_with_nested_list_field(self):
        @dataclass
        class Config:
            items: List[NestedInner] = field(default_factory=list)

        result = pyrallis.parse(Config, args=["--items", "[{label: a, scores: [1.0, 2.0]}]"])
        assert result.items == [NestedInner("a", [1.0, 2.0])]

    def test_list_of_dataclass_via_cli_overrides_config_file(self, tmp_path):
        @dataclass
        class Config:
            points: List[Point] = field(default_factory=list)

        cfg_file = Config(points=[Point(9.0, 9.0)])
        tmp_file = tmp_path / "config.yaml"
        pyrallis.dump(cfg_file, tmp_file.open("w"))

        result = pyrallis.parse(Config, args=[
            f"--config_path={tmp_file}",
            "--points", "[{x: 1.0, y: 2.0}]",
        ])
        assert result.points == [Point(1.0, 2.0)]

    def test_tuple_of_dataclasses_via_cli(self):
        @dataclass
        class Config:
            points: Tuple[Point, ...] = field(default_factory=tuple)

        result = pyrallis.parse(Config, args=["--points", "[{x: 1.0, y: 2.0}, {x: 3.0, y: 4.0}]"])
        assert result.points == (Point(1.0, 2.0), Point(3.0, 4.0))

    def test_list_of_dataclass_via_cli_many_items(self):
        @dataclass
        class Config:
            people: List[Person] = field(default_factory=list)

        people_yaml = "[" + ", ".join(f"{{name: person_{i}, age: {i}}}" for i in range(10)) + "]"
        result = pyrallis.parse(Config, args=["--people", people_yaml])
        assert result.people == [Person(f"person_{i}", i) for i in range(10)]


class TestCLIDictOfDataclasses:
    """Dict[str, Dataclass] fields can be set via CLI as a YAML/JSON string."""

    def test_dict_of_dataclass_via_cli_yaml_mapping(self):
        @dataclass
        class Config:
            mapping: Dict[str, Point] = field(default_factory=dict)

        result = pyrallis.parse(Config, args=[
            "--mapping", "{origin: {x: 0.0, y: 0.0}, target: {x: 1.0, y: 2.0}}"
        ])
        assert result.mapping == {"origin": Point(0.0, 0.0), "target": Point(1.0, 2.0)}

    def test_dict_of_dataclass_via_cli_json_string(self):
        @dataclass
        class Config:
            mapping: Dict[str, Point] = field(default_factory=dict)

        result = pyrallis.parse(Config, args=[
            "--mapping", '{"p": {"x": 1.0, "y": 2.0}}'
        ])
        assert result.mapping == {"p": Point(1.0, 2.0)}

    def test_dict_of_dataclass_via_cli_single_entry(self):
        @dataclass
        class Config:
            people: Dict[str, Person] = field(default_factory=dict)

        result = pyrallis.parse(Config, args=["--people", "{alice: {name: Alice, age: 30}}"])
        assert result.people == {"alice": Person("Alice", 30)}

    def test_dict_of_dataclass_via_cli_empty_dict(self):
        @dataclass
        class Config:
            mapping: Dict[str, Point] = field(default_factory=dict)

        result = pyrallis.parse(Config, args=["--mapping", "{}"])
        assert result.mapping == {}

    def test_dict_of_dataclass_via_cli_default_used_when_not_provided(self):
        @dataclass
        class Config:
            mapping: Dict[str, Point] = field(default_factory=dict)
            name: str = "default"

        result = pyrallis.parse(Config, args=["--name", "test"])
        assert result.mapping == {}
        assert result.name == "test"

    def test_dict_of_dataclass_via_cli_mixed_with_plain_fields(self):
        @dataclass
        class Config:
            name: str = "default"
            count: int = 0
            mapping: Dict[str, Point] = field(default_factory=dict)

        result = pyrallis.parse(Config, args=[
            "--name", "exp",
            "--count", "3",
            "--mapping", "{p: {x: 1.0, y: 2.0}}",
        ])
        assert result.name == "exp"
        assert result.count == 3
        assert result.mapping == {"p": Point(1.0, 2.0)}

    def test_dict_of_dataclass_via_cli_with_enum_field(self):
        @dataclass
        class Config:
            items: Dict[str, WithEnum] = field(default_factory=dict)

        result = pyrallis.parse(Config, args=["--items", "{warm: {color: red, intensity: 0.8}}"])
        assert result.items == {"warm": WithEnum(Color.red, 0.8)}

    def test_dict_of_dataclass_via_cli_overrides_config_file(self, tmp_path):
        @dataclass
        class Config:
            mapping: Dict[str, Point] = field(default_factory=dict)

        cfg_file = Config(mapping={"old": Point(9.0, 9.0)})
        tmp_file = tmp_path / "config.yaml"
        pyrallis.dump(cfg_file, tmp_file.open("w"))

        result = pyrallis.parse(Config, args=[
            f"--config_path={tmp_file}",
            "--mapping", "{new: {x: 1.0, y: 2.0}}",
        ])
        assert result.mapping == {"new": Point(1.0, 2.0)}

    def test_dict_of_dataclass_via_cli_with_nested_list_in_values(self):
        @dataclass
        class Config:
            mapping: Dict[str, NestedInner] = field(default_factory=dict)

        result = pyrallis.parse(Config, args=[
            "--mapping", "{item: {label: hello, scores: [1.0, 2.0]}}"
        ])
        assert result.mapping == {"item": NestedInner("hello", [1.0, 2.0])}


class TestCLIMixedContainers:
    """Combined CLI tests: both list and dict of dataclasses, alongside plain and nested fields."""

    def test_cli_both_list_and_dict(self):
        @dataclass
        class Config:
            points: List[Point] = field(default_factory=list)
            people: Dict[str, Person] = field(default_factory=dict)

        result = pyrallis.parse(Config, args=[
            "--points", "[{x: 1.0, y: 2.0}]",
            "--people", "{alice: {name: Alice, age: 30}}",
        ])
        assert result.points == [Point(1.0, 2.0)]
        assert result.people == {"alice": Person("Alice", 30)}

    def test_cli_list_alongside_nested_dataclass(self):
        @dataclass
        class Inner:
            value: int = 0

        @dataclass
        class Config:
            primary: Inner = field(default_factory=Inner)
            others: List[Inner] = field(default_factory=list)

        result = pyrallis.parse(Config, args=[
            "--primary.value", "42",
            "--others", "[{value: 1}, {value: 2}]",
        ])
        assert result.primary == Inner(42)
        assert result.others == [Inner(1), Inner(2)]

    def test_cli_dict_alongside_nested_dataclass(self):
        @dataclass
        class Inner:
            value: int = 0

        @dataclass
        class Config:
            primary: Inner = field(default_factory=Inner)
            named: Dict[str, Inner] = field(default_factory=dict)

        result = pyrallis.parse(Config, args=[
            "--primary.value", "10",
            "--named", "{a: {value: 1}, b: {value: 2}}",
        ])
        assert result.primary == Inner(10)
        assert result.named == {"a": Inner(1), "b": Inner(2)}

    def test_cli_container_fields_from_config_file_and_cli_override(self, tmp_path):
        """Config file sets list; CLI overrides dict; plain field comes from CLI."""

        @dataclass
        class Config:
            name: str = "default"
            points: List[Point] = field(default_factory=list)
            people: Dict[str, Person] = field(default_factory=dict)

        cfg_file = Config(
            name="from_file",
            points=[Point(9.0, 9.0)],
            people={"old": Person("Old", 99)},
        )
        tmp_file = tmp_path / "config.yaml"
        pyrallis.dump(cfg_file, tmp_file.open("w"))

        result = pyrallis.parse(Config, args=[
            f"--config_path={tmp_file}",
            "--name", "from_cli",
            "--people", "{alice: {name: Alice, age: 30}}",
        ])
        # CLI overrides name and people; points comes from file
        assert result.name == "from_cli"
        assert result.points == [Point(9.0, 9.0)]
        assert result.people == {"alice": Person("Alice", 30)}


class TestCLIDeeplyNestedContainers:
    """CLI tests for multiple levels of dataclass nesting inside containers."""

    def test_list_of_dataclass_containing_dict_of_dataclass(self):
        """List[DC] where each DC has a Dict[str, DC] field."""

        @dataclass
        class Team:
            name: str = ""
            positions: Dict[str, Point] = field(default_factory=dict)

        @dataclass
        class Config:
            teams: List[Team] = field(default_factory=list)

        result = pyrallis.parse(Config, args=[
            "--teams", "[{name: alpha, positions: {lead: {x: 1.0, y: 2.0}, support: {x: 3.0, y: 4.0}}}]"
        ])
        assert result.teams == [Team("alpha", {"lead": Point(1.0, 2.0), "support": Point(3.0, 4.0)})]

    def test_dict_of_dataclass_containing_list_of_dataclass(self):
        """Dict[str, DC] where each DC has a List[DC] field."""

        @dataclass
        class Group:
            label: str = ""
            points: List[Point] = field(default_factory=list)

        @dataclass
        class Config:
            groups: Dict[str, Group] = field(default_factory=dict)

        result = pyrallis.parse(Config, args=[
            "--groups", "{g1: {label: first, points: [{x: 1.0, y: 2.0}, {x: 3.0, y: 4.0}]}}"
        ])
        assert result.groups == {"g1": Group("first", [Point(1.0, 2.0), Point(3.0, 4.0)])}

    def test_list_of_dataclass_containing_list_of_dataclass(self):
        """List[DC] where each DC has a List[DC] field."""

        @dataclass
        class Cluster:
            center: Point = field(default_factory=Point)
            satellites: List[Point] = field(default_factory=list)

        @dataclass
        class Config:
            clusters: List[Cluster] = field(default_factory=list)

        result = pyrallis.parse(Config, args=[
            "--clusters", "[{center: {x: 0, y: 0}, satellites: [{x: 1, y: 1}, {x: 2, y: 2}]}]"
        ])
        assert result.clusters == [Cluster(Point(0, 0), [Point(1, 1), Point(2, 2)])]

    def test_dict_of_dataclass_containing_dict_of_dataclass(self):
        """Dict[str, DC] where each DC has a Dict[str, DC] field."""

        @dataclass
        class Registry:
            name: str = ""
            entries: Dict[str, Point] = field(default_factory=dict)

        @dataclass
        class Config:
            registries: Dict[str, Registry] = field(default_factory=dict)

        result = pyrallis.parse(Config, args=[
            "--registries", "{main: {name: primary, entries: {p1: {x: 1, y: 2}}}}"
        ])
        assert result.registries == {"main": Registry("primary", {"p1": Point(1, 2)})}

    def test_three_levels_deep(self):
        """DC -> Dict -> DC -> List -> DC."""

        @dataclass
        class Leaf:
            val: int = 0

        @dataclass
        class Branch:
            leaves: List[Leaf] = field(default_factory=list)

        @dataclass
        class Config:
            branches: Dict[str, Branch] = field(default_factory=dict)

        result = pyrallis.parse(Config, args=[
            "--branches", "{left: {leaves: [{val: 1}, {val: 2}]}, right: {leaves: [{val: 3}]}}"
        ])
        assert result.branches == {
            "left": Branch([Leaf(1), Leaf(2)]),
            "right": Branch([Leaf(3)]),
        }

    def test_multiple_nested_container_fields_in_same_config(self):
        """Config with multiple deeply nested container fields set via CLI simultaneously."""

        @dataclass
        class Member:
            name: str = ""
            scores: List[float] = field(default_factory=list)

        @dataclass
        class Config:
            teams: List[Member] = field(default_factory=list)
            leaders: Dict[str, Member] = field(default_factory=dict)

        result = pyrallis.parse(Config, args=[
            "--teams", "[{name: alice, scores: [9.5, 8.0]}, {name: bob, scores: [7.0]}]",
            "--leaders", "{alpha: {name: charlie, scores: [10.0]}}",
        ])
        assert result.teams == [Member("alice", [9.5, 8.0]), Member("bob", [7.0])]
        assert result.leaders == {"alpha": Member("charlie", [10.0])}
