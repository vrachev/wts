"""CLI command for selecting worktrees."""

import click

from wts.cli.autocomplete import complete_worktree_names
from wts.core.editor import open_editor
from wts.core.terminal import open_terminal
from wts.core.worktree import WorktreeManager
from wts.exceptions import (
    EditorNotConfiguredError,
    InvalidWorktreeNameError,
    UnsupportedEditorError,
    WorktreeNotFoundError,
)


@click.command()
@click.argument("name", shell_complete=complete_worktree_names)
@click.option("--terminal", "-t", is_flag=True, help="Open a new terminal tab in the worktree")
@click.option(
    "--editor",
    "-e",
    default=None,
    help="Open in editor (--editor=default uses WTS_EDITOR, or specify: --editor=cursor)",
)
def select(name: str, terminal: bool, editor: str | None) -> None:
    """Select an existing worktree with the given NAME."""
    try:
        manager = WorktreeManager()
        manager._validate_name(name)

        if not manager._worktree_exists(name):
            raise WorktreeNotFoundError(f"Worktree '{name}' not found")

        worktree_path = manager._get_worktree_path(name)
        click.echo(f"Selected worktree '{name}' at {worktree_path}")

        if terminal:
            open_terminal(worktree_path)
        if editor is not None:
            open_editor(worktree_path, None if editor == "default" else editor)
    except InvalidWorktreeNameError as e:
        raise click.ClickException(str(e))
    except WorktreeNotFoundError as e:
        raise click.ClickException(str(e))
    except EditorNotConfiguredError as e:
        raise click.ClickException(str(e))
    except UnsupportedEditorError as e:
        raise click.ClickException(str(e))
