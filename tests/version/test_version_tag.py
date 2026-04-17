from pathlib import Path
from types import SimpleNamespace

from click.testing import CliRunner

from xapp_tools.cli import cli
from xapp_tools.version.version_tag import _get_tag

_MOD = "xapp_tools.version.version_tag"


def _write_pyproject(path: Path, version: str) -> None:
    path.write_text(
        f'[project]\nname = "example"\nversion = "{version}"\n',
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# _get_tag
# ---------------------------------------------------------------------------


def test_get_tag(tmp_path):
    _write_pyproject(tmp_path / "pyproject.toml", "1.2.3")
    assert _get_tag(tmp_path / "pyproject.toml") == "v1.2.3"


# ---------------------------------------------------------------------------
# tag dryrun
# ---------------------------------------------------------------------------


def test_tag_dryrun_prints_tag(tmp_path, monkeypatch):
    _write_pyproject(tmp_path / "pyproject.toml", "1.0.0")
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["tag", "dryrun"])
    assert result.exit_code == 0
    assert "v1.0.0" in result.output


def test_tag_dryrun_missing_pyproject(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["tag", "dryrun"])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# tag create
# ---------------------------------------------------------------------------


def test_tag_create_fails_dirty_tree(tmp_path, monkeypatch, mocker):
    _write_pyproject(tmp_path / "pyproject.toml", "1.0.0")
    monkeypatch.chdir(tmp_path)
    mocker.patch(f"{_MOD}._is_tree_clean", return_value=False)
    result = CliRunner().invoke(cli, ["tag", "create"])
    assert result.exit_code == 1


def test_tag_create_fails_tag_already_exists(tmp_path, monkeypatch, mocker):
    _write_pyproject(tmp_path / "pyproject.toml", "1.0.0")
    monkeypatch.chdir(tmp_path)
    mocker.patch(f"{_MOD}._is_tree_clean", return_value=True)
    mocker.patch(f"{_MOD}._tag_exists", return_value=True)
    result = CliRunner().invoke(cli, ["tag", "create"])
    assert result.exit_code == 1
    assert "already exists" in result.output


def test_tag_create_succeeds(tmp_path, monkeypatch, mocker):
    _write_pyproject(tmp_path / "pyproject.toml", "1.0.0")
    monkeypatch.chdir(tmp_path)
    mocker.patch(f"{_MOD}._is_tree_clean", return_value=True)
    mocker.patch(f"{_MOD}._tag_exists", return_value=False)
    run = mocker.patch(
        f"{_MOD}.subprocess.run",
        return_value=SimpleNamespace(returncode=0),
    )
    result = CliRunner().invoke(cli, ["tag", "create"])
    assert result.exit_code == 0
    assert "Created tag v1.0.0" in result.output
    run.assert_called_once()
    assert run.call_args[0][0] == ["git", "tag", "-a", "v1.0.0", "-m", "Release v1.0.0"]


# ---------------------------------------------------------------------------
# tag push
# ---------------------------------------------------------------------------


def test_tag_push_fails_dirty_tree(tmp_path, monkeypatch, mocker):
    _write_pyproject(tmp_path / "pyproject.toml", "1.0.0")
    monkeypatch.chdir(tmp_path)
    mocker.patch(f"{_MOD}._is_tree_clean", return_value=False)
    result = CliRunner().invoke(cli, ["tag", "push"])
    assert result.exit_code == 1


def test_tag_push_fails_tag_not_local(tmp_path, monkeypatch, mocker):
    _write_pyproject(tmp_path / "pyproject.toml", "1.0.0")
    monkeypatch.chdir(tmp_path)
    mocker.patch(f"{_MOD}._is_tree_clean", return_value=True)
    mocker.patch(f"{_MOD}._tag_exists", return_value=False)
    result = CliRunner().invoke(cli, ["tag", "push"])
    assert result.exit_code == 1
    assert "does not exist locally" in result.output


def test_tag_push_succeeds(tmp_path, monkeypatch, mocker):
    _write_pyproject(tmp_path / "pyproject.toml", "1.0.0")
    monkeypatch.chdir(tmp_path)
    mocker.patch(f"{_MOD}._is_tree_clean", return_value=True)
    mocker.patch(f"{_MOD}._tag_exists", return_value=True)
    run = mocker.patch(
        f"{_MOD}.subprocess.run",
        return_value=SimpleNamespace(returncode=0),
    )
    result = CliRunner().invoke(cli, ["tag", "push"])
    assert result.exit_code == 0
    assert "Pushed tag v1.0.0" in result.output
    run.assert_called_once()
    assert run.call_args[0][0] == ["git", "push", "origin", "v1.0.0"]
