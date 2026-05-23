"""Tests for schemashift.enum_report."""
from __future__ import annotations

import json

import pytest

from schemashift.enum_check import EnumCheckResult, EnumIssue
from schemashift.enum_report import (
    format_enum_text,
    format_enum_json,
    format_enum_markdown,
    format_enum,
)

PATH = "data/new.parquet"


def _result(*issues: EnumIssue) -> EnumCheckResult:
    return EnumCheckResult(issues=list(issues))


def _encoded_issue() -> EnumIssue:
    return EnumIssue("status", "string", "dictionary<values=string, indices=int8>", "encoded")


def _decoded_issue() -> EnumIssue:
    return EnumIssue("category", "dictionary<values=string, indices=int8>", "string", "decoded")


# ---------------------------------------------------------------------------
# text
# ---------------------------------------------------------------------------

def test_no_issues_shows_no_changes():
    out = format_enum_text(PATH, _result())
    assert "No dictionary encoding changes" in out


def test_path_appears_in_text_header():
    out = format_enum_text(PATH, _result())
    assert PATH in out


def test_encoded_issue_shows_encoded_tag():
    out = format_enum_text(PATH, _result(_encoded_issue()))
    assert "[ENCODED]" in out


def test_decoded_issue_shows_decoded_tag():
    out = format_enum_text(PATH, _result(_decoded_issue()))
    assert "[DECODED]" in out


# ---------------------------------------------------------------------------
# json
# ---------------------------------------------------------------------------

def test_json_output_is_valid():
    out = format_enum_json(PATH, _result(_encoded_issue()))
    data = json.loads(out)
    assert data["path"] == PATH
    assert len(data["issues"]) == 1


def test_json_empty_issues_list():
    out = format_enum_json(PATH, _result())
    data = json.loads(out)
    assert data["issues"] == []


def test_json_issue_has_direction_field():
    out = format_enum_json(PATH, _result(_encoded_issue()))
    data = json.loads(out)
    assert data["issues"][0]["direction"] == "encoded"


# ---------------------------------------------------------------------------
# markdown
# ---------------------------------------------------------------------------

def test_markdown_no_issues():
    out = format_enum_markdown(PATH, _result())
    assert "No dictionary encoding changes" in out


def test_markdown_table_header_present():
    out = format_enum_markdown(PATH, _result(_encoded_issue()))
    assert "| Field |" in out


# ---------------------------------------------------------------------------
# dispatch
# ---------------------------------------------------------------------------

def test_format_enum_dispatches_json():
    out = format_enum("json", PATH, _result())
    json.loads(out)  # must not raise


def test_format_enum_dispatches_markdown():
    out = format_enum("markdown", PATH, _result())
    assert "##" in out
