from pathlib import Path

import pytest

from xapp_tools.project_meta import load_pyproject_config
from xapp_tools.project_meta import resolve_package_metadata


def _write_pyproject(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_resolve_package_metadata_single_package(tmp_path):
    pyproject = _write_pyproject(
        tmp_path / "pyproject.toml",
        """
[project]
name = "example-dist"
version = "1.0.0"

[tool.hatch.build.targets.wheel]
packages = ["src/example_pkg"]
""".strip(),
    )
    name, package_dir, version = resolve_package_metadata(pyproject_path=pyproject)
    assert name == "example-dist"
    assert package_dir == "example_pkg"
    assert version == "1.0.0"


def test_resolve_package_metadata_override_takes_precedence(tmp_path):
    pyproject = _write_pyproject(
        tmp_path / "pyproject.toml",
        """
[project]
name = "example-dist"

[tool.hatch.build.targets.wheel]
packages = ["src/example_pkg"]
""".strip(),
    )
    name, package_dir, version = resolve_package_metadata(
        package_name_override="override-dist",
        package_dir_override="override_pkg",
        pyproject_path=pyproject,
    )
    assert name == "override-dist"
    assert package_dir == "override_pkg"
    assert version is None


def test_resolve_package_metadata_multi_package_requires_override(tmp_path):
    pyproject = _write_pyproject(
        tmp_path / "pyproject.toml",
        """
[project]
name = "example-dist"

[tool.hatch.build.targets.wheel]
packages = ["src/pkg_one", "src/pkg_two"]
""".strip(),
    )
    with pytest.raises(ValueError, match="Multiple package paths"):
        resolve_package_metadata(pyproject_path=pyproject)


def test_resolve_package_metadata_missing_project_name_requires_override(tmp_path):
    pyproject = _write_pyproject(
        tmp_path / "pyproject.toml",
        """
[tool.hatch.build.targets.wheel]
packages = ["src/example_pkg"]
""".strip(),
    )
    with pytest.raises(ValueError, match=r"project\.name"):
        resolve_package_metadata(pyproject_path=pyproject)


def test_load_pyproject_config_round_trip(tmp_path):
    pyproject = _write_pyproject(
        tmp_path / "pyproject.toml",
        """
[project]
name = "example-dist"
""".strip(),
    )
    cfg = load_pyproject_config(pyproject)
    assert cfg["project"]["name"] == "example-dist"
