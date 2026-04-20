#!/usr/bin/env python
"""Generate or verify a package's public API contract."""

from __future__ import annotations

import ast
import json
import sys
from collections import defaultdict
from pathlib import Path

import click

from xapp_tools.console import print_error
from xapp_tools.console import print_success
from xapp_tools.project_meta import resolve_package_metadata


def _find_init_source(package_name: str) -> Path:
    for candidate in [
        Path(f"src/{package_name}/__init__.py"),
        Path(f"{package_name}/__init__.py"),
    ]:
        if candidate.exists():
            return candidate
    msg = f"Cannot find __init__.py for package '{package_name}'"
    raise FileNotFoundError(msg)


def _extract_all(source: str) -> list[str]:
    """Extract __all__ from Python source via AST."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        return [
                            elt.value
                            for elt in node.value.elts
                            if isinstance(elt, ast.Constant)
                            and isinstance(elt.value, str)
                        ]
    return []


def _extract_import_sources(source: str, package_name: str) -> dict[str, str]:
    """Map symbol names to their source module from import statements in __init__.py."""
    tree = ast.parse(source)
    sources: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level > 0:
                mod = f"{package_name}.{node.module}" if node.module else package_name
            else:
                mod = node.module or ""
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                sources[name] = mod
    return sources


def _diff_snapshots(contract: dict, current: dict) -> list[str]:
    lines = []
    contract_mods = contract.get("modules", {})
    current_mods = current.get("modules", {})
    for mod in sorted(set(contract_mods) | set(current_mods)):
        removed = sorted(
            set(contract_mods.get(mod, [])) - set(current_mods.get(mod, []))
        )
        added = sorted(set(current_mods.get(mod, [])) - set(contract_mods.get(mod, [])))
        if removed:
            lines.append(f"  {mod}: removed {', '.join(removed)}")
        if added:
            lines.append(f"  {mod}: added {', '.join(added)}")
    return lines


def build_snapshot(init_path: Path, package_name: str) -> dict:
    init_content = init_path.read_text(encoding="utf-8")
    all_names = sorted(_extract_all(init_content))
    import_sources = _extract_import_sources(init_content, package_name)

    grouped: dict[str, list[str]] = defaultdict(list)
    grouped[package_name] = all_names
    for name in all_names:
        source_mod = import_sources.get(name)
        if source_mod and source_mod != package_name:
            grouped[source_mod].append(name)

    return {"modules": {mod: sorted(names) for mod, names in sorted(grouped.items())}}


@click.command("api-snapshot")
@click.option(
    "--create",
    is_flag=True,
    help="Create the public API contract instead of verifying it.",
)
def main(create: bool) -> None:
    """Create/verify the package's public API contract."""
    _, package, _ = resolve_package_metadata()
    init_path = _find_init_source(package)
    snapshot = build_snapshot(init_path, package)
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
            diff = _diff_snapshots(json.loads(contract_text), snapshot)
            print_error("Public API has changed:")
            for line in diff:
                print_error(line)
            print_error(
                "Run [bold]xapp-tools dist api-snapshot --create[/bold] to update the contract."
            )
            sys.exit(1)
        print_success("Public API contract is up to date.")


if __name__ == "__main__":
    main()
