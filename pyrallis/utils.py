"""Utility functions used in various parts of the pyrallis package."""
import builtins
import collections.abc as c_abc
import dataclasses
import enum
import inspect
import logging
from dataclasses import _MISSING_TYPE
from enum import Enum
from logging import getLogger
from typing import (
    Any,
    Container,
    Dict,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import typing_inspect as tpi


try:
    from typing import get_args
except ImportError:
    def get_args(some_type: Type) -> Tuple[Type, ...]:
        return getattr(some_type, "__args__", ())

try:
    from typing import get_origin
except ImportError:
    from typing_inspect import get_origin

logger = getLogger(__name__)

builtin_types = [
    getattr(builtins, d)
    for d in dir(builtins)
    if isinstance(getattr(builtins, d), type)
]

T = TypeVar("T")

Dataclass = TypeVar("Dataclass")
DataclassType = Type[Dataclass]


class PyrallisException(Exception):
    pass


class ParsingError(PyrallisException):
    pass


def get_item_type(container_type: Type[Container[T]]) -> T:
    """Returns the `type` of the items in the provided container `type`.

    When no type annotation is found, or no item type is found, returns
    `typing.Any`.
    NOTE: If a type with multiple arguments is passed, only the first type
    argument is returned.
    """
    if container_type in {
        list,
        set,
        tuple,
        List,
        Set,
        Tuple,
        Dict,
        Mapping,
        MutableMapping,
    }:
        # the built-in `list` and `tuple` types don't have annotations for their item types.
        return Any
    type_arguments = getattr(container_type, "__args__", None)
    if type_arguments:
        return type_arguments[0]
    else:
        return Any


def _mro(t: Type) -> List[Type]:
    # TODO: This is mostly used in 'is_tuple' and such, and should be replaced with
    # either the build-in 'get_origin' from typing, or from typing-inspect.
    if t is None:
        return []
    if hasattr(t, "__mro__"):
        return t.__mro__
    elif tpi.get_origin(t) is type:
        return []
    elif hasattr(t, "mro") and callable(t.mro):
        return t.mro()
    return []


def is_list(t: Type) -> bool:
    return list in _mro(t)


def is_tuple(t: Type) -> bool:
    return tuple in _mro(t)


def is_dict(t: Type) -> bool:
    mro = _mro(t)
    return dict in mro or Mapping in mro or c_abc.Mapping in mro


def is_set(t: Type) -> bool:
    mro = _mro(t)
    return set in mro


def is_dataclass_type(t: Type) -> bool:
    """Returns wether t is a dataclass type or a TypeVar of a dataclass type.

    Args:
        t (Type): Some type.

    Returns:
        bool: Wether its a dataclass type.
    """
    return dataclasses.is_dataclass(t) or (
            tpi.is_typevar(t) and dataclasses.is_dataclass(tpi.get_bound(t))
    )


def is_enum(t: Type) -> bool:
    if inspect.isclass(t):
        return issubclass(t, enum.Enum)
    return Enum in _mro(t)


def is_bool(t: Type) -> bool:
    return bool in _mro(t)


def is_tuple_or_list(t: Type) -> bool:
    return is_list(t) or is_tuple(t)


def is_union(t: Type) -> bool:
    return getattr(t, "__origin__", "") == Union


def is_homogeneous_tuple_type(t: Type[Tuple]) -> bool:
    if not is_tuple(t):
        return False
    type_arguments = get_type_arguments(t)
    if not type_arguments:
        return True
    assert isinstance(type_arguments, tuple), type_arguments
    if len(type_arguments) == 2 and type_arguments[1] is Ellipsis:
        return True
    # TODO: Not sure if this will work with more complex item times (like nested tuples)
    return len(set(type_arguments)) == 1


def is_optional(t: Type) -> bool:
    return is_union(t) and type(None) in get_type_arguments(t)


def is_tuple_or_list_of_dataclasses(t: Type) -> bool:
    return is_tuple_or_list(t) and is_dataclass_type(get_item_type(t))


def contains_dataclass_type_arg(t: Type) -> bool:
    if is_dataclass_type(t):
        return True
    elif is_tuple_or_list_of_dataclasses(t):
        return True
    elif is_union(t):
        return any(contains_dataclass_type_arg(arg) for arg in get_type_arguments(t))
    return False


def get_dataclass_type_arg(t: Type) -> Optional[Type]:
    if not contains_dataclass_type_arg(t):
        return None
    if is_dataclass_type(t):
        return t
    elif is_tuple_or_list(t) or is_union(t):
        return next(
            filter(
                None, (get_dataclass_type_arg(arg) for arg in get_type_arguments(t))
            ),
            None,
        )
    return None


def get_type_arguments(container_type: Type) -> Tuple[Type, ...]:
    # return getattr(container_type, "__args__", ())
    return get_args(container_type)


def get_type_name(some_type: Type):
    result = getattr(some_type, "__name__", str(some_type))
    type_arguments = get_type_arguments(some_type)
    if type_arguments:
        result += f"[{','.join(get_type_name(T) for T in type_arguments)}]"
    return result


def default_value(field: dataclasses.Field) -> Union[T, _MISSING_TYPE]:
    """Returns the default value of a field in a dataclass, if available.
    When not available, returns `dataclasses.MISSING`.

    Args:
        field (dataclasses.Field): The dataclasses.Field to get the default value of.

    Returns:
        Union[T, _MISSING_TYPE]: The default value for that field, if present, or None otherwise.
    """
    if field.default is not dataclasses.MISSING:
        return field.default
    elif field.default_factory is not dataclasses.MISSING:  # type: ignore
        constructor = field.default_factory  # type: ignore
        return constructor()
    else:
        return dataclasses.MISSING


def get_defaults_dict(c: Dataclass):
    """" Get defaults of a dataclass without generating the object """
    defaults_dict = {}
    for field in dataclasses.fields(c):
        if is_dataclass_type(field.type):
            defaults_dict[field.name] = get_defaults_dict(field.type)
        else:
            if field.default is not dataclasses.MISSING:
                defaults_dict[field.name] = field.default
            elif field.default_factory is not dataclasses.MISSING:
                try:
                    defaults_dict[field.name] = field.default_factory()
                except Exception as e:
                    logging.debug(
                        f"Failed getting default for field {field.name} using its default factory.\n\tUnderlying error: {e}")
                    continue
    return defaults_dict


def keep_keys(d: Dict, keys_to_keep: Iterable[str]) -> Tuple[Dict, Dict]:
    d_keys = set(d.keys())  # save a copy since we will modify the dict.
    removed = {}
    for key in d_keys:
        if key not in keys_to_keep:
            removed[key] = d.pop(key)
    return d, removed


def flatten(d, parent_key=None, sep='.'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, c_abc.MutableMapping):
            items.extend(flatten(v, parent_key=new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def deflatten(d: Dict[str, Any], sep: str = '.'):
    deflat_d = {}
    for key in d:
        key_parts = key.split(sep)
        curr_d = deflat_d
        for inner_key in key_parts[:-1]:
            if not inner_key in curr_d:
                curr_d[inner_key] = {}
            curr_d = curr_d[inner_key]
        curr_d[key_parts[-1]] = d[key]
    return deflat_d


def remove_matching(dict_a, dict_b):
    dict_a = flatten(dict_a)
    dict_b = flatten(dict_b)
    for key in dict_b:
        if key in dict_a and dict_b[key] == dict_a[key]:
            del dict_a[key]
    return deflatten(dict_a)


def format_error(e: Exception):
    try:
        return f'{type(e).__name__}: {e}'
    except Exception:
        return f'Exception: {e}'


def is_generic_arg(arg):
    try:
        return arg.__name__ in ['KT', 'VT', 'T']
    except Exception:
        return False


def has_generic_arg(args):
    for arg in args:
        if is_generic_arg(arg):
            return True
    return False


CONFIG_ARG = 'config_path'

if __name__ == "__main__":
    import doctest

    doctest.testmod()
