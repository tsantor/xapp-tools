from pathlib import Path

import pytest
from click.testing import CliRunner

from xapp_tools.cli import cli
from xapp_tools.version.version_bump import _compute_new_version


def _write_pyproject(path: Path, version: str) -> None:
    path.write_text(
        f'[project]\nname = "example"\nversion = "{version}"\n',
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# _compute_new_version
# ---------------------------------------------------------------------------


def test_compute_new_version_patch():
    assert _compute_new_version("1.2.3", "patch") == "1.2.4"


def test_compute_new_version_minor():
    assert _compute_new_version("1.2.3", "minor") == "1.3.0"


def test_compute_new_version_major():
    assert _compute_new_version("1.2.3", "major") == "2.0.0"


def test_compute_new_version_invalid_raises():
    with pytest.raises(ValueError, match=r"not strict X.Y.Z"):
        _compute_new_version("bad", "patch")


# ---------------------------------------------------------------------------
# version show
# ---------------------------------------------------------------------------


def test_version_show(tmp_path, monkeypatch):
    _write_pyproject(tmp_path / "pyproject.toml", "1.2.3")
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["version", "show"])
    assert result.exit_code == 0
    assert "1.2.3" in result.output


def test_version_show_missing_pyproject(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["version", "show"])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# version set
# ---------------------------------------------------------------------------


def test_version_set_valid(tmp_path, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    _write_pyproject(pyproject, "1.0.0")
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["version", "set", "2.0.0"])
    assert result.exit_code == 0
    assert "2.0.0" in pyproject.read_text(encoding="utf-8")


def test_version_set_invalid_format(tmp_path, monkeypatch):
    _write_pyproject(tmp_path / "pyproject.toml", "1.0.0")
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["version", "set", "bad"])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# version bump
# ---------------------------------------------------------------------------


def test_version_bump_patch(tmp_path, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    _write_pyproject(pyproject, "1.0.0")
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["version", "bump", "patch"])
    assert result.exit_code == 0
    assert "1.0.1" in pyproject.read_text(encoding="utf-8")


def test_version_bump_minor(tmp_path, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    _write_pyproject(pyproject, "1.0.0")
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["version", "bump", "minor"])
    assert result.exit_code == 0
    assert "1.1.0" in pyproject.read_text(encoding="utf-8")


def test_version_bump_major(tmp_path, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    _write_pyproject(pyproject, "1.0.0")
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["version", "bump", "major"])
    assert result.exit_code == 0
    assert "2.0.0" in pyproject.read_text(encoding="utf-8")
