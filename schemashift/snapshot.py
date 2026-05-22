"""Schema snapshot management — save and load schema snapshots to/from disk."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pyarrow as pa


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


@dataclass
class Snapshot:
    path: str
    schema: pa.Schema
    captured_at: datetime

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "captured_at": self.captured_at.isoformat(),
            "fields": [
                {
                    "name": field.name,
                    "type": str(field.type),
                    "nullable": field.nullable,
                }
                for field in self.schema
            ],
        }


def save_snapshot(snapshot: Snapshot, dest: Path) -> None:
    """Serialise *snapshot* as JSON and write it to *dest*."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        dest.write_text(json.dumps(snapshot.to_dict(), indent=2))
    except OSError as exc:
        raise SnapshotError(f"Could not write snapshot to {dest}: {exc}") from exc


def load_snapshot(src: Path) -> Snapshot:
    """Deserialise a snapshot from *src* and return a :class:`Snapshot`."""
    if not src.exists():
        raise SnapshotError(f"Snapshot file not found: {src}")
    try:
        data = json.loads(src.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"Could not read snapshot from {src}: {exc}") from exc

    fields = [
        pa.field(f["name"], pa.lib.ensure_type(f["type"]), nullable=f["nullable"])
        for f in data["fields"]
    ]
    schema = pa.schema(fields)
    captured_at = datetime.fromisoformat(data["captured_at"])
    return Snapshot(path=data["path"], schema=schema, captured_at=captured_at)


def make_snapshot(dataset_path: str, schema: pa.Schema) -> Snapshot:
    """Create a new :class:`Snapshot` stamped with the current UTC time."""
    return Snapshot(
        path=dataset_path,
        schema=schema,
        captured_at=datetime.now(tz=timezone.utc),
    )
