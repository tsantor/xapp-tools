"""Git tag management commands derived from pyproject.toml."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import click

from xapp_tools.console import print_error
from xapp_tools.console import print_info
from xapp_tools.console import print_success
from xapp_tools.project_meta import load_pyproject_config

_TAG_RE = re.compile(r"^v\d+\.\d+\.\d+$")


def _get_tag(pyproject_path: Path) -> str:
    cfg = load_pyproject_config(pyproject_path)
    version = cfg["project"]["version"]
    return "v" + version


def _is_tree_clean() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == ""


def _tag_exists(tag: str) -> bool:
    result = subprocess.run(  # noqa: S603
        ["git", "rev-parse", tag],  # noqa: S607
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _resolve_tag() -> str:
    try:
        tag = _get_tag(Path("pyproject.toml"))
    except (KeyError, FileNotFoundError) as e:
        print_error(str(e))
        raise SystemExit(1) from e
    if not _TAG_RE.match(tag):
        print_error(f"Invalid tag format: {tag}")
        raise SystemExit(1)
    return tag


def _require_clean_tree(verb: str) -> None:
    if not _is_tree_clean():
        print_error(
            f"Working tree is not clean. Commit or stash changes before {verb}."
        )
        raise SystemExit(1)


@click.command("dryrun")
def dryrun() -> None:
    """Print the git tag for the current version without creating it."""
    try:
        tag = _get_tag(Path("pyproject.toml"))
    except (KeyError, FileNotFoundError) as e:
        print_error(str(e))
        raise SystemExit(1) from e
    print_info(tag)


@click.command("create")
def create() -> None:
    """Create a local annotated git tag for the current version."""
    tag = _resolve_tag()
    _require_clean_tree("tagging")
    if _tag_exists(tag):
        print_error(f"Tag already exists: {tag}")
        raise SystemExit(1)
    result = subprocess.run(  # noqa: S603
        ["git", "tag", "-a", tag, "-m", f"Release {tag}"],  # noqa: S607
        check=False,
    )
    if result.returncode != 0:
        print_error(f"Failed to create tag: {tag}")
        raise SystemExit(1)
    print_success(f"Created tag {tag}")


@click.command("push")
def push() -> None:
    """Push the current version tag to origin."""
    tag = _resolve_tag()
    _require_clean_tree("pushing tags")
    if not _tag_exists(tag):
        print_error(f"Tag does not exist locally: {tag}. Run 'tag create' first.")
        raise SystemExit(1)
    result = subprocess.run(  # noqa: S603
        ["git", "push", "origin", tag],  # noqa: S607
        check=False,
    )
    if result.returncode != 0:
        print_error(f"Failed to push tag: {tag}")
        raise SystemExit(1)
    print_success(f"Pushed tag {tag}")
