"""CLI command for creating worktrees."""

import click

from wts.core.worktree import WorktreeManager
from wts.exceptions import InvalidWorktreeNameError, WorktreeExistsError


@click.command()
@click.argument("name")
@click.option("--from-current", is_flag=True, help="Branch from current HEAD instead of main")
def create(name: str, from_current: bool) -> None:
    """Create a new worktree with the given NAME."""
    try:
        manager = WorktreeManager()
        worktree_path = manager.create(name, from_current=from_current)
        click.echo(f"Created worktree '{name}' at {worktree_path}")
    except InvalidWorktreeNameError as e:
        raise click.ClickException(str(e))
    except WorktreeExistsError as e:
        raise click.ClickException(str(e))
