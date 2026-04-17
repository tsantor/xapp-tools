import importlib.metadata

import click

from xapp_tools.check_version_source import main as check_version_source_cmd
from xapp_tools.public_api_snapshot import main as api_snapshot_cmd
from xapp_tools.update_coverage_badge import main as coverage_badge_cmd
from xapp_tools.update_deps import main as update_deps_cmd
from xapp_tools.verify_dist_artifacts import main as verify_dist_cmd
from xapp_tools.version_bump import main as bump_cmd
from xapp_tools.version_bump import set_version as set_version_cmd
from xapp_tools.version_bump import show as show_cmd
from xapp_tools.version_tag import create as tag_create_cmd
from xapp_tools.version_tag import dryrun as tag_dryrun_cmd
from xapp_tools.version_tag import push as tag_push_cmd
from xapp_tools.wheel_smoke_test import main as wheel_smoke_cmd


@click.group()
@click.version_option(importlib.metadata.version("xapp-tools"))
def cli() -> None:
    """xapp-core developer tools."""


@click.group("version")
def version_group() -> None:
    """Version management commands."""


version_group.add_command(show_cmd, name="show")
version_group.add_command(set_version_cmd, name="set")
version_group.add_command(bump_cmd, name="bump")
version_group.add_command(check_version_source_cmd, name="check-source")


@click.group("tag")
def tag_group() -> None:
    """Git tag management commands."""


tag_group.add_command(tag_dryrun_cmd)
tag_group.add_command(tag_create_cmd)
tag_group.add_command(tag_push_cmd)


@click.group("dist")
def dist_group() -> None:
    """Distribution artifact commands."""


dist_group.add_command(verify_dist_cmd, name="verify")
dist_group.add_command(wheel_smoke_cmd, name="wheel-smoke")
dist_group.add_command(api_snapshot_cmd, name="api-snapshot")


cli.add_command(version_group)
cli.add_command(tag_group)
cli.add_command(dist_group)
cli.add_command(coverage_badge_cmd, name="coverage-badge")
cli.add_command(update_deps_cmd, name="update-deps")
