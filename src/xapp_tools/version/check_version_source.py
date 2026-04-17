#!/usr/bin/env python3

"""Ensure no hardcoded __version__ string is defined in the package source.

The version must be declared only in pyproject.toml. Runtime access is
expected to use importlib.metadata.version(), not a literal version string.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import click

from xapp_tools.console import print_error
from xapp_tools.console import print_success

# Matches __version__ = "1.0.2" or __version__ = '2.0.0a1' etc.
# Does NOT match __version__ = version(...) or __version__ = "unknown".
_HARDCODED_VERSION = re.compile(r'^\s*__version__\s*=\s*["\'](\d[^"\']*)["\']')


def check_src(src_dir: Path) -> list[str]:
    """Return a list of violation strings (path:line: content) found under src_dir."""
    violations = []
    for path in sorted(src_dir.rglob("*.py")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _HARDCODED_VERSION.search(line):
                violations.append(f"{path}:{lineno}: {line.strip()}")
    return violations


@click.command("check-version-source")
@click.option(
    "--src-dir",
    default="src",
    show_default=True,
    help="Package source directory to scan.",
)
def main(src_dir: str) -> None:
    """Ensure no hardcoded __version__ in package."""
    src = Path(src_dir)

    if not src.is_dir():
        print_error(f"Error: source directory not found: {src}")
        sys.exit(2)

    violations = check_src(src)
    if violations:
        print_error("Error: hardcoded __version__ found in package source:")
        for v in violations:
            print_error(f"  [yellow]{v}[/yellow]")
        print_error("[dim]Version must be declared only in pyproject.toml.[/dim]")
        sys.exit(1)

    print_success(f"OK: no hardcoded __version__ in {src}/")


if __name__ == "__main__":
    main()
