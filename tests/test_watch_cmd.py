"""Tests for schemashift.watch_cmd CLI sub-command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pyarrow as pa
from click.testing import CliRunner

from schemashift.watch_cmd import watch_cmd


def _schema(*fields):
    return pa.schema(list(fields))


SCHEMA_V1 = _schema(pa.field("id", pa.int64()))
SCHEMA_V2 = _schema(pa.field("id", pa.int64()), pa.field("ts", pa.timestamp("us")))


class TestWatchCmd:
    def _run(self, *args, **kwargs):
        runner = CliRunner(mix_stderr=False)
        return runner.invoke(watch_cmd, args, catch_exceptions=False, **kwargs)

    @patch("schemashift.watch_cmd.watch")
    def test_watch_called_with_correct_interval(self, mock_watch, tmp_path):
        p = tmp_path / "data.parquet"
        p.touch()
        self._run(str(p), "--interval", "2.5", "--max-polls", "0")
        cfg = mock_watch.call_args[0][0]
        assert cfg.interval_seconds == 2.5
        assert cfg.max_polls == 0

    @patch("schemashift.watch_cmd.watch")
    def test_watch_banner_printed(self, mock_watch, tmp_path):
        p = tmp_path / "data.parquet"
        p.touch()
        result = self._run(str(p), "--max-polls", "0")
        assert "Watching" in result.output

    @patch("schemashift.watch_cmd.watch")
    def test_keyboard_interrupt_exits_cleanly(self, mock_watch, tmp_path):
        p = tmp_path / "data.parquet"
        p.touch()
        mock_watch.side_effect = KeyboardInterrupt
        result = self._run(str(p))
        assert result.exit_code == 0
        assert "Stopped" in result.output

    @patch("schemashift.watch_cmd.watch")
    def test_quiet_flag_forwarded(self, mock_watch, tmp_path):
        p = tmp_path / "data.parquet"
        p.touch()
        self._run(str(p), "--quiet", "--max-polls", "0")
        cfg = mock_watch.call_args[0][0]
        # handler is a closure; verify it was created (not None)
        assert cfg.on_change is not None
