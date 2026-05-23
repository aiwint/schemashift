"""Format CompatCheckResult for text, JSON, and Markdown output."""
from __future__ import annotations

import json
from typing import Any, Dict

from schemashift.compat_check import CompatCheckResult


def _issue_line(issue) -> str:
    return f"  [{issue.direction.value.upper()}] {issue.field_name}: {issue.reason}"


def format_compat_text(result: CompatCheckResult, path: str = "") -> str:
    lines = []
    header = f"Compatibility check ({result.direction.value})"
    if path:
        header += f" — {path}"
    lines.append(header)
    lines.append("-" * len(header))

    if result.is_compatible:
        lines.append("✓ Schemas are compatible.")
    else:
        lines.append(f"✗ {len(result.issues)} compatibility issue(s) found:")
        for issue in result.issues:
            lines.append(_issue_line(issue))

    return "\n".join(lines)


def format_compat_json(result: CompatCheckResult, path: str = "") -> str:
    payload: Dict[str, Any] = {
        "path": path,
        "direction": result.direction.value,
        "compatible": result.is_compatible,
        "issues": [
            {
                "direction": i.direction.value,
                "field": i.field_name,
                "reason": i.reason,
            }
            for i in result.issues
        ],
    }
    return json.dumps(payload, indent=2)


def format_compat_markdown(result: CompatCheckResult, path: str = "") -> str:
    lines = []
    header = f"## Compatibility check ({result.direction.value})"
    if path:
        header += f" — `{path}`"
    lines.append(header)

    if result.is_compatible:
        lines.append("\n✅ Schemas are compatible.")
    else:
        lines.append(f"\n❌ **{len(result.issues)} issue(s) found:**\n")
        lines.append("| Direction | Field | Reason |")
        lines.append("|-----------|-------|--------|")
        for issue in result.issues:
            lines.append(
                f"| {issue.direction.value} | `{issue.field_name}` | {issue.reason} |"
            )

    return "\n".join(lines)
