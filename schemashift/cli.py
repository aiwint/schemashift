"""CLI entry-point for schemashift."""

from __future__ import annotations

import sys

import click

from schemashift.schema_reader import read_schema
from schemashift.schema_diff import diff_schemas, has_breaking_changes, is_empty
from schemashift.report import OutputFormat, render


@click.group()
def cli() -> None:
    """schemashift — detect and summarise breaking schema changes."""


@cli.command(name="diff")
@click.argument("old_file", type=click.Path(exists=True))
@click.argument("new_file", type=click.Path(exists=True))
@click.option(
    "--format",
    "fmt",
    type=click.Choice([f.value for f in OutputFormat], case_sensitive=False),
    default=OutputFormat.TEXT.value,
    show_default=True,
    help="Output format.",
)
@click.option(
    "--exit-code",
    is_flag=True,
    default=False,
    help="Exit with code 1 when breaking changes are detected.",
)
def diff_cmd(old_file: str, new_file: str, fmt: str, exit_code: bool) -> None:
    """Diff the schema of OLD_FILE against NEW_FILE."""
    try:
        old_schema = read_schema(old_file)
        new_schema = read_schema(new_file)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error reading schema: {exc}", err=True)
        sys.exit(2)

    diff = diff_schemas(old_schema, new_schema)
    render(diff, fmt=OutputFormat(fmt))

    if exit_code and has_breaking_changes(diff):
        sys.exit(1)
