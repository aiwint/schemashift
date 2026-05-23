"""Tests for schemashift.profile_report."""

from __future__ import annotations

import json

import pyarrow as pa

from schemashift.profile import profile_table
from schemashift.profile_report import (
    format_profile_json,
    format_profile_markdown,
    format_profile_text,
)


def _make_profile():
    table = pa.table(
        {
            "id": pa.array([1, 2], type=pa.int64()),
            "label": pa.array(["a", None], type=pa.string()),
        }
    )
    return profile_table(table, "sample.parquet")


def test_text_contains_path():
    prof = _make_profile()
    output = format_profile_text(prof)
    assert "sample.parquet" in output


def test_text_contains_row_count():
    prof = _make_profile()
    output = format_profile_text(prof)
    assert "2" in output


def test_text_contains_field_names():
    prof = _make_profile()
    output = format_profile_text(prof)
    assert "id" in output
    assert "label" in output


def test_text_shows_null_percentage():
    prof = _make_profile()
    output = format_profile_text(prof)
    assert "50.0%" in output


def test_json_is_valid():
    prof = _make_profile()
    raw = format_profile_json(prof)
    data = json.loads(raw)
    assert data["row_count"] == 2
    assert len(data["fields"]) == 2


def test_json_null_rate():
    prof = _make_profile()
    raw = format_profile_json(prof)
    data = json.loads(raw)
    label = next(f for f in data["fields"] if f["name"] == "label")
    assert label["null_rate"] == 0.5


def test_markdown_has_table_header():
    prof = _make_profile()
    output = format_profile_markdown(prof)
    assert "| Field |" in output


def test_markdown_contains_field_rows():
    prof = _make_profile()
    output = format_profile_markdown(prof)
    assert "| id |" in output
    assert "| label |" in output


def test_markdown_heading_includes_path():
    prof = _make_profile()
    output = format_profile_markdown(prof)
    assert "sample.parquet" in output
