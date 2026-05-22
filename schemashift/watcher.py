"""Schema watcher: poll a dataset path and emit diffs when the schema changes."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from schemashift.schema_reader import read_schema
from schemashift.schema_diff import SchemaDiff, diff_schemas, has_breaking_changes


@dataclass
class WatchEvent:
    """Emitted each time a schema change is detected."""

    path: Path
    previous_schema: object  # pyarrow.Schema
    current_schema: object   # pyarrow.Schema
    diff: SchemaDiff
    is_breaking: bool


@dataclass
class WatcherConfig:
    """Configuration for :func:`watch`."""

    path: Path
    interval_seconds: float = 5.0
    max_polls: Optional[int] = None  # None => run forever
    on_change: Callable[[WatchEvent], None] = field(
        default_factory=lambda: lambda e: None
    )


def watch(config: WatcherConfig) -> None:
    """Poll *config.path* and call *config.on_change* whenever the schema changes.

    Blocks until *config.max_polls* polls have been performed (or forever when
    *max_polls* is ``None``).
    """
    previous_schema = read_schema(config.path)
    polls = 0

    while config.max_polls is None or polls < config.max_polls:
        time.sleep(config.interval_seconds)
        polls += 1

        current_schema = read_schema(config.path)
        diff = diff_schemas(previous_schema, current_schema)

        if diff.removed or diff.added or diff.type_changed or diff.nullability_changed:
            event = WatchEvent(
                path=config.path,
                previous_schema=previous_schema,
                current_schema=current_schema,
                diff=diff,
                is_breaking=has_breaking_changes(diff),
            )
            config.on_change(event)
            previous_schema = current_schema
