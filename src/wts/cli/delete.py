"""CLI command for deleting worktrees."""

import click

from wts.cli.completion import complete_worktree_names
from wts.core.worktree import WorktreeManager
from wts.exceptions import InvalidWorktreeNameError, WorktreeNotFoundError


@click.command()
@click.argument("name", shell_complete=complete_worktree_names)
@click.option("--keep-branch", is_flag=True, help="Keep the branch after removing the worktree")
def delete(name: str, keep_branch: bool) -> None:
    """Delete the worktree with the given NAME."""
    try:
        manager = WorktreeManager()
        manager.delete(name, keep_branch=keep_branch)
        click.echo(f"Deleted worktree '{name}'")
    except InvalidWorktreeNameError as e:
        raise click.ClickException(str(e))
    except WorktreeNotFoundError as e:
        raise click.ClickException(str(e))
