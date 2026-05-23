"""CLI command: compare two dataset files and report schema differences."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from schemashift.schema_reader import read_schema
from schemashift.schema_diff import diff_schemas
from schemashift.summarizer import summarize, Severity
from schemashift.report import format_report, OutputFormat


@click.command("compare")
@click.argument("baseline", type=click.Path(exists=True, dir_okay=False))
@click.argument("current", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--format",
    "output_format",
    type=click.Choice([f.value for f in OutputFormat], case_sensitive=False),
    default=OutputFormat.TEXT.value,
    show_default=True,
    help="Output format for the diff report.",
)
@click.option(
    "--breaking-only",
    is_flag=True,
    default=False,
    help="Exit with code 1 only when breaking changes are detected.",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    default=False,
    help="Suppress output; only use exit codes.",
)
def compare_cmd(
    baseline: str,
    current: str,
    output_format: str,
    breaking_only: bool,
    quiet: bool,
) -> None:
    """Compare schema of BASELINE and CURRENT dataset files."""
    baseline_schema = read_schema(Path(baseline))
    current_schema = read_schema(Path(current))

    diff = diff_schemas(baseline_schema, current_schema)
    summary = summarize(diff)

    fmt = OutputFormat(output_format)
    report = format_report(diff, summary, fmt)

    if not quiet:
        click.echo(report)

    if breaking_only and summary.severity == Severity.BREAKING:
        sys.exit(1)
    elif not breaking_only and summary.severity is not None:
        sys.exit(1)
