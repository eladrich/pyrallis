"""Abstact Wrapper base-class for the FieldWrapper and DataclassWrapper."""

from abc import ABC, abstractmethod
from typing import Generic, Optional, List

from pyrallis.utils import T


class Wrapper(Generic[T], ABC):
    def __init__(self, wrapped: T, name: str):
        self.wrapped = wrapped
        self._dest: Optional[str] = None

    @property
    def dest(self) -> str:
        """Where the attribute will be stored in the Namespace."""
        if self.parent is None:
            return self.name
        lineage_names: List[str] = [w.name for w in self.lineage()]
        if lineage_names[-1] is None: # root usually won't have a name
            lineage_names = lineage_names[:-1]
        self._dest = ".".join(reversed([self.name] + lineage_names))
        return self._dest

    def lineage(self) -> List["Wrapper"]:
        lineage: List[Wrapper] = []
        parent = self.parent
        while parent is not None:
            lineage.append(parent)
            parent = parent.parent
        return lineage

    @property
    def nesting_level(self) -> int:
        return len(self.lineage())
        level = 0
        parent = self.parent
        while parent is not None:
            parent = parent.parent
            level += 1
        return level

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def parent(self) -> Optional["Wrapper"]:
        pass
