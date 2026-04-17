from pathlib import Path

from xapp_tools.version.check_version_source import check_src


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_clean_source_passes(tmp_path):
    _write(tmp_path / "pkg/__init__.py", "import logging\n")
    assert check_src(tmp_path) == []


def test_hardcoded_version_flagged(tmp_path):
    _write(tmp_path / "pkg/__init__.py", '__version__ = "1.2.3"\n')
    violations = check_src(tmp_path)
    assert len(violations) == 1
    assert "1.2.3" in violations[0]
    assert "__version__" in violations[0]


def test_hardcoded_prerelease_version_flagged(tmp_path):
    _write(tmp_path / "pkg/__init__.py", "__version__ = '2.0.0a1'\n")
    violations = check_src(tmp_path)
    assert len(violations) == 1


def test_importlib_metadata_pattern_not_flagged(tmp_path):
    _write(
        tmp_path / "pkg/__init__.py",
        'from importlib.metadata import version\n__version__ = version("my-pkg")\n',
    )
    assert check_src(tmp_path) == []


def test_unknown_fallback_not_flagged(tmp_path):
    _write(
        tmp_path / "pkg/__init__.py",
        'except PackageNotFoundError:\n    __version__ = "unknown"\n',
    )
    assert check_src(tmp_path) == []


def test_multiple_files_all_checked(tmp_path):
    _write(tmp_path / "pkg/__init__.py", '__version__ = "1.0.0"\n')
    _write(tmp_path / "pkg/sub/module.py", '__version__ = "2.0.0"\n')
    violations = check_src(tmp_path)
    assert len(violations) == 2  # noqa: PLR2004
