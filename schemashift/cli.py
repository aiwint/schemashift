"""Command-line interface for SchemaShift."""

import sys
from pathlib import Path

import click

from schemashift import __version__
from schemashift.schema_reader import read_schema
from schemashift.schema_diff import diff_schemas


@click.group()
@click.version_option(__version__, prog_name="schemashift")
def cli() -> None:
    """SchemaShift — detect and summarize breaking schema changes."""


@cli.command("diff")
@click.argument("old_file", type=click.Path(exists=True, path_type=Path))
@click.argument("new_file", type=click.Path(exists=True, path_type=Path))
@click.option("--strict", is_flag=True, help="Exit with code 1 if breaking changes found.")
def diff_cmd(old_file: Path, new_file: Path, strict: bool) -> None:
    """Compare schemas of OLD_FILE and NEW_FILE and report changes."""
    try:
        old_schema = read_schema(old_file)
        new_schema = read_schema(new_file)
    except (FileNotFoundError, ValueError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(2)

    diff = diff_schemas(old_schema, new_schema)

    if diff.is_empty:
        click.echo(click.style("✔ Schemas are identical.", fg="green"))
        return

    if diff.removed:
        click.echo(click.style("REMOVED columns (breaking):", fg="red", bold=True))
        for f in diff.removed:
            click.echo(f"  - {f.name}: {f.type}")

    if diff.type_changed:
        click.echo(click.style("TYPE CHANGES (breaking):", fg="red", bold=True))
        for c in diff.type_changed:
            click.echo(f"  ~ {c['name']}: {c['old']} → {c['new']}")

    if diff.nullable_changed:
        click.echo(click.style("NULLABILITY CHANGES:", fg="yellow", bold=True))
        for c in diff.nullable_changed:
            click.echo(f"  ~ {c['name']}: nullable={c['old']} → nullable={c['new']}")

    if diff.added:
        click.echo(click.style("ADDED columns:", fg="cyan", bold=True))
        for f in diff.added:
            click.echo(f"  + {f.name}: {f.type}")

    if strict and diff.has_breaking_changes:
        sys.exit(1)


if __name__ == "__main__":
    cli()
