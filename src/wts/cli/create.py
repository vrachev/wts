"""CLI command for creating worktrees."""

import click

from wts.core.editor import get_editor, open_editor
from wts.core.terminal import open_terminal
from wts.core.worktree import WorktreeManager
from wts.exceptions import (
    EditorNotConfiguredError,
    InvalidWorktreeNameError,
    UnsupportedEditorError,
    WorktreeExistsError,
)


@click.command()
@click.argument("name")
@click.option("--from-current", is_flag=True, help="Branch from current HEAD instead of main")
@click.option("--terminal", "-t", is_flag=True, help="Open a new terminal tab in the worktree")
@click.option(
    "--editor",
    "-e",
    is_flag=False,
    flag_value="default",
    help="Open in editor (-e uses default, -e cursor for specific)",
)
@click.option("--no-init", is_flag=True, help="Skip running the init script")
def create(name: str, from_current: bool, terminal: bool, editor: str | None, no_init: bool) -> None:
    """Create a new worktree with the given NAME."""
    try:
        manager = WorktreeManager()

        # Determine where init should run:
        # - In new terminal if: -t flag OR -e claude
        # - In parent terminal if: no flags OR -e <GUI editor>
        editor_name = None
        if editor is not None:
            editor_name = get_editor(None if editor == "default" else editor)

        runs_in_terminal = editor_name == "claude"
        init_in_new_terminal = not no_init and (terminal or runs_in_terminal)

        # Create worktree - only run init in parent if NOT running in new terminal
        run_init_in_parent = not no_init and not init_in_new_terminal
        worktree_path = manager.create(name, from_current=from_current, run_init=run_init_in_parent)
        click.echo(f"Created worktree '{name}' at {worktree_path}")

        # Get init script for new terminal if needed
        init_script = manager.get_init_script() if init_in_new_terminal else None

        # Open terminal if -t or -e claude
        if terminal or runs_in_terminal:
            terminal_cmd = "claude" if runs_in_terminal else None
            open_terminal(worktree_path, command=terminal_cmd, init_script=init_script)

        # Open GUI editor (these open immediately, init runs in parent before)
        if editor is not None and not runs_in_terminal:
            open_editor(worktree_path, None if editor == "default" else editor)
    except InvalidWorktreeNameError as e:
        raise click.ClickException(str(e))
    except WorktreeExistsError as e:
        raise click.ClickException(str(e))
    except EditorNotConfiguredError as e:
        raise click.ClickException(str(e))
    except UnsupportedEditorError as e:
        raise click.ClickException(str(e))
