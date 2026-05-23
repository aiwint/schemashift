"""Tests for schemashift.history."""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pytest

from schemashift.history import (
    SchemaHistory,
    append_snapshot,
    load_history,
    HistoryError,
)
from schemashift.snapshot import Snapshot


def _make_snapshot(source: str, ts: str, schema: pa.Schema) -> Snapshot:
    return Snapshot(source=source, captured_at=ts, schema=schema)


SCHEMA_V1 = pa.schema([pa.field("id", pa.int64()), pa.field("name", pa.string())])
SCHEMA_V2 = pa.schema(
    [pa.field("id", pa.int64()), pa.field("name", pa.string()), pa.field("age", pa.int32())]
)


def test_load_history_empty_dir(tmp_path: Path) -> None:
    history = load_history(tmp_path)
    assert isinstance(history, SchemaHistory)
    assert history.entries == []
    assert history.latest is None


def test_load_history_missing_dir(tmp_path: Path) -> None:
    history = load_history(tmp_path / "nonexistent")
    assert history.entries == []


def test_append_and_load_single_snapshot(tmp_path: Path) -> None:
    snap = _make_snapshot("data.parquet", "2024-01-01T00:00:00", SCHEMA_V1)
    dest = append_snapshot(tmp_path, snap)
    assert dest.exists()

    history = load_history(tmp_path)
    assert len(history.entries) == 1
    assert history.entries[0].diff_from_previous is None
    assert history.latest is not None
    assert history.latest.source == "data.parquet"


def test_append_two_snapshots_produces_diff(tmp_path: Path) -> None:
    snap1 = _make_snapshot("data.parquet", "2024-01-01T00:00:00", SCHEMA_V1)
    snap2 = _make_snapshot("data.parquet", "2024-01-02T00:00:00", SCHEMA_V2)
    append_snapshot(tmp_path, snap1)
    append_snapshot(tmp_path, snap2)

    history = load_history(tmp_path)
    assert len(history.entries) == 2
    assert history.entries[0].diff_from_previous is None
    diff = history.entries[1].diff_from_previous
    assert diff is not None
    assert any(f.name == "age" for f in diff.added)


def test_load_history_raises_on_corrupt_file(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text("not json")
    with pytest.raises(HistoryError):
        load_history(tmp_path)


def test_append_creates_parent_dirs(tmp_path: Path) -> None:
    nested = tmp_path / "a" / "b" / "history"
    snap = _make_snapshot("x.parquet", "2024-03-01T12:00:00", SCHEMA_V1)
    append_snapshot(nested, snap)
    assert nested.exists()
    assert len(list(nested.glob("*.json"))) == 1
