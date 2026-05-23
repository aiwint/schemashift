"""Format RenameCheckResult for text, JSON, and Markdown output."""
from __future__ import annotations

import json
from typing import List

from schemashift.rename_check import RenameCandidate, RenameCheckResult


def _pct(confidence: float) -> str:
    return f"{confidence * 100:.0f}%"


def format_rename_text(result: RenameCheckResult, path: str = "") -> str:
    lines: List[str] = []
    header = f"Rename candidates: {path}" if path else "Rename candidates"
    lines.append(header)
    lines.append("-" * len(header))

    if not result.has_candidates:
        lines.append("No rename candidates detected.")
        return "\n".join(lines)

    for c in result.candidates:
        lines.append(
            f"  {c.old_name!r} -> {c.new_name!r}  "
            f"[type: {c.field_type}]  confidence: {_pct(c.confidence)}"
        )
    return "\n".join(lines)


def format_rename_json(result: RenameCheckResult, path: str = "") -> str:
    payload = {
        "path": path,
        "rename_candidates": [
            {
                "old_name": c.old_name,
                "new_name": c.new_name,
                "field_type": c.field_type,
                "confidence": c.confidence,
            }
            for c in result.candidates
        ],
    }
    return json.dumps(payload, indent=2)


def format_rename_markdown(result: RenameCheckResult, path: str = "") -> str:
    lines: List[str] = []
    lines.append(f"## Rename Candidates")
    if path:
        lines.append(f"**Path:** `{path}`")
    lines.append("")

    if not result.has_candidates:
        lines.append("_No rename candidates detected._")
        return "\n".join(lines)

    lines.append("| Old Name | New Name | Type | Confidence |")
    lines.append("|----------|----------|------|------------|")
    for c in result.candidates:
        lines.append(
            f"| `{c.old_name}` | `{c.new_name}` | `{c.field_type}` | {_pct(c.confidence)} |"
        )
    return "\n".join(lines)
