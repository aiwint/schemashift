"""CLI sub-command: watch a dataset path for schema changes."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from schemashift.report import OutputFormat, format_report
from schemashift.summarizer import summarize, Severity
from schemashift.watcher import WatchEvent, WatcherConfig, watch


def _make_handler(fmt: OutputFormat, quiet: bool) -> "Callable[[WatchEvent], None]":
    def handler(event: WatchEvent) -> None:
        summary = summarize(event.diff)
        label = "[BREAKING] " if event.is_breaking else "[info] "
        click.echo(f"\n{label}Schema change detected in {event.path}")
        if not quiet:
            click.echo(format_report(event.diff, summary, fmt))
        if event.is_breaking:
            # Flush stderr so CI tools capture it immediately
            click.echo(
                f"Breaking change in {event.path}: {summary.summary}",
                file=sys.stderr,
            )

    return handler


@click.command("watch")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--interval",
    default=5.0,
    show_default=True,
    help="Poll interval in seconds.",
)
@click.option(
    "--max-polls",
    default=None,
    type=int,
    help="Stop after this many polls (omit for infinite).",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice([f.value for f in OutputFormat]),
    default=OutputFormat.TEXT.value,
    show_default=True,
)
@click.option("--quiet", is_flag=True, help="Only print the change header, not the diff.")
def watch_cmd(
    path: Path,
    interval: float,
    max_polls: int | None,
    output_format: str,
    quiet: bool,
) -> None:
    """Watch PATH and report schema changes as they occur."""
    fmt = OutputFormat(output_format)
    click.echo(f"Watching {path} every {interval}s …  (Ctrl-C to stop)")
    cfg = WatcherConfig(
        path=path,
        interval_seconds=interval,
        max_polls=max_polls,
        on_change=_make_handler(fmt, quiet),
    )
    try:
        watch(cfg)
    except KeyboardInterrupt:
        click.echo("\nStopped.")
