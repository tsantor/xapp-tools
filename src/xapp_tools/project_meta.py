"""Resolve package metadata for reusable project scripts."""

from __future__ import annotations

import tomllib
from pathlib import Path


def load_pyproject_config(pyproject_path: Path = Path("pyproject.toml")) -> dict:
    """Load and return pyproject.toml as a dictionary."""
    if not pyproject_path.exists():
        msg = (
            f"Could not find {pyproject_path}. Pass explicit --package-name and "
            "--package-dir to continue."
        )
        raise FileNotFoundError(msg)
    with pyproject_path.open("rb") as f:
        return tomllib.load(f)


def _derive_package_dir(package_paths: list[str], pyproject_path: Path) -> str:
    if not package_paths:
        msg = (
            "No package paths found in tool.hatch.build.targets.wheel.packages. "
            "Pass --package-dir explicitly."
        )
        raise ValueError(msg)

    if len(package_paths) > 1:
        msg = (
            "Multiple package paths found in "
            f"{pyproject_path}: {package_paths}. Pass --package-dir explicitly."
        )
        raise ValueError(msg)

    path = package_paths[0].strip().rstrip("/\\")
    if not path:
        msg = "Detected empty package path. Pass --package-dir explicitly."
        raise ValueError(msg)
    return Path(path).name


def resolve_package_metadata(
    package_name_override: str | None = None,
    package_dir_override: str | None = None,
    package_version_override: str | None = None,
    pyproject_path: Path = Path("pyproject.toml"),
) -> tuple[str, str, str | None]:
    """Return (distribution_name, import_package_dir, version)."""
    cfg = load_pyproject_config(pyproject_path)

    project_name = package_name_override
    package_dir = package_dir_override
    package_version = package_version_override

    if not project_name:
        project_name = cfg.get("project", {}).get("name")
        if not project_name:
            msg = (
                "Could not resolve project.name from pyproject.toml. "
                "Pass --package-name explicitly."
            )
            raise ValueError(msg)

    if not package_dir:
        package_paths = (
            cfg.get("tool", {})
            .get("hatch", {})
            .get("build", {})
            .get("targets", {})
            .get("wheel", {})
            .get("packages", [])
        )
        package_dir = _derive_package_dir(package_paths, pyproject_path)

    if not package_version:
        package_version = cfg.get("project", {}).get("version") or None

    return project_name, package_dir, package_version
