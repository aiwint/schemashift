"""Format OverlapCheckResult for text, JSON, and Markdown output."""
from __future__ import annotations

import json
from typing import List

from schemashift.overlap_check import OverlapCheckResult, OverlapIssue, has_overlaps


def _issue_line(issue: OverlapIssue) -> str:
    return f"  {issue.old_name!r} -> {issue.new_name!r}  [{issue.field_type}]"


def format_overlap_text(result: OverlapCheckResult) -> str:
    lines: List[str] = []
    lines.append(f"Overlap Check: {result.path_old} vs {result.path_new}")
    lines.append("")
    if not has_overlaps(result):
        lines.append("No case-insensitive name collisions detected.")
        return "\n".join(lines)
    lines.append(f"Found {len(result.issues)} case-insensitive collision(s):")
    for issue in result.issues:
        lines.append(_issue_line(issue))
    return "\n".join(lines)


def format_overlap_json(result: OverlapCheckResult) -> str:
    payload = {
        "path_old": result.path_old,
        "path_new": result.path_new,
        "overlaps": [
            {"old_name": i.old_name, "new_name": i.new_name, "type": i.field_type}
            for i in result.issues
        ],
    }
    return json.dumps(payload, indent=2)


def format_overlap_markdown(result: OverlapCheckResult) -> str:
    lines: List[str] = []
    lines.append(f"## Overlap Check")
    lines.append(f"**Old:** `{result.path_old}`  ")
    lines.append(f"**New:** `{result.path_new}`")
    lines.append("")
    if not has_overlaps(result):
        lines.append("_No case-insensitive name collisions detected._")
        return "\n".join(lines)
    lines.append("| Old Name | New Name | Type |")
    lines.append("|----------|----------|------|")
    for issue in result.issues:
        lines.append(f"| `{issue.old_name}` | `{issue.new_name}` | `{issue.field_type}` |")
    return "\n".join(lines)
