"""CLI sub-command: export a schema diff to a file."""

from __future__ import annotations

from pathlib import Path

import click

from schemashift.schema_reader import read_schema
from schemashift.schema_diff import diff_schemas
from schemashift.exporter import export_diff, ExportError, ExportFormat


@click.command("export")
@click.argument("old_path", type=click.Path(exists=True, path_type=Path))
@click.argument("new_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output", "-o",
    required=True,
    type=click.Path(path_type=Path),
    help="Destination file for the exported report.",
)
@click.option(
    "--format", "fmt",
    type=click.Choice([f.value for f in ExportFormat], case_sensitive=False),
    default=ExportFormat.TEXT.value,
    show_default=True,
    help="Output format for the report.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite the output file if it already exists.",
)
def export_cmd(
    old_path: Path,
    new_path: Path,
    output: Path,
    fmt: str,
    overwrite: bool,
) -> None:
    """Export the schema diff between OLD_PATH and NEW_PATH to a file."""
    try:
        old_schema = read_schema(old_path)
        new_schema = read_schema(new_path)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(f"Failed to read schema: {exc}") from exc

    diff = diff_schemas(old_schema, new_schema)
    export_format = ExportFormat(fmt.lower())

    try:
        written = export_diff(diff, output, fmt=export_format, overwrite=overwrite)
    except ExportError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Report written to {written}")
