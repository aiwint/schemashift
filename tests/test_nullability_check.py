"""Tests for schemashift.nullability_check."""
import pyarrow as pa
import pytest

from schemashift.nullability_check import (
    NullabilityChange,
    check_nullability,
    has_breaking,
    has_issues,
)


def _old() -> pa.Schema:
    return pa.schema([
        pa.field("id", pa.int32(), nullable=False),
        pa.field("name", pa.string(), nullable=True),
        pa.field("score", pa.float64(), nullable=False),
    ])


def test_no_nullability_changes_returns_empty():
    schema = _old()
    result = check_nullability("data.parquet", schema, schema)
    assert not has_issues(result)
    assert not has_breaking(result)
    assert result.issues == []


def test_became_nullable_detected():
    old = _old()
    new = pa.schema([
        pa.field("id", pa.int32(), nullable=True),   # changed
        pa.field("name", pa.string(), nullable=True),
        pa.field("score", pa.float64(), nullable=False),
    ])
    result = check_nullability("data.parquet", old, new)
    assert has_issues(result)
    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.field_name == "id"
    assert issue.change == NullabilityChange.BECAME_NULLABLE
    assert not issue.is_breaking


def test_became_non_nullable_is_breaking():
    old = _old()
    new = pa.schema([
        pa.field("id", pa.int32(), nullable=False),
        pa.field("name", pa.string(), nullable=False),  # changed
        pa.field("score", pa.float64(), nullable=False),
    ])
    result = check_nullability("data.parquet", old, new)
    assert has_issues(result)
    assert has_breaking(result)
    issue = result.issues[0]
    assert issue.field_name == "name"
    assert issue.change == NullabilityChange.BECAME_NON_NULLABLE
    assert issue.is_breaking


def test_multiple_changes_detected():
    old = _old()
    new = pa.schema([
        pa.field("id", pa.int32(), nullable=True),    # became nullable
        pa.field("name", pa.string(), nullable=False), # became non-nullable
        pa.field("score", pa.float64(), nullable=False),
    ])
    result = check_nullability("data.parquet", old, new)
    assert len(result.issues) == 2
    names = {i.field_name for i in result.issues}
    assert names == {"id", "name"}
    assert has_breaking(result)


def test_added_and_removed_fields_ignored():
    old = pa.schema([pa.field("id", pa.int32(), nullable=False)])
    new = pa.schema([pa.field("name", pa.string(), nullable=True)])
    result = check_nullability("data.parquet", old, new)
    assert not has_issues(result)


def test_path_stored_in_result():
    schema = _old()
    result = check_nullability("some/path/file.parquet", schema, schema)
    assert result.path == "some/path/file.parquet"
