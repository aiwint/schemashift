"""Formatting and reporting utilities for schema diffs."""

from __future__ import annotations

from enum import Enum
from typing import TextIO
import sys

from schemashift.schema_diff import SchemaDiff, has_breaking_changes


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"


def _field_type_str(field) -> str:
    return str(field.type)


def format_text(diff: SchemaDiff) -> str:
    lines: list[str] = []

    if diff.removed_fields:
        lines.append("Removed fields (BREAKING):")
        for f in diff.removed_fields:
            lines.append(f"  - {f.name}: {_field_type_str(f)}")

    if diff.type_changes:
        lines.append("Type changes (BREAKING):")
        for name, (old, new) in diff.type_changes.items():
            lines.append(f"  ~ {name}: {old} -> {new}")

    if diff.added_fields:
        lines.append("Added fields:")
        for f in diff.added_fields:
            lines.append(f"  + {f.name}: {_field_type_str(f)}")

    if diff.nullability_changes:
        lines.append("Nullability changes:")
        for name, (old, new) in diff.nullability_changes.items():
            lines.append(f"  ! {name}: nullable={old} -> nullable={new}")

    if not lines:
        lines.append("No schema changes detected.")
    else:
        status = "BREAKING CHANGES DETECTED" if has_breaking_changes(diff) else "Non-breaking changes only"
        lines.insert(0, f"Schema diff summary: {status}")
        lines.insert(1, "")

    return "\n".join(lines)


def format_json(diff: SchemaDiff) -> str:
    import json

    payload = {
        "breaking": has_breaking_changes(diff),
        "removed_fields": [{"name": f.name, "type": _field_type_str(f)} for f in diff.removed_fields],
        "added_fields": [{"name": f.name, "type": _field_type_str(f)} for f in diff.added_fields],
        "type_changes": {
            name: {"from": str(old), "to": str(new)}
            for name, (old, new) in diff.type_changes.items()
        },
        "nullability_changes": {
            name: {"from": old, "to": new}
            for name, (old, new) in diff.nullability_changes.items()
        },
    }
    return json.dumps(payload, indent=2)


def format_markdown(diff: SchemaDiff) -> str:
    lines: list[str] = []
    breaking = has_breaking_changes(diff)
    status_badge = "🔴 Breaking" if breaking else "🟢 Non-breaking"
    lines.append(f"## Schema Diff — {status_badge}\n")

    if diff.removed_fields:
        lines.append("### Removed Fields _(breaking)_")
        for f in diff.removed_fields:
            lines.append(f"- `{f.name}` ({_field_type_str(f)})")
        lines.append("")

    if diff.type_changes:
        lines.append("### Type Changes _(breaking)_")
        for name, (old, new) in diff.type_changes.items():
            lines.append(f"- `{name}`: `{old}` → `{new}`")
        lines.append("")

    if diff.added_fields:
        lines.append("### Added Fields")
        for f in diff.added_fields:
            lines.append(f"- `{f.name}` ({_field_type_str(f)})")
        lines.append("")

    if diff.nullability_changes:
        lines.append("### Nullability Changes")
        for name, (old, new) in diff.nullability_changes.items():
            lines.append(f"- `{name}`: nullable=`{old}` → nullable=`{new}`")
        lines.append("")

    if len(lines) == 1:
        lines.append("_No schema changes detected._")

    return "\n".join(lines)


def render(diff: SchemaDiff, fmt: OutputFormat = OutputFormat.TEXT, out: TextIO = sys.stdout) -> None:
    formatters = {
        OutputFormat.TEXT: format_text,
        OutputFormat.JSON: format_json,
        OutputFormat.MARKDOWN: format_markdown,
    }
    output = formatters[fmt](diff)
    print(output, file=out)
