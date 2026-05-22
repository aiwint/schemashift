"""Tests for schemashift.snapshot_cmd."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pyarrow as pa
import pytest
from click.testing import CliRunner

from schemashift.snapshot_cmd import snapshot_cmd


_SCHEMA = pa.schema(
    [
        pa.field("id", pa.int64(), nullable=False),
        pa.field("value", pa.float64(), nullable=True),
    ]
)


def _run(args: list[str], schema: pa.Schema = _SCHEMA):
    runner = CliRunner(mix_stderr=False)
    with patch("schemashift.snapshot_cmd.read_schema", return_value=schema):
        return runner.invoke(snapshot_cmd, args, catch_exceptions=False)


class TestSnapshotCmd:
    def test_snapshot_saved_to_default_path(self, tmp_path: Path) -> None:
        result = _run([str(tmp_path / "users.parquet")])
        assert result.exit_code == 0
        assert "Snapshot saved" in result.output

    def test_snapshot_saved_to_explicit_output(self, tmp_path: Path) -> None:
        dest = tmp_path / "my_snap.json"
        result = _run(["users.parquet", "--output", str(dest)])
        assert result.exit_code == 0
        assert dest.exists()

    def test_output_is_valid_json(self, tmp_path: Path) -> None:
        dest = tmp_path / "snap.json"
        _run(["users.parquet", "-o", str(dest)])
        data = json.loads(dest.read_text())
        assert "fields" in data
        assert "captured_at" in data

    def test_field_count_in_output(self, tmp_path: Path) -> None:
        dest = tmp_path / "snap.json"
        result = _run(["users.parquet", "-o", str(dest)])
        assert "Fields  : 2" in result.output

    def test_read_schema_failure_shows_error(self) -> None:
        runner = CliRunner(mix_stderr=False)
        with patch(
            "schemashift.snapshot_cmd.read_schema",
            side_effect=FileNotFoundError("not found"),
        ):
            result = runner.invoke(snapshot_cmd, ["missing.parquet"])
        assert result.exit_code != 0
        assert "Failed to read schema" in result.output

    def test_save_failure_shows_error(self, tmp_path: Path) -> None:
        from schemashift.snapshot import SnapshotError

        runner = CliRunner(mix_stderr=False)
        with patch("schemashift.snapshot_cmd.read_schema", return_value=_SCHEMA), patch(
            "schemashift.snapshot_cmd.save_snapshot",
            side_effect=SnapshotError("disk full"),
        ):
            result = runner.invoke(snapshot_cmd, ["data.parquet"])
        assert result.exit_code != 0
        assert "disk full" in result.output
