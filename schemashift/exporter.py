"""Export schema diffs to various file formats."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Optional

from schemashift.schema_diff import SchemaDiff
from schemashift.report import format_text, format_json, format_markdown, OutputFormat


class ExportError(Exception):
    """Raised when an export operation fails."""


class ExportFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"


_FORMAT_MAP: dict[ExportFormat, OutputFormat] = {
    ExportFormat.TEXT: OutputFormat.TEXT,
    ExportFormat.JSON: OutputFormat.JSON,
    ExportFormat.MARKDOWN: OutputFormat.MARKDOWN,
}


def export_diff(
    diff: SchemaDiff,
    output_path: Path,
    fmt: ExportFormat = ExportFormat.TEXT,
    overwrite: bool = False,
) -> Path:
    """Render *diff* and write it to *output_path*.

    Parameters
    ----------
    diff:
        The :class:`SchemaDiff` to export.
    output_path:
        Destination file path.  Parent directories must already exist.
    fmt:
        Output format – one of ``text``, ``json``, or ``markdown``.
    overwrite:
        When *False* (default) raise :class:`ExportError` if the file
        already exists.

    Returns
    -------
    Path
        The resolved path of the written file.
    """
    resolved = output_path.resolve()

    if resolved.exists() and not overwrite:
        raise ExportError(
            f"Output file already exists: {resolved}. "
            "Pass overwrite=True to replace it."
        )

    output_format = _FORMAT_MAP[fmt]
    from schemashift.report import format_report
    content = format_report(diff, output_format)

    resolved.write_text(content, encoding="utf-8")
    return resolved
