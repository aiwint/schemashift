"""Tests for overlap_check and overlap_report."""
from __future__ import annotations

import json

import pyarrow as pa
import pytest

from schemashift.overlap_check import (
    OverlapCheckResult,
    check_overlaps,
    has_overlaps,
)
from schemashift.overlap_report import (
    format_overlap_json,
    format_overlap_markdown,
    format_overlap_text,
)


def _old(*fields: pa.Field) -> pa.Schema:
    return pa.schema(list(fields))


def _new(*fields: pa.Field) -> pa.Schema:
    return pa.schema(list(fields))


# ---------------------------------------------------------------------------
# check_overlaps
# ---------------------------------------------------------------------------

def test_no_changes_returns_empty():
    old = _old(pa.field("user_id", pa.int32()), pa.field("name", pa.string()))
    new = _new(pa.field("user_id", pa.int32()), pa.field("name", pa.string()))
    result = check_overlaps(old, new, "old.parquet", "new.parquet")
    assert not has_overlaps(result)
    assert result.issues == []


def test_case_insensitive_collision_detected():
    old = _old(pa.field("UserID", pa.int32()))
    new = _new(pa.field("userid", pa.int32()))
    result = check_overlaps(old, new, "a", "b")
    assert has_overlaps(result)
    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.old_name == "UserID"
    assert issue.new_name == "userid"
    assert issue.is_exact


def test_exact_same_name_not_flagged():
    old = _old(pa.field("email", pa.string()))
    new = _new(pa.field("email", pa.string()))
    result = check_overlaps(old, new, "a", "b")
    assert not has_overlaps(result)


def test_multiple_collisions():
    old = _old(pa.field("FirstName", pa.string()), pa.field("LastName", pa.string()))
    new = _new(pa.field("firstname", pa.string()), pa.field("lastname", pa.string()))
    result = check_overlaps(old, new, "a", "b")
    assert len(result.issues) == 2


def test_completely_different_fields_no_overlap():
    old = _old(pa.field("alpha", pa.int64()))
    new = _new(pa.field("beta", pa.int64()))
    result = check_overlaps(old, new, "a", "b")
    assert not has_overlaps(result)


# ---------------------------------------------------------------------------
# format_overlap_text
# ---------------------------------------------------------------------------

def test_text_no_issues():
    old = _old(pa.field("id", pa.int32()))
    new = _new(pa.field("id", pa.int32()))
    result = check_overlaps(old, new, "old.parquet", "new.parquet")
    text = format_overlap_text(result)
    assert "No case-insensitive" in text


def test_text_shows_collision():
    old = _old(pa.field("Name", pa.string()))
    new = _new(pa.field("name", pa.string()))
    result = check_overlaps(old, new, "old.parquet", "new.parquet")
    text = format_overlap_text(result)
    assert "Name" in text
    assert "name" in text


# ---------------------------------------------------------------------------
# format_overlap_json
# ---------------------------------------------------------------------------

def test_json_structure():
    old = _old(pa.field("Score", pa.float64()))
    new = _new(pa.field("score", pa.float64()))
    result = check_overlaps(old, new, "a.parquet", "b.parquet")
    data = json.loads(format_overlap_json(result))
    assert data["path_old"] == "a.parquet"
    assert len(data["overlaps"]) == 1
    assert data["overlaps"][0]["old_name"] == "Score"


# ---------------------------------------------------------------------------
# format_overlap_markdown
# ---------------------------------------------------------------------------

def test_markdown_table_rendered():
    old = _old(pa.field("ID", pa.int64()))
    new = _new(pa.field("id", pa.int64()))
    result = check_overlaps(old, new, "a", "b")
    md = format_overlap_markdown(result)
    assert "| Old Name |" in md
    assert "`ID`" in md
    assert "`id`" in md
