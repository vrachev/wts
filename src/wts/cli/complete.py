"""CLI command for completing (merging) worktrees."""

import click

from wts.cli.autocomplete import complete_worktree_names
from wts.config import Config
from wts.core.worktree import WorktreeManager
from wts.exceptions import (
    InvalidWorktreeNameError,
    MergeConflictError,
    RepoNotCleanError,
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
    "-a",
    is_flag=True,
    help="Auto-resolve conflicts using Claude CLI (requires claude to be installed)",
)
@click.option(
    "--preserve-commits",
    "-p",
    is_flag=True,
    help="Use regular merge instead of squash merge (preserves individual commits)",
)
@click.option(
    "--no-coauthor/--coauthor",
    "-n",
    default=None,
    help="Strip Co-Authored-By trailers (default: from config, true if not set)",
)
def complete(
    name: str,
    message: str | None,
    use_latest_msg: bool,
    no_cleanup: bool,
    into: str,
    auto_resolve_claude: bool,
    preserve_commits: bool,
    no_coauthor: bool | None,
) -> None:
    """Merge worktree NAME into target branch.

    By default, performs a squash merge requiring MESSAGE. Use --preserve-commits
    for a regular merge that preserves individual commits (no message needed).

    Examples:

        wts complete feature-auth "Add JWT authentication"

        wts complete feature-auth --use-latest-msg

        wts complete feature-api -l --into develop

        wts complete bugfix-123 "Fix login bug" --no-cleanup

        wts complete feature-api --preserve-commits
    """
    if not preserve_commits:
        if message and use_latest_msg:
            raise click.ClickException("Cannot specify both MESSAGE and --use-latest-msg")
        if not message and not use_latest_msg:
            raise click.ClickException("Must specify either MESSAGE or --use-latest-msg or -l")

    # Resolve no_coauthor: CLI flag overrides config
    if no_coauthor is None:
        config = Config.load()
        no_coauthor = config.no_coauthor

    try:
        manager = WorktreeManager()
        manager.complete(
            name,
            message,
            into=into,
            cleanup=not no_cleanup,
            use_latest_msg=use_latest_msg,
            auto_resolve_claude=auto_resolve_claude,
            squash=not preserve_commits,
            no_coauthor=no_coauthor,
        )
        merge_type = "Merged" if preserve_commits else "Squash merged"
        if no_cleanup:
            click.echo(f"{merge_type} worktree '{name}' into '{into}'")
        else:
            click.echo(f"{merge_type} worktree '{name}' into '{into}' and cleaned up")
    except InvalidWorktreeNameError as e:
        raise click.ClickException(str(e))
    except WorktreeNotFoundError as e:
        raise click.ClickException(str(e))
    except WorktreeNotCleanError as e:
        raise click.ClickException(str(e))
    except RepoNotCleanError as e:
        raise click.ClickException(str(e))
    except MergeConflictError as e:
        raise click.ClickException(str(e))
