"""Tests for schemashift.exporter."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

import pyarrow as pa

from schemashift.schema_diff import diff_schemas
from schemashift.exporter import export_diff, ExportError, ExportFormat


def _make_diff():
    old = pa.schema([pa.field("id", pa.int64()), pa.field("name", pa.string())])
    new = pa.schema([pa.field("id", pa.int64()), pa.field("email", pa.string())])
    return diff_schemas(old, new)


class TestExportDiff:
    def test_writes_text_file(self, tmp_path):
        diff = _make_diff()
        out = tmp_path / "report.txt"
        result = export_diff(diff, out, fmt=ExportFormat.TEXT)
        assert result == out.resolve()
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert len(content) > 0

    def test_writes_json_file(self, tmp_path):
        diff = _make_diff()
        out = tmp_path / "report.json"
        export_diff(diff, out, fmt=ExportFormat.JSON)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_writes_markdown_file(self, tmp_path):
        diff = _make_diff()
        out = tmp_path / "report.md"
        export_diff(diff, out, fmt=ExportFormat.MARKDOWN)
        content = out.read_text(encoding="utf-8")
        assert "##" in content or "#" in content or len(content) > 0

    def test_raises_on_existing_file_without_overwrite(self, tmp_path):
        diff = _make_diff()
        out = tmp_path / "report.txt"
        out.write_text("existing", encoding="utf-8")
        with pytest.raises(ExportError, match="already exists"):
            export_diff(diff, out, fmt=ExportFormat.TEXT, overwrite=False)

    def test_overwrites_existing_file_when_flag_set(self, tmp_path):
        diff = _make_diff()
        out = tmp_path / "report.txt"
        out.write_text("old content", encoding="utf-8")
        export_diff(diff, out, fmt=ExportFormat.TEXT, overwrite=True)
        assert out.read_text(encoding="utf-8") != "old content"

    def test_returns_resolved_path(self, tmp_path):
        diff = _make_diff()
        out = tmp_path / "report.txt"
        result = export_diff(diff, out)
        assert result.is_absolute()
