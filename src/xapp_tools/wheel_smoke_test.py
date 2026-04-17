#!/usr/bin/env python3
"""Build artifact smoke test: install built wheel in a clean venv and import package."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import click

from xapp_tools.console import print_success
from xapp_tools.project_meta import resolve_package_metadata


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
def main() -> None:
    """Install built wheel in a clean venv and verify the package imports."""
    dist = Path("dist")
    venv = Path(".tmp/release-wheel-smoke")

    pkg_name, pkg_dir, _ = resolve_package_metadata()

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
            f"from importlib.metadata import version; print(version('{pkg_name or pkg_dir}'))",
        ]
    )
    print_success(f"Wheel smoke test passed: {wheel.name}")


if __name__ == "__main__":
    main()
