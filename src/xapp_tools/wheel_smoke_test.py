#!/usr/bin/env python3
"""Build artifact smoke test: install built wheel in a clean venv and import package."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console

try:
    from xapp_tools.project_meta import resolve_package_metadata
except ModuleNotFoundError:
    from project_meta import resolve_package_metadata  # type: ignore[no-redef]

_out = Console()


def run(cmd: list[str]) -> None:
    # Commands are constructed internally and not user supplied.
    subprocess.run(cmd, check=True)  # noqa: S603


def newest_wheel(dist_dir: Path) -> Path:
    wheels = sorted(
        dist_dir.glob("*.whl"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not wheels:
        msg = f"No wheel found in {dist_dir}. Run `just dist` first."
        raise FileNotFoundError(msg)
    return wheels[0]


@click.command("wheel-smoke")
@click.option(
    "--dist-dir",
    default="dist",
    show_default=True,
    help="Directory containing wheels.",
)
@click.option(
    "--venv-dir",
    default=".tmp/release-wheel-smoke",
    show_default=True,
    help="Temporary venv path.",
)
@click.option(
    "--package-name",
    default=None,
    help="Distribution name override (defaults to project.name in pyproject.toml).",
)
@click.option(
    "--package-dir",
    default=None,
    help="Import package override (defaults to Hatch wheel package path).",
)
@click.option(
    "--package-version",
    default=None,
    help="Package version override (defaults to project.version in pyproject.toml).",
)
def main(
    dist_dir: str,
    venv_dir: str,
    package_name: str | None,
    package_dir: str | None,
    package_version: str | None,
) -> None:
    """Install built wheel in a clean venv and verify the package imports."""
    dist = Path(dist_dir)
    venv = Path(venv_dir)
    _, pkg_dir, _ = resolve_package_metadata(
        package_name_override=package_name,
        package_dir_override=package_dir,
        package_version_override=package_version,
    )

    wheel = newest_wheel(dist)

    if venv.exists():
        shutil.rmtree(venv)

    run([sys.executable, "-m", "venv", str(venv)])

    if sys.platform == "win32":
        python_bin = venv / "Scripts" / "python"
        pip_bin = venv / "Scripts" / "pip"
    else:
        python_bin = venv / "bin" / "python"
        pip_bin = venv / "bin" / "pip"

    run([str(pip_bin), "install", "--upgrade", "pip"])
    run([str(pip_bin), "install", str(wheel)])

    run(
        [
            str(python_bin),
            "-c",
            f"from importlib.metadata import version; print(version('{package_name or pkg_dir}'))",
        ]
    )
    _out.print(f"[green]Wheel smoke test passed:[/green] {wheel.name}")


if __name__ == "__main__":
    main()
