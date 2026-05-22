"""Summarize schema diffs into human-readable statistics and severity levels."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from schemashift.schema_diff import SchemaDiff, has_breaking_changes, is_empty


class Severity(str, Enum):
    NONE = "none"
    INFO = "info"
    WARNING = "warning"
    BREAKING = "breaking"


@dataclass
class DiffSummary:
    severity: Severity
    total_changes: int
    breaking_count: int
    added_count: int
    removed_count: int
    type_changed_count: int
    nullable_changed_count: int
    headline: str
    detail: Optional[str] = None


def summarize(diff: SchemaDiff) -> DiffSummary:
    """Produce a DiffSummary from a SchemaDiff."""
    added = len(diff.added_fields)
    removed = len(diff.removed_fields)
    type_changed = len(diff.type_changes)
    nullable_changed = len(diff.nullability_changes)

    breaking = removed + type_changed
    total = added + removed + type_changed + nullable_changed

    if is_empty(diff):
        severity = Severity.NONE
        headline = "No schema changes detected."
        detail = None
    elif has_breaking_changes(diff):
        severity = Severity.BREAKING
        parts = []
        if removed:
            parts.append(f"{removed} removed field(s)")
        if type_changed:
            parts.append(f"{type_changed} type change(s)")
        headline = "Breaking changes detected: " + ", ".join(parts) + "."
        detail = _build_detail(added, removed, type_changed, nullable_changed)
    elif nullable_changed or added:
        severity = Severity.WARNING if nullable_changed else Severity.INFO
        headline = (
            f"Non-breaking changes detected: {total} change(s)."
        )
        detail = _build_detail(added, removed, type_changed, nullable_changed)
    else:
        severity = Severity.INFO
        headline = f"{total} schema change(s) detected (non-breaking)."
        detail = _build_detail(added, removed, type_changed, nullable_changed)

    return DiffSummary(
        severity=severity,
        total_changes=total,
        breaking_count=breaking,
        added_count=added,
        removed_count=removed,
        type_changed_count=type_changed,
        nullable_changed_count=nullable_changed,
        headline=headline,
        detail=detail,
    )


def _build_detail(added: int, removed: int, type_changed: int, nullable_changed: int) -> str:
    lines = []
    if added:
        lines.append(f"  + {added} field(s) added")
    if removed:
        lines.append(f"  - {removed} field(s) removed")
    if type_changed:
        lines.append(f"  ~ {type_changed} field(s) changed type")
    if nullable_changed:
        lines.append(f"  ~ {nullable_changed} field(s) changed nullability")
    return "\n".join(lines)
