"""Tests for schemashift.summarizer."""

import pyarrow as pa
import pytest

from schemashift.schema_diff import diff_schemas
from schemashift.summarizer import DiffSummary, Severity, summarize


def _diff(old_fields, new_fields):
    old = pa.schema(old_fields)
    new = pa.schema(new_fields)
    return diff_schemas(old, new)


class TestSummarize:
    def test_empty_diff_has_none_severity(self):
        diff = _diff(
            [("id", pa.int64()), ("name", pa.string())],
            [("id", pa.int64()), ("name", pa.string())],
        )
        summary = summarize(diff)
        assert summary.severity == Severity.NONE
        assert summary.total_changes == 0
        assert summary.breaking_count == 0
        assert "No schema changes" in summary.headline
        assert summary.detail is None

    def test_removed_field_is_breaking(self):
        diff = _diff(
            [("id", pa.int64()), ("name", pa.string())],
            [("id", pa.int64())],
        )
        summary = summarize(diff)
        assert summary.severity == Severity.BREAKING
        assert summary.removed_count == 1
        assert summary.breaking_count == 1
        assert "Breaking" in summary.headline
        assert summary.detail is not None
        assert "removed" in summary.detail

    def test_added_field_is_info(self):
        diff = _diff(
            [("id", pa.int64())],
            [("id", pa.int64()), ("email", pa.string())],
        )
        summary = summarize(diff)
        assert summary.severity in (Severity.INFO, Severity.WARNING)
        assert summary.added_count == 1
        assert summary.breaking_count == 0
        assert summary.detail is not None
        assert "added" in summary.detail

    def test_type_change_is_breaking(self):
        diff = _diff(
            [("score", pa.int32())],
            [("score", pa.float64())],
        )
        summary = summarize(diff)
        assert summary.severity == Severity.BREAKING
        assert summary.type_changed_count == 1
        assert summary.breaking_count == 1
        assert "type change" in summary.headline

    def test_total_changes_are_summed(self):
        diff = _diff(
            [("a", pa.int32()), ("b", pa.string())],
            [("a", pa.float32()), ("c", pa.bool_())],
        )
        summary = summarize(diff)
        # b removed, a type changed, c added
        assert summary.total_changes == 3
        assert summary.removed_count == 1
        assert summary.added_count == 1
        assert summary.type_changed_count == 1

    def test_summary_returns_dataclass_instance(self):
        diff = _diff([("x", pa.int8())], [("x", pa.int8())])
        result = summarize(diff)
        assert isinstance(result, DiffSummary)
