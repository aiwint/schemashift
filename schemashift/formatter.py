"""Utilities for rendering schema fields and diffs in a consistent format."""

from __future__ import annotations

from typing import List, Tuple

import pyarrow as pa


def field_summary(field: pa.Field) -> str:
    """Return a short human-readable description of a single Arrow field."""
    nullable = "nullable" if field.nullable else "not nullable"
    return f"{field.name}: {field.type} ({nullable})"


def schema_table(schema: pa.Schema) -> List[Tuple[str, str, str]]:
    """Return a list of (name, type, nullable) tuples for tabular display."""
    rows = []
    for i in range(len(schema)):
        field = schema.field(i)
        rows.append((
            field.name,
            str(field.type),
            "yes" if field.nullable else "no",
        ))
    return rows


def diff_table(
    removed: List[pa.Field],
    added: List[pa.Field],
    type_changed: List[Tuple[pa.Field, pa.Field]],
    nullability_changed: List[Tuple[pa.Field, pa.Field]],
) -> List[Tuple[str, str, str]]:
    """Return a flat list of (change_kind, field_name, detail) rows.

    Suitable for rendering as a plain table or CSV.
    """
    rows: List[Tuple[str, str, str]] = []

    for f in removed:
        rows.append(("REMOVED", f.name, str(f.type)))

    for f in added:
        rows.append(("ADDED", f.name, str(f.type)))

    for old, new in type_changed:
        rows.append(("TYPE_CHANGED", old.name, f"{old.type} -> {new.type}"))

    for old, new in nullability_changed:
        old_null = "nullable" if old.nullable else "not nullable"
        new_null = "nullable" if new.nullable else "not nullable"
        rows.append(("NULLABILITY_CHANGED", old.name, f"{old_null} -> {new_null}"))

    return rows


def format_diff_table_text(rows: List[Tuple[str, str, str]]) -> str:
    """Render diff table rows as a fixed-width text table."""
    if not rows:
        return "No changes detected."

    headers = ("Change", "Field", "Detail")
    col_widths = [
        max(len(headers[i]), max(len(r[i]) for r in rows))
        for i in range(3)
    ]

    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    header_row = "| " + " | ".join(
        h.ljust(col_widths[i]) for i, h in enumerate(headers)
    ) + " |"

    lines = [sep, header_row, sep]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(3))
            + " |"
        )
    lines.append(sep)
    return "\n".join(lines)
