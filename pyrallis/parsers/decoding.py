""" Functions for decoding dataclass fields from "raw" values (e.g. from json).
"""
from collections import OrderedDict
from dataclasses import Field, MISSING, fields, is_dataclass
from functools import lru_cache, singledispatch
from functools import partial
from logging import getLogger
from typing import TypeVar, Any, Dict, Type, Callable, Optional, Union, List, Tuple, Set

import yaml

from pyrallis.utils import (
    get_type_arguments,
    is_dict,
    is_list,
    is_set,
    is_tuple,
    is_union,
    is_enum
)

logger = getLogger(__name__)

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")
Dataclass = TypeVar("Dataclass")


@singledispatch
def decode(t: Type[T], raw_value: Any) -> Any:
    return get_decoding_fn(t)(raw_value)


# Dictionary mapping from types/type annotations to their decoding functions.
for t in [str, float, int, bool, bytes]:
    decode.register(t, t)


def decode_dataclass(
        cls: Type[Dataclass], d: Dict[str, Any]) -> Dataclass:
    """Parses an instance of the dataclass `cls` from the dict `d`.

    Raises:
        RuntimeError: If an error is encountered while instantiating the class.

    Returns:
        Dataclass: An instance of the dataclass `cls`.
    """
    if d is None:
        return None
    obj_dict: Dict[str, Any] = d.copy()

    init_args: Dict[str, Any] = {}
    non_init_args: Dict[str, Any] = {}

    logger.debug(f"from_dict for {cls}")

    for field in fields(cls):
        name = field.name
        if name not in obj_dict:
            if field.default is MISSING and field.default_factory is MISSING:
                logger.warning(
                    f"Couldn't find the field '{name}' in the dict with keys "
                    f"{list(d.keys())}"
                )
            continue

        raw_value = obj_dict.pop(name)
        field_value = decode_field(field, raw_value)

        if field.init:
            init_args[name] = field_value
        else:
            non_init_args[name] = field_value

    extra_args = obj_dict

    # If there are arguments left over in the dict after taking all fields.
    if extra_args:
        raise Exception(f'The fields {extra_args} do not belong to the class')

    init_args.update(extra_args)
    try:
        instance = cls(**init_args)  # type: ignore
    except TypeError as e:
        # raise RuntimeError(f"Couldn't instantiate class {cls} using init args {init_args}.")
        raise RuntimeError(
            f"Couldn't instantiate class {cls} using init args {init_args.keys()}: {e}"
        )

    for name, value in non_init_args.items():
        logger.debug(f"Setting non-init field '{name}' on the instance.")
        setattr(instance, name, value)
    return instance


def decode_field(field: Field, raw_value: Any) -> Any:
    """Converts a "raw" value (e.g. from json file) to the type of the `field`.

    When serializing a dataclass to json, all objects are converted to dicts.
    The values which have a special type (not str, int, float, bool) are
    converted to string or dict. Hence this function allows us to recover the
    original type of pretty much any field which is of type `Serializable`, or
    has a registered decoding function (either through `register_decoding_fn` or
    through having `decoding_fn` passed directly to the `field` function.

    Args:
        field (Field): `Field` object from a dataclass.
        raw_value (Any): The `raw` value from deserializing the dataclass.

    Returns:
        Any: The "raw" value converted to the right type.
    """
    name = field.name
    field_type = field.type
    logger.debug(f"Decode name = {name}, type = {field_type}")
    return decode(field_type, raw_value)


