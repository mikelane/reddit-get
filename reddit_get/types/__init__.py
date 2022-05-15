from typing import (
    Any,
    Dict,
    Iterator,
    List,
    Optional,
)

try:
    from typing import Protocol
except ImportError:  # pragma: no cover
    from typing_extensions import Protocol  # type: ignore

from .enums import *


class PrawQuery(Protocol):  # pragma: no cover
    def __call__(self, limit: Optional[int]) -> Iterator[Any]:
        ...


CallMap = Dict[SortingOption, PrawQuery]
Posts = List[str]
