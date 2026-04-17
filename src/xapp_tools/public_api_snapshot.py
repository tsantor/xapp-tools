#!/usr/bin/env python
"""Generate or verify a package's public API contract."""

from __future__ import annotations

import importlib
import inspect
import json
import sys
from collections import defaultdict
from pathlib import Path

import click
from rich.console import Console

from xapp_tools.project_meta import resolve_package_metadata

_err = Console(stderr=True)


def build_snapshot(package_name: str) -> dict:
    pkg = importlib.import_module(package_name)
    all_names = getattr(pkg, "__all__", [])

    grouped: dict[str, list[str]] = defaultdict(list)
    for name in all_names:
        obj = getattr(pkg, name)
        module = inspect.getmodule(obj)
        module_name = module.__name__ if module else package_name
        grouped[module_name].append(name)

    return {"modules": {mod: sorted(names) for mod, names in sorted(grouped.items())}}


@click.command("api-snapshot")
@click.option(
    "--create",
    is_flag=True,
    help="Create the public API contract instead of verifying it.",
)
def main(create: bool) -> None:
    """Generate or verify the package's public API contract."""
    _, package, _ = resolve_package_metadata()
    snapshot = build_snapshot(package)
    snapshot_text = json.dumps(snapshot, indent=2) + "\n"

    output = Path("api/public_api.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(snapshot_text)

    contract_file = Path("api/public_api.contract.json")

    if create:
        contract_file.parent.mkdir(parents=True, exist_ok=True)
        contract_file.write_text(snapshot_text)
        click.echo(f"Contract updated: {contract_file}")
    else:
        if not contract_file.exists():
            _err.print(f"[red]Contract file not found:[/red] {contract_file}")
            sys.exit(1)
        contract_text = contract_file.read_text()
        if snapshot_text != contract_text:
            _err.print(
                "[red]Public API has changed.[/red] "
                "Run [bold]just api-snapshot[/bold] to update the contract."
            )
            _err.print(f"\nContract ({contract_file}):\n{contract_text}")
            _err.print(f"\nCurrent ({output}):\n{snapshot_text}")
            sys.exit(1)
        click.echo("Public API contract is up to date.")


if __name__ == "__main__":
    main()
