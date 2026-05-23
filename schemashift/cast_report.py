"""Format CastCheckResult for human and machine consumption."""
from __future__ import annotations

import json
from typing import List

from schemashift.cast_check import CastCheckResult, CastIssue, CastSafety

_ICONS = {
    CastSafety.SAFE: "✓",
    CastSafety.NARROWING: "⚠",
    CastSafety.INCOMPATIBLE: "✗",
}


def _issue_line(issue: CastIssue) -> str:
    icon = _ICONS[issue.safety]
    return f"  {icon} [{issue.safety.value.upper():12s}] {issue.field_name}: {issue.message}"


def format_cast_text(result: CastCheckResult, path: str = "") -> str:
    lines: List[str] = []
    header = f"Cast Check Report"
    if path:
        header += f" — {path}"
    lines.append(header)
    lines.append("=" * len(header))
    if not result.issues:
        lines.append("  No type changes detected.")
    else:
        for issue in result.issues:
            lines.append(_issue_line(issue))
    lines.append("")
    return "\n".join(lines)


def format_cast_json(result: CastCheckResult) -> str:
    payload = [
        {
            "field": i.field_name,
            "old_type": i.old_type,
            "new_type": i.new_type,
            "safety": i.safety.value,
            "message": i.message,
        }
        for i in result.issues
    ]
    return json.dumps({"cast_issues": payload}, indent=2)


def format_cast_markdown(result: CastCheckResult) -> str:
    lines: List[str] = ["## Cast Check Report", ""]
    if not result.issues:
        lines.append("_No type changes detected._")
    else:
        lines.append("| Field | Old Type | New Type | Safety |")
        lines.append("|-------|----------|----------|--------|")
        for i in result.issues:
            lines.append(f"| `{i.field_name}` | `{i.old_type}` | `{i.new_type}` | **{i.safety.value}** |")
    lines.append("")
    return "\n".join(lines)
