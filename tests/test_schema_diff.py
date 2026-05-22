"""Tests for schemashift.schema_diff."""

import pyarrow as pa
import pytest

from schemashift.schema_diff import diff_schemas, SchemaDiff


def _schema(*fields):
    return pa.schema(fields)


class TestDiffSchemas:
    def test_identical_schemas_produce_empty_diff(self):
        schema = _schema(pa.field("id", pa.int64()), pa.field("name", pa.string()))
        diff = diff_schemas(schema, schema)
        assert diff.is_empty
        assert not diff.has_breaking_changes

    def test_detects_removed_column(self):
        old = _schema(pa.field("id", pa.int64()), pa.field("name", pa.string()))
        new = _schema(pa.field("id", pa.int64()))
        diff = diff_schemas(old, new)
        assert len(diff.removed) == 1
        assert diff.removed[0].name == "name"
        assert diff.has_breaking_changes

    def test_detects_added_column(self):
        old = _schema(pa.field("id", pa.int64()))
        new = _schema(pa.field("id", pa.int64()), pa.field("email", pa.string()))
        diff = diff_schemas(old, new)
        assert len(diff.added) == 1
        assert diff.added[0].name == "email"
        assert not diff.has_breaking_changes

    def test_detects_type_change(self):
        old = _schema(pa.field("score", pa.int32()))
        new = _schema(pa.field("score", pa.float64()))
        diff = diff_schemas(old, new)
        assert len(diff.type_changed) == 1
        entry = diff.type_changed[0]
        assert entry["name"] == "score"
        assert entry["old"] == pa.int32()
        assert entry["new"] == pa.float64()
        assert diff.has_breaking_changes

    def test_detects_nullable_change(self):
        old = _schema(pa.field("id", pa.int64(), nullable=False))
        new = _schema(pa.field("id", pa.int64(), nullable=True))
        diff = diff_schemas(old, new)
        assert len(diff.nullable_changed) == 1
        assert diff.nullable_changed[0]["name"] == "id"
        assert not diff.has_breaking_changes  # nullable change alone is non-breaking

    def test_multiple_changes_in_single_diff(self):
        old = _schema(
            pa.field("id", pa.int64()),
            pa.field("legacy", pa.string()),
            pa.field("score", pa.int32()),
        )
        new = _schema(
            pa.field("id", pa.int64()),
            pa.field("score", pa.float64()),
            pa.field("new_col", pa.bool_()),
        )
        diff = diff_schemas(old, new)
        assert len(diff.removed) == 1
        assert len(diff.type_changed) == 1
        assert len(diff.added) == 1
        assert diff.has_breaking_changes
