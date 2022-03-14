from abc import get_cache_token
from dataclasses import dataclass
from functools import _find_impl, update_wrapper
from typing import Callable, Optional


@dataclass
class RegistryFunc:
    # The function saved in the registry
    func: Callable
    # Whether the function should be registered for subclasses as well
    include_subclasses: bool


def withregistry(base_func):
    import types, weakref

    registry = {}
    dispatch_cache = weakref.WeakKeyDictionary()
    cache_token = None

    def dispatch(cls) -> Optional[RegistryFunc]:
        nonlocal cache_token
        if cache_token is not None:
            current_token = get_cache_token()
            if cache_token != current_token:
                dispatch_cache.clear()
                cache_token = current_token
        if cls in dispatch_cache:
            impl = dispatch_cache[cls]
        else:
            if cls in registry:
                impl = registry[cls]
            else:
                try:
                    impl: Optional[RegistryFunc] = _find_impl(cls, registry)
                    if not impl.include_subclasses:
                        # Do not allow implicit inherited implementation without type
                        impl = None
                except Exception:
                    impl = None
            dispatch_cache[cls] = impl

        return impl

    def register(cls, func=None, include_subclasses=False):
        nonlocal cache_token
        if func is None:
            if isinstance(cls, type):
                return lambda f: register(cls, func=f, include_subclasses=include_subclasses)
            ann = getattr(cls, '__annotations__', {})
            if not ann:
                raise TypeError(
                    f"Invalid first argument to `register()`: {cls!r}. "
                    f"Use either `@register(some_class)` or plain `@register` "
                    f"on an annotated function."
                )
            func = cls

            # only import typing if annotation parsing is necessary
            from typing import get_type_hints
            argname, cls = next(iter(get_type_hints(func).items()))
            assert isinstance(cls, type), (
                f"Invalid annotation for {argname!r}. {cls!r} is not a class."
            )
        registry[cls] = RegistryFunc(func, include_subclasses)
        if cache_token is None and hasattr(cls, '__abstractmethods__'):
            cache_token = get_cache_token()
        dispatch_cache.clear()
        return func

    def wrapper(*args, **kw):
        # Unlike singledispatch we do not directly override the base call
        return base_func(*args, **kw)

    wrapper.register = register
    wrapper.dispatch = dispatch
    wrapper.registry = types.MappingProxyType(registry)
    wrapper._clear_cache = dispatch_cache.clear
    update_wrapper(wrapper, base_func)
    return wrapper
