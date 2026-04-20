import json
import tarfile
import zipfile
from pathlib import Path

from click.testing import CliRunner

from xapp_tools.cli import cli

_PYPROJECT = """\
[project]
name = "xapp-core"
version = "9.9.9"

[tool.hatch.build.targets.wheel]
packages = ["src/xapp_core"]
"""


def _setup_project(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT, encoding="utf-8")
    (tmp_path / "dist").mkdir()


def _write_contract(contract_file: Path, symbols: list[str]) -> None:
    contract_file.parent.mkdir(parents=True, exist_ok=True)
    contract_file.write_text(
        json.dumps({"modules": {"xapp_core.app": symbols}}, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_wheel(dist_dir: Path, *, version: str = "9.9.9") -> Path:
    wheel_path = dist_dir / f"xapp_core-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel_path, "w") as wheel:
        wheel.writestr("xapp_core/__init__.py", "")
        wheel.writestr("xapp_core/app.py", "class CoreApp:\n    pass\n")
        wheel.writestr(
            f"xapp_core-{version}.dist-info/METADATA",
            "Metadata-Version: 2.1\nName: xapp-core\nVersion: 9.9.9\n",
        )
    return wheel_path


def _write_sdist(dist_dir: Path, *, version: str = "9.9.9") -> Path:
    sdist_path = dist_dir / f"xapp_core-{version}.tar.gz"
    prefix = f"xapp_core-{version}"
    with tarfile.open(sdist_path, "w:gz") as sdist:
        pyproject_payload = b"[project]\nname = 'xapp-core'\nversion = '9.9.9'\n"
        pkg_info_payload = b"Metadata-Version: 2.1\nName: xapp-core\nVersion: 9.9.9\n"
        init_payload = b""

        pyproject_info = tarfile.TarInfo(name=f"{prefix}/pyproject.toml")
        pyproject_info.size = len(pyproject_payload)
        sdist.addfile(pyproject_info, fileobj=_BytesReader(pyproject_payload))

        pkg_info = tarfile.TarInfo(name=f"{prefix}/PKG-INFO")
        pkg_info.size = len(pkg_info_payload)
        sdist.addfile(pkg_info, fileobj=_BytesReader(pkg_info_payload))

        init_info = tarfile.TarInfo(name=f"{prefix}/src/xapp_core/__init__.py")
        init_info.size = len(init_payload)
        sdist.addfile(init_info, fileobj=_BytesReader(init_payload))
    return sdist_path


class _BytesReader:
    def __init__(self, data: bytes):
        self._data = data
        self._offset = 0

    def read(self, n: int = -1) -> bytes:
        if n < 0:
            n = len(self._data) - self._offset
        chunk = self._data[self._offset : self._offset + n]
        self._offset += len(chunk)
        return chunk


def _run_verify() -> object:
    runner = CliRunner()
    return runner.invoke(cli, ["dist", "verify"], catch_exceptions=False)


def test_verify_dist_artifacts_passes_with_contract(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    _setup_project(tmp_path)
    _write_wheel(tmp_path / "dist")
    _write_sdist(tmp_path / "dist")
    _write_contract(tmp_path / "api" / "public_api.contract.json", ["CoreApp"])

    result = _run_verify()

    assert result.exit_code == 0


def test_verify_dist_artifacts_fails_for_missing_symbol(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    _setup_project(tmp_path)
    _write_wheel(tmp_path / "dist")
    _write_sdist(tmp_path / "dist")
    _write_contract(
        tmp_path / "api" / "public_api.contract.json", ["CoreApp", "MissingSymbol"]
    )

    result = _run_verify()

    assert result.exit_code == 1
    assert "Wheel contract symbol verification failed" in result.output
    assert "xapp_core.app: missing symbols (MissingSymbol)" in result.output


def test_verify_dist_artifacts_fails_for_invalid_contract(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    _setup_project(tmp_path)
    _write_wheel(tmp_path / "dist")
    _write_sdist(tmp_path / "dist")
    contract = tmp_path / "api" / "public_api.contract.json"
    contract.parent.mkdir(parents=True, exist_ok=True)
    contract.write_text(json.dumps({"modules": {"xapp_core.app": []}}))

    result = _run_verify()

    assert result.exit_code == 1
    assert "Invalid symbol list for contract module 'xapp_core.app'" in result.output


def test_verify_dist_artifacts_passes_with_package_level_contract(
    tmp_path: Path, monkeypatch
) -> None:
    """Contract keyed on the package name resolves to __init__.py inside the wheel."""
    monkeypatch.chdir(tmp_path)
    _setup_project(tmp_path)

    # Wheel has xapp_core/__init__.py with a known symbol
    wheel_path = tmp_path / "dist" / "xapp_core-9.9.9-py3-none-any.whl"
    with zipfile.ZipFile(wheel_path, "w") as wheel:
        wheel.writestr("xapp_core/__init__.py", "def public_func(): pass\n")
        wheel.writestr(
            "xapp_core-9.9.9.dist-info/METADATA",
            "Metadata-Version: 2.1\nName: xapp-core\nVersion: 9.9.9\n",
        )
    _write_sdist(tmp_path / "dist")

    # Contract uses the package name (not a submodule) as the key
    contract = tmp_path / "api" / "public_api.contract.json"
    contract.parent.mkdir(parents=True, exist_ok=True)
    contract.write_text(
        json.dumps({"modules": {"xapp_core": ["public_func"]}}, indent=2) + "\n",
        encoding="utf-8",
    )

    result = _run_verify()

    assert result.exit_code == 0
