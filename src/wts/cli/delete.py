"""CLI command for deleting worktrees."""

import subprocess

import click

from wts.cli.autocomplete import complete_worktree_names
from wts.core.worktree import WorktreeManager
from wts.exceptions import InvalidWorktreeNameError, WorktreeNotFoundError


@click.command()
@click.argument("names", nargs=-1, required=True, shell_complete=complete_worktree_names)
@click.option("--keep-branch", is_flag=True, help="Keep the branch after removing the worktree")
@click.option("--force", "-f", is_flag=True, help="Force deletion even with modified/untracked files")
def delete(names: tuple[str, ...], keep_branch: bool, force: bool) -> None:
    """Delete the worktree(s) with the given NAME(s)."""
    if not force:
        names_list = ", ".join(names)
        click.confirm(f"Delete worktrees: {names_list}?", abort=True)

    manager = WorktreeManager()
    has_errors = False
    for name in names:
        try:
            manager.delete(name, keep_branch=keep_branch, force=force)
            click.echo(f"Deleted worktree '{name}'")
        except InvalidWorktreeNameError as e:
            click.echo(f"Error: {e}", err=True)
            has_errors = True
        except WorktreeNotFoundError as e:
            click.echo(f"Error: {e}", err=True)
            has_errors = True
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode().strip() if e.stderr else f"Command failed with exit code {e.returncode}"
            click.echo(f"Error deleting '{name}': {error_msg}", err=True)
            has_errors = True

    if has_errors:
        raise SystemExit(1)
