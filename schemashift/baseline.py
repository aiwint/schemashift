"""Baseline comparison: compare a live dataset schema against a saved snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pyarrow as pa

from schemashift.schema_diff import SchemaDiff, diff_schemas
from schemashift.snapshot import SnapshotError, load_snapshot
from schemashift.summarizer import DiffSummary, summarize


class BaselineError(Exception):
    """Raised when a baseline comparison cannot be completed."""


@dataclass(frozen=True)
class BaselineResult:
    """Result of comparing a schema against a baseline snapshot."""

    snapshot_path: Path
    diff: SchemaDiff
    summary: DiffSummary

    @property
    def has_changes(self) -> bool:
        return not self.diff.is_empty()


def compare_against_baseline(
    current_schema: pa.Schema,
    snapshot_path: Path,
    *,
    label: Optional[str] = None,
) -> BaselineResult:
    """Load a snapshot from *snapshot_path* and diff it against *current_schema*.

    Parameters
    ----------
    current_schema:
        The schema read from the live / current dataset.
    snapshot_path:
        Path to a JSON snapshot file previously saved by :func:`schemashift.snapshot.save_snapshot`.
    label:
        Optional human-readable label used in error messages.

    Returns
    -------
    BaselineResult
        Frozen dataclass containing the diff and its summary.

    Raises
    ------
    BaselineError
        If the snapshot cannot be loaded.
    """
    tag = label or str(snapshot_path)
    try:
        snapshot = load_snapshot(snapshot_path)
    except SnapshotError as exc:
        raise BaselineError(f"Could not load baseline snapshot '{tag}': {exc}") from exc

    diff = diff_schemas(snapshot.schema, current_schema)
    summary = summarize(diff)
    return BaselineResult(snapshot_path=snapshot_path, diff=diff, summary=summary)
