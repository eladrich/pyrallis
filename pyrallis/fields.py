import dataclasses


def field(*, default=dataclasses.MISSING, default_factory=dataclasses.MISSING, init=True, repr=True,
          hash=None, compare=True, metadata=None, is_mutable=False):
    if default is not dataclasses.MISSING and default_factory is not dataclasses.MISSING:
        raise ValueError('cannot specify both default and default_factory')
    if is_mutable and default is not dataclasses.MISSING:
        from copy import deepcopy
        copy_val = default
        default_factory = lambda: deepcopy(copy_val)
        default = dataclasses.MISSING
    return dataclasses.field(default=default, default_factory=default_factory,
                             init=init, repr=repr, hash=hash,
                             compare=compare, metadata=metadata)
