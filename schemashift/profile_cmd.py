"""CLI command: schemashift profile <file>."""

from __future__ import annotations

import click

from schemashift.profile import ProfileError, profile_file
from schemashift.profile_report import (
    format_profile_json,
    format_profile_markdown,
    format_profile_text,
)


@click.command("profile")
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "markdown"], case_sensitive=False),
    default="text",
    show_default=True,
    help="Output format.",
)
def profile_cmd(file: str, output_format: str) -> None:
    """Display field-level statistics for FILE."""
    try:
        prof = profile_file(file)
    except ProfileError as exc:
        raise click.ClickException(str(exc)) from exc

    fmt = output_format.lower()
    if fmt == "json":
        output = format_profile_json(prof)
    elif fmt == "markdown":
        output = format_profile_markdown(prof)
    else:
        output = format_profile_text(prof)

    click.echo(output)
