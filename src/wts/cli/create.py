"""CLI command for creating worktrees."""

import click

from wts.core.editor import open_editor
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
    default=None,
    help="Open in editor (--editor=default uses WTS_EDITOR, or specify: --editor=cursor)",
)
def create(name: str, from_current: bool, terminal: bool, editor: str | None) -> None:
    """Create a new worktree with the given NAME."""
    try:
        manager = WorktreeManager()
        worktree_path = manager.create(name, from_current=from_current)
        click.echo(f"Created worktree '{name}' at {worktree_path}")
        if terminal:
            open_terminal(worktree_path)
        if editor is not None:
            open_editor(worktree_path, None if editor == "default" else editor)
    except InvalidWorktreeNameError as e:
        raise click.ClickException(str(e))
    except WorktreeExistsError as e:
        raise click.ClickException(str(e))
    except EditorNotConfiguredError as e:
        raise click.ClickException(str(e))
    except UnsupportedEditorError as e:
        raise click.ClickException(str(e))
