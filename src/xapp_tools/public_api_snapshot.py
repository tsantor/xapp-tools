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

from xapp_tools.console import print_error
from xapp_tools.console import print_success
from xapp_tools.project_meta import resolve_package_metadata


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
        print_success(f"Contract updated: {contract_file}")
    else:
        if not contract_file.exists():
            print_error(f"Contract file not found: {contract_file}")
            sys.exit(1)
        contract_text = contract_file.read_text()
        if snapshot_text != contract_text:
            print_error(
                "Public API has changed. "
                "Run [bold]just api-snapshot[/bold] to update the contract."
            )
            print_error(f"\nContract ({contract_file}):\n{contract_text}")
            print_error(f"\nCurrent ({output}):\n{snapshot_text}")
            sys.exit(1)
        print_success("Public API contract is up to date.")


if __name__ == "__main__":
    main()