@lru_cache(maxsize=100)
def get_decoding_fn(t: Type[T]) -> Callable[[Any], T]:
    """Fetches/Creates a decoding function for the given type annotation.

    This decoding function can then be used to create an instance of the type
    when deserializing dicts (which could have been obtained with JSON or YAML).

    This function inspects the type annotation and creates the right decoding
    function recursively in a "dynamic-programming-ish" fashion.
    NOTE: We cache the results in a `functools.lru_cache` decorator to avoid
    wasteful calls to the function. This makes this process pretty efficient.

    Args:
        t (Type[T]):
            A type or type annotation. Can be arbitrarily nested.
            For example:
            - List[int]
            - Dict[str, Foo]
            - Tuple[int, str, Any],
            - Dict[Tuple[int, int], List[str]]
            - List[List[List[List[Tuple[int, str]]]]]
            - etc.

    Returns:
        Callable[[Any], T]:
            A function that decodes a 'raw' value to an instance of type `t`.

    """
    if t in decode.registry:
        # The type has a dedicated decoding function.
        return decode.dispatch(t)  # This returns the singledispatch function

    elif is_dataclass(t):
        return partial(decode_dataclass, t)

    elif t is Any:
        logger.debug(f"Decoding an Any type: {t}")
        return no_op

    elif is_dict(t):
        logger.debug(f"Decoding a Dict field: {t}")
        args = get_type_arguments(t)
        if len(args) != 2:
            args = (Any, Any)
        return decode_dict(*args)

    elif is_set(t):
        logger.debug(f"Decoding a Set field: {t}")
        args = get_type_arguments(t)
        if len(args) != 1:
            args = (Any,)
        return decode_set(args[0])

    elif is_tuple(t):
        logger.debug(f"Decoding a Tuple field: {t}")
        args = get_type_arguments(t)
        return decode_tuple(*args)

    elif is_list(t):  # NOTE: Looks like can't be written with a dictionary
        logger.debug(f"Decoding a List field: {t}")
        args = get_type_arguments(t)
        if not args:
            # Using a `List` or `list` annotation, so we don't know what do decode the
            # items into!
            args = (Any,)
        assert len(args) == 1
        decode_fn = decode_list(args[0])

        return decode_fn

    elif is_union(t):
        logger.debug(f"Decoding a Union field: {t}")
        args = get_type_arguments(t)
        return decode_union(*args)

    elif is_enum(t):
        return t

    import typing_inspect as tpi

    if tpi.is_typevar(t):
        bound = tpi.get_bound(t)
        logger.debug(f"Decoding a typevar: {t}, bound type is {bound}.")
        if bound is not None:
            return get_decoding_fn(bound)

    raise Exception(f"No decoding function for type {t}, consider using pyrallis.decode.register")

    # Alternatively could have tried type as constructor, but could be have a surprising behaviour
    # return try_constructor(t)


def decode_optional(t: Type[T]) -> Callable[[Optional[Any]], Optional[T]]:
    decode = get_decoding_fn(t)

    def _decode_optional(val: Optional[Any]) -> Optional[T]:
        return val if val is None else decode(val)

    return _decode_optional


def try_functions(*funcs: Callable[[Any], T]) -> Callable[[Any], Union[T, Any]]:
    """Tries to use the functions in succession, else returns the same value unchanged."""

    def _try_functions(val: Any) -> Union[T, Any]:
        for func in funcs:
            try:
                return func(val)
            except Exception:
                continue
        # If no function worked, raise an exception
        raise TypeError(f"No valid parsing for value {val}")

    return _try_functions


def decode_union(*types: Type[T]) -> Callable[[Any], Union[T, Any]]:
    types = list(types)
    optional = type(None) in types
    # Partition the Union into None and non-None types.
    while type(None) in types:
        types.remove(type(None))

    decoding_fns: List[Callable[[Any], T]] = [
        decode_optional(t) if optional else get_decoding_fn(t) for t in types
    ]
    # Try using each of the non-None types, in succession. Worst case, return the value.
    return try_functions(*decoding_fns)


def decode_list(t: Type[T]) -> Callable[[List[Any]], List[T]]:
    decode_item = get_decoding_fn(t)

    def _decode_list(val: List[Any]) -> List[T]:
        assert type(val) == list
        return [decode_item(v) for v in val]

    return _decode_list


