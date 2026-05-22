"""Tests for schemashift.watcher."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pyarrow as pa
import pytest

from schemashift.schema_diff import SchemaDiff
from schemashift.watcher import WatchEvent, WatcherConfig, watch


def _schema(*fields: pa.Field) -> pa.Schema:
    return pa.schema(list(fields))


SCHEMA_V1 = _schema(pa.field("id", pa.int64()), pa.field("name", pa.string()))
SCHEMA_V2 = _schema(
    pa.field("id", pa.int64()),
    pa.field("name", pa.string()),
    pa.field("email", pa.string()),
)
SCHEMA_V3 = _schema(pa.field("id", pa.int64()))  # 'name' removed — breaking


class TestWatch:
    def _make_config(self, side_effects, on_change, max_polls):
        cfg = WatcherConfig(
            path=Path("fake.parquet"),
            interval_seconds=0,
            max_polls=max_polls,
            on_change=on_change,
        )
        return cfg

    @patch("schemashift.watcher.time.sleep")
    @patch("schemashift.watcher.read_schema")
    def test_no_change_emits_no_event(self, mock_read, mock_sleep):
        mock_read.return_value = SCHEMA_V1
        events = []
        cfg = self._make_config(None, events.append, max_polls=3)
        watch(cfg)
        assert events == []
        assert mock_sleep.call_count == 3

    @patch("schemashift.watcher.time.sleep")
    @patch("schemashift.watcher.read_schema")
    def test_added_column_emits_event(self, mock_read, mock_sleep):
        mock_read.side_effect = [SCHEMA_V1, SCHEMA_V1, SCHEMA_V2]
        events = []
        cfg = self._make_config(None, events.append, max_polls=2)
        watch(cfg)
        assert len(events) == 1
        evt: WatchEvent = events[0]
        assert not evt.is_breaking
        assert "email" in {f.name for f in evt.diff.added}

    @patch("schemashift.watcher.time.sleep")
    @patch("schemashift.watcher.read_schema")
    def test_removed_column_is_breaking(self, mock_read, mock_sleep):
        mock_read.side_effect = [SCHEMA_V1, SCHEMA_V3]
        events = []
        cfg = self._make_config(None, events.append, max_polls=1)
        watch(cfg)
        assert len(events) == 1
        assert events[0].is_breaking
        assert "name" in {f.name for f in events[0].diff.removed}

    @patch("schemashift.watcher.time.sleep")
    @patch("schemashift.watcher.read_schema")
    def test_previous_schema_updated_after_change(self, mock_read, mock_sleep):
        mock_read.side_effect = [SCHEMA_V1, SCHEMA_V2, SCHEMA_V3]
        events = []
        cfg = self._make_config(None, events.append, max_polls=2)
        watch(cfg)
        assert len(events) == 2
        # Second event should compare V2 -> V3, not V1 -> V3
        removed_names = {f.name for f in events[1].diff.removed}
        assert "name" in removed_names
        assert "id" not in removed_names
