"""Tests for schemashift.report formatting utilities."""

from __future__ import annotations

import json
import io

import pyarrow as pa
import pytest

from schemashift.schema_diff import diff_schemas
from schemashift.report import (
    OutputFormat,
    format_text,
    format_json,
    format_markdown,
    render,
)


def _make_diff(old_fields, new_fields):
    old = pa.schema(old_fields)
    new = pa.schema(new_fields)
    return diff_schemas(old, new)


# ---------------------------------------------------------------------------
# format_text
# ---------------------------------------------------------------------------

class TestFormatText:
    def test_no_changes_message(self):
        diff = _make_diff(
            [("id", pa.int64())],
            [("id", pa.int64())],
        )
        out = format_text(diff)
        assert "No schema changes" in out

    def test_removed_field_marked_breaking(self):
        diff = _make_diff(
            [("id", pa.int64()), ("name", pa.string())],
            [("id", pa.int64())],
        )
        out = format_text(diff)
        assert "BREAKING" in out
        assert "name" in out

    def test_added_field_present(self):
        diff = _make_diff(
            [("id", pa.int64())],
            [("id", pa.int64()), ("score", pa.float64())],
        )
        out = format_text(diff)
        assert "score" in out
        assert "Added fields" in out

    def test_type_change_present(self):
        diff = _make_diff(
            [("value", pa.int32())],
            [("value", pa.int64())],
        )
        out = format_text(diff)
        assert "Type changes" in out
        assert "value" in out


# ---------------------------------------------------------------------------
# format_json
# ---------------------------------------------------------------------------

class TestFormatJson:
    def test_valid_json_output(self):
        diff = _make_diff([("id", pa.int64())], [("id", pa.int64())])
        raw = format_json(diff)
        data = json.loads(raw)
        assert "breaking" in data
        assert data["breaking"] is False

    def test_breaking_flag_true_on_removal(self):
        diff = _make_diff(
            [("id", pa.int64()), ("ts", pa.timestamp("ms"))],
            [("id", pa.int64())],
        )
        data = json.loads(format_json(diff))
        assert data["breaking"] is True
        assert any(f["name"] == "ts" for f in data["removed_fields"])

    def test_added_fields_in_json(self):
        diff = _make_diff(
            [("id", pa.int64())],
            [("id", pa.int64()), ("extra", pa.bool_())],
        )
        data = json.loads(format_json(diff))
        assert any(f["name"] == "extra" for f in data["added_fields"])


# ---------------------------------------------------------------------------
# format_markdown
# ---------------------------------------------------------------------------

class TestFormatMarkdown:
    def test_contains_heading(self):
        diff = _make_diff([("x", pa.int32())], [("x", pa.int32())])
        out = format_markdown(diff)
        assert "## Schema Diff" in out

    def test_breaking_badge(self):
        diff = _make_diff(
            [("col", pa.string())],
            [],
        )
        out = format_markdown(diff)
        assert "Breaking" in out

    def test_non_breaking_badge(self):
        diff = _make_diff(
            [("id", pa.int64())],
            [("id", pa.int64()), ("new_col", pa.float32())],
        )
        out = format_markdown(diff)
        assert "Non-breaking" in out


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------

def test_render_writes_to_stream():
    diff = _make_diff([("a", pa.int8())], [("a", pa.int8())])
    buf = io.StringIO()
    render(diff, fmt=OutputFormat.TEXT, out=buf)
    assert buf.getvalue().strip() != ""


def test_render_json_format():
    diff = _make_diff([("a", pa.int8())], [("b", pa.int8())])
    buf = io.StringIO()
    render(diff, fmt=OutputFormat.JSON, out=buf)
    data = json.loads(buf.getvalue())
    assert "breaking" in data
