"""Schema linting: detect common schema quality issues."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List

import pyarrow as pa


class LintSeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class LintIssue:
    field_name: str
    message: str
    severity: LintSeverity


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == LintSeverity.ERROR for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == LintSeverity.WARNING for i in self.issues)

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0


def _check_field(f: pa.Field) -> List[LintIssue]:
    issues: List[LintIssue] = []

    # Warn on fully nullable large string / binary columns with no metadata
    if f.type in (pa.large_string(), pa.large_binary()) and f.nullable:
        issues.append(
            LintIssue(
                field_name=f.name,
                message="Large string/binary field is nullable; consider explicit nullability intent.",
                severity=LintSeverity.WARNING,
            )
        )

    # Error on fields with empty names
    if not f.name or not f.name.strip():
        issues.append(
            LintIssue(
                field_name=repr(f.name),
                message="Field has an empty or blank name.",
                severity=LintSeverity.ERROR,
            )
        )

    # Warn on fields whose names contain spaces
    if f.name and " " in f.name:
        issues.append(
            LintIssue(
                field_name=f.name,
                message="Field name contains spaces, which may cause compatibility issues.",
                severity=LintSeverity.WARNING,
            )
        )

    # Warn on dictionary-encoded fields without explicit index type docs
    if pa.types.is_dictionary(f.type) and not (f.metadata or {}):
        issues.append(
            LintIssue(
                field_name=f.name,
                message="Dictionary-encoded field has no metadata; consider documenting index/value types.",
                severity=LintSeverity.WARNING,
            )
        )

    return issues


def lint_schema(schema: pa.Schema) -> LintResult:
    """Run all lint checks against *schema* and return a :class:`LintResult`."""
    result = LintResult()
    seen: set[str] = set()
    for f in schema:
        if f.name in seen:
            result.issues.append(
                LintIssue(
                    field_name=f.name,
                    message="Duplicate field name detected.",
                    severity=LintSeverity.ERROR,
                )
            )
        seen.add(f.name)
        result.issues.extend(_check_field(f))
    return result
