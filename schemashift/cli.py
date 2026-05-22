"""Entry-point for the schemashift CLI."""

from __future__ import annotations

from pathlib import Path

import click

from schemashift.report import OutputFormat, format_report
from schemashift.schema_diff import diff_schemas
from schemashift.schema_reader import read_schema
from schemashift.summarizer import summarize
from schemashift.watch_cmd import watch_cmd


@click.group()
def cli() -> None:
    """schemashift — detect and summarize breaking schema changes."""


@cli.command("diff")
@click.argument("old", type=click.Path(exists=True, path_type=Path))
@click.argument("new", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "output_format",
    type=click.Choice([f.value for f in OutputFormat]),
    default=OutputFormat.TEXT.value,
    show_default=True,
    help="Output format.",
)
@click.option(
    "--fail-on-breaking",
    is_flag=True,
    help="Exit with code 1 if breaking changes are detected.",
)
def diff_cmd(
    old: Path,
    new: Path,
    output_format: str,
    fail_on_breaking: bool,
) -> None:
    """Compare schemas of OLD and NEW datasets and report differences."""
    old_schema = read_schema(old)
    new_schema = read_schema(new)
    diff = diff_schemas(old_schema, new_schema)
    summary = summarize(diff)
    fmt = OutputFormat(output_format)
    click.echo(format_report(diff, summary, fmt))
    if fail_on_breaking and summary.is_breaking:
        raise SystemExit(1)


cli.add_command(watch_cmd)

if __name__ == "__main__":
    cli()
