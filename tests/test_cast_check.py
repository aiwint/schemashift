"""Tests for schemashift.cast_check."""
from __future__ import annotations

import pyarrow as pa
import pytest

from schemashift.cast_check import CastSafety, check_casts
from schemashift.schema_diff import diff_schemas


def _schemas(old_fields, new_fields):
    return (
        pa.schema(old_fields),
        pa.schema(new_fields),
    )


class TestCheckCasts:
    def test_no_type_changes_returns_empty(self):
        old, new = _schemas(
            [("id", pa.int32())],
            [("id", pa.int32())],
        )
        result = check_casts(diff_schemas(old, new))
        assert result.issues == []
        assert not result.has_incompatible
        assert not result.has_narrowing

    def test_widening_int32_to_int64_is_safe(self):
        old, new = _schemas(
            [("val", pa.int32())],
            [("val", pa.int64())],
        )
        result = check_casts(diff_schemas(old, new))
        assert len(result.issues) == 1
        assert result.issues[0].safety == CastSafety.SAFE
        assert not result.has_incompatible

    def test_narrowing_int64_to_int32_is_narrowing(self):
        old, new = _schemas(
            [("val", pa.int64())],
            [("val", pa.int32())],
        )
        result = check_casts(diff_schemas(old, new))
        assert len(result.issues) == 1
        assert result.issues[0].safety == CastSafety.NARROWING
        assert result.has_narrowing
        assert not result.has_incompatible

    def test_string_to_int_is_incompatible(self):
        old, new = _schemas(
            [("label", pa.string())],
            [("label", pa.int32())],
        )
        result = check_casts(diff_schemas(old, new))
        assert len(result.issues) == 1
        assert result.issues[0].safety == CastSafety.INCOMPATIBLE
        assert result.has_incompatible

    def test_multiple_fields_reported_independently(self):
        old, new = _schemas(
            [("a", pa.int8()), ("b", pa.float32())],
            [("a", pa.int64()), ("b", pa.string())],
        )
        result = check_casts(diff_schemas(old, new))
        assert len(result.issues) == 2
        safeties = {i.field_name: i.safety for i in result.issues}
        assert safeties["a"] == CastSafety.SAFE
        assert safeties["b"] == CastSafety.INCOMPATIBLE

    def test_float32_to_float64_is_safe(self):
        old, new = _schemas(
            [("score", pa.float32())],
            [("score", pa.float64())],
        )
        result = check_casts(diff_schemas(old, new))
        assert result.issues[0].safety == CastSafety.SAFE
