"""Check forward/backward compatibility between two schemas."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List

import pyarrow as pa

from schemashift.schema_diff import SchemaDiff, diff_schemas


class CompatDirection(str, Enum):
    FORWARD = "forward"   # new schema can read old data
    BACKWARD = "backward"  # old schema can read new data
    FULL = "full"          # both directions


@dataclass
class CompatIssue:
    direction: CompatDirection
    field_name: str
    reason: str


@dataclass
class CompatCheckResult:
    direction: CompatDirection
    issues: List[CompatIssue] = field(default_factory=list)

    @property
    def is_compatible(self) -> bool:
        return len(self.issues) == 0


def _forward_issues(diff: SchemaDiff) -> List[CompatIssue]:
    """New schema reading old data: removed fields break forward compat."""
    issues: List[CompatIssue] = []
    for f in diff.removed:
        issues.append(
            CompatIssue(
                direction=CompatDirection.FORWARD,
                field_name=f.name,
                reason=f"Field '{f.name}' removed; old data will be missing it",
            )
        )
    for old_f, new_f in diff.type_changed:
        issues.append(
            CompatIssue(
                direction=CompatDirection.FORWARD,
                field_name=old_f.name,
                reason=(
                    f"Field '{old_f.name}' type changed "
                    f"{old_f.type} -> {new_f.type}; may not be readable"
                ),
            )
        )
    return issues


def _backward_issues(diff: SchemaDiff) -> List[CompatIssue]:
    """Old schema reading new data: added non-nullable fields break backward compat."""
    issues: List[CompatIssue] = []
    for f in diff.added:
        if not f.nullable:
            issues.append(
                CompatIssue(
                    direction=CompatDirection.BACKWARD,
                    field_name=f.name,
                    reason=(
                        f"Non-nullable field '{f.name}' added; "
                        "old readers cannot satisfy constraint"
                    ),
                )
            )
    return issues


def check_compat(
    old: pa.Schema,
    new: pa.Schema,
    direction: CompatDirection = CompatDirection.FULL,
) -> CompatCheckResult:
    diff = diff_schemas(old, new)
    issues: List[CompatIssue] = []

    if direction in (CompatDirection.FORWARD, CompatDirection.FULL):
        issues.extend(_forward_issues(diff))
    if direction in (CompatDirection.BACKWARD, CompatDirection.FULL):
        issues.extend(_backward_issues(diff))

    return CompatCheckResult(direction=direction, issues=issues)
