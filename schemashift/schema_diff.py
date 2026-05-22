"""Compare two Arrow schemas and produce a structured diff report."""

from dataclasses import dataclass, field
from typing import List

import pyarrow as pa


@dataclass
class SchemaDiff:
    """Holds the result of comparing two schemas."""

    added: List[pa.Field] = field(default_factory=list)
    removed: List[pa.Field] = field(default_factory=list)
    type_changed: List[dict] = field(default_factory=list)  # {name, old, new}
    nullable_changed: List[dict] = field(default_factory=list)  # {name, old, new}

    @property
    def has_breaking_changes(self) -> bool:
        """Return True if any breaking changes were detected."""
        return bool(self.removed or self.type_changed)

    @property
    def is_empty(self) -> bool:
        """Return True when schemas are identical."""
        return not (self.added or self.removed or self.type_changed or self.nullable_changed)


def diff_schemas(old: pa.Schema, new: pa.Schema) -> SchemaDiff:
    """Compare *old* schema against *new* schema and return a SchemaDiff.

    Args:
        old: The baseline (previous) schema.
        new: The updated (current) schema.

    Returns:
        A SchemaDiff describing all detected changes.
    """
    result = SchemaDiff()

    old_fields = {f.name: f for f in old}
    new_fields = {f.name: f for f in new}

    for name, old_field in old_fields.items():
        if name not in new_fields:
            result.removed.append(old_field)
        else:
            new_field = new_fields[name]
            if old_field.type != new_field.type:
                result.type_changed.append(
                    {"name": name, "old": old_field.type, "new": new_field.type}
                )
            if old_field.nullable != new_field.nullable:
                result.nullable_changed.append(
                    {"name": name, "old": old_field.nullable, "new": new_field.nullable}
                )

    for name, new_field in new_fields.items():
        if name not in old_fields:
            result.added.append(new_field)

    return result