def decode_tuple(*tuple_item_types: Type[T]) -> Callable[[List[T]], Tuple[T, ...]]:
    """Makes a parsing function for creating tuples.

    Can handle tuples with different item types, for instance:
    - `Tuple[int, Foo, str, float, ...]`.

    Returns:
        Callable[[List[T]], Tuple[T, ...]]: A parsing function for creating tuples.
    """
    # Get the decoding function for each item type
    has_ellipsis = False
    if Ellipsis in tuple_item_types:
        # TODO: This isn't necessary, the ellipsis will always be at index 1.
        ellipsis_index = tuple_item_types.index(Ellipsis)
        decoding_fn_index = ellipsis_index - 1
        decoding_fn = get_decoding_fn(tuple_item_types[decoding_fn_index])
        has_ellipsis = True
    elif len(tuple_item_types) == 0:
        has_ellipsis = True
        decoding_fn = no_op  # Functionality will be the same as Tuple[Any,...]
    else:
        decoding_fns = [get_decoding_fn(t) for t in tuple_item_types]

    # Note, if there are more values than types in the tuple type, then the
    # last type is used.

    def _decode_tuple(val: Tuple[Any, ...]) -> Tuple[T, ...]:
        if has_ellipsis:
            return tuple(decoding_fn(v) for v in val)
        else:
            if len(decoding_fns) != len(val):
                err_msg = f'Trying to decode {len(val)} values for a predfined {len(decoding_fns)}-Tuple'
                raise TypeError(err_msg)
            return tuple(decoding_fns[i](v) for i, v in enumerate(val))

    return _decode_tuple


def decode_set(item_type: Type[T]) -> Callable[[List[T]], Set[T]]:
    """Makes a parsing function for creating sets with items of type `item_type`.

    Args:
        item_type (Type[T]): the type of the items in the set.

    Returns:
        Callable[[List[T]], Set[T]]: [description]
    """
    # Get the parsers fn for a list of items of type `item_type`.
    parse_list_fn = decode_list(item_type)

    def _decode_set(val: List[Any]) -> Set[T]:
        return set(parse_list_fn(val))

    return _decode_set


def decode_dict(
        K_: Type[K], V_: Type[V]
) -> Callable[[List[Tuple[Any, Any]]], Dict[K, V]]:
    """Creates a decoding function for a dict type. Works with OrderedDict too.

    Args:
        K_ (Type[K]): The type of the keys.
        V_ (Type[V]): The type of the values.

    Returns:
        Callable[[List[Tuple[Any, Any]]], Dict[K, V]]: A function that parses a
            Dict[K_, V_].
    """
    decode_k = get_decoding_fn(K_)
    decode_v = get_decoding_fn(V_)

    def _decode_dict(val: Union[Dict[Any, Any], List[Tuple[Any, Any]]]) -> Dict[K, V]:
        result: Dict[K, V] = {}
        if isinstance(val, list):
            result = OrderedDict()
            items = val
        elif isinstance(val, OrderedDict):
            # NOTE(ycho): Needed to propagate `OrderedDict` type
            result = OrderedDict()
            items = val.items()
        else:
            items = val.items()
        for k, v in items:
            k_ = decode_k(k)
            v_ = decode_v(v)
            result[k_] = v_
        return result

    return _decode_dict


def no_op(v: T) -> T:
    """Decoding function that gives back the value as-is.

    Args:
        v ([Any]): Any value.

    Returns:
        [type]: The value unchanged.
    """
    return v


def try_constructor(t: Type[T]) -> Callable[[Any], Union[T, Any]]:
    """Tries to use the type as a constructor. If that fails, returns the value as-is.

    Args:
        t (Type[T]): A type.

    Returns:
        Callable[[Any], Union[T, Any]]: A decoding function that might return nothing.
    """
    return try_functions(lambda val: t(**val), lambda val: t(val))


from pathlib import Path

decode.register(Path, Path)


def load(t: Type[Dataclass], stream, Loader=yaml.SafeLoader):
    dict = yaml.load(stream=stream, Loader=Loader)
    return decode(t, dict)
