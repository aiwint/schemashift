"""Detect unsafe type casts between schema versions."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

import pyarrow as pa

from schemashift.schema_diff import SchemaDiff


class CastSafety(str, Enum):
    SAFE = "safe"
    NARROWING = "narrowing"
    INCOMPATIBLE = "incompatible"


@dataclass
class CastIssue:
    field_name: str
    old_type: str
    new_type: str
    safety: CastSafety
    message: str


@dataclass
class CastCheckResult:
    issues: List[CastIssue] = field(default_factory=list)

    @property
    def has_incompatible(self) -> bool:
        return any(i.safety == CastSafety.INCOMPATIBLE for i in self.issues)

    @property
    def has_narrowing(self) -> bool:
        return any(i.safety == CastSafety.NARROWING for i in self.issues)


_NUMERIC_WIDENING: dict[str, int] = {
    "int8": 1, "int16": 2, "int32": 3, "int64": 4,
    "uint8": 1, "uint16": 2, "uint32": 3, "uint64": 4,
    "float16": 10, "float32": 11, "float64": 12,
}


def _cast_safety(old: pa.DataType, new: pa.DataType) -> Optional[CastSafety]:
    if old == new:
        return None
    old_s = str(old)
    new_s = str(new)
    old_rank = _NUMERIC_WIDENING.get(old_s)
    new_rank = _NUMERIC_WIDENING.get(new_s)
    if old_rank is not None and new_rank is not None:
        if new_rank >= old_rank:
            return CastSafety.SAFE
        return CastSafety.NARROWING
    return CastSafety.INCOMPATIBLE


def check_casts(diff: SchemaDiff) -> CastCheckResult:
    """Inspect type-changed fields in *diff* and classify each cast."""
    result = CastCheckResult()
    for fc in diff.type_changes:
        safety = _cast_safety(fc.old_type, fc.new_type)
        if safety is None:
            continue
        old_s = str(fc.old_type)
        new_s = str(fc.new_type)
        if safety == CastSafety.SAFE:
            msg = f"Widening cast {old_s} -> {new_s} is safe."
        elif safety == CastSafety.NARROWING:
            msg = f"Narrowing cast {old_s} -> {new_s} may lose precision."
        else:
            msg = f"Incompatible cast {old_s} -> {new_s}."
        result.issues.append(CastIssue(fc.field_name, old_s, new_s, safety, msg))
    return result
