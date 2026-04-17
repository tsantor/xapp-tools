import importlib.metadata

import click

from xapp_tools.check_version_source import main as check_version_source_cmd
from xapp_tools.public_api_snapshot import main as api_snapshot_cmd
from xapp_tools.update_coverage_badge import main as coverage_badge_cmd
from xapp_tools.update_deps import main as update_deps_cmd
from xapp_tools.verify_dist_artifacts import main as verify_dist_cmd
from xapp_tools.version_bump import main as version_bump_cmd
from xapp_tools.version_bump import set_version as version_set_cmd
from xapp_tools.version_bump import show as version_show_cmd
from xapp_tools.version_tag import main as version_tag_cmd
from xapp_tools.wheel_smoke_test import main as wheel_smoke_cmd


@click.group()
@click.version_option(importlib.metadata.version("xapp-tools"))
def cli() -> None:
    """xapp-core developer tools."""


cli.add_command(api_snapshot_cmd, name="api-snapshot")
cli.add_command(check_version_source_cmd, name="check-version-source")
cli.add_command(coverage_badge_cmd, name="coverage-badge")
cli.add_command(update_deps_cmd, name="update-deps")
cli.add_command(verify_dist_cmd, name="verify-dist")
cli.add_command(version_bump_cmd, name="version-bump")
cli.add_command(version_set_cmd, name="version-set")
cli.add_command(version_show_cmd, name="version-show")
cli.add_command(version_tag_cmd, name="version-tag")
cli.add_command(wheel_smoke_cmd, name="wheel-smoke")
