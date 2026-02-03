"""WTS CLI entry point."""

import click

from wts.cli.autocomplete import autocomplete
from wts.cli.complete import complete
from wts.cli.config import config
from wts.cli.create import create
from wts.cli.delete import delete
from wts.cli.init import init, run_init
from wts.cli.list import list_cmd
from wts.cli.select import select
from wts.config import config_exists, maybe_update_config

# Commands that should skip auto-initialization
SKIP_INIT_COMMANDS = {"init", "autocomplete"}


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """WTS - Worktree Management System.

    Manage git worktrees for multi-agent development workflows.
    """
    # Skip auto-init for certain commands
    if ctx.invoked_subcommand in SKIP_INIT_COMMANDS:
        return

    # Auto-initialize if no config exists
    if not config_exists():
        click.echo("WTS needs to be initialized.")
        run_init()
        click.echo()  # Add blank line before command output
    else:
        # Update config file if it's missing new options
        maybe_update_config()


cli.add_command(autocomplete)
cli.add_command(complete)
cli.add_command(config)
cli.add_command(create)
cli.add_command(delete)
cli.add_command(init)
cli.add_command(list_cmd)
cli.add_command(select)
