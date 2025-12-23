"""CLI command for generating shell completion scripts."""

import os
import subprocess
import sys

import click
from click.shell_completion import CompletionItem

from wts.core.worktree import WorktreeManager


def complete_worktree_names(ctx: object, param: object, incomplete: str) -> list[CompletionItem]:
    """Provide completion for worktree names.

    Args:
        ctx: Click context (unused but required by signature).
        param: Click parameter (unused but required by signature).
        incomplete: The partial worktree name typed so far.

    Returns:
        List of CompletionItem objects matching the incomplete prefix.
    """
    try:
        manager = WorktreeManager()
        worktrees = manager.list()
        return [CompletionItem(name) for name in worktrees if name.startswith(incomplete)]
    except Exception:
        # If completion fails (e.g., not in a git repo), return empty list
        return []


@click.command("autocomplete")
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
def autocomplete(shell: str) -> None:
    """Generate shell completion script.

    Output a script to enable shell completion for wts commands.

    \b
    Installation:

    \b
    Bash:
      wts autocomplete bash >> ~/.bashrc

    \b
    Zsh:
      wts autocomplete zsh >> ~/.zshrc

    \b
    Fish:
      wts autocomplete fish > ~/.config/fish/completions/wts.fish

    \b
    After installation, restart your shell or source the config file.
    """
    # Find the wts executable path
    wts_path = subprocess.run(
        ["which", "wts"],
        capture_output=True,
        text=True,
    ).stdout.strip()

    if not wts_path:
        wts_path = "wts"

    # Generate the completion script by invoking wts with the completion env var
    env = os.environ.copy()
    env["_WTS_COMPLETE"] = f"{shell}_source"

    result = subprocess.run(
        [wts_path],
        env=env,
        capture_output=True,
        text=True,
    )

    if result.stdout:
        click.echo(result.stdout)
    elif result.stderr:
        click.echo(result.stderr, err=True)
        sys.exit(1)
