"""CLI command: schemashift enum-check <old> <new>"""
from __future__ import annotations

import sys

import click

from schemashift.schema_reader import read_schema
from schemashift.schema_diff import diff_schemas
from schemashift.enum_check import check_enum_changes, has_issues
from schemashift.enum_report import format_enum


@click.command("enum-check")
@click.argument("old_path")
@click.argument("new_path")
@click.option(
    "--format",
    "fmt",
    default="text",
    type=click.Choice(["text", "json", "markdown"], case_sensitive=False),
    help="Output format.",
    show_default=True,
)
@click.option(
    "--fail-on-change",
    is_flag=True,
    default=False,
    help="Exit with code 1 if any encoding changes are detected.",
)
def enum_cmd(old_path: str, new_path: str, fmt: str, fail_on_change: bool) -> None:
    """Check for dictionary/categorical encoding changes between two datasets."""
    old_schema = read_schema(old_path)
    new_schema = read_schema(new_path)
    diff = diff_schemas(old_schema, new_schema)
    result = check_enum_changes(diff)
    click.echo(format_enum(fmt, new_path, result))
    if fail_on_change and has_issues(result):
        sys.exit(1)
