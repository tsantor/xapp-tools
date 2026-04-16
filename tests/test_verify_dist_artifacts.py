import json
import tarfile
import zipfile
from pathlib import Path

from click.testing import CliRunner

from xapp_tools.cli import cli


def _write_contract(contract_file: Path, symbols: list[str]) -> None:
    contract_file.write_text(
        json.dumps({"modules": {"xapp_core.app": symbols}}, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_wheel(dist_dir: Path, *, version: str = "9.9.9") -> Path:
    wheel_path = dist_dir / f"xapp_core-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel_path, "w") as wheel:
        wheel.writestr("xapp_core/__init__.py", "__version__ = '9.9.9'\n")
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
        init_payload = b"__version__ = '9.9.9'\n"

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


def _run_verify(dist_dir: Path, contract_file: Path) -> object:
    runner = CliRunner()
    return runner.invoke(
        cli,
        [
            "verify-dist",
            "--dist-dir",
            str(dist_dir),
            "--package-name",
            "xapp-core",
            "--package-dir",
            "xapp_core",
            "--package-version",
            "9.9.9",
            "--contract-file",
            str(contract_file),
        ],
        catch_exceptions=False,
    )


def test_verify_dist_artifacts_passes_with_contract(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    contract_file = tmp_path / "contract.json"
    _write_contract(contract_file, ["CoreApp"])
    _write_wheel(dist_dir)
    _write_sdist(dist_dir)

    result = _run_verify(dist_dir, contract_file)

    assert result.exit_code == 0


def test_verify_dist_artifacts_fails_for_missing_symbol(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    contract_file = tmp_path / "contract.json"
    _write_contract(contract_file, ["CoreApp", "MissingSymbol"])
    _write_wheel(dist_dir)
    _write_sdist(dist_dir)

    result = _run_verify(dist_dir, contract_file)

    assert result.exit_code == 1
    assert "Wheel contract symbol verification failed" in result.output
    assert "xapp_core.app: missing symbols (MissingSymbol)" in result.output


def test_verify_dist_artifacts_fails_for_invalid_contract(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    contract_file = tmp_path / "contract.json"
    contract_file.write_text(json.dumps({"modules": {"xapp_core.app": []}}))
    _write_wheel(dist_dir)
    _write_sdist(dist_dir)

    result = _run_verify(dist_dir, contract_file)

    assert result.exit_code == 1
    assert "Invalid symbol list for contract module 'xapp_core.app'" in result.output
