"""Render a SchemaProfile as text, JSON, or Markdown."""

from __future__ import annotations

import json
from typing import List

from schemashift.profile import FieldProfile, SchemaProfile


def _pct(rate: float) -> str:
    return f"{rate * 100:.1f}%"


def format_profile_text(profile: SchemaProfile) -> str:
    lines: List[str] = [
        f"Profile: {profile.path}",
        f"Rows   : {profile.row_count:,}",
        f"Fields : {len(profile.fields)}",
        "-" * 52,
        f"{'Field':<24} {'Type':<14} {'Nullable':<10} {'Null %'}",
        "-" * 52,
    ]
    for fp in profile.fields:
        lines.append(
            f"{fp.name:<24} {fp.type:<14} {str(fp.nullable):<10} {_pct(fp.null_rate)}"
        )
    lines.append("-" * 52)
    return "\n".join(lines)


def format_profile_json(profile: SchemaProfile) -> str:
    data = {
        "path": profile.path,
        "row_count": profile.row_count,
        "fields": [
            {
                "name": fp.name,
                "type": fp.type,
                "nullable": fp.nullable,
                "null_count": fp.null_count,
                "null_rate": round(fp.null_rate, 6),
            }
            for fp in profile.fields
        ],
    }
    return json.dumps(data, indent=2)


def format_profile_markdown(profile: SchemaProfile) -> str:
    lines: List[str] = [
        f"## Profile: `{profile.path}`",
        "",
        f"- **Rows**: {profile.row_count:,}",
        f"- **Fields**: {len(profile.fields)}",
        "",
        "| Field | Type | Nullable | Null % |",
        "|-------|------|----------|--------|",
    ]
    for fp in profile.fields:
        lines.append(
            f"| {fp.name} | {fp.type} | {fp.nullable} | {_pct(fp.null_rate)} |"
        )
    return "\n".join(lines)
