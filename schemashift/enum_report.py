"""Format EnumCheckResult as text, JSON, or Markdown."""
from __future__ import annotations

import json
from typing import List

from schemashift.enum_check import EnumCheckResult, EnumIssue


def _issue_line(issue: EnumIssue) -> str:
    tag = {
        "encoded": "[ENCODED]",
        "decoded": "[DECODED]",
        "type_changed": "[TYPE_CHANGED]",
    }.get(issue.direction, "[UNKNOWN]")
    return f"  {tag} {issue.description}"


def format_enum_text(path: str, result: EnumCheckResult) -> str:
    lines: List[str] = [f"Dictionary/Enum Check: {path}"]
    if not result.issues:
        lines.append("  No dictionary encoding changes detected.")
        return "\n".join(lines)
    for issue in result.issues:
        lines.append(_issue_line(issue))
    return "\n".join(lines)


def format_enum_json(path: str, result: EnumCheckResult) -> str:
    payload = {
        "path": path,
        "issues": [
            {
                "field": i.field_name,
                "old_type": i.old_type,
                "new_type": i.new_type,
                "direction": i.direction,
                "description": i.description,
            }
            for i in result.issues
        ],
    }
    return json.dumps(payload, indent=2)


def format_enum_markdown(path: str, result: EnumCheckResult) -> str:
    lines: List[str] = [f"## Dictionary/Enum Check: `{path}`", ""]
    if not result.issues:
        lines.append("_No dictionary encoding changes detected._")
        return "\n".join(lines)
    lines += ["| Field | Direction | Old Type | New Type |",
              "|-------|-----------|----------|----------|"]  
    for i in result.issues:
        lines.append(f"| {i.field_name} | {i.direction} | {i.old_type} | {i.new_type} |")
    return "\n".join(lines)


def format_enum(fmt: str, path: str, result: EnumCheckResult) -> str:
    if fmt == "json":
        return format_enum_json(path, result)
    if fmt in ("md", "markdown"):
        return format_enum_markdown(path, result)
    return format_enum_text(path, result)
