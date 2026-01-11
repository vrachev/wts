"""CLI command for creating worktrees."""

import subprocess

import click

from wts.core.editor import get_editor, is_terminal_editor, open_editor
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
    "editors",
    multiple=True,
    is_flag=False,
    flag_value="default",
    help="Open in editor(s), can be specified multiple times (-e uses default, -e cursor for specific)",
)
@click.option("--no-init", is_flag=True, help="Skip running the init script")
def create(name: str, from_current: bool, terminal: bool, editors: tuple[str, ...], no_init: bool) -> None:
    """Create a new worktree with the given NAME."""
    try:
        manager = WorktreeManager()

        # Resolve all editor names (handle "default" values)
        resolved_editors = []
        for e in editors:
            resolved_editors.append(get_editor(None if e == "default" else e))

        # Separate by type
        terminal_editors = [e for e in resolved_editors if is_terminal_editor(e)]
        gui_editors = [e for e in resolved_editors if not is_terminal_editor(e)]

        # Init runs in new terminal if: any terminal-based editor OR -t flag
        init_in_new_terminal = not no_init and (terminal or terminal_editors)

        # Create worktree - only run init in parent if NOT running in new terminal
        run_init_in_parent = not no_init and not init_in_new_terminal
        worktree_path = manager.create(name, from_current=from_current, run_init=run_init_in_parent)
        click.echo(f"Created worktree '{name}' at {worktree_path}")

        # Get init script once if needed
        init_script = manager.get_init_script() if init_in_new_terminal else None
        init_used = False

        # Open plain terminal if -t (gets init script first)
        if terminal:
            open_terminal(worktree_path, init_script=init_script)
            init_used = True

        # Open each terminal-based editor
        for editor in terminal_editors:
            script = init_script if not init_used else None
            open_terminal(worktree_path, command=editor, init_script=script)
            init_used = True

        # Open GUI editors
        for editor in gui_editors:
            open_editor(worktree_path, editor)
    except InvalidWorktreeNameError as e:
        raise click.ClickException(str(e))
    except WorktreeExistsError as e:
        raise click.ClickException(str(e))
    except EditorNotConfiguredError as e:
        raise click.ClickException(str(e))
    except UnsupportedEditorError as e:
        raise click.ClickException(str(e))
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if isinstance(e.stderr, str) else (e.stderr.decode() if e.stderr else str(e))
        raise click.ClickException(error_msg)
