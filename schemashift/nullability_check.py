"""Check for nullability changes between two schemas."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List

import pyarrow as pa


class NullabilityChange(str, Enum):
    BECAME_NULLABLE = "became_nullable"
    BECAME_NON_NULLABLE = "became_non_nullable"


@dataclass(frozen=True)
class NullabilityIssue:
    field_name: str
    change: NullabilityChange

    @property
    def is_breaking(self) -> bool:
        """Becoming non-nullable is a breaking change for existing writers."""
        return self.change == NullabilityChange.BECAME_NON_NULLABLE


@dataclass
class NullabilityCheckResult:
    path: str
    issues: List[NullabilityIssue] = field(default_factory=list)


def has_issues(result: NullabilityCheckResult) -> bool:
    return len(result.issues) > 0


def has_breaking(result: NullabilityCheckResult) -> bool:
    return any(i.is_breaking for i in result.issues)


def _type_str(t: pa.DataType) -> str:
    return str(t)


def check_nullability(
    path: str,
    old: pa.Schema,
    new: pa.Schema,
) -> NullabilityCheckResult:
    """Return nullability issues for fields present in both schemas."""
    result = NullabilityCheckResult(path=path)

    old_fields = {f.name: f for f in old}
    new_fields = {f.name: f for f in new}

    common = old_fields.keys() & new_fields.keys()
    for name in sorted(common):
        old_f = old_fields[name]
        new_f = new_fields[name]
        if old_f.nullable == new_f.nullable:
            continue
        if new_f.nullable and not old_f.nullable:
            change = NullabilityChange.BECAME_NULLABLE
        else:
            change = NullabilityChange.BECAME_NON_NULLABLE
        result.issues.append(NullabilityIssue(field_name=name, change=change))

    return result
