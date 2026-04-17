"""Create and push git version tags derived from pyproject.toml."""

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


def _require_clean_tree(action: str) -> None:
    if not _is_tree_clean():
        noun = "tagging" if action == "create" else "pushing tags"
        print_error(
            f"Working tree is not clean. Commit or stash changes before {noun}."
        )
        raise SystemExit(1)


def _create_tag(tag: str) -> None:
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


def _push_tag(tag: str) -> None:
    if not _tag_exists(tag):
        print_error(
            f"Tag does not exist locally: {tag}. Run 'version-tag create' first."
        )
        raise SystemExit(1)
    result = subprocess.run(  # noqa: S603
        ["git", "push", "origin", tag],  # noqa: S607
        check=False,
    )
    if result.returncode != 0:
        print_error(f"Failed to push tag: {tag}")
        raise SystemExit(1)
    print_success(f"Pushed tag {tag}")


@click.command("version-tag")
@click.argument("action", type=click.Choice(["dryrun", "create", "push"]))
def main(action: str) -> None:
    """Manage git version tags derived from pyproject.toml.

    ACTION is one of: dryrun (print tag), create (annotated tag), push (push to origin).
    """
    try:
        tag = _get_tag(Path("pyproject.toml"))
    except (KeyError, FileNotFoundError) as e:
        print_error(str(e))
        raise SystemExit(1) from e

    if action == "dryrun":
        print_info(tag)
        return

    if not _TAG_RE.match(tag):
        print_error(f"Invalid tag format: {tag}")
        raise SystemExit(1)

    _require_clean_tree(action)

    if action == "create":
        _create_tag(tag)
    else:
        _push_tag(tag)


if __name__ == "__main__":
    main()
