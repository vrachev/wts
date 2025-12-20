"""CLI command for committing (squash merging) worktrees."""

import click

from wts.core.worktree import WorktreeManager
from wts.exceptions import (
    InvalidWorktreeNameError,
    MergeConflictError,
    WorktreeNotCleanError,
    WorktreeNotFoundError,
)


@click.command()
@click.argument("name")
@click.argument("message")
@click.option(
    "--no-cleanup",
    is_flag=True,
    help="Keep worktree and branch after merge (default: cleanup)",
)
@click.option(
    "--into",
    default="main",
    help="Target branch to merge into (default: main)",
)
def commit(name: str, message: str, no_cleanup: bool, into: str) -> None:
    """Squash merge worktree NAME into target branch with MESSAGE.

    Performs a squash merge of the worktree's branch into the target branch
    (default: main), then cleans up the worktree and branch by default.

    Examples:

        wts commit feature-auth "Add JWT authentication"

        wts commit feature-api "Add REST API" --into develop

        wts commit bugfix-123 "Fix login bug" --no-cleanup
    """
    try:
        manager = WorktreeManager()
        manager.commit(name, message, into=into, cleanup=not no_cleanup)
        if no_cleanup:
            click.echo(f"Merged worktree '{name}' into '{into}'")
        else:
            click.echo(f"Merged worktree '{name}' into '{into}' and cleaned up")
    except InvalidWorktreeNameError as e:
        raise click.ClickException(str(e))
    except WorktreeNotFoundError as e:
        raise click.ClickException(str(e))
    except WorktreeNotCleanError as e:
        raise click.ClickException(str(e))
    except MergeConflictError as e:
        raise click.ClickException(str(e))
