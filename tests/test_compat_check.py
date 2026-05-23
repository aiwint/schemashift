"""Tests for schemashift.compat_check."""
from __future__ import annotations

import pyarrow as pa
import pytest

from schemashift.compat_check import (
    CompatDirection,
    check_compat,
)


def _old():
    return pa.schema(
        [
            pa.field("id", pa.int32(), nullable=False),
            pa.field("name", pa.string(), nullable=True),
            pa.field("score", pa.float64(), nullable=True),
        ]
    )


def _new_added_nullable():
    return pa.schema(
        [
            pa.field("id", pa.int32(), nullable=False),
            pa.field("name", pa.string(), nullable=True),
            pa.field("score", pa.float64(), nullable=True),
            pa.field("tag", pa.string(), nullable=True),
        ]
    )


def _new_added_non_nullable():
    return pa.schema(
        [
            pa.field("id", pa.int32(), nullable=False),
            pa.field("name", pa.string(), nullable=True),
            pa.field("score", pa.float64(), nullable=True),
            pa.field("required", pa.int64(), nullable=False),
        ]
    )


def _new_removed_field():
    return pa.schema(
        [
            pa.field("id", pa.int32(), nullable=False),
            pa.field("name", pa.string(), nullable=True),
        ]
    )


def _new_type_changed():
    return pa.schema(
        [
            pa.field("id", pa.int64(), nullable=False),
            pa.field("name", pa.string(), nullable=True),
            pa.field("score", pa.float64(), nullable=True),
        ]
    )


def test_identical_schemas_are_fully_compatible():
    result = check_compat(_old(), _old(), CompatDirection.FULL)
    assert result.is_compatible
    assert result.issues == []


def test_added_nullable_field_is_fully_compatible():
    result = check_compat(_old(), _new_added_nullable(), CompatDirection.FULL)
    assert result.is_compatible


def test_added_non_nullable_field_breaks_backward_compat():
    result = check_compat(_old(), _new_added_non_nullable(), CompatDirection.BACKWARD)
    assert not result.is_compatible
    assert len(result.issues) == 1
    assert result.issues[0].field_name == "required"


def test_added_non_nullable_does_not_break_forward_compat():
    result = check_compat(_old(), _new_added_non_nullable(), CompatDirection.FORWARD)
    assert result.is_compatible


def test_removed_field_breaks_forward_compat():
    result = check_compat(_old(), _new_removed_field(), CompatDirection.FORWARD)
    assert not result.is_compatible
    field_names = [i.field_name for i in result.issues]
    assert "score" in field_names


def test_removed_field_does_not_break_backward_compat():
    result = check_compat(_old(), _new_removed_field(), CompatDirection.BACKWARD)
    assert result.is_compatible


def test_type_change_breaks_forward_compat():
    result = check_compat(_old(), _new_type_changed(), CompatDirection.FORWARD)
    assert not result.is_compatible
    assert any(i.field_name == "id" for i in result.issues)


def test_full_direction_catches_both_issue_types():
    schema_with_both = pa.schema(
        [
            pa.field("id", pa.int32(), nullable=False),
            pa.field("new_required", pa.string(), nullable=False),
        ]
    )
    result = check_compat(_old(), schema_with_both, CompatDirection.FULL)
    directions = {i.direction for i in result.issues}
    assert CompatDirection.FORWARD in directions   # removed name, score
    assert CompatDirection.BACKWARD in directions  # added non-nullable
