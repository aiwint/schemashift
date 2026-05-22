"""Schema diffing logic for Parquet/Arrow schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import pyarrow as pa


@dataclass
class SchemaDiff:
    """Container for differences between two Arrow schemas."""

    removed_fields: List[pa.Field] = field(default_factory=list)
    added_fields: List[pa.Field] = field(default_factory=list)
    type_changes: Dict[str, Tuple[pa.DataType, pa.DataType]] = field(default_factory=dict)
    nullability_changes: Dict[str, Tuple[bool, bool]] = field(default_factory=dict)


def is_empty(diff: SchemaDiff) -> bool:
    """Return True when there are no detected changes."""
    return (
        not diff.removed_fields
        and not diff.added_fields
        and not diff.type_changes
        and not diff.nullability_changes
    )


def has_breaking_changes(diff: SchemaDiff) -> bool:
    """Return True when the diff contains at least one breaking change.

    Breaking changes are:
    - Removed fields
    - Type changes on existing fields
    """
    return bool(diff.removed_fields or diff.type_changes)


def diff_schemas(old: pa.Schema, new: pa.Schema) -> SchemaDiff:
    """Compare *old* schema against *new* schema and return a :class:`SchemaDiff`."""
    diff = SchemaDiff()

    old_fields: Dict[str, pa.Field] = {f.name: f for f in old}
    new_fields: Dict[str, pa.Field] = {f.name: f for f in new}

    # Removed fields — present in old but not new
    for name, f in old_fields.items():
        if name not in new_fields:
            diff.removed_fields.append(f)

    # Added fields — present in new but not old
    for name, f in new_fields.items():
        if name not in old_fields:
            diff.added_fields.append(f)

    # Changed fields — present in both
    for name in old_fields.keys() & new_fields.keys():
        old_f = old_fields[name]
        new_f = new_fields[name]

        if old_f.type != new_f.type:
            diff.type_changes[name] = (old_f.type, new_f.type)

        if old_f.nullable != new_f.nullable:
            diff.nullability_changes[name] = (old_f.nullable, new_f.nullable)

    return diff
