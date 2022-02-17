"""Utility functions used in various parts of the pyrallis package."""
import argparse
import builtins
import collections.abc as c_abc
import dataclasses
import enum
import inspect
import logging
from collections import OrderedDict
from dataclasses import _MISSING_TYPE
from enum import Enum
from logging import getLogger
from typing import (
    Any,
    Callable,
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

K = TypeVar("K")
T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")
W = TypeVar("W")

Dataclass = TypeVar("Dataclass")
DataclassType = Type[Dataclass]

SimpleValueType = Union[bool, int, float, str]
SimpleIterable = Union[
    List[SimpleValueType], Dict[Any, SimpleValueType], Set[SimpleValueType]
]

TRUE_STRINGS: List[str] = ["yes", "true", "t", "y", "1"]
FALSE_STRINGS: List[str] = ["no", "false", "f", "n", "0"]


class PyrallisException(Exception):
    pass


class ParsingError(PyrallisException):
    pass


def str2bool(raw_value: Union[str, bool]) -> bool:
    """
    Taken from https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
    """
    if isinstance(raw_value, bool):
        return raw_value
    v = raw_value.strip().lower()
    if v in TRUE_STRINGS:
        return True
    elif v in FALSE_STRINGS:
        return False
    else:
        raise argparse.ArgumentTypeError(
            f"Boolean value expected for argument, received '{raw_value}'"
        )


def get_item_type(container_type: Type[Container[T]]) -> T:
    """Returns the `type` of the items in the provided container `type`.

    When no type annotation is found, or no item type is found, returns
    `typing.Any`.
    NOTE: If a type with multiple arguments is passed, only the first type
    argument is returned.

    >>> import typing
    >>> from typing import List, Tuple
    >>> get_item_type(list)
    typing.Any
    >>> get_item_type(List)
    typing.Any
    >>> get_item_type(tuple)
    typing.Any
    >>> get_item_type(Tuple)
    typing.Any
    >>> get_item_type(List[int])
    <class 'int'>
    >>> get_item_type(List[str])
    <class 'str'>
    >>> get_item_type(List[float])
    <class 'float'>
    >>> get_item_type(List[float])
    <class 'float'>
    >>> get_item_type(List[Tuple])
    typing.Tuple
    >>> get_item_type(List[Tuple[int, int]])
    typing.Tuple[int, int]
    >>> get_item_type(Tuple[int, str])
    <class 'int'>
    >>> get_item_type(Tuple[str, int])
    <class 'str'>
    >>> get_item_type(Tuple[str, str, str, str])
    <class 'str'>

    Arguments:
        list_type {Type} -- A type, preferably one from the Typing module (List, Tuple, etc).

    Returns:
        Type -- the type of the container's items, if found, else Any.
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


def get_argparse_type_for_container(
        container_type: Type,
) -> Union[Type, Callable[[str], bool]]:
    """Gets the argparse 'type' option to be used for a given container type.
    When an annotation is present, the 'type' option of argparse is set to that type.
    if not, then the default value of 'str' is returned.

    Arguments:
        container_type {Type} -- A container type (ideally a typing.Type such as List, Tuple, along with an item annotation: List[str], Tuple[int, int], etc.)

    Returns:
        typing.Type -- the type that should be used in argparse 'type' argument option.

    TODO: This overlaps in a weird way with `get_parsing_fn`, which returns the 'type'
    to use for a given annotation! This function however doesn't deal with 'weird' item
    types, it just returns the first annotation.
    """
    T = get_item_type(container_type)
    if T is bool:
        return str2bool
    if T is Any:
        return str
    return T


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
    """returns True when `t` is a List type.

    Args:
        t (Type): a type.

    Returns:
        bool: True if `t` is list or a subclass of list.

    >>> from typing import *
    >>> is_list(list)
    True
    >>> is_list(tuple)
    False
    >>> is_list(List)
    True
    >>> is_list(List[int])
    True
    >>> is_list(List[Tuple[int, str, None]])
    True
    >>> is_list(Optional[List[int]])
    False
    >>> class foo(List[int]):
    ...   pass
    ...
    >>> is_list(foo)
    True
    """
    return list in _mro(t)


def is_tuple(t: Type) -> bool:
    """returns True when `t` is a tuple type.

    Args:
        t (Type): a type.

    Returns:
        bool: True if `t` is tuple or a subclass of tuple.

    >>> from typing import *
    >>> is_tuple(list)
    False
    >>> is_tuple(tuple)
    True
    >>> is_tuple(Tuple)
    True
    >>> is_tuple(Tuple[int])
    True
    >>> is_tuple(Tuple[int, str, None])
    True
    >>> class foo(tuple):
    ...   pass
    ...
    >>> is_tuple(foo)
    True
    >>> is_tuple(List[int])
    False
    """
    return tuple in _mro(t)


def is_dict(t: Type) -> bool:
    """returns True when `t` is a dict type or annotation.

    Args:
        t (Type): a type.

    Returns:
        bool: True if `t` is dict or a subclass of dict.

    >>> from typing import *
    >>> from collections import OrderedDict
    >>> is_dict(dict)
    True
    >>> is_dict(OrderedDict)
    True
    >>> is_dict(tuple)
    False
    >>> is_dict(Dict)
    True
    >>> is_dict(Dict[int, float])
    True
    >>> is_dict(Dict[Any, Dict])
    True
    >>> is_dict(Optional[Dict])
    False
    >>> is_dict(Mapping[str, int])
    True
    >>> class foo(Dict):
    ...   pass
    ...
    >>> is_dict(foo)
    True
    """
    mro = _mro(t)
    return dict in mro or Mapping in mro or c_abc.Mapping in mro


def is_set(t: Type) -> bool:
    """returns True when `t` is a set type or annotation.

    Args:
        t (Type): a type.

    Returns:
        bool: True if `t` is set or a subclass of set.

    >>> from typing import *
    >>> is_set(set)
    True
    >>> is_set(Set)
    True
    >>> is_set(tuple)
    False
    >>> is_set(Dict)
    False
    >>> is_set(Set[int])
    True
    >>> is_set(Set["something"])
    True
    >>> is_set(Optional[Set])
    False
    >>> class foo(Set):
    ...   pass
    ...
    >>> is_set(foo)
    True
    """
    mro = _mro(t)
    return set in _mro(t)


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
    """Returns wether or not the given Type annotation is a variant (or subclass) of typing.Union

    Args:
        t (Type): some type annotation

    Returns:
        bool: Wether this type represents a Union type.

    >>> from typing import *
    >>> is_union(Union[int, str])
    True
    >>> is_union(Union[int, str, float])
    True
    >>> is_union(Tuple[int, str])
    False
    """
    return getattr(t, "__origin__", "") == Union


def is_homogeneous_tuple_type(t: Type[Tuple]) -> bool:
    """Returns wether the given Tuple type is homogeneous: if all items types are the
    same.

    This also includes Tuple[<some_type>, ...]

    Returns
    -------
    bool

    >>> from typing import *
    >>> is_homogeneous_tuple_type(Tuple)
    True
    >>> is_homogeneous_tuple_type(Tuple[int, int])
    True
    >>> is_homogeneous_tuple_type(Tuple[int, str])
    False
    >>> is_homogeneous_tuple_type(Tuple[int, str, float])
    False
    >>> is_homogeneous_tuple_type(Tuple[int, ...])
    True
    >>> is_homogeneous_tuple_type(Tuple[Tuple[int, str], ...])
    True
    >>> is_homogeneous_tuple_type(Tuple[List[int], List[str]])
    False
    """
    if not is_tuple(t):
        return False
    type_arguments = get_type_arguments(t)
    if not type_arguments:
        return True
    assert isinstance(type_arguments, tuple), type_arguments
    if len(type_arguments) == 2 and type_arguments[1] is Ellipsis:
        return True
    # Tuple[str, str, str] -> True
    # Tuple[str, str, float] -> False
    # TODO: Not sure if this will work with more complex item times (like nested tuples)
    return len(set(type_arguments)) == 1


def is_optional(t: Type) -> bool:
    """Returns True if the given Type is a variant of the Optional type.

    Parameters
    ----------
    - t : Type

        a Type annotation (or "live" type)

    Returns
    -------
    bool
        Wether or not this is an Optional.

    >>> from typing import Union, Optional, List
    >>> is_optional(str)
    False
    >>> is_optional(Optional[str])
    True
    >>> is_optional(Union[str, None])
    True
    >>> is_optional(Union[str, List])
    False
    >>> is_optional(Union[str, List, int, float, None])
    True
    """
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
    """Removes all the keys in `d` that aren't in `keys`.

    Parameters
    ----------
    d : Dict
        Some dictionary.
    keys_to_keep : Iterable[str]
        The set of keys to keep

    Returns
    -------
    Tuple[Dict, Dict]
        The same dictionary (with all the unwanted keys removed) as well as a
        new dict containing only the removed item.

    """
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
