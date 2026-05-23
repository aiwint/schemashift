"""Tests for schemashift.cast_report."""
from __future__ import annotations

import json

import pyarrow as pa
import pytest

from schemashift.cast_check import check_casts
from schemashift.cast_report import format_cast_json, format_cast_markdown, format_cast_text
from schemashift.schema_diff import diff_schemas


def _result_with_changes():
    old = pa.schema([("val", pa.int64()), ("label", pa.string())])
    new = pa.schema([("val", pa.int32()), ("label", pa.int32())])
    return check_casts(diff_schemas(old, new))


def _empty_result():
    s = pa.schema([("id", pa.int32())])
    return check_casts(diff_schemas(s, s))


class TestFormatCastText:
    def test_no_issues_shows_no_changes(self):
        out = format_cast_text(_empty_result())
        assert "No type changes" in out

    def test_path_appears_in_header(self):
        out = format_cast_text(_empty_result(), path="data/new.parquet")
        assert "data/new.parquet" in out

    def test_narrowing_shows_warning_icon(self):
        out = format_cast_text(_result_with_changes())
        assert "⚠" in out

    def test_incompatible_shows_cross_icon(self):
        out = format_cast_text(_result_with_changes())
        assert "✗" in out

    def test_field_name_present(self):
        out = format_cast_text(_result_with_changes())
        assert "val" in out
        assert "label" in out


class TestFormatCastJson:
    def test_returns_valid_json(self):
        out = format_cast_json(_result_with_changes())
        data = json.loads(out)
        assert "cast_issues" in data

    def test_issue_has_required_keys(self):
        out = format_cast_json(_result_with_changes())
        data = json.loads(out)
        issue = data["cast_issues"][0]
        assert {"field", "old_type", "new_type", "safety", "message"} <= issue.keys()

    def test_empty_result_has_empty_list(self):
        out = format_cast_json(_empty_result())
        data = json.loads(out)
        assert data["cast_issues"] == []


class TestFormatCastMarkdown:
    def test_contains_header(self):
        out = format_cast_markdown(_result_with_changes())
        assert "## Cast Check Report" in out

    def test_contains_table_header(self):
        out = format_cast_markdown(_result_with_changes())
        assert "| Field |" in out

    def test_no_issues_shows_no_changes_message(self):
        out = format_cast_markdown(_empty_result())
        assert "No type changes" in out
