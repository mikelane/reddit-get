from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Optional,
)

try:
    from typing import Protocol
except ImportError:  # pragma: no cover
    from typing import Protocol  # type: ignore

from .enums import *

if TYPE_CHECKING:
    from collections.abc import Iterator


class PrawQuery(Protocol):  # pragma: no cover
    def __call__(self, limit: int | None) -> Iterator[Any]:
        ...


CallMap = dict[SortingOption, PrawQuery]
Posts = list[str]
