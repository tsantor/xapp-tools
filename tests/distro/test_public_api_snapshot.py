import json
from pathlib import Path

from click.testing import CliRunner

from xapp_tools.cli import cli
from xapp_tools.distro.public_api_snapshot import _diff_snapshots
from xapp_tools.distro.public_api_snapshot import _extract_all
from xapp_tools.distro.public_api_snapshot import _extract_import_sources
from xapp_tools.distro.public_api_snapshot import build_snapshot

_PYPROJECT = """\
[project]
name = "mypkg"
version = "1.0.0"

[tool.hatch.build.targets.wheel]
packages = ["src/mypkg"]
"""


def _write_init(src_dir: Path, package_name: str, init_src: str) -> Path:
    pkg_dir = src_dir / package_name
    pkg_dir.mkdir(parents=True, exist_ok=True)
    init_path = pkg_dir / "__init__.py"
    init_path.write_text(init_src, encoding="utf-8")
    return init_path


# --- _diff_snapshots ---


def test_diff_snapshots_removed():
    contract = {"modules": {"pkg": ["foo", "bar"]}}
    current = {"modules": {"pkg": ["foo"]}}
    assert _diff_snapshots(contract, current) == ["  pkg: removed bar"]


def test_diff_snapshots_added():
    contract = {"modules": {"pkg": ["foo"]}}
    current = {"modules": {"pkg": ["foo", "bar"]}}
    assert _diff_snapshots(contract, current) == ["  pkg: added bar"]


def test_diff_snapshots_removed_module():
    contract = {"modules": {"pkg": ["foo"], "pkg.sub": ["foo"]}}
    current = {"modules": {"pkg": []}}
    lines = _diff_snapshots(contract, current)
    assert "  pkg: removed foo" in lines
    assert "  pkg.sub: removed foo" in lines


def test_diff_snapshots_no_change():
    snap = {"modules": {"pkg": ["foo", "bar"]}}
    assert _diff_snapshots(snap, snap) == []


# --- _extract_all ---


def test_extract_all_list():
    assert _extract_all('__all__ = ["Foo", "bar"]\n') == ["Foo", "bar"]


def test_extract_all_tuple():
    assert _extract_all('__all__ = ("Alpha", "Beta")\n') == ["Alpha", "Beta"]


def test_extract_all_empty():
    assert _extract_all("__all__ = []\n") == []


def test_extract_all_missing():
    assert _extract_all("def foo(): pass\n") == []


def test_extract_all_multiline():
    src = '__all__ = [\n    "Foo",\n    "bar",\n    "baz",\n]\n'
    assert _extract_all(src) == ["Foo", "bar", "baz"]


def test_extract_all_defined_after_imports():
    src = 'from .sub import Foo\nfrom .other import bar\n__all__ = ["Foo", "bar"]\n'
    assert _extract_all(src) == ["Foo", "bar"]


# --- _extract_import_sources ---


def test_extract_import_sources_relative():
    src = "from .cpu import get_cpu_info\nfrom .net import get_net_info\n"
    sources = _extract_import_sources(src, "pkg")
    assert sources["get_cpu_info"] == "pkg.cpu"
    assert sources["get_net_info"] == "pkg.net"


def test_extract_import_sources_alias():
    src = "from .cpu import _impl as get_cpu_info\n"
    assert _extract_import_sources(src, "pkg")["get_cpu_info"] == "pkg.cpu"


def test_extract_import_sources_bare_relative():
    src = "from . import helper\n"
    assert _extract_import_sources(src, "pkg")["helper"] == "pkg"


# --- build_snapshot ---


def test_build_snapshot_top_level_entry(tmp_path):
    init = _write_init(
        tmp_path, "mypkg", '__all__ = ["Foo", "bar"]\nfrom .sub import Foo, bar\n'
    )
    result = build_snapshot(init, "mypkg")
    assert result["modules"]["mypkg"] == ["Foo", "bar"]


def test_build_snapshot_source_module_entries(tmp_path):
    init = _write_init(
        tmp_path, "mypkg", '__all__ = ["Foo", "bar"]\nfrom .sub import Foo, bar\n'
    )
    result = build_snapshot(init, "mypkg")
    assert result["modules"]["mypkg.sub"] == ["Foo", "bar"]


def test_build_snapshot_init_defined_symbols_not_duplicated(tmp_path):
    init = _write_init(tmp_path, "mypkg", '__all__ = ["inline"]\ndef inline(): pass\n')
    result = build_snapshot(init, "mypkg")
    assert list(result["modules"].keys()) == ["mypkg"]


def test_build_snapshot_empty_all(tmp_path):
    init = _write_init(tmp_path, "mypkg", "__all__ = []\n")
    result = build_snapshot(init, "mypkg")
    assert result == {"modules": {"mypkg": []}}


def test_build_snapshot_multiline_all_with_submodules(tmp_path):
    src = (
        "from .cpu import get_cpu_info\n"
        "from .mem import get_mem_info\n"
        "__all__ = [\n"
        '    "get_cpu_info",\n'
        '    "get_mem_info",\n'
        "]\n"
    )
    init = _write_init(tmp_path, "mypkg", src)
    result = build_snapshot(init, "mypkg")
    assert result["modules"]["mypkg"] == ["get_cpu_info", "get_mem_info"]
    assert result["modules"]["mypkg.cpu"] == ["get_cpu_info"]
    assert result["modules"]["mypkg.mem"] == ["get_mem_info"]


# --- CLI integration ---


def _setup(tmp_path: Path, init_src: str) -> None:
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT)
    _write_init(tmp_path / "src", "mypkg", init_src)


def test_api_snapshot_create(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup(tmp_path, '__all__ = ["MyClass"]\nfrom .core import MyClass\n')

    result = CliRunner().invoke(
        cli, ["dist", "api-snapshot", "--create"], catch_exceptions=False
    )

    assert result.exit_code == 0
    contract = json.loads((tmp_path / "api" / "public_api.contract.json").read_text())
    assert contract["modules"]["mypkg"] == ["MyClass"]
    assert contract["modules"]["mypkg.core"] == ["MyClass"]


def test_api_snapshot_verify_passes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup(tmp_path, '__all__ = ["MyClass"]\nfrom .core import MyClass\n')

    runner = CliRunner()
    runner.invoke(cli, ["dist", "api-snapshot", "--create"], catch_exceptions=False)
    result = runner.invoke(cli, ["dist", "api-snapshot"], catch_exceptions=False)

    assert result.exit_code == 0


def test_api_snapshot_verify_fails_on_removed_export(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT)

    # Create contract with two exports
    _write_init(
        tmp_path / "src",
        "mypkg",
        '__all__ = ["MyClass", "helper"]\nfrom .core import MyClass, helper\n',
    )
    runner = CliRunner()
    runner.invoke(cli, ["dist", "api-snapshot", "--create"], catch_exceptions=False)

    # Remove one export from source directly (no rebuild needed)
    _write_init(
        tmp_path / "src", "mypkg", '__all__ = ["MyClass"]\nfrom .core import MyClass\n'
    )

    result = runner.invoke(cli, ["dist", "api-snapshot"], catch_exceptions=False)

    assert result.exit_code == 1
    assert "Public API has changed" in result.output
    assert "mypkg: removed helper" in result.output
    assert "mypkg.core: removed helper" in result.output
