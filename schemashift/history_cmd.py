"""CLI command: schemashift history — show schema change history."""

from __future__ import annotations

from pathlib import Path

import click

from schemashift.history import load_history, HistoryError
from schemashift.schema_diff import has_breaking_changes
from schemashift.report import format_text


@click.command("history")
@click.argument("history_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--breaking-only",
    is_flag=True,
    default=False,
    help="Show only snapshots that introduced breaking changes.",
)
def history_cmd(history_dir: Path, breaking_only: bool) -> None:  # noqa: FBT001
    """Display a timeline of schema changes stored in HISTORY_DIR."""
    try:
        history = load_history(history_dir)
    except HistoryError as exc:
        raise click.ClickException(str(exc)) from exc

    if not history.entries:
        click.echo("No snapshots found in history directory.")
        return

    shown = 0
    for entry in history.entries:
        diff = entry.diff_from_previous
        if breaking_only and (diff is None or not has_breaking_changes(diff)):
            continue

        click.echo(f"\n{'=' * 60}")
        click.echo(f"Snapshot : {entry.snapshot.captured_at}")
        click.echo(f"Source   : {entry.snapshot.source}")

        if diff is None:
            click.echo("(initial snapshot — no previous baseline)")
        else:
            click.echo(format_text(diff))

        shown += 1

    if shown == 0:
        click.echo("No breaking changes found in history.")
