"""Tests for schemashift.report."""

from __future__ import annotations

import json

import pyarrow as pa
import pytest

from schemashift.schema_diff import SchemaDiff
from schemashift.summarizer import DiffSummary, Severity
from schemashift.report import (
    OutputFormat,
    format_text,
    format_json,
    format_markdown,
    format_report,
)


def _make_diff(
    removed=(),
    added=(),
    type_changed=None,
    nullability_changed=None,
) -> SchemaDiff:
    return SchemaDiff(
        removed=list(removed),
        added=list(added),
        type_changed=type_changed or {},
        nullability_changed=nullability_changed or {},
    )


def _summary(severity=None, details=None) -> DiffSummary:
    return DiffSummary(severity=severity, details=details or [])


class TestFormatText:
    def test_no_changes_message(self):
        diff = _make_diff()
        summary = _summary()
        result = format_text(diff, summary)
        assert "No schema changes" in result

    def test_removed_field_marked_breaking(self):
        field = pa.field("old_col", pa.int32())
        diff = _make_diff(removed=[field])
        summary = _summary(severity=Severity.BREAKING, details=["Removed: old_col"])
        result = format_text(diff, summary)
        assert "old_col" in result
        assert "BREAKING" in result

    def test_added_field_present(self):
        field = pa.field("new_col", pa.string())
        diff = _make_diff(added=[field])
        summary = _summary(severity=Severity.INFO)
        result = format_text(diff, summary)
        assert "new_col" in result

    def test_type_change_shown(self):
        diff = _make_diff(type_changed={"col": (pa.int32(), pa.int64())})
        summary = _summary(severity=Severity.BREAKING)
        result = format_text(diff, summary)
        assert "col" in result
        assert "int32" in result
        assert "int64" in result

    def test_nullability_change_shown(self):
        diff = _make_diff(nullability_changed={"col": (True, False)})
        summary = _summary(severity=Severity.WARNING)
        result = format_text(diff, summary)
        assert "col" in result
        assert "nullable" in result


class TestFormatJson:
    def test_returns_valid_json(self):
        diff = _make_diff()
        summary = _summary()
        data = json.loads(format_json(diff, summary))
        assert "summary" in data

    def test_added_field_in_json(self):
        field = pa.field("score", pa.float64())
        diff = _make_diff(added=[field])
        summary = _summary(severity=Severity.INFO)
        data = json.loads(format_json(diff, summary))
        assert any(f["name"] == "score" for f in data["added"])

    def test_severity_in_summary(self):
        diff = _make_diff(removed=[pa.field("x", pa.int32())])
        summary = _summary(severity=Severity.BREAKING)
        data = json.loads(format_json(diff, summary))
        assert data["summary"]["severity"] == "breaking"


class TestFormatMarkdown:
    def test_contains_header(self):
        diff = _make_diff()
        summary = _summary()
        result = format_markdown(diff, summary)
        assert "## Schema Diff Report" in result

    def test_removed_field_in_markdown(self):
        field = pa.field("gone", pa.bool_())
        diff = _make_diff(removed=[field])
        summary = _summary(severity=Severity.BREAKING)
        result = format_markdown(diff, summary)
        assert "`gone`" in result


class TestFormatReport:
    def test_dispatches_to_json(self):
        diff = _make_diff()
        summary = _summary()
        result = format_report(diff, summary, OutputFormat.JSON)
        json.loads(result)  # must not raise

    def test_dispatches_to_markdown(self):
        diff = _make_diff()
        summary = _summary()
        result = format_report(diff, summary, OutputFormat.MARKDOWN)
        assert "#" in result

    def test_dispatches_to_text(self):
        diff = _make_diff()
        summary = _summary()
        result = format_report(diff, summary, OutputFormat.TEXT)
        assert "No schema changes" in result
