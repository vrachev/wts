"""CLI command for completing (squash merging) worktrees."""

import click

from wts.cli.completion import complete_worktree_names
from wts.core.worktree import WorktreeManager
from wts.exceptions import (
    InvalidWorktreeNameError,
    MergeConflictError,
    WorktreeNotCleanError,
    WorktreeNotFoundError,
)


@click.command()
@click.argument("name", shell_complete=complete_worktree_names)
@click.argument("message", required=False)
@click.option(
    "--use-latest-msg",
    "-l",
    is_flag=True,
    help="Use the latest commit message from the worktree branch",
)
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
@click.option(
    "--auto-resolve-claude",
    is_flag=True,
    help="Auto-resolve conflicts using Claude CLI (requires claude to be installed)",
)
def complete(
    name: str, message: str | None, use_latest_msg: bool, no_cleanup: bool, into: str, auto_resolve_claude: bool
) -> None:
    """Squash merge worktree NAME into target branch with MESSAGE.

    Performs a squash merge of the worktree's branch into the target branch
    (default: main), then cleans up the worktree and branch by default.

    Examples:

        wts complete feature-auth "Add JWT authentication"

        wts complete feature-auth --use-latest-msg

        wts complete feature-api -l --into develop

        wts complete bugfix-123 "Fix login bug" --no-cleanup
    """
    if message and use_latest_msg:
        raise click.ClickException("Cannot specify both MESSAGE and --use-latest-msg")
    if not message and not use_latest_msg:
        raise click.ClickException("Must specify either MESSAGE or --use-latest-msg or -l")
    try:
        manager = WorktreeManager()
        manager.complete(
            name,
            message,
            into=into,
            cleanup=not no_cleanup,
            use_latest_msg=use_latest_msg,
            auto_resolve_claude=auto_resolve_claude,
        )
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
