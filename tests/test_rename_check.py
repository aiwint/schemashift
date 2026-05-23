"""Tests for rename_check and rename_report."""
from __future__ import annotations

import json

import pyarrow as pa
import pytest

from schemashift.schema_diff import diff_schemas
from schemashift.rename_check import check_renames, RenameCandidate
from schemashift.rename_report import (
    format_rename_text,
    format_rename_json,
    format_rename_markdown,
)


def _old():
    return pa.schema([
        pa.field("id", pa.int64()),
        pa.field("user_name", pa.string()),
        pa.field("amount", pa.float64()),
    ])


def _new_renamed():
    """user_name -> username (same type, adjacent position)."""
    return pa.schema([
        pa.field("id", pa.int64()),
        pa.field("username", pa.string()),
        pa.field("amount", pa.float64()),
    ])


def _new_type_changed():
    """user_name removed, username added but with different type."""
    return pa.schema([
        pa.field("id", pa.int64()),
        pa.field("username", pa.int32()),
        pa.field("amount", pa.float64()),
    ])


# ---------------------------------------------------------------------------
# check_renames
# ---------------------------------------------------------------------------

class TestCheckRenames:
    def test_no_changes_returns_empty(self):
        schema = _old()
        diff = diff_schemas(schema, schema)
        result = check_renames(schema, schema, diff)
        assert not result.has_candidates

    def test_detects_simple_rename(self):
        old, new = _old(), _new_renamed()
        diff = diff_schemas(old, new)
        result = check_renames(old, new, diff)
        assert result.has_candidates
        assert len(result.candidates) == 1
        c = result.candidates[0]
        assert c.old_name == "user_name"
        assert c.new_name == "username"
        assert c.field_type == "string"
        assert 0.5 <= c.confidence <= 1.0

    def test_type_mismatch_not_a_candidate(self):
        old, new = _old(), _new_type_changed()
        diff = diff_schemas(old, new)
        result = check_renames(old, new, diff)
        assert not result.has_candidates

    def test_confidence_below_threshold_excluded(self):
        old, new = _old(), _new_renamed()
        diff = diff_schemas(old, new)
        result = check_renames(old, new, diff, min_confidence=0.99)
        # confidence for adjacent rename should be < 0.99 only if position differs;
        # here positions are identical so confidence == 1.0 — still included.
        # Force exclusion with an impossibly high threshold.
        result2 = check_renames(old, new, diff, min_confidence=1.01)
        assert not result2.has_candidates


# ---------------------------------------------------------------------------
# rename_report
# ---------------------------------------------------------------------------

def _make_result():
    old, new = _old(), _new_renamed()
    diff = diff_schemas(old, new)
    return check_renames(old, new, diff)


def test_text_no_candidates():
    from schemashift.rename_check import RenameCheckResult
    out = format_rename_text(RenameCheckResult(), path="data.parquet")
    assert "No rename candidates" in out


def test_text_shows_old_and_new_name():
    out = format_rename_text(_make_result(), path="data.parquet")
    assert "user_name" in out
    assert "username" in out
    assert "data.parquet" in out


def test_json_is_valid_and_contains_candidates():
    raw = format_rename_json(_make_result(), path="data.parquet")
    payload = json.loads(raw)
    assert payload["path"] == "data.parquet"
    assert len(payload["rename_candidates"]) == 1
    assert payload["rename_candidates"][0]["old_name"] == "user_name"


def test_markdown_contains_table_header():
    out = format_rename_markdown(_make_result())
    assert "| Old Name |" in out
    assert "`user_name`" in out
    assert "`username`" in out
