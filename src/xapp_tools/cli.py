import click

from xapp_tools.check_version_source import main as check_version_source_cmd
from xapp_tools.public_api_snapshot import main as api_snapshot_cmd
from xapp_tools.update_coverage_badge import main as coverage_badge_cmd
from xapp_tools.update_deps import main as update_deps_cmd
from xapp_tools.verify_dist_artifacts import main as verify_dist_cmd
from xapp_tools.wheel_smoke_test import main as wheel_smoke_cmd


@click.group()
def cli() -> None:
    """xapp-core developer tools."""


cli.add_command(api_snapshot_cmd, name="api-snapshot")
cli.add_command(check_version_source_cmd, name="check-version-source")
cli.add_command(coverage_badge_cmd, name="coverage-badge")
cli.add_command(update_deps_cmd, name="update-deps")
cli.add_command(verify_dist_cmd, name="verify-dist")
cli.add_command(wheel_smoke_cmd, name="wheel-smoke")
