"""Simple, Elegant Argument parsing.
@author: Fabrice Normandin
"""
import argparse
import inspect
import sys
import warnings
from argparse import HelpFormatter, Namespace
from collections import defaultdict
from functools import wraps
from logging import getLogger
from typing import Dict, List, Sequence, Text, Type, Union, TypeVar, Generic, Optional

import yaml

from pyrallis import utils
from pyrallis.parsers import decoding
from pyrallis.help_formatter import SimpleHelpFormatter
from pyrallis.utils import Dataclass
from pyrallis.wrappers import DataclassWrapper

logger = getLogger(__name__)


T = TypeVar('T')


class ArgumentParser(Generic[T], argparse.ArgumentParser):
    def __init__(
            self,
            config_class: Type[T],
            config_path: Optional[str] = None,
            formatter_class: Type[HelpFormatter] = SimpleHelpFormatter,
            *args,
            **kwargs,
    ):
        """ Creates an ArgumentParser instance. """
        kwargs["formatter_class"] = formatter_class
        super().__init__(*args, **kwargs)

        # constructor arguments for the dataclass instances.
        # (a Dict[dest, [attribute, value]])
        self.constructor_arguments: Dict[str, Dict] = defaultdict(dict)

        self._wrappers: List[DataclassWrapper] = []

        self._preprocessing_done: bool = False
        self.config_path = config_path
        self.config_class = config_class
        self.add_argument('--CONFIG', type=str, help='Path for a config file to parsers with pyrallis')
        self.add_arguments(config_class, dest=utils.BASE_KEY)

    def add_arguments(
            self,
            dataclass: Union[Type[Dataclass], Dataclass],
            dest: str,
            prefix: str = "",
            default: Union[Dataclass, Dict] = None,
            dataclass_wrapper_class: Type[DataclassWrapper] = DataclassWrapper,
    ):
        """ Adds command-line arguments for the fields of `dataclass`. """
        for wrapper in self._wrappers:
            if wrapper.dest == dest:
                raise argparse.ArgumentError(
                    argument=None,
                    message=f"Destination attribute {dest} is already used for "
                            f"dataclass of type {dataclass}. Make sure all destinations"
                            f" are unique.",
                )
        if not isinstance(dataclass, type):
            default = dataclass if default is None else default
            dataclass = type(dataclass)

        new_wrapper = dataclass_wrapper_class(dataclass, dest, prefix=prefix, default=default)
        self._wrappers.append(new_wrapper)

    def parse_args(self, args=None, namespace=None) -> T:
        return super().parse_args(args, namespace)

    def parse_known_args(
            self,
            args: Sequence[Text] = None,
            namespace: Namespace = None,
            attempt_to_reorder: bool = False,
    ):
        # NOTE: since the usual ArgumentParser.parse_args() calls
        # parse_known_args, we therefore just need to overload the
        # parse_known_args method to support both.
        if args is None:
            # args default to the system args
            args = sys.argv[1:]
        else:
            # make sure that args are mutable
            args = list(args)
        self._preprocessing()

        if '--help' not in args:
            for action in self._actions:
                action.default = argparse.SUPPRESS  # To avoid setting of defaults in actual run
                action.type = str  # In practice we want all processing to happen with yaml
        parsed_args, unparsed_args = super().parse_known_args(args, namespace)

        parsed_args = self._postprocessing(parsed_args)
        return parsed_args, unparsed_args

    def print_help(self, file=None):
        self._preprocessing()
        return super().print_help(file)

    def _add_descendants(self) -> None:
        descendant_wrappers = []
        for wrapper in self._wrappers:
            descendant_wrappers.extend(wrapper.descendants)
        self._wrappers += descendant_wrappers

    def _preprocessing(self) -> None:
        """ Add all the arguments."""
        logger.debug("\nPREPROCESSING\n")
        if self._preprocessing_done:
            return

        self._add_descendants()

        # Create one argument group per dataclass
        for wrapper in self._wrappers:
            logger.debug(
                f"Adding arguments for dataclass: {wrapper.dataclass} "
                f"at destinations {wrapper.destinations}"
            )
            wrapper.add_arguments(parser=self)
        self._preprocessing_done = True

    def _postprocessing(self, parsed_args: Namespace) -> T:
        logger.debug("\nPOST PROCESSING\n")
        logger.debug(f"(raw) parsed args: {parsed_args}")

        parsed_arg_values = vars(parsed_args)

        for key in parsed_arg_values:
            parsed_arg_values[key] = yaml.safe_load(parsed_arg_values[key])

        config_path = self.config_path  # Could be NONE

        if 'CONFIG' in parsed_arg_values:
            new_config_path = parsed_arg_values['CONFIG']
            if config_path is not None:
                warnings.warn(
                    UserWarning(f'Overriding default {config_path} with {new_config_path}')
                )
            config_path = new_config_path
            del parsed_arg_values['CONFIG']

        if config_path is not None:
            yaml_args = yaml.full_load(open(config_path, 'r'))
            yaml_args = utils.flatten(yaml_args, parent_key=utils.BASE_KEY, sep='.')
            yaml_args.update(parsed_arg_values)
            parsed_arg_values = yaml_args

        deflat_d = utils.deflatten(parsed_arg_values, parent_key=utils.BASE_KEY, sep='.')
        cfg = decoding.decode(self.config_class, deflat_d)

        return cfg


def wrap(config_path=None):
    def wrapper_outer(fn):
        @wraps(fn)
        def wrapper_inner(*args, **kwargs):
            argspec = inspect.getfullargspec(fn)
            argtype = argspec.annotations[argspec.args[0]]
            cfg = ArgumentParser(config_class=argtype, config_path=config_path).parse_args()
            response = fn(cfg, *args, **kwargs)
            return response

        return wrapper_inner

    return wrapper_outer
