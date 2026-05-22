"""Tests for schemashift.snapshot."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pytest

from schemashift.snapshot import (
    Snapshot,
    SnapshotError,
    load_snapshot,
    make_snapshot,
    save_snapshot,
)


_SCHEMA = pa.schema(
    [
        pa.field("id", pa.int64(), nullable=False),
        pa.field("name", pa.string(), nullable=True),
    ]
)


def _make_snapshot() -> Snapshot:
    return Snapshot(
        path="/data/users.parquet",
        schema=_SCHEMA,
        captured_at=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
    )


class TestSaveAndLoad:
    def test_round_trip(self, tmp_path: Path) -> None:
        dest = tmp_path / "snap.json"
        snap = _make_snapshot()
        save_snapshot(snap, dest)
        loaded = load_snapshot(dest)
        assert loaded.path == snap.path
        assert loaded.schema.equals(snap.schema)
        assert loaded.captured_at == snap.captured_at

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        dest = tmp_path / "nested" / "dir" / "snap.json"
        save_snapshot(_make_snapshot(), dest)
        assert dest.exists()

    def test_load_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(SnapshotError, match="not found"):
            load_snapshot(tmp_path / "missing.json")

    def test_load_corrupt_json_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("not json{{")
        with pytest.raises(SnapshotError, match="Could not read"):
            load_snapshot(bad)

    def test_serialised_fields_correct(self, tmp_path: Path) -> None:
        dest = tmp_path / "snap.json"
        save_snapshot(_make_snapshot(), dest)
        raw = json.loads(dest.read_text())
        assert raw["fields"][0]["name"] == "id"
        assert raw["fields"][0]["nullable"] is False
        assert raw["fields"][1]["name"] == "name"
        assert raw["fields"][1]["nullable"] is True


class TestMakeSnapshot:
    def test_path_stored(self) -> None:
        snap = make_snapshot("s3://bucket/data.parquet", _SCHEMA)
        assert snap.path == "s3://bucket/data.parquet"

    def test_schema_stored(self) -> None:
        snap = make_snapshot("data.parquet", _SCHEMA)
        assert snap.schema.equals(_SCHEMA)

    def test_captured_at_is_utc(self) -> None:
        snap = make_snapshot("data.parquet", _SCHEMA)
        assert snap.captured_at.tzinfo == timezone.utc

    def test_to_dict_contains_required_keys(self) -> None:
        snap = _make_snapshot()
        d = snap.to_dict()
        assert set(d.keys()) == {"path", "captured_at", "fields"}
