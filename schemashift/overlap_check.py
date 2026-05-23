"""Check field name overlaps between two schemas (case-insensitive collisions)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pyarrow as pa


@dataclass
class OverlapIssue:
    """A single case-insensitive name collision between two fields."""

    old_name: str
    new_name: str
    field_type: str

    @property
    def is_exact(self) -> bool:
        """True when the names differ only in case."""
        return self.old_name != self.new_name and self.old_name.lower() == self.new_name.lower()


@dataclass
class OverlapCheckResult:
    path_old: str
    path_new: str
    issues: List[OverlapIssue] = field(default_factory=list)


def has_overlaps(result: OverlapCheckResult) -> bool:
    return len(result.issues) > 0


def _type_str(t: pa.DataType) -> str:
    return str(t)


def check_overlaps(old: pa.Schema, new: pa.Schema, path_old: str, path_new: str) -> OverlapCheckResult:
    """Detect fields whose names collide case-insensitively across old and new schemas.

    A collision is reported when a field present in *old* maps (case-insensitively)
    to a field in *new* but the names are not byte-for-byte identical, suggesting
    a silent rename that could break case-sensitive consumers.
    """
    result = OverlapCheckResult(path_old=path_old, path_new=path_new)

    old_by_lower = {f.name.lower(): f for f in old}
    new_by_lower = {f.name.lower(): f for f in new}

    for lower_key, old_field in old_by_lower.items():
        if lower_key in new_by_lower:
            new_field = new_by_lower[lower_key]
            if old_field.name != new_field.name:
                result.issues.append(
                    OverlapIssue(
                        old_name=old_field.name,
                        new_name=new_field.name,
                        field_type=_type_str(old_field.type),
                    )
                )

    return result
