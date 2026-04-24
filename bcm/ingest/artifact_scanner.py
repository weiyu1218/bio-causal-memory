from __future__ import annotations

from typing import Iterable, Set


def diff_files(files_before: Iterable[str], files_after: Iterable[str]) -> Set[str]:
    return set(files_after) - set(files_before)
