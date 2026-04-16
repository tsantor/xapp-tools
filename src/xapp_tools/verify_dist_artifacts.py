#!/usr/bin/env python3
"""Verify wheel and sdist build artifacts."""

from __future__ import annotations

import json
import sys
import tarfile
import zipfile
from email import message_from_string
from pathlib import Path

import click
from rich.console import Console

try:
    from xapp_tools.project_meta import resolve_package_metadata
except ModuleNotFoundError:
    from project_meta import resolve_package_metadata  # type: ignore[no-redef]

_err = Console(stderr=True)


def _latest_artifact(pattern: str, dist_dir: Path) -> Path:
    matches = sorted(dist_dir.glob(pattern))
    if not matches:
        msg = f"No artifact found matching: {dist_dir / pattern}"
        raise FileNotFoundError(msg)
    return matches[-1]


def _verify_wheel(
    wheel_path: Path, package_name: str, package_dir: str, package_version: str
) -> None:
    with zipfile.ZipFile(wheel_path, "r") as wheel:
        names = set(wheel.namelist())
        assert f"{package_dir}/__init__.py" in names

        dist_info_dir = next(
            name for name in names if name.endswith(".dist-info/METADATA")
        ).rsplit("/", maxsplit=1)[0]
        metadata_name = f"{dist_info_dir}/METADATA"
        metadata = message_from_string(wheel.read(metadata_name).decode("utf-8"))
        assert metadata["Name"] == package_name
        assert metadata["Version"] == package_version


def _verify_sdist(sdist_path: Path, package_dir: str) -> None:
    with tarfile.open(sdist_path, "r:gz") as sdist:
        names = set(sdist.getnames())
        assert any(name.endswith(f"src/{package_dir}/__init__.py") for name in names)
        assert any(name.endswith("pyproject.toml") for name in names)


def _verify_contract(wheel_path: Path, contract_file: Path) -> None:
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    modules = contract.get("modules", {})

    invalid = [mod for mod, syms in modules.items() if not syms]
    if invalid:
        for mod in invalid:
            _err.print(f"Invalid symbol list for contract module '{mod}'")
        sys.exit(1)

    failures: dict[str, list[str]] = {}
    with zipfile.ZipFile(wheel_path, "r") as wheel:
        for module, symbols in modules.items():
            file_path = module.replace(".", "/") + ".py"
            try:
                content = wheel.read(file_path).decode("utf-8")
            except KeyError:
                failures[module] = symbols
                continue
            missing = [s for s in symbols if s not in content]
            if missing:
                failures[module] = missing

    if failures:
        _err.print("Wheel contract symbol verification failed")
        for mod, missing in failures.items():
            _err.print(f"{mod}: missing symbols ({', '.join(missing)})")
        sys.exit(1)


@click.command("verify-dist")
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
    help="Version override (defaults to project.version in pyproject.toml).",
)
@click.option(
    "--dist-dir",
    default="dist",
    show_default=True,
    help="Directory containing built artifacts.",
)
@click.option(
    "--contract-file",
    default=None,
    type=click.Path(path_type=Path),
    help="Path to a JSON contract file for symbol verification.",
)
def main(
    package_name: str | None,
    package_dir: str | None,
    package_version: str | None,
    dist_dir: str,
    contract_file: Path | None,
) -> None:
    """Verify wheel and sdist build artifacts."""
    dist = Path(dist_dir)
    pkg_name, pkg_dir, pkg_version = resolve_package_metadata(
        package_name_override=package_name,
        package_dir_override=package_dir,
        package_version_override=package_version,
    )
    wheel_path = _latest_artifact("*.whl", dist)
    sdist_path = _latest_artifact("*.tar.gz", dist)
    _verify_wheel(wheel_path, pkg_name, pkg_dir, pkg_version)
    _verify_sdist(sdist_path, pkg_dir)
    if contract_file:
        _verify_contract(wheel_path, contract_file)


if __name__ == "__main__":
    main()
