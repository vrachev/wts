"""CLI command for listing worktrees."""

import click

from wts.core.worktree import WorktreeManager


@click.command("list")
def list_cmd() -> None:
    """List all worktrees for the current repository."""
    manager = WorktreeManager()
    worktrees = manager.list()
    for name in worktrees:
        click.echo(name)
