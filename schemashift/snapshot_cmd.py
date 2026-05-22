"""CLI sub-command: schemashift snapshot — capture a schema snapshot."""

from __future__ import annotations

from pathlib import Path

import click

from schemashift.schema_reader import read_schema
from schemashift.snapshot import SnapshotError, make_snapshot, save_snapshot


@click.command("snapshot")
@click.argument("dataset", metavar="DATASET")
@click.option(
    "--output",
    "-o",
    default=None,
    show_default=True,
    help=(
        "Destination file for the snapshot JSON. "
        "Defaults to <dataset_stem>.snapshot.json in the current directory."
    ),
)
@click.pass_context
def snapshot_cmd(ctx: click.Context, dataset: str, output: str | None) -> None:
    """Capture a schema snapshot of DATASET and write it to disk.

    DATASET may be a local Parquet/Arrow file or a directory of Parquet files.
    """
    try:
        schema = read_schema(dataset)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(f"Failed to read schema from '{dataset}': {exc}") from exc

    dest = Path(output) if output else _default_output(dataset)

    snapshot = make_snapshot(dataset, schema)
    try:
        save_snapshot(snapshot, dest)
    except SnapshotError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Snapshot saved → {dest}")
    click.echo(f"  Dataset : {dataset}")
    click.echo(f"  Fields  : {len(schema)}")
    click.echo(f"  Captured: {snapshot.captured_at.isoformat()}")


def _default_output(dataset: str) -> Path:
    stem = Path(dataset).stem or "schema"
    return Path(f"{stem}.snapshot.json")
