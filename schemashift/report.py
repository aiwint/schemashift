"""Render a SchemaDiff + DiffSummary into human-readable or structured output."""

from __future__ import annotations

import json
from enum import Enum
from typing import Any

import pyarrow as pa

from schemashift.schema_diff import SchemaDiff
from schemashift.summarizer import DiffSummary, Severity


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"


def _field_type_str(field: pa.Field) -> str:
    nullable = "nullable" if field.nullable else "not nullable"
    return f"{field.type} ({nullable})"


def format_text(diff: SchemaDiff, summary: DiffSummary) -> str:
    lines: list[str] = []
    if summary.severity is None:
        lines.append("No schema changes detected.")
        return "\n".join(lines)

    lines.append(f"Severity: {summary.severity.value.upper()}")
    lines.append("")

    if diff.removed:
        lines.append("Removed fields (BREAKING):")
        for f in diff.removed:
            lines.append(f"  - {f.name}: {_field_type_str(f)}")

    if diff.added:
        lines.append("Added fields:")
        for f in diff.added:
            lines.append(f"  + {f.name}: {_field_type_str(f)}")

    if diff.type_changed:
        lines.append("Type changes (BREAKING):")
        for name, (old, new) in diff.type_changed.items():
            lines.append(f"  ~ {name}: {old} -> {new}")

    if diff.nullability_changed:
        lines.append("Nullability changes:")
        for name, (old, new) in diff.nullability_changed.items():
            old_s = "nullable" if old else "not nullable"
            new_s = "nullable" if new else "not nullable"
            lines.append(f"  ~ {name}: {old_s} -> {new_s}")

    if summary.details:
        lines.append("")
        lines.append("Summary:")
        for detail in summary.details:
            lines.append(f"  {detail}")

    return "\n".join(lines)


def format_json(diff: SchemaDiff, summary: DiffSummary) -> str:
    payload: dict[str, Any] = {
        "summary": {
            "severity": summary.severity.value if summary.severity else None,
            "details": summary.details,
        },
        "removed": [{"name": f.name, "type": str(f.type)} for f in diff.removed],
        "added": [{"name": f.name, "type": str(f.type)} for f in diff.added],
        "type_changed": {
            name: {"from": str(old), "to": str(new)}
            for name, (old, new) in diff.type_changed.items()
        },
        "nullability_changed": {
            name: {"from": old, "to": new}
            for name, (old, new) in diff.nullability_changed.items()
        },
    }
    return json.dumps(payload, indent=2)


def format_markdown(diff: SchemaDiff, summary: DiffSummary) -> str:
    lines: list[str] = ["## Schema Diff Report", ""]
    sev = summary.severity.value.upper() if summary.severity else "NONE"
    lines.append(f"**Severity:** {sev}")
    lines.append("")

    if diff.removed:
        lines.append("### Removed Fields _(breaking)_")
        for f in diff.removed:
            lines.append(f"- `{f.name}` — {_field_type_str(f)}")
        lines.append("")

    if diff.added:
        lines.append("### Added Fields")
        for f in diff.added:
            lines.append(f"- `{f.name}` — {_field_type_str(f)}")
        lines.append("")

    if diff.type_changed:
        lines.append("### Type Changes _(breaking)_")
        for name, (old, new) in diff.type_changed.items():
            lines.append(f"- `{name}`: `{old}` → `{new}`")
        lines.append("")

    return "\n".join(lines)


def format_report(diff: SchemaDiff, summary: DiffSummary, fmt: OutputFormat) -> str:
    if fmt == OutputFormat.JSON:
        return format_json(diff, summary)
    if fmt == OutputFormat.MARKDOWN:
        return format_markdown(diff, summary)
    return format_text(diff, summary)
