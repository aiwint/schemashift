"""Detect potential field renames between two schemas.

A rename candidate is a (removed, added) field pair where the types match
but the names differ.  This is heuristic — it cannot be certain — so we
expose a confidence score based on type compatibility and positional
proximity.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

import pyarrow as pa

from schemashift.schema_diff import SchemaDiff


@dataclass(frozen=True)
class RenameCandidate:
    old_name: str
    new_name: str
    field_type: str
    confidence: float  # 0.0 – 1.0


@dataclass
class RenameCheckResult:
    candidates: List[RenameCandidate] = field(default_factory=list)

    @property
    def has_candidates(self) -> bool:
        return bool(self.candidates)


def _type_str(f: pa.Field) -> str:
    return str(f.type)


def _positional_score(old_index: int, new_index: int, total: int) -> float:
    """Return 1.0 when indices are identical, decaying toward 0."""
    if total <= 1:
        return 1.0
    distance = abs(old_index - new_index) / total
    return max(0.0, 1.0 - distance)


def check_renames(
    old_schema: pa.Schema,
    new_schema: pa.Schema,
    diff: SchemaDiff,
    min_confidence: float = 0.5,
) -> RenameCheckResult:
    """Return rename candidates derived from *diff*.

    Only removed/added pairs with matching types and confidence >=
    *min_confidence* are included.
    """
    result = RenameCheckResult()

    removed_fields: List[Tuple[int, pa.Field]] = [
        (old_schema.get_field_index(name), old_schema.field(name))
        for name in diff.removed
    ]
    added_fields: List[Tuple[int, pa.Field]] = [
        (new_schema.get_field_index(name), new_schema.field(name))
        for name in diff.added
    ]

    if not removed_fields or not added_fields:
        return result

    total_fields = max(len(old_schema), len(new_schema))

    for old_idx, old_f in removed_fields:
        for new_idx, new_f in added_fields:
            if _type_str(old_f) != _type_str(new_f):
                continue
            pos_score = _positional_score(old_idx, new_idx, total_fields)
            # Exact type match gives base confidence of 0.7; position adds up to 0.3
            confidence = round(0.7 + 0.3 * pos_score, 4)
            if confidence >= min_confidence:
                result.candidates.append(
                    RenameCandidate(
                        old_name=old_f.name,
                        new_name=new_f.name,
                        field_type=_type_str(old_f),
                        confidence=confidence,
                    )
                )

    return result
