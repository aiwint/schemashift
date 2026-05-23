"""Track and query a history of schema snapshots over time."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from schemashift.snapshot import Snapshot, to_dict, load_snapshot
from schemashift.schema_diff import diff_schemas, SchemaDiff


class HistoryError(Exception):
    """Raised when history operations fail."""


@dataclass
class HistoryEntry:
    snapshot: Snapshot
    diff_from_previous: Optional[SchemaDiff] = None


@dataclass
class SchemaHistory:
    entries: List[HistoryEntry] = field(default_factory=list)

    @property
    def latest(self) -> Optional[Snapshot]:
        return self.entries[-1].snapshot if self.entries else None


def load_history(history_dir: Path) -> SchemaHistory:
    """Load all snapshots from *history_dir* sorted by timestamp."""
    if not history_dir.exists():
        return SchemaHistory()

    snapshot_files = sorted(history_dir.glob("*.json"))
    if not snapshot_files:
        return SchemaHistory()

    history = SchemaHistory()
    previous: Optional[Snapshot] = None

    for path in snapshot_files:
        try:
            snapshot = load_snapshot(path)
        except Exception as exc:  # noqa: BLE001
            raise HistoryError(f"Failed to load snapshot {path}: {exc}") from exc

        diff = diff_schemas(previous.schema, snapshot.schema) if previous else None
        history.entries.append(HistoryEntry(snapshot=snapshot, diff_from_previous=diff))
        previous = snapshot

    return history


def append_snapshot(history_dir: Path, snapshot: Snapshot) -> Path:
    """Persist *snapshot* into *history_dir* using its timestamp as filename."""
    history_dir.mkdir(parents=True, exist_ok=True)
    safe_ts = snapshot.captured_at.replace(":", "-").replace(" ", "T")
    dest = history_dir / f"{safe_ts}.json"
    dest.write_text(json.dumps(to_dict(snapshot), indent=2))
    return dest
