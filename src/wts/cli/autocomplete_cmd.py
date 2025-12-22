"""CLI command for generating shell completion scripts."""

import os
import subprocess
import sys

import click


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
