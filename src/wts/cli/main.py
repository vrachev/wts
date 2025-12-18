"""WTS CLI entry point."""

import click

from wts.cli.create import create
from wts.cli.delete import delete
from wts.cli.list import list_cmd


@click.group()
def cli() -> None:
    """WTS - Worktree Management System.

    Manage git worktrees for multi-agent development workflows.
    """
    pass


cli.add_command(create)
cli.add_command(delete)
cli.add_command(list_cmd)
