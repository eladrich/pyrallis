import shlex
import shlex
import string
import sys
from contextlib import contextmanager, suppress
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    cast,
)

import pytest
import pyrallis
from pyrallis import (
    ArgumentParser,
    ParsingError,
    SimpleHelpFormatter,
)
from pyrallis.wrappers import DataclassWrapper


xfail = pytest.mark.xfail
parametrize = pytest.mark.parametrize


def xfail_param(*args, reason: str):
    if len(args) == 1 and isinstance(args[0], tuple):
        args = args[0]
    return pytest.param(*args, marks=pytest.mark.xfail(reason=reason))


Dataclass = TypeVar("Dataclass")


@contextmanager
def raises(exception=ParsingError, match=None, code: int = None):
    with pytest.raises(exception, match=match):
        yield


from io import StringIO
from contextlib import redirect_stderr


@contextmanager
def exits_and_writes_to_stderr(match: str = ""):
    s = StringIO()
    with redirect_stderr(s), raises(SystemExit):
        yield
    s.seek(0)
    err_string = s.read()
    if match:
        assert match in err_string, err_string
    else:
        assert err_string, err_string


@contextmanager
def raises_missing_required_arg():
    with exits_and_writes_to_stderr("the following arguments are required"):
        yield


@contextmanager
def raises_expected_n_args(n: int):
    with exits_and_writes_to_stderr(f"expected {n} arguments"):
        yield


@contextmanager
def raises_unrecognized_args(*args: str):
    with exits_and_writes_to_stderr(f"unrecognized arguments: " + " ".join(args or [])):
        yield


def assert_help_output_equals(actual: str, expected: str) -> bool:
    # Replace the start with `prog`, since the tests runner might not always be
    # `pytest`, could also be __main__ when debugging with VSCode
    prog = sys.argv[0].split("/")[-1]
    if prog != "pytest":
        expected = expected.replace("usage: pytest", f"usage: {prog}")
    remove = string.punctuation + string.whitespace
    actual_str = "".join(actual.split())
    expected_str = "".join(expected.split())
    assert actual_str == expected_str, f"{actual_str} != {expected_str}"


T = TypeVar("T")


class TestParser(pyrallis.ArgumentParser, Generic[T]):
    __test__ = False
    """ A parser subclass just used for testing.
    Makes the retrieval of the arguments a bit easier to read.
    """

    def __init__(self, *args, **kwargs):
        self._current_dest = None
        self._current_dataclass = None
        super().__init__(*args, **kwargs)

    def add_arguments(self, dataclass: Type, dest, prefix="", default=None):
        if self._current_dest == dest and self._current_dataclass == dataclass:
            return  # already added arguments for that dataclass.
        self._current_dest = dest
        self._current_dataclass = dataclass
        return super().add_arguments(dataclass, dest, prefix=prefix, default=default)

    def __call__(self, args: str) -> T:
        namespace = self.parse_args(shlex.split(args))
        value = getattr(namespace, self._current_dest)
        value = cast(T, value)
        return value


class TestSetup:
    @classmethod
    def setup(
            cls: Type[Dataclass],
            arguments: Optional[str] = "",
            dest: Optional[str] = None,
            default: Optional[Dataclass] = None,
            parse_known_args: bool = False,
            attempt_to_reorder: bool = False,
    ) -> Dataclass:
        """Basic setup for a tests.

        Keyword Arguments:
            arguments {Optional[str]} -- The arguments to pass to the parser (default: {""})
            dest {Optional[str]} -- the attribute where the argument should be stored. (default: {None})

        Returns:
            {cls}} -- the class's type.
        """
        parser = pyrallis.ArgumentParser(config_class=cls)

        if arguments is None:
            if parse_known_args:
                args = parser.parse_known_args(attempt_to_reorder=attempt_to_reorder)
            else:
                args = parser.parse_args()
        else:
            splits = shlex.split(arguments)
            if parse_known_args:
                args, unknown_args = parser.parse_known_args(
                    splits, attempt_to_reorder=attempt_to_reorder
                )
            else:
                args = parser.parse_args(splits)
        return args

    @classmethod
    def get_help_text(
            cls,
            multiple=False,
    ) -> str:
        import contextlib
        from io import StringIO

        f = StringIO()
        with contextlib.suppress(SystemExit), contextlib.redirect_stdout(f):
            _ = cls.setup(
                "--help",
            )
        s = f.getvalue()
        return s


ListFormattingFunction = Callable[[List[Any]], str]
ListOfListsFormattingFunction = Callable[[List[List[Any]]], str]


def format_list_using_spaces(value_list: List[Any]) -> str:
    return " ".join(str(p) for p in value_list)


def format_list_using_brackets(value_list: List[Any]) -> str:
    return f"[{','.join(str(p) for p in value_list)}]"


def format_list_using_single_quotes(value_list: List[Any]) -> str:
    return f"'{format_list_using_spaces(value_list)}'"


def format_list_using_double_quotes(value_list: List[Any]) -> str:
    return f'"{format_list_using_spaces(value_list)}"'


def format_lists_using_brackets(list_of_lists: List[List[Any]]) -> str:
    return " ".join(
        format_list_using_brackets(value_list) for value_list in list_of_lists
    )


def format_lists_using_double_quotes(list_of_lists: List[List[Any]]) -> str:
    return " ".join(
        format_list_using_double_quotes(value_list) for value_list in list_of_lists
    )


def format_lists_using_single_quotes(list_of_lists: List[List[Any]]) -> str:
    return " ".join(
        format_list_using_single_quotes(value_list) for value_list in list_of_lists
    )
