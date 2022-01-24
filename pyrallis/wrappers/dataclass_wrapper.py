import argparse
import dataclasses
from dataclasses import _MISSING_TYPE
from logging import getLogger
from typing import Dict, List, Optional, Type, Union, cast

from pyrallis.utils import Dataclass
from . import docstring
from .field_wrapper import FieldWrapper
from .wrapper import Wrapper
from .. import utils

logger = getLogger(__name__)


class DataclassWrapper(Wrapper[Dataclass]):
    def __init__(
            self,
            dataclass: Type[Dataclass],
            name: Optional[str] = None,
            default: Union[Dataclass, Dict] = None,
            prefix: str = "",
            parent: "DataclassWrapper" = None,
            _field: dataclasses.Field = None,
            field_wrapper_class: Type[FieldWrapper] = FieldWrapper
    ):
        # super().__init__(dataclass, name)
        self.dataclass = dataclass
        self._name = name
        self.default = default
        self.prefix = prefix

        self.fields: List[FieldWrapper] = []
        self._required: bool = False
        self._explicit: bool = False
        self._dest: str = ""
        self._children: List[DataclassWrapper] = []
        self._parent = parent
        # the field of the parent, which contains this child dataclass.
        self._field = _field

        # the default values
        self._defaults: List[Dataclass] = []

        if default:
            self.defaults = [default]

        self.optional: bool = False

        for field in dataclasses.fields(self.dataclass):
            if not field.init:
                continue

            elif utils.is_tuple_or_list_of_dataclasses(field.type):
                raise NotImplementedError(
                    f"Field {field.name} is of type {field.type}, which isn't "
                    f"supported yet. (container of a dataclass type)"
                )

            elif dataclasses.is_dataclass(field.type):
                # handle a nested dataclass attribute
                dataclass, name = field.type, field.name
                child_wrapper = DataclassWrapper(
                    dataclass, name, parent=self, _field=field
                )
                self._children.append(child_wrapper)

            elif utils.contains_dataclass_type_arg(field.type):
                dataclass = utils.get_dataclass_type_arg(field.type)
                name = field.name
                child_wrapper = DataclassWrapper(
                    dataclass, name, parent=self, _field=field, default=None
                )
                child_wrapper.required = False
                child_wrapper.optional = True
                self._children.append(child_wrapper)

            else:
                # a normal attribute
                field_wrapper = field_wrapper_class(field, parent=self, prefix=self.prefix)
                logger.debug(
                    f"wrapped field at {field_wrapper.dest} has a default value of {field_wrapper.default}"
                )
                self.fields.append(field_wrapper)

        logger.debug(
            f"The dataclass at attribute {self.dest} has default values: {self.defaults}"
        )

    def add_arguments(self, parser: argparse.ArgumentParser):
        from pyrallis.argparsing import ArgumentParser

        parser = cast(ArgumentParser, parser)
        option_fields = [field for field in self.fields if field.arg_options]

        if len(option_fields) > 0:
            # Only show groups with parameters
            group = parser.add_argument_group(
                title=self.title, description=self.description
            )
            for wrapped_field in option_fields:
                logger.debug(
                    f"Arg options for field '{wrapped_field.name}': {wrapped_field.arg_options}"
                )
                group.add_argument(
                    *wrapped_field.option_strings, **wrapped_field.arg_options
                )

    @property
    def name(self) -> str:
        return self._name

    @property
    def parent(self) -> Optional["DataclassWrapper"]:
        return self._parent

    @property
    def defaults(self) -> List[Dataclass]:
        if self._defaults:
            return self._defaults
        if self._field is None:
            return []
        assert self.parent is not None
        if self.parent.defaults:
            self._defaults = []
            for default in self.parent.defaults:
                if default is None:
                    default = None
                else:
                    default = getattr(default, self.name)
                self._defaults.append(default)
        else:
            try:
                default_field_value = utils.default_value(self._field)
            except TypeError as e:
                # utils.default_value tries to construct the field to get default value and might fail
                # if the field has some required arguments
                logger.debug(
                    f"Could not get default value for field '{self._field.name}'\n\tUnderlying Error: {e}")
                default_field_value = dataclasses.MISSING
            if isinstance(default_field_value, _MISSING_TYPE):
                self._defaults = []
            else:
                self._defaults = [default_field_value]
        return self._defaults

    @defaults.setter
    def defaults(self, value: List[Dataclass]):
        self._defaults = value

    @property
    def title(self) -> str:
        title = self.dataclass.__qualname__
        if self.dest is not None:  # Show name if exists
            title += f" ['{self.dest}']"
        return title

    @property
    def description(self) -> str:
        if self.parent and self._field:
            doc = docstring.get_attribute_docstring(
                self.parent.dataclass, self._field.name
            )
            if doc is not None:
                if doc.docstring_below:
                    return doc.docstring_below
                elif doc.comment_above:
                    return doc.comment_above
                elif doc.comment_inline:
                    return doc.comment_inline
        class_doc = self.dataclass.__doc__ or ""
        if class_doc.startswith(f'{self.dataclass.__name__}('):
            return ""  # The base dataclass doc looks confusing, remove it
        return class_doc

    @property
    def required(self) -> bool:
        return self._required

    @required.setter
    def required(self, value: bool):
        self._required = value
        for field in self.fields:
            field.required = value
        for child_wrapper in self._children:
            child_wrapper.required = value

    @property
    def descendants(self):
        for child in self._children:
            yield child
            yield from child.descendants
