"""Tests for schemashift.enum_check."""
from __future__ import annotations

import pyarrow as pa
import pytest

from schemashift.schema_diff import diff_schemas
from schemashift.enum_check import check_enum_changes, has_issues, EnumIssue


def _old(*fields: pa.Field) -> pa.Schema:
    return pa.schema(list(fields))


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

STR_FIELD = pa.field("status", pa.string())
DICT_FIELD = pa.field("status", pa.dictionary(pa.int8(), pa.string()))
DICT_FIELD_INT32 = pa.field("status", pa.dictionary(pa.int32(), pa.string()))
INT_FIELD = pa.field("count", pa.int32())


def test_no_type_changes_returns_empty():
    old = pa.schema([STR_FIELD, INT_FIELD])
    new = pa.schema([STR_FIELD, INT_FIELD])
    diff = diff_schemas(old, new)
    result = check_enum_changes(diff)
    assert not has_issues(result)
    assert result.issues == []


def test_plain_to_dict_is_encoded():
    old = pa.schema([STR_FIELD])
    new = pa.schema([DICT_FIELD])
    diff = diff_schemas(old, new)
    result = check_enum_changes(diff)
    assert has_issues(result)
    assert len(result.issues) == 1
    assert result.issues[0].direction == "encoded"
    assert result.issues[0].field_name == "status"


def test_dict_to_plain_is_decoded():
    old = pa.schema([DICT_FIELD])
    new = pa.schema([STR_FIELD])
    diff = diff_schemas(old, new)
    result = check_enum_changes(diff)
    assert has_issues(result)
    assert result.issues[0].direction == "decoded"


def test_dict_index_type_change_is_type_changed():
    old = pa.schema([DICT_FIELD])
    new = pa.schema([DICT_FIELD_INT32])
    diff = diff_schemas(old, new)
    result = check_enum_changes(diff)
    assert has_issues(result)
    assert result.issues[0].direction == "type_changed"


def test_unrelated_type_change_not_flagged():
    old = pa.schema([pa.field("count", pa.int32())])
    new = pa.schema([pa.field("count", pa.int64())])
    diff = diff_schemas(old, new)
    result = check_enum_changes(diff)
    # int32 -> int64 is not dict-related; no enum issues
    assert not has_issues(result)


def test_issue_description_contains_field_name():
    old = pa.schema([STR_FIELD])
    new = pa.schema([DICT_FIELD])
    diff = diff_schemas(old, new)
    result = check_enum_changes(diff)
    assert "status" in result.issues[0].description
