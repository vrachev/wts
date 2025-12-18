"""WTS CLI entry point."""

import click

from wts.cli.create import create
from wts.cli.delete import delete


@click.group()
def cli() -> None:
    """WTS - Worktree Management System.

    Manage git worktrees for multi-agent development workflows.
    """
    pass


cli.add_command(create)
cli.add_command(delete)
