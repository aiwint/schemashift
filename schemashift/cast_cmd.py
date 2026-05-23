"""CLI sub-command: cast-check — report unsafe type casts between two schemas."""
from __future__ import annotations

import sys

import click

from schemashift.cast_check import check_casts
from schemashift.cast_report import format_cast_json, format_cast_markdown, format_cast_text
from schemashift.schema_diff import diff_schemas
from schemashift.schema_reader import read_schema


@click.command("cast-check")
@click.argument("old_path", metavar="OLD")
@click.argument("new_path", metavar="NEW")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "markdown"], case_sensitive=False),
    default="text",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--fail-on-narrowing",
    is_flag=True,
    default=False,
    help="Exit with code 1 when narrowing casts are present.",
)
def cast_cmd(
    old_path: str,
    new_path: str,
    output_format: str,
    fail_on_narrowing: bool,
) -> None:
    """Check for unsafe type casts between OLD and NEW schemas."""
    old_schema = read_schema(old_path)
    new_schema = read_schema(new_path)
    diff = diff_schemas(old_schema, new_schema)
    result = check_casts(diff)

    fmt = output_format.lower()
    if fmt == "json":
        click.echo(format_cast_json(result))
    elif fmt == "markdown":
        click.echo(format_cast_markdown(result))
    else:
        click.echo(format_cast_text(result, path=new_path))

    if result.has_incompatible:
        sys.exit(1)
    if fail_on_narrowing and result.has_narrowing:
        sys.exit(1)
