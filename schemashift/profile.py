"""Schema profiling: collect field-level statistics from a dataset."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pyarrow as pa


class ProfileError(Exception):
    """Raised when profiling fails."""


@dataclass
class FieldProfile:
    name: str
    type: str
    nullable: bool
    null_count: int
    total_count: int

    @property
    def null_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.null_count / self.total_count


@dataclass
class SchemaProfile:
    path: str
    row_count: int
    fields: List[FieldProfile] = field(default_factory=list)

    def field_names(self) -> List[str]:
        return [f.name for f in self.fields]

    def get_field(self, name: str) -> Optional[FieldProfile]:
        for f in self.fields:
            if f.name == name:
                return f
        return None


def profile_table(table: pa.Table, path: str) -> SchemaProfile:
    """Build a SchemaProfile from an in-memory Arrow table."""
    row_count = table.num_rows
    fields: List[FieldProfile] = []

    for i, col_field in enumerate(table.schema):
        column = table.column(i)
        null_count = column.null_count
        fp = FieldProfile(
            name=col_field.name,
            type=str(col_field.type),
            nullable=col_field.nullable,
            null_count=null_count,
            total_count=row_count,
        )
        fields.append(fp)

    return SchemaProfile(path=path, row_count=row_count, fields=fields)


def profile_file(path: str) -> SchemaProfile:
    """Read a Parquet or Arrow file and return its SchemaProfile."""
    import pathlib

    suffix = pathlib.Path(path).suffix.lower()
    try:
        if suffix == ".parquet":
            import pyarrow.parquet as pq
            table = pq.read_table(path)
        elif suffix in (".arrow", ".ipc", ".feather"):
            import pyarrow.ipc as ipc
            with ipc.open_file(path) as reader:
                table = reader.read_all()
        else:
            raise ProfileError(f"Unsupported file format: {suffix!r}")
    except ProfileError:
        raise
    except Exception as exc:  # pragma: no cover
        raise ProfileError(f"Failed to profile {path!r}: {exc}") from exc

    return profile_table(table, path)
