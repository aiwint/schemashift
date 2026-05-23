"""Tests for schemashift.history_cmd."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pyarrow as pa
import pytest
from click.testing import CliRunner

from schemashift.history import append_snapshot
from schemashift.history_cmd import history_cmd
from schemashift.snapshot import Snapshot


SCHEMA_V1 = pa.schema([pa.field("id", pa.int64())])
SCHEMA_V2 = pa.schema([pa.field("id", pa.int64()), pa.field("score", pa.float64())])
SCHEMA_V3 = pa.schema([pa.field("score", pa.float64())])  # removed 'id' — breaking


def _run(args: list[str]):
    return CliRunner().invoke(history_cmd, args, catch_exceptions=False)


def test_empty_history_dir(tmp_path: Path) -> None:
    result = _run([str(tmp_path)])
    assert result.exit_code == 0
    assert "No snapshots" in result.output


def test_single_snapshot_shows_initial_message(tmp_path: Path) -> None:
    snap = Snapshot(source="a.parquet", captured_at="2024-01-01T00:00:00", schema=SCHEMA_V1)
    append_snapshot(tmp_path, snap)
    result = _run([str(tmp_path)])
    assert result.exit_code == 0
    assert "initial snapshot" in result.output


def test_two_snapshots_shows_diff(tmp_path: Path) -> None:
    append_snapshot(tmp_path, Snapshot("f.parquet", "2024-01-01T00:00:00", SCHEMA_V1))
    append_snapshot(tmp_path, Snapshot("f.parquet", "2024-01-02T00:00:00", SCHEMA_V2))
    result = _run([str(tmp_path)])
    assert result.exit_code == 0
    assert "score" in result.output


def test_breaking_only_filters_non_breaking(tmp_path: Path) -> None:
    append_snapshot(tmp_path, Snapshot("f.parquet", "2024-01-01T00:00:00", SCHEMA_V1))
    # V1 -> V2 is non-breaking (addition only)
    append_snapshot(tmp_path, Snapshot("f.parquet", "2024-01-02T00:00:00", SCHEMA_V2))
    result = _run([str(tmp_path), "--breaking-only"])
    assert result.exit_code == 0
    assert "No breaking changes" in result.output


def test_breaking_only_shows_breaking_entry(tmp_path: Path) -> None:
    append_snapshot(tmp_path, Snapshot("f.parquet", "2024-01-01T00:00:00", SCHEMA_V1))
    append_snapshot(tmp_path, Snapshot("f.parquet", "2024-01-02T00:00:00", SCHEMA_V3))
    result = _run([str(tmp_path), "--breaking-only"])
    assert result.exit_code == 0
    assert "id" in result.output
