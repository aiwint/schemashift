"""Detect fields whose types changed to or from dictionary/categorical encoding."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pyarrow as pa

from schemashift.schema_diff import SchemaDiff


@dataclass
class EnumIssue:
    field_name: str
    old_type: str
    new_type: str
    direction: str  # "encoded" | "decoded" | "type_changed"

    @property
    def description(self) -> str:
        if self.direction == "encoded":
            return f"'{self.field_name}' changed to dictionary encoding ({self.old_type} -> {self.new_type})"
        if self.direction == "decoded":
            return f"'{self.field_name}' removed dictionary encoding ({self.old_type} -> {self.new_type})"
        return f"'{self.field_name}' dictionary value type changed ({self.old_type} -> {self.new_type})"


@dataclass
class EnumCheckResult:
    issues: List[EnumIssue] = field(default_factory=list)


def has_issues(result: EnumCheckResult) -> bool:
    return len(result.issues) > 0


def _type_str(t: pa.DataType) -> str:
    return str(t)


def _is_dict(t: pa.DataType) -> bool:
    return pa.types.is_dictionary(t)


def check_enum_changes(diff: SchemaDiff) -> EnumCheckResult:
    """Return issues for fields whose dictionary encoding status changed."""
    issues: List[EnumIssue] = []

    for name, (old_field, new_field) in diff.type_changed.items():
        old_t = old_field.type
        new_t = new_field.type
        old_dict = _is_dict(old_t)
        new_dict = _is_dict(new_t)

        if not old_dict and new_dict:
            issues.append(EnumIssue(name, _type_str(old_t), _type_str(new_t), "encoded"))
        elif old_dict and not new_dict:
            issues.append(EnumIssue(name, _type_str(old_t), _type_str(new_t), "decoded"))
        elif old_dict and new_dict:
            old_val = old_t.value_type  # type: ignore[union-attr]
            new_val = new_t.value_type  # type: ignore[union-attr]
            if old_val != new_val:
                issues.append(
                    EnumIssue(
                        name,
                        f"dict<{_type_str(old_val)}>",
                        f"dict<{_type_str(new_val)}>",
                        "type_changed",
                    )
                )

    return EnumCheckResult(issues=issues)
