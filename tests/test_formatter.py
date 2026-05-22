"""Tests for schemashift.formatter."""

from __future__ import annotations

import pyarrow as pa
import pytest

from schemashift.formatter import (
    diff_table,
    field_summary,
    format_diff_table_text,
    schema_table,
)


# ---------------------------------------------------------------------------
# field_summary
# ---------------------------------------------------------------------------

def test_field_summary_nullable():
    f = pa.field("age", pa.int32(), nullable=True)
    assert field_summary(f) == "age: int32 (nullable)"


def test_field_summary_not_nullable():
    f = pa.field("id", pa.int64(), nullable=False)
    assert field_summary(f) == "id: int64 (not nullable)"


# ---------------------------------------------------------------------------
# schema_table
# ---------------------------------------------------------------------------

def test_schema_table_returns_correct_rows():
    schema = pa.schema([
        pa.field("name", pa.string(), nullable=True),
        pa.field("score", pa.float64(), nullable=False),
    ])
    rows = schema_table(schema)
    assert rows == [
        ("name", "string", "yes"),
        ("score", "double", "no"),
    ]


def test_schema_table_empty_schema():
    assert schema_table(pa.schema([])) == []


# ---------------------------------------------------------------------------
# diff_table
# ---------------------------------------------------------------------------

def test_diff_table_removed():
    f = pa.field("old_col", pa.int32())
    rows = diff_table(removed=[f], added=[], type_changed=[], nullability_changed=[])
    assert rows == [("REMOVED", "old_col", "int32")]


def test_diff_table_added():
    f = pa.field("new_col", pa.string())
    rows = diff_table(removed=[], added=[f], type_changed=[], nullability_changed=[])
    assert rows == [("ADDED", "new_col", "string")]


def test_diff_table_type_changed():
    old = pa.field("amount", pa.int32())
    new = pa.field("amount", pa.float64())
    rows = diff_table(removed=[], added=[], type_changed=[(old, new)], nullability_changed=[])
    assert rows == [("TYPE_CHANGED", "amount", "int32 -> double")]


def test_diff_table_nullability_changed():
    old = pa.field("flag", pa.bool_(), nullable=False)
    new = pa.field("flag", pa.bool_(), nullable=True)
    rows = diff_table(removed=[], added=[], type_changed=[], nullability_changed=[(old, new)])
    assert rows == [("NULLABILITY_CHANGED", "flag", "not nullable -> nullable")]


def test_diff_table_empty():
    assert diff_table([], [], [], []) == []


# ---------------------------------------------------------------------------
# format_diff_table_text
# ---------------------------------------------------------------------------

def test_format_diff_table_text_no_changes():
    assert format_diff_table_text([]) == "No changes detected."


def test_format_diff_table_text_contains_headers():
    rows = [("REMOVED", "col_a", "int32")]
    output = format_diff_table_text(rows)
    assert "Change" in output
    assert "Field" in output
    assert "Detail" in output


def test_format_diff_table_text_contains_row_data():
    rows = [("ADDED", "new_field", "string")]
    output = format_diff_table_text(rows)
    assert "ADDED" in output
    assert "new_field" in output
    assert "string" in output
