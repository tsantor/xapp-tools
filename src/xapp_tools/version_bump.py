"""Version management commands for pyproject.toml."""

from __future__ import annotations

import re
from pathlib import Path

import click

from xapp_tools.console import print_error
from xapp_tools.console import print_info
from xapp_tools.console import print_success
from xapp_tools.project_meta import load_pyproject_config

_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _compute_new_version(version: str, bump_type: str) -> str:
    parts = version.split(".")
    parts_length = 3
    if len(parts) != parts_length or not all(p.isdigit() for p in parts):
        msg = f"Current version is not strict X.Y.Z: {version}"
        raise ValueError(msg)
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    if bump_type == "major":
        return str(major + 1) + ".0.0"
    if bump_type == "minor":
        return str(major) + "." + str(minor + 1) + ".0"
    return str(major) + "." + str(minor) + "." + str(patch + 1)


def _write_version(pyproject_path: Path, new_version: str) -> None:
    text = pyproject_path.read_text(encoding="utf-8")
    new_text, count = re.subn(
        r'^(version\s*=\s*")[^"]+(")$',
        r"\g<1>" + new_version + r"\g<2>",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        msg = "Could not update version in pyproject.toml"
        raise ValueError(msg)
    pyproject_path.write_text(new_text, encoding="utf-8")


@click.command("version-bump")
@click.argument("bump_type", type=click.Choice(["patch", "minor", "major"]))
def main(bump_type: str) -> None:
    """Bump the package version in pyproject.toml.

    BUMP_TYPE is one of: patch (X.Y.Z+1), minor (X.Y+1.0), major (X+1.0.0).
    """
    pyproject_path = Path("pyproject.toml")
    try:
        cfg = load_pyproject_config(pyproject_path)
        current = cfg["project"]["version"]
        new_version = _compute_new_version(current, bump_type)
        _write_version(pyproject_path, new_version)
        print_success(f"{current} → {new_version}")
    except (ValueError, KeyError, FileNotFoundError) as e:
        print_error(str(e))
        raise SystemExit(1) from e


@click.command("version-show")
def show() -> None:
    """Print the current package version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    try:
        cfg = load_pyproject_config(pyproject_path)
        print_info(cfg["project"]["version"])
    except (KeyError, FileNotFoundError) as e:
        print_error(str(e))
        raise SystemExit(1) from e


@click.command("version-set")
@click.argument("new_version")
def set_version(new_version: str) -> None:
    """Set the package version in pyproject.toml to NEW_VERSION (strict X.Y.Z)."""
    if not _VERSION_RE.match(new_version):
        print_error(f"Invalid version: {new_version}. Use X.Y.Z")
        raise SystemExit(1)
    pyproject_path = Path("pyproject.toml")
    try:
        _write_version(pyproject_path, new_version)
        print_success(new_version)
    except (ValueError, FileNotFoundError) as e:
        print_error(str(e))
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
