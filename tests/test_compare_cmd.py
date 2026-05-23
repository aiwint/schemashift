"""Tests for the compare CLI command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pyarrow as pa
import pytest
from click.testing import CliRunner

from schemashift.compare_cmd import compare_cmd
from schemashift.schema_diff import SchemaDiff
from schemashift.summarizer import DiffSummary, Severity


_SCHEMA_A = pa.schema([
    pa.field("id", pa.int64(), nullable=False),
    pa.field("name", pa.string()),
])

_SCHEMA_B = pa.schema([
    pa.field("id", pa.int64(), nullable=False),
    pa.field("name", pa.string()),
    pa.field("email", pa.string()),
])


def _run(args, read_side_effect):
    runner = CliRunner()
    with patch("schemashift.compare_cmd.read_schema", side_effect=read_side_effect):
        return runner.invoke(compare_cmd, args, catch_exceptions=False)


def test_identical_schemas_exits_zero():
    result = _run(
        ["baseline.parquet", "current.parquet"],
        [_SCHEMA_A, _SCHEMA_A],
    )
    assert result.exit_code == 0


def test_added_column_exits_nonzero():
    result = _run(
        ["baseline.parquet", "current.parquet"],
        [_SCHEMA_A, _SCHEMA_B],
    )
    assert result.exit_code == 1


def test_breaking_only_flag_no_exit_on_info_change():
    """Added column is INFO, so --breaking-only should not trigger exit 1."""
    result = _run(
        ["baseline.parquet", "current.parquet", "--breaking-only"],
        [_SCHEMA_A, _SCHEMA_B],
    )
    assert result.exit_code == 0


def test_output_contains_field_name():
    result = _run(
        ["baseline.parquet", "current.parquet"],
        [_SCHEMA_A, _SCHEMA_B],
    )
    assert "email" in result.output


def test_quiet_flag_suppresses_output():
    result = _run(
        ["baseline.parquet", "current.parquet", "--quiet"],
        [_SCHEMA_A, _SCHEMA_A],
    )
    assert result.output.strip() == ""


def test_json_format_produces_valid_output():
    import json
    result = _run(
        ["baseline.parquet", "current.parquet", "--format", "json"],
        [_SCHEMA_A, _SCHEMA_B],
    )
    data = json.loads(result.output)
    assert "added" in data or "removed" in data or "summary" in data
