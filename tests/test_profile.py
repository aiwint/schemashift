"""Tests for schemashift.profile."""

from __future__ import annotations

import pyarrow as pa
import pytest

from schemashift.profile import (
    FieldProfile,
    ProfileError,
    SchemaProfile,
    profile_table,
)


def _make_table() -> pa.Table:
    return pa.table(
        {
            "id": pa.array([1, 2, 3], type=pa.int64()),
            "name": pa.array(["alice", None, "carol"], type=pa.string()),
            "score": pa.array([9.5, 8.0, None], type=pa.float64()),
        }
    )


def test_profile_table_row_count():
    table = _make_table()
    prof = profile_table(table, "dummy.parquet")
    assert prof.row_count == 3


def test_profile_table_field_names():
    table = _make_table()
    prof = profile_table(table, "dummy.parquet")
    assert prof.field_names() == ["id", "name", "score"]


def test_profile_table_null_counts():
    table = _make_table()
    prof = profile_table(table, "dummy.parquet")
    assert prof.get_field("id").null_count == 0
    assert prof.get_field("name").null_count == 1
    assert prof.get_field("score").null_count == 1


def test_null_rate_calculation():
    fp = FieldProfile(
        name="x", type="int64", nullable=True, null_count=1, total_count=4
    )
    assert fp.null_rate == 0.25


def test_null_rate_zero_rows():
    fp = FieldProfile(
        name="x", type="int64", nullable=True, null_count=0, total_count=0
    )
    assert fp.null_rate == 0.0


def test_get_field_missing_returns_none():
    table = _make_table()
    prof = profile_table(table, "dummy.parquet")
    assert prof.get_field("nonexistent") is None


def test_profile_file_unsupported_format(tmp_path):
    bad = tmp_path / "data.csv"
    bad.write_text("a,b\n1,2\n")
    from schemashift.profile import profile_file

    with pytest.raises(ProfileError, match="Unsupported file format"):
        profile_file(str(bad))


def test_profile_file_parquet_round_trip(tmp_path):
    import pyarrow.parquet as pq
    from schemashift.profile import profile_file

    table = _make_table()
    path = tmp_path / "data.parquet"
    pq.write_table(table, str(path))
    prof = profile_file(str(path))
    assert prof.row_count == 3
    assert len(prof.fields) == 3
