"""Refresh dependency specifiers in pyproject.toml using uv add/remove.

This script updates project dependencies and all dependency groups dynamically.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import click

from xapp_tools.console import print_error
from xapp_tools.console import print_info
from xapp_tools.console import print_success
from xapp_tools.project_meta import load_pyproject_config
from xapp_tools.project_meta import resolve_package_metadata


def extract_package_name(dependency: str) -> str:
    """Extract base package name from a dependency string."""
    dep = dependency.split(";", maxsplit=1)[0].strip()
    match = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)", dep)
    if not match:
        msg = f"Could not parse package name from dependency: {dependency!r}"
        raise ValueError(msg)
    return match.group(1)


def build_uv_commands(
    pyproject: dict,
) -> list[tuple[str | None, str, list[str], list[str]]]:
    """Build uv remove/add command pairs for project deps and all dependency-groups."""
    commands: list[tuple[str | None, str, list[str], list[str]]] = []

    for dep in pyproject.get("project", {}).get("dependencies", []):
        package = extract_package_name(dep)
        commands.append(
            (None, package, ["uv", "remove", package], ["uv", "add", package])
        )

    groups = pyproject.get("dependency-groups", {})
    for group_name, deps in groups.items():
        for dep in deps:
            if isinstance(dep, dict):
                continue  # skip inline tables (path dependencies etc.)
            package = extract_package_name(dep)
            commands.append(
                (
                    group_name,
                    package,
                    ["uv", "remove", package, "--group", group_name],
                    ["uv", "add", package, "--group", group_name],
                )
            )

    return commands


def run_uv(cmd: list[str], dry_run: bool) -> int:
    """Run a uv command; return process returncode."""
    print_info(" ".join(cmd))
    if dry_run:
        return 0
    # Command is generated internally from pyproject dependencies.
    completed = subprocess.run(cmd, check=False)  # noqa: S603
    return completed.returncode


@click.command("update-deps")
@click.option(
    "--pyproject",
    default="pyproject.toml",
    show_default=True,
    help="Path to pyproject.toml.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Print uv commands without executing them.",
)
@click.option(
    "--package-name",
    default=None,
    help="Optional distribution name override for metadata validation.",
)
@click.option(
    "--package-dir",
    default=None,
    help="Optional import package override for metadata validation.",
)
def main(
    pyproject: str, dry_run: bool, package_name: str | None, package_dir: str | None
) -> None:
    """Refresh all dependencies in pyproject.toml to their latest versions."""
    pyproject_path = Path(pyproject)

    package_name_val, package_dir_val, _ = resolve_package_metadata(
        package_name_override=package_name,
        package_dir_override=package_dir,
        pyproject_path=pyproject_path,
    )
    print_info(
        f"Resolved project metadata: name=[bold]{package_name_val}[/bold], "
        f"package=[bold]{package_dir_val}[/bold]"
    )

    cfg = load_pyproject_config(pyproject_path)
    command_specs = build_uv_commands(cfg)
    if not command_specs:
        print_info("No dependencies found to update.")
        return

    failures: list[str] = []
    for group_name, package, remove_cmd, add_cmd in command_specs:
        scope = f"group:{group_name}" if group_name else "project"
        if run_uv(remove_cmd, dry_run) != 0:
            failures.append(f"{scope}:{package}: remove failed")
        if run_uv(add_cmd, dry_run) != 0:
            failures.append(f"{scope}:{package}: add failed")

    mode = "dry-run" if dry_run else "executed"
    print_info(f"Processed [bold]{len(command_specs)}[/bold] dependencies ({mode}).")

    if failures:
        print_error("Failures:")
        for item in failures:
            print_error(f"  - {item}")
        raise SystemExit(1)

    print_info("Dependency refresh completed successfully.")


if __name__ == "__main__":
    main()
