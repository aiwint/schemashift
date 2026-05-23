"""Tests for schemashift.lint."""
from __future__ import annotations

import pyarrow as pa
import pytest

from schemashift.lint import (
    LintSeverity,
    lint_schema,
)


def _schema(*fields: pa.Field) -> pa.Schema:
    return pa.schema(list(fields))


# ---------------------------------------------------------------------------
# clean schema
# ---------------------------------------------------------------------------

def test_clean_schema_produces_no_issues():
    schema = _schema(
        pa.field("id", pa.int64(), nullable=False),
        pa.field("name", pa.string(), nullable=True),
    )
    result = lint_schema(schema)
    assert result.is_clean
    assert not result.has_errors
    assert not result.has_warnings


# ---------------------------------------------------------------------------
# empty / blank field names
# ---------------------------------------------------------------------------

def test_empty_field_name_is_error():
    schema = _schema(pa.field("", pa.int32()))
    result = lint_schema(schema)
    assert result.has_errors
    issue = result.issues[0]
    assert issue.severity == LintSeverity.ERROR
    assert "empty" in issue.message.lower()


# ---------------------------------------------------------------------------
# spaces in field names
# ---------------------------------------------------------------------------

def test_field_name_with_spaces_is_warning():
    schema = _schema(pa.field("my field", pa.string()))
    result = lint_schema(schema)
    assert result.has_warnings
    assert not result.has_errors
    assert any("spaces" in i.message.lower() for i in result.issues)


# ---------------------------------------------------------------------------
# duplicate field names
# ---------------------------------------------------------------------------

def test_duplicate_field_name_is_error():
    schema = _schema(
        pa.field("id", pa.int64()),
        pa.field("id", pa.string()),
    )
    result = lint_schema(schema)
    assert result.has_errors
    assert any("duplicate" in i.message.lower() for i in result.issues)


# ---------------------------------------------------------------------------
# large string / binary nullable warning
# ---------------------------------------------------------------------------

def test_nullable_large_string_is_warning():
    schema = _schema(pa.field("payload", pa.large_string(), nullable=True))
    result = lint_schema(schema)
    assert result.has_warnings
    assert any("large string" in i.message.lower() for i in result.issues)


def test_non_nullable_large_string_no_warning():
    schema = _schema(pa.field("payload", pa.large_string(), nullable=False))
    result = lint_schema(schema)
    # no large-string warning expected
    assert not any("large string" in i.message.lower() for i in result.issues)


# ---------------------------------------------------------------------------
# dictionary field without metadata
# ---------------------------------------------------------------------------

def test_dictionary_field_without_metadata_is_warning():
    dict_type = pa.dictionary(pa.int8(), pa.string())
    schema = _schema(pa.field("category", dict_type))
    result = lint_schema(schema)
    assert result.has_warnings
    assert any("dictionary" in i.message.lower() for i in result.issues)


# ---------------------------------------------------------------------------
# multiple issues accumulate
# ---------------------------------------------------------------------------

def test_multiple_issues_accumulate():
    schema = _schema(
        pa.field("my field", pa.large_string(), nullable=True),  # spaces + large nullable
    )
    result = lint_schema(schema)
    assert len(result.issues) >= 2
