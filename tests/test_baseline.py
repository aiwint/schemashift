"""Tests for schemashift.baseline."""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pytest

from schemashift.baseline import BaselineError, BaselineResult, compare_against_baseline
from schemashift.summarizer import Severity


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE_SCHEMA = pa.schema(
    [
        pa.field("id", pa.int64(), nullable=False),
        pa.field("name", pa.string(), nullable=True),
    ]
)


def _write_snapshot(path: Path, schema: pa.Schema) -> None:
    """Write a minimal snapshot JSON that load_snapshot can read."""
    fields = [
        {"name": f.name, "type": str(f.type), "nullable": f.nullable}
        for f in schema
    ]
    payload = {"schema": fields, "metadata": {}}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCompareAgainstBaseline:
    def test_identical_schemas_no_changes(self, tmp_path: Path) -> None:
        snap = tmp_path / "snap.json"
        _write_snapshot(snap, _BASE_SCHEMA)
        result = compare_against_baseline(_BASE_SCHEMA, snap)
        assert isinstance(result, BaselineResult)
        assert not result.has_changes
        assert result.summary.severity is None

    def test_added_column_detected(self, tmp_path: Path) -> None:
        snap = tmp_path / "snap.json"
        _write_snapshot(snap, _BASE_SCHEMA)
        new_schema = pa.schema(
            [
                pa.field("id", pa.int64(), nullable=False),
                pa.field("name", pa.string(), nullable=True),
                pa.field("email", pa.string(), nullable=True),
            ]
        )
        result = compare_against_baseline(new_schema, snap)
        assert result.has_changes
        assert result.summary.severity == Severity.INFO
        assert any(c.field_name == "email" for c in result.diff.added)

    def test_removed_column_is_breaking(self, tmp_path: Path) -> None:
        snap = tmp_path / "snap.json"
        _write_snapshot(snap, _BASE_SCHEMA)
        new_schema = pa.schema([pa.field("id", pa.int64(), nullable=False)])
        result = compare_against_baseline(new_schema, snap)
        assert result.has_changes
        assert result.summary.severity == Severity.BREAKING
        assert any(c.field_name == "name" for c in result.diff.removed)

    def test_missing_snapshot_raises_baseline_error(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist.json"
        with pytest.raises(BaselineError, match="Could not load baseline snapshot"):
            compare_against_baseline(_BASE_SCHEMA, missing)

    def test_result_stores_snapshot_path(self, tmp_path: Path) -> None:
        snap = tmp_path / "snap.json"
        _write_snapshot(snap, _BASE_SCHEMA)
        result = compare_against_baseline(_BASE_SCHEMA, snap)
        assert result.snapshot_path == snap

    def test_label_appears_in_error_message(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing.json"
        with pytest.raises(BaselineError, match="my-dataset"):
            compare_against_baseline(_BASE_SCHEMA, missing, label="my-dataset")
