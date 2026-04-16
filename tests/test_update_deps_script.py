import pytest

import xapp_tools.update_deps as _update_deps_module
from xapp_tools.update_deps import build_uv_commands, extract_package_name, run_uv


def test_extract_package_name_variants():
    assert extract_package_name("click>=8.3.2") == "click"
    assert extract_package_name("pytest-cov==7.0.0") == "pytest-cov"
    assert extract_package_name("requests[socks]>=2.0") == "requests"
    assert (
        extract_package_name("pkg @ git+https://example.com/repo.git") == "pkg"
    )


def test_build_uv_commands_dynamic_groups():
    pyproject = {
        "project": {"dependencies": ["click>=8.3.2"]},
        "dependency-groups": {
            "dev": ["ruff>=0.14.9"],
            "test": ["pytest>=9.0.3"],
            "docs": ["mkdocs>=1.6.0"],
        },
    }
    commands = build_uv_commands(pyproject)
    assert (
        None,
        "click",
        ["uv", "remove", "click"],
        ["uv", "add", "click"],
    ) in commands
    assert (
        "dev",
        "ruff",
        ["uv", "remove", "ruff", "--group", "dev"],
        ["uv", "add", "ruff", "--group", "dev"],
    ) in commands
    assert (
        "docs",
        "mkdocs",
        ["uv", "remove", "mkdocs", "--group", "docs"],
        ["uv", "add", "mkdocs", "--group", "docs"],
    ) in commands
    assert len(commands) == 4  # noqa: PLR2004


def test_run_uv_dry_run_no_subprocess(mocker):
    run_spy = mocker.patch("xapp_tools.update_deps.subprocess.run")
    rc = run_uv(["uv", "add", "click"], dry_run=True)
    assert rc == 0
    run_spy.assert_not_called()


def test_extract_package_name_invalid_raises():
    with pytest.raises(ValueError, match="Could not parse package name"):
        extract_package_name(">=1.0")
